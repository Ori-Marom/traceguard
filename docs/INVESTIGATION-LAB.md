# Open an investigation report

Generate a report from the checked-in sample from the repository root:

```bash
mkdir -p captures
python3 -m traceguard.report tests/fixtures/connection-refusals.jsonl --output captures/investigation.html
```

To investigate a real lab run, replace the sample path with the local JSON Lines path printed by the capture script. Open the HTML file in a browser. From Ubuntu under WSL, `(cd captures && explorer.exe .)` opens the containing directory in Windows Explorer.

## What to inspect

- **Alerts** shows the matched rule, elapsed time, and links to the exact evidence records. Select an event number to highlight its row in the timeline.
- **Process tree** groups observed processes by their captured parent identity. Missing parents are labeled. Process links include the start time so reused PIDs remain distinct.
- **Timeline** lists all records ordered by timestamp and source sequence. The time column is relative to the first record. The source nanoseconds are available in each time cell's tooltip.

The report is self-contained and has no server dependency. It contains process and network details from the capture, so store it with the ignored local captures.
