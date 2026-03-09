import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'wifi_security.db')


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ssid TEXT,
            bssid TEXT,
            signal INTEGER,
            channel TEXT,
            security TEXT,
            encryption TEXT,
            vendor TEXT,
            frequency TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ssid TEXT,
            bssid TEXT,
            signal INTEGER,
            channel TEXT,
            security TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_networks(networks: List[Dict], scanned_at: Optional[datetime] = None):
    if not networks:
        return
    ts = (scanned_at or datetime.utcnow()).isoformat() + 'Z'
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany('''
        INSERT INTO networks (timestamp, ssid, bssid, signal, channel, security, encryption, vendor, frequency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [(
        ts,
        n.get('ssid'), n.get('bssid'), n.get('signal'), str(n.get('channel')) if n.get('channel') is not None else None,
        n.get('security'), n.get('encryption'), n.get('vendor'), n.get('frequency')
    ) for n in networks])
    conn.commit()
    conn.close()


def insert_history_snapshot(networks: List[Dict], scanned_at: Optional[datetime] = None):
    if not networks:
        return
    ts = (scanned_at or datetime.utcnow()).isoformat() + 'Z'
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany('''
        INSERT INTO history (timestamp, ssid, bssid, signal, channel, security)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [(
        ts,
        n.get('ssid'), n.get('bssid'), n.get('signal'), str(n.get('channel')) if n.get('channel') is not None else None,
        n.get('security')
    ) for n in networks])
    conn.commit()
    conn.close()


def get_latest_networks(limit: int = 200) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM networks ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_history(limit: int = 200) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM history ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
