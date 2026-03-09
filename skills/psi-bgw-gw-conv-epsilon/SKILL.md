---
name: psi-bgw-gw-conv-epsilon
user-invokable: true
description: Set up epsilon+sigma convergence sweep for epsilon_cutoff or epsilon number_bands (re-runs epsilon.x with coarse q-grid)
argument-hint: "sweep:param values:v1,v2,v3 [parent_parabands:cNNN] [calc_id:cNNN] vbm:ik=N,n=M cbm:ik=N,n=M qgrid:Nx,Ny,Nz [options...]"
---

Set up a convergence sweep that re-runs `epsilon.x` for each sweep point (using a coarse q-grid for speed), then runs `sigma.x`. Tests convergence of the dielectric function itself.

Use this for:
- Testing convergence with respect to `epsilon_cutoff` (e.g., 10, 15, 20, 25, 30 Ry).
- Testing convergence with respect to `number_bands` in epsilon (e.g., 500, 1000, 1500, 2000).

This is Step 4 in the recommended GW convergence workflow (optional validation).

## Usage

```
psi:bgw-gw-conv-epsilon sweep:param values:v1,v2,v3 [parent_parabands:cNNN] vbm:ik=N,n=M cbm:ik=N,n=M qgrid:Nx,Ny,Nz [options...]
```

- `sweep:param` — **Required.** Parameter to sweep: `epsilon_cutoff` or `number_bands`.
- `values:v1,v2,...` — **Required.** Comma-separated list of values (e.g., `values:10,15,20,25,30` Ry, or `values:500,1000,1500,2000` bands).
- `parent_parabands:cNNN` — Parent parabands calculation (provides the maximum available bands in WFN_pb).
- `vbm:ik=N,n=M` — VBM k-point index and band index for sigma's kpoints/diag blocks.
- `cbm:ik=N,n=M` — CBM k-point index and band index for sigma's kpoints/diag blocks.
- `qgrid:Nx,Ny,Nz` — Coarse q-grid for epsilon runs (e.g., `qgrid:2,2,1` for a 2D material). **Required.**
- `sigma_cutoff:Ry` — Fixed screened_coulomb_cutoff for all sigma runs (default: = epsilon_cutoff of each point).
- `sigma_bands:N` — Fixed number_bands for all sigma runs (default: = epsilon number_bands of each point).
- `frequency_dependence:N` — 0 = GPP (default for epsilon), 1 = GPP (default for sigma).

## Execution

### Step 1: Gather required information

1. If `vbm` and `cbm` are not specified, ask the user.
2. If `qgrid` is not specified, ask the user for the coarse q-grid.
3. Generate the q-points list from the coarse q-grid (ask user to confirm or provide manually).

### Step 2: Create sweep subdirectory structure

For each sweep value `v`, create:
```
conv_epsilon_{param}/
  val_{v}/
    epsilon.inp
    sigma.inp
```

**epsilon.inp per sweep point (with coarse q-grid):**
```
epsilon_cutoff    {epsilon_cutoff}      # = v if sweeping cutoff, else fixed
number_bands      {number_bands}        # = v if sweeping bands, else fixed

begin qpoints
  {coarse q-points from qgrid}
end
```

**sigma.inp per sweep point:**
```
screened_coulomb_cutoff  {sigma_cutoff}    # = epsilon_cutoff of this point (or user-specified)
bare_coulomb_cutoff      {sigma_cutoff}
number_bands             {sigma_bands}     # = epsilon number_bands or user-specified

frequency_dependence     1

begin kpoints
  {vbm_kpt}
  {cbm_kpt}
end

begin diag
  {vbm_n}
  {cbm_n}
end
```

Key rule: `screened_coulomb_cutoff` in sigma.inp is automatically set equal to `epsilon_cutoff` of that sweep point.

### Step 3: Generate coarse q-points

From `qgrid:Nx,Ny,Nz`, generate the irreducible q-points (or full grid if no symmetry). Ask the user to confirm the q-points list, or let them provide it manually.

For a simple 2×2×1 grid (2D material):
```
begin qpoints
  0.001 0.0 0.0  1  1
  0.5   0.0 0.0  1  0
  0.0   0.5 0.0  1  0
  0.5   0.5 0.0  1  0
end
```
(q→0 as the first point with flag=1 for semiconductor/insulator.)

### Step 4: Report

After creating all files, report:
```
Created convergence sweep: sweep={param}
  conv_epsilon_{param}/val_{v1}/epsilon.inp + sigma.inp
  conv_epsilon_{param}/val_{v2}/epsilon.inp + sigma.inp
  ...

Each point: run epsilon.x first, then sigma.x.
  cd conv_epsilon_{param}/val_{v1}
  epsilon.x < epsilon.inp > epsilon.out
  sigma.x   < sigma.inp   > sigma.out

After runs complete, analyze with:
  /psi-bgw-gw-conv-analyze calcs:conv_epsilon_{param}/val_{v1},... vbm:ik={ik},n={n} cbm:ik={ik},n={n} sweep:{param}
```

## Validation

- All `epsilon_cutoff` values: warn if > 40 Ry.
- All `number_bands` values must be ≤ bands in WFN_pb. If parent_parabands is known, check this.
- `sigma_cutoff` (= epsilon_cutoff per point) satisfies `screened_coulomb_cutoff ≤ epsilon_cutoff`. This is automatically satisfied when they are equal.
- At least 2 sweep values are required.

## Rules

- **`screened_coulomb_cutoff` = `epsilon_cutoff` per point.** Set them equal automatically unless the user explicitly overrides.
- **Use a coarse q-grid** for epsilon runs to keep them fast. Remind the user that coarse q-grid results are only for convergence testing, not production.
- **Use VBM + CBM k-points only** in sigma's kpoints block for all convergence runs.
- **Report the exact run commands** (epsilon.x then sigma.x per directory) after creating the structure.
- If `vbm`/`cbm` or `qgrid` are not given, ask before creating any files.
