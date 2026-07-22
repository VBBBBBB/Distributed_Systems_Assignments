"""
=============================================================
  Distributed Systems Assignment
  TCP Socket Client
=============================================================
  HOW TO RUN (on the CLIENT laptop):
    python client.py

  When prompted, enter the SERVER's IP address.
  (Ask your friend to run `ipconfig` and share their IPv4 address)

  Commands:
    /quit  — Disconnect from the server
=============================================================
"""

import socket
import threading
import sys

# ── Configuration ─────────────────────────────────────────
DEFAULT_HOST = "127.0.0.1"  # Change to server's LAN IP when running across laptops
PORT = 5050
BUFFER_SIZE = 1024
# ──────────────────────────────────────────────────────────

connected = True  # Global flag to coordinate threads


def receive_messages(client_socket: socket.socket) -> None:
    """
    Runs in a background thread.
    Continuously listens for messages from the server and prints them.
    """
    global connected
    while connected:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                print("\n[CLIENT] Server closed the connection.")
                connected = False
                break
            print(f"\r{data.decode('utf-8')}\n> ", end="", flush=True)
        except OSError:
            if connected:
                print("\n[CLIENT] Lost connection to server.")
            connected = False
            break


def start_client() -> None:
    """Connect to the server and start the send/receive loops."""
    global connected

    print("=" * 55)
    print("  Distributed Systems — TCP Socket Client")
    print("=" * 55)

    # Let user pick the server IP at runtime
    host = input(f"  Enter server IP address [{DEFAULT_HOST}]: ").strip()
    if not host:
        host = DEFAULT_HOST

    print(f"  Connecting to {host}:{PORT} ...")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((host, PORT))
    except ConnectionRefusedError:
        print(f"\n[ERROR] Could not connect to {host}:{PORT}.")
        print("  Make sure the server is running and the IP/port is correct.")
        sys.exit(1)
    except OSError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    print(f"  Connected! Type messages and press Enter to send.")
    print("  Type /quit to exit.")
    print("=" * 55)

    # Start background thread to receive messages
    recv_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
    recv_thread.start()

    # Main thread handles user input
    try:
        while connected:
            user_input = input("> ").strip()
            if not user_input:
                continue

            try:
                client_socket.sendall(user_input.encode("utf-8"))
            except OSError:
                print("[CLIENT] Failed to send message.")
                break

            if user_input.lower() in ("/quit", "/exit", "/q"):
                connected = False
                break

    except (KeyboardInterrupt, EOFError):
        print("\n[CLIENT] Disconnecting...")
        connected = False

    finally:
        client_socket.close()
        print("[CLIENT] Disconnected.")


if __name__ == "__main__":
    start_client()
