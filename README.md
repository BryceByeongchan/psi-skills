# psi-agent

A Claude Code custom agent for computational research provenance tracking. Manages calculation and report tracking using a lightweight, file-based system inspired by AiiDA's provenance graph — no database, no daemon, just markdown and YAML.

## Installation

1. Install the CLI tool (requires Python >= 3.10):

```bash
pip install -e /path/to/psi-agent
```

2. Copy the agent definition to your Claude Code agents directory:

```bash
cp agents/psi.md ~/.claude/agents/psi.md
```

3. Verify the CLI is available:

```bash
psi-cli --help
```

## Architecture

psi-agent has two layers:

- **psi-cli** — a Python CLI that handles all deterministic file operations (YAML parsing, markdown table manipulation, bidirectional link updates, index management)
- **psi subagent** (`agents/psi.md`) — an LLM agent that handles judgment-based tasks (argument parsing, user interaction, content writing) and delegates file I/O to psi-cli

## Usage

Issue commands prefixed with `psi:` in Claude Code:

| Command | Description |
|---------|-------------|
| `psi:init` | Initialize tracking in current project |
| `psi:new-calc [title] [code] [parents:...] [tags:...]` | Create a new calculation entry |
| `psi:update-calc [id] [field=value ...]` | Update calculation metadata |
| `psi:new-report [title] [calcs:...] [tags:...]` | Create a new report |
| `psi:update-report [id] [field=value ...]` | Update report metadata |
| `psi:status` | Show project status summary |
| `psi:graph [id?]` | Display provenance DAG |
| `psi:rebuild-index` | Rebuild index files from front matter |
| `psi:add-computer [name] [type] [...]` | Register an HPC/local computer |
| `psi:list-computers` | List registered computers |
| `psi:remove-computer [name]` | Remove a computer |
| `psi:push-calc [id] [--all]` | Push calc files to remote HPC |
| `psi:pull-calc [id] [--all]` | Pull calc results from remote HPC |

### CLI direct usage

The CLI can also be used directly outside the agent:

```bash
# Read front matter as JSON
psi-cli fm read calc_db/c001/README.md

# Update front matter via JSON merge
echo '{"status":"completed"}' | psi-cli fm write calc_db/c001/README.md

# Get next sequential ID
psi-cli index next-id calc_db

# Rebuild indexes from front matter
psi-cli index rebuild calc_db

# Manage bidirectional links
psi-cli link add-child c001 c002

# Show provenance graph
psi-cli graph

# Project status summary (JSON)
psi-cli status
```

## How It Works

psi tracks two entities:
- **Calculations** (`calc_db/c{NNN}/`) — individual computational jobs (DFT, post-processing, scripts)
- **Reports** (`reports/r{NNN}/`) — analysis documents referencing one or more calculations

Relationships form a DAG (directed acyclic graph):

```
c001 (relax) → c002 (scf) → c003 (bands)
                  └→ c004 (dos)
       r001 references c002, c003
```

All data is stored as markdown with YAML front matter — fully git-friendly, human-readable, and diff-able.

## Development

```bash
pip install -e .
pytest tests/
```

## License

MIT
