# Process events v1

TraceGuard stores one JSON object per line. Each capture belongs to one host and Linux boot. Run the offline demo from the repository root with Python 3.10 or later:

```bash
python3 -m traceguard.replay tests/fixtures/lifecycle.jsonl
```

The checked-in capture is synthetic. The [live lifecycle lab](LIFECYCLE-LAB.md) includes a scoped bpftrace experiment and a normalizer for this format.

## Common fields

| Field | Meaning |
| --- | --- |
| `version` | Integer schema version, currently 1 |
| `host_id` | Stable identifier assigned to the Linux host by the collector |
| `boot_id` | Identifier for the current Linux boot |
| `seq` | Positive capture sequence, unique within this input. It breaks timestamp ties |
| `ts_ns` | Event time in boot-relative monotonic nanoseconds. It is not a wall-clock timestamp |
| `type` | `fork`, `exec`, `exit`, `loss`, or `connect` |

All event and process start timestamps in a capture use the same clock domain. The contract uses Linux monotonic time and assumes a collector can obtain compatible process start and event timestamps. Mapping the live kernel fields to this contract must be verified before capture integration. A capture has one sequence stream. Multi-sensor merging and wall-clock conversion are deferred.

## Process identity and payloads

Process identity is `(host_id, boot_id, pid, start_ns)`. Keep the original process start timestamp at nanosecond resolution. The PID is the process ID in the sensor's kernel view, consistent with the parent PID. The same PID can identify different processes within one boot when their start times differ. A successful exec can change the executable without changing this identity.

Each lifecycle or connect event has a `process` object containing `pid` and `start_ns`.

| Type | Additional fields and semantics |
| --- | --- |
| `fork` | `process` is the newly created process. `parent` is its parent identity or null if unavailable |
| `exec` | Successful executable replacement. `parent` is the observed parent identity or null. `comm` is the short task name. `comm_truncated` is true, false, or null when unknown |
| `exit` | Exit of the process identity. Future live instrumentation must distinguish process exit from individual thread exit |
| `connect` | IPv4 destination `address`, destination `port` (1–65535), and signed syscall `result`. The timestamp is taken at syscall return |
| `loss` | Positive integer `count` of newly reported dropped events. `ts_ns` is the time the loss was reported |

```json
{"version":1,"host_id":"lab","boot_id":"boot-a","seq":3,"ts_ns":120,"type":"fork","process":{"pid":42,"start_ns":120},"parent":{"pid":10,"start_ns":80}}
```

A `connect` event records a call result. Zero means success. A negative value is a Linux errno. A pending nonblocking call is not a completed connection. The event does not identify the socket transport.

## Replay rules

- Sort by `ts_ns`, then `seq`, and emit processes sorted by PID and start time. Shuffling input lines does not change a valid capture's result.
- Retain the most recent known parent reference. `parent: null` in the snapshot means no parent identity was observed. A reference with `observed: false` means that exact parent identity has no record in the capture. A matching PID with another start time does not resolve it.
- `fork_seen: false` and `exit_ns: null` indicate missing evidence for those events. An absent exit does not prove a process was still alive.
- List connect records in timestamp and sequence order. `process_observed` is true only when the same PID and start time occur in a lifecycle record in this capture. A connect event alone does not create a process node.
- Sum explicit loss reports. Sequence gaps alone do not establish loss, and a zero reported count is not a completeness guarantee.
- Invalid records fail with a line number and a nonzero exit status. Mixed hosts or boots and duplicate sequences are rejected. Replay holds one capture in memory and is intended for local experiments.

Run the regression tests with `python3 -m unittest discover -s tests -v`.
