# Universal Session Format (USF) 1.0

USF is the provider-neutral archive model. It is the only boundary used by renderers, archive packaging, search, and future migration services:

```text
provider raw data -> adapter parser -> UniversalSession -> renderer / archive / future writer
```

The top-level document contains `format: "ai-coding-session"`, `version: "1.0"`, `session`, `messages`, `metadata`, `attachments`, and `environment`. A session retains its source identity (`source`, `source_session_id`) and must retain fields it cannot normalize in `metadata` or `unsupported_records`.

Every message has an id, optional parent id, role, timestamp, content parts, and metadata. Supported content part types are `text`, `reasoning`, `tool_call`, `tool_result`, `file`, `image`, `command`, `command_result`, `patch`, `diff`, `system`, and `metadata`.

## Loss policy

Adapters must not discard unknown records. A syntactically invalid JSONL line is represented as an `UnsupportedRecord` with its source line, reason, and raw text. Semantically unknown but valid records belong in raw archive payloads and provider metadata. This permits improved parsers to reprocess an archive later.

## Archive boundary

The Phase 1 backup container is implemented as a ZIP with the `.ai-session` extension:

```text
manifest.json
universal/session.json
raw/<provider-source-files>
exports/
```

`raw/` is mandatory. Every payload is declared with its byte size and SHA-256 digest in `manifest.json`; creation uses a same-directory temporary file, verifies the completed ZIP, and then atomically commits it. A successful USF conversion means **archive-compatible**, not native-resume-compatible.
