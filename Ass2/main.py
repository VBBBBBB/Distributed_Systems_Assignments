"""
Interactive Simulator for Distributed Coordinator Election (Bully & Ring Algorithms).

Run this script to interactively simulate leader election, crash nodes, recover nodes,
or run pre-configured demo test scenarios.
"""

import sys
from bully import BullyElectionSystem
from ring import RingElectionSystem


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


def run_bully_demo():
    print_banner("RUNNING BULLY ALGORITHM AUTOMATED DEMO")
    pids = [1, 2, 3, 4, 5, 6, 7]
    print(f"1. Initializing Bully System with processes: {pids}")
    bully = BullyElectionSystem(pids)
    print(bully.get_status())

    print("\n2. Coordinator Process 7 CRASHES!")
    bully.crash_process(7)
    print(bully.get_status())

    print("\n3. Process 2 detects failure and starts an Election:")
    bully.start_election(2)
    print(bully.get_status())

    print("\n4. Former Coordinator Process 7 RECOVERS and reclaims leadership:")
    bully.recover_process(7)
    print(bully.get_status())
    print(f"\nTotal messages exchanged during demo: {bully.total_messages_sent}")


def run_ring_demo():
    print_banner("RUNNING RING ALGORITHM AUTOMATED DEMO")
    ring_order = [1, 3, 5, 2, 6, 4]
    print(f"1. Initializing Ring System with topology: {ring_order}")
    ring = RingElectionSystem(ring_order)
    print(ring.get_status())

    print("\n2. Coordinator Process 6 and Process 4 CRASH!")
    ring.crash_process(6)
    ring.crash_process(4)
    print(ring.get_status())

    print("\n3. Process 3 detects failure and starts an Election:")
    ring.start_election(3)
    print(ring.get_status())

    print("\n4. Process 6 RECOVERS and starts an election:")
    ring.recover_process(6)
    print(ring.get_status())
    print(f"\nTotal messages exchanged during demo: {ring.total_messages_sent}")


def interactive_bully():
    print_banner("INTERACTIVE BULLY ALGORITHM SIMULATOR")
    try:
        raw_pids = input("Enter Process IDs separated by spaces (default: 1 2 3 4 5 6): ").strip()
        pids = [int(x) for x in raw_pids.split()] if raw_pids else [1, 2, 3, 4, 5, 6]
    except ValueError:
        print("[!] Invalid input, using default [1, 2, 3, 4, 5, 6]")
        pids = [1, 2, 3, 4, 5, 6]

    system = BullyElectionSystem(pids)

    while True:
        print("\n" + "-" * 40)
        print(system.get_status())
        print("-" * 40)
        print("1. Crash a process")
        print("2. Recover a process")
        print("3. Start Election from a process")
        print("4. Back to Main Menu")

        choice = input("Enter option (1-4): ").strip()
        if choice == '1':
            try:
                pid = int(input("Enter PID to crash: ").strip())
                system.crash_process(pid)
            except ValueError:
                print("[-] Please enter a valid numeric PID.")
        elif choice == '2':
            try:
                pid = int(input("Enter PID to recover: ").strip())
                system.recover_process(pid)
            except ValueError:
                print("[-] Please enter a valid numeric PID.")
        elif choice == '3':
            try:
                pid = int(input("Enter initiator PID: ").strip())
                system.start_election(pid)
            except ValueError:
                print("[-] Please enter a valid numeric PID.")
        elif choice == '4':
            break
        else:
            print("[-] Invalid choice.")


def interactive_ring():
    print_banner("INTERACTIVE RING ALGORITHM SIMULATOR")
    try:
        raw_pids = input("Enter Ring Process Order separated by spaces (default: 1 2 3 4 5 6): ").strip()
        pids = [int(x) for x in raw_pids.split()] if raw_pids else [1, 2, 3, 4, 5, 6]
    except ValueError:
        print("[!] Invalid input, using default [1, 2, 3, 4, 5, 6]")
        pids = [1, 2, 3, 4, 5, 6]

    system = RingElectionSystem(pids)

    while True:
        print("\n" + "-" * 40)
        print(system.get_status())
        print("-" * 40)
        print("1. Crash a process")
        print("2. Recover a process")
        print("3. Start Election from a process")
        print("4. Back to Main Menu")

        choice = input("Enter option (1-4): ").strip()
        if choice == '1':
            try:
                pid = int(input("Enter PID to crash: ").strip())
                system.crash_process(pid)
            except ValueError:
                print("[-] Please enter a valid numeric PID.")
        elif choice == '2':
            try:
                pid = int(input("Enter PID to recover: ").strip())
                system.recover_process(pid)
            except ValueError:
                print("[-] Please enter a valid numeric PID.")
        elif choice == '3':
            try:
                pid = int(input("Enter initiator PID: ").strip())
                system.start_election(pid)
            except ValueError:
                print("[-] Please enter a valid numeric PID.")
        elif choice == '4':
            break
        else:
            print("[-] Invalid choice.")


def main():
    while True:
        print_banner("DISTRIBUTED COORDINATOR ELECTION SIMULATOR")
        print("1. Bully Algorithm (Interactive Mode)")
        print("2. Ring Algorithm (Interactive Mode)")
        print("3. Run Bully Algorithm Demo")
        print("4. Run Ring Algorithm Demo")
        print("5. Exit")

        choice = input("\nSelect an option (1-5): ").strip()
        if choice == '1':
            interactive_bully()
        elif choice == '2':
            interactive_ring()
        elif choice == '3':
            run_bully_demo()
        elif choice == '4':
            run_ring_demo()
        elif choice == '5':
            print("\nExiting simulator. Good luck with your assignment!\n")
            sys.exit(0)
        else:
            print("[-] Invalid option, please choose 1-5.")


if __name__ == "__main__":
    main()
