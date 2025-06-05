import os
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app)

DB_NAME = 'chat.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/messages')
def get_messages():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT username, message, timestamp FROM messages ORDER BY id DESC LIMIT 50')
    messages = c.fetchall()
    conn.close()
    # Return as list of dicts (JSON will serialize)
    messages = [{'username': m[0], 'message': m[1], 'timestamp': m[2]} for m in reversed(messages)]
    return {'messages': messages}

@socketio.on('send_message')
def handle_send_message(data):
    username = data.get('username', 'Anonymous')
    message = data.get('message', '')
    if message.strip() == '':
        return
    # Save to DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO messages (username, message) VALUES (?, ?)', (username, message))
    conn.commit()
    conn.close()
    # Broadcast to all
    emit('receive_message', {'username': username, 'message': message}, broadcast=True)

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000)