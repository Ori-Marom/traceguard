"""Replay a TraceGuard v1 JSON Lines capture into a process snapshot."""

import argparse
import json
from pathlib import Path


def _integer(value, field, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _identity(value, field, timestamp):
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    pid = _integer(value.get("pid"), f"{field}.pid", 1)
    start = _integer(value.get("start_ns"), f"{field}.start_ns")
    if start > timestamp:
        raise ValueError(f"{field}.start_ns exceeds the event timestamp")
    return pid, start


def _load_events(lines):
    scope = None
    sequences = set()
    events = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("expected an event object")
            if _integer(event.get("version"), "version", 1) != 1:
                raise ValueError("unsupported schema version")
            current_scope = (event.get("host_id"), event.get("boot_id"))
            if not all(isinstance(value, str) and value for value in current_scope):
                raise ValueError("host_id and boot_id must be non-empty strings")
            if scope is not None and scope != current_scope:
                raise ValueError("expected events from a single host and boot")
            scope = current_scope
            sequence = _integer(event.get("seq"), "seq", 1)
            if sequence in sequences:
                raise ValueError(f"duplicate seq {sequence}")
            sequences.add(sequence)
            _integer(event.get("ts_ns"), "ts_ns")
            if event.get("type") not in ("fork", "exec", "exit", "loss"):
                raise ValueError("unknown event type")
            events.append((line_number, event))
        except ValueError as exc:
            raise ValueError(f"line {line_number}: {exc}") from exc
    if scope is None:
        raise ValueError("capture contains no events")
    return scope, sorted(events, key=lambda row: (row[1]["ts_ns"], row[1]["seq"]))


def replay(lines):
    """Build an observed process snapshot from one host and boot."""
    (host_id, boot_id), events = _load_events(lines)
    processes = {}
    lost_events = 0

    for line_number, event in events:
        kind = event["type"]
        timestamp = event["ts_ns"]
        try:
            if kind == "loss":
                lost_events += _integer(event.get("count"), "count", 1)
                continue

            identity = _identity(event.get("process"), "process", timestamp)
            if identity not in processes:
                processes[identity] = {
                    "pid": identity[0],
                    "start_ns": identity[1],
                    "parent": None,
                    "first_seen_ns": timestamp,
                    "fork_seen": False,
                    "exit_ns": None,
                    "comm": None,
                    "comm_truncated": None,
                }
            process = processes[identity]
            if process["exit_ns"] is not None:
                raise ValueError("process event follows exit for the same identity")

            if kind in ("fork", "exec"):
                if "parent" not in event:
                    raise ValueError("parent must be present, using null if unknown")
                if event["parent"] is not None:
                    parent = _identity(event["parent"], "parent", timestamp)
                    if parent == identity:
                        raise ValueError("a process cannot be its own parent")
                    process["parent"] = {"pid": parent[0], "start_ns": parent[1]}

            if kind == "fork":
                process["fork_seen"] = True
            elif kind == "exec":
                comm = event.get("comm")
                truncated = event.get("comm_truncated")
                if not isinstance(comm, str) or not comm:
                    raise ValueError("comm must be a non-empty string")
                if "comm_truncated" not in event or (
                    truncated is not None and type(truncated) is not bool
                ):
                    raise ValueError("comm_truncated must be true, false, or null")
                process["comm"] = comm
                process["comm_truncated"] = truncated
            else:
                process["exit_ns"] = timestamp
        except ValueError as exc:
            raise ValueError(f"line {line_number}: {exc}") from exc

    for process in processes.values():
        parent = process["parent"]
        if parent is not None:
            parent["observed"] = (parent["pid"], parent["start_ns"]) in processes

    return {
        "version": 1,
        "host_id": host_id,
        "boot_id": boot_id,
        "lost_events": lost_events,
        "processes": [processes[key] for key in sorted(processes)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="v1 JSON Lines capture")
    args = parser.parse_args()
    try:
        with args.capture.open(encoding="utf-8") as capture:
            snapshot = replay(capture)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"traceguard replay: {exc}\n")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
