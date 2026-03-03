# Example 1: MoS2 Monolayer — QE + Wannier90

## Project Goal

Calculate band structure and projected density of states for monolayer MoS2
using Quantum ESPRESSO, then construct maximally-localized Wannier functions
using Wannier90.

## HPC Environment

- **Computer**: stampede3 (TACC)
- **Login**: ywchoi92@stampede3.tacc.utexas.edu
- **Scheduler**: slurm
- **QE location**: custom build under `$WORK/software/qe-7.3/bin/`
- **Wannier90 location**: `$WORK/software/wannier90-3.1.0/wannier90.x`
- **Work directory**: `$WORK/calculations`
- **Queues**: normal, development
- **Modules**: `intel/24.0`, `impi/21.11`

## Calculation Chain

```
c001 (relax)
  └─ c002 (scf)
       ├─ c003 (bands)
       ├─ c004 (pdos)
       └─ c005 (nscf for wannier)
            └─ c006 (wannier90)
```

## Prompts

Execute these commands sequentially in a Claude Code session with psi-agent installed.

### Step 1: Initialize project and register computer

```
psi:init
```

When prompted about computing environment, provide:
```
psi:add-computer stampede3 hpc hostname:stampede3.tacc.utexas.edu user:ywchoi92 scheduler:slurm work_dir:$WORK/calculations queues:normal,development modules:intel/24.0,impi/21.11 env_setup:export PATH=$WORK/software/qe-7.3/bin:$WORK/software/wannier90-3.1.0:$PATH
```

### Step 2: Create the relaxation calculation

```
psi:new-calc MoS2 monolayer structural relaxation QE tags:MoS2,2D,relaxation computer:stampede3
```

Expected: Creates c001 with status=planned, code=QE.

### Step 3: After relaxation completes, create SCF calculation

```
psi:update-calc c001 status=completed key_results.total_energy=-45.2831 key_results.a_lat=3.185 key_results.force_max=0.0001
```

```
psi:new-calc MoS2 SCF on relaxed structure QE parents:c001 tags:MoS2,scf computer:stampede3
```

Expected: Creates c002 with parent c001. c001.children should include c002.

### Step 4: Band structure, PDOS, and NSCF calculations (can be created together)

```
psi:new-calc MoS2 band structure along G-M-K-G path QE parents:c002 tags:MoS2,bands computer:stampede3
```

```
psi:new-calc MoS2 projected density of states QE parents:c002 tags:MoS2,pdos computer:stampede3
```

```
psi:new-calc MoS2 NSCF for Wannierization QE parents:c002 tags:MoS2,nscf,wannier computer:stampede3
```

Expected: Creates c003, c004, c005 all with parent c002. c002.children = [c003, c004, c005].

### Step 5: Wannier90 calculation

```
psi:new-calc MoS2 Wannier90 MLWFs for Mo-d and S-p states wannier90 parents:c005 tags:MoS2,wannier,MLWF computer:stampede3
```

Expected: Creates c006 with parent c005. Note code=wannier90.

### Step 6: Mark some calculations as completed and add results

```
psi:update-calc c002 status=completed key_results.total_energy=-45.2831 key_results.n_electrons=26
```

```
psi:update-calc c003 status=completed key_results.bandgap_direct=1.67 key_results.vbm_location=K key_results.cbm_location=K
```

```
psi:update-calc c004 status=completed
```

```
psi:update-calc c005 status=completed key_results.n_kpoints=144
```

```
psi:update-calc c006 status=completed key_results.spread_total=5.231 key_results.n_wannier=11 key_results.disentanglement_converged=true
```

### Step 7: Create a report summarizing the electronic structure

```
psi:new-report MoS2 monolayer electronic structure and Wannier functions calcs:c002,c003,c004,c006 tags:MoS2,electronic-structure,wannier
```

Expected: Creates r001 referencing c002, c003, c004, c006. Each of those calcs should have r001 in their reports list.

### Step 8: Check project status and provenance graph

```
psi:status
```

```
psi:graph
```

```
psi:graph c002
```

## Expected Final State

- 6 calculations (c001-c006), all completed
- 1 report (r001), status=draft
- DAG: c001 → c002 → {c003, c004, c005} → c006 (from c005)
- r001 references c002, c003, c004, c006
- Index files consistent with front matter
