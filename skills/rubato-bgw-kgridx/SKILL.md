---
name: rubato-bgw-kgridx
user-invokable: true
description: Generate kgrid.inp from an XSF structure file for BerkeleyGW kgrid.x
argument-hint: "<xsf_file> kgrid:nk1,nk2,nk3 [kshift:dk1,dk2,dk3] [qshift:dq1,dq2,dq3] [fft_grid:nr1,nr2,nr3] [calc_id:cNNN]"
---

Generate `kgrid.inp` for the BerkeleyGW `kgrid.x` utility, which produces symmetry-reduced k-point lists for Quantum ESPRESSO `K_POINTS crystal` cards.

## Usage

```
rubato:bgw-kgridx <xsf_file> kgrid:nk1,nk2,nk3 [kshift:dk1,dk2,dk3] [qshift:dq1,dq2,dq3] [fft_grid:nr1,nr2,nr3] [calc_id:cNNN]
```

- `<xsf_file>` — **Required.** Path to XSF structure file (CRYSTAL format with PRIMVEC and PRIMCOORD blocks).
- `kgrid:nk1,nk2,nk3` — **Required.** Monkhorst-Pack k-grid dimensions (e.g., `kgrid:6,6,1`).
- `kshift:dk1,dk2,dk3` — Grid offset per direction: 0.0 = unshifted, 0.5 = half-shifted (default `0.0,0.0,0.0`).
- `qshift:dq1,dq2,dq3` — Small q-shift for WFNq in Epsilon (default `0.0,0.0,0.0`). Typical: `0.0,0.0,0.001`.
- `fft_grid:nr1,nr2,nr3` — FFT grid size for symmetry commensurate check (default `0,0,0` to skip).
- `calc_id:cNNN` — Save `kgrid.inp` to `calc_db/{calc_id}/input/`. If omitted, save to current directory.

## Execution

### Step 1: Parse arguments and run the script

Parse the user arguments and call the Python script:

```bash
python {skill_dir}/bgw_kgridx.py '<json>'
```

where `<json>` is:
```json
{
  "xsf_path": "<xsf_file>",
  "kgrid": [nk1, nk2, nk3],
  "kshift": [dk1, dk2, dk3],
  "qshift": [dq1, dq2, dq3],
  "fft_grid": [nr1, nr2, nr3]
}
```

If the script returns `status: "error"`, show the error message to the user and stop.

### Step 2: Show and save

1. Show the complete `kgrid.inp` to the user in a code block.
2. Show the species legend (species ID → element symbol mapping) so the user can verify correctness.
3. Ask for confirmation or modifications.
4. Save to `calc_db/{calc_id}/input/kgrid.inp` if `calc_id` is given, or `./kgrid.inp` otherwise.

## kgrid.inp Format Reference

```
nk1 nk2 nk3              ! k-grid dimensions
dk1 dk2 dk3              ! grid offset (0.0 unshifted, 0.5 half-shifted)
dq1 dq2 dq3              ! q-shift for WFNq (0.0 = none)
a1x a1y a1z              ! lattice vector 1 (Cartesian, Angstrom)
a2x a2y a2z              ! lattice vector 2
a3x a3y a3z              ! lattice vector 3
n                         ! number of atoms
s1 x1 y1 z1              ! species ID and Cartesian position
...
nr1 nr2 nr3              ! FFT grid (0 0 0 to skip check)
.false.                   ! time-reversal symmetry (always false for BerkeleyGW)
```

## Validation

- `kgrid` values must all be positive integers. Die with error if any are ≤ 0.
- `kshift` values must be 0.0 or 0.5. Warn if other values are given.
- XSF file must contain both PRIMVEC and PRIMCOORD blocks. Die with error if missing.

## Rules

- **`kgrid` (nk1, nk2, nk3) is always required.** If the user does not provide it, ask.
- **Always set time-reversal symmetry to `.false.`** for BerkeleyGW k-point generation.
- **Lattice vectors and atomic positions are in Angstrom**, as read from the XSF file. This is fine — kgrid.x accepts arbitrary consistent units.
- **Species IDs are 1-indexed integers**, assigned in order of first appearance in the XSF file.
- **Show the complete kgrid.inp before saving.** Never write without user confirmation.
- **When saving to a calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/kgrid.inp`.
- **For 2D systems** (slab/monolayer), the out-of-plane k-grid dimension should typically be 1 (e.g., `kgrid:6,6,1`). Warn if nk3 > 1 and the c-axis lattice vector is much larger than a and b.
