"""
Chandy-Misra-Haas Distributed Deadlock Detection Algorithm (Edge-Chasing).

Theory:
- In distributed systems, no single coordinator may possess global visibility of all wait-for edges.
- Chandy-Misra-Haas (CMH) is an edge-chasing algorithm designed for the AND-request model.
- A probe message is defined as:
    PROBE(initiator, sender, receiver)
  where:
    - initiator: The process that became blocked and initiated the detection.
    - sender: The process forwarding the probe.
    - receiver: The process receiving the probe.

Detection Rules:
1. When a process P_i becomes BLOCKED waiting for processes {P_j}:
   - P_i sends PROBE(i, i, j) to each dependent process P_j.
2. When process P_j receives PROBE(initiator, sender, j):
   - If P_j is BLOCKED:
     - If initiator == j:
       --> A DEADLOCK IS DETECTED! (The probe has completed a full cycle).
     - Else:
       --> P_j propagates the probe by sending PROBE(initiator, j, k) to all processes
           P_k that P_j is waiting on.
   - If P_j is ACTIVE (not blocked):
     --> Discard the probe (no deadlock exists on this dependency path).

Resolution:
- Once initiator P_i detects the cycle, an abort/resolution message is issued.
- A victim (e.g. initiator or lowest priority node in the cycle) is chosen to abort,
  releasing resources and breaking the deadlock.
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ProcessStatus(Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    ABORTED = "ABORTED"


@dataclass
class Probe:
    initiator: str
    sender: str
    receiver: str
    visited_path: List[str] = field(default_factory=list)

    def __repr__(self):
        path_str = " -> ".join(self.visited_path) if self.visited_path else f"{self.sender} -> {self.receiver}"
        return f"Probe(initiator={self.initiator}, hop: {self.sender} -> {self.receiver}, path: [{path_str}])"


class DistributedProcess:
    def __init__(self, pid: str, priority: int = 1):
        self.pid = pid
        self.priority = priority
        self.status = ProcessStatus.ACTIVE
        # Dependent processes this process is waiting on
        self.waiting_for: Set[str] = set()
        # Resources currently held by this process
        self.held_resources: Set[str] = set()

    def block_on(self, dependent_pids: List[str]):
        self.status = ProcessStatus.BLOCKED
        for pid in dependent_pids:
            self.waiting_for.add(pid)

    def unblock(self):
        self.status = ProcessStatus.ACTIVE
        self.waiting_for.clear()

    def abort(self):
        self.status = ProcessStatus.ABORTED
        self.waiting_for.clear()
        self.held_resources.clear()


class ChandyMisraHaasSystem:
    def __init__(self):
        self.processes: Dict[str, DistributedProcess] = {}
        self.probe_history: List[Probe] = []
        self.detected_deadlocks: List[Dict] = []
        self.log_messages: List[str] = []

    def log(self, text: str):
        self.log_messages.append(text)
        print(text)

    def add_process(self, pid: str, priority: int = 1) -> DistributedProcess:
        if pid not in self.processes:
            self.processes[pid] = DistributedProcess(pid, priority)
        return self.processes[pid]

    def set_dependency(self, waiting_pid: str, target_pid: str):
        """Configure waiting_pid as blocked and waiting for target_pid."""
        p_wait = self.add_process(waiting_pid)
        p_target = self.add_process(target_pid)
        p_wait.block_on([target_pid])

    def initiate_probe(self, initiator_pid: str) -> bool:
        """
        Initiates deadlock detection from initiator_pid.
        Sends probes along wait-for edges and propagates them recursively.
        Returns True if a deadlock is detected, False otherwise.
        """
        if initiator_pid not in self.processes:
            self.log(f"[-] Process {initiator_pid} does not exist.")
            return False

        initiator = self.processes[initiator_pid]
        if initiator.status != ProcessStatus.BLOCKED:
            self.log(f"[*] Process {initiator_pid} is ACTIVE (not blocked). No deadlock detection needed.")
            return False

        self.log(f"\n{'='*65}")
        self.log(f"  CHANDY-MISRA-HAAS PROBE INITIATION BY PROCESS: {initiator_pid}")
        self.log(f"{'='*65}")
        self.log(f"[*] Process {initiator_pid} is BLOCKED waiting on: {sorted(initiator.waiting_for)}")

        deadlock_found = False
        queue: List[Probe] = []

        # Send initial probe to all dependents
        for dep in sorted(initiator.waiting_for):
            initial_probe = Probe(
                initiator=initiator_pid,
                sender=initiator_pid,
                receiver=dep,
                visited_path=[initiator_pid, dep]
            )
            queue.append(initial_probe)
            self.probe_history.append(initial_probe)
            self.log(f"  -> [SEND PROBE] {initiator_pid} ---> {dep} | Probe({initiator_pid}, {initiator_pid}, {dep})")

        # Process probe propagation
        step = 1
        while queue:
            current_probe = queue.pop(0)
            recv_pid = current_probe.receiver

            if recv_pid not in self.processes:
                self.log(f"  [!] Process {recv_pid} does not exist in system.")
                continue

            receiver_proc = self.processes[recv_pid]

            # Rule 2: If receiver is not blocked, probe is discarded
            if receiver_proc.status != ProcessStatus.BLOCKED:
                self.log(f"  [-] Process {recv_pid} received probe but is ACTIVE. Probe discarded along this branch.")
                continue

            # Check if probe returned to initiator
            if recv_pid == current_probe.initiator:
                deadlock_cycle = current_probe.visited_path
                self.log(f"\n[!] >>> DEADLOCK DETECTED BY CHANDY-MISRA-HAAS! <<<")
                self.log(f"[!] Probe returned to Initiator '{recv_pid}'!")
                self.log(f"[!] Deadlock Cycle: {' ---> '.join(deadlock_cycle)}")

                self.detected_deadlocks.append({
                    "initiator": current_probe.initiator,
                    "cycle": deadlock_cycle,
                    "probes_exchanged": len(self.probe_history)
                })
                deadlock_found = True
                continue

            # Forward probe to all processes the receiver is waiting for
            for next_dep in sorted(receiver_proc.waiting_for):
                # Avoid infinite loops along already visited sub-paths if not returning to initiator
                if next_dep in current_probe.visited_path and next_dep != current_probe.initiator:
                    continue

                forwarded_probe = Probe(
                    initiator=current_probe.initiator,
                    sender=recv_pid,
                    receiver=next_dep,
                    visited_path=current_probe.visited_path + [next_dep]
                )
                queue.append(forwarded_probe)
                self.probe_history.append(forwarded_probe)
                self.log(f"  -> [FORWARD PROBE] {recv_pid} ---> {next_dep} | Probe({current_probe.initiator}, {recv_pid}, {next_dep})")

            step += 1

        if not deadlock_found:
            self.log(f"\n[+] No deadlock detected by Process {initiator_pid}.")

        return deadlock_found

    def resolve_deadlock(self, victim_pid: Optional[str] = None) -> bool:
        """
        Resolves detected deadlock by aborting a victim process and clearing its dependencies.
        If victim_pid is not specified, selects the initiator of the latest detected deadlock.
        """
        if not self.detected_deadlocks:
            self.log("[-] No active detected deadlock to resolve.")
            return False

        latest_deadlock = self.detected_deadlocks[-1]
        cycle = latest_deadlock["cycle"]

        if victim_pid is None or victim_pid not in self.processes:
            # Default victim selection: lowest priority process in cycle
            cycle_procs = [self.processes[p] for p in cycle[:-1] if p in self.processes]
            victim = min(cycle_procs, key=lambda p: (p.priority, p.pid))
            victim_pid = victim.pid

        self.log(f"\n{'='*65}")
        self.log(f"  RESOLVING DEADLOCK: ABORTING VICTIM '{victim_pid}'")
        self.log(f"{'='*65}")

        victim_proc = self.processes[victim_pid]
        victim_proc.abort()

        # Remove dependencies pointing to or from victim
        for p in self.processes.values():
            if victim_pid in p.waiting_for:
                p.waiting_for.remove(victim_pid)
                if not p.waiting_for:
                    p.status = ProcessStatus.ACTIVE
                    self.log(f"[*] Process {p.pid} is now UNBLOCKED (victim released dependencies).")

        self.log(f"[SUCCESS] Victim Process '{victim_pid}' aborted and resources freed.")
        self.detected_deadlocks.pop()
        return True

    def get_topology_status(self) -> str:
        lines = ["\nDistributed Process Status:"]
        for pid in sorted(self.processes.keys()):
            p = self.processes[pid]
            waiting = f"waiting on {sorted(p.waiting_for)}" if p.waiting_for else "none"
            lines.append(f"  Process {pid:6} | Status: {p.status.value:8} | Priority: {p.priority} | Dependencies: {waiting}")
        return "\n".join(lines)
