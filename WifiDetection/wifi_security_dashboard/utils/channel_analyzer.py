from collections import Counter
from typing import List, Dict


def analyze_channels(networks: List[Dict]) -> Dict:
    counts = Counter()
    for n in networks:
        ch = n.get('channel')
        if ch is None:
            continue
        try:
            ch = int(str(ch).strip())
        except ValueError:
            continue
        counts[ch] += 1
    return {
        'channels': list(counts.keys()),
        'counts': [counts[c] for c in counts.keys()]
    }
