---
name: rubato-qe-input-generator
user-invokable: true
description: Generate Quantum Espresso input files (pw.x, pp.x, dos.x, bands.x, projwfc.x, ph.x, pw2wannier90.x)
argument-hint: "<structure_file> <calc_type> [options...] OR <executable> [options...] [parent:cNNN]"
---

Generate Quantum Espresso input files. Supports pw.x (from structure files) and post-processing codes (pp.x, dos.x, bands.x, projwfc.x, ph.x, pw2wannier90.x).

## Prerequisites

Requires `pymatgen` (for pw.x and ph.x modes only):

```bash
pip install pymatgen
```

## Usage

### pw.x mode (structure → input)

```
rubato:qe-input-generator <structure_file> <calc_type> [calc_id:cNNN] [ecutwfc:NN] [kgrid:Nx,Ny,Nz] [pp_dir:path] [pp_template:pattern] [options...]
```

### Post-processing mode

```
rubato:qe-input-generator <executable> [parent:cNNN] [calc_id:cNNN] [options...]
```

**You** determine the mode from the first argument:
- If it ends with `.cif` or `.xsf` → **pw.x mode**
- If it matches an executable name → **post-processing mode**

### Common arguments

- `calc_id:cNNN` — Save to `calc_db/{calc_id}/input/{filename}`. If not specified, save to current directory.
- `parent:cNNN` — Parent calculation. Used to extract `outdir` and `prefix` from the parent's input file.
- Additional QE parameters as `namelist.key=value` (e.g., `system.occupations=smearing`, `electrons.mixing_beta=0.4`).

### pw.x arguments

- **structure_file**: Path to a `.cif` or `.xsf` file. May be absolute or relative.
- **calc_type**: One of `scf`, `relax`, `vc-relax`, `nscf`, `bands`, `md`, `vc-md`.
- `ecutwfc:NN` — Wavefunction cutoff in Ry. If not specified, **you** suggest an appropriate value (see Cutoff Guidance below).
- `kgrid:Nx,Ny,Nz` — Override k-point grid. If not specified, the script auto-calculates from cell size.
- `pp_dir:path` — Pseudopotential directory. Default: `./pseudo`.
- `pp_template:pattern` — PP filename template. Default: `{Element}.upf`.

### Post-processing arguments

- **executable**: One of `pp`, `dos`, `bands_post`, `projwfc`, `ph`, `pw2wannier90`.
- Executable-specific options are described in the relevant sections below.

## Execution

### Step 1: Get structural data from Python

Build a JSON object and run:

```bash
python {skill_dir}/qe_input_gen.py '<json>'
```

JSON fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `structure_file` | string | (required) | Path to CIF or XSF file |
| `mode` | string | `"full"` | `"structure"`, `"kpoints_auto"`, `"kpoints_path"`, `"full"` |
| `kpoints_mode` | string | `"automatic"` | `"automatic"` for MP grid, `"crystal_b"` for bands k-path |
| `kppra` | int | `1000` | K-points per reciprocal atom for auto grid |
| `kpath_density` | int | `20` | K-point density for bands k-path (points per inverse angstrom) |
| `pp_template` | string | `"{Element}.upf"` | PP filename pattern |
| `kshift` | list | `[0,0,0]` | K-grid shift |

For **scf, relax, vc-relax, nscf, md, vc-md**: use `kpoints_mode: "automatic"`.
For **nscf**: use `kppra: 4000` (denser grid than scf).
For **bands**: use `kpoints_mode: "crystal_b"`.

The script returns JSON with `cards` (atomic_species, atomic_positions, cell_parameters, kpoints) and structure info (formula, elements, nat, ntyp, lattice).

### Step 2: Construct namelists

Using the script output and the calc_type, **you** construct the QE namelists. Use `ibrav = 0` always (CELL_PARAMETERS card is provided by the script).

#### scf

```
&CONTROL
  calculation = 'scf'
  restart_mode = 'from_scratch'
  pseudo_dir = '{pp_dir}'
  outdir = './out'
  prefix = '{formula}'
  tprnfor = .TRUE.
  tstress = .TRUE.
/
&SYSTEM
  ibrav = 0
  nat = {nat}
  ntyp = {ntyp}
  ecutwfc = {ecutwfc}
  ecutrho = {ecutrho}
/
&ELECTRONS
  conv_thr = 1.0d-8
  mixing_beta = 0.7
/
```

