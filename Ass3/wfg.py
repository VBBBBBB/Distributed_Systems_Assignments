"""
Wait-For Graph (WFG) and Resource Allocation Graph (RAG) Deadlock Detection Engine.

Theory:
- In a Resource Allocation Graph (RAG), nodes are Processes (P) and Resources (R).
  - Allocation Edge: R_k -> P_i (Resource R_k is allocated to Process P_i).
  - Request Edge: P_i -> R_k (Process P_i is requesting Resource R_k).
- A Wait-For Graph (WFG) is constructed directly between processes:
  - Directed Edge: P_i -> P_j means Process P_i is waiting for a resource currently held by P_j.
- In single-unit resource systems, a cycle in the WFG is a NECESSARY and SUFFICIENT condition for DEADLOCK.
- In multi-unit systems or general WFGs, cycle detection via Depth First Search (DFS) with 3-state coloring
  (WHITE, GRAY, BLACK) pinpoints all elementary deadlock cycles.

Deadlock Resolution:
- Select a victim process based on a policy (Lowest Priority, Fewest Resources, Highest PID, etc.).
- Abort/terminate the victim process, release all resources it holds, and re-allocate them to waiting processes.
- Repeat until the WFG is completely cycle-free.
"""

from typing import List, Dict, Set, Tuple, Optional
from enum import Enum
import copy


class VictimPolicy(Enum):
    LOWEST_PRIORITY = "LOWEST_PRIORITY"
    FEWEST_RESOURCES = "FEWEST_RESOURCES"
    HIGHEST_PID = "HIGHEST_PID"
    LOWEST_PID = "LOWEST_PID"


class NodeColor(Enum):
    WHITE = 0  # Unvisited
    GRAY = 1   # Currently visiting (in recursion stack)
    BLACK = 2  # Completely visited


class ResourceAllocationGraph:
    """
    Maintains resources, processes, allocations, and requests.
    Translates RAG to a direct Wait-For Graph (WFG).
    """
    def __init__(self):
        self.processes: Set[str] = set()
        self.resources: Set[str] = set()
        # allocations: resource -> process holding it (assuming 1 unit per resource or exclusive hold)
        self.allocations: Dict[str, str] = {}
        # requests: process -> set of resources it is waiting for
        self.requests: Dict[str, Set[str]] = {}
        # process priorities (default priority = 1, higher value = higher priority)
        self.priorities: Dict[str, int] = {}

    def add_process(self, pid: str, priority: int = 1):
        self.processes.add(pid)
        self.priorities[pid] = priority
        if pid not in self.requests:
            self.requests[pid] = set()

    def add_resource(self, rid: str):
        self.resources.add(rid)

    def allocate_resource(self, rid: str, pid: str):
        """Allocate resource rid to process pid."""
        self.add_process(pid)
        self.add_resource(rid)
        self.allocations[rid] = pid
        # If it was previously waiting for it, remove request
        if pid in self.requests and rid in self.requests[pid]:
            self.requests[pid].remove(rid)

    def request_resource(self, pid: str, rid: str):
        """Process pid requests resource rid."""
        self.add_process(pid)
        self.add_resource(rid)
        self.requests[pid].add(rid)

    def release_resource(self, rid: str):
        """Release resource rid."""
        if rid in self.allocations:
            del self.allocations[rid]

    def build_wait_for_graph(self) -> 'WaitForGraph':
        """
        Convert RAG to WFG:
        If P_i requests R_k and R_k is held by P_j (and P_i != P_j),
        then add directed edge P_i -> P_j.
        """
        wfg = WaitForGraph()
        for p in self.processes:
            wfg.add_process(p, priority=self.priorities.get(p, 1))

        for p_requester, requested_res in self.requests.items():
            for rid in requested_res:
                holder = self.allocations.get(rid)
                if holder and holder != p_requester:
                    wfg.add_wait_edge(p_requester, holder, resource_id=rid)

        return wfg


