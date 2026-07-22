# Distributed Systems Assignment
## Client–Server Program using Socket / gRPC

---

## 1. Objective

Implement a simple client-server communication model using **TCP Sockets** and **gRPC** to exchange messages between distributed nodes running on separate physical machines connected over a LAN.

---

## 2. Theory

### 2.1 What is a Socket?

A **socket** is a software abstraction that represents one endpoint of a two-way communication link between two programs running on a network. Sockets can use different transport protocols:

| Protocol | Type | Reliability | Use Case |
|---|---|---|---|
| **TCP** | Stream | Reliable, ordered | Chat, file transfer |
| **UDP** | Datagram | Unreliable, fast | Video streaming, gaming |

In this assignment we use **TCP** (`SOCK_STREAM`) because message delivery must be guaranteed and ordered.

#### Socket Lifecycle

```
SERVER                          CLIENT
  │                               │
  ├─ socket()                     ├─ socket()
  ├─ bind(IP, PORT)               │
  ├─ listen()                     │
  ├─ accept()  ◄──────────────── connect()
  │                               │
  ├─ recv()    ◄──────────────── send(message)
  ├─ send()   ──────────────────► recv()
  │                               │
  └─ close()                     └─ close()
```

### 2.2 What is gRPC?

**gRPC** (Google Remote Procedure Call) is a modern, high-performance RPC framework that uses:
- **HTTP/2** as the transport layer (multiplexed, binary, compressed)
- **Protocol Buffers** (protobuf) as the Interface Definition Language (IDL) and serialization format

It supports 4 communication patterns:

| Pattern | Description | Example |
|---|---|---|
| **Unary** | 1 request → 1 response | REST-like API call |
| **Server Streaming** | 1 request → N responses | Live scores, log tailing |
| **Client Streaming** | N requests → 1 response | File upload |
| **Bidirectional** | N requests ↔ N responses | Real-time chat |

#### gRPC Architecture

```
CLIENT                          SERVER
  │                               │
  │  ClientRequest (protobuf)     │
  ├──────── HTTP/2 stream ───────►│
  │                               ├─ Deserialize
  │                               ├─ Process
  │                               ├─ Serialize
  │◄──────── HTTP/2 stream ───────┤
  │  ChatMessage (protobuf)       │
```

### 2.3 Comparison: Sockets vs gRPC

| Feature | TCP Sockets | gRPC |
|---|---|---|
| Protocol | TCP | HTTP/2 |
| Serialization | Raw bytes / text | Protocol Buffers |
| API definition | None (manual) | `.proto` file (IDL) |
| Language support | Universal | 10+ languages |
| Streaming | Manual | Built-in |
| Performance | Low overhead | High throughput |
| Complexity | Low | Medium |
| Use in industry | Legacy systems | Microservices, cloud |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     LAN / Wi-Fi Network                 │
│                                                         │
│   ┌────────────────┐         ┌────────────────────┐    │
│   │  YOUR LAPTOP   │         │  FRIEND'S LAPTOP   │    │
│   │                │         │                    │    │
│   │  client.py     │◄───────►│  server.py         │    │
│   │  (Socket/gRPC) │ TCP/    │  (Socket/gRPC)     │    │
│   └────────────────┘ HTTP2   └────────────────────┘    │
│                                                         │
│   IP: 192.168.x.y              IP: 192.168.x.z         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. File Structure

```
DSASSIGNMENTS/
├── README.md                ← This file (assignment report)
│
├── socket/                  ── TCP Socket Implementation ──
│   ├── server.py            Multi-threaded server (port 5050)
│   └── client.py            Chat client with thread for receiving
│
└── grpc/                    ── gRPC Implementation ──
    ├── chat.proto            Protocol Buffer service definition
    ├── chat_pb2.py           Auto-generated message stubs
    ├── chat_pb2_grpc.py      Auto-generated service stubs
    ├── server.py             gRPC server (port 50051)
    └── client.py             gRPC client (3 RPC mode demos)
```

---

## 5. How to Run

### Prerequisites

Both laptops must:
- Be on the **same Wi-Fi network** (same router)
- Have **Python 3.8+** installed

---

### 5.1 TCP Socket — Step by Step

#### On the SERVER laptop (your friend's):

```bash
# Navigate to the socket folder
cd DSASSIGNMENTS/socket

# Start the server
python server.py
```

