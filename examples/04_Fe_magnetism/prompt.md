# Example 4: BCC Fe — Magnetic Properties

## Project Goal

Study magnetic properties of BCC iron: structural relaxation with spin
polarization, magnetic moment analysis, spin-resolved DOS, and magnetic
anisotropy energy (MAE) via SOC calculations along different axes. Demonstrates
tracking spin-polarized and SOC calculations with VASP.

## HPC Environment

- **Computer**: stampede3 (TACC)
- **Code**: VASP (vasp_std for collinear, vasp_ncl for SOC)

## Calculation Chain

```
c001 (relax, spin-polarized)
  └─ c002 (scf, spin-polarized, fine k-mesh)
       ├─ c003 (spin-resolved DOS)
       ├─ c004 (SOC, M//[001])
       ├─ c005 (SOC, M//[110])
       └─ c006 (SOC, M//[111])
            └─ r001 (magnetic properties report)
```

## Prompts

### Step 1: Initialize

```
psi:init
```

```
psi:add-computer stampede3 hpc hostname:stampede3.tacc.utexas.edu user:ywchoi92 scheduler:slurm work_dir:$WORK/calculations queues:normal,development modules:intel/24.0,impi/21.11
```

### Step 2: Spin-polarized relaxation

```
psi:new-calc BCC Fe spin-polarized relaxation VASP tags:Fe,magnetic,relaxation,spin-polarized computer:stampede3
```

```
psi:update-calc c001 status=completed key_results.total_energy=-8.2365 key_results.a_lat=2.831 key_results.magnetic_moment=2.17 key_results.n_ionic_steps=4
```

### Step 3: Fine-mesh SCF

```
psi:new-calc BCC Fe SCF with fine 16x16x16 k-mesh VASP parents:c001 tags:Fe,scf,spin-polarized computer:stampede3
```

```
psi:update-calc c002 status=completed key_results.total_energy=-8.2371 key_results.magnetic_moment=2.19 key_results.kpoints=16x16x16
```

### Step 4: Spin-resolved DOS

```
psi:new-calc BCC Fe spin-resolved DOS VASP parents:c002 tags:Fe,dos,spin-polarized computer:stampede3
```

```
psi:update-calc c003 status=completed key_results.exchange_splitting_d=1.85 key_results.dos_majority_at_fermi=1.23 key_results.dos_minority_at_fermi=3.45 notes="Exchange splitting of d-band center in eV"
```

### Step 5: SOC calculations for MAE (three magnetization directions)

```
psi:new-calc BCC Fe SOC M//[001] for MAE VASP parents:c002 tags:Fe,SOC,MAE,001 computer:stampede3
```

```
psi:new-calc BCC Fe SOC M//[110] for MAE VASP parents:c002 tags:Fe,SOC,MAE,110 computer:stampede3
```

```
psi:new-calc BCC Fe SOC M//[111] for MAE VASP parents:c002 tags:Fe,SOC,MAE,111 computer:stampede3
```

```
psi:update-calc c004 status=completed key_results.total_energy=-8.23892 key_results.saxis=0,0,1 key_results.orbital_moment=0.045
```

```
psi:update-calc c005 status=completed key_results.total_energy=-8.23888 key_results.saxis=1,1,0 key_results.orbital_moment=0.048
```

```
psi:update-calc c006 status=completed key_results.total_energy=-8.23885 key_results.saxis=1,1,1 key_results.orbital_moment=0.047
```

### Step 6: Magnetic properties report

```
psi:new-report BCC Fe magnetic properties and MAE calcs:c002,c003,c004,c005,c006 tags:Fe,magnetism,MAE,analysis
```

### Step 7: Status and graph

```
psi:status
```

```
psi:graph
```

## Expected Final State

- 6 calculations (c001-c006), all completed
- 1 report (r001), draft
- DAG: c001 → c002 → {c003, c004, c005, c006}
- MAE = E[001] - E[111] ≈ -0.07 meV/atom (easy axis [001])
- r001 references c002-c006