#### scf (spin-polarized variant)

When `nspin = 2` is confirmed, add to &SYSTEM:

```
  nspin = 2
  starting_magnetization(1) = {mag_1}
  starting_magnetization(2) = {mag_2}
```

For magnetic metals, also add `occupations = 'smearing'`, `smearing = 'cold'`, `degauss = 0.02`.

#### scf (metallic variant)

When the material is metallic (confirmed by user), add to &SYSTEM:

```
  occupations = 'smearing'
  smearing = 'cold'
  degauss = 0.02
```

#### relax

Same as scf, plus add `forc_conv_thr = 1.0d-4` to &CONTROL, and:

```
&IONS
  ion_dynamics = 'bfgs'
/
```

#### vc-relax

Same as relax, plus:

```
&CELL
  cell_dynamics = 'bfgs'
  press_conv_thr = 0.5
/
```

#### nscf

```
&CONTROL
  calculation = 'nscf'
  pseudo_dir = '{pp_dir}'
  outdir = './out'
  prefix = '{prefix}'
/
&SYSTEM
  ibrav = 0
  nat = {nat}
  ntyp = {ntyp}
  ecutwfc = {ecutwfc}
  ecutrho = {ecutrho}
  nosym = .TRUE.
  noinv = .TRUE.
  nbnd = {nbnd}
/
&ELECTRONS
  conv_thr = 1.0d-8
/
```

- `nbnd`: Set to ~20% more than the number of occupied bands. Calculate as: `ceil(total_valence_electrons / 2) * 1.2`.
- `outdir` and `prefix` **must match the parent SCF**.

#### bands

Same namelists as nscf, but `calculation = 'bands'` and K_POINTS uses `crystal_b` mode.


### Step 3: Assemble pw.in

Combine the namelists (from Step 2) with the cards (from Step 1) in this order:

```
{namelists}

{ATOMIC_SPECIES}

{ATOMIC_POSITIONS}

{K_POINTS}

{CELL_PARAMETERS}
```

### Step 4: Show and save

1. Show the complete `pw.in` to the user.
2. Ask for confirmation or modifications.
3. Save to `calc_db/{calc_id}/input/pw.in` if calc_id is given, or `./pw.in` otherwise.

## Cutoff Guidance

PseudoDojo ONCVPSP (norm-conserving) pseudopotentials. **ecutrho = 4 * ecutwfc** always.

Suggest ecutwfc based on the heaviest/hardest element in the structure:

- **Light elements** (H, C, N, O, F): 80–90 Ry
- **2nd/3rd row** (Si, P, S, Cl, Al): 60–80 Ry
- **Transition metals** (Ti, Fe, Co, Ni, Cu, Zn, Mo, W): 70–90 Ry
- **Heavy elements** (Sn, Pb, Bi): 60–80 Ry
- **Rare earths**: 70–90 Ry

When in doubt, use **80 Ry** as a safe default. Always mention the chosen value and let the user confirm.
If you are not sure with this, please **do the convergence test with respect to ecutwfc** and report the results to the user.

## Material Physics Analysis

Before constructing namelists, **you** analyze the material composition and proactively suggest physics-appropriate settings. Present your analysis to the user and ask for confirmation before adding.

### Magnetic Materials

If the structure contains magnetic elements, suggest spin-polarized calculation:

**3d magnetic elements**: Mn, Fe, Co, Ni, Cr, V (common magnetic ordering)
**4f/5f elements**: Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, U, Np, Pu (often magnetic)

When magnetic elements are detected:
1. Suggest `nspin = 2` for collinear magnetism.
2. Suggest `starting_magnetization(i)` for each magnetic species:
   - Fe: ~2.0, Co: ~1.5, Ni: ~0.5, Mn: ~4.0, Cr: ~3.0 (as magnetic moment, |value| >= 1)
   - Or use fractional form (0 to 1): Fe: ~0.5, Co: ~0.4, Ni: ~0.2, Mn: ~0.8, Cr: ~0.6
   - Rare earths: ask user for expected magnetic configuration.
