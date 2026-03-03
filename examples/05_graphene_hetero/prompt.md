# Example 5: Graphene/hBN Heterostructure — Interlayer Interaction

## Project Goal

Study a graphene/hexagonal boron nitride (Gr/hBN) van der Waals heterostructure.
Compare PBE (no vdW), DFT-D3, and optB88-vdW functionals for interlayer binding.
Calculate electronic structure with the best functional. Demonstrates multi-
functional comparison and 2D heterostructure workflow.

## HPC Environment

- **Computer**: stampede3 (TACC)
- **Code**: VASP

## Calculation Chain

```
c001 (graphene relax)   ─┐
c002 (hBN relax)        ─┼─ c003 (Gr/hBN relax, PBE)
                          ├─ c004 (Gr/hBN relax, DFT-D3)
                          └─ c005 (Gr/hBN relax, optB88-vdW)
                               └─ c006 (Gr/hBN SCF, optB88-vdW)
                                    ├─ c007 (bands)
                                    ├─ c008 (pdos)
                                    └─ c009 (charge density diff)
                                         └─ r001 (binding + electronic structure)
```

## Prompts

### Step 1: Initialize

```
psi:init
```

```
psi:add-computer stampede3 hpc hostname:stampede3.tacc.utexas.edu user:ywchoi92 scheduler:slurm work_dir:$WORK/calculations queues:normal,development modules:intel/24.0,impi/21.11
```

### Step 2: Isolated layer relaxations

```
psi:new-calc Graphene monolayer relaxation VASP tags:graphene,2D,relaxation computer:stampede3
```

```
psi:new-calc hBN monolayer relaxation VASP tags:hBN,2D,relaxation computer:stampede3
```

```
psi:update-calc c001 status=completed key_results.total_energy=-18.4523 key_results.a_lat=2.468
```

```
psi:update-calc c002 status=completed key_results.total_energy=-17.2341 key_results.a_lat=2.512
```

### Step 3: Functional comparison — three relaxations of the heterostructure

```
psi:new-calc Gr/hBN heterostructure relaxation PBE (no vdW) VASP parents:c001,c002 tags:Gr-hBN,relaxation,PBE,vdW-comparison computer:stampede3
```

```
psi:new-calc Gr/hBN heterostructure relaxation DFT-D3 VASP parents:c001,c002 tags:Gr-hBN,relaxation,DFT-D3,vdW-comparison computer:stampede3
```

```
psi:new-calc Gr/hBN heterostructure relaxation optB88-vdW VASP parents:c001,c002 tags:Gr-hBN,relaxation,optB88-vdW,vdW-comparison computer:stampede3
```

### Step 4: Complete functional comparison calcs

```
psi:update-calc c003 status=completed key_results.total_energy=-35.6801 key_results.interlayer_distance=4.12 key_results.binding_energy=-2.1 notes="PBE: almost no binding, huge interlayer distance. Binding energy in meV/atom."
```

```
psi:update-calc c004 status=completed key_results.total_energy=-35.7234 key_results.interlayer_distance=3.35 key_results.binding_energy=-25.3 notes="DFT-D3: reasonable distance and binding. Binding energy in meV/atom."
```

```
psi:update-calc c005 status=completed key_results.total_energy=-35.7189 key_results.interlayer_distance=3.32 key_results.binding_energy=-23.8 notes="optB88-vdW: similar to D3, slightly different energetics. Binding energy in meV/atom."
```

### Step 5: Production electronic structure with optB88-vdW

```
psi:new-calc Gr/hBN SCF with optB88-vdW fine k-mesh VASP parents:c005 tags:Gr-hBN,scf,optB88-vdW computer:stampede3
```

```
psi:update-calc c006 status=completed key_results.total_energy=-35.7190 key_results.kpoints=15x15x1
```

```
psi:new-calc Gr/hBN band structure G-M-K-G VASP parents:c006 tags:Gr-hBN,bands,optB88-vdW computer:stampede3
```

```
psi:new-calc Gr/hBN projected DOS VASP parents:c006 tags:Gr-hBN,pdos,optB88-vdW computer:stampede3
```

```
psi:new-calc Gr/hBN charge density difference VASP parents:c006 tags:Gr-hBN,charge-density,optB88-vdW computer:stampede3
```

### Step 6: Complete electronic structure calcs

```
psi:update-calc c007 status=completed key_results.dirac_cone_gap=30 key_results.hBN_gap=4.7 notes="Gap opening at Dirac point in meV due to hBN substrate"
```

```
psi:update-calc c008 status=completed notes="PDOS shows clear separation of graphene pi and hBN sigma states"
```

```
psi:update-calc c009 status=completed notes="Charge redistribution mainly at interface, ~0.01 e/A^2 transfer"
```

### Step 7: Comprehensive report

```
psi:new-report Gr/hBN heterostructure: vdW functional comparison and electronic structure calcs:c003,c004,c005,c006,c007,c008,c009 tags:Gr-hBN,vdW,electronic-structure,analysis
```

### Step 8: Status and graph

```
psi:status
```

```
psi:graph
```

```
psi:graph c005
```

## Expected Final State

- 9 calculations (c001-c009), all completed
- 1 report (r001), draft
- Two root nodes: c001 (graphene), c002 (hBN)
- Functional comparison branch: c001,c002 → {c003, c004, c005}
- Production branch from c005: c005 → c006 → {c007, c008, c009}
- r001 references c003-c009 (all heterostructure calcs)
