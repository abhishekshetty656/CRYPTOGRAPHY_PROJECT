import os
import json
import time
import platform
import threading
import subprocess
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

from flask import Flask, jsonify, render_template, request

# Optional WiFi libs (graceful fallback)
SCAPY_AVAILABLE = False
PYPYWI_AVAILABLE = False
try:
    from scapy.all import sniff, Dot11  # type: ignore
    SCAPY_AVAILABLE = True
except Exception:
    SCAPY_AVAILABLE = False

try:
    from pywifi import PyWiFi, const  # type: ignore
    PYPYWI_AVAILABLE = True
except Exception:
    PYPYWI_AVAILABLE = False

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_FILE = os.path.join(DATA_DIR, 'attack_logs.json')
os.makedirs(DATA_DIR, exist_ok=True)

# State
state_lock = threading.Lock()
networks_cache: List[Dict[str, Any]] = []
last_scan_ts: float = 0.0

# Trusted router OUIs (use your own list for production)
TRUSTED_OUIS = {
    '00:1A:11', '00:1B:63', 'B8:27:EB', '3C:84:6A', 'FC:FB:FB', 'F4:F5:E8',
}

# Utilities

def normalize_mac(mac: str) -> str:
    return (mac or '').upper()


def oui(mac: str) -> str:
    m = normalize_mac(mac)
    return m[:8] if len(m) >= 8 else ''


def load_logs() -> List[dict]:
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_logs(logs: List[dict]):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs[-1000:], f, indent=2)


def log_detection(entry: dict):
    logs = load_logs()
    logs.append(entry)
    save_logs(logs)


def encryption_label_from_cap(cap: str) -> str:
    c = (cap or '').upper()
    if 'WPA3' in c:
        return 'WPA3'
    if 'WPA2' in c:
        return 'WPA2'
    if 'WPA' in c:
        return 'WPA'
    if 'WEP' in c:
        return 'WEP'
    if 'PRIVACY' in c:
        return 'WPA/WEP'
    return 'OPEN'


def select_wifi_interface(ifaces):
    if not ifaces:
        return None
    # Prefer names indicating WLAN
    named = []
    for i in ifaces:
        name = getattr(i, 'name', '') or getattr(i, 'iface', '') or ''
        named.append((name.lower(), i))
    for nm, iface in named:
        if 'wlan' in nm or 'wi-fi' in nm or 'wifi' in nm:
            return iface
    return ifaces[0]


def get_connected_network() -> Dict[str, str]:
    """Detect currently connected network. Returns dict with ssid, bssid, auth (if known), and signal_pct (if known)."""
    info = {'ssid': '', 'bssid': '', 'auth': '', 'signal_pct': ''}
    try:
        if platform.system().lower().startswith('win'):
            out = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], encoding='utf-8', errors='ignore')
            for line in out.splitlines():
                L = line.strip()
                low = L.lower()
                if low.startswith('ssid') and not low.startswith('ssid bssid'):
                    v = L.split(':', 1)[1].strip()
                    if v and v.lower() != 'not connected':
                        info['ssid'] = v
                elif low.startswith('bssid'):
                    info['bssid'] = L.split(':', 1)[1].strip().upper()
                elif low.startswith('authentication'):
                    info['auth'] = L.split(':', 1)[1].strip()
                elif low.startswith('signal'):
                    # e.g., Signal             : 98%
                    val = L.split(':', 1)[1].strip().rstrip('%')
                    info['signal_pct'] = val
            return info
    except Exception:
        pass
    try:
        if platform.system().lower().startswith('linux'):
            out = subprocess.check_output(['nmcli', '-t', '-f', 'active,ssid,bssid', 'dev', 'wifi'], encoding='utf-8', errors='ignore')
            for line in out.splitlines():
                if line.startswith('yes:'):
                    parts = line.strip().split(':')
                    if len(parts) >= 3:
                        info['ssid'] = parts[1]
                        info['bssid'] = parts[2].upper()
                        break
            return info
    except Exception:
        pass
    return info

# Scanning

