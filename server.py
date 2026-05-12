#!/usr/bin/env python3
"""
Suna Archives — Serveur Flask + SQLite
Usage : python3 server.py
API disponible sur http://localhost:5000
"""

import os
import sqlite3
import json
import base64
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime

# ─── Config ───────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, 'suna.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')
CORS(app)

ALLOWED_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ─── Base de données ──────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                number      TEXT    NOT NULL,
                title       TEXT    NOT NULL,
                rank        TEXT    NOT NULL DEFAULT 'B',
                date_mission TEXT,
                duration    TEXT,
                lieu        TEXT,
                statut      TEXT    DEFAULT 'Succès',
                body        TEXT    NOT NULL,
                created_at  TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key         TEXT PRIMARY KEY,
                value       TEXT
            );

            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('char_image', NULL);
        """)
        # Rapport exemple si table vide
        row = conn.execute("SELECT COUNT(*) as c FROM reports").fetchone()
        if row['c'] == 0:
            conn.execute("""
                INSERT INTO reports (number, title, rank, date_mission, duration, lieu, statut, body)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                '001',
                'Escorte du Kazekage',
                'A',
                'An 15 · 3ème mois',
                '3 jours',
                'Route Suna → Konoha',
                'Succès',
                "Mission d'escorte du cinquième Kazekage lors de son déplacement diplomatique vers le Village de Konoha.\n\nLe convoi a été intercepté au col de Tetsu par un groupe de trois nukenin appartenant à une faction inconnue. L'affrontement a duré vingt minutes. Les cibles ont été neutralisées sans pertes de notre côté.\n\nLe Kazekage est arrivé à destination sans encombre. La mission est considérée comme accomplie."
            ))
    print("✓ Base de données initialisée :", DB_PATH)

# ─── Routes statiques ─────────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(PUBLIC_DIR, 'admin.html')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ─── API Rapports ──────────────────────────────────────────
@app.route('/api/reports', methods=['GET'])
def get_reports():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY CAST(number AS INTEGER) ASC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/reports', methods=['POST'])
def create_report():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('body'):
        return jsonify({'error': 'title et body requis'}), 400

    # Auto-numéro si absent
    number = data.get('number', '').strip()
    if not number:
        with get_db() as conn:
            row = conn.execute("SELECT MAX(CAST(number AS INTEGER)) as m FROM reports").fetchone()
            number = str((row['m'] or 0) + 1).zfill(3)

    with get_db() as conn:
        cur = conn.execute("""
            INSERT INTO reports (number, title, rank, date_mission, duration, lieu, statut, body)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            number,
            data['title'],
            data.get('rank', 'B'),
            data.get('date_mission', ''),
            data.get('duration', ''),
            data.get('lieu', ''),
            data.get('statut', 'Succès'),
            data['body']
        ))
        new_id = cur.lastrowid
        report = conn.execute("SELECT * FROM reports WHERE id = ?", (new_id,)).fetchone()
    return jsonify(dict(report)), 201

@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        return jsonify({'error': 'Rapport introuvable'}), 404
    return jsonify(dict(row))

@app.route('/api/reports/<int:report_id>', methods=['PUT'])
def update_report(report_id):
    data = request.get_json()
    with get_db() as conn:
        conn.execute("""
            UPDATE reports
            SET number=?, title=?, rank=?, date_mission=?, duration=?, lieu=?, statut=?, body=?
            WHERE id=?
        """, (
            data.get('number'),
            data.get('title'),
            data.get('rank', 'B'),
            data.get('date_mission', ''),
            data.get('duration', ''),
            data.get('lieu', ''),
            data.get('statut', 'Succès'),
            data.get('body', ''),
            report_id
        ))
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        return jsonify({'error': 'Rapport introuvable'}), 404
    return jsonify(dict(row))

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Rapport introuvable'}), 404
        conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    return jsonify({'deleted': report_id})

# ─── API Image personnage ──────────────────────────────────
@app.route('/api/char-image', methods=['GET'])
def get_char_image():
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'char_image'").fetchone()
    val = row['value'] if row else None
    if val:
        return jsonify({'image_url': val})
    return jsonify({'image_url': None})

@app.route('/api/char-image', methods=['POST'])
def set_char_image():
    # Accept multipart file OR base64 JSON
    if 'file' in request.files:
        f = request.files['file']
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
        if ext not in ALLOWED_IMG:
            return jsonify({'error': 'Format non supporté'}), 400
        filename = f'char.{ext}'
        path = os.path.join(UPLOAD_DIR, filename)
        f.save(path)
        url = f'/uploads/{filename}'
    elif request.is_json:
        data = request.get_json()
        url = data.get('image_url', '')
    else:
        return jsonify({'error': 'Aucune donnée reçue'}), 400

    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('char_image', ?)",
            (url,)
        )
    return jsonify({'image_url': url})

# ─── API Infos ────────────────────────────────────────────
@app.route('/api/info')
def api_info():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM reports").fetchone()['c']
    return jsonify({
        'status': 'ok',
        'reports_count': count,
        'version': '1.0.0',
        'character': 'Ousen Zafura',
        'village': 'Sunagakure'
    })

# ─── Lancement ────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("╔══════════════════════════════════════════╗")
    print("║   🏜  Suna Archives — Serveur actif       ║")
    print("║                                          ║")
    print("║  Site public  →  http://localhost:5000   ║")
    print("║  Admin        →  http://localhost:5000/admin ║")
    print("║  API          →  http://localhost:5000/api   ║")
    print("╚══════════════════════════════════════════╝")
    app.run(host='0.0.0.0', port=5000, debug=True)
