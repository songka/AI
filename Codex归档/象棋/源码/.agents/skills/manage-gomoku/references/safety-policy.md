# Safety policy

## Risk model

Deletion is the declared high-risk operation. The runtime therefore has no delete,
clear, reset, persistence, or overwrite capability. The initial project also
avoids network access, credentials, telemetry, and shell execution. Any future
change in these areas requires explicit user authorization, architecture and
contract updates, and a mapped safety test.

## Operational rules

- Never delete or overwrite project data, user data, saved games, or releases.
- Treat invalid/destructive text as inert input; never translate it into an OS action.
- Keep gameplay in memory and local to the Python process.
- Do not auto-publish, upload, push, tag, or install.
- Do not weaken a validation check to permit packaging.
- Exclude passwords, tokens, keys, user data, logs, caches, packages, and VCS data
  from releases.
- Do not include the Skill unless `-IncludeSkill` is explicitly supplied.
- If packaging fails after a partial archive is created, report the partial file;
  do not delete it automatically.

The following block is contractual and must exactly match the `safety_rules` array
in `gomoku/project-contract.json`. Every `test` target must exist.

<!-- CONTRACT:SAFETY_RULES -->
```json
[
  {
    "id": "SAFE-NO-DELETE",
    "requirement": "The application exposes no command that deletes or overwrites user data.",
    "test": "tests/test_unit_safety.py::test_parser_rejects_destructive_commands"
  },
  {
    "id": "SAFE-LOCAL-ONLY",
    "requirement": "Runtime gameplay performs no network access and persists no user data.",
    "test": "tests/test_unit_safety.py::test_game_has_no_persistence_or_network_api"
  },
  {
    "id": "SAFE-RELEASE-CONTENTS",
    "requirement": "Release validation rejects sensitive filenames and credential-like content.",
    "test": "tests/test_unit_safety.py::test_sensitive_scanner_detects_forbidden_fixture"
  },
  {
    "id": "SAFE-NO-OVERWRITE",
    "requirement": "Release creation refuses to overwrite an existing package.",
    "test": "tests/test_unit_safety.py::test_release_script_has_no_overwrite_path"
  },
  {
    "id": "SAFE-EXPLICIT-SKILL",
    "requirement": "The project Skill is included in a release only through an explicit parameter.",
    "test": "tests/test_unit_safety.py::test_release_skill_inclusion_is_explicit"
  }
]
```

