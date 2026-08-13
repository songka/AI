---
name: manage-feishu-signing
description: Safely inspect, maintain, test, deploy, or extend this repository's Feishu signing system, including message routing, AI intent handling, signing and rejection rules, group-notification policy, callback services, unified CLI commands, per-user statistics, OAuth dashboard, and deployment packages. Use when changing or diagnosing the 飞书自动签核 project or its server deployment.
---

# Manage Feishu Signing

Work from the repository root. Treat signing and rejection as high-impact mutations.

## Safety workflow

1. Read `references/safety-policy.md` before changing routing, AI prompts, confirmation, signing, or rejection.
2. Read `references/rule-schema.md` before changing rules or notification behavior.
3. Read `references/commands.md` before changing CLI or user-facing commands.
4. Preserve existing user data under `users/`; never put credentials in example files, logs, archives, or test output.
5. Make ambiguous AI signing intent advisory only. Never let AI output call a signing mutation directly.
6. Require confirmation for all-sign, all-reject, and manual actions opposite to a matched action rule.
7. Record only platform-verified actions in the per-user statistics database.
8. Enforce dashboard ownership server-side from Feishu OAuth `open_id`; never trust an `open_id` query parameter.
9. Keep credentials and system secrets encrypted at rest with a master key outside
   the repository. Back up with authenticated encryption, verify restores in an
   empty staging directory, and require exact `open_id` confirmation plus an
   encrypted archive before offboarding deletion.
10. Keep global production KPI access restricted to configured administrator
    OAuth `open_id` values. Base capacity changes on stored real-load evidence,
    and require an independently approved change record with canary and rollback
    criteria before building a production release.
11. Keep service and scheduler bootstrap scripts on the same repository-external
    runtime environment source; never package that environment file.

## Change workflow

1. Read the repository `AGENTS.md` and classify the change with its code-to-Skill sync matrix.
2. Inspect the relevant module and current deployment documentation.
3. Add or update regression cases for the reported phrase or behavior.
4. Update the mapped safety, rule-schema, command, architecture, deployment, or release guidance when behavior changes.
5. Keep the unified `qh.py` entry point stable while placing logic in focused modules.
6. Run `powershell -File scripts/validate-project.ps1`; do not claim completion, package, or deploy when it fails.
7. Rebuild `qh-deploy-fixed.zip` only through `build-release.ps1` with an
   independently approved Change Record. Use `-IncludeSkill` only when a
   server-side AI agent needs the maintenance Skill.

## Sync gate

- Treat `AGENTS.md` as the mandatory change classifier and completion contract.
- Keep `references/safety-policy.md` synchronized with routing, AI, confirmation, signing, and rejection behavior.
- Keep `references/rule-schema.md` synchronized with rules, groups, compatibility, and notification precedence.
- Keep `references/commands.md` synchronized with CLI commands, Feishu phrases, cards, menus, and settings.
- Add a regression test for every user-visible behavior change or reported bug.
- Keep the application version identical in code, release notes, the user guide, and deployment guide.
- Run the project-owned no-dependency Skill validator; also run skill-creator `quick_validate.py` when PyYAML is available.
- Require the release script to run all validation before archive creation and verify archive contents afterward.
- Keep `run-server.sh` and `run-scheduler.sh` aligned on the same external runtime
  environment source so service startup and scheduled execution do not silently diverge.

## Architecture boundaries

- Keep Feishu transport and callback concerns in `feishu.py`, `cli_feishu.py`, and `callback_server.py`.
- Keep platform submission logic in `auto_sign.py` and signing CLI commands in `cli.py`.
- Keep action matching in `rules.py`; keep group notification decisions in `notification_policy.py`.
- Keep safe text classification in `intent_router.py`.
- Keep user-isolated audit data in `stats_store.py` and web authentication/presentation in `web_dashboard.py`.
- Use `qh.py` as the single user-facing CLI entry point; do not merge all modules into one file.

Do not auto-import the legacy global `sign_records.xlsx` into personal statistics because it has no reliable Feishu `open_id` ownership.
