# Codex local session format research

Observed on this Windows workstation on 2026-08-12 (read-only inspection):

```text
%USERPROFILE%\.codex\sessions\YYYY\MM\DD\rollout-*.jsonl
%USERPROFILE%\.codex\session_index.jsonl
```

The inspected session begins with a JSONL envelope containing `timestamp`, `type`, and `payload`.

- `session_meta`: payload includes `session_id`, `id`, `timestamp`, `cwd`, `originator`, `cli_version`, `source`, `model_provider`, and runtime/context metadata.
- `event_msg`: lifecycle/runtime events.
- `response_item`: items whose payload contains a discriminating `type`; message-like records expose `id`, `role`, and `content`.

The prototype only maps message-like `response_item` entries and session metadata. Event records and unrecognized payloads remain available in the original JSONL when archived. The current implementation does not write to Codex paths, and it makes no native-resume claim.

The `.codex` root also contains SQLite state files. They are explicitly out of scope for Phase 1; readers must not assume they are stable session sources or modify them.
