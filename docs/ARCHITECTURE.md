# Architecture proposal

Status: design proposal; implementation choices remain subject to the environment probe.

## Data flow

A Linux kernel sensor emits bounded records to a userspace collector. The collector validates records, assigns stable event IDs, stores them locally, and passes normalized events to a detection engine. An investigation API exposes events, alerts, and process relationships to a UI.

Start with a single host and local storage. Remote agents and distributed deployment can follow a working local pipeline.

## Process identity

A PID is reused and must not be treated as a permanent identity. Plan a key containing host ID, boot ID, PID, and process start time. Record parent identity when available, distinguish thread IDs from process IDs, and represent missing ancestry explicitly.

PID values must carry their scope. The prototype reports process and parent IDs from the same kernel view. If the collector later adds namespace-local IDs, label their namespace explicitly and avoid joining them directly with kernel-view IDs.

Execution replaces a process image; it does not necessarily create a new process. Capture fork/clone, successful exec, and exit as distinct event types when building the complete lifecycle model.

## Event envelope

The [v1 event contract](EVENTS.md) defines the current offline replay input. The fields below describe the broader target envelope for live collection.

Proposed common fields:

- schema_version, event_id, event_type
- host_id, boot_id, sensor_sequence
- monotonic_timestamp_ns and a documented wall-clock mapping
- process identity, parent identity when known, UID
- event-specific data and explicit truncation flags

Document namespaces and clock semantics before treating events from containers or separate boots as comparable.

## Reliability

Use bounded kernel-to-userspace buffering and expose loss counters. Measure loss under load and report gaps; do not silently present incomplete capture as complete.

Keep initial telemetry small. Avoid command arguments and environment variables by default. If later enabled, apply explicit limits and document the privacy implications.

## Detection model

Rules produce an identifier, version, severity, explanation, time window, and supporting event IDs. An alert indicates a matched behavior, not proof of compromise.

Replay synthetic fixtures through the same normalization and rule interfaces. Test timeouts, out-of-order input, missing events, PID reuse, and benign lookalikes.

## Security boundaries

Keep privileged collection as small as practical. The API and UI should not run with sensor privileges. Bind future development services to loopback by default. Document the required privileges after testing the chosen hooks.

Initial response is visibility and investigation. Automated killing or blocking is deferred.

## Storage and stack

Begin with local append-only event capture; evaluate SQLite for indexed investigation. C/libbpf plus a Python collector is a candidate, not yet an adopted stack. Record decisions with rationale and evidence when the prototype is validated.
