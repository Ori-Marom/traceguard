"""Generate a self-contained HTML investigation report from a TraceGuard capture."""

import argparse
from collections import defaultdict
from html import escape
from pathlib import Path

from traceguard.detect import LINUX_ECONNREFUSED, detect_snapshot
from traceguard.replay import replay


STYLE = """
:root { color-scheme: dark; background: #0b1220; color: #e6eef8;
        font: 16px/1.55 system-ui, sans-serif; }
* { box-sizing: border-box; }
body { max-width: 1040px; margin: auto; padding: 32px 20px 64px; }
header { padding: 24px 0; border-bottom: 1px solid #33445d; }
h1 { font-size: clamp(2rem, 6vw, 3.25rem); margin: .15em 0; line-height: 1.1; }
h2 { margin: 0 0 .65em; font-size: 1.4rem; }
p { margin: .5em 0; }
a { color: #86dcff; text-underline-offset: .2em; }
.brand { color: #86dcff; font-weight: 700; letter-spacing: .12em; }
.muted { color: #b1bfd4; overflow-wrap: anywhere; }
nav { display: flex; flex-wrap: wrap; gap: 18px; margin: 14px 0 2px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
         gap: 12px; margin-top: 24px; }
.stat, section { background: #111c2e; border: 1px solid #33445d; border-radius: 12px; }
.stat { padding: 12px 16px; }
.stat strong { display: block; font-size: 1.5rem; }
section { margin-top: 20px; padding: 20px; }
details { border-left: 3px solid #f2bd74; padding: 0 14px; margin: 14px 0; }
summary { cursor: pointer; font-weight: 700; }
.badge { color: #f6cc91; text-transform: uppercase; font-size: .8rem; margin-right: .65em; }
.tree { list-style: none; padding: 0; margin: 0; }
.tree li { margin: 0; padding: 7px 12px; border-bottom: 1px solid #33445d; }
.tree li[data-depth]:not([data-depth="0"]) {
    padding-inline-start: calc(12px + min(var(--depth), 10) * 14px);
}
.tree li[data-depth]:not([data-depth="0"])::before { content: "↳ "; color: #86dcff; }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; text-align: left; }
th, td { padding: 9px 10px; border-bottom: 1px solid #33445d; }
td { overflow-wrap: anywhere; }
th, .number { white-space: nowrap; font-variant-numeric: tabular-nums; }
:target { background: #263850; outline: 1px solid #86dcff; }
"""


def _key(process):
    return process["pid"], process["start_ns"]


def _anchor(process):
    return f"process-{process['pid']}-{process['start_ns']}"


def _process_ref(process, observed):
    label = f"PID {process['pid']}"
    if observed:
        return f'<a href="#{_anchor(process)}">{label}</a>'
    return f'{label} <span class="muted">(not observed)</span>'


def _endpoint(event):
    address = event["address"]
    if ":" in address:
        address = f"[{address}]"
    return f"{address}:{event['port']}"


def _process_tree(processes):
    if not processes:
        return '<p class="muted">No lifecycle events in this capture.</p>'

    nodes = {_key(process): process for process in processes}
    children = defaultdict(list)
    roots = []
    for key, process in nodes.items():
        parent = process["parent"]
        if parent is not None and _key(parent) in nodes:
            children[_key(parent)].append(key)
        else:
            roots.append(key)

    rows = []
    visited = set()
    # The fallback also shows disconnected cycles without traversing them forever.
    for root in [*roots, *nodes]:
        pending = [(root, 0)]
        while pending:
            key, depth = pending.pop()
            if key in visited:
                continue
            visited.add(key)
            process = nodes[key]
            parent = process["parent"]
            name = escape(process["comm"] or "Executable not observed")
            parent_label = (
                _process_ref(parent, parent["observed"]) if parent else "Unknown"
            )
            rows.append(
                f'<li id="{_anchor(process)}" data-depth="{depth}" style="--depth:{depth}">'
                f'<strong>{name}</strong> · PID {process["pid"]} '
                f'<span class="muted">· Start {process["start_ns"]} ns · Parent {parent_label}'
                '</span></li>'
            )
            pending.extend((child, depth + 1) for child in reversed(children[key]))
    return '<ul class="tree">' + "".join(rows) + "</ul>"


