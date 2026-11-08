# TraceGuard

An educational Linux endpoint detection and investigation platform, planned around eBPF telemetry.

**Status: initial process sensor prototype. Scoped WSL2 labs verified live process lifecycle events, parent linkage, and outbound IPv4 and IPv6 connection outcomes. Both labs save JSON Lines captures.**

## Goal

Explain suspicious activity through evidence: which process ran, who started it, which network connection it made, and which detection rule matched.

The target demonstration is a controlled process chain in a local lab, reconstructed as a process tree and investigation timeline.

## Initial scope

- Linux process execution and parent-child relationships.
- Network connections linked to process identities.
- Versioned events, local storage, and deterministic replay.
- Explainable rules that correlate events over time.
- Investigation interface and reproducible performance measurements.

Development starts on Windows using Ubuntu under WSL2. The Linux sensor observes the Linux environment; it does not monitor native Windows processes. eBPF support must be checked on the actual kernel before choosing the sensor implementation. A Linux VM is the fallback if required features are unavailable.

## First milestone

The first lab captured a short-lived command and verified its parent PID using a tagged Bash workload. The [offline replay demo](docs/EVENTS.md) reconstructs a process snapshot from structured lifecycle events. The live lifecycle lab records and validates the same format for a controlled workload.

Run the [exec sensor lab](docs/EXEC-LAB.md) to compare a captured event with known process and parent IDs.

## Documentation

- [Development setup](docs/SETUP.md)
- [Architecture proposal](docs/ARCHITECTURE.md)
- [Event format and replay demo](docs/EVENTS.md)
- [Live lifecycle lab](docs/LIFECYCLE-LAB.md)
- [Outbound IPv4 and IPv6 connection lab](docs/NETWORK-LAB.md)
- [Detection rule and offline demo](docs/DETECTION-LAB.md)
- [Investigation report](docs/INVESTIGATION-LAB.md)
- [Roadmap and acceptance criteria](docs/ROADMAP.md)
- [Development journal](docs/DEVLOG.md)
- [Contribution workflow](CONTRIBUTING.md)

## Planned components

| Component | Responsibility | Status |
| --- | --- | --- |
| Linux sensor | Kernel telemetry and loss counters | Scoped lifecycle capture verified |
| Collector | Validation, normalization, local storage | Local JSON Lines and replay |
| Detection engine | Stateful rules and evidence references | First offline rule available |
| Investigation UI | Alert evidence, process tree, and event timeline | Offline HTML report |
| Lab and benchmarks | Reproducible correctness and overhead checks | Planned |

The first exec experiment uses bpftrace. C/libbpf is a candidate for the next sensor iteration, and Python is a candidate for collection and detection.

## Development

Track work in Issues. Each change should include a focused commit, appropriate verification, and updated documentation. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Limitations

This is a learning and engineering project, not a production endpoint protection product. Automatic process termination, stealth, tamper resistance, and Windows-native collection are outside the initial scope.

Real telemetry may contain usernames, paths, command arguments, and destination addresses. Keep it local; commit only synthetic or reviewed, sanitized fixtures.
