---
name: psi-new-calc
user-invokable: true
description: Create a new calculation entry
argument-hint: "<title> <code> [parents:...] [tags:...] [computer:...]"
---

Create a new calculation entry in the provenance tracking system.

## Usage

```
psi:new-calc <title> <code> [parents:c001,c002] [tags:tag1,tag2] [computer:name]
```

**You** parse the user's arguments — this requires judgment:
- Title: first positional argument (may be multi-word).
- Code: second positional argument (VASP, QE, python, custom, etc.).
- `parents:c001,c002` — comma-separated parent calc IDs.
- `tags:tag1,tag2` — comma-separated tags.
- `computer:name` — registered computer name. If not specified and only one computer is registered, use it. If multiple exist, choose based on context or ask.

## Execution

Build a JSON object from parsed arguments and run:

```bash
python {skill_dir}/new_calc.py '<json>'
```

JSON fields: `title`, `code`, `parents` (list), `tags` (list), `computer` (string).

The script handles: next-id, mkdir, README.md creation, index append, parent link updates.

## Rules

- **Create calcs with the same parent SEQUENTIALLY, not in parallel.** Parallel creation with shared parents causes contention on `index.md` and the parent's `README.md`.
- If a parent ID doesn't exist, warn but still create the calc.
- Use today's date for the `date` field.
