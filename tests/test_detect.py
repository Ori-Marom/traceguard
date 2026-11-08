import json
from pathlib import Path
import unittest

from traceguard.detect import WINDOW_NS, detect


FIXTURE = Path(__file__).parent / "fixtures" / "connection-refusals.jsonl"


def analyze(events):
    return detect(json.dumps(event) for event in events)


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.events = [
            json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        ]
        self.first, self.second = self.events[2], self.events[4]

    def test_matches_exact_evidence_in_replay_order_and_deduplicates(self):
        more = dict(self.second, seq=6, ts_ns=501, port=41005)
        result = analyze(reversed([*self.events, more]))
        self.assertEqual(len(result["alerts"]), 1)
        alert = result["alerts"][0]
        self.assertEqual(alert["process"], {"pid": 42, "start_ns": 80})
        self.assertTrue(alert["process_observed"])
        self.assertEqual([item["seq"] for item in alert["evidence"]], [3, 5])

    def test_one_second_boundary_is_inclusive(self):
        boundary = self.first["ts_ns"] + WINDOW_NS
        pair = [self.first, dict(self.second, ts_ns=boundary)]
        self.assertEqual(len(analyze(pair)["alerts"]), 1)
        pair[1]["ts_ns"] += 1
        self.assertEqual(analyze(pair)["alerts"], [])

    def test_ignores_retries_to_one_endpoint_and_pending_connections(self):
        repeat = dict(self.second, address=self.first["address"], port=self.first["port"])
        pending = dict(self.second, result=-115)
        self.assertEqual(analyze([self.first, repeat])["alerts"], [])
        self.assertEqual(analyze([self.first, pending])["alerts"], [])

    def test_does_not_join_a_reused_pid(self):
        later = dict(self.second, process={"pid": 42, "start_ns": 450})
        self.assertEqual(analyze([self.first, later])["alerts"], [])

    def test_reports_loss_and_requires_two_observed_refusals(self):
        loss = {
            "version": 1, "host_id": "lab", "boot_id": "boot-a",
            "seq": 6, "ts_ns": 600, "type": "loss", "count": 2,
        }
        incomplete = analyze([self.first, loss])
        self.assertEqual(incomplete["lost_events"], 2)
        self.assertEqual(incomplete["alerts"], [])

        result = analyze([self.first, self.second, loss])
        self.assertEqual(result["lost_events"], 2)
        self.assertFalse(result["alerts"][0]["process_observed"])
