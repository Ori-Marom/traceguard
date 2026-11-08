"""Verify that the scoped network capture matches the local TCP workload."""

import argparse
import errno
import json
from pathlib import Path
import sys

from traceguard.normalize import normalize, read_scope
from traceguard.replay import replay


def verify_connections(events, client_comm, expected):
    lines = [json.dumps(event) for event in events]
    snapshot = replay(lines)
    clients = [process for process in snapshot["processes"] if process["comm"] == client_comm]
    if len(clients) != 1:
        raise ValueError("expected one exec event for the tagged client")

    client = clients[0]
    identity = {"pid": client["pid"], "start_ns": client["start_ns"]}
    connections = snapshot["connections"]
    if len(connections) != len(expected) or any(
        item["process"] != identity or not item["process_observed"] for item in connections
    ):
        raise ValueError("connection events do not match the tagged client identity")

    actual = [
        {key: item[key] for key in ("address", "port", "result")} for item in connections
    ]
    if actual != expected:
        raise ValueError(f"expected loopback results {expected}, got {actual}")

    return lines, client["pid"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("client_comm")
    parser.add_argument("expected", type=Path)
    args = parser.parse_args()
    try:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        events = normalize(sys.stdin, *read_scope())
        lines, pid = verify_connections(events, args.client_comm, expected)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"traceguard network lab: {exc}\n")

    print("\n".join(lines))
    outcomes = []
    for item in expected:
        address, port, result = item["address"], item["port"], item["result"]
        endpoint = f"[{address}]:{port}" if ":" in address else f"{address}:{port}"
        outcome = "connected" if result == 0 else errno.errorcode.get(-result, str(result))
        outcomes.append(f"{endpoint} {outcome}")
    print(f"PASS TCP connect: pid={pid}, {', '.join(outcomes)}", file=sys.stderr)


if __name__ == "__main__":
    main()
