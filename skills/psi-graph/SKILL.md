---
name: psi-graph
user-invokable: true
description: Display provenance DAG
argument-hint: "[calc_id]"
---

Display the provenance graph as a Unicode tree.

## Usage

```
psi:graph [calc_id]
```

- Without an ID: shows the full DAG from all root nodes.
- With an ID: shows ancestors, the target (highlighted), and descendants.

## Execution

```bash
python {skill_dir}/graph.py [calc_id]
```

Display the output directly to the user.
