import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'suna.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')
CORS(app)

ALLOWED_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL,
                title TEXT NOT NULL,
                rank TEXT DEFAULT '',
                date_mission TEXT,
                duration TEXT,
                lieu TEXT,
                statut TEXT DEFAULT 'Succes',
                body TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            INSERT OR IGNORE INTO settings (key, value) VALUES ('char_image', NULL);
        """)
        row = conn.execute("SELECT COUNT(*) as c FROM reports").fetchone()
        if row['c'] == 0:
            conn.execute(
                "INSERT INTO reports (number, title, rank, date_mission, duration, lieu, statut, body) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ('001', 'Escorte du Kazekage', 'A', 'An 15 - 3eme mois', '3 jours', 'Route Suna vers Konoha', 'Succes', 'Mission escorte du Kazekage accomplie avec succes.')
            )

@app.route('/')
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(PUBLIC_DIR, 'admin.html')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/api/reports', methods=['GET'])
def get_reports():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM reports ORDER BY CAST(number AS INTEGER) ASC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/reports', methods=['POST'])
def create_report():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('body'):
        return jsonify({'error': 'title et body requis'}), 400
    number = data.get('number', '').strip()
    if not number:
        with get_db() as conn:
            row = conn.execute("SELECT MAX(CAST(number AS INTEGER)) as m FROM reports").fetchone()
            number = str((row['m'] or 0) + 1).zfill(3)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO reports (number, title, rank, date_mission, duration, lieu, statut, body) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (number, data['title'], data.get('rank', ''), data.get('date_mission', ''), data.get('duration', ''), data.get('lieu', ''), data.get('statut', 'Succes'), data['body'])
        )
        report = conn.execute("SELECT * FROM reports WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(report)), 201

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Rapport introuvable'}), 404
        conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    return jsonify({'deleted': report_id})

@app.route('/api/char-image', methods=['GET'])
def get_char_image():
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'char_image'").fetchone()
    val = row['value'] if row else None
    return jsonify({'image_url': val})

@app.route('/api/char-image', methods=['POST'])
def set_char_image():
    if 'file' in request.files:
        f = request.files['file']
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
        if ext not in ALLOWED_IMG:
            return jsonify({'error': 'Format non supporte'}), 400
        filename = 'char.' + ext
        f.save(os.path.join(UPLOAD_DIR, filename))
        url = '/uploads/' + filename
    elif request.is_json:
        url = request.get_json().get('image_url', '')
    else:
        return jsonify({'error': 'Aucune donnee recue'}), 400
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('char_image', ?)", (url,))
    return jsonify({'image_url': url})

@app.route('/api/info')
def api_info():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM reports").fetchone()['c']
    return jsonify({'status': 'ok', 'reports_count': count})

init_db()
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
