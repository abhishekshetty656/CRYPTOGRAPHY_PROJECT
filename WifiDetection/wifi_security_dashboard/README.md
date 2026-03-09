Wi‑Fi Security Dashboard
=========================

A professional cybersecurity dashboard for real Wi‑Fi monitoring and Evil Twin detection. Cross‑platform: Windows and Linux. Real‑time updates via WebSockets, analytics with Chart.js, and persistent history in SQLite.

Highlights
- Real Wi‑Fi network scanning (no mock data)
  - Windows: netsh wlan show networks mode=bssid
  - Linux: nmcli device wifi list
- Live connection status
  - Connected Wi‑Fi SSID + BSSID, local IP, gateway, DNS, interface, type
  - Ethernet interfaces: speed, status, IP, packet counters
  - Internet reachability check with latency (TCP to common endpoints)
- Evil Twin detection
  - Duplicate SSIDs with different BSSIDs, stronger signal duplicates, open variant mimicry
  - Risk levels: LOW, MEDIUM, HIGH
- Live analytics and graphs (Chart.js)
  - Signal strength history (top networks)
  - Channel congestion analyzer
  - Security distribution (Open/WPA2/WPA3, etc.)
- Security alerts panel
- Network history stored in SQLite
- Export reports: CSV and JSON
- REST API: /api/networks, /api/current, /api/suspicious, /api/history

Project structure
```
wifi_security_dashboard/
  app.py
  scanner/
    wifi_scanner.py          # OS-level scanning (netsh/nmcli) and parsing
    network_info.py          # Current Wi‑Fi/Ethernet info, gateway/DNS, LAN scan, internet check
    evil_twin_detector.py    # Suspicion logic and risk scoring
  database/
    models.py                # SQLite schema and data access
  static/
    css/
      style.css
    js/
      charts.js
      dashboard.js           # WebSocket client and UI updates
  templates/
    dashboard.html           # Tailwind-based dark SOC UI
  utils/
    mac_vendor_lookup.py     # OUI lookup with local fallback
    channel_analyzer.py      # Channel congestion analysis
  requirements.txt
  README.md
```

Quick start
1) Open a terminal in wifi_security_dashboard/

2) Create a virtual environment and install dependencies
- Windows (PowerShell):
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1
  - pip install -r requirements.txt
- Linux:
  - python3 -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt

3) Platform prerequisites
- Windows: netsh is built-in. Ensure WLAN AutoConfig service (WlanSvc) is running. For best results, run terminal as Administrator.
- Linux: Ensure NetworkManager is installed and the Wi‑Fi interface is managed by it (nmcli must work). Example for Debian/Ubuntu: sudo apt-get install network-manager

4) Run the server
- python app.py

5) Open the dashboard
- http://localhost:5000

Environment variables (optional)
- SCAN_INTERVAL: Scan cadence in seconds (default 5). Example: set SCAN_INTERVAL=10 (Windows), export SCAN_INTERVAL=10 (Linux)
- PORT: Server port (default 5000)
- FLASK_SECRET: Session secret (default dev-secret)

REST API
- GET /api/networks
  - Recent networks with fields: timestamp, ssid, bssid, signal, channel, security, encryption, vendor, frequency
- GET /api/current
  - { current: {...}, ethernet: {...}, internet: {...} }
    - current: connected_ssid, router_bssid, ip_address, gateway, dns_server[], local_mac, interface, network_type
    - ethernet: interfaces[] with interface, speed, status, ip, packets_sent, packets_recv
    - internet: { online: bool, target: "host:port", latency_ms: int? }
- GET /api/suspicious
  - Array of evil twin suspicions: { ssid, bssids[], count, has_open_variant, strong_signal_variant, risk }
- GET /api/history
  - Recent network history snapshots, for trend analysis

Exports
- GET /export/csv → downloads networks.csv (recent records)
- GET /export/json → downloads networks.json (recent records)

How it works
- A background thread scans every SCAN_INTERVAL seconds:
  - Windows: netsh wlan show networks mode=bssid
  - Linux: nmcli -t -f SSID,BSSID,CHAN,SIGNAL,SECURITY,FREQ device wifi list
- Results are enriched with vendor (OUI), frequency band inference, and pushed to the browser via WebSockets.
- Data is stored in SQLite for history and export.

Internet connectivity card
- Performs a quick TCP connect to multiple endpoints (1.1.1.1:53, 8.8.8.8:53, 9.9.9.9:53, www.google.com:80)
- Shows Online/Offline and, when Online, the target and round-trip latency (ms)
- This indicates actual reachability, separate from Wi‑Fi/Ethernet link state

Troubleshooting
Windows
1) Verify the OS returns scan results:
   - netsh wlan show networks mode=bssid
   - If you see “There is no wireless interface on the system.” → No Wi‑Fi adapter is present
   - If you see “The Wireless AutoConfig Service (wlansvc) is not running.” → Start it: net start WlanSvc
   - If nothing appears, ensure Wi‑Fi is ON and not in airplane mode
2) Verify Wi‑Fi interface details:
   - netsh wlan show interfaces (should show SSID/BSSID when connected)
3) Locale (non‑English netsh output):
   - The parser looks for English headings (SSID, BSSID, Signal, Channel, Authentication, Encryption)
   - If your system uses another language, update scanner/wifi_scanner.py headings accordingly
4) Virtual machines:
   - NAT adapters typically don’t expose nearby SSIDs. Use a bridged Wi‑Fi adapter or run on the host OS

Linux
1) Ensure NetworkManager and nmcli are available:
   - nmcli device wifi list (should list SSIDs/BSSIDs)
2) Interface management:
   - If managed by wpa_supplicant or other tools, nmcli may not show data; consider switching to NetworkManager or adapting the scanner

General
- Use the browser DevTools → Console to see any scan_error messages
- Run the server with debug to surface stack traces:
  - Windows (PowerShell): $env:FLASK_DEBUG=1; python app.py
  - Linux: export FLASK_DEBUG=1; python app.py

Database
- SQLite file: database/wifi_security.db
- Tables:
  - networks(timestamp, ssid, bssid, signal, channel, security, encryption, vendor, frequency)
  - history(timestamp, ssid, bssid, signal, channel, security)
- You can inspect with any SQLite client

Vendor (OUI) lookup
- utils/mac_vendor_lookup.py contains a lightweight fallback map
- Optionally provide utils/oui.txt to expand coverage
  - Format per line: PREFIX VendorName (e.g., FC:EC:DA Apple)

Security & deployment notes
- Flask-SocketIO uses default threading; for higher concurrency you can add eventlet or gevent in production
- Consider running behind a reverse proxy (e.g., Nginx) and enabling HTTPS for remote access
- Some operations benefit from elevated privileges depending on OS and network stack configuration

Known limitations
- Scanning depends on OS tools (netsh/nmcli); features vary by adapter/driver and environment
- Hidden SSIDs and some enterprise networks may expose limited metadata
- VM environments may not present the radio layer to the guest

License
- For internal security monitoring and educational use. Validate compliance with local policies and regulations when scanning networks.
