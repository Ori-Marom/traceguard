import json
from pathlib import Path
import unittest

from traceguard.report import render_report


FIXTURES = Path(__file__).parent / "fixtures"


class ReportTests(unittest.TestCase):
    def test_alert_links_to_process_and_exact_evidence(self):
        capture = FIXTURES / "connection-refusals.jsonl"
        report = render_report(capture.read_text(encoding="utf-8").splitlines(), capture.name)
        for seq in (3, 5):
            self.assertIn(f'href="#event-{seq}"', report)
            self.assertIn(f'id="event-{seq}"', report)
        self.assertIn('href="#process-42-80"', report)
        self.assertIn('id="process-42-80"', report)
        self.assertIn("[::1]:41004", report)

    def test_tree_separates_reused_pids_and_labels_unobserved_parent(self):
        capture = FIXTURES / "lifecycle.jsonl"
        report = render_report(capture.read_text(encoding="utf-8").splitlines(), capture.name)
        self.assertIn('id="process-42-120" data-depth="1"', report)
        self.assertIn('id="process-42-190" data-depth="1"', report)
        self.assertIn('PID 42 <span class="muted">(not observed)</span>', report)
        self.assertIn("No alerts matched the current rule.", report)

    def test_capture_strings_are_escaped(self):
        capture = FIXTURES / "connection-refusals.jsonl"
        event = json.loads(capture.read_text(encoding="utf-8").splitlines()[0])
        event["comm"] = "<img src=x onerror=alert(1)>"
        report = render_report([json.dumps(event)], "<script>sample</script>")
        self.assertNotIn("<img", report)
        self.assertNotIn("<script>", report)
        self.assertIn("&lt;img", report)
        self.assertIn("&lt;script&gt;sample", report)
