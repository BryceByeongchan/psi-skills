---
name: psi-update-calc
user-invokable: true
description: Update a calculation's metadata
argument-hint: "<calc_id> [field=value ...]"
---

Update a calculation's metadata fields.

## Usage

```
psi:update-calc <id> [field=value ...]
```

**You** parse the field=value pairs — this requires judgment:
- Dot notation: `key_results.energy=-5.43` → nested dict update.
- Comma-separated lists: `tags=silicon,relaxation` → list.
- Status values: `status=completed`.

## Execution

Build a JSON object from parsed field=value pairs and run:

```bash
python {skill_dir}/update_calc.py <calc_id> '<json>'
```

The script handles: frontmatter read/merge/write, index update, parent link changes.

## Rules

- **Do NOT use sed to modify index files.** All index updates go through the script.
- **Preserve the markdown body below frontmatter unchanged.**
