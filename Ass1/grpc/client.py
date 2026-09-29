"""
=============================================================
  Distributed Systems Assignment
  gRPC Chat Client
=============================================================
  HOW TO RUN (on the CLIENT laptop):
    1. pip install grpcio grpcio-tools
    2. python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto
       (or copy the chat_pb2.py and chat_pb2_grpc.py from server)
    3. python client.py

  When prompted, enter the server's IP address and choose a mode:
    [1] Unary     - Send one message, get one reply
    [2] Join      - Receive full message history (server-streaming)
    [3] LiveChat  - Real-time bidirectional chat
=============================================================
"""

import grpc
import threading
import sys
import time

try:
    import chat_pb2
    import chat_pb2_grpc
except ImportError:
    print("[ERROR] Stub files not found!")
    print("  Run this command first:")
    print("  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto")
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────
DEFAULT_HOST = "localhost"
PORT = 50051
# ──────────────────────────────────────────────────────────


def demo_unary(stub: chat_pb2_grpc.ChatServiceStub, username: str) -> None:
    """
    Demonstrates UNARY RPC.
    Sends a single message and prints the server's one-time response.
    """
    print("\n── Unary RPC Demo ──────────────────────────────")
    message = input("  Enter your message: ").strip()
    if not message:
        print("  (No message entered)")
        return

    try:
        response = stub.SendMessage(
            chat_pb2.ClientRequest(username=username, content=message)
        )
        print(f"  Server replied → Status: {response.status}")
        print(f"                  Message: {response.message}")
    except grpc.RpcError as e:
        print(f"  [RPC ERROR] {e.code()}: {e.details()}")


def demo_server_streaming(stub: chat_pb2_grpc.ChatServiceStub, username: str) -> None:
    """
    Demonstrates SERVER-STREAMING RPC.
    Server streams back the chat history one message at a time.
    """
    print("\n── Server-Streaming RPC: Fetching Chat History ─")
    try:
        stream = stub.JoinChat(
            chat_pb2.ClientRequest(username=username, content="join")
        )
        count = 0
        for msg in stream:
            print(f"  [{msg.timestamp}] {msg.username}: {msg.content}")
            count += 1
        print(f"  ── Stream ended. {count} messages received. ──")
    except grpc.RpcError as e:
        print(f"  [RPC ERROR] {e.code()}: {e.details()}")


def demo_bidirectional(stub: chat_pb2_grpc.ChatServiceStub, username: str) -> None:
    """
    Demonstrates BIDIRECTIONAL-STREAMING RPC.
    Real-time chat: user types messages, server broadcasts to everyone.
    """
    print("\n── Bidirectional Streaming RPC: Live Chat ───────")
    print("  Type messages and press Enter. Type /quit to leave.\n")

    running = True
    message_queue = []
    queue_lock = threading.Lock()
    queue_event = threading.Event()

    def request_generator():
        """Yields ClientRequest objects as the user types them."""
        # Send a join message first
        yield chat_pb2.ClientRequest(username=username, content=f"[{username} joined the live chat]")

        while running:
            queue_event.wait(timeout=0.5)
            queue_event.clear()
            with queue_lock:
                while message_queue:
                    yield chat_pb2.ClientRequest(
                        username=username,
                        content=message_queue.pop(0),
                    )

    def print_responses(stream):
        """Background thread: prints messages from the server."""
        try:
            for msg in stream:
                print(f"\r  [{msg.timestamp}] {msg.username}: {msg.content}")
                print("> ", end="", flush=True)
        except grpc.RpcError:
            pass

    try:
        stream = stub.LiveChat(request_generator())
        recv_thread = threading.Thread(target=print_responses, args=(stream,), daemon=True)
        recv_thread.start()

        while True:
            user_input = input("> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("/quit", "/exit", "/q"):
                with queue_lock:
                    message_queue.append(f"[{username} left the chat]")
                queue_event.set()
                time.sleep(0.3)
                running = False
                break
            with queue_lock:
                message_queue.append(user_input)
            queue_event.set()

    except (KeyboardInterrupt, EOFError):
        running = False
        print("\n  Disconnecting...")
    except grpc.RpcError as e:
        print(f"  [RPC ERROR] {e.code()}: {e.details()}")


def main() -> None:
    print("=" * 55)
    print("  Distributed Systems — gRPC Chat Client")
    print("=" * 55)

    host = input(f"  Enter server IP address [{DEFAULT_HOST}]: ").strip() or DEFAULT_HOST
    username = input("  Enter your username: ").strip() or "Anonymous"

    address = f"{host}:{PORT}"
    print(f"\n  Connecting to {address} ...")

    # Create an insecure channel (no TLS — fine for LAN/assignment)
    channel = grpc.insecure_channel(address)

    # Check connectivity
    try:
        grpc.channel_ready_future(channel).result(timeout=5)
        print("  Connected!\n")
    except grpc.FutureTimeoutError:
        print(f"\n[ERROR] Could not reach gRPC server at {address}")
        print("  Make sure the server is running and port 50051 is open.")
        sys.exit(1)

    stub = chat_pb2_grpc.ChatServiceStub(channel)

    print("  Choose a demo mode:")
    print("    [1] Unary RPC          — Send one message, get one reply")
    print("    [2] Server-Streaming   — Receive full message history")
    print("    [3] Bidirectional Chat — Real-time live chat (recommended)")
    print("    [q] Quit")
    print()

    while True:
        choice = input("  Your choice: ").strip().lower()

        if choice == "1":
            demo_unary(stub, username)
        elif choice == "2":
            demo_server_streaming(stub, username)
        elif choice == "3":
            demo_bidirectional(stub, username)
        elif choice in ("q", "quit", "exit"):
            break
        else:
            print("  Invalid choice. Enter 1, 2, 3, or q.")

    channel.close()
    print("\n  Goodbye!")


if __name__ == "__main__":
    main()
