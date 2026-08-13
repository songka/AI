# AS228T confirmation-file template

Use this compact structure for each G0–G7 artifact in `references/project-confirmation-workflow.md`.

```text
Project:
Document:
Revision:
Status: 草案 | 待确认 | 已确认 | 已作废
Date:
Confirmed by/user wording:

Confirmed decisions:
- ...

Assumptions/site checks:
- ...

Open items:
- none | ...

Sources:
- drawing/project/manual/file ...

Downstream impact:
- valid artifacts ...
- artifacts requiring reconfirmation ...
```

For tables, keep stable IDs so revisions can identify changed rows. Never silently delete a previously confirmed decision; record it as changed or obsolete.