def scan_pywifi() -> List[dict]:
    if not PYPYWI_AVAILABLE:
        return []
    try:
        wifi = PyWiFi()
        iface = select_wifi_interface(wifi.interfaces())
        if not iface:
            return []
        iface.scan()
        time.sleep(2.0)
        results = iface.scan_results()
        nets = []
        for r in results:
            enc = 'OPEN'
            akm = getattr(r, 'akm', []) or []
            if akm:
                if const.AKM_TYPE_SAE in akm:
                    enc = 'WPA3'
                elif const.AKM_TYPE_WPA2 in akm:
                    enc = 'WPA2'
                elif const.AKM_TYPE_WPA in akm:
                    enc = 'WPA'
                else:
                    enc = 'WPA'
            if hasattr(r, 'capabilities') and enc == 'OPEN':
                enc = encryption_label_from_cap(getattr(r, 'capabilities', ''))
            nets.append({
                'ssid': r.ssid or '',
                'bssid': normalize_mac(getattr(r, 'bssid', '')),
                'signal': int(getattr(r, 'signal', -100)),
                'channel': getattr(r, 'channel', 0) or 0,
                'frequency': getattr(r, 'freq', 0) or 0,
                'encryption': enc,
                'source': 'pywifi'
            })
        return nets
    except Exception:
        return []


def scan_scapy(timeout: int = 4) -> List[dict]:
    if not SCAPY_AVAILABLE:
        return []
    seen: Dict[str, dict] = {}
    def handler(pkt):
        if pkt.haslayer(Dot11):
            d = pkt.getlayer(Dot11)
            if d.type == 0 and d.subtype in (8, 5):
                bssid = normalize_mac(d.addr2 or '')
                ssid = ''
                try:
                    ssid = pkt.info.decode(errors='ignore') if hasattr(pkt, 'info') else ''
                except Exception:
                    pass
                sig = -100
                try:
                    if hasattr(pkt, 'dBm_AntSignal'):
                        sig = int(pkt.dBm_AntSignal)
                except Exception:
                    pass
                caps = ''
                ch = 0
                try:
                    if hasattr(pkt, 'network_stats'):
                        stats = pkt.network_stats()
                        enc_list = stats.get('crypto', [])
                        if enc_list:
                            caps = ','.join(enc_list)
                        ch = stats.get('channel', 0)
                except Exception:
                    pass
                enc = encryption_label_from_cap(caps)
                cur = seen.get(bssid)
                if (not cur) or (sig > cur.get('signal', -100)):
                    seen[bssid] = {
                        'ssid': ssid,
                        'bssid': bssid,
                        'signal': sig,
                        'channel': ch,
                        'frequency': 0,
                        'encryption': enc,
                        'source': 'scapy'
                    }
    try:
        sniff(prn=handler, timeout=timeout, store=0)
    except Exception:
        return []
    return list(seen.values())


def perform_scan(connected_only: bool = False) -> List[dict]:
    nets = scan_pywifi()
    nets = merge_networks(nets, scan_scapy())
    if not nets:
        # Demo sample for UI
        demo = [
            {'ssid': 'GalaxyHub', 'bssid': '00:1A:11:AA:BB:01', 'signal': -46, 'channel': 6, 'frequency': 2437, 'encryption': 'OPEN', 'source': 'demo'},
            {'ssid': 'GalaxyHub', 'bssid': '3C:84:6A:00:11:22', 'signal': -57, 'channel': 6, 'frequency': 2437, 'encryption': 'WPA2', 'source': 'demo'},
            {'ssid': 'NebulaNet', 'bssid': 'FC:FB:FB:AA:BB:CC', 'signal': -52, 'channel': 11, 'frequency': 2462, 'encryption': 'WPA3', 'source': 'demo'},
            {'ssid': 'Free_Airport_WiFi', 'bssid': '12:34:56:78:90:12', 'signal': -31, 'channel': 1, 'frequency': 2412, 'encryption': 'OPEN', 'source': 'demo'},
            {'ssid': 'OrionCorp', 'bssid': 'F4:F5:E8:99:88:77', 'signal': -75, 'channel': 44, 'frequency': 5220, 'encryption': 'WEP', 'source': 'demo'}
        ]
        nets = demo
    if connected_only:
        info = get_connected_network()
        # Try to match connected BSSID or SSID from scan results
        matched: List[dict] = []
        if info.get('bssid'):
            bb = info['bssid'].upper()
            matched = [n for n in nets if (n.get('bssid','').upper() == bb)]
        if not matched and info.get('ssid'):
            matched = [n for n in nets if (n.get('ssid') or '') == info['ssid']]
        if matched:
            nets = matched
        else:
            # Synthesize a single entry from OS info if scans don't include it
            enc = 'OPEN'
            auth = (info.get('auth') or '').upper()
            if 'WPA3' in auth:
                enc = 'WPA3'
            elif 'WPA2' in auth:
                enc = 'WPA2'
            elif 'WPA' in auth:
                enc = 'WPA'
            elif 'WEP' in auth:
                enc = 'WEP'
            sig_pct = 0
            try:
                sig_pct = int(info.get('signal_pct') or '0')
            except Exception:
                pass
            # rough conversion from percent to dBm (approx)
            sig_dbm = int(sig_pct/2) - 100 if sig_pct else -60
            nets = [{
                'ssid': info.get('ssid') or '<hidden>',
                'bssid': info.get('bssid') or '',
                'signal': sig_dbm,
                'channel': 0,
                'frequency': 0,
                'encryption': enc,
                'source': 'osinfo'
            }]
    return nets


