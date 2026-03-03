---
name: psi-list-computers
user-invokable: true
description: List registered computers
---

List all registered computers with their configuration and SSH status.

## Usage

```
psi:list-computers
```

## Execution

```bash
python {skill_dir}/list_computers.py [--json]
```

Without `--json`: displays a formatted table with SSH status for HPC computers.
With `--json`: outputs raw JSON for programmatic use.
