# Development journal

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
