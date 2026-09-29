"""
Interactive Simulator and Demos for Deadlock Detection and Resolution Algorithms.

Supports:
1. Centralized Wait-For Graph (WFG) & RAG Deadlock Detection (DFS 3-color Cycle Detection).
2. Distributed Edge-Chasing Algorithm (Chandy-Misra-Haas Probe Model).
3. Deadlock Resolution via Victim Selection Policies.
"""

import sys
from wfg import WaitForGraph, ResourceAllocationGraph, VictimPolicy
from chandy_misra_haas import ChandyMisraHaasSystem, ProcessStatus


def print_banner(title: str):
    print("\n" + "=" * 68)
    print(f"  {title}")
    print("=" * 68)


def run_wfg_circular_demo():
    print_banner("DEMO 1: CLASSIC 3-PROCESS CIRCULAR WAIT-FOR GRAPH DEADLOCK")
    print("Scenario:")
    print("  - Process P1 is holding R1 and waiting for R2 (held by P2)")
    print("  - Process P2 is holding R2 and waiting for R3 (held by P3)")
    print("  - Process P3 is holding R3 and waiting for R1 (held by P1)")
    print("  Dependencies: P1 -> P2 -> P3 -> P1\n")

    wfg = WaitForGraph()
    wfg.add_process("P1", priority=3, held_resources=1)
    wfg.add_process("P2", priority=2, held_resources=1)
    wfg.add_process("P3", priority=1, held_resources=1)

    wfg.add_wait_edge("P1", "P2", resource_id="R2")
    wfg.add_wait_edge("P2", "P3", resource_id="R3")
    wfg.add_wait_edge("P3", "P1", resource_id="R1")

    print("[1] Current Wait-For Graph State:")
    print(wfg.display())

    print("\n[2] Executing Cycle Detection (DFS 3-Color Algorithm)...")
    cycles = wfg.detect_cycles()
    if cycles:
        print(f"[!] DEADLOCK DETECTED! Found {len(cycles)} cycle(s):")
        for idx, cycle in enumerate(cycles, 1):
            print(f"    Cycle {idx}: {' ---> '.join(cycle)}")
    else:
        print("[+] No deadlock detected.")

    print("\n[3] Deadlock Resolution (Policy: LOWEST_PRIORITY)...")
    actions = wfg.resolve_deadlocks(policy=VictimPolicy.LOWEST_PRIORITY)
    for act in actions:
        print(f"    - Iteration {act['iteration']}: Cycle {' ---> '.join(act['detected_cycle'])}")
        print(f"      Selected Victim: {act['selected_victim']} (Priority={act['victim_priority']})")
        print(f"      Action: Terminated victim process and freed wait dependencies.")

    print("\n[4] Wait-For Graph After Resolution:")
    print(wfg.display())
    print(f"[*] Cycle Detection Post-Resolution: {wfg.detect_cycles()} (Deadlock Free: {not wfg.is_deadlocked()})")


def run_rag_demo():
    print_banner("DEMO 2: RESOURCE ALLOCATION GRAPH (RAG) TO WFG CONVERSION")
    print("Scenario:")
    print("  Resources: R1, R2, R3, R4")
    print("  Allocations: R1 -> P1, R2 -> P2, R3 -> P3")
    print("  Requests:    P1 requests R2, P2 requests R3, P3 requests R1, P4 requests R3 (non-deadlocked branch)\n")

    rag = ResourceAllocationGraph()
    # Priorities
    rag.add_process("P1", priority=1)
    rag.add_process("P2", priority=2)
    rag.add_process("P3", priority=3)
    rag.add_process("P4", priority=4)

    # Allocations
    rag.allocate_resource("R1", "P1")
    rag.allocate_resource("R2", "P2")
    rag.allocate_resource("R3", "P3")

    # Requests
    rag.request_resource("P1", "R2")
    rag.request_resource("P2", "R3")
    rag.request_resource("P3", "R1")
    rag.request_resource("P4", "R3")

    print("[1] Building Wait-For Graph from RAG...")
    wfg = rag.build_wait_for_graph()
    print(wfg.display())

    print("\n[2] Detecting Cycles...")
    cycles = wfg.detect_cycles()
    for idx, c in enumerate(cycles, 1):
        print(f"    Deadlock Cycle {idx}: {' ---> '.join(c)}")

    print("\n[3] Deadlock Resolution (Policy: LOWEST_PRIORITY)...")
    actions = wfg.resolve_deadlocks(policy=VictimPolicy.LOWEST_PRIORITY)
    for act in actions:
        print(f"    Aborted: {act['selected_victim']}")

    print("\n[4] Wait-For Graph Post Resolution:")
    print(wfg.display())
    print(f"[*] Remaining Cycles: {wfg.detect_cycles()} (Cycle-free: {not wfg.is_deadlocked()})")


