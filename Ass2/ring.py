"""
Ring Election Algorithm Implementation.

In the Ring Election Algorithm:
1. All processes are arranged in a logical unidirectional ring (P_0 -> P_1 -> ... -> P_n-1 -> P_0).
2. When a process notices the coordinator is down, it initiates an election:
   - Builds an ELECTION message containing [initiator_id].
   - Forwards it to the next active successor in the ring (skipping crashed nodes).
3. Each receiving process appends its own ID to the active list and forwards to its successor.
4. When the message arrives back at the initiator (initiator sees its ID already in the list):
   - The coordinator is chosen as max(active_list).
   - A COORDINATOR message is circulated around the ring to update all active nodes.
"""

from typing import List, Dict, Optional
from enum import Enum


class ProcessState(Enum):
    ACTIVE = "ACTIVE"
    CRASHED = "CRASHED"
    COORDINATOR = "COORDINATOR"


class RingProcess:
    def __init__(self, pid: int):
        self.pid = pid
        self.state = ProcessState.ACTIVE

    def is_alive(self) -> bool:
        return self.state != ProcessState.CRASHED

    def __repr__(self):
        return f"RingProcess(PID={self.pid}, State={self.state.value})"


class RingElectionSystem:
    def __init__(self, process_ids: List[int]):
        # Keep ring ordered by process_ids as defined
        self.ring_order: List[int] = list(process_ids)
        self.processes: Dict[int, RingProcess] = {pid: RingProcess(pid) for pid in self.ring_order}
        self.coordinator_id: Optional[int] = None
        self.message_log: List[str] = []
        self.total_messages_sent: int = 0

        if self.processes:
            highest_id = max(self.processes.keys())
            self.processes[highest_id].state = ProcessState.COORDINATOR
            self.coordinator_id = highest_id

    def log(self, text: str):
        self.message_log.append(text)
        print(text)

    def _get_next_alive_successor(self, current_pid: int) -> Optional[int]:
        """Find the next alive process in the ring."""
        n = len(self.ring_order)
        curr_idx = self.ring_order.index(current_pid)

        for step in range(1, n):
            next_pid = self.ring_order[(curr_idx + step) % n]
            if self.processes[next_pid].is_alive():
                return next_pid
        return None  # No other alive process in the ring

    def crash_process(self, pid: int) -> bool:
        if pid not in self.processes:
            self.log(f"[-] Process {pid} does not exist in the ring.")
            return False

        process = self.processes[pid]
        if process.state == ProcessState.CRASHED:
            self.log(f"[-] Process {pid} is already crashed.")
            return False

        was_coordinator = (self.coordinator_id == pid)
        process.state = ProcessState.CRASHED
        self.log(f"[!] Process {pid} has CRASHED.")

        if was_coordinator:
            self.coordinator_id = None
            self.log(f"[!] Coordinator {pid} is down! Ring currently has NO coordinator.")
        return True

    def recover_process(self, pid: int) -> bool:
        if pid not in self.processes:
            self.log(f"[-] Process {pid} does not exist in the ring.")
            return False

        process = self.processes[pid]
        if process.state != ProcessState.CRASHED:
            self.log(f"[-] Process {pid} is already active.")
            return False

        process.state = ProcessState.ACTIVE
        self.log(f"[+] Process {pid} has RECOVERED and re-joined the ring.")
        self.log(f"[*] Recovered Process {pid} initiates an election...")
        self.start_election(pid)
        return True

    def start_election(self, initiator_id: int) -> Optional[int]:
        """
        Runs the Ring Election algorithm initiated by initiator_id.
        Phase 1: Circulate active candidate list around the ring.
        Phase 2: Circulate coordinator announcement around the ring.
        """
        if initiator_id not in self.processes:
            self.log(f"[-] Invalid initiator ID {initiator_id}.")
            return None

        initiator = self.processes[initiator_id]
        if not initiator.is_alive():
            self.log(f"[-] Process {initiator_id} is crashed and cannot start an election.")
            return None

        self.log(f"\n=======================================================")
        self.log(f"   RING ELECTION INITIATED BY PROCESS {initiator_id}")
        self.log(f"=======================================================")
        self.log(f"[*] Ring Topology: {' -> '.join(str(p) for p in self.ring_order)} -> {self.ring_order[0]}")

        # Phase 1: Candidate List Propagation
        active_list = [initiator_id]
        current_node = initiator_id

        self.log(f"\n--- PHASE 1: Circulating ELECTION Message ---")
        while True:
            next_node = self._get_next_alive_successor(current_node)
            if next_node is None:
                # Sole active node
                self.log(f"[*] Process {current_node} is the ONLY alive process in the ring.")
                elected_leader = current_node
                break

            self.total_messages_sent += 1
            self.log(f"    -> [ELECTION msg: {active_list}] Process {current_node} ---> Process {next_node}")

            if next_node == initiator_id:
                # Message completed full circle back to initiator
                self.log(f"[*] Election message completed full loop back to Initiator {initiator_id}.")
                elected_leader = max(active_list)
                self.log(f"[*] Final Candidate List: {active_list}")
                self.log(f"[*] Highest PID in list is {elected_leader}.")
                break
            else:
                if next_node not in active_list:
                    active_list.append(next_node)
                current_node = next_node

        # Phase 2: Coordinator Announcement Circulation
        self.log(f"\n--- PHASE 2: Circulating COORDINATOR Announcement ---")
        self.coordinator_id = elected_leader
        curr_announcer = initiator_id

        while True:
            next_node = self._get_next_alive_successor(curr_announcer)
            if next_node is None or next_node == initiator_id:
                break

            self.total_messages_sent += 1
            self.log(f"    -> [COORDINATOR: {elected_leader}] Process {curr_announcer} ---> Process {next_node}")
            curr_announcer = next_node

        # Update states
        for pid, proc in self.processes.items():
            if proc.is_alive():
                if pid == elected_leader:
                    proc.state = ProcessState.COORDINATOR
                else:
                    proc.state = ProcessState.ACTIVE

        self.log(f"\n[SUCCESS] >>> Process {elected_leader} is elected as the COORDINATOR <<<\n")
        return elected_leader

    def get_status(self) -> str:
        lines = []
        lines.append(f"Current Coordinator: {self.coordinator_id if self.coordinator_id is not None else 'NONE'}")
        lines.append(f"Ring Topology: {' -> '.join(str(p) for p in self.ring_order)} -> {self.ring_order[0]}")
        lines.append("Processes Status:")
        for pid in self.ring_order:
            p = self.processes[pid]
            status_tag = f"[{p.state.value}]"
            lines.append(f"  PID {pid:2d}: {status_tag}")
        return "\n".join(lines)
