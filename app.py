from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import os
import hashlib
import segno
from io import BytesIO

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
QR_FOLDER = "qrcodes"
ATTENDANCE_FILE = "attendance.csv"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

attendance = set()

def hash_r_number(r_number):
    return hashlib.sha256(str(r_number).encode()).hexdigest()

def generate_qr(data, filename):
    qr = segno.make(data)
    img_path = os.path.join(QR_FOLDER, filename)
    qr.save(img_path, scale=10)
    return img_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    file = request.files['file']
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filepath)
        else:
            return jsonify({"error": "Unsupported file format"})
        
        df['QR_Hash'] = df['R Number'].apply(hash_r_number)
        for _, row in df.iterrows():
            generate_qr(row['QR_Hash'], f"{row['R Number']}.png")
        df.to_csv(filepath, index=False)
        return jsonify({"message": "QR Codes generated successfully"})
    return jsonify({"error": "File upload failed"})

@app.route('/scan', methods=['POST'])
def scan_qr():
    data = request.json.get("qr_hash")
    if data:
        attendance.add(data)
        return jsonify({"message": "Attendance marked"})
    return jsonify({"error": "Invalid QR hash"})

@app.route('/export', methods=['GET'])
def export_attendance():
    df = pd.DataFrame({"QR_Hash": list(attendance)})
    df.to_csv(ATTENDANCE_FILE, index=False)
    return send_file(ATTENDANCE_FILE, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
