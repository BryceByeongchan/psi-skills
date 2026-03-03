---
name: psi-add-computer
user-invokable: true
description: Register a new computer in the global registry
argument-hint: "<name> <type> [hostname:...] [user:...] [scheduler:...] [work_dir:...]"
---

Register a new computer for use in psi calculations.

## Usage

```
psi:add-computer <name> <type> [hostname:...] [user:...] [scheduler:...] [work_dir:...] [queues:...] [modules:...] [env_setup:...]
```

**You** parse the keyword arguments into a JSON object. Then run:

## Execution

```bash
python {skill_dir}/add_computer.py <name> '<json>'
```

If type is `hpc`, check SSH connectivity afterward and provide setup instructions if disconnected.

## Rules

- **NEVER create a local `computers/` directory.** The registry is global at `~/.claude/agent-memory/psi/computers.yaml`.
- **NEVER hardcode or guess remote environment details.** When setting up a new HPC computer:
  1. **Work directory**: Run commands on the remote to find scratch/work filesystem (`echo $SCRATCH`, `echo $WORK`, `df -h`). If ambiguous, ask the user.
  2. **Software paths**: Never assume paths for codes (QE, VASP, Wannier90, etc.). Run `which pw.x`, `which vasp_std`, etc. on the remote. If not found, check `module avail` or ask the user.
  3. **Modules**: Do not guess module names/versions. Run `module avail` on the remote to discover available modules.
  4. All remote environment information must be discovered from the live system or confirmed by the user.

## SSH ControlMaster Setup

If SSH is disconnected, print these instructions:

```
# Add to ~/.ssh/config:
Host <alias>
    HostName <hostname>
    User <user>
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist yes
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Start persistent connection:
ssh -MNf <alias>

# Check connection:
ssh -O check <alias>
```
