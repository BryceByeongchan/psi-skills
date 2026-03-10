---
name: rubato-bgw-sigma
user-invokable: true
description: Generate and validate sigma.inp for BerkeleyGW self-energy (quasiparticle correction) calculation
argument-hint: "screened_coulomb_cutoff:Ry number_bands:N [parent_epsilon:cNNN] [calc_id:cNNN] [options...] | validate:<input_file>"
---

Generate or validate `sigma.inp` for the `sigma.x` executable, which computes the GW self-energy and quasiparticle (QP) corrections.

## Usage

**Generate mode** (default):
```
rubato:bgw-sigma screened_coulomb_cutoff:Ry number_bands:N [parent_epsilon:cNNN] [calc_id:cNNN] [options...]
```

**Validate mode**:
```
rubato:bgw-sigma validate:<input_file>
```

### Generate arguments

- `screened_coulomb_cutoff:Ry` — Cutoff for the screened Coulomb interaction (must be <= epsilon_cutoff).
- `number_bands:N` — Number of bands in the CH sum (must be <= epsilon number_bands).
- `parent_epsilon:cNNN` — Parent epsilon calculation. Used to read `epsilon_cutoff` and `number_bands` for constraint checks.
- `calc_id:cNNN` — Save `sigma.inp` to `calc_db/{calc_id}/input/`. If omitted, save to current directory.
- `frequency_dependence:N` — 1 = GPP (default), 2 = full-frequency. Must match the parent epsilon `frequency_dependence`.
- `kpoints:...` — K-points for QP correction. If not given, **you must ask the user**.
- `diag:...` — Band indices for QP correction. If not given, **you must ask the user**.
- `mode:convergence` — Convergence test mode: use only VBM + CBM k-points in kpoints block (fast).

## Execution — Generate Mode

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

### Step 4: Validate the generated input

Before showing the result, run the validator:

```bash
python {skill_dir}/bgw_validate.py '{"mode": "validate", "input_file": "<temp_path>", "ref_file": "{skill_dir}/refs/sigma.json"}'
```

If errors are found, fix them before proceeding.

### Step 5: Show and save

1. Show the complete `sigma.inp` to the user.
2. If the validator found warnings, show them.
3. Ask for confirmation or modifications.
4. Save to `calc_db/{calc_id}/input/sigma.inp` if `calc_id` is given, or `./sigma.inp` otherwise.

## Execution — Validate Mode

When `validate:<input_file>` is given, validate an existing sigma.inp file.

### Step 1: Run mechanical validation

```bash
python {skill_dir}/bgw_validate.py '{"mode": "validate", "input_file": "<path>", "ref_file": "{skill_dir}/refs/sigma.json"}'
```

### Step 2: Semantic validation (your judgment)

- `screened_coulomb_cutoff` must be <= `epsilon_cutoff`. If parent epsilon is accessible, check.
- `number_bands` must be <= `epsilon.number_bands`. If parent is accessible, check.
- `frequency_dependence` must match epsilon: epsilon 0 -> sigma 1 (GPP), epsilon 2 -> sigma 2 (FF).
- The kpoints block must not be empty.
- The diag block must not be empty.
- `epsilon_cutoff` should NOT appear in sigma.inp (that is an epsilon-only keyword).

### Step 3: Report results

1. Show summary: N errors, M warnings.
2. List each error with explanation and fix suggestion.
3. List warnings.
4. Add semantic issues from Step 2.
5. Offer to fix issues automatically if the user wants.

### Keyword lookup

```bash
python {skill_dir}/bgw_validate.py '{"mode": "lookup", "ref_file": "{skill_dir}/refs/sigma.json", "variables": ["keyword1", ...]}'
```

## K-Points Format

Each line in the `begin kpoints ... end` block:
```
kx  ky  kz  divisor
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

## Frequency Dependence Mapping

| epsilon `frequency_dependence` | sigma `frequency_dependence` | Description |
|---|---|---|
| 0 | 1 | GPP (Hybertsen-Louie, default) |
| 2 | 2 | Full-frequency contour deformation |

## Convergence Test Mode

When `mode:convergence` is given:
- Include only the VBM and CBM k-points in the kpoints block.
- Ask user for: `vbm_kpt` and `cbm_kpt`.
- The `diag` block should include the VBM and CBM band indices.

## Rules

- **`screened_coulomb_cutoff` <= `epsilon_cutoff`.** Enforce this constraint.
- **`number_bands` <= `epsilon.number_bands`.** Enforce this constraint.
- **`bare_coulomb_cutoff` defaults to `screened_coulomb_cutoff`.** Only separate them if the user requests.
- **The kpoints and diag blocks are required.** If not provided, ask the user.
- **`frequency_dependence` must be consistent with parent epsilon.** Warn if mismatched.
- **Show the complete sigma.inp before saving.** Never write without user confirmation.
- **When saving to a calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/sigma.inp`.
- **In validate mode, show all errors at once.** Do not stop at the first error.
- **Suggest fixes for every error.**
