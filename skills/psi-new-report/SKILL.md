---
name: psi-new-report
user-invokable: true
description: Create a new report entry
argument-hint: "<title> [calcs:...] [tags:...]"
---

Create a new report that references one or more calculations.

## Usage

```
psi:new-report <title> [calcs:c001,c002] [tags:tag1,tag2]
```

**You** parse the arguments:
- Title: first positional argument (may be multi-word).
- `calcs:c001,c002` — comma-separated calc IDs to reference.
- `tags:tag1,tag2` — comma-separated tags.

## Execution

Build a JSON object and run:

```bash
python {skill_dir}/new_report.py '<json>'
```

JSON fields: `title`, `calcs` (list), `tags` (list).

The script handles: next-id, mkdir, README.md creation, index append, calc link updates.
