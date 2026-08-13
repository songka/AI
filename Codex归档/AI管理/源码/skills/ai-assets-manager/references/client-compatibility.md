# Client compatibility

The folder uses the common Agent Skills layout: a top-level `SKILL.md` plus optional
`scripts/`, `references/`, and `agents/`.

| Client | User-level destination | Project-level destination |
|---|---|---|
| Codex | `%USERPROFILE%\.codex\skills\ai-assets-manager` | Project-configured skills location |
| Claude Code | `%USERPROFILE%\.claude\skills\ai-assets-manager` | `.claude\skills\ai-assets-manager` |
| Gemini CLI | `%USERPROFILE%\.gemini\skills\ai-assets-manager` or `%USERPROFILE%\.agents\skills\ai-assets-manager` | `.gemini\skills\ai-assets-manager` or `.agents\skills\ai-assets-manager` |
| Cursor | `%USERPROFILE%\.cursor\skills\ai-assets-manager` | `.cursor\skills\ai-assets-manager` or `.agents\skills\ai-assets-manager` |

Copy the entire folder, not only `SKILL.md`. Do not maintain separate content variants
for each client. `scripts/ai_assets_skill.py` is the shared behavior contract and emits
machine-readable JSON so different agents receive the same decisions.

If a client does not support Agent Skills natively, its project instruction file may
point to this folder's `SKILL.md`; all state-changing work must still go through the
bundled scripts.