class WaitForGraph:
    """
    Explicit Wait-For Graph between processes.
    Vertices: Processes
    Directed Edge: P_i -> P_j (P_i is waiting for P_j)
    """
    def __init__(self):
        self.processes: Set[str] = set()
        # adjacency: p_i -> set of processes p_j that p_i is waiting for
        self.adj: Dict[str, Set[str]] = {}
        # edge metadata: (p_i, p_j) -> resource name
        self.edge_resources: Dict[Tuple[str, str], str] = {}
        # Process priorities
        self.priorities: Dict[str, int] = {}
        # Process held resources count (for victim selection)
        self.held_resources_count: Dict[str, int] = {}

    def add_process(self, pid: str, priority: Optional[int] = None, held_resources: Optional[int] = None):
        self.processes.add(pid)
        if pid not in self.adj:
            self.adj[pid] = set()
        if priority is not None:
            self.priorities[pid] = priority
        elif pid not in self.priorities:
            self.priorities[pid] = 1

        if held_resources is not None:
            self.held_resources_count[pid] = held_resources
        elif pid not in self.held_resources_count:
            self.held_resources_count[pid] = 0

    def add_wait_edge(self, p_from: str, p_to: str, resource_id: str = ""):
        self.add_process(p_from)
        self.add_process(p_to)
        self.adj[p_from].add(p_to)
        if resource_id:
            self.edge_resources[(p_from, p_to)] = resource_id

    def remove_wait_edge(self, p_from: str, p_to: str):
        if p_from in self.adj and p_to in self.adj[p_from]:
            self.adj[p_from].remove(p_to)
            self.edge_resources.pop((p_from, p_to), None)

    def remove_process(self, pid: str):
        """Remove a process and all incoming & outgoing wait-for edges."""
        if pid in self.processes:
            self.processes.remove(pid)
        if pid in self.adj:
            del self.adj[pid]
        self.priorities.pop(pid, None)
        self.held_resources_count.pop(pid, None)

        # Remove outgoing edges to pid
        for p in list(self.adj.keys()):
            if pid in self.adj[p]:
                self.adj[p].remove(pid)

        # Clean edge_resources
        keys_to_del = [k for k in self.edge_resources if k[0] == pid or k[1] == pid]
        for k in keys_to_del:
            del self.edge_resources[k]

    def detect_cycles(self) -> List[List[str]]:
        """
        Detects all elementary cycles in the Wait-For Graph using DFS with 3-state coloring.
        Returns a list of cycles, where each cycle is a list of node IDs forming the loop:
        e.g., ['P1', 'P2', 'P3', 'P1']
        """
        color: Dict[str, NodeColor] = {p: NodeColor.WHITE for p in self.processes}
        parent_map: Dict[str, str] = {}
        all_cycles: List[List[str]] = []
        visited_cycles_signatures: Set[Tuple[str, ...]] = set()

        def dfs(u: str, current_path: List[str]):
            color[u] = NodeColor.GRAY
            current_path.append(u)

            # Sort neighbors for deterministic traversal
            for v in sorted(self.adj.get(u, set())):
                if color.get(v, NodeColor.WHITE) == NodeColor.GRAY:
                    # Cycle found! Extract cycle from v to u
                    idx = current_path.index(v)
                    cycle = current_path[idx:] + [v]

                    # Canonical representation of cycle to avoid duplicates (min rotation)
                    raw_cycle = cycle[:-1]
                    min_idx = raw_cycle.index(min(raw_cycle))
                    canonical = tuple(raw_cycle[min_idx:] + raw_cycle[:min_idx])

                    if canonical not in visited_cycles_signatures:
                        visited_cycles_signatures.add(canonical)
                        all_cycles.append(cycle)

                elif color.get(v, NodeColor.WHITE) == NodeColor.WHITE:
                    dfs(v, current_path)

            current_path.pop()
            color[u] = NodeColor.BLACK

        for node in sorted(self.processes):
            if color[node] == NodeColor.WHITE:
                dfs(node, [])

        return all_cycles

    def is_deadlocked(self) -> bool:
        return len(self.detect_cycles()) > 0

    def select_victim(self, cycle: List[str], policy: VictimPolicy = VictimPolicy.LOWEST_PRIORITY) -> str:
        """
        Selects a victim process from a deadlock cycle based on the chosen policy.
        Cycle is represented as ['P1', 'P2', ..., 'P1'].
        """
        nodes_in_cycle = list(set(cycle[:-1]))
        if not nodes_in_cycle:
            return ""

        if policy == VictimPolicy.LOWEST_PRIORITY:
            # Min priority value (or lowest PID if tied)
            return min(nodes_in_cycle, key=lambda p: (self.priorities.get(p, 1), p))

        elif policy == VictimPolicy.FEWEST_RESOURCES:
            # Process holding fewest resources (least rollback cost)
            return min(nodes_in_cycle, key=lambda p: (self.held_resources_count.get(p, 0), p))

        elif policy == VictimPolicy.HIGHEST_PID:
            # Highest numerical PID (or lexicographical)
            try:
                return max(nodes_in_cycle, key=lambda p: int(''.join(filter(str.isdigit, p)) or 0))
            except ValueError:
                return max(nodes_in_cycle)

        elif policy == VictimPolicy.LOWEST_PID:
            try:
                return min(nodes_in_cycle, key=lambda p: int(''.join(filter(str.isdigit, p)) or 0))
            except ValueError:
                return min(nodes_in_cycle)

        return nodes_in_cycle[0]

    def resolve_deadlocks(self, policy: VictimPolicy = VictimPolicy.LOWEST_PRIORITY) -> List[Dict]:
        """
        Iteratively detects cycles, selects victims, and terminates them until no cycles remain.
        Returns a log of actions taken during resolution.
        """
        resolution_log: List[Dict] = []
        iteration = 1

        while True:
            cycles = self.detect_cycles()
            if not cycles:
                break

            target_cycle = cycles[0]
            victim = self.select_victim(target_cycle, policy)

            log_entry = {
                "iteration": iteration,
                "detected_cycle": target_cycle,
                "policy": policy.value,
                "selected_victim": victim,
                "victim_priority": self.priorities.get(victim, 1),
                "held_resources": self.held_resources_count.get(victim, 0)
            }
            resolution_log.append(log_entry)

            # Terminate victim
            self.remove_process(victim)
            iteration += 1

        return resolution_log

    def display(self) -> str:
        """Textual visualization of the Wait-For Graph."""
        lines = []
        lines.append("Processes in WFG: " + (", ".join(sorted(self.processes)) if self.processes else "(none)"))
        lines.append("Wait-For Dependencies:")
        if not self.processes:
            lines.append("  (Empty graph)")
            return "\n".join(lines)

        has_edges = False
        for p in sorted(self.processes):
            waiting_on = sorted(self.adj.get(p, set()))
            if waiting_on:
                has_edges = True
                details = []
                for target in waiting_on:
                    res = self.edge_resources.get((p, target))
                    res_str = f" [holding {res}]" if res else ""
                    details.append(f"{target}{res_str}")
                lines.append(f"  {p} ---> {', '.join(details)}")
            else:
                lines.append(f"  {p} ---> (None, running or idle)")

        return "\n".join(lines)
