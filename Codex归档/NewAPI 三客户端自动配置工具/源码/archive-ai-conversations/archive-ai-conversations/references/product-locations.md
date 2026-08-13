# Product locations and transcript formats

Use these as discovery candidates, not proof that every installed version uses the same layout. Prefer a product-provided export when it exists.

| Product | Typical Windows data location | Supported discovery |
| --- | --- | --- |
| Codex | `%USERPROFILE%\.codex\sessions\**\*.jsonl` | Reads `response_item.payload.role` and textual `payload.content`; associates `session_meta.payload.cwd`. |
| Claude Code | `%USERPROFILE%\.claude\projects\**\*.jsonl` | Reads JSONL `type` records with `message.role` / `message.content`, retaining only `user` and `assistant`. |
| OpenCode | `%LOCALAPPDATA%\opencode`, `%APPDATA%\opencode`, `%USERPROFILE%\.local\share\opencode` | Searches only JSON/JSONL files below user-supplied or known transcript folders and extracts explicit user/assistant message objects. Its storage format can differ by release. |
| Other tools | User-supplied `--transcript-root` | Searches JSON/JSONL and exports only objects that explicitly provide `role: user|assistant` plus text content. |

Do not recursively archive the complete product directory. It may contain authentication, settings, caches, databases, or tool payloads.
