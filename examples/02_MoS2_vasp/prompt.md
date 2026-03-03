# Example 2: MoS2 Monolayer — VASP

## Project Goal

Same physical system as Example 1 (MoS2 monolayer), but using VASP instead of
Quantum ESPRESSO. Demonstrates a typical VASP DFT workflow: relax → SCF → bands
→ DOS, plus SOC band structure for comparison.

## HPC Environment

- **Computer**: stampede3 (TACC)
- **Login**: ywchoi92@stampede3.tacc.utexas.edu
- **Scheduler**: slurm
- **VASP location**: `$WORK/software/vasp.6.4.3/bin/vasp_std` (and `vasp_ncl` for SOC)
- **Work directory**: `$WORK/calculations`
- **Queues**: normal, development
- **Modules**: `intel/24.0`, `impi/21.11`

## Calculation Chain

```
c001 (relax, PBE)
  └─ c002 (scf, PBE)
       ├─ c003 (bands, PBE)
       ├─ c004 (DOS, PBE)
       └─ c005 (bands+SOC, PBE+SOC)
```

## Prompts

### Step 1: Initialize and register computer

```
psi:init
```

```
psi:add-computer stampede3 hpc hostname:stampede3.tacc.utexas.edu user:ywchoi92 scheduler:slurm work_dir:$WORK/calculations queues:normal,development modules:intel/24.0,impi/21.11 env_setup:export PATH=$WORK/software/vasp.6.4.3/bin:$PATH
```

### Step 2: Relaxation

```
psi:new-calc MoS2 monolayer PBE relaxation VASP tags:MoS2,2D,relaxation,PBE computer:stampede3
```

### Step 3: Update relaxation as completed, create SCF

```
psi:update-calc c001 status=completed key_results.total_energy=-19.4527 key_results.a_lat=3.190 key_results.ediff_reached=true key_results.n_ionic_steps=12
```

```
psi:new-calc MoS2 SCF with fine k-mesh VASP parents:c001 tags:MoS2,scf,PBE computer:stampede3
```

### Step 4: SCF done, create band structure and DOS

```
psi:update-calc c002 status=completed key_results.total_energy=-19.4529 key_results.n_bands=36 key_results.kpoints=12x12x1
```

```
psi:new-calc MoS2 PBE band structure G-M-K-G VASP parents:c002 tags:MoS2,bands,PBE computer:stampede3
```

```
psi:new-calc MoS2 total and projected DOS VASP parents:c002 tags:MoS2,dos,PBE computer:stampede3
```

### Step 5: SOC band structure (uses SCF WAVECAR)

```
psi:new-calc MoS2 band structure with SOC VASP parents:c002 tags:MoS2,bands,SOC,PBE computer:stampede3
```

### Step 6: Mark everything completed

```
psi:update-calc c003 status=completed key_results.bandgap=1.64 key_results.gap_type=direct key_results.vbm=K key_results.cbm=K
```

```
psi:update-calc c004 status=completed key_results.dos_at_fermi=0.0
```

```
psi:update-calc c005 status=completed key_results.soc_splitting_vbm=148 key_results.soc_splitting_cbm=3 notes="SOC splitting in meV at K point"
```

### Step 7: Report comparing PBE and SOC results

```
psi:new-report MoS2 VASP electronic structure: PBE vs SOC calcs:c003,c004,c005 tags:MoS2,electronic-structure,SOC-comparison
```

### Step 8: Status and graph

```
psi:status
```

```
psi:graph
```

## Expected Final State

- 5 calculations (c001-c005), all completed
- 1 report (r001), draft
- DAG: c001 → c002 → {c003, c004, c005}
- r001 references c003, c004, c005
