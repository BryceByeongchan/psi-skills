# psi-agent Examples

Example DFT projects demonstrating psi provenance tracking workflows. Each
example contains a `prompt.md` with step-by-step `psi:` commands that can be
executed in a Claude Code session.

## Prerequisites

1. Install psi-cli: `pip install -e /path/to/psi-agent`
2. Copy agent: `cp agents/psi.md ~/.claude/agents/psi.md`

## Examples

| # | Project | Code | Features Demonstrated |
|---|---------|------|----------------------|
| 01 | [MoS2 — QE + Wannier90](01_MoS2_qe_wannier/) | QE, Wannier90 | Multi-code workflow, Wannierization chain |
| 02 | [MoS2 — VASP](02_MoS2_vasp/) | VASP | SOC bands, PBE vs SOC comparison |
| 03 | [Si convergence](03_Si_convergence/) | VASP | Parameter sweeps, convergence report, production chain |
| 04 | [Fe magnetism](04_Fe_magnetism/) | VASP | Spin-polarized, SOC, magnetic anisotropy energy |
| 05 | [Gr/hBN heterostructure](05_graphene_hetero/) | VASP | Multi-parent DAG, functional comparison, 2D heterostructure |

## How to Use

1. Create a new empty directory for each test
2. Start a Claude Code session in that directory
3. Copy-paste the `psi:` commands from `prompt.md` sequentially
4. Observe the provenance graph building up

Each example is self-contained — no actual HPC access needed to test the
tracking workflow (calculations are manually marked as completed with mock
results).