3. For antiferromagnets: warn that distinct atomic species are needed for up/down sublattices.
4. For noncollinear/SOC systems, suggest `noncolin = .TRUE.` instead of `nspin = 2`.

### Metallic Systems

If the material is likely metallic, suggest smearing:

**Indicators**: elemental metals (Li, Na, Al, Cu, Ag, Au, Pt, Pd, etc.), alloys, intermetallics, the user mentions "metal".

When metallic character is expected:
1. `occupations = 'smearing'`
2. `smearing = 'cold'` (Marzari-Vanderbilt, recommended for metals)
3. `degauss = 0.02` Ry (typical starting point, 0.01–0.03 Ry range)

**For insulators/semiconductors**: `occupations = 'fixed'` (default), no smearing needed.
**When uncertain**: ask the user.

### DFT+U (Hubbard Corrections)

For transition metal oxides, rare earth compounds, or strongly correlated systems, suggest DFT+U:

**Common scenarios**: FeO, NiO, CoO, MnO, TiO2, Fe2O3, CeO2 — materials with localized d or f electrons.

When suggesting DFT+U:
1. Use the HUBBARD card (QE >= 6.8 syntax):
   ```
   HUBBARD ortho-atomic
     U {Element}-3d {U_value}
   ```
2. Typical U values as starting points (must be verified):
   - Fe-3d: 4.0–5.0 eV, Co-3d: 3.0–4.0 eV, Ni-3d: 5.0–6.0 eV
   - Mn-3d: 3.5–5.0 eV, Ti-3d: 2.0–4.0 eV, Cu-3d: 5.0–8.0 eV
   - Ce-4f: 4.0–5.5 eV, U-5f: 3.0–4.5 eV
3. Always warn: "U values are approximate. Verify with linear-response calculation or literature."

### Spin-Orbit Coupling (SOC)

For systems where relativistic effects are significant:

**Heavy elements (Z > 50)**: Pb, Bi, Te, Sb, Sn, W, Pt, Au, Hg, Tl, etc.
**Topological materials**: band inversion, topological insulator, Weyl semimetal.
**5d transition metals**: W, Re, Os, Ir, Pt, Au.

When suggesting SOC:
1. `noncolin = .TRUE.` (sets nspin=4 internally)
2. `lspinorb = .TRUE.`
3. Requires fully relativistic pseudopotentials (`_rel` or FR PPs).
4. Warn: SOC calculations are ~4x more expensive.

### Van der Waals Corrections

For weakly bonded systems where dispersion interactions are important:

**Layered materials**: graphite, h-BN, MoS2, WS2, WSe2, MoSe2, black phosphorus, and other 2D materials in bulk or few-layer form.
**Molecular crystals**: organic crystals, adsorption on surfaces, molecules on substrates.
**Weakly bonded heterostructures**: van der Waals heterostructures, intercalated compounds.

When suggesting vdW correction:
1. `vdw_corr = 'grimme-d3'` (DFT-D3, most widely used and reliable)
2. Alternatives: `'grimme-d2'` (simpler, faster), `'mbd'` (many-body dispersion, more accurate for large systems), `'tkatchenko-scheffler'` (TS-vdW)
3. DFT-D3 requires no additional parameters beyond `vdw_corr`.
4. For layered bulk materials, vdW is critical for correct interlayer distances and energetics.

### Slab and Surface Calculations

When the structure has vacuum (slab, molecule, or 1D chain):

**Indicators**: large c-axis with vacuum gap, user mentions "surface", "slab", "adsorption", "work function".

