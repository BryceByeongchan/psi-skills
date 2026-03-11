# RUBATO

**RUBATO: Research Utility Bot for Ab-initio TOolkits**

A collection of Claude Code skills for ab-initio computational research. Each skill is a self-contained unit with a SKILL.md prompt and a Python script.

## Project Structure

```
skills/
├── rubato-fetch-struct/          # Fetch structure from Materials Project
├── rubato-qe-input-generator/    # Generate QE input (pw.x + post-processing)
├── rubato-qe-input-validator/    # Validate QE input against official flags
├── rubato-qe-plotbands/          # Plot band structure from QE bands.x XML
├── rubato-bgw-kgridx/            # Generate kgrid.inp from XSF for k-point generation
├── rubato-bgw-pw2bgw/            # Generate pw2bgw.inp (QE → BGW format)
├── rubato-bgw-parabands/         # Generate parabands.inp (many empty bands via pseudobands)
├── rubato-bgw-epsilon/           # Generate and validate epsilon.inp (dielectric function)
├── rubato-bgw-sigma/             # Generate and validate sigma.inp (self-energy / QP correction)
├── rubato-bgw-kernel/            # Generate and validate kernel.inp (BSE kernel)
├── rubato-bgw-absorption/        # Generate and validate absorption.inp (BSE absorption)
├── rubato-bgw-gw-conv-sigma/     # Convergence sweep: sigma-only (fixed epsmat)
├── rubato-bgw-gw-conv-epsilon/   # Convergence sweep: epsilon+sigma (coarse q-grid)
├── rubato-bgw-gw-conv-analyze/   # Parse sigma.out → QP gap convergence table
└── rubato-bgw-plotbands-gw-dft/  # Plot DFT vs GW band structure overlay
```

Each directory contains:
- `SKILL.md` — Skill prompt (usage, rules, execution instructions)
- `*.py` — Self-contained Python script (depends on PyYAML; `rubato-fetch-struct` and `rubato-qe-input-generator` additionally require `pymatgen`)

## Design Principles

- **Self-contained scripts**: Each Python script inlines all needed utilities. No shared imports.
- **Deterministic file ops in Python, judgment in prompts**: Scripts handle file I/O. SKILL.md prompts handle argument parsing and user interaction.

## Development Rules

- **SKILL.md files are prompts, not code.** Edits must preserve natural-language clarity.
- **Every behavioral fix must become a rule in the relevant SKILL.md.** Not just a memory note.
- **Keep rules minimal and precise.** Each rule addresses one specific failure mode.
- **Do not create shared utility modules.** Each script must be self-contained.
- **After adding or modifying skills, update README.md** to reflect the changes.
