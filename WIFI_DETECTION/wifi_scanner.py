import subprocess
import platform


def scan_networks():
    networks = []

    try:
        if platform.system().lower() == "windows":

            output = subprocess.check_output(
                "netsh wlan show networks mode=bssid",
                shell=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            current_ssid = None
            bssid = None
            signal = None

            for line in output.splitlines():
                line = line.strip()

                # SSID
                if line.startswith("SSID ") and "BSSID" not in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        current_ssid = parts[1].strip()
                        if not current_ssid:
                            current_ssid = "Hidden Network"

                # BSSID
                elif line.startswith("BSSID"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        bssid = parts[1].strip()

                # Signal
                elif line.startswith("Signal"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        signal = parts[1].strip()

                # Authentication
                elif line.startswith("Authentication"):
                    parts = line.split(":", 1)
                    security = parts[1].strip() if len(parts) > 1 else "Unknown"

                    # Add network after authentication line
                    networks.append({
                        "ssid": current_ssid,
                        "bssid": bssid,
                        "signal": signal,
                        "security": security
                    })

        else:
            # Linux/macOS
            output = subprocess.check_output(
                ["nmcli", "-f", "SSID,BSSID,SIGNAL,SECURITY", "device", "wifi", "list"],
                text=True
            )

            lines = output.strip().split("\n")[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    networks.append({
                        "ssid": parts[0],
                        "bssid": parts[1],
                        "signal": parts[2] + "%",
                        "security": " ".join(parts[3:])
                    })

    except Exception as e:
        print("Error scanning networks:", e)

    return networks


def detect_suspicious(networks):
    suspicious = []
    ssid_map = {}

    for net in networks:
        ssid = net["ssid"]

        if ssid not in ssid_map:
            ssid_map[ssid] = []
        ssid_map[ssid].append(net)

    for ssid, entries in ssid_map.items():

        # Evil Twin detection
        if len(entries) > 1:
            for net in entries:
                net["risk"] = "HIGH – Possible Evil Twin"
                suspicious.append(net)

        else:
            net = entries[0]

            try:
                signal_value = int(net["signal"].replace("%", ""))
            except:
                signal_value = 0

            if "Open" in net["security"]:
                net["risk"] = "MEDIUM – Open Network"
                suspicious.append(net)

            elif signal_value > 85:
                net["risk"] = "MEDIUM – Very Strong Signal"
                suspicious.append(net)

    return suspicious
