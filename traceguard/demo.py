"""Run the TraceGuard network demo and optionally measure the capture pipeline."""

import argparse
import json
import os
from pathlib import Path
import platform
import re
from statistics import median
import subprocess
import tempfile
from time import perf_counter

from traceguard.detect import detect
from traceguard.replay import replay
from traceguard.report import render_report


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _measure(command, directory):
    """Measure one Linux command, including its waited-for children."""
    directory.mkdir()
    stdout = directory / "stdout.log"
    stderr = directory / "stderr.log"
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        started = perf_counter()
        with subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err) as child:
            _, status, usage = os.wait4(child.pid, 0)
            child.returncode = os.waitstatus_to_exitcode(status)
        wall_ms = (perf_counter() - started) * 1000
    return {
        "returncode": child.returncode,
        "wall_ms": round(wall_ms, 3),
        "cpu_ms": round((usage.ru_utime + usage.ru_stime) * 1000, 3),
        "peak_rss_kib": usage.ru_maxrss,
    }


def _trace(directory, repetitions):
    result = _measure(
        ["bash", "scripts/check-network.sh", str(directory), str(repetitions)], directory
    )
    expected = 4 * repetitions
    result.update(expected_connects=expected, observed_connects=None, reported_lost_events=None)
    if result["returncode"] != 0:
        diagnostics = (directory / "stderr.log").read_text(encoding="utf-8")
        counts = re.findall(r"^Lost (\d+) events?\b", diagnostics, re.MULTILINE)
        if counts:
            result["reported_lost_events"] = sum(map(int, counts))
        incomplete = re.search(r"expected \d+ connect events, observed (\d+)", diagnostics)
        if incomplete:
            result["observed_connects"] = int(incomplete[1])
        return result, None

    capture, = directory.glob("network-*.jsonl")
    with capture.open(encoding="utf-8") as stream:
        snapshot = replay(stream)
    result["observed_connects"] = len(snapshot["connections"])
    result["reported_lost_events"] = snapshot["lost_events"]
    return result, capture


def _demo(directory):
    trace_dir = directory / "trace"
    _, capture = _trace(trace_dir, 1)
    if capture is None:
        raise ValueError(f"network capture failed; see {trace_dir / 'stderr.log'}")

    lines = capture.read_text(encoding="utf-8").splitlines()
    result = detect(lines)
    if len(result["alerts"]) != 1:
        raise ValueError(f"expected one demo alert, got {len(result['alerts'])}")
    _write_json(directory / "alerts.json", result)
    report = directory / "investigation.html"
    report.write_text(render_report(lines, capture.name), encoding="utf-8")
    print(f"Demo passed: 4 connections, 1 alert. Report: {report.relative_to(ROOT)}", flush=True)


def _benchmark(directory, iterations, repetitions):
    runs = {"baseline": [], "traced": []}
    for index in range(1, iterations + 1):
        # Alternate order so the same mode does not always run first.
        order = ("baseline", "traced") if index % 2 else ("traced", "baseline")
        for mode in order:
            print(f"Benchmark {index}/{iterations}: {mode}", flush=True)
            run_dir = directory / f"{index:02d}-{mode}"
            if mode == "baseline":
                result = _measure(
                    ["/usr/bin/python3", "scripts/tcp-workload.py",
                     str(run_dir / "outcomes.json"), str(repetitions)],
                    run_dir,
                )
            else:
                result, _ = _trace(run_dir, repetitions)
            runs[mode].append({"directory": run_dir.name, **result})

    medians = {}
    for mode, samples in runs.items():
        passed = [sample for sample in samples if sample["returncode"] == 0]
        medians[mode] = {
            "successful_runs": len(passed),
            **{field: median(sample[field] for sample in passed) if passed else None
               for field in ("wall_ms", "cpu_ms", "peak_rss_kib")},
        }

    version = subprocess.run(["bpftrace", "--version"], capture_output=True, text=True)
    metrics = directory / "metrics.json"
    _write_json(metrics, {
        "environment": {
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "logical_cpus": os.cpu_count(),
            "bpftrace": version.stdout.strip() or version.stderr.strip(),
        },
        "repetitions_per_run": repetitions,
        "expected_connects_per_traced_run": 4 * repetitions,
        "runs": runs,
        "median_successful_runs": medians,
    })
    print(f"Benchmark results: {metrics.relative_to(ROOT)}", flush=True)
    if any(summary["successful_runs"] != iterations for summary in medians.values()):
        raise ValueError("some benchmark runs failed; see metrics.json and the per-run logs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", action="store_true", help="also run the timed comparison")
    parser.add_argument("--iterations", type=int, default=3, help="runs per benchmark mode")
    parser.add_argument("--repetitions", type=int, default=100, help="four-connect batches per run")
    args = parser.parse_args()
    if not 1 <= args.iterations <= 20 or not 1 <= args.repetitions <= 10000:
        parser.error("iterations must be 1–20 and repetitions must be 1–10000")
    if not hasattr(os, "wait4") or platform.system() != "Linux":
        parser.error("the live demo requires Linux or WSL2")

    captures = ROOT / "captures"
    try:
        captures.mkdir(exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix="demo-", dir=captures))
        print(f"Run directory: {directory.relative_to(ROOT)}", flush=True)
        _demo(directory)
        if args.benchmark:
            _benchmark(directory, args.iterations, args.repetitions)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"traceguard demo: {exc}\n")


if __name__ == "__main__":
    main()
