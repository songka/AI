# Rule schema

Action rules live in `auto_reject` and `auto_approve`:

```json
{
  "name": "简体拒签",
  "conditions": [{"field": "描述", "op": "has_cn", "value": ""}],
  "logic": "AND",
  "reason": "描述含简体字",
  "group_notify": false
}
```

For `has_cn`, the fixed material-description label `型号:` (also with optional
spaces or a full-width colon) is excluded from Simplified/Traditional detection.
Only that label is excluded: Simplified Chinese after the colon or elsewhere in
the description still matches the operator.

Named groups are stored per user in `groups.json`:

```json
{
  "version": 2,
  "user_groups": {"常用申请人": ["张三", "李四"]},
  "content_groups": {"常规料号": ["半成品;軟體"]},
  "legacy_migrations": {"whitelist": true}
}
```

Group conditions use:

```json
{"field": "申请人", "op": "in_user_group", "value": "常用申请人"}
{"field": "申请人", "op": "not_in_user_group", "value": "限制人员"}
{"field": "描述", "op": "starts_with_content_group", "value": "常规料号"}
{"field": "描述", "op": "not_starts_with_content_group", "value": "禁用开头"}
{"field": "描述", "op": "ends_with_content_group", "value": "允许结尾"}
{"field": "描述", "op": "not_ends_with_content_group", "value": "禁用结尾"}
{"field": "描述", "op": "contains_content_group", "value": "紧急项目"}
{"field": "描述", "op": "not_contains_content_group", "value": "排除内容"}
```

User-group membership is exact after trimming and case folding. Missing or empty
groups must fail closed for every group operator, including `not_in_user_group`.
Block deletion of referenced groups and update references on rename.

Compatibility mapping is non-destructive:

- `whitelist` → `默认用户组`
- `blacklist` → `限制用户组`
- `content_whitelist` → `默认内容组`

`legacy_migrations` records a legacy list after its generated default group is
renamed or deleted. Once recorded, the old list must not recreate that default
group. Version 1 group files remain readable and normalize to version 2.

Keep the legacy operators readable at runtime until an edit or rename converts
that specific reference. Do not expose `in_whitelist`, `in_blacklist`, or
`starts_with_content_wl` in new web rule dropdowns, and never mass-rewrite
existing users during startup.

The rule editor must make group operators field-dependent:

- `申请人` may use `in_user_group` and `not_in_user_group`; its value must be an
  existing user group selected from a list.
- `描述` may use the six content-group starts/ends/contains positive or negative
  operators; its value must be an existing content group selected from a list.
- Missing or empty groups fail closed, including every negative operator.

`reason` is optional for legacy rules. Compatibility reads also accept
`reject_reason`, `rejectReason`, `拒签理由`, and `拒签原因`. Any card or command edit
writes the canonical `reason` field and removes only those recognized aliases.

Independent group-notification rules live in `notification_rules`:

```json
{
  "name": "紧急项目发群",
  "conditions": [{"field": "描述", "op": "contains", "value": "紧急"}],
  "logic": "AND",
  "notify": true
}
```

Apply notification precedence in this order:

1. Explicit manual `发群` or `不发群`.
2. First matched `notification_rules` entry.
3. Matched action rule's `group_notify`.
4. User `default_group_notify`, default `false`.

Treat legacy `notify` entries as send-notification rules during compatibility reads.

GSC field compatibility:

- Material applications normally expose raw item-type codes such as `P`, `PH`, or
  `FG`; rules should compare `类别` with the raw value shown by query/preview.
- Non-material applications may use an alphanumeric `No:` and
  `Applicant:姓名 [工号]`. Parse these records with category `非料号` instead of
  displaying an unknown applicant or empty application number.
- Preview notification labels describe what would happen only after a real,
  platform-verified action. Preview itself never sends the group notification.
