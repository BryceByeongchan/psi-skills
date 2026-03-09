---
name: psi-qe-plotbands
user-invokable: true
description: Plot band structure from Quantum Espresso bands.x XML output
argument-hint: "<xml_file> [--labels \"G M K G\"] [--erange -4 4] [--out bands.png] [--title \"Title\"] [--spin 0]"
---

Plot band structure from a Quantum ESPRESSO `bands.x` XML output file.

## Prerequisites

```bash
pip install numpy matplotlib
```

## Usage

```
psi:qe-plotbands <xml_file> [--labels "G M K G"] [--erange -4 4] [--out bands.png] [--title "Title"] [--spin 0]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `xml` | Path to QE bands XML file | required |
| `--labels` | High-sym k-point labels, space-separated | none |
| `--erange` | Energy window in eV | `-4 4` |
| `--out` | Output PNG filename | `<xml_stem>_bands.png` |
| `--title` | Plot title | none |
| `--spin` | Spin channel: 0=up, 1=dn (spin-polarized only) | `0` |

### Label shorthand

`G` or `GAMMA` → `Γ`. All standard k-point symbols are supported as-is (M, K, A, L, H, X, …).

## Execution

Run the bundled Python script:

```bash
python {skill_dir}/qe_plotbands.py <xml> [options]
```

## Workflow

When the user asks to plot a band structure:

1. Identify the XML file (look for `*.xml` in the current directory if not specified; prefer files in `bands/` or `*/bands.save/`)
2. Ask the user for k-path labels if not provided (e.g., `"G M K G"`)
3. Run:
   ```bash
   python {skill_dir}/qe_plotbands.py <xml> --labels "<labels>" [--erange <emin> <emax>] [--out <png>] [--title "<title>"]
   ```
4. Report the output PNG filename

## Examples

```bash
# Basic — no labels
python {skill_dir}/qe_plotbands.py bands/pwscf.xml

# With k-path labels
python {skill_dir}/qe_plotbands.py bands/pwscf.xml --labels "G M K G A L H A"

# Custom energy window and output
python {skill_dir}/qe_plotbands.py bands/pwscf.xml --labels "G M K G" --erange -6 4 --out ws2_bands.png --title "2H-WS2"

# Spin-down channel
python {skill_dir}/qe_plotbands.py bands/pwscf.xml --labels "G M K G" --spin 1
```

## Output

Saves a `<name>_bands.png` figure (200 dpi, 3.3×3.3 in) with:
- Bands aligned to Fermi energy (E − E_F)
- Vertical lines at high-sym k-points
- Dashed horizontal line at E = 0

## Rules

- **Always ask for k-path labels** if not provided. The plot is much more useful with labeled high-symmetry points.
- **Show the output PNG path** after plotting so the user can open it.
- **If the XML file is not found**, search for `*.xml` in common locations (`bands/`, `*/bands.save/`, `./out/`).
- **For spin-polarized calculations**, inform the user that `--spin 0` (up) is default and `--spin 1` plots down channel.
- **If `calc_id` context is available**, look for the XML file in `calc_db/{calc_id}/output/` or similar paths.