def run_chandy_misra_haas_demo():
    print_banner("DEMO 3: CHANDY-MISRA-HAAS DISTRIBUTED EDGE-CHASING")
    print("Scenario:")
    print("  4 Distributed nodes arranged in a cycle: P1 -> P2 -> P3 -> P4 -> P1")
    print("  Process P1 suspects a deadlock and initiates edge-chasing probe.\n")

    cmh = ChandyMisraHaasSystem()
    cmh.add_process("P1", priority=2)
    cmh.add_process("P2", priority=4)
    cmh.add_process("P3", priority=1)
    cmh.add_process("P4", priority=3)

    cmh.set_dependency("P1", "P2")
    cmh.set_dependency("P2", "P3")
    cmh.set_dependency("P3", "P4")
    cmh.set_dependency("P4", "P1")

    print(cmh.get_topology_status())

    print("\n--- Running Probe Initiation ---")
    detected = cmh.initiate_probe("P1")
    print(f"\nDeadlock Detected: {detected}")

    print("\n--- Resolving Deadlock ---")
    cmh.resolve_deadlock()
    print(cmh.get_topology_status())


def run_multi_cycle_demo():
    print_banner("DEMO 4: COMPLEX MULTI-CYCLE DEADLOCK RESOLUTION")
    print("Scenario: Two interconnected cycles:")
    print("  Cycle 1: P1 -> P2 -> P1")
    print("  Cycle 2: P2 -> P3 -> P4 -> P2\n")

    wfg = WaitForGraph()
    wfg.add_process("P1", priority=5)
    wfg.add_process("P2", priority=1)  # Lowest priority node shared by both cycles
    wfg.add_process("P3", priority=4)
    wfg.add_process("P4", priority=3)

    wfg.add_wait_edge("P1", "P2")
    wfg.add_wait_edge("P2", "P1")
    wfg.add_wait_edge("P2", "P3")
    wfg.add_wait_edge("P3", "P4")
    wfg.add_wait_edge("P4", "P2")

    print("[1] Initial State:")
    print(wfg.display())

    cycles = wfg.detect_cycles()
    print(f"\n[2] Initial Detected Cycles ({len(cycles)}):")
    for c in cycles:
        print(f"    {' ---> '.join(c)}")

    print("\n[3] Resolving Deadlocks with LOWEST_PRIORITY policy...")
    actions = wfg.resolve_deadlocks(policy=VictimPolicy.LOWEST_PRIORITY)
    for act in actions:
        print(f"    Iteration {act['iteration']}: Cycle {' ---> '.join(act['detected_cycle'])} -> Aborted '{act['selected_victim']}'")

    print("\n[4] State After Resolution:")
    print(wfg.display())
    print(f"[*] Total Cycles Remaining: {len(wfg.detect_cycles())}")


