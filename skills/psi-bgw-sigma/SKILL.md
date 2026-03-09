---
name: psi-bgw-sigma
user-invokable: true
description: Generate sigma.inp for BerkeleyGW self-energy (quasiparticle correction) calculation
argument-hint: "screened_coulomb_cutoff:Ry number_bands:N [parent_epsilon:cNNN] [calc_id:cNNN] [options...]"
---

Generate `sigma.inp` for the `sigma.x` executable, which computes the GW self-energy and quasiparticle (QP) corrections.

## Usage

```
psi:bgw-sigma screened_coulomb_cutoff:Ry number_bands:N [parent_epsilon:cNNN] [calc_id:cNNN] [options...]
```

- `screened_coulomb_cutoff:Ry` — Cutoff for the screened Coulomb interaction (must be ≤ epsilon_cutoff).
- `number_bands:N` — Number of bands in the CH sum (must be ≤ epsilon number_bands).
- `parent_epsilon:cNNN` — Parent epsilon calculation. Used to read `epsilon_cutoff` and `number_bands` for constraint checks.
- `calc_id:cNNN` — Save `sigma.inp` to `calc_db/{calc_id}/input/`. If omitted, save to current directory.
- `frequency_dependence:N` — 1 = GPP (default), 2 = full-frequency. Must match the parent epsilon `frequency_dependence`.
- `kpoints:...` — K-points for QP correction. If not given, **you must ask the user**.
- `diag:...` — Band indices for QP correction. If not given, **you must ask the user**.
- `mode:convergence` — Convergence test mode: use only VBM + CBM k-points in kpoints block (fast).

## Execution

### Step 1: (Optional) Read parent epsilon

If `parent_epsilon:cNNN` is given, read `calc_db/{epsilon_dir}/input/epsilon.inp` to extract:
- `epsilon_cutoff` — for constraint validation of `screened_coulomb_cutoff`.
- `number_bands` — for constraint validation of sigma `number_bands`.

### Step 2: Ask for k-points and diag bands if not given

If `kpoints` are not specified, ask:
> "Please provide the k-points for QP correction. Format per line: `kx ky kz  divisor`. For production, include all nscf k-points. For convergence tests, include only VBM and CBM k-points."

If `diag` bands are not specified, ask:
> "Please provide the band indices for QP correction (one per line in the `begin diag` block). These are the bands for which Eqp0 and Eqp1 are computed."

### Step 3: Construct sigma.inp

```
screened_coulomb_cutoff  {screened_coulomb_cutoff}
bare_coulomb_cutoff      {bare_coulomb_cutoff}
number_bands             {number_bands}

frequency_dependence     {frequency_dependence}

begin kpoints
  {k-points}
end

begin diag
  {band indices}
end
```

- `bare_coulomb_cutoff` defaults to `screened_coulomb_cutoff`. Set them equal unless the user requests otherwise.
- `frequency_dependence`: 1 = GPP (Hybertsen-Louie, default), 2 = full-frequency contour deformation.

### Step 4: Show and save

1. Show the complete `sigma.inp` to the user.
2. Ask for confirmation or modifications.
3. Save to `calc_db/{calc_id}/input/sigma.inp` if `calc_id` is given, or `./sigma.inp` otherwise.

## K-Points Format

Each line in the `begin kpoints ... end` block:
```
kx  ky  kz  divisor
```
- `kx ky kz` — k-point in fractional coordinates (divided by `divisor`).
- `divisor` — integer divisor; actual k = (kx, ky, kz) / divisor.

Example (two k-points for convergence test):
```
begin kpoints
  0  0  0  1
  1  0  0  2
end
```

## Diag Block Format

Each line in the `begin diag ... end` block is a single band index:
```
begin diag
  7
  8
  9
  10
end
```
These are the KS band indices (1-based) for which QP corrections are computed.

## Validation

- `screened_coulomb_cutoff` must be ≤ `epsilon_cutoff` from the parent epsilon. If parent is known, check this.
- `number_bands` must be ≤ `epsilon.number_bands`. If parent is known, check this.
- The kpoints block must not be empty.
- The diag block must not be empty.
- `frequency_dependence` in sigma must match that in the parent epsilon (0 or 2 in epsilon correspond to 1 or 2 in sigma). Specifically:
  - If epsilon used GPP (freq_dep=0), sigma should use `frequency_dependence 1` (GPP).
  - If epsilon used full-frequency (freq_dep=2), sigma should use `frequency_dependence 2`.

## Frequency Dependence Mapping

| epsilon `frequency_dependence` | sigma `frequency_dependence` | Description |
|---|---|---|
| 0 | 1 | GPP (Hybertsen-Louie, default) |
| 2 | 2 | Full-frequency contour deformation |

## Convergence Test Mode

When `mode:convergence` is given:
- Include only the VBM and CBM k-points in the kpoints block (much faster than a full production run).
- Ask user for: `vbm_kpt` and `cbm_kpt` (as fractional coordinates or as indices from the nscf k-list).
- The `diag` block should include the VBM band index and CBM band index.

## Rules

- **`screened_coulomb_cutoff` ≤ `epsilon_cutoff`.** Enforce this constraint and die with a clear error if violated.
- **`number_bands` ≤ `epsilon.number_bands`.** Enforce this constraint.
- **`bare_coulomb_cutoff` defaults to `screened_coulomb_cutoff`.** Only separate them if the user requests.
- **The kpoints and diag blocks are required.** If not provided, ask the user.
- **`frequency_dependence` must be consistent with parent epsilon.** Warn if mismatched.
- **Show the complete sigma.inp before saving.** Never write without user confirmation.
- **When saving to a psi calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/sigma.inp`.
