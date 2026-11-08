# Verify the exec sensor on WSL2

This lab checks that TraceGuard captures a successful exec and reports the correct process and parent IDs. It requires `bpftrace` and readable kernel BTF. Run from the root of the repository in Ubuntu.

## Start capture

In the first Ubuntu terminal:

```bash
sudo bpftrace sensor/exec.bt
```

Wait for `Attaching 1 probe...`. The sensor prints successful exec events from the Linux environment. Stop it with Ctrl+C after the experiment.

## Generate an event with known IDs

In a second Ubuntu terminal, run these commands in Bash:

```bash
/usr/bin/sleep 1 &
child_pid=$!
printf 'EXPECTED pid=%s ppid=%s\n' "$child_pid" "$BASHPID"
wait "$child_pid"
```

The background command gives Bash a child PID in `$!`. `$BASHPID` is the PID of the Bash process running the commands. Find the `EXEC` line with the matching `pid` and `comm=sleep`. Confirm its `ppid` equals the shell PID printed above. Multiple execs can have the same `comm`, so match the PID as well.

## What the fields mean

| Field | Meaning |
| --- | --- |
| `ts_ns` | Kernel timestamp in nanoseconds |
| `pid` | Linux process ID |
| `ppid` | Process ID of the task's real parent at exec time |
| `uid` | User ID reported by bpftrace |
| `comm` | Short kernel task name, which can be truncated |

This probe observes successful program execution, including when an existing process replaces its executable. Fork and exit events, stable process identity, persistent storage, executable paths, and loss accounting are later work. Test on a quiet lab instance and share only the synthetic `EXPECTED` line and matching `EXEC` line.