When suggesting slab-specific settings:
1. `assume_isolated = 'esm'` or `'2D'` — for 2D slab geometries, eliminates spurious interaction between periodic images. `'2D'` (Truncated Coulomb) is simpler and recommended for symmetric slabs.
2. For asymmetric slabs (different top/bottom surfaces): add dipole correction with `tefield = .TRUE.` and `dipfield = .TRUE.` in &CONTROL, plus `edir = 3`, `emaxpos = 0.95`, `eopreg = 0.1`, `eamp = 0.0` in &SYSTEM (for vacuum along z).
3. K-grid should have 1 in the vacuum direction (the script's auto-grid warning already handles this).
4. Ensure sufficient vacuum (typically >= 15 Å) to avoid image interaction.

### Charged Systems and Defects

For charged defect calculations or systems with non-neutral total charge:

**Indicators**: user mentions "defect", "vacancy", "charged", "dopant", "+1", "-1".

When suggesting charged system settings:
1. `tot_charge = {charge}` — total charge of the system in units of e (positive = electron removed).
2. For charged cells, a compensating background is added automatically.
3. Warn: charged slab calculations require special care (use ESM barrier method or compensating counter-charge).
4. For defect calculations in supercells, suggest sufficiently large supercell to minimize defect-defect interaction.

### Hybrid Functionals

Do **not** auto-suggest. Only add when user explicitly requests HSE06, PBE0, etc.:
1. `input_dft = 'HSE'` (or `'PBE0'`, `'B3LYP'`)
2. Warn about very high computational cost.

### Analysis Workflow

After parsing the structure (Step 1), before constructing namelists (Step 2):
1. List the elements found.
2. Classify: metal / semiconductor / insulator / magnetic / strongly correlated / heavy-element / layered / slab.
3. Present physics suggestions from the categories above.
4. For any suggested flag not in the templates above, look up its official documentation using the validator's lookup mode:
   ```bash
   python {validator_skill_dir}/qe_input_validator.py '{"mode": "lookup", "ref_file": "{validator_skill_dir}/refs/pw.json", "variables": ["nspin", "vdw_corr", ...]}'
   ```
   where `{validator_skill_dir}` is the `rubato-qe-input-validator` skill directory (sibling of this skill's directory). Use the returned `info`, `options`, and `default` to present accurate suggestions.
5. Ask the user to confirm or reject each suggestion.
6. Proceed to namelist construction with confirmed settings.

## Rules

- **Always use `ibrav = 0`.** The script provides CELL_PARAMETERS explicitly.
- **ecutrho = 4 * ecutwfc** for norm-conserving pseudopotentials (PseudoDojo ONCVPSP). Never use a different ratio unless the user explicitly requests it.
- **For bands/nscf, always ask about the parent SCF calculation.** The `outdir` and `prefix` must match.
- **For bands, show the k-path labels** (e.g., G→M→K→G→A→L→H→A) and ask the user to confirm before saving.
- **Show the complete pw.in before saving.** Never write without user confirmation.
- **PP file naming defaults to `{Element}.upf`.** This matches PseudoDojo standard distribution.
- **Spin-polarized, DFT+U, SOC** — proactively suggest when Material Physics Analysis indicates they are appropriate. Always ask the user for confirmation before adding. Hybrid functionals are added only on explicit user request.
- **If the structure has vacuum** (slab, chain or molecule), warn that the k-grid may have dimension 1 in the vacuum direction and confirm this is intentional.
- **When saving to a calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/pw.in`.
- **For post-processing codes, extract parent's outdir/prefix** by reading the parent's pw.in (or equivalent). If `parent:cNNN` is given, look in `calc_db/{parent_dir}/input/pw.in`.
- **Post-processing codes do NOT call the Python script.** You construct their namelists directly.

---

## Post-Processing Codes

For all post-processing codes, `prefix` and `outdir` **must match the parent pw.x calculation**. If `parent:cNNN` is given, read the parent's input file to extract these values.

### pp.x

Generates input for charge density, potential, and other post-processing plots.

```
&INPUTPP
  prefix = '{prefix}'
  outdir = './out'
  filplot = '{prefix}.pp'
  plot_num = {plot_num}
/
&PLOT
  iflag = {iflag}
  output_format = {output_format}
  fileout = '{fileout}'
/
```

Common `plot_num` values:
- `0` — Electron charge density
- `1` — Total potential (V_bare + V_H + V_xc)
- `6` — Spin polarization (rho_up - rho_down)
- `7` — |psi|^2 for selected states
- `9` — Charge density minus superposition of atomic densities
- `10` — Integrated LDOS (from emin to emax)
- `17` — All-electron valence charge density (PAW only)
- `22` — Kinetic energy density

Common `iflag` values for &PLOT:
- `0` — 1D plot (spherical average)
- `1` — 1D plot along a line
- `2` — 2D plot on a plane
- `3` — 3D plot (full grid)
- `4` — 2D polar plot

Common `output_format` values for &PLOT:
- `0` — gnuplot format (1D/2D)
- `3` — XCrySDen XSF format (2D/3D)
- `5` — Gaussian cube format (3D)
- `6` — gnuplot format (2D polar)
- `7` — gnuplot format (1D spherical average)

Ask the user what quantity they want to plot and select the appropriate `plot_num`. Show the options above. Save as `pp.in`.

### dos.x

Generates input for density of states calculation.

```
&DOS
  prefix = '{prefix}'
  outdir = './out'
  fildos = '{prefix}.dos'
  Emin = {Emin}
  Emax = {Emax}
  DeltaE = 0.01
  degauss = {degauss}
/
```

- `Emin`/`Emax`: Energy window in eV. If not specified, use band extrema.
- `DeltaE`: Energy grid spacing in eV. Default 0.01 eV.
- `degauss`: Gaussian broadening in Ry (not eV). If not specified, uses the value from the pw.x calculation.

Save as `dos.in`.

### bands.x (bands_post)

Generates input for band structure post-processing (reordering, symmetry analysis).

```
&BANDS
  prefix = '{prefix}'
  outdir = './out'
  filband = '{prefix}.bands'
  lsym = .true.
/
```

- `lsym`: If `.true.`, bands are classified by irreducible representations.
- Parent must be a `calculation = 'bands'` pw.x run.

Save as `bands.in`.

### projwfc.x

Generates input for projected density of states (PDOS).

```
&PROJWFC
  prefix = '{prefix}'
  outdir = './out'
  filpdos = '{prefix}'
  Emin = {Emin}
  Emax = {Emax}
  DeltaE = 0.01
  degauss = {degauss}
/
```

- Similar energy window parameters as dos.x.
- Parent should be an NSCF calculation with enough bands.

Save as `projwfc.in`.

### ph.x

Generates input for phonon calculations.

```
&INPUTPH
  prefix = '{prefix}'
  outdir = './out'
  fildyn = '{prefix}.dyn'
  tr2_ph = 1.0d-14
  ldisp = .true.
  nq1 = {nq1}
  nq2 = {nq2}
  nq3 = {nq3}
/
```

For phonon dispersion (`ldisp = .true.`), a q-point grid is needed. Use the Python script to auto-calculate:

```bash
python {skill_dir}/qe_input_gen.py '{"structure_file": "<path>", "mode": "qgrid", "qppra": 500}'
```

The script returns `qgrid` as `[nq1, nq2, nq3]`. Default QPPRA is 500 (q-grid is typically coarser than k-grid).

For single q-point calculation, omit `ldisp` and add q-point coordinates after the namelist:

```
{title_line}

&INPUTPH
  prefix = '{prefix}'
  outdir = './out'
  fildyn = '{prefix}.dyn'
  tr2_ph = 1.0d-14
/
0.0 0.0 0.0
```

Note: ph.x input has a title line before the namelist.

Common ph.x options:
- `epsil = .true.` — Compute dielectric constant and effective charges (Gamma only)
- `trans = .true.` — Compute phonons (default)
- `electron_phonon = 'interpolated'` — Compute electron-phonon coefficients
- `recover = .true.` — Restart from interrupted calculation

Save as `ph.in`.

### pw2wannier90.x

Generates input for the Wannier90 interface.

```
&INPUTPP
  prefix = '{prefix}'
  outdir = './out'
  seedname = '{seedname}'
  wan_mode = 'standalone'
  write_amn = .true.
  write_mmn = .true.
  write_unk = .false.
/
```

- `seedname`: Must match the Wannier90 calculation seedname. Default: the material formula.
- `write_unk = .true.`: Enable to plot Wannier functions (large files).
- Parent must be an NSCF calculation.

Common options:
- `scdm_proj = .true.` — Use SCDM method for initial projections
- `atom_proj = .true.` — Use pseudo-atomic projections

Save as `pw2wannier90.in`.
