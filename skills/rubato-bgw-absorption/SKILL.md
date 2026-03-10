---
name: rubato-bgw-absorption
user-invokable: true
description: Generate and validate absorption.inp for BerkeleyGW BSE optical absorption calculation
argument-hint: "number_val_bands_coarse:N number_cond_bands_coarse:N number_val_bands_fine:N number_cond_bands_fine:N energy_resolution:eV [calc_id:cNNN] [options...] | validate:<input_file>"
---

Generate or validate `absorption.inp` for the `absorption.x` executable, which solves the Bethe-Salpeter equation (BSE) to compute optical absorption spectra and exciton properties.

## Usage

**Generate mode** (default):
```
rubato:bgw-absorption number_val_bands_coarse:N number_cond_bands_coarse:N number_val_bands_fine:N number_cond_bands_fine:N energy_resolution:eV [calc_id:cNNN] [options...]
```

**Validate mode**:
```
rubato:bgw-absorption validate:<input_file>
```

### Generate arguments

- `number_val_bands_coarse:N` — **Required.** Valence bands on coarse grid (must match kernel.inp).
- `number_cond_bands_coarse:N` — **Required.** Conduction bands on coarse grid (must match kernel.inp).
- `number_val_bands_fine:N` — **Required.** Valence bands on fine grid.
- `number_cond_bands_fine:N` — **Required.** Conduction bands on fine grid.
- `energy_resolution:eV` — **Required.** Broadening width for absorption spectrum (eV). Typical: 0.05–0.15 eV.
- `calc_id:cNNN` — Save to `calc_db/{calc_id}/input/`. If omitted, save to current directory.
- `use_velocity` — Use velocity operator for dipole transitions (recommended).
- `use_momentum` — Use momentum operator (no WFNq_fi needed).
- `diagonalization` / `haydock` / `lanczos` — Solver method (default: diagonalization).
- `tda_bse` / `full_bse` — TDA (default) or full BSE.
- `eqp_co_corrections` — Interpolate QP corrections from coarse to fine grid.
- `write_eigenvectors:N` — Write first N eigenvectors (0=none).
- `gaussian_broadening` / `lorentzian_broadening` / `voigt_broadening` — Broadening type.
- `cell_slab_truncation` / `cell_box_truncation` / `cell_wire_truncation` — Coulomb truncation.

## Execution — Generate Mode

### Step 1: Construct absorption.inp

```
number_val_bands_coarse    {number_val_bands_coarse}
number_cond_bands_coarse   {number_cond_bands_coarse}
number_val_bands_fine      {number_val_bands_fine}
number_cond_bands_fine     {number_cond_bands_fine}

diagonalization
use_velocity
gaussian_broadening
energy_resolution          {energy_resolution}
```

Optional additions (include only if user requests):
```
eqp_co_corrections                 # interpolate QP corrections
write_eigenvectors  {N}            # write first N exciton eigenvectors
use_wfn_hdf5                       # HDF5 wavefunctions
cell_slab_truncation               # 2D Coulomb truncation
screening_semiconductor            # default, usually omitted
haydock                            # iterative solver (replaces diagonalization)
number_iterations    100           # for haydock/lanczos
full_bse                           # non-TDA (replaces tda_bse)
```

### Step 2: Validate the generated input

```bash
python {skill_dir}/bgw_validate.py '{"mode": "validate", "input_file": "<temp_path>", "ref_file": "{skill_dir}/refs/absorption.json"}'
```

If errors are found, fix them before proceeding.

### Step 3: Show and save

1. Show the complete `absorption.inp` to the user.
2. If the validator found warnings, show them.
3. Ask for confirmation or modifications.
4. Save to `calc_db/{calc_id}/input/absorption.inp` if `calc_id` is given, or `./absorption.inp` otherwise.

## Execution — Validate Mode

When `validate:<input_file>` is given, validate an existing absorption.inp file.

### Step 1: Run mechanical validation

```bash
python {skill_dir}/bgw_validate.py '{"mode": "validate", "input_file": "<path>", "ref_file": "{skill_dir}/refs/absorption.json"}'
```

### Step 2: Semantic validation (your judgment)

- All four band counts are required. Error if any are missing.
- `energy_resolution` is required. Error if missing.
- `number_val_bands_coarse` and `number_cond_bands_coarse` must match kernel.inp values.
- `number_val_bands_fine` >= `number_val_bands_coarse` (typically).
- `number_cond_bands_fine` >= `number_cond_bands_coarse` (typically).
- Solver keywords are mutually exclusive: only one of `diagonalization`, `haydock`, `lanczos`, `diagonalization_primme`.
- Broadening keywords are mutually exclusive: only one of `gaussian_broadening`, `lorentzian_broadening`, `voigt_broadening`.
- `haydock` requires `lorentzian_broadening`. Warn if `gaussian_broadening` is used with `haydock`.
- `full_bse` auto-sets `extended_kernel`. Warn if `extended_kernel` is missing from kernel.inp.
- `use_symmetries_coarse_grid` must match kernel.inp setting.
- Only one Coulomb truncation keyword should be present (mutually exclusive).
- Only one screening model should be present (mutually exclusive).

### Step 3: Report results

1. Show summary: N errors, M warnings.
2. List each error with explanation and fix suggestion.
3. Add semantic issues from Step 2.
4. Offer to fix issues automatically.

### Keyword lookup

```bash
python {skill_dir}/bgw_validate.py '{"mode": "lookup", "ref_file": "{skill_dir}/refs/absorption.json", "variables": ["keyword1", ...]}'
```

## Rules

- **All four band counts and `energy_resolution` are always required.** If the user does not provide them, ask.
- **`number_val_bands_coarse` and `number_cond_bands_coarse` must match kernel.inp.** Warn if mismatch detected.
- **Solver keywords are mutually exclusive.** Only one of `diagonalization`, `haydock`, `lanczos`, `diagonalization_primme`.
- **`haydock` only supports `lorentzian_broadening`.** Die with error if combined with `gaussian_broadening`.
- **`voigt_broadening` requires `energy_resolution_sigma` and `energy_resolution_gamma`.** Both Gaussian and Lorentzian components must be specified.
- **`full_bse` requires `extended_kernel` in kernel.inp.** Remind the user of this requirement.
- **For 2D systems, always include `cell_slab_truncation`.** Warn if slab system detected but truncation missing.
- **Show the complete absorption.inp before saving.** Never write without user confirmation.
- **When saving to a calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/absorption.inp`.
- **In validate mode, show all errors at once.** Suggest fixes for every error.
