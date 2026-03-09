from collections import defaultdict
from typing import List, Dict


RISK_LOW = 'LOW'
RISK_MEDIUM = 'MEDIUM'
RISK_HIGH = 'HIGH'


def risk_level(duplicate_count: int, has_open_variant: bool, strong_signal_variant: bool) -> str:
    if strong_signal_variant and has_open_variant:
        return RISK_HIGH
    if strong_signal_variant or has_open_variant:
        return RISK_MEDIUM
    if duplicate_count > 1:
        return RISK_LOW
    return RISK_LOW


def detect_evil_twins(networks: List[Dict]) -> List[Dict]:
    groups = defaultdict(list)
    for n in networks:
        ssid = n.get('ssid') or '(hidden)'
        groups[ssid].append(n)
    suspicious = []
    for ssid, arr in groups.items():
        if len(arr) <= 1:
            continue
        # Identify duplicates with different BSSID
        bssids = {a.get('bssid') for a in arr}
        if len(bssids) <= 1:
            continue
        # strongest signal among duplicates
        strongest = max([a.get('signal') or -100 for a in arr])
        has_open = any(('open' in str(a.get('security','')).lower()) or str(a.get('security','')).strip()=='' for a in arr)
        strong_dup = any(((a.get('signal') or -100) >= strongest - 5) for a in arr)
        r = risk_level(len(arr), has_open, strong_dup)
        suspicious.append({
            'ssid': ssid,
            'bssids': list(bssids),
            'count': len(arr),
            'has_open_variant': has_open,
            'strong_signal_variant': strong_dup,
            'risk': r,
        })
    # Sort by risk
    order = {RISK_HIGH: 0, RISK_MEDIUM: 1, RISK_LOW: 2}
    suspicious.sort(key=lambda x: order.get(x['risk'], 3))
    return suspicious
