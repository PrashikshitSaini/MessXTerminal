import socket
import threading
import sys
import select

def display_message(message):
    sys.stdout.write('\r' + ' ' * (len(prompt) + len(current_input)) + '\r')
    print(message)
    sys.stdout.write(prompt + current_input)
    sys.stdout.flush()

def connect_to_server(server_ip, server_port, name):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10.0)
    try:
        print(f"Attempting to connect to {server_ip}:{server_port}...")
        client_socket.connect((server_ip, server_port))
        client_socket.settimeout(None)
        print(f"Connection established. Sending name '{name}'...")
        client_socket.sendall(name.encode('utf-8'))

        client_socket.settimeout(5.0)
        response = client_socket.recv(1024).decode('utf-8')
        client_socket.settimeout(None)

        if response.startswith("ERROR:"):
            print(f"Server rejected connection: {response}")
            client_socket.close()
            return None
        elif response.startswith("OK"):
            print("Connected successfully!")
            remainder = response[len("OK"):].strip()
            if remainder:
                print(remainder)
            return client_socket
        else:
            print(f"Unexpected response from server: {response}")
            client_socket.close()
            return None

    except socket.timeout:
        print(f"Connection attempt timed out. Check server IP and firewall.")
        client_socket.close()
        return None
    except socket.error as e:
        print(f"Failed to connect to server {server_ip}:{server_port} - {e}")
        client_socket.close()
        return None
    except Exception as e:
        print(f"An error occurred during connection: {e}")
        if client_socket:
            client_socket.close()
        return None

def receive_messages(sock):
    global running
    while running:
        try:
            ready_to_read, _, _ = select.select([sock], [], [], 0.1)
            if ready_to_read:
                data = sock.recv(1024)
                if not data:
                    display_message("\nServer disconnected.")
                    running = False
                    break
                message = data.decode('utf-8')
                display_message(message)
        except socket.error:
            display_message("\nConnection error with the server.")
            running = False
            break
        except Exception as e:
            if running:
                print(f"\nError receiving data: {e}")
            running = False
            break
    print("Receive thread finished.")

def send_messages(sock, name):
    global running
    global current_input
    while running:
        try:
            sys.stdout.write(prompt)
            sys.stdout.flush()

            current_input = input()

            if not running:
                break

            if current_input.strip() == "@exit":
                print("DEBUG: Exiting.") # Added
                running = False
                break
            elif current_input:
                # print(f"DEBUG: Sending: '{current_input}'") # Added
                try:
                    sock.sendall(current_input.encode('utf-8'))
                    # print("DEBUG: Sent successfully.") # Added
                except socket.error as send_err:
                    # Log if sendall itself fails
                    print(f"DEBUG: Error during sendall: {send_err}") # Added
                    raise 
            current_input = ""

        except EOFError:
            print("\nExiting due to EOF.")
            running = False
            break
        except KeyboardInterrupt:
            print("\nExiting due to KeyboardInterrupt.")
            running = False
            break
        except socket.error as e:
            # This will catch errors from input or the re-raised sendall error
            print(f"\nFailed to send message: {e}")
            running = False
            break
        except Exception as e:
            print(f"\nError sending message: {e}")
            running = False
            break

    print("Send thread finished. Closing connection...")
    if running:
        running = False
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except socket.error:
        pass
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <name>")
        sys.exit(1)

    server_ip = sys.argv[1]
    name = sys.argv[2]
    server_port = 9000

    if not name:
        print("Error: Name cannot be blank.")
        sys.exit(1)
    if ' ' in name:
        print("Error: Name cannot contain spaces.")
        sys.exit(1)

    client_socket = connect_to_server(server_ip, server_port, name)

    if client_socket:
        running = True
        prompt = f"{name}> "
        current_input = ""

        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
        send_thread = threading.Thread(target=send_messages, args=(client_socket, name))

        receive_thread.start()
        send_thread.start()

        send_thread.join()

        running = False
        receive_thread.join(timeout=1.0)

        print("Client program finished.")
    else:
        print("Could not establish connection. Exiting.")
        sys.exit(1)
