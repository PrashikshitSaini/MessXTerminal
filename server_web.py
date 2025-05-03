# Flask-based web server for chat application
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import datetime, logging
import sys
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

app = Flask(__name__)
app.logger.setLevel(logging.ERROR)  # Reduce Flask logging level
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

# Chat logging setup
chat_logger = logging.getLogger('chat')
chat_logger.setLevel(logging.INFO)
chat_handler = logging.FileHandler('logs/chat.log')
chat_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
chat_logger.addHandler(chat_handler)
chat_logger.propagate = False

# Server logging setup
server_logger = logging.getLogger('server')
server_logger.setLevel(logging.INFO)
server_handler = logging.FileHandler('logs/server.log')
server_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
server_logger.addHandler(server_handler)
server_logger.propagate = False

# Track connected users
users = {}

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def on_connect():
    server_logger.info(f"New connection from {request.remote_addr}")
    # Initial connection - don't send history yet
    pass

@socketio.on("join")
def on_join(data):
    # User has selected a username
    username = data.get('username', '').strip()
    sid = request.sid
    
    # Validate username
    if not username:
        emit("system_message", {"message": "Error: Username cannot be empty"})
        return
    
    if username in users.values():
        emit("system_message", {"message": "Error: Username already taken"})
        return
    
    # Store the user
    users[sid] = username
    
    # Announce the new user to everyone (terminal style)
    join_msg = f"** {username} is joining the chat **"
    chat_logger.info(join_msg)
    server_logger.info(f"User '{username}' connected from {request.remote_addr}")
    
    # Send join message to all users (including the one joining)
    socketio.emit("chat_message", {"sender": "System", "message": join_msg})
    
    # Send chat history to the new user
    try:
        with open("logs/chat.log") as f:
            history_lines = []
            for line in f:
                line_text = line.strip()
                # Skip server logs
                if (not "/socket.io" in line_text and
                    not "GET /" in line_text and
                    not "POST /" in line_text and
                    not "HTTP" in line_text and
                    not "transport=polling" in line_text and
                    not "Running on" in line_text and
                    not "WARNING:" in line_text and
                    not "Press CTRL+C" in line_text):
                    history_lines.append(line_text)
            
            # Only send the last 20 lines of history to avoid overwhelming the client
            for line_text in history_lines[-20:]:
                emit("chat_message", {"sender": "History", "message": line_text})
    except FileNotFoundError:
        pass
    
    # Send welcome message only to the joining user
    emit("system_message", {"message": f"Welcome, {username}! You are now connected."})

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    if sid in users:
        username = users[sid]
        leave_msg = f"** {username} is leaving the chat **"
        chat_logger.info(leave_msg)
        server_logger.info(f"User '{username}' disconnected")
        socketio.emit("chat_message", {"sender": "System", "message": leave_msg})
        del users[sid]

@socketio.on("chat")
def on_chat(data):
    sid = request.sid
    message = data.get('message', '').strip()
    timestamp = data.get('timestamp', datetime.datetime.now().strftime('[%d/%m/%Y: %H:%M]'))
    
    if not message:
        return
        
    if sid in users:
        username = users[sid]
        chat_msg = f"{timestamp} [{username}] {message}"
        chat_logger.info(chat_msg)
        
        # Send message to ALL users INCLUDING the sender
        # The sender needs to see their own message from the server
        socketio.emit("chat_message", {
            "sender": username, 
            "message": message,
            "timestamp": timestamp
        })
    else:
        # User hasn't set username yet
        emit("system_message", {"message": "Please set a username first"})

@socketio.on("get_users")
def get_users():
    """Return list of connected users"""
    user_list = list(users.values())
    emit("user_list", {"users": user_list})

if __name__ == "__main__":
    # Disable flask debug logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Prevent Flask startup messages
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *args, **kwargs: None
    
    # Log server start
    server_logger.info("Secure server starting on port 9000 (HTTPS)")
    
    # Define certificate paths
    cert_path = os.path.join(os.path.dirname(__file__), 'certs', 'cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'certs', 'key.pem')
    
    # Check if certificates exist
    if os.path.exists(cert_path) and os.path.exists(key_path):
        # Start the server with SSL/TLS
        socketio.run(
            app, 
            host="0.0.0.0", 
            port=9000, 
            debug=False, 
            log_output=False,
            ssl_context=(cert_path, key_path)
        )
    else:
        server_logger.warning("SSL certificates not found. Running in unsecured mode!")
        # Start the server without SSL/TLS (unsecured)
        socketio.run(app, host="0.0.0.0", port=9000, debug=False, log_output=False)