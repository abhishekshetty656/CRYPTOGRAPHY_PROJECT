NovaGuard WiFi Sentinel — Fake WiFi Detection System

Overview
- Real-time detection of suspicious and fake WiFi networks (Evil Twins, Open nets, Unknown MAC vendors, abnormally strong signals).
- Backend: Flask (Python) with PyWiFi/Scapy scanning and graceful demo fallback.
- Frontend: Bootstrap + Chart.js, cyber-themed neon UI, animated radar and alerts.

Install
1) Create a virtual environment (Windows):
   python -m venv venv
   venv\Scripts\activate
2) Install dependencies:
   pip install -r requirements.txt
3) Run the server:
   python app.py
4) Open in browser:
   http://127.0.0.1:5000/

Notes
- Windows passive capture via Scapy is limited; PyWiFi scanning is preferred.
- If neither library returns data, demo mode provides sample networks so the UI remains functional.

Features
- Auto-refresh every 5s
- Risk scoring: duplicate SSID +40, open +30, unknown MAC +20, strong signal +10
- Labels: Safe (<30), Suspicious (30–59), Dangerous (60–100)
- Evil Twin alerts and red row highlights
- Logs persisted to data/attack_logs.json with timestamp, SSID, BSSID, attack type, risk
- Scanner has a toggle to show only the currently connected network

Ethics
- For educational/defensive use only. Respect laws and policies.
