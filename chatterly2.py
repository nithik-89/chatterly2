from flask import Flask, request, redirect, url_for, render_template_string, session, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import os

# ---------------- Flask setup ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DB_FILE = "chat.db"

# ---------------- Database setup ----------------
def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_FILE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )""")
        db.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message TEXT NOT NULL
        )""")
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

# ---------------- User class ----------------
class User(UserMixin):
    def __init__(self, id_, username):
        self.id = id_
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if user:
        return User(user['id'], user['username'])
    return None

# ---------------- Routes ----------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

# ---------- Register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        try:
            db.execute("INSERT INTO users(username,password) VALUES(?,?)", (username, password))
            db.commit()
            return redirect(url_for('login'))
        except:
            return "<h3>Username already exists. Try again.</h3>"
    return render_template_string('''
    <h1>Chatterly - Register</h1>
    <form method="post">
      Username: <input type="text" name="username" required><br>
      Password: <input type="password" name="password" required><br>
      <input type="submit" value="Register">
    </form>
    <p>Already have an account? <a href="/login">Login</a></p>
    ''')

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        if user:
            login_user(User(user['id'], user['username']))
            return redirect(url_for('chat'))
        return "<h3>Invalid credentials. Try again.</h3>"
    return render_template_string('''
    <h1>Chatterly - Login</h1>
    <form method="post">
      Username: <input type="text" name="username" required><br>
      Password: <input type="password" name="password" required><br>
      <input type="submit" value="Login">
    </form>
    <p>Don't have an account? <a href="/register">Register</a></p>
    ''')

# ---------- Logout ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------- Chat ----------
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    db = get_db()
    users = db.execute("SELECT username FROM users WHERE username!=?", (current_user.username,)).fetchall()
    users = [u['username'] for u in users]

    chat_with = request.args.get('user')
    messages = []
    if chat_with:
        messages = db.execute(
            "SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id",
            (current_user.username, chat_with, chat_with, current_user.username)
        ).fetchall()

    if request.method == 'POST':
        msg = request.form['message']
        receiver = request.form['receiver']
        if msg and receiver:
            db.execute("INSERT INTO messages(sender,receiver,message) VALUES(?,?,?)",
                       (current_user.username, receiver, msg))
            db.commit()
            return redirect(url_for('chat', user=receiver))

    return render_template_string('''
    <h1>Chatterly - Chat</h1>
    <p>Logged in as {{current_user.username}} | <a href="/logout">Logout</a></p>
    <h3>Users:</h3>
    <ul>
    {% for user in users %}
      <li><a href="{{url_for('chat', user=user)}}">{{user}}</a></li>
    {% endfor %}
    </ul>

    {% if chat_with %}
      <h3>Chat with {{chat_with}}</h3>
      <div style="border:1px solid #000;padding:10px;height:300px;overflow-y:scroll;">
      {% for m in messages %}
        <p><b>{{m['sender']}}:</b> {{m['message']}}</p>
      {% endfor %}
      </div>
      <form method="post">
        <input type="hidden" name="receiver" value="{{chat_with}}">
        <input type="text" name="message" placeholder="Type your message" required>
        <input type="submit" value="Send">
      </form>
    {% else %}
      <p>Select a user to start chatting.</p>
    {% endif %}
    ''', users=users, chat_with=chat_with, messages=messages)

# ---------------- Run App ----------------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000, debug=True)
