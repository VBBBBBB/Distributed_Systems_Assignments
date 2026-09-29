"""
Unit and Integration Tests for Deadlock Detection & Resolution Algorithms.
"""

import unittest
from wfg import WaitForGraph, ResourceAllocationGraph, VictimPolicy
from chandy_misra_haas import ChandyMisraHaasSystem, ProcessStatus


class TestWaitForGraph(unittest.TestCase):
    def setUp(self):
        self.wfg = WaitForGraph()

    def test_empty_graph(self):
        self.assertEqual(len(self.wfg.detect_cycles()), 0)
        self.assertFalse(self.wfg.is_deadlocked())

    def test_acyclic_graph(self):
        # P1 -> P2 -> P3 -> P4 (No cycle)
        self.wfg.add_wait_edge("P1", "P2")
        self.wfg.add_wait_edge("P2", "P3")
        self.wfg.add_wait_edge("P3", "P4")

        cycles = self.wfg.detect_cycles()
        self.assertEqual(len(cycles), 0)
        self.assertFalse(self.wfg.is_deadlocked())

    def test_two_process_deadlock(self):
        # P1 <-> P2
        self.wfg.add_wait_edge("P1", "P2")
        self.wfg.add_wait_edge("P2", "P1")

        cycles = self.wfg.detect_cycles()
        self.assertEqual(len(cycles), 1)
        self.assertTrue(self.wfg.is_deadlocked())
        self.assertEqual(set(cycles[0]), {"P1", "P2"})

    def test_three_process_circular_deadlock(self):
        # P1 -> P2 -> P3 -> P1
        self.wfg.add_wait_edge("P1", "P2")
        self.wfg.add_wait_edge("P2", "P3")
        self.wfg.add_wait_edge("P3", "P1")

        cycles = self.wfg.detect_cycles()
        self.assertEqual(len(cycles), 1)
        self.assertTrue(self.wfg.is_deadlocked())
        self.assertEqual(set(cycles[0]), {"P1", "P2", "P3"})

    def test_multiple_cycles(self):
        # Cycle 1: P1 -> P2 -> P1
        # Cycle 2: P3 -> P4 -> P3
        self.wfg.add_wait_edge("P1", "P2")
        self.wfg.add_wait_edge("P2", "P1")
        self.wfg.add_wait_edge("P3", "P4")
        self.wfg.add_wait_edge("P4", "P3")

        cycles = self.wfg.detect_cycles()
        self.assertEqual(len(cycles), 2)
        self.assertTrue(self.wfg.is_deadlocked())

    def test_resolution_by_lowest_priority(self):
        self.wfg.add_process("P1", priority=10)
        self.wfg.add_process("P2", priority=1)   # Victim
        self.wfg.add_process("P3", priority=5)

        self.wfg.add_wait_edge("P1", "P2")
        self.wfg.add_wait_edge("P2", "P3")
        self.wfg.add_wait_edge("P3", "P1")

        actions = self.wfg.resolve_deadlocks(policy=VictimPolicy.LOWEST_PRIORITY)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["selected_victim"], "P2")
        self.assertFalse(self.wfg.is_deadlocked())
        self.assertNotIn("P2", self.wfg.processes)

    def test_resolution_by_fewest_resources(self):
        self.wfg.add_process("P1", held_resources=5)
        self.wfg.add_process("P2", held_resources=1)  # Victim
        self.wfg.add_process("P3", held_resources=3)

        self.wfg.add_wait_edge("P1", "P2")
        self.wfg.add_wait_edge("P2", "P3")
        self.wfg.add_wait_edge("P3", "P1")

        actions = self.wfg.resolve_deadlocks(policy=VictimPolicy.FEWEST_RESOURCES)
        self.assertEqual(actions[0]["selected_victim"], "P2")
        self.assertFalse(self.wfg.is_deadlocked())


class TestResourceAllocationGraph(unittest.TestCase):
    def test_rag_to_wfg_deadlock(self):
        rag = ResourceAllocationGraph()
        rag.allocate_resource("R1", "P1")
        rag.allocate_resource("R2", "P2")

        rag.request_resource("P1", "R2")
        rag.request_resource("P2", "R1")

        wfg = rag.build_wait_for_graph()
        self.assertTrue(wfg.is_deadlocked())
        cycles = wfg.detect_cycles()
        self.assertEqual(len(cycles), 1)

    def test_rag_acyclic(self):
        rag = ResourceAllocationGraph()
        rag.allocate_resource("R1", "P1")
        rag.allocate_resource("R2", "P2")

        rag.request_resource("P1", "R2")
        # P2 does not request R1, requests R3 (available or free)
        wfg = rag.build_wait_for_graph()
        self.assertFalse(wfg.is_deadlocked())


class TestChandyMisraHaas(unittest.TestCase):
    def setUp(self):
        self.cmh = ChandyMisraHaasSystem()

    def test_active_initiator_no_probe(self):
        self.cmh.add_process("P1")
        detected = self.cmh.initiate_probe("P1")
        self.assertFalse(detected)

    def test_acyclic_probe_termination(self):
        # P1 -> P2 -> P3 (P3 is active, not blocked)
        self.cmh.add_process("P1")
        self.cmh.add_process("P2")
        self.cmh.add_process("P3")

        self.cmh.set_dependency("P1", "P2")
        self.cmh.set_dependency("P2", "P3")

        detected = self.cmh.initiate_probe("P1")
        self.assertFalse(detected)

    def test_circular_probe_deadlock_detection(self):
        # P1 -> P2 -> P3 -> P1
        self.cmh.set_dependency("P1", "P2")
        self.cmh.set_dependency("P2", "P3")
        self.cmh.set_dependency("P3", "P1")

        detected = self.cmh.initiate_probe("P1")
        self.assertTrue(detected)
        self.assertEqual(len(self.cmh.detected_deadlocks), 1)

    def test_probe_deadlock_resolution(self):
        self.cmh.add_process("P1", priority=10)
        self.cmh.add_process("P2", priority=1)   # Lowest priority
        self.cmh.add_process("P3", priority=5)

        self.cmh.set_dependency("P1", "P2")
        self.cmh.set_dependency("P2", "P3")
        self.cmh.set_dependency("P3", "P1")

        self.cmh.initiate_probe("P1")
        self.cmh.resolve_deadlock()

        # P2 was aborted, so P1 is unblocked
        self.assertEqual(self.cmh.processes["P2"].status, ProcessStatus.ABORTED)
        self.assertEqual(self.cmh.processes["P1"].status, ProcessStatus.ACTIVE)


if __name__ == "__main__":
    unittest.main()
