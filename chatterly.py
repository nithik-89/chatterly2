# chatterly.py

from flask import Flask, render_template_string, request, redirect, url_for, flash, g
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DB_PATH = "chat.db"  # For demo; switch to PostgreSQL for production

def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        username TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT,
        created_at TEXT
    );
    """)
    db.commit()

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db:
        db.close()

class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.email = row["email"]
        self.username = row["username"]

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return User(row) if row else None

BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Chatterly</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body { padding-top: 70px; }
.messages { height: 300px; overflow:auto; border:1px solid #ccc; padding:10px; background:#f8f9fa; border-radius:5px; }
.msg { margin-bottom:8px; }
.username { font-weight:600; }
</style>
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
<div class="container-fluid">
  <a class="navbar-brand" href="{{ url_for('index') }}">Chatterly</a>
  <div class="collapse navbar-collapse">
    <ul class="navbar-nav ms-auto">
      {% if current_user.is_authenticated %}
        <li class="nav-item"><span class="nav-link">Hi, {{ current_user.username or current_user.email }}</span></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('logout') }}">Logout</a></li>
      {% else %}
        <li class="nav-item"><a class="nav-link" href="{{ url_for('register') }}">Register</a></li>
        <li class="nav-item"><a class="nav-link" href="{{ url_for('login') }}">Login</a></li>
      {% endif %}
    </ul>
  </div>
</div>
<div class="container mt-5">
"""

# --- Routes (same as previous version) ---
# index, register, login, logout, chat routes remain unchanged
# For brevity, you can copy all route code from the previous single-file version

# --- Run App ---
if __name__=="__main__":
    with app.app_context():
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
