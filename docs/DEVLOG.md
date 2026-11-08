# Development journal

## 2026-11-08 — Add the live lifecycle lab

- Confirmed bpftrace v0.20.2 and the fork, exec, and exit tracepoints on the development WSL2 machine.
- Added a scoped lifecycle probe, a Python normalizer, and a lab that checks the child's three-event timeline and exact parent identity before saving a capture.
- Ran seven Python regression tests and checked the shell script syntax. The new probe has not yet been run on WSL2.
- Next: run the lifecycle lab on the target kernel and verify it saves a replayable JSON Lines capture.

## 2026-11-08 — Define process events and offline replay

- Defined v1 JSON Lines events and a process key scoped to a host and boot. The key includes process start time to distinguish reused PIDs.
- Added a Python replay command and a synthetic fixture for fork, exec, exit, and loss. Replay preserves unknown parent and truncation information.
- Ran four regression tests and the CLI demo locally. The fixture produced two separate records for PID 42 and left the unmatched parent identity unresolved.
- Next: collect the lifecycle events from the Linux sensor and validate the timestamp and identity mapping on WSL2.

## 2026-11-08 — Verify the tagged parent-child lab

- Confirmed the repository was cloned and the lab ran inside Ubuntu on WSL2.
- Observed parent `tgp-x52aoH` with sensor PID `1898` and child `tgc-x52aoH` with sensor PID `1899` and PPID `1898`. Both names matched the workload's independently printed markers.
- Bash reported its own PID as `1565` and the child's as `1566`. Parent linkage agreed within each PID view.
- Both expected exec events were present. This run verifies the controlled parent-child case. It does not quantify event loss under load.
- Next: define the event schema, identity across PID reuse, and replay fixtures in [#3](https://github.com/Ori-Marom/traceguard/issues/3).

## 2026-11-08 — Compare the shell and sensor views of PIDs

- Ran the repository sensor with a Bash workload using bpftrace `-c`.
- The sensor reported `bash pid=1830` and `sleep pid=1831 ppid=1830`. These events agree on the parent in the sensor's view.
- The same workload printed `pid=1498 ppid=1497` from Bash. Comparing these numbers directly with the sensor IDs made the earlier procedure inconclusive. The discrepancy is consistent with different Linux PID namespace views.
- Updated the lab to give both executables unique names per run and compare the parent link within the sensor output. The revised lab still needs to run on the developer's WSL2 instance.

## 2026-11-08 — Capture the first exec event

- Confirmed that a temporary bpftrace program attached to `sched:sched_process_exec` on Ubuntu under WSL2 and captured `/usr/bin/true`.
- Observed `EXEC pid=1280 uid=1000 comm=true`.
- Added a bpftrace prototype that records the parent PID and a lab procedure with an independently known child and parent PID.
- Next, run the repository script on WSL2 and compare its captured IDs against the shell output. Parent PID validation is pending.

## 2026-11-08 — Inspect the WSL2 environment

- PowerShell reported WSL `2.6.1.0`, with Ubuntu and WSL2 as defaults.
- Ubuntu reported Linux `6.6.87.2-microsoft-standard-WSL2` on `x86_64`.
- `/sys/kernel/btf/vmlinux` was listed with read permissions, and Git reported version `2.43.0`.
- The BTF file listing verifies availability of the file. Attaching an eBPF program and observing an event are still pending.
- Next check for [#1](https://github.com/Ori-Marom/traceguard/issues/1): attach a temporary bpftrace program to `sched:sched_process_exec` and verify it emits an event for `/usr/bin/true`. This is a feature check ahead of the TraceGuard sensor.

## 2026-11-06 — Project foundation

### Completed

- Selected an educational Linux endpoint detection and investigation project.
- Created the private repository `Ori-Marom/traceguard`.
- Added a scope, architecture proposal, roadmap, setup guide, and contribution workflow.

### Decisions

- Develop from Windows using a Linux environment.
- Validate eBPF support before committing to a sensor toolchain.
- Build process telemetry before network correlation or UI.
- Keep measured capabilities separate from planned capabilities.

### Verification

Repository creation and private visibility were verified. Local WSL and eBPF checks are pending. No application or sensor tests have run because no implementation exists yet.

### Next session

Inspect WSL output, probe Linux tracing support, and implement the smallest successful-exec capture experiment.

## Entry template

### Goal
What behavior are we trying to add?

### Changes
What changed and why?

### Verification
Exact commands, observed results, environment, and unresolved failures.

### Lessons / decisions
What did we learn or choose?

### Next step
The smallest useful continuation.
