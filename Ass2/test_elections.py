"""
Unit and Integration Tests for Bully and Ring Election Algorithms.
"""

import unittest
from bully import BullyElectionSystem, ProcessState as BullyProcessState
from ring import RingElectionSystem, ProcessState as RingProcessState


class TestBullyAlgorithm(unittest.TestCase):
    def setUp(self):
        self.pids = [1, 2, 3, 4, 5, 6, 7]
        self.system = BullyElectionSystem(self.pids)

    def test_initial_coordinator(self):
        self.assertEqual(self.system.coordinator_id, 7)
        self.assertEqual(self.system.processes[7].state, BullyProcessState.COORDINATOR)
        self.assertEqual(self.system.processes[1].state, BullyProcessState.ACTIVE)

    def test_coordinator_crash_and_election_from_middle(self):
        # Crash coordinator 7
        self.system.crash_process(7)
        self.assertIsNone(self.system.coordinator_id)

        # Process 3 initiates election
        elected = self.system.start_election(3)
        self.assertEqual(elected, 6)
        self.assertEqual(self.system.coordinator_id, 6)
        self.assertEqual(self.system.processes[6].state, BullyProcessState.COORDINATOR)

    def test_multiple_crashes(self):
        # Crash 7, 6, 5
        self.system.crash_process(7)
        self.system.crash_process(6)
        self.system.crash_process(5)

        # Process 2 initiates election
        elected = self.system.start_election(2)
        self.assertEqual(elected, 4)
        self.assertEqual(self.system.coordinator_id, 4)

    def test_recovered_highest_node_bullies(self):
        self.system.crash_process(7)
        self.system.start_election(1)
        self.assertEqual(self.system.coordinator_id, 6)

        # Process 7 recovers, which triggers automatic election
        self.system.recover_process(7)
        self.assertEqual(self.system.coordinator_id, 7)
        self.assertEqual(self.system.processes[7].state, BullyProcessState.COORDINATOR)


class TestRingAlgorithm(unittest.TestCase):
    def setUp(self):
        self.ring_order = [1, 3, 5, 2, 6, 4]
        self.system = RingElectionSystem(self.ring_order)

    def test_initial_coordinator(self):
        self.assertEqual(self.system.coordinator_id, 6)
        self.assertEqual(self.system.processes[6].state, RingProcessState.COORDINATOR)

    def test_coordinator_crash_and_election(self):
        self.system.crash_process(6)
        self.assertIsNone(self.system.coordinator_id)

        elected = self.system.start_election(3)
        self.assertEqual(elected, 5)
        self.assertEqual(self.system.coordinator_id, 5)
        self.assertEqual(self.system.processes[5].state, RingProcessState.COORDINATOR)

    def test_multiple_consecutive_crashes(self):
        # In ring [1, 3, 5, 2, 6, 4]
        # Crash 5, 2, 6
        self.system.crash_process(5)
        self.system.crash_process(2)
        self.system.crash_process(6)

        # Process 3 initiates election -> next alive is 4 -> 1 -> 3
        elected = self.system.start_election(3)
        self.assertEqual(elected, 4)
        self.assertEqual(self.system.coordinator_id, 4)

    def test_recovery_and_re_election(self):
        self.system.crash_process(6)
        self.system.start_election(1)
        self.assertEqual(self.system.coordinator_id, 5)

        # Process 6 recovers
        self.system.recover_process(6)
        self.assertEqual(self.system.coordinator_id, 6)


if __name__ == "__main__":
    unittest.main()
