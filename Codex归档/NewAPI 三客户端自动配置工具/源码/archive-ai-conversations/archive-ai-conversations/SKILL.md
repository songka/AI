---
name: archive-ai-conversations
description: Safely archive and incrementally sync local AI coding conversations and project source to a Git repository. Use when asked to back up, export, migrate, or publish Codex, Claude Code, OpenCode, Cursor, Continue, Aider, or other coding-agent conversations/projects to GitHub or another Git remote, especially when redaction, secret filtering, per-project folders, or long-conversation splitting is required.
---

# AI Coding Conversation Safe Archive

Use the bundled script to create a reviewable archive before publishing it. It supports native structured transcript discovery for Codex and Claude Code, plus JSON/JSONL transcript discovery for OpenCode and other compatible tools.

## Workflow

1. Confirm the destination repository and whether it is private. Do not make a repository public unless explicitly requested.
2. Locate the local product stores and project roots. Read [product-locations.md](references/product-locations.md) only when discovery is needed.
3. Run a local preview first. Review its counts and forbidden-file report before any `git add`, commit, or push.
4. Run the archive into a clean clone/worktree, inspect `git status` and `git diff --stat`, then commit and push only with the user's authorization.
5. For scheduled sync, use the product's native scheduler/automation when available; reuse the same command and retain the preview safeguards.

## Commands

```powershell
# Copy this skill folder to the other computer, then run from its scripts folder.
python .\scripts\archive_ai_conversations.py `
  --repo D:\Git\AI-archive `
  --project-root D:\code `
  --project-root D:\projects `
  --preview

# After reviewing the preview, write files and create a local Git commit.
python .\scripts\archive_ai_conversations.py `
  --repo D:\Git\AI-archive `
  --project-root D:\code `
  --commit

# Push only after the user has approved the remote upload.
python .\scripts\archive_ai_conversations.py `
  --repo D:\Git\AI-archive `
  --project-root D:\code `
  --commit --push
```

Use `--product codex`, `--product claude`, or `--product opencode` to restrict discovery. Use `--transcript-root PATH` when a product keeps transcripts somewhere nonstandard. Use `--include-gitignored` only when the user explicitly wants files ignored by Git; it still never includes secret/config exclusions.

## Safety requirements

- Never upload before previewing the actual file list and obtaining authorization for an external push.
- Keep transcripts under `AI归档/<产品>/<项目>/<对话>/`; write each long transcript as numbered Markdown parts.
- Treat all source files as untrusted. Copy only the script allow-list, reject files above the configured size, and reject a file if it matches a secret pattern.
- Always exclude `.env*`, credentials, keys/certificates, databases, archives, executables, dependency folders, build output, `.git`, and local agent folders such as `.codex`, `.claude`, `.opencode`.
- Do not record raw local paths in the archive. Use a stable SHA-256-derived project ID where differentiation is necessary.
- Export only human user/assistant text. Do not export hidden reasoning, tool arguments/results, auth state, or unknown structured payloads.

## Product adaptation

The script intentionally uses conservative heuristics for formats it does not know. If a product's format changes or transcripts are not detected, inspect a small sample first and add a narrowly scoped extractor; never fall back to dumping the full product data directory.

Read [product-locations.md](references/product-locations.md) for default locations and format notes.