def merge_networks(a: List[dict], b: List[dict]) -> List[dict]:
    by = {n.get('bssid',''): n for n in a}
    for n in b:
        k = n.get('bssid','')
        if k in by:
            base = by[k]
            if n.get('signal', -100) > base.get('signal', -100):
                base['signal'] = n.get('signal')
            for key in ('ssid','channel','frequency','encryption','source'):
                if not base.get(key) and n.get(key):
                    base[key] = n.get(key)
        else:
            by[k] = n
    return list(by.values())

# Analysis

def analyze(nets: List[dict]) -> List[dict]:
    groups: Dict[str, List[dict]] = defaultdict(list)
    for n in nets:
        groups[n.get('ssid') or '<hidden>'].append(n)

    analyzed = []
    for n in nets:
        ssid = n.get('ssid') or '<hidden>'
        bssid = n.get('bssid','')
        enc = n.get('encryption') or 'OPEN'
        sig = n.get('signal', -100)
        siblings = groups.get(ssid, [])

        # Risk weights (per spec): duplicate +40, open +30, unknown MAC +20, strong +10
        score = 0
        if len(siblings) > 1:
            score += 40
        if enc == 'OPEN':
            score += 30
        if oui(bssid) not in TRUSTED_OUIS:
            score += 20
        try:
            sigs = sorted([x.get('signal', -100) for x in siblings]) if siblings else [sig]
            median = sigs[len(sigs)//2]
            if sig - median >= 20:
                score += 10
        except Exception:
            pass
        score = min(score, 100)

        level = {
            'OPEN': 'High Risk',
            'WEP': 'Weak Security',
            'WPA': 'Medium Security',
            'WPA2': 'Secure',
            'WPA3': 'Very Secure'
        }.get(enc, 'Unknown')

        analyzed.append({
            **n,
            'encryption': enc,
            'risk': score,
            'risk_label': 'Safe' if score < 30 else ('Suspicious' if score < 60 else 'Dangerous'),
            'security_level': level,
            'evil_twin': len(siblings) > 1,
            'unknown_mac': oui(bssid) not in TRUSTED_OUIS,
        })
    return analyzed

# Background refresher

def refresher():
    global networks_cache, last_scan_ts
    while True:
        # Force connected-only mode in background
        fresh = perform_scan(connected_only=True)
        analyzed = analyze(fresh)
        with state_lock:
            networks_cache = analyzed
            last_scan_ts = time.time()
        for n in analyzed:
            if n['risk'] >= 30:
                log_detection({
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'ssid': n.get('ssid') or '<hidden>',
                    'bssid': n.get('bssid'),
                    'attack_type': 'Evil Twin' if n.get('evil_twin') else 'Suspicious Network',
                    'risk': n.get('risk'),
                })
        time.sleep(5)

threading.Thread(target=refresher, daemon=True).start()

# Routes

@app.context_processor
def inject_flags():
    return {
        'SCAPY_AVAILABLE': SCAPY_AVAILABLE,
        'PYPYWI_AVAILABLE': PYPYWI_AVAILABLE,
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/analysis')
def analysis_page():
    return render_template('analysis.html')

@app.route('/logs')
def logs_page():
    return render_template('logs.html')

@app.route('/api/scan')
def api_scan():
    # Always return only the connected network
    fresh = perform_scan(connected_only=True)
    analyzed = analyze(fresh)
    return jsonify({'timestamp': time.time(), 'networks': analyzed})

@app.route('/api/networks')
def api_networks():
    with state_lock:
        return jsonify({'timestamp': last_scan_ts, 'networks': networks_cache})

@app.route('/api/logs')
def api_logs():
    return jsonify({'logs': load_logs()})

@app.route('/api/clear_logs', methods=['POST'])
def api_clear_logs():
    save_logs([])
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=True)
