# Verify the exec sensor on WSL2

Run from the repository root in Ubuntu with bpftrace installed and kernel BTF available:

```bash
bash scripts/check-exec.sh
```

The lab starts a Bash process and a child that runs `sleep`. It gives both temporary executable names with a shared random suffix so their exec events can be found in the same output. The workload runs under sudo as part of this lab, so its events may have `uid=0`.

1. Find `EXPECTED`. It lists the process names as `parent_comm` and `child_comm`.
2. Find the two `EXEC` lines with those names.
3. Confirm that the child's `ppid` equals the parent's `pid` in the sensor output.

The values printed by Bash are local to its PID namespace. The sensor reads IDs from the kernel and may see different numbers for the same processes. Compare IDs within a single view and use the generated names to correlate across views. If either name is absent from the trace, the run is inconclusive.

## What the fields mean

| Field | Meaning |
| --- | --- |
| `ts_ns` | Kernel timestamp in nanoseconds |
| `pid` | Process ID in the sensor's kernel view |
| `ppid` | Real parent's process ID in the same view at exec time |
| `uid` | User ID reported by bpftrace |
| `comm` | Short kernel task name, which can be truncated |

The probe observes successful execs, including when an existing process replaces its executable. Fork and exit events, stable process identity, persistent storage, executable paths, and loss accounting are later work.
