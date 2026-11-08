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
