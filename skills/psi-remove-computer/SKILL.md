---
name: psi-remove-computer
user-invokable: true
description: Remove a computer from the registry
argument-hint: "<name>"
---

Remove a registered computer.

## Usage

```
psi:remove-computer <name>
```

Before removing, check if any calcs reference this computer and warn the user.

## Execution

```bash
python {skill_dir}/remove_computer.py <name>
```
