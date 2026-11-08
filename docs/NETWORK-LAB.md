# Record outbound IPv4 connections on WSL2

From the repository root in Ubuntu:

```bash
bash scripts/check-network.sh
```

The lab starts a tagged Python executable that opens two blocking TCP connections to `127.0.0.1`. It connects to a listening port, then attempts a connection to a reserved port with no listener. Both ports are allocated by Linux for the run.

The script prints `PASS TCP connect` and a local JSON Lines capture path after the two destinations and return codes match the workload. It also verifies that both attempts match the tagged exec by PID and process start time. Replay the capture using the path printed by the script:

```bash
python3 -m traceguard.replay captures/network-EXAMPLE.jsonl
```

Look under `connections` for the address, port, return code, and process identity. The capture is ignored by Git. The script rejects probe diagnostics or an incomplete trace.

## Capture scope

- The enter probe reads the requested IPv4 socket address. The exit probe emits the return code from the same thread's `connect()` call.
- The recorded timestamp is the syscall return time. A return of zero is success. A negative return is a Linux errno. In particular, a nonblocking call returning `-EINPROGRESS` is pending and would require later evidence of completion.
- The lab workload uses TCP. The syscall alone does not establish the socket transport, and this event does not claim a protocol.
- The probe filters by the tagged task name and handles IPv4 destinations with nonzero ports. IPv6, UDP attribution, and nonblocking completion are outside this lab.
- The TCP workload and Python replay were verified locally. The live lab passed on WSL2 with bpftrace v0.20.2. Both attempts matched the tagged process identity, and the validated JSON Lines capture was saved locally.
