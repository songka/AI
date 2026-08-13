---
name: validation-doc-check
description: Use when checking validation, quality, biological-process, FAT/SAT, URS traceability, test record, deviation, and acceptance document packages for automation projects. Review completeness, version consistency, signatures, dates, requirement-to-test traceability, deviations, and unresolved evidence gaps. Do not use as final quality release or regulatory approval without authorized reviewer confirmation.
---

# Validation Doc Check

Use this skill to prepare a validation or quality document package for human review.

## Workflow

1. Read `references/validation-rules.md` before checking the package.
2. Identify the document set: URS, design specification, FAT, SAT, test records, deviation list, and acceptance report.
3. Build a traceability view from requirement to evidence where possible.
4. Check signatures, dates, versions, page completeness, test result status, deviation closure, and attachment references.
5. Output issues in the fields shown in `assets/validation-issue-template.csv`.
6. End with a package status: `ready for review`, `minor gaps`, or `major gaps`.

## Boundary

Do not decide regulatory compliance or release status. Provide a structured pre-check for authorized reviewers.
