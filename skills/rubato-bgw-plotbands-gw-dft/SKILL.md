---
name: rubato-bgw-plotbands-gw-dft
user-invokable: true
description: Plot DFT vs GW band structure overlay from QE XML and BerkeleyGW bandstructure.dat
argument-hint: "--dft <xml> --gw <bandstructure.dat> --inteqp <inteqp.inp> [--labels \"G A X G\"] [--erange -2 6] [--out bands.png]"
---

Plot DFT vs GW band structure as an overlay figure. DFT bands from QE pw.x XML (red dashed), GW quasiparticle bands from BerkeleyGW `bandstructure.dat` (blue solid). VBM aligned to 0 eV.

## Prerequisites

```bash
pip install numpy matplotlib
```

No `qwt` dependency — the script parses QE XML directly.

## Usage

```
rubato:bgw-plotbands-gw-dft --dft <xml> --gw <bandstructure.dat> --inteqp <inteqp.inp> [options]
rubato:bgw-plotbands-gw-dft --dft <xml> --gw <bandstructure.dat> --nv <int> [options]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--dft` | Yes | QE pw.x XML output (band structure calculation) |
| `--gw` | Yes | BerkeleyGW `bandstructure.dat` from inteqp |
| `--inteqp` | Yes* | `inteqp.inp` file — reads `number_val_bands_fine` as nv |
| `--nv` | Yes* | Number of valence bands in GW data (alternative to `--inteqp`) |
| `--labels` | No | High-sym k-point labels, space-separated (e.g. `"G A X G M R G Z"`) |
| `--erange` | No | Energy window in eV (default: `-2 6`) |
| `--out` | No | Output PNG filename (default: `<gw_stem>_gw_dft_bands.png`) |
| `--title` | No | Plot title |
| `--no-sort-bands` | No | Disable band sorting at each k-point |
| `--dft-label` | No | DFT legend text (default: `"DFT"`) |
| `--gw-label` | No | GW legend text (default: `"GW"`) |

*Either `--inteqp` or `--nv` is required (mutually exclusive).

### Label shorthand

`G` or `GAMMA` → `Γ`. All standard k-point symbols are supported as-is (M, K, A, L, H, X, R, Z, …).

## Execution

Run the bundled Python script:

```bash
python {skill_dir}/bgw_plotbands_gw_dft.py --dft <xml> --gw <dat> --inteqp <inteqp.inp> [options]
```

## Workflow

When the user asks to plot DFT vs GW bands:

1. **Locate files.** The three required files are typically in the same inteqp directory:
   - `bandstructure.dat` — GW interpolated bands
   - `*.xml` or a nearby QE XML — DFT band structure
   - `inteqp.inp` — contains `number_val_bands_fine`
   If not provided, search the current directory and parent directories.

2. **Determine nv.** Prefer reading from `inteqp.inp` (`number_val_bands_fine`). Only use `--nv` if the user explicitly provides it or `inteqp.inp` is unavailable.

3. **Ask for k-path labels** if not provided. The plot is much more useful with labeled high-symmetry points.

4. **Run the script:**
   ```bash
   python {skill_dir}/bgw_plotbands_gw_dft.py \
       --dft <xml> --gw <dat> --inteqp <inteqp.inp> \
       --labels "<labels>" [--erange <emin> <emax>] [--out <png>]
   ```

5. **Report** the output PNG path and the band gap values (GW and DFT).

## Examples

```bash
# Basic — with inteqp.inp for nv
python {skill_dir}/bgw_plotbands_gw_dft.py \
    --dft Bi2O2Se.xml --gw bandstructure.dat --inteqp inteqp.inp

# With labels and custom energy range
python {skill_dir}/bgw_plotbands_gw_dft.py \
    --dft Bi2O2Se.xml --gw bandstructure.dat --inteqp inteqp.inp \
    --labels "G A X G M R G Z" --erange -1 4

# SOC calculation with custom legend
python {skill_dir}/bgw_plotbands_gw_dft.py \
    --dft Bi2O2Se.xml --gw bandstructure.dat --nv 28 \
    --labels "G A X G M R G Z" --dft-label "DFT-PBE (SOC)" --gw-label "GW (SOC)"

# Explicit nv instead of inteqp
python {skill_dir}/bgw_plotbands_gw_dft.py \
    --dft bands.xml --gw bandstructure.dat --nv 14 --out my_bands.png
```

## Output

Saves a PNG figure (300 dpi, 6×4 in) with:
- DFT bands: red dashed lines (α=0.5)
- GW bands: blue solid lines
- VBM aligned to 0 eV (grey dotted reference line)
- High-symmetry k-point labels and grid lines (if labels provided)
- Legend in upper right corner

Prints to stdout:
- GW band gap (eV) with VBM/CBM values
- DFT band gap (eV) with VBM/CBM values

## How it works

1. **DFT**: Parses QE pw.x XML (eigenvalues in Hartree → eV, crystal k-coords → Cartesian distances)
2. **GW**: Reads `bandstructure.dat` columns: spin | band | kx | ky | kz | E_mf | E_qp | dE
3. **Alignment**: Both shifted so VBM = 0 eV. GW uses `eqp[nv-1].max()`, DFT uses Fermi energy.
4. **k-path scaling**: GW Cartesian k-distances rescaled to match DFT cumulative k-path length.
5. **Band sorting** (default on): At each k-point, bands are sorted by energy to suppress crossing artifacts from interpolation.

## Rules

- **Always ask for k-path labels** if not provided. The plot is significantly more useful with labeled high-symmetry points.
- **Prefer `--inteqp` over `--nv`** to avoid manual errors in valence band count.
- **`number_val_bands_fine`** in `inteqp.inp` is the correct nv (number of valence bands in the fine/interpolated grid), not `number_val_bands_coarse`.
- **Show the output PNG path** and band gap values after plotting.
- **If files are not found**, search for `bandstructure.dat`, `*.xml`, and `inteqp.inp` in common BerkeleyGW directory layouts (e.g., `*-inteqp/`, `*-gwbands/`).
- **DFT energies are aligned to the Fermi energy** from the XML, while GW energies are aligned to VBM from `eqp`. This means DFT VBM may not be exactly at 0 eV — this is expected behavior showing the GW correction.
- **Band sorting is on by default.** Disable with `--no-sort-bands` only if the user wants to see raw interpolated band crossings.
