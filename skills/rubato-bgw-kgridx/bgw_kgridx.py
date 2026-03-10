#!/usr/bin/env python3
"""Parse an XSF file and generate kgrid.inp for BerkeleyGW kgrid.x.

Usage:
    python bgw_kgridx.py '<json>'

Input JSON keys:
    xsf_path   (str)  — Path to XSF structure file (required).
    kgrid      (list)  — [nk1, nk2, nk3] k-grid dimensions (required).
    kshift     (list)  — [dk1, dk2, dk3] grid offset (default [0.0, 0.0, 0.0]).
    qshift     (list)  — [dq1, dq2, dq3] q-shift for WFNq (default [0.0, 0.0, 0.0]).
    fft_grid   (list)  — [nr1, nr2, nr3] FFT grid size (default [0, 0, 0] to skip check).

Output JSON keys:
    status     (str)  — "ok" or "error".
    kgrid_inp  (str)  — Complete kgrid.inp file content (only when status == "ok").
    message    (str)  — Error description (only when status == "error").
"""

import json
import sys


def _ok(payload: dict) -> str:
    return json.dumps({"status": "ok", **payload}, indent=2)


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message}, indent=2)


def parse_xsf(path: str) -> dict:
    """Parse XSF file and return lattice vectors and atomic positions.

    Returns dict with keys:
        lattice: [[a1x,a1y,a1z], [a2x,a2y,a2z], [a3x,a3y,a3z]]
        atoms: [{"symbol": str, "x": float, "y": float, "z": float}, ...]
    """
    with open(path, "r") as f:
        lines = f.readlines()

    lattice = []
    atoms = []
    natoms = 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line == "PRIMVEC":
            for j in range(1, 4):
                parts = lines[i + j].split()
                lattice.append([float(x) for x in parts[:3]])
            i += 4
            continue

        if line == "PRIMCOORD":
            parts = lines[i + 1].split()
            natoms = int(parts[0])
            for j in range(2, 2 + natoms):
                parts = lines[i + j].split()
                symbol = parts[0]
                coords = [float(x) for x in parts[1:4]]
                atoms.append({
                    "symbol": symbol,
                    "x": coords[0],
                    "y": coords[1],
                    "z": coords[2],
                })
            i += 2 + natoms
            continue

        i += 1

    if len(lattice) != 3:
        raise ValueError(f"Expected 3 lattice vectors in PRIMVEC, found {len(lattice)}")
    if len(atoms) == 0:
        raise ValueError("No atoms found in PRIMCOORD block")

    return {"lattice": lattice, "atoms": atoms}


def build_kgrid_inp(
    lattice: list,
    atoms: list,
    kgrid: list,
    kshift: list,
    qshift: list,
    fft_grid: list,
) -> str:
    """Build kgrid.inp content string."""
    lines = []

    # Line 1: k-grid dimensions
    lines.append(f"{kgrid[0]} {kgrid[1]} {kgrid[2]}")
    # Line 2: k-grid offset
    lines.append(f"{kshift[0]:.1f} {kshift[1]:.1f} {kshift[2]:.1f}")
    # Line 3: q-shift
    lines.append(f"{qshift[0]} {qshift[1]} {qshift[2]}")

    # Lines 4-6: lattice vectors
    for vec in lattice:
        lines.append(f"  {vec[0]:.12f}  {vec[1]:.12f}  {vec[2]:.12f}")

    # Line 7: number of atoms
    lines.append(str(len(atoms)))

    # Map symbols to species IDs (1-indexed, ordered by first appearance)
    seen = []
    for atom in atoms:
        if atom["symbol"] not in seen:
            seen.append(atom["symbol"])
    species_map = {s: i + 1 for i, s in enumerate(seen)}

    # Lines 8..7+n: species and Cartesian positions
    for atom in atoms:
        sid = species_map[atom["symbol"]]
        lines.append(f"  {sid}  {atom['x']:.12f}  {atom['y']:.12f}  {atom['z']:.12f}")

    # FFT grid
    lines.append(f"{fft_grid[0]} {fft_grid[1]} {fft_grid[2]}")
    # Time-reversal symmetry — always false for BerkeleyGW
    lines.append(".false.")

    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print(_error("Usage: python bgw_kgridx.py '<json>'"))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(_error(f"Invalid JSON input: {exc}"))
        sys.exit(1)

    xsf_path = args.get("xsf_path")
    if not xsf_path:
        print(_error("'xsf_path' is required"))
        sys.exit(1)

    kgrid = args.get("kgrid")
    if not kgrid or len(kgrid) != 3:
        print(_error("'kgrid' must be a list of 3 integers [nk1, nk2, nk3]"))
        sys.exit(1)

    kshift = args.get("kshift", [0.0, 0.0, 0.0])
    qshift = args.get("qshift", [0.0, 0.0, 0.0])
    fft_grid = args.get("fft_grid", [0, 0, 0])

    try:
        parsed = parse_xsf(xsf_path)
    except Exception as exc:
        print(_error(f"Failed to parse XSF file: {exc}"))
        sys.exit(1)

    content = build_kgrid_inp(
        lattice=parsed["lattice"],
        atoms=parsed["atoms"],
        kgrid=kgrid,
        kshift=kshift,
        qshift=qshift,
        fft_grid=fft_grid,
    )

    # Build species legend for display
    seen = []
    for atom in parsed["atoms"]:
        if atom["symbol"] not in seen:
            seen.append(atom["symbol"])
    species_legend = {i + 1: s for i, s in enumerate(seen)}

    print(_ok({
        "kgrid_inp": content,
        "species_legend": species_legend,
        "natoms": len(parsed["atoms"]),
    }))


if __name__ == "__main__":
    main()
