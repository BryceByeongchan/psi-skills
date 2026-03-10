---
name: rubato-bgw-kernel
user-invokable: true
description: Generate and validate kernel.inp for BerkeleyGW BSE kernel calculation
argument-hint: "number_val_bands:N number_cond_bands:N [screened_coulomb_cutoff:Ry] [calc_id:cNNN] [options...] | validate:<input_file>"
---

Generate or validate `kernel.inp` for the `kernel.x` executable, which computes the electron-hole interaction kernel for the Bethe-Salpeter equation (BSE).

## Usage

**Generate mode** (default):
```
rubato:bgw-kernel number_val_bands:N number_cond_bands:N [screened_coulomb_cutoff:Ry] [bare_coulomb_cutoff:Ry] [calc_id:cNNN] [options...]
```

**Validate mode**:
```
rubato:bgw-kernel validate:<input_file>
```

### Generate arguments

- `number_val_bands:N` — **Required.** Number of valence bands in BSE kernel.
- `number_cond_bands:N` — **Required.** Number of conduction bands in BSE kernel.
- `screened_coulomb_cutoff:Ry` — Cutoff for screened Coulomb W. If omitted, uses epsilon_cutoff.
- `bare_coulomb_cutoff:Ry` — Cutoff for bare Coulomb v. If omitted, uses WFN cutoff.
- `calc_id:cNNN` — Save to `calc_db/{calc_id}/input/`. If omitted, save to current directory.
- `extended_kernel` — Include if full (non-TDA) BSE is planned.
- `cell_slab_truncation` / `cell_box_truncation` / `cell_wire_truncation` — Coulomb truncation for low-dimensional systems.
- `screening_semiconductor` / `screening_metal` / `screening_graphene` — Screening model (default: semiconductor).

## Execution — Generate Mode

### Step 1: Construct kernel.inp

```
number_val_bands          {number_val_bands}
number_cond_bands         {number_cond_bands}
screened_coulomb_cutoff   {screened_coulomb_cutoff}
bare_coulomb_cutoff       {bare_coulomb_cutoff}
```

Optional additions (include only if user requests):
```
extended_kernel                    # for full BSE (non-TDA)
cell_slab_truncation               # for 2D systems
screening_semiconductor            # default, usually omitted
use_wfn_hdf5                       # if using HDF5 wavefunctions
```

### Step 2: Validate the generated input

```bash
python {skill_dir}/bgw_validate.py '{"mode": "validate", "input_file": "<temp_path>", "ref_file": "{skill_dir}/refs/kernel.json"}'
```

If errors are found, fix them before proceeding.

### Step 3: Show and save

1. Show the complete `kernel.inp` to the user.
2. If the validator found warnings, show them.
3. Ask for confirmation or modifications.
4. Save to `calc_db/{calc_id}/input/kernel.inp` if `calc_id` is given, or `./kernel.inp` otherwise.

## Execution — Validate Mode

When `validate:<input_file>` is given, validate an existing kernel.inp file.

### Step 1: Run mechanical validation

```bash
python {skill_dir}/bgw_validate.py '{"mode": "validate", "input_file": "<path>", "ref_file": "{skill_dir}/refs/kernel.json"}'
```

### Step 2: Semantic validation (your judgment)

- `number_val_bands` and `number_cond_bands` are required. Error if missing.
- `screened_coulomb_cutoff` must be <= `epsilon_cutoff` and <= `bare_coulomb_cutoff`.
- Only one Coulomb truncation keyword should be present (mutually exclusive).
- Only one screening model should be present (mutually exclusive).
- If `extended_kernel` is set, this implies a non-TDA BSE absorption calculation is planned.
- `use_symmetries_coarse_grid` must match between kernel.inp and absorption.inp.

### Step 3: Report results

1. Show summary: N errors, M warnings.
2. List each error with explanation and fix suggestion.
3. Add semantic issues from Step 2.
4. Offer to fix issues automatically.

### Keyword lookup

```bash
python {skill_dir}/bgw_validate.py '{"mode": "lookup", "ref_file": "{skill_dir}/refs/kernel.json", "variables": ["keyword1", ...]}'
```

## Rules

- **`number_val_bands` and `number_cond_bands` are always required.** If the user does not provide them, ask.
- **Coulomb truncation keywords are mutually exclusive.** Only one of `spherical_truncation`, `cell_box_truncation`, `cell_wire_truncation`, `cell_slab_truncation` may be used.
- **Screening keywords are mutually exclusive.** Only one of `screening_semiconductor`, `screening_metal`, `screening_graphene` may be used.
- **For 2D systems (slabs/monolayers), always include `cell_slab_truncation`.** Warn if a slab system is detected but truncation is missing.
- **`extended_kernel` is required for non-TDA BSE.** If the user plans full BSE absorption, include this keyword.
- **Show the complete kernel.inp before saving.** Never write without user confirmation.
- **When saving to a calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/kernel.inp`.
- **In validate mode, show all errors at once.** Suggest fixes for every error.
