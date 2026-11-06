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

## Stage 0: current work

- [x] Create a private GitHub repository.
- [x] Add initial project documentation.
- [ ] Inspect the developer's Windows / WSL environment.
- [ ] Probe required eBPF features and privileges.
- [ ] Choose and document the sensor toolchain.
- [ ] Clone the project locally.

## Validation strategy

Compare capture against a controlled workload with known process count and relationships. Add stress tests only once the basic capture is correct. Record kernel version, hardware, workload, duration, and losses with every benchmark.

For detections, report false positives and false negatives on a labeled lab dataset; do not generalize those measurements to all real-world threats.

## First demonstration

Launch a known command in Ubuntu, capture its successful exec, inspect the event, and identify its parent. A process appearing in a periodically sampled process list is insufficient evidence of reliable short-lived process capture.
