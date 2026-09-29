"""
Bully Election Algorithm Implementation.

In the Bully Algorithm:
1. When a process P notices the coordinator is down, it sends an ELECTION message
   to all processes with higher IDs.
2. If no process responds (or all are down), P wins and broadcasts COORDINATOR.
3. If any higher-ID process responds with OK, that higher process takes over the election.
4. When a crashed process recovers, if it has the highest ID, it "bullies" everyone
   and immediately becomes the coordinator.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ProcessState(Enum):
    ACTIVE = "ACTIVE"
    CRASHED = "CRASHED"
    COORDINATOR = "COORDINATOR"


@dataclass
class Message:
    sender_id: int
    receiver_id: int
    msg_type: str  # "ELECTION", "OK", "COORDINATOR"
    content: str = ""


class Process:
    def __init__(self, pid: int):
        self.pid = pid
        self.state = ProcessState.ACTIVE

    def is_alive(self) -> bool:
        return self.state != ProcessState.CRASHED

    def __repr__(self):
        return f"Process(PID={self.pid}, State={self.state.value})"


class BullyElectionSystem:
    def __init__(self, process_ids: List[int]):
        self.processes: Dict[int, Process] = {pid: Process(pid) for pid in sorted(process_ids)}
        self.coordinator_id: Optional[int] = None
        self.message_log: List[str] = []
        self.total_messages_sent: int = 0
        
        # Initial election to set up the highest ID as coordinator
        if self.processes:
            highest_id = max(self.processes.keys())
            self.processes[highest_id].state = ProcessState.COORDINATOR
            self.coordinator_id = highest_id

    def log(self, text: str):
        self.message_log.append(text)
        print(text)

    def crash_process(self, pid: int) -> bool:
        if pid not in self.processes:
            self.log(f"[-] Process {pid} does not exist.")
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
            self.log(f"[!] Coordinator {pid} is down! System currently has NO coordinator.")
        return True

    def recover_process(self, pid: int) -> bool:
        if pid not in self.processes:
            self.log(f"[-] Process {pid} does not exist.")
            return False
        
        process = self.processes[pid]
        if process.state != ProcessState.CRASHED:
            self.log(f"[-] Process {pid} is already active.")
            return False
        
        process.state = ProcessState.ACTIVE
        self.log(f"[+] Process {pid} has RECOVERED.")
        
        # When a process recovers in Bully algorithm, it initiates an election
        self.log(f"[*] Recovered Process {pid} initiates an election...")
        self.start_election(pid)
        return True

    def start_election(self, initiator_id: int) -> Optional[int]:
        """
        Initiates a Bully election starting from initiator_id.
        Returns the elected coordinator ID.
        """
        if initiator_id not in self.processes:
            self.log(f"[-] Invalid initiator ID {initiator_id}.")
            return None

        initiator = self.processes[initiator_id]
        if not initiator.is_alive():
            self.log(f"[-] Process {initiator_id} is crashed and cannot start an election.")
            return None

        self.log(f"\n=======================================================")
        self.log(f"  BULLY ELECTION INITIATED BY PROCESS {initiator_id}")
        self.log(f"=======================================================")

        higher_pids = [pid for pid in sorted(self.processes.keys()) if pid > initiator_id]

        if not higher_pids:
            # Initiator is the highest ID in the whole system
            self.log(f"[*] Process {initiator_id} has the highest ID in the system.")
            self._declare_coordinator(initiator_id)
            return initiator_id

        self.log(f"[*] Process {initiator_id} sending ELECTION messages to higher processes: {higher_pids}")
        
        higher_active_pids = []
        for h_id in higher_pids:
            self.total_messages_sent += 1
            if self.processes[h_id].is_alive():
                self.log(f"    -> [ELECTION] Process {initiator_id} ---> Process {h_id}")
                self.log(f"    <- [OK / ANSWER] Process {h_id} ---> Process {initiator_id}")
                self.total_messages_sent += 1
                higher_active_pids.append(h_id)
            else:
                self.log(f"    -> [ELECTION] Process {initiator_id} ---> Process {h_id} (TIMEOUT - No Response)")

        if not higher_active_pids:
            # None of the higher processes responded
            self.log(f"[*] No response from higher processes. Process {initiator_id} wins the election!")
            self._declare_coordinator(initiator_id)
            return initiator_id
        else:
            # Higher processes take over the election
            self.log(f"[*] Process {initiator_id} steps aside. Higher process(es) {higher_active_pids} take over.")
            
            # The highest active among them will run the election
            highest_active = max(higher_active_pids)
            return self.start_election(highest_active)

    def _declare_coordinator(self, coordinator_id: int):
        self.coordinator_id = coordinator_id
        for pid, proc in self.processes.items():
            if proc.is_alive():
                if pid == coordinator_id:
                    proc.state = ProcessState.COORDINATOR
                else:
                    proc.state = ProcessState.ACTIVE
                self.total_messages_sent += 1
                self.log(f"    [COORDINATOR ANNOUNCEMENT] Process {coordinator_id} ---> Process {pid}: 'I am the new Coordinator!'")

        self.log(f"[SUCCESS] >>> Process {coordinator_id} is elected as the COORDINATOR <<<\n")

    def get_status(self) -> str:
        lines = []
        lines.append(f"Current Coordinator: {self.coordinator_id if self.coordinator_id is not None else 'NONE'}")
        lines.append("Processes Status:")
        for pid in sorted(self.processes.keys()):
            p = self.processes[pid]
            status_tag = f"[{p.state.value}]"
            lines.append(f"  PID {pid:2d}: {status_tag}")
        return "\n".join(lines)
