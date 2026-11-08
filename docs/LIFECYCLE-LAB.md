# Record a live process lifecycle on WSL2

In Ubuntu, run from the repository root with Python and bpftrace installed:

```bash
bash scripts/check-lifecycle.sh
```

The script launches a tagged Bash workload and captures its tagged child running `sleep`. A successful run prints `PASS fork → exec → exit` and a path under `captures/`. To replay the result, substitute the path printed by the script:

```bash
python3 -m traceguard.replay captures/lifecycle-EXAMPLE.jsonl
```

The lab validates the child's complete timeline and compares the parent identities on both fork and exec. It keeps the sensor's PID view throughout. The capture is saved only after normalization and replay validation succeed. Machine and boot IDs stay in the local, ignored capture file. Share the PASS line or the error when reporting the result.

## How the experiment works

- The initial exec matches the lab's unique Bash task name. Subsequent fork, exec, and exit events are scoped to this workload and identified by PID and start time.
- The raw fork tracepoint exposes the child task so the sensor can read its start time before it runs. The sensor uses `task_struct.start_time` and `nsecs(monotonic)` for the same clock domain. See the [Linux v6.6 fork source](https://github.com/torvalds/linux/blob/v6.6/kernel/fork.c) and the [bpftrace v0.20.2 reference](https://github.com/bpftrace/bpftrace/blob/v0.20.2/docs/reference_guide.md#36-nsecs-timestamps-and-time-deltas).
- The lab supports the supplied single-threaded workload. A thread creation in the tracked workload causes validation to fail. A general process-exit detector must account for thread groups.
- The parser rejects bpftrace diagnostics and incomplete workload captures. This run does not measure the general event-loss rate. The task name's truncation status is recorded as unknown.
- The Python path has passed synthetic regression tests. The new probe still needs its first successful run on the target WSL2 environment.
