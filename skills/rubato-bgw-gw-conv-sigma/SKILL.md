---
name: rubato-bgw-gw-conv-sigma
user-invokable: true
description: Set up a sigma-only convergence sweep (reusing a fixed epsmat) for screened_coulomb_cutoff or number_bands
argument-hint: "sweep:param values:v1,v2,v3 parent_epsilon:cNNN [calc_id:cNNN] vbm:ik=N,n=M cbm:ik=N,n=M [options...]"
---

Set up a convergence sweep that runs `sigma.x` multiple times, each with a different value of one parameter, while reusing a single pre-computed `epsmat` from a parent epsilon calculation.

This is Step 2 or Step 3 in the recommended GW convergence workflow.

## Usage

```
rubato:bgw-gw-conv-sigma sweep:param values:v1,v2,v3 parent_epsilon:cNNN [calc_id:cNNN] vbm:ik=N,n=M cbm:ik=N,n=M [options...]
```

- `sweep:param` — **Required.** Parameter to sweep: `screened_coulomb_cutoff` or `number_bands`.
- `values:v1,v2,...` — **Required.** Comma-separated list of values to sweep (e.g., `values:15,20,25,30` for cutoff in Ry, or `values:1000,1500,2000,2500` for bands).
- `parent_epsilon:cNNN` — **Required.** Parent epsilon calculation that produced the large epsmat.
- `calc_id:cNNN` — Optional base calc to anchor the sweep.
- `vbm:ik=N,n=M` — VBM k-point index and band index for the kpoints/diag blocks.
- `cbm:ik=N,n=M` — CBM k-point index and band index for the kpoints/diag blocks.
- `bare_coulomb_cutoff:Ry` — Override bare_coulomb_cutoff (default: = screened_coulomb_cutoff).
- `frequency_dependence:N` — 1 = GPP (default), 2 = full-frequency.

## Execution

### Step 1: Gather required information

1. Read `parent_epsilon` calc to extract:
   - `epsilon_cutoff` (for constraint validation).
   - `number_bands` (for constraint validation of sigma's `number_bands`).
   - K-points list (to determine VBM/CBM k-points in fractional coordinates).

2. If `vbm` and `cbm` are not specified, ask the user for:
   > "Please specify VBM and CBM k-point and band indices: `vbm:ik=N,n=M cbm:ik=N,n=M`"
   > "Where `ik` is the k-point index from the nscf k-list, and `n` is the band index."

3. Determine fixed parameters:
   - If sweeping `screened_coulomb_cutoff`: fix `number_bands` (ask user, or use epsilon's `number_bands`).
   - If sweeping `number_bands`: fix `screened_coulomb_cutoff` (ask user for a converged value, or use epsilon_cutoff as upper bound).

### Step 2: Create sweep subdirectory structure

For each sweep value `v`, create:
```
conv_sigma_{param}/
  val_{v}/
    sigma.inp
```

Inside each `sigma.inp`, set:
- The swept parameter to value `v`.
- The fixed parameters.
- `begin kpoints` block: only VBM + CBM k-points (fast convergence runs).
- `begin diag` block: only VBM + CBM band indices.

**Template for each sigma.inp:**

```
screened_coulomb_cutoff  {screened_coulomb_cutoff}
bare_coulomb_cutoff      {bare_coulomb_cutoff}
number_bands             {number_bands}

frequency_dependence     {frequency_dependence}

begin kpoints
  {vbm_kpt}
  {cbm_kpt}
end

begin diag
  {vbm_n}
  {cbm_n}
end
```

### Step 3: Report

After creating all directories and input files, report:
```
Created convergence sweep: sweep={param}
  conv_sigma_{param}/val_{v1}/sigma.inp
  conv_sigma_{param}/val_{v2}/sigma.inp
  ...

Fixed parameters:
  {other_param} = {value}
  parent epsmat: calc_db/{epsilon_dir}/

To run:
  cd conv_sigma_{param}/val_{v1} && sigma.x < sigma.inp > sigma.out
  cd conv_sigma_{param}/val_{v2} && sigma.x < sigma.inp > sigma.out
  ...

After runs complete, analyze with:
  /rubato-bgw-gw-conv-analyze calcs:conv_sigma_{param}/val_{v1},conv_sigma_{param}/val_{v2},... vbm:ik={ik},n={n} cbm:ik={ik},n={n} sweep:{param}
```

## Validation

- All `screened_coulomb_cutoff` values must be ≤ parent `epsilon_cutoff`. Warn and skip any values that violate this.
- All `number_bands` values must be ≤ parent epsilon `number_bands`. Warn and skip any values that violate this.
- At least 2 sweep values are required for a meaningful convergence test.

## Rules

- **Sweep only one parameter at a time.** Do not mix cutoff and band sweeps in one call.
- **Use VBM + CBM k-points only** in the kpoints block for convergence runs (much faster than full k-grid).
- **The epsmat is shared** — sigma.inp files must point to the same epsmat location.
- **Never sweep parameters that violate constraints.** Check and warn before creating files.
- **Report the exact run commands and the analyze command** after creating the structure.
- If `vbm`/`cbm` are not given, ask before creating any files.
