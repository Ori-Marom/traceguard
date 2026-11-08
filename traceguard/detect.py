"""Evaluate the first TraceGuard detection rule against a saved capture."""

import argparse
import json
from pathlib import Path

from traceguard.replay import replay


LINUX_ECONNREFUSED = -111
WINDOW_NS = 1_000_000_000
RULE_ID = "distinct_connection_refusals"
EVIDENCE_FIELDS = ("seq", "ts_ns", "address", "port", "result")


def detect(lines):
    """Find the earliest qualifying pair per process in a single capture."""
    return detect_snapshot(replay(lines))


def detect_snapshot(snapshot):
    """Evaluate the rule against a validated replay snapshot."""
    recent_refusal = {}
    alerts = {}

    # Replay validates the capture and orders connections by timestamp and sequence.
    for event in snapshot["connections"]:
        if event["result"] != LINUX_ECONNREFUSED:
            continue
        process = event["process"]
        identity = (process["pid"], process["start_ns"])
        if identity in alerts:
            continue

        previous = recent_refusal.get(identity)
        recent_refusal[identity] = event
        if previous is None:
            continue

        elapsed = event["ts_ns"] - previous["ts_ns"]
        previous_endpoint = (previous["address"], previous["port"])
        endpoint = (event["address"], event["port"])
        if elapsed > WINDOW_NS or previous_endpoint == endpoint:
            continue

        alerts[identity] = {
            "rule_id": RULE_ID,
            "rule_version": 1,
            "severity": "low",
            "process": process,
            "process_observed": event["process_observed"],
            "window_ns": WINDOW_NS,
            "elapsed_ns": elapsed,
            "reason": "One process received connection refusals from two distinct endpoints within one second.",
            "evidence": [
                {key: item[key] for key in EVIDENCE_FIELDS} for item in (previous, event)
            ],
        }

    return {
        "version": 1,
        "host_id": snapshot["host_id"],
        "boot_id": snapshot["boot_id"],
        "lost_events": snapshot["lost_events"],
        "alerts": list(alerts.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="TraceGuard v1 JSON Lines capture")
    args = parser.parse_args()
    try:
        with args.capture.open(encoding="utf-8") as capture:
            result = detect(capture)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"traceguard detect: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
