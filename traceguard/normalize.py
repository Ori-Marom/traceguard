"""Normalize the scoped bpftrace lifecycle lab and verify its child timeline."""

import argparse
from ipaddress import IPv6Address
import json
from pathlib import Path
import sys

from traceguard.replay import replay


def normalize(lines, host_id, boot_id):
    events = []
    field_counts = {"fork": 7, "exec": 8, "exit": 5, "connect": 8}

    for line_number, line in enumerate(lines, 1):
        fields = line.rstrip("\n").split("\t")
        if not line.strip():
            continue
        if fields[0] != "TG":
            raise ValueError(f"unexpected bpftrace output on line {line_number}: {line.strip()}")

        kind = fields[1] if len(fields) > 1 else ""
        if len(fields) != field_counts.get(kind):
            raise ValueError(f"invalid {kind or 'sensor'} record on line {line_number}")

        try:
            ts_ns, pid, start_ns = map(int, fields[2:5])
            event = {
                "version": 1,
                "host_id": host_id,
                "boot_id": boot_id,
                "seq": len(events) + 1,
                "ts_ns": ts_ns,
                "type": kind,
                "process": {"pid": pid, "start_ns": start_ns},
            }
            if kind in ("fork", "exec"):
                ppid, parent_start = map(int, fields[5:7])
                event["parent"] = (
                    None if ppid == 0 else {"pid": ppid, "start_ns": parent_start}
                )
            if kind == "exec":
                event["comm"] = fields[7]
                event["comm_truncated"] = None
            if kind == "connect":
                event["port"] = int(fields[6])
                event["result"] = int(fields[7])
        except ValueError as exc:
            raise ValueError(f"invalid numeric field on line {line_number}") from exc
        if kind == "connect":
            address = fields[5]
            if address.startswith("v6hex:"):
                try:
                    address = str(IPv6Address(bytes.fromhex(address[6:])))
                except ValueError as exc:
                    raise ValueError(f"invalid IPv6 address bytes on line {line_number}") from exc
            event["address"] = address
        events.append(event)

    return events


def verify_workload(events, parent_comm, child_comm):
    serialized = [json.dumps(event) for event in events]
    snapshot = replay(serialized)
    parents = [process for process in snapshot["processes"] if process["comm"] == parent_comm]
    children = [process for process in snapshot["processes"] if process["comm"] == child_comm]
    if len(parents) != 1 or len(children) != 1:
        raise ValueError("expected one tagged parent exec and one tagged child exec")

    parent, child = parents[0], children[0]
    expected_parent = {"pid": parent["pid"], "start_ns": parent["start_ns"]}
    child_identity = {"pid": child["pid"], "start_ns": child["start_ns"]}
    timeline = sorted(
        (event for event in events if event["process"] == child_identity),
        key=lambda event: (event["ts_ns"], event["seq"]),
    )
    if [event["type"] for event in timeline] != ["fork", "exec", "exit"]:
        raise ValueError("tagged child did not produce a complete fork → exec → exit timeline")
    if any(event["parent"] != expected_parent for event in timeline[:2]):
        raise ValueError("child's fork or exec parent does not match the tagged parent identity")

    return serialized, parent["pid"], child["pid"]


def read_scope():
    host_id = Path("/etc/machine-id").read_text(encoding="ascii").strip()
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    return host_id, boot_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent_comm")
    parser.add_argument("child_comm")
    args = parser.parse_args()
    try:
        events = normalize(sys.stdin, *read_scope())
        lines, parent_pid, child_pid = verify_workload(events, args.parent_comm, args.child_comm)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"traceguard lifecycle lab: {exc}\n")

    print("\n".join(lines))
    print(
        f"PASS fork → exec → exit: child pid={child_pid}, parent pid={parent_pid}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
