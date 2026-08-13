# Commands

Unified CLI:

```text
python auto-sign/qh.py sign <list|approve|reject|fetch|run> ...
python auto-sign/qh.py feishu <serve|send|test|setup|lookup|ai-setup> ...
python auto-sign/qh.py web serve --host 127.0.0.1 --port 7000
python auto-sign/qh.py security <init-key|migrate|backup|restore-drill|restore|offboard> ...
python auto-sign/qh.py ops capacity --db data/stats.db --days 7 --cpu N --memory-mb N
```

Security administration is local CLI-only and must never be exposed as a Feishu
message or AI action. `restore` accepts only an empty staging directory and an
exact absolute-path confirmation. `offboard` requires an exact `open_id` repeat
and creates an encrypted archive before deleting owned data.
Operations capacity analysis is also local CLI-only. It must return "no real
load" instead of inventing Worker, scheduler, or database settings when the
metrics database has no request/run samples.

High-value Feishu messages:

```text
查询
模拟自动签核
执行一次自动签核          # explicit one-shot rule execution; not all-sign
@人员 执行一次自动签核    # group: exact command, targeted user, 5-minute debounce
签核 1 3 [发群|不发群]
拒签 2 [原因:资料不完整] [发群|不发群]
全签 / 全拒               # always requires 确认
确认 / 取消
群通知默认 开|关
统计
管理中心
规则
组管理
用户组
内容组
设置
待手动提醒 开
待手动提醒 关
等待设置                    # card: select one or more logged-in users
```

Fixed commands and intent routing accept Simplified Chinese, Traditional Chinese,
and mixed-script variants by comparing a normalized copy. Never normalize stored
person names, group names, rule names, or condition values. AI receives the
original input; clear all-Traditional input gets Traditional natural replies and
fallback command guidance, while internal `DO:`, `SUGGEST:`, `RULE:`, and `REPLY:`
protocol prefixes remain unchanged.

Management cards use Feishu Card JSON 2.0. The `规则` card exposes
`default_group_notify` at the top. Each `auto_approve` and `auto_reject` rule has
a three-state notification button: inherit policy → send → suppress → inherit
policy. Each rule also has an edit button that opens a single-rule form for name,
AND/OR logic, all conditions, notification behavior, and optional rejection
reason. Save normalizes legacy `reject_reason`, `rejectReason`, `拒签理由`, or
`拒签原因` into `reason`; a rule with no reason field remains valid.

Manual rule syntax:

```text
加规则 拒签 描述 has_cn --name 简体拒签 --reason 描述含简体字 --notify suppress
加规则 通知 描述 contains 紧急 --name 紧急发群 --notify send
改拒签理由 0 资料不完整
清除拒签理由 0
加规则 签核 申请人 in_user_group 常用申请人 描述 starts_with_content_group 常规料号 --name 组签核
```

The Feishu management UI is card-first:

- `规则` opens the rule list and a Card JSON 2.0 editor for every rule.
- `组管理` opens user/content group cards with create/edit/rename/delete forms;
  renaming updates every action and notification rule reference.
- `设置` opens the settings card for automatic signing, incremental manual-pending
  private reminders, schedule, waiting, and default group notification.
- `执行一次自动签核` (also `自动签核一次`, `立即自动签核`) runs one rule-driven
  cycle for the current logged-in user. It bypasses the saved schedule/pause only
  for that run, does not change saved settings, and never acts on unmatched items.
  A submit or platform-verification exception must return a failed result and a
  credential-safe reason; it must never fall back to a "no processable items"
  success message.
- In group chat, `@人员 执行一次自动签核` runs that mentioned logged-in
  person's rule cycle. Multiple mentioned people are handled independently.
  Mentioning the bot alone does nothing. The same chat/person is debounced for
  five minutes; action and group-notification decisions still use the target
  person's rules and settings.
- `待手动提醒 开|关` controls an independent read-only monitor. Its first run
  establishes a baseline; later runs privately notify only newly added manual or
  confirmation-required items. It may run while automatic signing is paused,
  never sends an empty-list notification, and must never execute actions by itself.
- `等待设置` / `等签核` opens a card containing only other logged-in users.
  Multiple selections use ANY semantics. When any selected user completes a real
  signing action, run exactly one cycle of the waiting user's current rules,
  leave unmatched items manual, then clear the wait. There is no action selector
  and no manually typed person name.
- Bot menu event keys are `rules`, `groups`, `settings`, and `stats`, in addition
  to `help` and `query_pending`. `stats` returns the current user's OAuth-protected
  statistics page card.

The OAuth page has `统计`, `规则`, `用户组/内容组`, and `设置` sections. Rule
mutations use field-dependent operator dropdowns: applicant exposes existing
user groups; description exposes existing content groups with starts/ends/
contains and their negations. Group values are selected, never free-typed.
All reads and writes derive ownership from the OAuth session `open_id` and all
POST requests require a CSRF token.

`/stats/kpi` is a global production KPI page and is not a normal per-user page.
It is available only when the OAuth session `open_id` matches `private_id` or an
explicit `kpi_admin_open_ids` entry. Query parameters must never grant access.
The page reports unique-work-item automatic handling rate, initial manual-route
rate, platform-verification failure rate, and first-seen-to-verified average
duration.

Every OAuth page exposes a Simplified/Traditional switch. `settings.json`
`ui_language` defaults to `simplified`, is updated from the user's latest Feishu
message containing Chinese (`traditional` only for clear all-Traditional input),
and is also updated by the CSRF-protected web switch. Traditional rendering may
translate visible labels, placeholders, and displayed data, but must not mutate
form values, textarea contents, URLs, scripts, stored rules, or group identifiers.
