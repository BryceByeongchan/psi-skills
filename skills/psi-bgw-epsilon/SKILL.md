---
name: psi-bgw-epsilon
user-invokable: true
description: Generate epsilon.inp for BerkeleyGW dielectric function calculation
argument-hint: "epsilon_cutoff:Ry number_bands:N [parent:cNNN] [calc_id:cNNN] [options...]"
---

Generate `epsilon.inp` for the `epsilon.x` executable, which computes the dielectric function (polarizability / inverse dielectric matrix).

## Usage

```
psi:bgw-epsilon epsilon_cutoff:Ry number_bands:N [parent:cNNN] [calc_id:cNNN] [options...]
```

- `epsilon_cutoff:Ry` — **Required.** Plane-wave cutoff for the dielectric matrix in Ry (typical: 15–30 Ry).
- `number_bands:N` — **Required.** Number of bands in the polarizability sum (from WFN_pb). Must be ≤ bands in WFN_pb.
- `parent:cNNN` — Parent parabands (or pw2bgw) calculation. Used to infer the number of available bands in WFN_pb.
- `calc_id:cNNN` — Save `epsilon.inp` to `calc_db/{calc_id}/input/`. If omitted, save to current directory.
- `frequency_dependence:N` — 0 = GPP (default), 2 = full-frequency contour deformation.
- `qpoints:...` — Q-points block. If not given, **you must ask the user** for the q-points list.

## Execution

### Step 1: Gather q-points

The q-points block is required. If the user did not provide q-points, ask:
> "Please provide the q-points list. Format per line: `qx qy qz  divisor  flag` where flag = 0 (regular), 1 (q→0 for semiconductor/insulator), 2 (q=0 exactly for metal)."

For production runs, q-points match the nscf k-grid (all irreducible q-points including q→0). For convergence test runs, a coarse grid (e.g., 2×2×1) may be used.

### Step 2: Construct epsilon.inp

```
epsilon_cutoff    {epsilon_cutoff}
number_bands      {number_bands}

begin qpoints
  {q-points}
end
```

Optional additions (include only if user requests):
```
frequency_dependence  {0|2}    # default: 0 (GPP); 2 = full-frequency
```

**Do not include** `screened_coulomb_cutoff` in epsilon.inp — that keyword belongs to sigma.inp.

### Step 3: Show and save

1. Show the complete `epsilon.inp` to the user.
2. Ask for confirmation or modifications.
3. Save to `calc_db/{calc_id}/input/epsilon.inp` if `calc_id` is given, or `./epsilon.inp` otherwise.

## Q-Points Format

Each line in the `begin qpoints ... end` block:
```
qx  qy  qz  divisor  flag
```
- `qx qy qz` — q-point in fractional coordinates (divided by `divisor`).
- `divisor` — integer divisor; actual q = (qx, qy, qz) / divisor.
- `flag` — 0: regular q; 1: q→0 (small finite displacement, for semiconductors/insulators); 2: q=0 exactly (for metals).

**The block must contain exactly one q→0 or q=0 point** (flag = 1 or 2). This is required for the head of the dielectric matrix.

Example for a 4×4×1 k-grid semiconductor slab (q→0 along x):
```
begin qpoints
  0.001 0.0 0.0  1  1
  0.25  0.0 0.0  1  0
  0.5   0.0 0.0  1  0
  0.0   0.25 0.0 1  0
  0.25  0.25 0.0 1  0
  0.5   0.25 0.0 1  0
  0.0   0.5  0.0 1  0
  0.25  0.5  0.0 1  0
end
```

## Validation

- `epsilon_cutoff`: warn if > 40 Ry ("This is unusually large; confirm this is intentional.").
- `number_bands`: must be ≤ bands available in WFN_pb. If parent is known, check this.
- The qpoints block must contain at least one q-point with flag = 1 or 2 (the q→0 point).
- `frequency_dependence`: valid values are 0 (GPP) and 2 (full-frequency). Value 1 is not used in epsilon.

## Frequency Dependence Notes

- `frequency_dependence 0` (GPP, default): Static calculation, fast. The Generalized Plasmon Pole model is applied in sigma.x. Recommended starting point.
- `frequency_dependence 2` (Full-frequency): Computes frequency-dependent polarizability on a grid. Required for full-frequency sigma. Much more expensive.
- For GW-BSE, GPP is standard. Full-frequency is for advanced users needing more accurate self-energies.

## Rules

- **`epsilon_cutoff` and `number_bands` are always required.** If the user does not provide them, ask.
- **The qpoints block is required.** If not provided, ask the user for the q-points list.
- **Do not add `screened_coulomb_cutoff` to epsilon.inp.** That keyword is only valid in sigma.inp.
- **`epsilon.number_bands` ≥ `sigma.number_bands`.** Remind the user of this constraint when both are being set.
- **Show the complete epsilon.inp before saving.** Never write without user confirmation.
- **When saving to a psi calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/epsilon.inp`.
