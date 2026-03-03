---
name: psi-new-calc
user-invokable: true
description: Create a new calculation entry
argument-hint: "<title> <code> [parents:...] [tags:...] [computer:...]"
---

Create a new calculation entry in the provenance tracking system.

## Usage

```
psi:new-calc <title> <code> [parents:c001,c002] [tags:tag1,tag2] [computer:name] [type:multi] [subjobs:400,500,600]
```

**You** parse the user's arguments — this requires judgment:
- Title: first positional argument (may be multi-word).
- Code: second positional argument (VASP, QE, python, custom, etc.).
- `parents:c001,c002` — comma-separated parent calc IDs.
- `tags:tag1,tag2` — comma-separated tags.
- `computer:name` — registered computer name. If not specified and only one computer is registered, use it. If multiple exist, choose based on context or ask.
- `type:multi` — creates a multi-job calculation with shared `code/` and per-subjob `{label}/input/`, `{label}/output/`.
- `subjobs:400,500,600` — comma-separated sub-job labels (required when `type:multi`).

## Execution

Build a JSON object from parsed arguments and run:

```bash
python {skill_dir}/new_calc.py '<json>'
```

JSON fields: `title`, `code`, `parents` (list), `tags` (list), `computer` (string), `type` (string, optional), `subjobs` (list of labels, optional).

The script handles: next-id, mkdir, README.md creation, index append, parent link updates.

## Rules

- **Create calcs with the same parent SEQUENTIALLY, not in parallel.** Parallel creation with shared parents causes contention on `index.md` and the parent's `README.md`.
- If a parent ID doesn't exist, warn but still create the calc.
- Use today's date for the `date` field.
- **Use multi-job for systematic parameter variations** (convergence tests, parameter sweeps) where jobs share the same code but vary parameters. Use separate calcs for independent calculations.
- **Sub-job labels must be filesystem-safe**: no spaces, slashes, or special characters. Use alphanumeric, hyphens, and underscores only.