Expected output:
```
=======================================================
  Distributed Systems — TCP Socket Server
=======================================================
  Listening on  : 0.0.0.0:5050
  Max clients   : 10
  Press Ctrl+C to stop the server.
=======================================================
```

**Find the server's IP:** Open a new terminal and run:
```bash
# Windows
ipconfig
# Look for "IPv4 Address" under your Wi-Fi adapter
# Example: 192.168.1.105
```

#### On the CLIENT laptop (yours):

```bash
cd DSASSIGNMENTS/socket
python client.py

# When prompted:
#   Enter server IP address: 192.168.1.105   ← friend's IP
```

Multiple clients can connect simultaneously. Messages are broadcast to all connected users.

---

### 5.2 gRPC — Step by Step

#### Install dependencies (BOTH laptops):

```bash
pip install grpcio grpcio-tools
```

#### Generate Python stubs from proto (BOTH laptops):

```bash
cd DSASSIGNMENTS/grpc

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto
```

This creates two files:
- `chat_pb2.py` — Python classes for the proto messages
- `chat_pb2_grpc.py` — Python stubs for the service

#### On the SERVER laptop (your friend's):

```bash
python server.py
```

#### On the CLIENT laptop (yours):

```bash
python client.py
# Enter server IP when prompted
# Choose mode 3 (Bidirectional) for live chat
```

---

## 6. Features Demonstrated

### TCP Socket
- Multi-threaded server handles multiple clients simultaneously
- Real-time message broadcasting to all connected clients
- Join/Leave notifications
- Graceful `/quit` command

### gRPC
- **Mode 1 — Unary RPC**: Send one message, receive one structured response
- **Mode 2 — Server Streaming**: Client requests and receives full message history as a stream
- **Mode 3 — Bidirectional Streaming**: Full real-time chat using concurrent read/write streams

---

## 7. Key Concepts Illustrated

| Concept | Where |
|---|---|
| Socket binding & listening | `socket/server.py` |
| Multi-threading for concurrency | Both socket files |
| Protocol Buffer serialization | `grpc/chat.proto` |
| RPC method dispatch | `grpc/server.py` (ChatServicer) |
| Generator-based streaming | `grpc/client.py` (request_generator) |
| Thread-safe shared state | `_lock` in gRPC server |

---

## 8. Troubleshooting

| Problem | Solution |
|---|---|
| `ConnectionRefusedError` | Server is not running, or wrong IP/port |
| `Port already in use` | Another process uses port 5050/50051. Kill it or change the port in both files |
| Can't connect across laptops | Disable Windows Firewall temporarily, or add inbound rule for port 5050/50051 |
| `ModuleNotFoundError: chat_pb2` | Run the `protoc` command to generate stubs |
| Friend can't reach server | Make sure both are on the **same Wi-Fi** (not mobile hotspot vs home Wi-Fi) |

### Open Windows Firewall port (run as Administrator):

```powershell
# For TCP Socket
netsh advfirewall firewall add rule name="DS Assignment Socket" dir=in action=allow protocol=TCP localport=5050

# For gRPC
netsh advfirewall firewall add rule name="DS Assignment gRPC" dir=in action=allow protocol=TCP localport=50051
```

---

## 9. Sample Output

### TCP Socket
```
[10:15:32] [+] New connection from 192.168.1.102:54321
[10:15:34] 🔵 Alice joined the chat from 192.168.1.102
[10:15:40] Alice: Hello from the other laptop!
[10:15:45] Bob: Hey Alice! I can see your message!
[10:15:50] 🔴 Alice left the chat.
```

### gRPC (Bidirectional)
```
[10:20:01] [LiveChat] Alice: [Alice joined the live chat]
[10:20:05] [LiveChat] Alice: This is gRPC bidirectional streaming!
[10:20:08] [LiveChat] Bob: Amazing! HTTP/2 under the hood!
```

---

## 10. References

1. Python `socket` module docs: https://docs.python.org/3/library/socket.html
2. gRPC Python quickstart: https://grpc.io/docs/languages/python/quickstart/
3. Protocol Buffers guide: https://protobuf.dev/getting-started/pythontutorial/
4. Tanenbaum, A.S. & Van Steen, M. — *Distributed Systems: Principles and Paradigms*

---

*Assignment submitted for Distributed Systems course*
