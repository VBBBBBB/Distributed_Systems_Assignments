# Distributed Systems Assignments

Repository containing practical implementations and simulations for Distributed Systems coursework.

---

## Table of Contents

- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Assignment 1: Client–Server using TCP Sockets and gRPC](#assignment-1-clientserver-using-tcp-sockets-and-grpc)
  - [Overview](#overview)
  - [Running the Socket Implementation](#running-the-socket-implementation)
  - [Running the gRPC Implementation](#running-the-grpc-implementation)
- [Assignment 2: Distributed Leader Election (Bully & Ring)](#assignment-2-distributed-leader-election-bully--ring)
  - [Overview](#overview-1)
  - [Running the Election Simulator](#running-the-election-simulator)
  - [Running Unit Tests](#running-unit-tests)
- [Assignment 3: Deadlock Detection & Resolution Algorithms](#assignment-3-deadlock-detection--resolution-algorithms)
  - [Overview](#overview-2)
  - [Running the Deadlock Simulator](#running-the-deadlock-simulator)
  - [Running Unit Tests](#running-unit-tests-1)
- [Author & License](#author--license)

---

## Repository Structure

```
Distributed_Systems_Assignments/
├── .gitignore
├── README.md                          # Root documentation & run guide
├── Ass1/                              # Assignment 1: Sockets and gRPC
│   ├── .gitignore
│   ├── README.md                      # Detailed Ass1 documentation
│   ├── requirements.txt               # Dependencies (grpcio, protobuf)
│   ├── socket/
│   │   ├── server.py                  # Multi-threaded TCP Socket Server
│   │   └── client.py                  # Interactive TCP Socket Client
│   └── grpc/
│       ├── chat.proto                 # gRPC Protocol Buffer Definition
│       ├── chat_pb2.py                # Protobuf Python bindings
│       ├── chat_pb2_grpc.py           # gRPC Service stubs
│       ├── server.py                  # gRPC Server implementation
│       └── client.py                  # gRPC Client implementation
├── Ass2/                              # Assignment 2: Leader Election
│   ├── README.md                      # Detailed Ass2 documentation
│   ├── bully.py                       # Bully Election Algorithm engine
│   ├── ring.py                        # Ring Election Algorithm engine
│   ├── main.py                        # Interactive CLI simulator & demos
│   └── test_elections.py              # Automated unit and integration tests
└── Ass3/                              # Assignment 3: Deadlock Detection & Resolution
    ├── README.md                      # Detailed Ass3 documentation
    ├── wfg.py                         # Wait-For Graph, RAG, DFS 3-color cycles & resolution
    ├── chandy_misra_haas.py           # Distributed edge-chasing probe algorithm
    ├── main.py                        # Interactive CLI simulator & 4 automated demos
    └── test_deadlock.py               # Unit and integration test suite
```

---

## Prerequisites

- **Python**: Version 3.8 or higher.
- Verify installation:
  ```bash
  python --version
  ```

---

## Assignment 1: Client–Server using TCP Sockets and gRPC

### Overview

Demonstrates inter-process and distributed machine communication using two paradigms:
1. **TCP Sockets (`socket` module)**: Low-level, reliable byte stream connection handling multi-threaded client requests.
2. **gRPC (`grpcio` + `protobuf`)**: Modern high-performance Remote Procedure Call framework utilizing Protocol Buffers and HTTP/2 transport.

### Installation

Navigate to `Ass1` and install the required packages:

```bash
cd Ass1
pip install -r requirements.txt
```

---

### Running the Socket Implementation

#### 1. Start Socket Server
In your first terminal:
```bash
cd Ass1/socket
python server.py
```
*Defaults to port `5000` listening on all available interfaces (`0.0.0.0`).*

#### 2. Start Socket Client
In a second terminal:
- **Same machine (localhost)**:
  ```bash
  cd Ass1/socket
  python client.py
  ```
- **Across LAN / separate machine**:
  ```bash
  python client.py --host <SERVER_IP> --port 5000
  ```

---

### Running the gRPC Implementation

#### 1. Start gRPC Server
In your first terminal:
```bash
cd Ass1/grpc
python server.py
```
*Runs on port `50051`.*

#### 2. Start gRPC Client
In a second terminal:
- **Same machine (localhost)**:
  ```bash
  cd Ass1/grpc
  python client.py
  ```
- **Across LAN / separate machine**:
  ```bash
  python client.py --host <SERVER_IP> --port 50051
  ```

*(Optional) To regenerate protobuf stubs from `chat.proto`:*
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto
```

---

## Assignment 2: Distributed Leader Election (Bully & Ring)

### Overview

Simulates coordinator/leader election in distributed networks where coordinator failures must be handled dynamically:
- **Bully Algorithm**: Higher process IDs take priority. When a failure is detected, nodes send election messages to higher IDs; highest active node becomes the coordinator.
- **Ring Algorithm**: Logical token/message passing along an ordered unidirectional ring ($P_0 \to P_1 \to \dots \to P_{n-1} \to P_0$). Automatically skips crashed successors.

### Running the Election Simulator

Navigate to `Ass2`:
```bash
cd Ass2
python main.py
```

You will see the interactive menu:
```
=================================================================
  DISTRIBUTED COORDINATOR ELECTION SIMULATOR
=================================================================
1. Bully Algorithm (Interactive Mode)
2. Ring Algorithm (Interactive Mode)
3. Run Bully Algorithm Demo
4. Run Ring Algorithm Demo
5. Exit
```

- **Interactive Modes (1 & 2)**: Interactively simulate node crashes, recoveries, and view detailed step-by-step message flows.
- **Automated Demos (3 & 4)**: View pre-configured scenarios illustrating coordinator crash, election takeover, and recovery.

### Running Unit Tests

Run the test suite verifying election correctness, message logs, and edge cases:

From repository root:
```bash
python -m unittest discover -s Ass2
```
Or from inside `Ass2`:
```bash
cd Ass2
python -m unittest test_elections.py
```

---

## Assignment 3: Deadlock Detection & Resolution Algorithms

### Overview

Implements deadlock detection and resolution across centralized and distributed environments:
- **Wait-For Graph (WFG) & Resource Allocation Graph (RAG)**: Models processes and resources, collapses allocations/requests into a directed WFG, and identifies cycles using Depth-First Search with 3-state coloring (`WHITE`, `GRAY`, `BLACK`).
- **Chandy-Misra-Haas (CMH) Algorithm**: Distributed edge-chasing probe mechanism for the AND-request model where blocked processes propagate `Probe(initiator, sender, receiver)` messages.
- **Deadlock Resolution**: Dynamically selects victims using policies (`LOWEST_PRIORITY`, `FEWEST_RESOURCES`, `PID`), terminates victim processes, frees dependencies, and verifies that the system becomes cycle-free.

### Running the Deadlock Simulator

Navigate to `Ass3`:
```bash
cd Ass3
python main.py
```

You will see the menu:
```
====================================================================
  DISTRIBUTED SYSTEMS ASSIGNMENT 3: DEADLOCK DETECTION & RESOLUTION
====================================================================
1. Run Demo 1: Classic Circular WFG Deadlock (P1 -> P2 -> P3 -> P1)
2. Run Demo 2: Resource Allocation Graph (RAG) to WFG Conversion
3. Run Demo 3: Chandy-Misra-Haas Distributed Edge-Chasing
4. Run Demo 4: Complex Multi-Cycle Deadlock Resolution
5. Interactive Wait-For Graph (WFG) Simulator
6. Interactive Chandy-Misra-Haas Distributed Simulator
7. Exit
```

- **Options 1–4**: Run automated scenarios showcasing cycle detection, RAG-to-WFG conversion, distributed probe journeys, and multi-cycle recovery.
- **Options 5 & 6**: Interactive sandboxes to build custom graphs, trigger probes, and test victim resolution policies.

### Running Unit Tests

Run the unit tests verifying cycle detection, RAG conversion, CMH probe routing, and victim resolution:

From repository root:
```bash
python -m unittest discover -s Ass3
```
Or from inside `Ass3`:
```bash
cd Ass3
python -m unittest test_deadlock.py
```

---

## Author & License

Developed as part of Distributed Systems coursework.
Licensed under the [MIT License](LICENSE).
