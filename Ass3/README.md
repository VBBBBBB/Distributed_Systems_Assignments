# Distributed Systems Assignment 3
## Deadlock Detection & Resolution Algorithms

---

## 1. Objective

Implement a complete deadlock detection and resolution mechanism using:
1. **Wait-For Graph (WFG) & Resource Allocation Graph (RAG)**: Cycle detection using Depth-First Search with 3-state coloring (`WHITE`, `GRAY`, `BLACK`) to detect and report all elementary deadlock cycles.
2. **Chandy-Misra-Haas (CMH) Algorithm**: An edge-chasing probe-based distributed deadlock detection algorithm for AND-request models.
3. **Deadlock Resolution Strategies**: Dynamic victim selection (by Lowest Priority, Fewest Resources Held, or Process ID) and resource release/process termination until all deadlocks are resolved.

---

## 2. Theory & Concepts

### 2.1 Coffman Conditions for Deadlock
A deadlock occurs in a concurrent or distributed system when four conditions hold simultaneously:
1. **Mutual Exclusion**: At least one resource is held in a non-shareable mode.
2. **Hold and Wait**: A process is holding at least one resource and requesting additional resources held by other processes.
3. **No Preemption**: Resources cannot be preempted forcibly; they can only be released voluntarily by the holding process.
4. **Circular Wait**: A closed chain of processes exists such that each process holds at least one resource needed by the next process in the chain.

---

### 2.2 Resource Allocation Graph (RAG) vs. Wait-For Graph (WFG)

```
        RAG                                          WFG
  [P1] ──requests──► (R2)                     [P1]
   ▲                  │                         │
   │                  ▼                         ▼
  (R1) ◄──alloc───── [P2]                      [P2]
   ▲                                            │
   │ ──alloc── (R1 held by P1)                  ▼
  [P3] ◄──requests── (R3 held by P3)           [P3] ──► [P1]
```

- **RAG (Resource Allocation Graph)**: Bipartite directed graph with two disjoint sets of vertices: Processes $P$ and Resources $R$.
  - Edge $R_k \to P_i$: Resource $R_k$ is allocated to process $P_i$.
  - Edge $P_i \to R_k$: Process $P_i$ is requesting resource $R_k$.
- **WFG (Wait-For Graph)**: Constructed by collapsing resources from the RAG:
  - Directed edge $P_i \to P_j$ exists if and only if $P_i$ is waiting for a resource currently allocated to $P_j$.
- **Condition for Deadlock**: In a single-unit resource system, **a cycle in the Wait-For Graph is a necessary and sufficient condition for deadlock**.

---

### 2.3 Cycle Detection via DFS 3-Coloring

To detect elementary cycles without infinite looping in directed graphs, nodes are classified into three colors during Depth-First Search:
- **`WHITE` (Unvisited)**: Node has not been visited yet.
- **`GRAY` (Visiting)**: Node is currently in the active recursion call stack. If a directed edge points to a `GRAY` node, **a back-edge exists, confirming a cycle / deadlock**.
- **`BLACK` (Visited)**: Node and all its descendants have been completely explored.

---

### 2.4 Chandy-Misra-Haas (CMH) Distributed Edge-Chasing

In a distributed system without a centralized coordinator:
- A blocked process $P_i$ generates probe messages:
  $$\text{Probe}(initiator, sender, receiver)$$
- **Forwarding Rule**: When process $P_j$ receives $\text{Probe}(i, sender, j)$:
  - If $P_j$ is **BLOCKED**:
    - If $i == j$: The probe completed the loop! **Deadlock detected by initiator $P_i$**.
    - If $i \neq j$: $P_j$ forwards $\text{Probe}(i, j, k)$ to all processes $P_k$ it is waiting on.
  - If $P_j$ is **ACTIVE**: The probe is discarded (no deadlock along that path).

---

### 2.5 Deadlock Resolution Strategies

Once cycles are identified, deadlocks are broken by selecting a **victim process** according to a configured policy:
- **`LOWEST_PRIORITY`**: Selects the process with the smallest priority value (preserving higher priority critical processes).
- **`FEWEST_RESOURCES`**: Selects the process holding the smallest number of resources (minimizing rollback/cleanup costs).
- **`HIGHEST_PID` / `LOWEST_PID`**: Deterministic selection based on numerical/alphabetical process ID.

The victim process is aborted, releasing its dependencies and held resources, after which the graph is re-evaluated until cycle-free.

---

## 3. Project Structure

```
Ass3/
├── wfg.py                 # Wait-For Graph, RAG conversion, DFS cycle detection & resolution
├── chandy_misra_haas.py   # Distributed edge-chasing probe algorithm implementation
├── main.py                # Interactive CLI simulator and automated demos
├── test_deadlock.py       # Comprehensive unit and integration test suite
└── README.md              # Assignment 3 documentation
```

---

## 4. Requirements & Setup

Uses standard Python 3.8+ with no external third-party dependencies required.

Check your Python version:
```bash
python --version
```

---

## 5. How to Run

### Option 1: Interactive CLI Simulator & Demos

From the root directory:
```bash
cd Ass3
python main.py
```

Main Menu:
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

#### Demo Descriptions:
- **Demo 1**: Classic 3-process circular dependency ($P_1 \to P_2 \to P_3 \to P_1$) with step-by-step cycle detection and victim resolution.
- **Demo 2**: Sets up resources $R_1, R_2, R_3, R_4$ with allocations and requests, automatically builds the WFG, detects cycles, and resolves the deadlock.
- **Demo 3**: Traces distributed probe forwarding across nodes in Chandy-Misra-Haas algorithm until detection and resolution.
- **Demo 4**: Resolves complex overlapping multi-cycle graphs iteratively.
- **Option 5 & 6**: Interactive sandboxes allowing you to build custom graphs, add processes, set priorities, inject dependencies, run cycle detection, and test victim policies.

---

### Option 2: Running Unit Tests

Run the full automated test suite verifying edge cases, RAG conversions, DFS cycles, and probe routing:

From repository root:
```bash
python -m unittest discover -s Ass3
```

Or from inside `Ass3`:
```bash
cd Ass3
python -m unittest test_deadlock.py
```
