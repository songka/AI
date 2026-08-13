---
name: scheme-review
description: Use when reviewing a non-standard automation project scheme from customer URS, process notes, layout sketches, station descriptions, cycle-time targets, acceptance requirements, or meeting notes. Produce structured review questions, risk items, missing-input requests, and a meeting-ready checklist. Do not use for final design approval, pricing commitment, or safety sign-off without human review.
---

# Scheme Review

Use this skill to turn early project inputs into a scheme review checklist for a non-standard automation project.

## Workflow

1. Identify the input type: URS, process description, layout, station list, meeting notes, or mixed materials.
2. Read `references/review-rules.md` before producing the checklist.
3. Extract project context: product, process flow, station sequence, cycle time, acceptance method, site limits, and open assumptions.
4. Separate issues into four groups: missing inputs, technical risks, customer confirmations, and internal owner actions.
5. Write the result in a table using the fields from `assets/review-checklist-template.csv`.
6. End with a short decision status: `can continue`, `continue with assumptions`, or `pause for missing inputs`.

## Output Rules

- Do not invent project facts. If a fact is missing, mark it as `to confirm`.
- Use direct engineering language and avoid generic AI advice.
- Assign each issue to one recommended owner role: sales, PM, mechanical, electrical, software, quality, or customer.
- Mark safety, acceptance, and cycle-time risks as high priority unless the input clearly resolves them.
