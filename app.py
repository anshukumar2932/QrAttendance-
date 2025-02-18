from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import pandas as pd
import os
import hashlib
import segno
from io import BytesIO

app = Flask(__name__)

# Define folders
UPLOAD_FOLDER = "uploads"
QR_FOLDER = "qrcodes"
ATTENDANCE_FOLDER = "attendance"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)

attendance = {}
student_data = {}

def hash_r_number(r_number):
    return hashlib.sha256(str(r_number).encode()).hexdigest()

def generate_qr(data, filename, event_name):
    event_folder = os.path.join(QR_FOLDER, event_name)
    os.makedirs(event_folder, exist_ok=True)
    img_path = os.path.join(event_folder, filename)
    qr = segno.make(data)
    qr.save(img_path, scale=10)
    return img_path

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/generate')
def generate_page():
    return render_template('generate.html')

@app.route('/scan')
def scan_page():
    return render_template('scan.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    file = request.files.get('file')
    event_name = request.form.get('event_name')
    if not file or not event_name:
        return jsonify({"error": "File and event name are required"})
    
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
        student_data[row['QR_Hash']] = {'name': row['Name'], 'r_number': row['R Number']}
        generate_qr(row['QR_Hash'], f"{row['R Number']}.png", event_name)
    
    df.to_csv(filepath, index=False)
    return jsonify({"message": "QR Codes generated successfully"})

@app.route('/scan', methods=['POST'])
def scan_qr():
    data = request.json.get("qr_hash")
    event_name = request.json.get("event_name")
    if data and event_name:
        if event_name not in attendance:
            attendance[event_name] = set()
        attendance[event_name].add(data)
        student_info = student_data.get(data, {"name": "Unknown", "r_number": "Unknown"})
        return jsonify({"message": "Attendance marked", "name": student_info['name'], "r_number": student_info['r_number']})
    return jsonify({"error": "Invalid QR hash or missing event name"})

@app.route('/export', methods=['GET'])
def export_attendance():
    event_name = request.args.get("event_name")
    if not event_name or event_name not in attendance:
        return jsonify({"error": "Invalid event name"})
    
    df = pd.DataFrame({"QR_Hash": list(attendance[event_name])})
    attendance_file = os.path.join(ATTENDANCE_FOLDER, f"{event_name}_attendance.csv")
    df.to_csv(attendance_file, index=False)
    return send_file(attendance_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)


I've updated the system so that when a QR code is scanned, it will display the student's name and registration number. Let me know if you need any further modifications!

