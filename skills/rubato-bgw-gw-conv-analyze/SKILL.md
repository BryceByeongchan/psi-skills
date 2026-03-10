---
name: rubato-bgw-gw-conv-analyze
user-invokable: true
description: Parse sigma.out files from a convergence sweep and report the QP gap table with convergence suggestion
argument-hint: "calcs:dir1,dir2,... vbm:ik=N,n=M cbm:ik=N,n=M sweep:param [threshold:eV]"
---

Parse `sigma.out` files from a convergence sweep (from `rubato-bgw-gw-conv-sigma` or `rubato-bgw-gw-conv-epsilon`) and report a QP gap convergence table using the Eqp1 column.

## Usage

```
rubato:bgw-gw-conv-analyze calcs:dir1,dir2,... vbm:ik=N,n=M cbm:ik=N,n=M sweep:param [threshold:0.05]
```

- `calcs:dir1,dir2,...` — **Required.** Comma-separated list of directories containing `sigma.out` files. May be absolute paths or relative to current directory.
- `vbm:ik=N,n=M` — **Required.** K-point index and band index of the VBM. Must match what was used in the sigma runs.
- `cbm:ik=N,n=M` — **Required.** K-point index and band index of the CBM. Must match what was used in the sigma runs.
- `sweep:param` — **Required.** Parameter being swept: `screened_coulomb_cutoff`, `number_bands`, or `epsilon_cutoff`. Used for display.
- `threshold:eV` — Convergence criterion: |gap[i] − gap[i−1]| < threshold (default: 0.05 eV).

## Execution

### Step 1: Parse sigma.out files

For each directory, run:

```bash
python {skill_dir}/bgw_conv_analyze.py '{json}'
```

JSON fields:

| Field | Type | Description |
|-------|------|-------------|
| `sigma_out` | string | Path to `sigma.out` file |
| `vbm_ik` | int | VBM k-point index (1-based, from `ik =` in sigma.out) |
| `vbm_n` | int | VBM band index (1-based) |
| `cbm_ik` | int | CBM k-point index (1-based) |
| `cbm_n` | int | CBM band index (1-based) |

The script returns JSON:
```json
{
  "vbm_eqp1": -1.045,
  "cbm_eqp1":  1.423,
  "gap":        2.468,
  "found_vbm": true,
  "found_cbm": true,
  "error": null
}
```

### Step 2: Extract sweep parameter value

For each directory, determine the swept parameter value. This is done by reading the sigma.inp (or epsilon.inp) in the same directory:
- If sweeping `screened_coulomb_cutoff` or `number_bands`: read from `sigma.inp` in the same directory.
- If sweeping `epsilon_cutoff`: read from `epsilon.inp` in the same directory.

If the parameter cannot be read, use the directory name as the label.

### Step 3: Build and print convergence table

Sort the results by the sweep parameter value (ascending). Then print:

```
sweep: {param}    threshold: {threshold} eV
-------------------------------------------------------
 dir            | param  | E_VBM  | E_CBM  |  gap   | delta
-------------------------------------------------------
 dir1           |  15 Ry | -1.045 |  1.423 | 2.468  |  —
 dir2           |  20 Ry | -1.031 |  1.427 | 2.458  | 0.010
 dir3           |  25 Ry | -1.029 |  1.428 | 2.457  | 0.001  <-- converged
 dir4           |  30 Ry | -1.028 |  1.428 | 2.456  | 0.001
-------------------------------------------------------
Suggestion: converged at {param}={converged_value} (delta < {threshold} eV)
```

Convergence is declared when |gap[i] − gap[i−1]| < threshold for the first time. The converged value is the parameter at that point.

If no convergence is reached, print:
```
WARNING: Gap did not converge within the sweep range. Consider extending the sweep.
```

### Step 4: (Optional) Summary suggestion

After the table, suggest the converged parameter value for use in production calculations.

## Rules

- **Eqp1 is the converged QP energy** (linearized quasiparticle energy). Always use Eqp1, never Eqp0.
- **`ik` and `n` are 1-based indices** matching the `ik =` and `n` columns in sigma.out.
- **Sort results by sweep parameter** before computing deltas. Do not use directory order.
- If a `sigma.out` file is missing or does not contain the requested k/band, report an error for that point and continue.
- **The QP gap = E_CBM(Eqp1) − E_VBM(Eqp1).** Report positive gap values.
- If both VBM and CBM are at the same k-point, report both energies from that single k-block.
