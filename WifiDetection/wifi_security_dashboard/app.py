import os
import json
import platform
import sqlite3
from datetime import datetime
from threading import Thread, Event
from queue import Queue, Empty

from flask import Flask, render_template, jsonify, send_file, Response
from flask_socketio import SocketIO

from scanner.wifi_scanner import scan_wifi_networks
from scanner.network_info import get_current_network_info, get_ethernet_info, scan_lan_devices, check_internet
from scanner.evil_twin_detector import detect_evil_twins
from database.models import init_db, insert_networks, get_latest_networks, get_history, insert_history_snapshot
from utils.channel_analyzer import analyze_channels
from utils.mac_vendor_lookup import oui_lookup

APP_TITLE = "Wi-Fi Security Dashboard"
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", 5))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'dev-secret')
socketio = SocketIO(app, cors_allowed_origins='*')

stop_event = Event()
scan_queue: Queue = Queue()


def background_scanner():
    while not stop_event.is_set():
        try:
            networks = scan_wifi_networks()
            # Enrich with vendor and frequency
            for n in networks:
                n['vendor'] = oui_lookup(n.get('bssid'))
                # infer band if missing
                if 'frequency' not in n or not n['frequency']:
                    ch = n.get('channel')
                    try:
                        ch_int = int(str(ch).strip()) if ch is not None else None
                    except ValueError:
                        ch_int = None
                    if ch_int is not None:
                        if 1 <= ch_int <= 14:
                            n['frequency'] = '2.4GHz'
                        else:
                            n['frequency'] = '5GHz'
            suspicious = detect_evil_twins(networks)
            channel_stats = analyze_channels(networks)
            now = datetime.utcnow()

            # Persist to DB
            insert_networks(networks, scanned_at=now)
            insert_history_snapshot(networks, scanned_at=now)

            payload = {
                'timestamp': now.isoformat() + 'Z',
                'networks': networks,
                'suspicious': suspicious,
                'channel_stats': channel_stats,
                'current': get_current_network_info(),
                'ethernet': get_ethernet_info(),
                'internet': check_internet(),
            }
            scan_queue.put(payload)
            socketio.emit('scan_update', payload)
        except Exception as e:
            socketio.emit('scan_error', {'error': str(e)})
        stop_event.wait(SCAN_INTERVAL)


@app.route('/')
def dashboard():
    return render_template('dashboard.html', app_title=APP_TITLE)


@app.route('/api/networks')
def api_networks():
    return jsonify(get_latest_networks(limit=200))


@app.route('/api/current')
def api_current():
    return jsonify({
        'current': get_current_network_info(),
        'ethernet': get_ethernet_info(),
        'internet': check_internet(),
    })


@app.route('/api/suspicious')
def api_suspicious():
    nets = get_latest_networks(limit=500)
    return jsonify(detect_evil_twins(nets))


@app.route('/api/history')
def api_history():
    return jsonify(get_history(limit=100))


@app.route('/export/csv')
def export_csv():
    nets = get_latest_networks(limit=1000)
    # Create CSV in-memory
    headers = ['timestamp','ssid','bssid','signal','channel','security','encryption','vendor','frequency']
    lines = [','.join(headers)]
    for n in nets:
        row = [
            str(n.get('timestamp','')),
            '"%s"' % str(n.get('ssid','')).replace('"','""'),
            str(n.get('bssid','')),
            str(n.get('signal','')),
            str(n.get('channel','')),
            str(n.get('security','')),
            str(n.get('encryption','')),
            str(n.get('vendor','')),
            str(n.get('frequency','')),
        ]
        lines.append(','.join(row))
    data = '\n'.join(lines)
    return Response(data, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=networks.csv'})


@app.route('/export/json')
def export_json():
    nets = get_latest_networks(limit=1000)
    return Response(json.dumps(nets, indent=2), mimetype='application/json', headers={'Content-Disposition': 'attachment; filename=networks.json'})


def main():
    init_db()
    t = Thread(target=background_scanner, daemon=True)
    t.start()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


if __name__ == '__main__':
    main()
