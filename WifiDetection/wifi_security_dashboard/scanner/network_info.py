import platform
import socket
import subprocess
import psutil
import time
from typing import Dict, List


def get_gateway_dns() -> Dict:
    gateways = psutil.net_if_addrs()
    gws = psutil.net_if_stats()
    # Gateway via netifaces or psutil is limited; use route command per OS
    gateway = None
    dns = []
    system = platform.system().lower()
    try:
        if system == 'windows':
            out = subprocess.check_output(['ipconfig', '/all'], text=True, encoding='utf-8', errors='ignore')
            gw = None
            dnss = []
            for line in out.splitlines():
                if 'Default Gateway' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        gw = parts[1].strip()
                        if gw:
                            gateway = gw
                if 'DNS Servers' in line or 'DNS Server' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        val = parts[1].strip()
                        if val:
                            dnss.append(val)
            dns = dnss
        else:
            out = subprocess.check_output(['bash','-lc','ip route show default || route -n | grep ^0.0.0.0 || true'], text=True)
            if out.strip():
                gateway = out.strip().split()[2]
            # resolv.conf
            out = subprocess.check_output(['bash','-lc','grep ^nameserver /etc/resolv.conf | awk "{print $2}" || true'], text=True)
            dns = [x.strip() for x in out.splitlines() if x.strip()]
    except Exception:
        pass
    return {'gateway': gateway, 'dns': dns}


def get_current_network_info() -> Dict:
    info = {
        'connected_ssid': None,
        'router_bssid': None,
        'ip_address': None,
        'gateway': None,
        'dns_server': [],
        'local_mac': None,
        'interface': None,
        'network_type': None,
    }
    system = platform.system().lower()
    try:
        if system == 'windows':
            out = subprocess.check_output(['netsh','wlan','show','interfaces'], text=True, encoding='utf-8', errors='ignore')
            for line in out.splitlines():
                if 'SSID' in line and 'BSSID' not in line:
                    info['connected_ssid'] = line.split(':', 1)[1].strip()
                elif 'BSSID' in line:
                    info['router_bssid'] = line.split(':', 1)[1].strip()
                elif 'State' in line and 'connected' in line.lower():
                    pass
                elif 'Radio type' in line:
                    pass
                elif 'Physical address' in line:
                    info['local_mac'] = line.split(':', 1)[1].strip()
                elif 'Name' in line and info['interface'] is None:
                    info['interface'] = line.split(':', 1)[1].strip()
            # IP
            addrs = psutil.net_if_addrs()
            if info['interface'] and info['interface'] in addrs:
                for snic in addrs[info['interface']]:
                    if snic.family.name == 'AF_INET' or snic.family == socket.AF_INET:
                        info['ip_address'] = snic.address
        else:
            out = subprocess.check_output(['bash','-lc','nmcli -t -f ACTIVE,SSID,BSSID,DEVICE dev wifi | grep "^yes:" || true'], text=True)
            if out.strip():
                parts = out.strip().split(':')
                if len(parts) >= 4:
                    info['connected_ssid'] = parts[1]
                    info['router_bssid'] = parts[2]
                    info['interface'] = parts[3]
            # IP via psutil
            if info['interface']:
                addrs = psutil.net_if_addrs()
                if info['interface'] in addrs:
                    for snic in addrs[info['interface']]:
                        if snic.family.name == 'AF_INET' or snic.family == socket.AF_INET:
                            info['ip_address'] = snic.address
        # Common gateway/DNS
        gwdns = get_gateway_dns()
        info['gateway'] = gwdns.get('gateway')
        info['dns_server'] = gwdns.get('dns', [])
        # Determine network type by interface name heuristics
        if info['interface']:
            name = info['interface'].lower()
            if any(x in name for x in ['wi-fi','wlan','wifi']):
                info['network_type'] = 'WiFi'
            elif any(x in name for x in ['eth','ethernet','enp','eno']):
                info['network_type'] = 'Ethernet'
    except Exception:
        pass
    return info


def get_ethernet_info() -> Dict:
    result = {
        'interfaces': []
    }
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    io = psutil.net_io_counters(pernic=True)
    for iface, st in stats.items():
        lname = iface.lower()
        if any(x in lname for x in ['eth','ethernet','enp','eno']):
            entry = {
                'interface': iface,
                'speed': st.speed,
                'status': 'up' if st.isup else 'down',
                'ip': None,
                'packets_sent': None,
                'packets_recv': None,
            }
            if iface in addrs:
                for snic in addrs[iface]:
                    if snic.family.name == 'AF_INET' or snic.family == socket.AF_INET:
                        entry['ip'] = snic.address
                        break
            if iface in io:
                entry['packets_sent'] = io[iface].packets_sent
                entry['packets_recv'] = io[iface].packets_recv
            result['interfaces'].append(entry)
    return result


def scan_lan_devices(timeout: int = 2) -> List[Dict]:
    # Basic arp table parsing as a cross-platform low-priv fallback
    devices = []
    system = platform.system().lower()
    try:
        if system == 'windows':
            out = subprocess.check_output(['arp','-a'], text=True, encoding='utf-8', errors='ignore')
            for line in out.splitlines():
                if '-' in line and ':' not in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[1]
                        if mac.count('-') == 5:
                            mac = mac.replace('-', ':').lower()
                        devices.append({'ip': ip, 'mac': mac})
        else:
            out = subprocess.check_output(['bash','-lc','arp -n || ip neigh || true'], text=True)
            for line in out.splitlines():
                if 'ether' in line or ':' in line:
                    parts = line.split()
                    ip = parts[0]
                    mac = None
                    for p in parts:
                        if len(p) == 17 and p.count(':') == 5:
                            mac = p.lower()
                            break
                    if mac:
                        devices.append({'ip': ip, 'mac': mac})
    except Exception:
        pass
    # Vendor and hostname enrichment best-effort
    for d in devices:
        try:
            d['hostname'] = socket.getfqdn(d['ip'])
        except Exception:
            d['hostname'] = None
    return devices


def check_internet(timeout: int = 2) -> Dict:
    """Best-effort Internet connectivity check with small timeout.
    Tries multiple well-known endpoints (DNS/HTTP). Returns a dict with online flag and basic telemetry.
    """
    targets = [
        ('1.1.1.1', 53),
        ('8.8.8.8', 53),
        ('9.9.9.9', 53),
        ('www.google.com', 80),
    ]
    start = time.perf_counter()
    for host, port in targets:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                latency = int((time.perf_counter() - start) * 1000)
                return {'online': True, 'target': f'{host}:{port}', 'latency_ms': latency}
        except Exception:
            continue
    return {'online': False}
