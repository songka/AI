# Claude Code local session format research

Observed on this Windows workstation on 2026-08-12 (read-only inspection):

```text
%USERPROFILE%\.claude\projects\<encoded-project-path>\<session-uuid>.jsonl
```

The project directory name encodes the original working path. Session JSONL records observed include `user`, `assistant`, `system`, `mode`, and `permission-mode`. Message records can contain `uuid`, `parentUuid`, `timestamp`, `cwd`, `sessionId`, `gitBranch`, and nested `message` data. Claude content blocks can be text, thinking, tool use, and tool result.

Actual local data included malformed JSON lines (for example an invalidly encoded `cwd`). The adapter therefore parses line-by-line, retains invalid lines as `UnsupportedRecord`, and continues. It never derives a write schema from such observations.

No Claude data is modified. Native resume is unimplemented and should remain disabled until a release-specific writer, transaction tests, and end-to-end validation exist.
