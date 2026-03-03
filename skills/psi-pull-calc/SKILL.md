---
name: psi-pull-calc
user-invokable: true
description: Pull calculation files from remote HPC
argument-hint: "<calc_id> [--all]"
---

Pull calculation output files from the remote HPC computer via rsync.

## Usage

```
psi:pull-calc <calc_id> [--all]
```

- Default: pulls `output/` with 50MB size limit. Lists skipped large files.
- `--all`: pulls the entire calc directory without size limit.

## Execution

```bash
python {skill_dir}/pull_calc.py <calc_id> [--all]
```

## Rules

- **NEVER hardcode or guess remote paths.** The `hpc_path` is auto-populated from the computer's `work_dir` if not already set.
- Files above 50MB are never transferred without explicit user approval.
- When skipping large files, always list them with sizes so the user can decide.
