---
name: ai-assets-manager
description: Manage shared, versioned AI Skill, CLI, and Agent assets across Codex, Claude Code, Gemini CLI, and Cursor. Use when a user wants to log in to the AI Assets SMB Hub, inspect their role, create or version a local asset, resolve dependencies, submit/review/publish an update, install a specific release, or update this management skill itself.
---

# AI Assets Manager

Use the bundled scripts as the deterministic control plane. Never request, read, repeat,
store, log, or pass an SMB password through the AI conversation.

## Mandatory login gate

Run this before every Hub operation:

```powershell
python "<skill-folder>\scripts\ai_assets_skill.py" gate
```

Parse its JSON result.

- If `state` is `login_required`, output only the value of `login_instruction` and stop.
  Do not list assets, disclose roles, suggest publishing, or attempt another Hub command.
- If `state` is `setup_required`, SMB authentication succeeded but the Hub registry has
  not been deployed. Output only `setup_instruction` and stop. Do not misreport this as
  a login failure.
- If `state` is `ready`, use only the guidance under `role_prompt` and the allowed
  operations returned by the command.
- Never ask the user to paste an account or password into chat.
- The login script creates a non-persistent Windows user-session SMB connection with
  `net use`; do not replace it with a process-scoped `New-PSDrive`.
- If a different or temporary SMB account is needed, tell the user to run
  `scripts\secure-login.ps1` outside the AI conversation. Account names without a
  domain are normalized to `GETACAD\username` by that script.

## Local asset workflow

Treat Skill, CLI, and Agent as equal asset types with IDs `skill/name`, `cli/name`, and
`agent/name`. Because every unpublished change is automatically backed up, local
initialize, status, bump, and package commands also apply the login gate before changing
state. If SMB is unavailable, show only the login instruction and stop.

Initialize metadata in an existing project:

```powershell
python "<skill-folder>\scripts\ai_assets_skill.py" init --path "<project>" --type skill --name example --version 0.1.0
```

Use `--dependency skill/name@^1.2.0` repeatedly when needed. Run `status --path
"<project>"` after edits. It computes a reproducible content digest and reports whether
the working copy differs from its last packaged/submitted state.

Every `init`, `status`, `bump`, and `package` command automatically backs up the current
unpublished content to both SMB repositories. This is unconditional for every role and
does not require a separate user request or a Hub permission. The explicit command below
is only for recovery or diagnostics:

```powershell
python "<skill-folder>\scripts\ai_assets_skill.py" draft-backup --path "<project>"
```

The command maintains a managed local shadow Git repository and pushes the same commit
to `drafts/<SMB-principal>/<asset-id>.git` in public and backup repositories. It never
force-pushes: divergence is treated as possible direct SMB modification and must stop
with an error. Draft history is not published and is not added to `registry.json`.
Obvious secret files such as `.env`, private keys, and credential files block backup.
Never weaken that check; ask the user to remove the secret from the asset.

Create a candidate package:

```powershell
python "<skill-folder>\scripts\ai_assets_skill.py" package --path "<project>" --output "<folder>"
```

Every published candidate must contain non-empty Chinese release notes. `package`
automatically generates a Chinese factual draft from the added, modified, and removed
files since the previous package. Show the generated notes to the user. If the diff is
insufficient or the user wants business context, ask for Chinese wording and rerun with
`--release-notes "<text>"`.
Never invent test results, compatibility claims, or business impact. Hub submission and
publication must reject a candidate whose release notes are empty.

Do not publish automatically. After packaging, prompt according to the logged-in role:

- `user`: may submit the candidate.
- `reviewer`: may submit or review; review does not publish.
- `publisher`: may publish only an already reviewed candidate.
- `administrator`: may assign roles, recover/mirror repositories, and perform all above.

Read [role workflow](references/roles-and-workflow.md) only when a ready session needs
role-specific commands. Read [client placement](references/client-compatibility.md) when
installing this folder for another coding agent.

## Hub install and dependencies

Every ready role—user, reviewer, publisher, and administrator—may view and pull
published assets. Use `view [asset-id]` to list the catalog and versions. Use `pull
asset-id@version --activate` to download the selected version and its required
dependencies. A user's unpublished draft is private to that SMB principal and is not
shown as a published release.

Prefer the bundled wrapper so users never need to define a `$hub` PowerShell variable:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill-folder>\scripts\hub.ps1" view
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill-folder>\scripts\hub.ps1" pull "skill/name@1.2.0" --activate
```

The wrapper must execute its bundled `scripts\asset_hub.py`, not a possibly stale client
copied on SMB. The bundled client still reads both repositories and enforces their role
policy.

For administration, use the same wrapper, for example `hub.ps1 accounts list`. Do not
show commands containing an undefined placeholder such as `python $hub ...`.
The wrapper must verify the actual SMB identity in its own PowerShell process. Use
`Get-SmbConnection` first and the Windows network provider `WNetGetUser` as the trusted
fallback for non-domain PCs. If both are missing, invoke `secure-login.ps1` locally and
continue only after the actual SMB username is visible.
If Windows reports multiple usernames connected to the same server, ask locally before
disconnecting only connections whose remote server is `10.97.0.210`, then retry. Never
disconnect mappings to other servers and never perform the cleanup without local
confirmation.

The Hub resolves required dependencies before installing. Never install a dependency by
guessing its version. Never edit artifacts or registry files directly on SMB.

## Updating this Skill

This folder is itself the asset `skill/ai-assets-manager`. After a successful gate, run:

```powershell
python "<skill-folder>\scripts\ai_assets_skill.py" self-check
```

If an update exists, explain the version change and ask before changing the installed
copy. On explicit approval, run `self-update`. The updater verifies the registered
SHA-256, validates the extracted Skill, swaps directories, and retains at most three
timestamped sibling backups of the user's previous copies. Do not self-update a source
development checkout containing `.git`.

After a successful update, always tell the user:

1. The old and new versions and the backup directory.
2. Close and reopen the current Code/Agent session so it reloads `SKILL.md`.
3. Run `self-backups` to list retained copies.
4. If the new version misbehaves, run `self-rollback`; then restart the session again.

Never delete more than the updater's fourth-and-older managed backups. Do not touch
unrelated user folders or backups that do not match `.ai-assets-manager.backup.*`.

## Safety boundaries

- SMB credentials stay inside the separate Windows credential prompt.
- The public SMB tree is a distribution surface, not a trusted write boundary.
- Privileged actions must use the actual identity returned by `Get-SmbConnection` or
  Windows `WNetGetUser`; never use an environment variable or chat-provided account.
- Published artifacts must originate from the reviewed backup/authority repository.
- Keep the current installed version if download, digest, extraction, or validation fails.
- Never use `/savecred`, `cmdkey /pass`, plaintext password environment variables, or
  serialized `PSCredential` objects.
