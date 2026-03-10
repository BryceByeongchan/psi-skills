#!/usr/bin/env python3
"""Parse structure files and generate QE input data.

Accepts JSON input:
    python qe_input_gen.py '{"structure_file": "Si.cif", "mode": "full"}'
    python qe_input_gen.py '{"structure_file": "Si.cif", "mode": "qgrid", "qppra": 500}'

Outputs JSON to stdout with structural cards, k-points, and/or q-grid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(payload: dict) -> str:
    return json.dumps({"status": "ok", **payload}, indent=2)


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message}, indent=2)


# ---------------------------------------------------------------------------
# Structure loading
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".cif", ".xsf"}


def load_structure(filepath: str):
    """Load structure from CIF or XSF file using pymatgen."""
    from pymatgen.core import Structure

    ext = Path(filepath).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported format '{ext}'. Use one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    return Structure.from_file(filepath)


# ---------------------------------------------------------------------------
# Card rendering
# ---------------------------------------------------------------------------

def render_atomic_species(structure, pp_template: str = "{Element}.upf") -> str:
    """Render ATOMIC_SPECIES card."""
    from pymatgen.core import Element as PmgElement

    elements = sorted({site.specie.symbol for site in structure})
    lines = ["ATOMIC_SPECIES"]
    for elem in elements:
        mass = float(PmgElement(elem).atomic_mass)
        pp_file = pp_template.replace("{Element}", elem)
        lines.append(f"  {elem:<4s} {mass:10.4f}  {pp_file}")
    return "\n".join(lines)


def render_atomic_positions(structure) -> str:
    """Render ATOMIC_POSITIONS in crystal (fractional) coordinates."""
    lines = ["ATOMIC_POSITIONS crystal"]
    for site in structure:
        elem = site.specie.symbol
        x, y, z = site.frac_coords
        lines.append(f"  {elem:<4s} {x:16.12f} {y:16.12f} {z:16.12f}")
    return "\n".join(lines)


def render_cell_parameters(structure) -> str:
    """Render CELL_PARAMETERS in angstrom."""
    lines = ["CELL_PARAMETERS angstrom"]
    for vec in structure.lattice.matrix:
        lines.append(f"  {vec[0]:16.12f} {vec[1]:16.12f} {vec[2]:16.12f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# K-points
# ---------------------------------------------------------------------------

def auto_kgrid(structure, kppra: int = 1000) -> tuple[int, int, int]:
    """Calculate Monkhorst-Pack grid using KPPRA approach.

    KPPRA = k-points per reciprocal atom. The grid is distributed
    proportionally to reciprocal lattice vector lengths.
    """
    import numpy as np

    natoms = len(structure)
    if natoms == 0:
        raise ValueError("Structure has no atoms; cannot calculate k-grid.")

    rec_lengths = np.array(structure.lattice.reciprocal_lattice.abc)
    if rec_lengths.min() <= 0:
        raise ValueError(
            f"Degenerate reciprocal lattice vector detected: {rec_lengths}. "
            "Cannot auto-calculate k-grid."
        )

    target_nk = max(1, kppra // natoms)
    ratio = rec_lengths / rec_lengths.min()
    scale = (target_nk / np.prod(ratio)) ** (1.0 / 3.0)
    grid = tuple(max(1, round(r * scale)) for r in ratio)
    return grid


def auto_qgrid(structure, qppra: int = 500) -> tuple[int, int, int]:
    """Calculate phonon q-point grid using QPPRA approach.

    Same algorithm as auto_kgrid but with a coarser default density
    (QPPRA = 500 vs KPPRA = 1000).
    """
    return auto_kgrid(structure, kppra=qppra)


def render_kpoints_automatic(grid: tuple, shift: tuple = (0, 0, 0)) -> str:
    """Render K_POINTS automatic card."""
    lines = ["K_POINTS automatic"]
    lines.append(f"  {grid[0]} {grid[1]} {grid[2]}  {shift[0]} {shift[1]} {shift[2]}")
    return "\n".join(lines)


def get_bands_kpath(structure, density: int = 20) -> tuple[str, list[str]]:
    """Generate high-symmetry k-path for band structure calculation.

    Uses Setyawan-Curtarolo convention via pymatgen.
    density: k-point density (points per inverse angstrom in reciprocal space).
    Returns (kpoints_card_text, path_description as list of segment strings).
    """
    from pymatgen.symmetry.kpath import KPathSetyawanCurtarolo
    import numpy as np

    kpath_obj = KPathSetyawanCurtarolo(structure)
    kpath = kpath_obj.kpath
    kpts = kpath["kpoints"]
    rec_lattice = kpath_obj.rec_lattice

    points = []
    segment_labels = []
    for segment in kpath["path"]:
        seg_display = []
        for i, label in enumerate(segment):
            coords = kpts[label]
            display_label = label.replace("\\Gamma", "G")
            seg_display.append(display_label)

            if i < len(segment) - 1:
                next_coords = kpts[segment[i + 1]]
                start_cart = rec_lattice.get_cartesian_coords(coords)
                end_cart = rec_lattice.get_cartesian_coords(next_coords)
                dist = float(np.linalg.norm(end_cart - start_cart))
                n = max(2, round(dist * density))
                points.append((coords, n, display_label))
            else:
                points.append((coords, 0, display_label))
        segment_labels.append("→".join(seg_display))

    lines = ["K_POINTS crystal_b", f"  {len(points)}"]
    for coords, n, label in points:
        x, y, z = coords
        lines.append(f"  {x:12.8f} {y:12.8f} {z:12.8f}  {n:4d}  ! {label}")

    return "\n".join(lines), segment_labels


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _structure_info(structure) -> dict:
    """Extract basic structure info as a plain dict."""
    lattice = structure.lattice
    elements = sorted({site.specie.symbol for site in structure})
    return {
        "formula": structure.composition.reduced_formula,
        "elements": elements,
        "nat": len(structure),
        "ntyp": len(elements),
        "lattice": {
            "a": round(lattice.a, 6),
            "b": round(lattice.b, 6),
            "c": round(lattice.c, 6),
            "alpha": round(lattice.alpha, 4),
            "beta": round(lattice.beta, 4),
            "gamma": round(lattice.gamma, 4),
        },
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(_error("Usage: python qe_input_gen.py '<json>'"))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(_error(f"Invalid JSON: {exc}"))
        sys.exit(1)

    structure_file = args.get("structure_file", "").strip()
    if not structure_file:
        print(_error("Missing required field: structure_file"))
        sys.exit(1)

    if not Path(structure_file).exists():
        print(_error(f"Structure file not found: {structure_file}"))
        sys.exit(1)

    VALID_MODES = {"full", "structure", "kpoints_auto", "kpoints_path", "qgrid"}
    VALID_KPOINTS_MODES = {"automatic", "crystal_b"}

    mode = args.get("mode", "full")
    if mode not in VALID_MODES:
        print(_error(f"Invalid mode '{mode}'. Choose from: {', '.join(sorted(VALID_MODES))}"))
        sys.exit(1)

    kpoints_mode = args.get("kpoints_mode", "automatic")
    if kpoints_mode not in VALID_KPOINTS_MODES:
        print(_error(
            f"Invalid kpoints_mode '{kpoints_mode}'. "
            f"Choose from: {', '.join(sorted(VALID_KPOINTS_MODES))}"
        ))
        sys.exit(1)

    pp_template = args.get("pp_template", "{Element}.upf")
    try:
        kppra = int(args.get("kppra", 1000))
        kpath_density = int(args.get("kpath_density", 20))
    except (ValueError, TypeError) as exc:
        print(_error(f"Invalid numeric parameter: {exc}"))
        sys.exit(1)

    try:
        structure = load_structure(structure_file)
    except Exception as exc:
        print(_error(f"Failed to load structure: {exc}"))
        sys.exit(1)

    result = _structure_info(structure)
    cards = {}
    warnings = []

    # --- Q-grid for ph.x ---
    if mode == "qgrid":
        try:
            qppra = int(args.get("qppra", 500))
        except (ValueError, TypeError) as exc:
            print(_error(f"Invalid qppra value: {exc}"))
            sys.exit(1)
        qgrid = auto_qgrid(structure, qppra=qppra)
        result["qgrid"] = list(qgrid)
        if any(q == 1 for q in qgrid):
            warnings.append(
                f"Q-grid has dimension 1 in some direction ({qgrid}). "
                "This is expected for slabs/molecules but verify for bulk."
            )
        result["warnings"] = warnings
        print(_ok(result))
        return

    # --- Structural cards ---
    if mode in ("structure", "full"):
        cards["atomic_species"] = render_atomic_species(structure, pp_template)
        cards["atomic_positions"] = render_atomic_positions(structure)
        cards["cell_parameters"] = render_cell_parameters(structure)

    # --- K-points ---
    need_kpoints = mode in ("kpoints_auto", "kpoints_path", "full")
    if need_kpoints and kpoints_mode == "automatic":
        grid = auto_kgrid(structure, kppra=kppra)
        kshift_raw = args.get("kshift", [0, 0, 0])
        if len(kshift_raw) != 3 or not all(v in (0, 1) for v in kshift_raw):
            print(_error("kshift must be a list of exactly 3 values, each 0 or 1"))
            sys.exit(1)
        shift = tuple(kshift_raw)
        cards["kpoints"] = render_kpoints_automatic(grid, shift)
        result["kpoints_grid"] = list(grid)

        if any(g == 1 for g in grid):
            warnings.append(
                f"K-grid has dimension 1 in some direction ({grid}). "
                "This is expected for slabs/molecules but verify for bulk."
            )

    elif need_kpoints and kpoints_mode == "crystal_b":
        try:
            kpoints_text, labels = get_bands_kpath(structure, density=kpath_density)
            cards["kpoints"] = kpoints_text
            result["kpath_labels"] = labels
        except Exception as exc:
            warnings.append(f"Failed to generate k-path: {exc}")

    result["cards"] = cards
    result["warnings"] = warnings
    print(_ok(result))


if __name__ == "__main__":
    main()
