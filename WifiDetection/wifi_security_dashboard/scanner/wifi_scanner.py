import os
import platform
import re
import subprocess
from typing import List, Dict

# Optionally use scapy for future extensions; avoid root dependency for listing
try:
    from scapy.all import sniff  # noqa: F401
except Exception:
    pass


def parse_windows_netsh(output: str) -> List[Dict]:
    networks = []
    current = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith('SSID '):
            # new network
            if current:
                networks.append(current)
                current = {}
            # SSID 1 : MyWifi
            parts = line.split(':', 1)
            if len(parts) == 2:
                current['ssid'] = parts[1].strip()
        elif line.startswith('BSSID '):
            # BSSID 1 : aa:bb:cc:dd:ee:ff
            bssid = line.split(':', 1)[1].strip()
            current['bssid'] = bssid
        elif line.lower().startswith('signal'):
            # Signal             : 78%
            sig = line.split(':', 1)[1].strip().replace('%','')
            try:
                current['signal'] = int(sig)
            except ValueError:
                current['signal'] = None
        elif line.lower().startswith('channel'):
            ch = line.split(':', 1)[1].strip()
            try:
                current['channel'] = int(ch)
            except ValueError:
                current['channel'] = ch
        elif line.lower().startswith('authentication'):
            current['security'] = line.split(':', 1)[1].strip()
        elif line.lower().startswith('encryption'):
            current['encryption'] = line.split(':', 1)[1].strip()
        elif 'network type' in line.lower():
            # not used but can parse
            pass
    if current:
        networks.append(current)
    return [n for n in networks if n.get('bssid')]


def parse_linux_nmcli(output: str) -> List[Dict]:
    # Expect columns: SSID:BSSID:CHAN:SIGNAL:SECURITY:FREQ
    networks = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 6:
            continue
        ssid, bssid, chan, signal, security, freq = parts[:6]
        try:
            chan_val = int(chan)
        except ValueError:
            chan_val = None
        try:
            signal_val = int(signal)
        except ValueError:
            signal_val = None
        n = {
            'ssid': ssid.strip() or '(hidden)',
            'bssid': bssid.strip(),
            'channel': chan_val if chan_val is not None else chan.strip(),
            'signal': signal_val,
            'security': security.strip() or 'Open',
            'encryption': security.strip(),
            'frequency': freq.strip(),
        }
        networks.append(n)
    return networks


def scan_wifi_networks() -> List[Dict]:
    system = platform.system().lower()
    try:
        if system == 'windows':
            cmd = ['netsh', 'wlan', 'show', 'networks', 'mode=bssid']
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')
            return parse_windows_netsh(out)
        else:
            # Linux
            # Use tab-separated columns for reliable parsing
            fmt = 'SSID,BSSID,CHAN,SIGNAL,SECURITY,FREQ'
            cmd = [
                'bash', '-lc',
                "nmcli -t -f SSID,BSSID,CHAN,SIGNAL,SECURITY,FREQ device wifi list || true"
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')
            # nmcli -t uses ':' as default separator; replace with tabs carefully (BSSID contains ':')
            lines = []
            for raw in out.splitlines():
                # SSID:BSSID:CHAN:SIGNAL:SECURITY:FREQ with BSSID including ':'
                # Split only first field, then BSSID, then rest
                fields = raw.split(':')
                if len(fields) < 6:
                    continue
                # Rebuild to tabs: SSID \t BSSID \t CHAN \t SIGNAL \t SECURITY \t FREQ
                ssid = fields[0]
                bssid = ':'.join(fields[1:7]) if len(fields) >= 7 else fields[1]
                # To be safer, use regex to extract MAC
                mac_match = re.search(r"([0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5})", raw)
                if mac_match:
                    bssid = mac_match.group(1)
                rest = raw.split(bssid, 1)[-1].lstrip(':')
                rest_fields = rest.split(':')
                if len(rest_fields) < 4:
                    continue
                line = '\t'.join([ssid, bssid, rest_fields[0], rest_fields[1], rest_fields[2], rest_fields[3]])
                lines.append(line)
            tsv = '\n'.join(lines)
            return parse_linux_nmcli(tsv)
    except subprocess.CalledProcessError as e:
        return []
