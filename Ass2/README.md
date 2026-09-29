# Distributed Systems Assignment 2
## Leader Election in Distributed Systems: Bully and Ring Algorithms

---

## 1. Objective

Implement and simulate coordinator / leader election algorithms in distributed systems:
1. **Bully Election Algorithm** (Garcia-Molina)
2. **Ring Election Algorithm** (Chang and Roberts / Token-Ring style)

The implementation models process failure (crash), node recovery, message passing, election propagation, timeout handling, and coordinator announcement.

---

## 2. Theory & Concepts

In distributed systems, a coordinator or leader process is often needed to manage shared resources, coordinate consensus, or schedule tasks. If the coordinator fails, the remaining active nodes must detect the failure and elect a unique coordinator.

### 2.1 The Bully Algorithm

The Bully Algorithm assumes that every process has a unique numerical priority / process ID (PID). Higher PID processes have higher priority.

#### Core Rules:
1. **Initiation**: When any process $P$ notices the coordinator has crashed, it sends an `ELECTION` message to all processes with higher PIDs ($P_i > P$).
2. **Response**:
   - If no process responds (times out), $P$ wins and broadcasts a `COORDINATOR` announcement to all lower processes.
   - If any higher process responds with `OK` / `ANSWER`, that higher process takes over the election, and $P$'s duty is done.
3. **Recovery**: When a crashed process with a higher ID recovers, it immediately initiates an election (or broadcasts its coordinator status if it holds the highest PID in the system), "bullying" the current leader into stepping down.

#### Message Complexity:
- **Best Case**: The process just below the coordinator detects failure $\rightarrow O(N)$ messages.
- **Worst Case**: The lowest ID process detects failure $\rightarrow O(N^2)$ messages.

```
Process 2 detects crash of Coord 7:
  P2 ----[ELECTION]----> P3, P4, P5, P6, P7
  P3, P4, P5, P6 -------[OK]-------> P2 (P2 steps aside)
  P6 ----[ELECTION]----> P7 (Times out - P7 is crashed)
  P6 ----[COORDINATOR]--> All active processes (P6 elected!)
```

---

### 2.2 The Ring Algorithm

Processes are organized in a logical unidirectional ring topology ($P_0 \rightarrow P_1 \rightarrow \dots \rightarrow P_{n-1} \rightarrow P_0$).

#### Core Rules:
1. **Initiation**: When any process $P$ notices coordinator failure, it creates an `ELECTION` message containing its own PID (`[P]`) and forwards it to its active successor in the ring (skipping crashed nodes).
2. **Forwarding**: Each active successor appends its PID to the list (`[P, P_next, ...]`) and forwards it to the next active successor.
3. **Loop Completion**: When the election message completes the circle and returns to the initiator $P$:
   - $P$ selects the process with the highest PID from the list as the new coordinator: $\max(\text{active list})$.
   - $P$ forwards a `COORDINATOR` message around the ring announcing the elected leader.

#### Message Complexity:
- Circulation of Election message: $N - 1$ messages.
- Circulation of Coordinator message: $N - 1$ messages.
- Total messages: $2(N - 1)$ or $O(N)$ messages.

```
Ring: 1 -> 3 -> 5 -> 2 -> 6 -> 4 -> 1
Crash: 6, 4
Initiator: 3
  Phase 1 (Election list):
    3 --[3]--> 5 --[3,5]--> 2 --[3,5,2]--> 1 --[3,5,2,1]--> 3
  Phase 2 (Coordinator announcement):
    Winner = max([3, 5, 2, 1]) = 5
    3 --[Coord: 5]--> 5 --[Coord: 5]--> 2 --[Coord: 5]--> 1
```

---

## 3. Project Structure

```
Ass2/
├── bully.py             # Bully Election System class and state machine
├── ring.py              # Ring Election System class and topology traversal
├── main.py              # Interactive CLI simulator and automated demos
├── test_elections.py    # Comprehensive unit and integration test suite
└── README.md            # Assignment 2 documentation
```

---

## 4. Requirements & Setup

No external third-party dependencies are required. The project uses standard Python 3.8+.

Ensure Python is available:
```bash
python --version
```

---

## 5. How to Run

### Option 1: Interactive CLI Simulator

Navigate to the `Ass2` directory and run:

```bash
cd Ass2
python main.py
```

Main Menu:
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

- **Option 1 (Bully Interactive)**: Set custom process IDs, crash nodes, recover nodes, and trigger elections from any active process.
- **Option 2 (Ring Interactive)**: Set custom ring order, crash nodes, recover nodes, and trace ring message forwarding.
- **Option 3 (Bully Demo)**: Runs an automated step-by-step scenario demonstrating coordinator crash, middle-node election, and highest-node recovery.
- **Option 4 (Ring Demo)**: Runs an automated step-by-step scenario with multiple crashed nodes, ring skipping, and re-election.

---

### Option 2: Running Unit Tests

To run the automated test suite verifying both Bully and Ring algorithms:

From the repository root:
```bash
python -m unittest discover -s Ass2
```

Or from inside `Ass2`:
```bash
cd Ass2
python -m unittest test_elections.py
```

Test coverage includes:
- Initial coordinator determination
- Coordinator crash detection and election from arbitrary nodes
- Cascading and multiple consecutive node failures
- High-priority node recovery and coordinator reclamation
- Ring traversal and successor failure bypass