def _alerts(alerts):
    if not alerts:
        return '<p class="muted">No alerts matched the current rule.</p>'

    cards = []
    for index, alert in enumerate(alerts):
        process = _process_ref(alert["process"], alert["process_observed"])
        elapsed = alert["elapsed_ns"] / 1_000_000
        evidence = "".join(
            f'<li><a href="#event-{event["seq"]}">Event #{event["seq"]}</a> · '
            f'{escape(_endpoint(event))} · Connection refused</li>'
            for event in alert["evidence"]
        )
        opened = " open" if index == 0 else ""
        cards.append(
            f'<details{opened}><summary><span class="badge">{escape(alert["severity"])}</span>'
            f'{escape(alert["rule_id"])} · PID {alert["process"]["pid"]}</summary>'
            f'<p>{escape(alert["reason"])}</p>'
            f'<p>{process} · {elapsed:.3f} ms between refusals</p><ul>{evidence}</ul></details>'
        )
    return "".join(cards)


def _event_detail(event):
    kind = event["type"]
    if kind == "connect":
        result = event["result"]
        if result == 0:
            outcome = "Connected"
        elif result == LINUX_ECONNREFUSED:
            outcome = "Connection refused"
        else:
            outcome = f"Syscall result {result}"
        return f"{_endpoint(event)} · {outcome}"
    if kind == "exec":
        return event["comm"]
    if kind == "loss":
        return f'{event["count"]} events reported lost'
    return "Process created" if kind == "fork" else "Process exited"


def _timeline(events, processes):
    observed = {_key(process) for process in processes}
    origin = events[0]["ts_ns"]
    rows = []
    for event in events:
        elapsed = (event["ts_ns"] - origin) / 1_000_000
        process = event["process"] if event["type"] != "loss" else None
        reference = _process_ref(process, _key(process) in observed) if process else "—"
        rows.append(
            f'<tr id="event-{event["seq"]}"><td>#{event["seq"]}</td>'
            f'<td class="number" title="{event["ts_ns"]} ns">+{elapsed:.3f} ms</td>'
            f'<td>{escape(event["type"])}</td><td>{reference}</td>'
            f'<td>{escape(_event_detail(event))}</td></tr>'
        )
    return "".join(rows)


def render_report(lines, capture_name):
    snapshot = replay(lines, include_timeline=True)
    alerts = detect_snapshot(snapshot)["alerts"]
    processes = snapshot["processes"]
    events = snapshot["timeline"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
  <title>TraceGuard Investigation</title>
  <style>{STYLE}</style>
</head>
<body>
  <header>
    <div class="brand">TRACEGUARD</div>
    <h1>Investigation report</h1>
    <p class="muted">Capture: {escape(capture_name)}</p>
    <nav aria-label="Report sections">
      <a href="#alerts">Alerts</a>
      <a href="#processes">Process tree</a>
      <a href="#timeline">Timeline</a>
    </nav>
  </header>
  <main>
    <div class="stats">
      <div class="stat"><strong>{len(alerts)}</strong>Alerts</div>
      <div class="stat"><strong>{len(processes)}</strong>Observed processes</div>
      <div class="stat"><strong>{len(events)}</strong>Records</div>
      <div class="stat"><strong>{snapshot["lost_events"]}</strong>Reported lost events</div>
    </div>
    <section id="alerts">
      <h2>Alerts</h2>
      {_alerts(alerts)}
    </section>
    <section id="processes">
      <h2>Process tree</h2>
      {_process_tree(processes)}
    </section>
    <section id="timeline">
      <h2>Timeline</h2>
      <p class="muted">Time is relative to the first record. Event numbers identify records in the capture.</p>
      <div class="table-scroll" tabindex="0" role="region" aria-label="Timeline table">
        <table>
          <thead><tr><th scope="col">Event</th><th scope="col">Time</th><th scope="col">Type</th>
              <th scope="col">Process</th><th scope="col">Details</th></tr></thead>
          <tbody>{_timeline(events, processes)}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="TraceGuard v1 JSON Lines capture")
    parser.add_argument("--output", type=Path, required=True, help="HTML report path")
    args = parser.parse_args()
    try:
        if args.capture.resolve() == args.output.resolve() or (
            args.output.exists() and args.output.samefile(args.capture)
        ):
            raise ValueError("the output path must differ from the capture path")
        with args.capture.open(encoding="utf-8") as capture:
            report = render_report(capture, args.capture.name)
        args.output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"traceguard report: {exc}\n")
    print(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
