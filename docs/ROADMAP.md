# Roadmap

Progress is based on demonstrated behavior, not elapsed time.

| Stage | Deliverable | Completion criteria |
| --- | --- | --- |
| 0 | Environment and repository | WSL2 or Linux VM verified; feature probe recorded; repository cloned |
| 1 | Process sensor | Successful execution captured for a short-lived lab command; fields validated; limitations documented |
| 2 | Lifecycle and storage | Fork/exec/exit distinguished; PID reuse handled; events stored and replayed |
| 3 | Network telemetry | Outbound connection linked to process identity; IPv4/IPv6 and failed-connect semantics documented |
| 4 | Detection engine | One bounded-time correlation rule with positive, negative, and incomplete-data fixtures |
| 5 | Investigation UI | Alert evidence, process tree, and timeline shown from stored events |
| 6 | Evaluation and demo | Reproducible lab, measured CPU/memory/event loss, setup guide and demo recording |

## Stage 0: environment

- [x] Create a private GitHub repository.
- [x] Add initial project documentation.
- [x] Inspect the developer's Windows / WSL environment.
- [x] Verify the initial exec tracepoint attaches and emits an event under sudo.
- [x] Choose bpftrace for the initial sensor experiment.
- [x] Clone the project inside Ubuntu.

## Stage 1: process sensor

- [x] Capture a successful exec with an inline probe.
- [x] Add the repository prototype and a repeatable lab.
- [x] Run the tagged lab on WSL2 and verify the child PPID matches the parent's PID in the sensor output.

## Stage 2: lifecycle and storage

- [x] Define the v1 event format and process identity.
- [x] Replay synthetic events and verify PID reuse, missing parents, and out-of-order input.
- [x] Capture live fork and process exit events for the scoped workload on WSL2.
- [x] Normalize a live capture, validate it with replay, and save it locally.

## Stage 3: network telemetry

- [x] Add an IPv4 connect event and join it to the full process identity in replay.
- [x] Add a local TCP workload with successful and refused connections.
- [ ] Verify both live outcomes on WSL2.
- [ ] Extend the probe to IPv6 and validate it on WSL2.

## Validation strategy

Compare capture against a controlled workload with known process count and relationships. Add stress tests only once the basic capture is correct. Record kernel version, hardware, workload, duration, and losses with every benchmark.

For detections, report false positives and false negatives on a labeled lab dataset; do not generalize those measurements to all real-world threats.

## First demonstration

Launch a known command in Ubuntu, capture its successful exec, inspect the event, and identify its parent. A process appearing in a periodically sampled process list is insufficient evidence of reliable short-lived process capture.
