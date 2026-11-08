import json
import unittest

from traceguard.normalize import normalize, verify_workload


# Deliberately list exit before exec to model out-of-order delivery.
WIRE = [
    "TG\texec\t100\t10\t80\t0\t0\ttgp-test\n",
    "TG\tfork\t120\t42\t115\t10\t80\n",
    "TG\texit\t160\t42\t115\n",
    "TG\texec\t140\t42\t115\t10\t80\ttgc-test\n",
]


class LiveNormalizationTests(unittest.TestCase):
    def test_verified_wire_format_round_trips_to_replay(self):
        events = normalize(WIRE, "lab", "boot-a")
        lines, parent_pid, child_pid = verify_workload(events, "tgp-test", "tgc-test")
        self.assertEqual((parent_pid, child_pid), (10, 42))
        child_exec = json.loads(lines[-1])
        self.assertEqual(child_exec["process"], {"pid": 42, "start_ns": 115})
        self.assertEqual(child_exec["parent"], {"pid": 10, "start_ns": 80})
        self.assertIsNone(child_exec["comm_truncated"])

    def test_incomplete_or_wrong_parent_capture_cannot_pass(self):
        without_exit = normalize([WIRE[0], WIRE[1], WIRE[3]], "lab", "boot-a")
        with self.assertRaisesRegex(ValueError, "complete fork"):
            verify_workload(without_exit, "tgp-test", "tgc-test")

        events = normalize(WIRE, "lab", "boot-a")
        events[1]["parent"]["start_ns"] = 70
        with self.assertRaisesRegex(ValueError, "parent identity"):
            verify_workload(events, "tgp-test", "tgc-test")

    def test_rejects_probe_diagnostics(self):
        with self.assertRaisesRegex(ValueError, "unexpected bpftrace output"):
            normalize([*WIRE, "Lost 3 events\n"], "lab", "boot-a")
