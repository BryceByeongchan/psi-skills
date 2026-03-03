---
name: psi-push-calc
user-invokable: true
description: Push calculation files to remote HPC
argument-hint: "<calc_id> [--all]"
---

Push local calculation files to the remote HPC computer via rsync.

## Usage

```
psi:push-calc <calc_id> [--all]
```

- Default: pushes `input/`, `code/`, and `README.md`.
- `--all`: pushes the entire calc directory.

## Execution

```bash
python {skill_dir}/push_calc.py <calc_id> [--all]
```

## Rules

- **NEVER hardcode or guess remote paths.** The `hpc_path` is auto-populated from the computer's `work_dir` if not already set.
- All transfers use `rsync -avz -e "ssh"` over the existing ControlMaster connection.
