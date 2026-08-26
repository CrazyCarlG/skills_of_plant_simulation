# log/

This directory holds human-readable session logs. The convention is one
file per session, named `session-YYYYMMDD[-N].md`, where N is a
sequence number for multiple sessions in the same day.

Each entry should record:

1. **What was tried** — subcommand + args.
2. **Server reply** — JSON envelope or first/last few lines.
3. **Interpretation** — did the op succeed? What does the resulting
   `before`/`after` state mean for the model?
4. **Quirks observed** — any new quirk not yet captured in
   `references/protocol-notes.md`.

Initial v1 entry: see `session-20260826-v1.md`.