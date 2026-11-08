# Record outbound IPv4 and IPv6 connections on WSL2

From the repository root in Ubuntu:

```bash
bash scripts/check-network.sh
```

The lab starts one tagged Python executable. It connects to a listening port and attempts a connection to a reserved port with no listener, first on `127.0.0.1`, then on `::1`. Linux allocates the ports for each run.

The script prints `PASS TCP connect` and a local JSON Lines capture path after all four destinations and return codes match the workload. It also verifies that every attempt matches the tagged exec by PID and process start time. Replay the capture using the path printed by the script:

```bash
python3 -m traceguard.replay captures/network-EXAMPLE.jsonl
```

Look under `connections` for the address, port, return code, and process identity. The capture is ignored by Git. The script rejects probe diagnostics or an incomplete trace.

## Capture scope

- The enter probe reads the requested IPv4 or IPv6 socket address. The exit probe emits the return code from the same thread's `connect()` call.
- The recorded timestamp is the syscall return time. A return of zero is success. A negative return is a Linux errno. In particular, a nonblocking call returning `-EINPROGRESS` is pending and would require later evidence of completion.
- The lab workload uses TCP. The syscall alone does not establish the socket transport, and this event does not claim a protocol.
- The probe filters by the tagged task name and handles IPv4 and IPv6 destinations with nonzero ports. The capture stores the IPv6 address without an interface scope ID. UDP attribution and nonblocking completion are outside this lab.
- The combined lab passed on WSL2 with bpftrace v0.20.2. The capture contained one successful connection and one refused connection for each family. All four records matched the same tagged process.
