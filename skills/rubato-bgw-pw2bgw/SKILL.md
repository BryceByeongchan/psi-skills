---
name: rubato-bgw-pw2bgw
user-invokable: true
description: Generate pw2bgw.inp for QE → BerkeleyGW format conversion (WFN, RHO, VXC, VSC, VKB)
argument-hint: "[parent:cNNN] [calc_id:cNNN] [options...]"
---

Generate `pw2bgw.inp` for the `pw2bgw.x` executable (Quantum ESPRESSO → BerkeleyGW wavefunction conversion).

## Usage

```
rubato:bgw-pw2bgw [parent:cNNN] [calc_id:cNNN] [options...]
```

- `parent:cNNN` — Parent QE nscf calculation. **Required** to extract `prefix`, `outdir`, k-grid (`nk1`, `nk2`, `nk3`), and `nbnd`.
- `calc_id:cNNN` — Save `pw2bgw.inp` to `calc_db/{calc_id}/input/`. If omitted, save to current directory.
- Any namelist field can be overridden as `field=value` (e.g., `outdir=./out`).

## Execution

### Step 1: Read parent nscf input

If `parent:cNNN` is given, read `calc_db/{parent_dir}/input/pw.in` to extract:
- `prefix` — from `&CONTROL prefix = '...'`
- `outdir` — from `&CONTROL outdir = '...'`
- `nk1`, `nk2`, `nk3` — from `K_POINTS automatic` card (first three integers)
- `nbnd` — from `&SYSTEM nbnd = ...`

### Step 2: Construct pw2bgw.inp

Always write the full namelist:

```fortran
&input_pw2bgw
  prefix        = '{prefix}'
  outdir        = '{outdir}'
  real_or_complex = 2
  wfng_flag     = .true.
  wfng_file     = 'WFN'
  wfng_kgrid    = .true.
  wfng_nk1      = {nk1}
  wfng_nk2      = {nk2}
  wfng_nk3      = {nk3}
  wfng_dk1      = 0.0
  wfng_dk2      = 0.0
  wfng_dk3      = 0.0
  rhog_flag     = .true.
  rhog_file     = 'RHO'
  vxcg_flag     = .true.
  vxcg_file     = 'VXC'
  vxc_flag      = .true.
  vxc_diag_nmin = 1
  vxc_diag_nmax = {nbnd}
  vscg_flag     = .true.
  vscg_file     = 'VSC'
  vkbg_flag     = .true.
  vkbg_file     = 'VKB'
/
```

### Step 3: Show and save

1. Show the complete `pw2bgw.inp` to the user.
2. Ask for confirmation or modifications.
3. Save to `calc_db/{calc_id}/input/pw2bgw.inp` if `calc_id` is given, or `./pw2bgw.inp` otherwise.

## Validation

Before saving, check:
- `wfng_nk1`, `wfng_nk2`, `wfng_nk3` must all be > 0. Die with a clear error if any are zero (parent k-grid not found).
- `vxc_diag_nmax` must equal `nbnd` from the parent nscf. Warn if not.

## Rules

- **Always set `real_or_complex = 2`.** BerkeleyGW GW calculations always use complex wavefunctions.
- **Always output all five file types**: WFN, RHO, VXC (both vxcg and vxc matrix elements), VSC, VKB. These are all required for the full GW workflow.
- **`vxc_diag_nmax` must equal the parent `nbnd`.** The sigma code reads vxc.dat for all bands.
- **`outdir` must match the parent pw.x `outdir` exactly** so pw2bgw.x can find the QE output files.
- **Show the complete pw2bgw.inp before saving.** Never write without user confirmation.
- **When saving to a calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/pw2bgw.inp`.
- If no parent is given and k-grid is unknown, ask the user for `nk1`, `nk2`, `nk3` and `nbnd` explicitly.
