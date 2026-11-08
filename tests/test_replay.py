import json
from pathlib import Path
import unittest

from traceguard.replay import replay


FIXTURE = Path(__file__).parent / "fixtures" / "lifecycle.jsonl"


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.lines = FIXTURE.read_text(encoding="utf-8").splitlines()

    def test_tracks_pid_reuse_and_only_links_exact_parent_identity(self):
        snapshot = replay(self.lines)
        shell, first_child, second_child, orphan = snapshot["processes"]
        self.assertEqual(shell["pid"], 10)
        self.assertIsNone(shell["parent"])
        self.assertEqual((first_child["pid"], second_child["pid"]), (42, 42))
        self.assertEqual(first_child["exit_ns"], 160)
        self.assertIsNone(second_child["exit_ns"])
        self.assertEqual(first_child["comm"], "sleep")
        self.assertEqual(second_child["comm"], "date")
        self.assertTrue(first_child["fork_seen"])
        self.assertEqual(first_child["parent"], {"pid": 10, "start_ns": 80, "observed": True})
        self.assertEqual(orphan["parent"], {"pid": 42, "start_ns": 30, "observed": False})
        self.assertTrue(orphan["comm_truncated"])
        self.assertEqual(snapshot["lost_events"], 2)

    def test_reordered_capture_replays_to_same_snapshot(self):
        self.assertEqual(replay(self.lines), replay(reversed(self.lines)))

    def test_exec_preserves_identity_and_tied_timestamps_use_sequence(self):
        first = json.loads(self.lines[0])
        later = dict(first, seq=2, comm="python", comm_truncated=None)
        snapshot = replay([json.dumps(later), self.lines[0]])
        self.assertEqual(len(snapshot["processes"]), 1)
        self.assertEqual(snapshot["processes"][0]["comm"], "python")
        self.assertIsNone(snapshot["processes"][0]["comm_truncated"])

    def test_rejects_mixed_boots_and_duplicate_sequence(self):
        other_boot = json.loads(self.lines[0])
        other_boot.update(boot_id="boot-b", seq=99)
        with self.assertRaisesRegex(ValueError, "single host and boot"):
            replay([*self.lines, json.dumps(other_boot)])
        with self.assertRaisesRegex(ValueError, "duplicate seq"):
            replay([*self.lines, self.lines[0]])


if __name__ == "__main__":
    unittest.main()
