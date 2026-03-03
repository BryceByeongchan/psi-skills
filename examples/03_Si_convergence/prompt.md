# Example 3: Si Bulk — Convergence Study + Electronic Structure

## Project Goal

Systematic convergence study for bulk silicon: plane-wave cutoff energy and
k-point mesh convergence, followed by a production electronic structure
workflow. Demonstrates how psi tracks parameter sweeps and convergence analysis.

## HPC Environment

- **Computer**: stampede3 (TACC)
- **Code**: VASP
- Same environment as Example 2.

## Calculation Chain

```
c001 (ecut 300 eV)  ──┐
c002 (ecut 400 eV)  ──┤
c003 (ecut 500 eV)  ──├─ r001 (convergence report)
c004 (ecut 600 eV)  ──┤
c005 (ecut 700 eV)  ──┘
c006 (kpt 4x4x4)   ──┐
c007 (kpt 6x6x6)   ──├─ r001 (convergence report, updated)
c008 (kpt 8x8x8)   ──┤
c009 (kpt 10x10x10) ─┤
c010 (kpt 12x12x12) ─┘
c011 (relax, converged params)
  └─ c012 (scf)
       ├─ c013 (bands)
       └─ c014 (dos)
             └─ r002 (electronic structure report)
```

## Prompts

### Step 1: Initialize

```
psi:init
```

```
psi:add-computer stampede3 hpc hostname:stampede3.tacc.utexas.edu user:ywchoi92 scheduler:slurm work_dir:$WORK/calculations queues:normal,development modules:intel/24.0,impi/21.11
```

### Step 2: Ecut convergence series

```
psi:new-calc Si ecut convergence ENCUT=300eV VASP tags:Si,convergence,ecut computer:stampede3
```

```
psi:new-calc Si ecut convergence ENCUT=400eV VASP tags:Si,convergence,ecut computer:stampede3
```

```
psi:new-calc Si ecut convergence ENCUT=500eV VASP tags:Si,convergence,ecut computer:stampede3
```

```
psi:new-calc Si ecut convergence ENCUT=600eV VASP tags:Si,convergence,ecut computer:stampede3
```

```
psi:new-calc Si ecut convergence ENCUT=700eV VASP tags:Si,convergence,ecut computer:stampede3
```

### Step 3: Mark ecut series complete with energies

```
psi:update-calc c001 status=completed key_results.total_energy=-10.8234 key_results.encut=300
```

```
psi:update-calc c002 status=completed key_results.total_energy=-10.9312 key_results.encut=400
```

```
psi:update-calc c003 status=completed key_results.total_energy=-10.9387 key_results.encut=500
```

```
psi:update-calc c004 status=completed key_results.total_energy=-10.9391 key_results.encut=600
```

```
psi:update-calc c005 status=completed key_results.total_energy=-10.9392 key_results.encut=700
```

### Step 4: K-point convergence series (using converged ecut=500)

```
psi:new-calc Si kpoint convergence 4x4x4 ENCUT=500eV VASP tags:Si,convergence,kpoints computer:stampede3
```

```
psi:new-calc Si kpoint convergence 6x6x6 ENCUT=500eV VASP tags:Si,convergence,kpoints computer:stampede3
```

```
psi:new-calc Si kpoint convergence 8x8x8 ENCUT=500eV VASP tags:Si,convergence,kpoints computer:stampede3
```

```
psi:new-calc Si kpoint convergence 10x10x10 ENCUT=500eV VASP tags:Si,convergence,kpoints computer:stampede3
```

```
psi:new-calc Si kpoint convergence 12x12x12 ENCUT=500eV VASP tags:Si,convergence,kpoints computer:stampede3
```

### Step 5: Mark kpoint series complete

```
psi:update-calc c006 status=completed key_results.total_energy=-10.8901 key_results.kpoints=4x4x4
```

```
psi:update-calc c007 status=completed key_results.total_energy=-10.9287 key_results.kpoints=6x6x6
```

```
psi:update-calc c008 status=completed key_results.total_energy=-10.9385 key_results.kpoints=8x8x8
```

```
psi:update-calc c009 status=completed key_results.total_energy=-10.9388 key_results.kpoints=10x10x10
```

```
psi:update-calc c010 status=completed key_results.total_energy=-10.9387 key_results.kpoints=12x12x12
```

### Step 6: Convergence report

```
psi:new-report Si convergence study: ecut and k-points calcs:c001,c002,c003,c004,c005,c006,c007,c008,c009,c010 tags:Si,convergence,analysis
```

### Step 7: Production workflow with converged parameters

```
psi:new-calc Si relaxation with converged parameters ENCUT=500eV 8x8x8 VASP tags:Si,relaxation,production computer:stampede3
```

```
psi:update-calc c011 status=completed key_results.total_energy=-10.9385 key_results.a_lat=5.431 key_results.n_ionic_steps=5
```

```
psi:new-calc Si SCF on relaxed structure VASP parents:c011 tags:Si,scf,production computer:stampede3
```

```
psi:update-calc c012 status=completed key_results.total_energy=-10.9386 key_results.bandgap=0.61
```

```
psi:new-calc Si band structure L-G-X-W-K-G VASP parents:c012 tags:Si,bands,production computer:stampede3
```

```
psi:new-calc Si total and projected DOS VASP parents:c012 tags:Si,dos,production computer:stampede3
```

```
psi:update-calc c013 status=completed key_results.bandgap=0.61 key_results.gap_type=indirect key_results.vbm=G key_results.cbm=X_0.85
```

```
psi:update-calc c014 status=completed key_results.dos_at_fermi=0.0
```

### Step 8: Electronic structure report

```
psi:new-report Si electronic structure with PBE calcs:c012,c013,c014 tags:Si,electronic-structure,PBE
```

### Step 9: Final checks

```
psi:status
```

```
psi:graph
```

```
psi:graph c012
```

## Expected Final State

- 14 calculations (c001-c014), all completed
- 2 reports (r001 convergence, r002 electronic structure)
- Convergence calcs are independent (no parent-child), linked only via report
- Production chain: c011 → c012 → {c013, c014}
