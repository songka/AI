# Development roadmap and agent workflow

Updated: 2026-08-13

The current product is a safe WPF browser, exporter, archive library, Context Resume generator, and project backup/restore tool. Provider data remains read-only; native Agent write-back remains blocked until a public or version-verified writer contract exists.

## Installed development skills

The following skills are installed in the user's Codex skills directory and are development tools; they are not distributed with the application.

| Skill | Source | License | Intended use |
|---|---|---|---|
| dotnet-best-practices | github/awesome-copilot | MIT | .NET architecture and code quality |
| csharp-async | github/awesome-copilot | MIT | cancellation, streaming, async correctness |
| csharp-xunit | github/awesome-copilot | MIT | golden, robustness, and integration tests |
| mvvm-toolkit | github/awesome-copilot | MIT | WPF MVVM separation and commands |
| opencode-session-toolkit | wufei-png/skills | MIT | read-only OpenCode SQLite research |
| codex-session-recovery | wufei-png/skills | MIT | Codex index/archive/subagent discovery |
| security-threat-model | openai/skills curated | Apache-2.0 | repository-grounded threat modeling |
| security-best-practices | openai/skills curated | Apache-2.0 | limited use: does not currently cover C# |
| screenshot | openai/skills curated | Apache-2.0 | desktop visual regression capture |

`codex-session-exporter` was reviewed but not installed because its skill is primarily a Bash launcher that also needs the full Node CLI. It remains a behavior/reference source only.

## Mandatory gates

1. Real user sessions are read-only research inputs and must never be copied into fixtures without redaction.
2. Archive support must not be labelled native resume support.
3. No Agent write API may be added before dry-run, snapshot, atomic commit, verification, and rollback contracts exist.
4. Unknown schemas remain archive-only.
5. Every work package ends with the full test suite and an independent read-only review.

## Work packages

### WP0 — Contracts and fixtures

Owner: primary integration agent.

- Freeze USF 1.0 wire format: snake_case JSON, string enums, ISO-8601 timestamps.
- Define unknown/raw preservation and deterministic serialization.
- Define `.ai-session` manifest schema.
- Add redacted golden fixtures for text, reasoning, tools, commands, diffs, attachments, usage, Git metadata, unknown fields, and malformed lines.

Acceptance: deterministic golden serialization, unknown data preserved, no secrets or real paths in fixtures.

### WP1 — Adapter conformance

Owner: adapter agent.

- Codex: session index, archived sessions, response/event deduplication, tool calls/results, exec, patch, MCP, usage, Git and model metadata.
- Claude Code: nested content blocks, tool input/results, sidechains, model/usage/Git metadata, summaries and attachments.
- OpenCode: use the official CLI for SQLite-backed `session list/export`, with the official legacy JSON storage layout as a read-only fallback. (Complete.)

Acceptance: provider contract tests and golden tests; zero writes to provider storage. Current adapters satisfy this gate with synthetic fixtures.

### WP2 — Scan, cancellation, and performance

Owner: async/performance agent.

- Introduce a session catalog service and dependency injection.
- Add refresh and selection cancellation tokens.
- Isolate failures per Agent, directory, and file.
- Skip reparse points and tolerate access denied, active writes and disappearing files.
- Batch UI updates and remove per-file UI-context yields.
- Virtualize preview messages and page very large sessions.

Acceptance: cancellation tests, 10,000-session list test, large-session memory budget, responsive rapid selection switching.

### WP3 — Renderers and archive

Owner: export/archive agent.

- Implement provider-neutral JSON, Markdown, and single-file HTML renderers.
- HTML-encode every source field and test XSS payloads.
- Implement `.ai-session` ZIP with mandatory raw source, USF JSON, exports, attachments, SHA-256 and sizes.
- Write to a temporary output and atomically rename after verification.
- Reject rooted/traversal/duplicate ZIP entries and enforce size limits for future import.

Acceptance: renderer snapshots, offline HTML, hash verification, raw byte equality, no partial archive after failure.

### WP4 — UI integration

Owner: WPF agent after WP0/WP2 contracts stabilize.

- Export JSON, Markdown, HTML, and `.ai-session` actions.
- Raw record viewer and compatibility report.
- Progress, cancellation and clear error reporting.
- Project/date filters and meaningful title extraction.

Acceptance: keyboard and high-DPI smoke tests; exported outputs open correctly offline.

### WP5 — Security before restore

Owner: security/reviewer agent.

- Threat model, secret scanner and privacy manifest.
- Canonical path enforcement, junction/symlink defense and ZIP bomb limits.
- Schema/version preflight and provider-running/DB-lock detection.
- Design the single write pipeline: dry run, snapshot, temp/transaction, verify, commit, rollback.

Acceptance: fault-injection plan covers crash, disk full, lock conflict and validation failure. Restore implementation remains blocked until this gate passes.

### WP6 — Restore and cross-agent migration (partially complete)

Start only after WP5.

- Program-owned archive import and safe project restore are complete.
- Compatibility reports measure Archive, Context Resume, and Native Resume separately.
- Context Resume is implemented as the default fallback and marks historical commands/tools/patches inert.
- Native same-agent and cross-agent write-back remain intentionally disabled because no supported writer contract has been validated.

## Four-agent execution pattern

With four slots including the primary agent:

- Primary: USF contracts, shared interfaces, integration and final verification.
- Agent A: adapters and provider golden tests.
- Agent B: renderers and `.ai-session` archive.
- Agent C: security tests, threat review, fault injection and independent review.

For the immediate next iteration, use UI performance, scan/cancellation, adapter contract tests and OpenCode SQLite research as four isolated workstreams. Shared solution/project/interface files are owned by the primary agent to avoid merge conflicts.

## Current known risks and remaining work

- Complete `.ai-session` / `.ai-project` archives intentionally contain sensitive raw data; the UI warns before creation.
- No real OpenCode installation was available on this host, so official CLI behavior is verified from source and synthetic fixtures, not a user's live database.
- Native Agent write-back remains unavailable; adding it requires a supported schema/API plus backup, verification and rollback tests on the exact target version.
- Global FTS, multi-select session operations, a whole-machine `.aibackup`, configuration/skill migration, path rewriting, installer signing, i18n, and .NET 10 migration remain future product work.
