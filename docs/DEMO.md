# Reproduce the TraceGuard demo

From the repository root on Ubuntu under WSL2:

```bash
sudo -v
python3 -m traceguard.demo
```

A successful run saves a verified capture, `alerts.json`, and `investigation.html` under a new `captures/demo-*` directory. Open the report in a browser. Expand the alert and select one of its evidence records to jump to the refused connection. The workload makes one successful and one refused blocking TCP connection per loopback family.

## Measure the capture pipeline

```bash
sudo -v
python3 -m traceguard.demo --benchmark --iterations 3 --repetitions 100
```

This generates the demo report first. It then runs three samples per mode, alternating the order. Each sample runs 100 batches of the same socket workload. Each batch attempts four connections. The ports are allocated anew. The baseline runs the Python workload directly. The traced mode runs the full network lab, including bpftrace startup, attachment, workload execution, normalization, validation, and capture writing. Run `sudo -v` outside the measurements so a password prompt does not inflate the traced timings.

`metrics.json` records:

| Field | Meaning |
| --- | --- |
| `wall_ms` | Elapsed time for the measured command |
| `cpu_ms` | User and system CPU time for the command and its waited-for descendants |
| `peak_rss_kib` | Linux peak resident set size reported for the command and its descendants. This is a maximum, not a sum of concurrent memory |
| `expected_connects` | Four connections per workload repetition |
| `observed_connects` | Verified connection count, or a partial count if available in the failure diagnostics |
| `reported_lost_events` | Explicit loss reported by the capture or bpftrace. Null means the count was unavailable |
| `returncode` | Zero for a completed sample, nonzero for a rejected run |

The benchmark records the kernel, architecture, logical CPU count, and bpftrace version. Medians use successful runs only and include the sample count. Failed runs retain their logs and are excluded from medians. A zero loss count and matching workload counts verify these samples. They do not establish a general drop rate or guarantee capture under heavier load. The timing differences compare full commands and do not isolate per-event kernel overhead.

The generated data stays under the ignored `captures/` directory. Review logs before sharing them.

## Measured WSL2 run

Ubuntu on WSL2 used kernel `6.6.87.2-microsoft-standard-WSL2`, x86_64, 12 logical CPUs, and bpftrace v0.20.2. The demo saved an investigation report for four captured connections and one alert. The benchmark used three samples per mode and 100 workload batches per sample.

| Sample | Mode | Wall time (ms) | CPU time (ms) | Peak RSS (KiB) | Observed / expected connects | Reported loss |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Baseline | 31.634 | 27.069 | 15,104 | — | — |
| 2 | Baseline | 30.659 | 30.142 | 15,872 | — | — |
| 3 | Baseline | 29.733 | 29.215 | 15,872 | — | — |
| 1 | Traced | 553.712 | 43.899 | 15,104 | 400 / 400 | 0 |
| 2 | Traced | 552.222 | 39.349 | 15,872 | 400 / 400 | 0 |
| 3 | Traced | 566.686 | 42.643 | 15,872 | 400 / 400 | 0 |

The baseline medians were 30.659 ms wall time, 29.215 ms CPU, and 15,872 KiB peak RSS. The traced medians were 553.712 ms wall time, 42.643 ms CPU, and 15,872 KiB peak RSS. The traced command includes bpftrace startup and attachment, validation, and capture writing. Identical peak RSS readings describe the reported maximum and cannot establish aggregate concurrent memory use. These samples covered 1,200 expected connection records on a controlled loopback workload.
