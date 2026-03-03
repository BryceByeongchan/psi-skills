---
name: psi-update-report
user-invokable: true
description: Update a report's metadata
argument-hint: "<report_id> [field=value ...]"
---

Update a report's metadata fields.

## Usage

```
psi:update-report <id> [field=value ...]
```

**You** parse the field=value pairs — this requires judgment:
- `status=final`
- `calcs=c001,c002,c003` (comma-separated → list)
- `tags=analysis,summary`

## Execution

Build a JSON object from parsed field=value pairs and run:

```bash
python {skill_dir}/update_report.py <report_id> '<json>'
```

The script handles: frontmatter read/merge/write, index update, calc link changes.

## Rules

- **Do NOT use sed to modify index files.** All index updates go through the script.
- **Preserve the markdown body below frontmatter unchanged.**
