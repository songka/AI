# Role workflow

| Role | Normal guidance after login |
|---|---|
| user | View and pull published versions, activate, initialize/package locally, submit candidate |
| reviewer | User actions plus review or reject candidate; cannot publish |
| publisher | User actions plus publish reviewed candidate and mirror backup to public |
| administrator | All actions plus assign/remove accounts and repository recovery |

All four roles inherit `asset.list`, `asset.install`, and `asset.activate`. The friendly
Hub commands are `view`, `pull`, and `activate`.

The role is matched against the actual SMB connection identity, case-insensitively.
Unassigned accounts receive the configured default role (`user`).

Flow:

1. Develop Skill, CLI, or Agent locally and maintain `asset-manifest.json`.
2. Package and calculate SHA-256.
3. User submits a candidate to the public repository.
4. Reviewer records reviewed or rejected decision.
5. Publisher publishes a reviewed candidate into the backup authority repository.
6. Publisher mirrors the immutable published generation from backup to public.
7. Clients resolve dependencies, download, verify, install, and activate locally.

An administrator changes account roles through the Hub command, never by manually
editing SMB JSON. Publishing and role changes must fail closed when the actual SMB
identity cannot be established.
