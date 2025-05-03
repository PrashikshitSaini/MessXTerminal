import socket
import threading
import logging
import datetime

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 9000
LOG_FILE = 'server.log'
MAX_CLIENTS = 10

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Server State ---
clients = {}
client_lock = threading.Lock()

# --- Helper Functions ---
def broadcast(message, sender_conn=None):
    """Sends a message to all clients, optionally excluding the sender."""
    with client_lock:
        if not message.startswith("**"):
             logging.info(message)
        for name, conn in clients.items():
            if conn != sender_conn:
                try:
                    conn.sendall(message.encode('utf-8'))
                except socket.error:
                    pass

def log_event(message):
    """Logs an event with a timestamp."""
    logging.info(f"{datetime.datetime.now()} - {message}")

# --- Client Handling ---
def handle_client(conn, addr):
    """Handles a single client connection."""
    client_ip, client_port = addr
    name = None
    try:
        name_bytes = conn.recv(1024)
        if not name_bytes:
            logging.info(f"Connection attempt from {client_ip}:{client_port} with no name provided. Closing.")
            return

        name = name_bytes.decode('utf-8').strip()

        log_msg_prefix = f"Connection from {client_ip}:{client_port}, Name='{name}'"
        if not name:
            error_msg = "Rejected - Name cannot be blank."
            logging.warning(f"{log_msg_prefix} - {error_msg}")
            conn.sendall(f"ERROR: {error_msg}".encode('utf-8'))
            return
        with client_lock:
            # --- This is the duplicate name check ---
            if name in clients:
                error_msg = "Rejected - Name already in use."
                logging.warning(f"{log_msg_prefix} - {error_msg}")
                conn.sendall(f"ERROR: {error_msg}".encode('utf-8'))
                return # Exit the handler function, rejecting the client
            # --- End of duplicate name check ---

        logging.info(f"{log_msg_prefix} - Accepted.")
        conn.sendall("OK".encode('utf-8'))

        with client_lock:
            clients[name] = conn
        join_msg = f"** {name} is joining the chat **"
        log_event(f"** {name} joined from {client_ip}:{client_port} **")
        broadcast(join_msg)

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                broadcast_msg = f"[{name}] {message}"
                broadcast(broadcast_msg, conn)
            except ConnectionResetError:
                break
            except Exception as e:
                logging.error(f"Error receiving data from {name}: {e}")
                break

    except Exception as e:
        logging.error(f"Error handling client {addr}: {e}")

    finally:
        if name:
            with client_lock:
                if name in clients:
                    del clients[name]
            leave_msg = f"** {name} is leaving the chat **"
            log_event(f"** {name} left ({client_ip}:{client_port}) **")
            broadcast(leave_msg)
        if conn:
            conn.close()
        logging.info(f"Connection closed for {addr}")


# --- Main Server Logic ---
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_CLIENTS)
        logging.info(f"Server listening on {HOST}:{PORT}")

        while True:
            try:
                conn, addr = server_socket.accept()
                logging.info(f"New connection attempt from {addr}")
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

    except OSError as e:
        logging.error(f"Could not bind to port {PORT}: {e}")
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
    finally:
        server_socket.close()
        logging.info("Server socket closed.")

if __name__ == "__main__":
    start_server()