def interactive_wfg():
    print_banner("INTERACTIVE WAIT-FOR GRAPH SIMULATOR")
    wfg = WaitForGraph()

    while True:
        print("\n" + "-" * 40)
        print(wfg.display())
        print("-" * 40)
        print("1. Add a Process (with Priority)")
        print("2. Add a Wait-For Edge (Pi -> Pj)")
        print("3. Remove a Wait-For Edge")
        print("4. Detect Deadlocks (Cycles)")
        print("5. Resolve Deadlocks (Auto-victim selection)")
        print("6. Reset Graph")
        print("7. Back to Main Menu")

        choice = input("Enter choice (1-7): ").strip()
        if choice == '1':
            pid = input("Enter Process ID (e.g. P1): ").strip()
            if not pid:
                continue
            prio_str = input("Enter Priority (integer, higher=more critical, default 1): ").strip()
            prio = int(prio_str) if prio_str.isdigit() else 1
            wfg.add_process(pid, priority=prio)
            print(f"[+] Added process {pid} with priority {prio}")

        elif choice == '2':
            p_from = input("Enter waiting process (e.g. P1): ").strip()
            p_to = input("Enter target process it is waiting for (e.g. P2): ").strip()
            res = input("Optional resource name being waited for (or press Enter): ").strip()
            if p_from and p_to:
                wfg.add_wait_edge(p_from, p_to, resource_id=res)
                print(f"[+] Added wait edge: {p_from} ---> {p_to}")

        elif choice == '3':
            p_from = input("Enter waiting process: ").strip()
            p_to = input("Enter target process: ").strip()
            wfg.remove_wait_edge(p_from, p_to)
            print(f"[-] Removed wait edge: {p_from} ---> {p_to}")

        elif choice == '4':
            cycles = wfg.detect_cycles()
            if cycles:
                print(f"\n[!] DEADLOCK DETECTED! Found {len(cycles)} cycle(s):")
                for idx, c in enumerate(cycles, 1):
                    print(f"    Cycle {idx}: {' ---> '.join(c)}")
            else:
                print("\n[+] Graph is DEADLOCK FREE! No cycles detected.")

        elif choice == '5':
            cycles = wfg.detect_cycles()
            if not cycles:
                print("\n[+] No deadlock to resolve.")
                continue

            print("\nSelect Victim Policy:")
            print("1. LOWEST_PRIORITY (Default)")
            print("2. FEWEST_RESOURCES")
            print("3. HIGHEST_PID")
            print("4. LOWEST_PID")
            pol_choice = input("Choice (1-4): ").strip()
            policy_map = {
                '1': VictimPolicy.LOWEST_PRIORITY,
                '2': VictimPolicy.FEWEST_RESOURCES,
                '3': VictimPolicy.HIGHEST_PID,
                '4': VictimPolicy.LOWEST_PID
            }
            policy = policy_map.get(pol_choice, VictimPolicy.LOWEST_PRIORITY)

            actions = wfg.resolve_deadlocks(policy=policy)
            print(f"\n[SUCCESS] Deadlock resolution completed using policy {policy.value}:")
            for act in actions:
                print(f"  - Aborted {act['selected_victim']} from cycle {' ---> '.join(act['detected_cycle'])}")

        elif choice == '6':
            wfg = WaitForGraph()
            print("[*] Graph cleared.")

        elif choice == '7':
            break


def interactive_cmh():
    print_banner("INTERACTIVE CHANDY-MISRA-HAAS DISTRIBUTED PROBE SIMULATOR")
    cmh = ChandyMisraHaasSystem()

    while True:
        print(cmh.get_topology_status())
        print("\n1. Add / Configure a Process")
        print("2. Set a Wait Dependency (Pi waits for Pj)")
        print("3. Initiate Deadlock Probe from a Process")
        print("4. Resolve Detected Deadlock")
        print("5. Reset Topology")
        print("6. Back to Main Menu")

        choice = input("Enter choice (1-6): ").strip()
        if choice == '1':
            pid = input("Enter Process ID (e.g. P1): ").strip()
            prio_str = input("Enter Priority (integer, default 1): ").strip()
            prio = int(prio_str) if prio_str.isdigit() else 1
            cmh.add_process(pid, priority=prio)
            print(f"[+] Process {pid} configured.")

        elif choice == '2':
            p_wait = input("Enter blocked process: ").strip()
            p_target = input("Enter process it is waiting for: ").strip()
            if p_wait and p_target:
                cmh.set_dependency(p_wait, p_target)
                print(f"[+] Dependency configured: {p_wait} is blocked waiting on {p_target}")

        elif choice == '3':
            initiator = input("Enter initiator Process ID: ").strip()
            cmh.initiate_probe(initiator)

        elif choice == '4':
            cmh.resolve_deadlock()

        elif choice == '5':
            cmh = ChandyMisraHaasSystem()
            print("[*] Topology reset.")

        elif choice == '6':
            break


def main():
    while True:
        print_banner("DISTRIBUTED SYSTEMS ASSIGNMENT 3: DEADLOCK DETECTION & RESOLUTION")
        print("1. Run Demo 1: Classic Circular WFG Deadlock (P1 -> P2 -> P3 -> P1)")
        print("2. Run Demo 2: Resource Allocation Graph (RAG) to WFG Conversion")
        print("3. Run Demo 3: Chandy-Misra-Haas Distributed Edge-Chasing")
        print("4. Run Demo 4: Complex Multi-Cycle Deadlock Resolution")
        print("5. Interactive Wait-For Graph (WFG) Simulator")
        print("6. Interactive Chandy-Misra-Haas Distributed Simulator")
        print("7. Exit")

        choice = input("\nSelect an option (1-7): ").strip()
        if choice == '1':
            run_wfg_circular_demo()
        elif choice == '2':
            run_rag_demo()
        elif choice == '3':
            run_chandy_misra_haas_demo()
        elif choice == '4':
            run_multi_cycle_demo()
        elif choice == '5':
            interactive_wfg()
        elif choice == '6':
            interactive_cmh()
        elif choice == '7':
            print("\nExiting Deadlock Detection Simulator. Goodbye!\n")
            sys.exit(0)
        else:
            print("[-] Invalid option, please choose 1-7.")


if __name__ == "__main__":
    main()
