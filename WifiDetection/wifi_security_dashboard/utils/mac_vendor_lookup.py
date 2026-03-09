import os
import re
from functools import lru_cache

# Minimal OUI dataset fallback; prefer local cached file if provided
OUI_FILE = os.path.join(os.path.dirname(__file__), 'oui.txt')


def _load_oui() -> dict:
    db = {}
    if os.path.exists(OUI_FILE):
        with open(OUI_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    prefix, vendor = parts
                    db[prefix.upper()] = vendor
    # Some common prefixes as seed
    db.setdefault('FC:EC:DA', 'Apple')
    db.setdefault('F4:F5:E8', 'TP-Link')
    db.setdefault('3C:84:6A', 'Cisco')
    db.setdefault('44:65:0D', 'Ubiquiti')
    db.setdefault('9C:5C:8E', 'Huawei')
    db.setdefault('BC:30:7D', 'Netgear')
    db.setdefault('D4:35:1D', 'Xiaomi')
    return db


@lru_cache(maxsize=4096)
def oui_lookup(mac: str) -> str:
    if not mac:
        return ''
    mac = mac.strip().upper().replace('-', ':')
    if not re.match(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$", mac):
        return ''
    prefix = ':'.join(mac.split(':')[:3])
    db = _load_oui()
    return db.get(prefix, '')
