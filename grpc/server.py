"""
=============================================================
  Distributed Systems Assignment
  gRPC Chat Server
=============================================================
  THEORY:
  gRPC (Google Remote Procedure Call) uses HTTP/2 as transport
  and Protocol Buffers for serialization. It supports 4 RPC types:
    1. Unary           - One request, one response
    2. Server-stream   - One request, many responses
    3. Client-stream   - Many requests, one response
    4. Bidirectional   - Many requests AND many responses

  This server implements all three that are defined in chat.proto.

  HOW TO RUN (on the SERVER laptop):
    1. pip install grpcio grpcio-tools
    2. python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto
    3. python server.py

  Share your local IP with your friend (run `ipconfig` on Windows).
=============================================================
"""

import grpc
import datetime
import threading
import time
from concurrent import futures

# Import the auto-generated stubs (run protoc first!)
try:
    import chat_pb2
    import chat_pb2_grpc
except ImportError:
    print("[ERROR] Stub files not found!")
    print("  Run this command first:")
    print("  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto")
    import sys
    sys.exit(1)

# ── Configuration ─────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 50051
MAX_WORKERS = 10
# ──────────────────────────────────────────────────────────


def now() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    """
    Implements all RPCs defined in chat.proto.
    Inherits from the auto-generated base class.
    """

    def __init__(self):
        # All connected live-chat clients (event queues)
        # Key: client identifier, Value: threading.Queue of ChatMessage
        self._subscribers: dict[str, "queue.Queue"] = {}
        self._lock = threading.Lock()
        self._message_history: list[chat_pb2.ChatMessage] = []

    # ── 1. Unary RPC ─────────────────────────────────────

    def SendMessage(
        self,
        request: chat_pb2.ClientRequest,
        context: grpc.ServicerContext,
    ) -> chat_pb2.ServerResponse:
        """
        Unary RPC: Client sends ONE message → server replies with ONE response.
        The server also broadcasts this message to all LiveChat subscribers.
        """
        if not request.content.strip():
            return chat_pb2.ServerResponse(
                status="ERROR",
                message="Message content cannot be empty.",
            )

        msg = chat_pb2.ChatMessage(
            username=request.username or "Anonymous",
            content=request.content,
            timestamp=now(),
        )
        log_msg = f"[{msg.timestamp}] [{msg.username}] {msg.content}"
        print(log_msg)

        # Store in history and broadcast to live subscribers
        with self._lock:
            self._message_history.append(msg)
            for q in self._subscribers.values():
                q.put(msg)

        return chat_pb2.ServerResponse(
            status="OK",
            message=f"Message delivered at {msg.timestamp}",
        )

    # ── 2. Server-Streaming RPC ──────────────────────────

    def JoinChat(
        self,
        request: chat_pb2.ClientRequest,
        context: grpc.ServicerContext,
    ):
        """
        Server-Streaming RPC: Client connects → server streams back message history.
        The client receives all previous messages in one go.
        """
        print(f"[{now()}] {request.username} requested chat history ({len(self._message_history)} messages)")

        # Stream back ALL messages in history
        with self._lock:
            history_snapshot = list(self._message_history)

        for msg in history_snapshot:
            if not context.is_active():
                return
            yield msg
            time.sleep(0.05)  # Small delay to simulate streaming

        # Send a system message indicating end of history
        yield chat_pb2.ChatMessage(
            username="SERVER",
            content=f"--- End of history. {len(history_snapshot)} messages loaded. ---",
            timestamp=now(),
        )

    # ── 3. Bidirectional-Streaming RPC ───────────────────

    def LiveChat(
        self,
        request_iterator,
        context: grpc.ServicerContext,
    ):
        """
        Bidirectional-Streaming RPC: Both sides stream simultaneously.
        This is the most advanced gRPC pattern — like a real-time chat.

        Client streams: ClientRequest messages (username + content)
        Server streams: ChatMessage broadcasts from all connected users
        """
        import queue

        client_queue: queue.Queue = queue.Queue()
        client_id = str(id(context))  # Unique ID per connection

        # Register this client's queue so it receives broadcasts
        with self._lock:
            self._subscribers[client_id] = client_queue

        print(f"[{now()}] LiveChat client connected (id={client_id[:8]}...)")

        # ── Background thread: read from client stream ────
        def consume_requests():
            try:
                for req in request_iterator:
                    if not context.is_active():
                        break
                    if req.content.strip():
                        msg = chat_pb2.ChatMessage(
                            username=req.username or "Anonymous",
                            content=req.content,
                            timestamp=now(),
                        )
                        print(f"[{msg.timestamp}] [LiveChat] {msg.username}: {msg.content}")
                        with self._lock:
                            self._message_history.append(msg)
                            for q in self._subscribers.values():
                                q.put(msg)
            except Exception:
                pass
            finally:
                # Signal the yield loop to stop
                client_queue.put(None)

        reader = threading.Thread(target=consume_requests, daemon=True)
        reader.start()

        # ── Main thread: yield from queue to client stream ──
        try:
            while context.is_active():
                try:
                    msg = client_queue.get(timeout=1.0)
                    if msg is None:
                        break
                    yield msg
                except Exception:
                    continue  # Timeout — check if still active
        finally:
            with self._lock:
                self._subscribers.pop(client_id, None)
            print(f"[{now()}] LiveChat client disconnected (id={client_id[:8]}...)")


def serve() -> None:
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKERS))

    # Register the servicer with the server
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), server)

    address = f"{HOST}:{PORT}"
    server.add_insecure_port(address)
    server.start()

    print("=" * 55)
    print("  Distributed Systems — gRPC Chat Server")
    print("=" * 55)
    print(f"  Listening on  : {address}")
    print(f"  Max workers   : {MAX_WORKERS}")
    print(f"  Protocol      : gRPC / HTTP2 + Protobuf")
    print("  Press Ctrl+C to stop.")
    print("=" * 55)

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
        server.stop(grace=2)
        print("[SERVER] Server stopped.")


if __name__ == "__main__":
    serve()
