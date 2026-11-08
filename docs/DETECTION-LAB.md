# Evaluate the first detection rule

Run from the repository root:

```bash
python3 -m traceguard.detect tests/fixtures/connection-refusals.jsonl
```

The same command accepts a local JSON Lines capture from `scripts/check-network.sh`.

## Rule: distinct_connection_refusals

- An alert requires two Linux `ECONNREFUSED` results (`-111`) from the same process to different address and port pairs. The calls must return within one second of each other, inclusive.
- The rule uses the first qualifying pair per process in each capture. Successful calls, pending calls, and repeated refusals to only one endpoint do not contribute a second distinct destination.
- A capture is scoped to one host and boot. The detector groups by PID and process start time, so PID reuse cannot merge two processes.
- The output marks the alert as low severity and lists the two source `seq` values, timestamps, destinations, and results. Each `seq` points to a record in the input capture.
- `process_observed` reports whether replay found a lifecycle record for the process. The alert can still be emitted from two valid connection records. `lost_events` reports known loss for the capture. An incomplete capture may miss matches, and the detector does not count events it did not observe.

The threshold is chosen for the controlled lab. Normal software can generate the same pattern. This rule identifies a behavior for review and makes no claim that an intrusion took place. Detection runs on saved captures.

The rule was also verified on a saved WSL2 dual-stack loopback capture. It produced one alert with the two refused destinations and their input sequence numbers.
