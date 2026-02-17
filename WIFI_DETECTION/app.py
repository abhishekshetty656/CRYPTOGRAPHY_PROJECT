from flask import Flask, render_template
from wifi_scanner import scan_networks, detect_suspicious

app = Flask(__name__)

@app.route("/")
def index():
    networks = scan_networks()

    # Safety check
    if networks is None:
        networks = []

    suspicious_networks = detect_suspicious(networks)

    return render_template(
        "index.html",
        networks=networks,
        suspicious=suspicious_networks
    )

if __name__ == "__main__":
    app.run(debug=True)
