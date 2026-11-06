# Development workflow

1. Pick an Issue with concrete acceptance criteria.
2. Create a focused branch such as `feat/process-events` or `docs/setup`.
3. Implement one reviewable change.
4. Run checks that demonstrate the intended behavior.
5. Update the relevant documentation and development journal.
6. Commit, push, and open a pull request describing behavior, validation, and limitations.

Example commit subjects:

- `docs: define architecture and milestones`
- `feat: capture successful process execution`
- `fix: distinguish reused process identifiers`
- `test: cover missing parent events`

Never claim that a check passed unless it actually ran. Use synthetic fixtures for committed telemetry. Keep credentials, local event captures, private logs, and build artifacts out of Git.

A feature is complete when its acceptance criteria are demonstrated, its known limitations are documented, and another developer can reproduce the result.
