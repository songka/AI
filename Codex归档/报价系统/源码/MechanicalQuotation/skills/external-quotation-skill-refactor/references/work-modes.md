# Work modes and migration decisions

## User-facing modes

| Mode | Writes | Required result |
|---|---:|---|
| Analyze only | No | Evidence inventory, capability matrix, risks and recommendation |
| Refactor/migrate existing | Yes | Compatibility-preserving resources, V2 routes, migration and regression tests |
| Create/train new | Yes | New resources built from requirements, examples, counterexamples and acceptance tests |

## Migration actions

Assign every existing capability exactly one primary action:

- `KEEP`: valid boundary and contract; no change beyond verification.
- `SHARE`: one global/category Agent or Skill serves several routes without duplicated prompts.
- `STANDARDIZE`: preserve behavior; fix manifests, IDs, schemas, evidence, timeouts and fallbacks.
- `SPLIT`: separate different permissions, runtimes, owners, side effects, failure boundaries or release cycles.
- `MERGE`: combine truly duplicate resources with identical contract and governance.
- `DEPRECATE`: retain compatibility metadata but remove it from new routes; state replacement and sunset criteria.
- `REPLACE`: independently implement a safer or proven resource and migrate routes.

Do not delete a used resource merely because it looks redundant. Prove route usage, publish a replacement, migrate, test, then deprecate.

## One Skill, several Skills, or Agent reuse

Keep one Skill when inputs, outputs, owner, permission, runtime, timeout, side effects, release cadence and fallback are substantially the same. Split when any of these differ materially.

Share an Agent across Skills when the reasoning role and input/output schema are identical. Use different Agents when domain evidence and acceptance thresholds differ, for example grinding time versus welding time. Keep Excel modification/export commands separate from reasoning because they mutate files and have a separate runtime failure boundary.
