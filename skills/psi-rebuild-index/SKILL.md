---
name: psi-rebuild-index
user-invokable: true
description: Rebuild index files from README front matter
---

Rebuild both `calc_db/index.md` and `reports/index.md` from the YAML front matter of each entry's `README.md`.

## Usage

```
psi:rebuild-index
```

## Execution

```bash
python {skill_dir}/rebuild_index.py
```

Rebuilds both indexes and reports the number of entries found.
