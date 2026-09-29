"""
=============================================================
  Distributed Systems Assignment
  TCP Socket Server — Multi-Client Chat
=============================================================
  THEORY:
  A socket is an endpoint in a network communication. This server
  uses the TCP protocol (connection-oriented, reliable delivery).
  Each client gets its own thread so they can chat simultaneously.

  HOW TO RUN (on the SERVER laptop):
    python server.py

  Then share your local IP address with your friend (run `ipconfig`
  on Windows or `ifconfig` on Linux/Mac to find it).
=============================================================
"""

import socket
import threading
import datetime

# ── Configuration ─────────────────────────────────────────
HOST = "0.0.0.0"   # Listen on ALL network interfaces
PORT = 5050         # Port to listen on (make sure firewall allows this)
MAX_CLIENTS = 10    # Maximum simultaneous clients
BUFFER_SIZE = 1024  # Bytes per message
# ──────────────────────────────────────────────────────────

# Shared list of all connected (socket, address) pairs
clients: list[tuple[socket.socket, tuple]] = []
clients_lock = threading.Lock()


def timestamp() -> str:
    """Return current time as a short string."""
    return datetime.datetime.now().strftime("%H:%M:%S")


def broadcast(message: str, sender_socket: socket.socket | None = None) -> None:
    """
    Send `message` to every connected client except the sender.
    If sender_socket is None, the message is sent to ALL clients (e.g. system notices).
    """
    with clients_lock:
        dead_clients = []
        for client_sock, addr in clients:
            if client_sock == sender_socket:
                continue  # Don't echo back to sender
            try:
                client_sock.sendall(message.encode("utf-8"))
            except OSError:
                # Client disconnected unexpectedly
                dead_clients.append((client_sock, addr))

        # Clean up dead connections
        for dead in dead_clients:
            clients.remove(dead)
            dead[0].close()
            print(f"[SERVER] Removed dead client {dead[1]}")


def handle_client(client_socket: socket.socket, address: tuple) -> None:
    """
    Dedicated thread for each connected client.
    Receives messages and broadcasts them to everyone else.
    """
    print(f"[{timestamp()}] [+] New connection from {address[0]}:{address[1]}")

    # Ask client for a username
    client_socket.sendall("[SERVER] Welcome! Enter your username: ".encode("utf-8"))
    try:
        username = client_socket.recv(BUFFER_SIZE).decode("utf-8").strip()
        if not username:
            username = f"User_{address[1]}"
    except OSError:
        client_socket.close()
        return

    join_msg = f"[{timestamp()}] 🔵 {username} joined the chat from {address[0]}"
    print(join_msg)
    broadcast(join_msg, sender_socket=client_socket)
    client_socket.sendall(f"[SERVER] Hello {username}! You are connected. Start chatting!\n".encode("utf-8"))

    # Main message loop
    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                # Empty data = client closed connection gracefully
                break

            message = data.decode("utf-8").strip()

            if message.lower() in ("/quit", "/exit", "/q"):
                client_socket.sendall("[SERVER] Goodbye!\n".encode("utf-8"))
                break

            formatted = f"[{timestamp()}] {username}: {message}"
            print(formatted)
            broadcast(formatted, sender_socket=client_socket)

        except OSError:
            break  # Socket error — client likely disconnected

    # Cleanup after client leaves
    with clients_lock:
        clients[:] = [(s, a) for s, a in clients if s != client_socket]
    client_socket.close()

    leave_msg = f"[{timestamp()}] 🔴 {username} left the chat."
    print(leave_msg)
    broadcast(leave_msg)


def start_server() -> None:
    """Initialize and run the TCP server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow reusing the port immediately after restart
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_CLIENTS)

    print("=" * 55)
    print("  Distributed Systems — TCP Socket Server")
    print("=" * 55)
    print(f"  Listening on  : {HOST}:{PORT}")
    print(f"  Max clients   : {MAX_CLIENTS}")
    print(f"  Buffer size   : {BUFFER_SIZE} bytes")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 55)

    try:
        while True:
            # Block until a new client connects
            client_sock, addr = server_socket.accept()

            with clients_lock:
                clients.append((client_sock, addr))

            # Spawn a daemon thread per client (dies when server exits)
            thread = threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True,
            )
            thread.start()
            print(f"[SERVER] Active connections: {len(clients)}")

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down gracefully...")
    finally:
        with clients_lock:
            for sock, _ in clients:
                sock.close()
        server_socket.close()
        print("[SERVER] Server stopped.")


if __name__ == "__main__":
    start_server()
