# Safety policy

- Permit direct execution only from deterministic explicit commands such as `签核 1 3` or `拒签 2`.
- Convert every AI approve/reject/all decision into a command suggestion; never execute it.
- Route messages containing 模拟、测试、预览、试跑 to preview before query or action parsing.
- Permit `执行一次自动签核` only as a deterministic explicit command. It may
  bypass the user's schedule/pause for one run without changing saved settings,
  but may act only on items matched by the current approve/reject rules. AI output
  must never invoke this command.
- In a group, accept only the exact fixed command `@人员 执行一次自动签核` (or
  documented exact aliases) after removing Feishu mention placeholders. Do not
  require or execute for an @mentioned bot. Target each mentioned logged-in
  person's own rules, keep their notification precedence unchanged, and debounce
  the same chat/target for five minutes in addition to event-ID deduplication.
- Waiting may target one or more already logged-in users and uses ANY semantics.
  A real completion by any target may trigger one current-rule cycle even when
  scheduled automatic signing is paused. It must never force approve/reject on
  unmatched items, must not expose an action selector, and must clear itself
  after the triggered cycle.
- An empty manual-pending result updates the baseline only; never send an empty
  reminder card.
- Route 为什么、怎么、解释、说明 questions to natural chat before query parsing.
- Normalize Simplified, Traditional, and mixed-script Chinese only for intent and
  fixed-command comparison. Preserve the user's original text for AI context and
  rule literal values. If the input has clear all-Traditional characteristics,
  AI natural replies and local AI-fallback guidance must be Traditional; mixed
  input remains supported without changing any signing safety decision.
- Store the latest detected Feishu conversation script per user as the OAuth
  dashboard default. The web language toggle must be session-owned and
  CSRF-protected. Localization is presentation-only: never convert submitted
  values, textarea rule content, URLs, scripts, identifiers, or persisted rules.
- Always confirm full approve/reject against a stored application-number snapshot.
- Confirm a manual approve that conflicts with a reject rule and a manual reject that conflicts with an approve rule.
- Re-fetch pending applications during confirmation and execute only stored application numbers.
- Let manual reject reasons be optional. Use matched reject-rule `reason`, then rule `name`, then `人工拒签（未填写原因）`.
- Do not send group notifications until the platform recheck confirms success.
- Never log passwords, API keys, access tokens, OAuth codes, session cookies, or full credential files.
- Encrypt user credentials and system secrets at rest with a master key supplied
  only by `QH_MASTER_KEY` or `QH_MASTER_KEY_FILE`. Never include the master key,
  `auth.enc`, `secrets.enc`, or encrypted operational backups in a release archive.
- Load service and scheduler secrets from the same repository-external runtime
  environment file (default `/etc/qh/qh.env`) or an approved secret injection
  mechanism. Fail closed when neither source provides a master key, and never
  include the runtime environment file in a release archive.
- Backups must use authenticated encryption, carry a per-file hash manifest, and
  pass a restore drill into an empty temporary/staging directory before they are
  accepted. Production restore must never overwrite an existing data directory.
- Offboarding is an explicit administrative action: require the exact Feishu
  `open_id`, create an encrypted archive first, then remove that user's directory,
  owned statistics, and wait references. Never infer offboarding from chat or AI.
