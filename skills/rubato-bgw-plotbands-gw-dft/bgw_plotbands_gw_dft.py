#!/usr/bin/env python3
"""Plot DFT vs GW band structure overlay.

Reads DFT bands from QE pw.x XML and GW bands from BerkeleyGW bandstructure.dat.
Valence band count is read from inteqp.inp (number_val_bands_fine).

Dependencies: numpy, matplotlib  (no qwt required)

Usage:
    python bgw_plotbands_gw_dft.py --dft bands.xml --gw bandstructure.dat --inteqp inteqp.inp
    python bgw_plotbands_gw_dft.py --dft bands.xml --gw bandstructure.dat --nv 14
    python bgw_plotbands_gw_dft.py --dft bands.xml --gw bandstructure.dat --inteqp inteqp.inp \
        --labels "G A X G M R G Z" --erange -2 6 --out my_bands.png
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Physical constants
_HA_TO_EV = 27.211396132
_BOHR_TO_ANG = 0.529177210903

mpl.use("Agg")
mpl.rcParams["font.size"] = 12.0
mpl.rcParams["legend.frameon"] = False
mpl.rcParams["axes.labelweight"] = "bold"

_LABEL_MAP = {
    "G": "\u0393", "GM": "\u0393", "GAMMA": "\u0393",
    "A": "A", "B": "B", "C": "C", "D": "D",
    "H": "H", "K": "K", "L": "L", "M": "M",
    "R": "R", "S": "S", "T": "T", "U": "U",
    "V": "V", "W": "W", "X": "X", "Y": "Y", "Z": "Z",
}


# ---------------------------------------------------------------------------
# inteqp.inp parser
# ---------------------------------------------------------------------------

def read_nv_from_inteqp(inteqp_path):
    """Read number_val_bands_fine from inteqp.inp."""
    nv = None
    with open(inteqp_path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            parts = stripped.split()
            if len(parts) >= 2 and parts[0] == "number_val_bands_fine":
                nv = int(parts[1])
                break
    if nv is None:
        raise ValueError(
            f"number_val_bands_fine not found in {inteqp_path}"
        )
    return nv


# ---------------------------------------------------------------------------
# QE XML parser
# ---------------------------------------------------------------------------

def read_dft_bands(pw_xml):
    """Read band structure from QE pw.x XML.

    Returns
    -------
    kpath  : ndarray (nk,)       cumulative k-distance in Ang^-1
    enk    : ndarray (nspin, nbnd, nk) eigenvalues in eV (absolute)
    ef     : float               Fermi energy in eV
    """
    root = ET.parse(pw_xml).getroot()
    out = root.find("output")
    bs = out.find("band_structure")

    lsda = bs.find("lsda").text.strip() == "true"
    spinorbit = bs.find("spinorbit").text.strip() == "true"
    noncolin = bs.find("noncolin").text.strip() == "true"
    nspin = 4 if (spinorbit or noncolin) else (2 if lsda else 1)

    kpoints, enk_list = [], []
    for ks in root.iter("ks_energies"):
        kpoints.append(np.fromstring(ks.find("k_point").text, sep=" "))
        enk_list.append(np.fromstring(ks.find("eigenvalues").text, sep=" "))

    kpoints = np.array(kpoints)  # (nk, 3) crystal coords
    enk_raw = np.array(enk_list)  # (nk, nbnd_raw)
    nk = len(kpoints)

    if nspin == 2:
        nbnd_up = int(bs.find("nbnd_up").text)
        enk_raw = enk_raw.reshape(nk, 2, nbnd_up).transpose(1, 0, 2)
    else:
        enk_raw = enk_raw[np.newaxis, :, :]  # (1, nk, nbnd)

    # (nspin, nk, nbnd) -> (nspin, nbnd, nk)
    enk = enk_raw.transpose(0, 2, 1) * _HA_TO_EV

    # Fermi energy
    ef_node = bs.find("fermi_energy")
    if ef_node is None:
        ef_node = bs.find("highestOccupiedLevel")
    if ef_node is None:
        raise RuntimeError("Fermi energy not found in XML")
    ef = float(ef_node.text) * _HA_TO_EV

    # Reciprocal lattice -> k-path distance
    cell_node = out.find("atomic_structure").find("cell")
    avec = np.array([
        np.fromstring(cell_node.find("a1").text, sep=" "),
        np.fromstring(cell_node.find("a2").text, sep=" "),
        np.fromstring(cell_node.find("a3").text, sep=" "),
    ])  # in Bohr
    bvec = 2 * np.pi * np.linalg.inv(avec).T

    kcart = kpoints @ bvec  # Bohr^-1
    dk = np.linalg.norm(np.diff(kcart, axis=0), axis=1) / _BOHR_TO_ANG
    kpath = np.concatenate([[0.0], np.cumsum(dk)])

    return kpath, enk, ef


# ---------------------------------------------------------------------------
# BerkeleyGW bandstructure.dat parser
# ---------------------------------------------------------------------------

def read_gw_bands(dat_path):
    """Read GW bands from BerkeleyGW inteqp bandstructure.dat.

    Returns
    -------
    kpoints : ndarray (nk, 3)     Cartesian k-coords
    elda    : ndarray (nbnd, nk)  DFT (mean-field) energies in eV
    eqp     : ndarray (nbnd, nk)  GW quasiparticle energies in eV
    band_indices : ndarray (nbnd,) original band indices (1-based)
    """
    data = np.loadtxt(dat_path)
    # columns: spin | band | kx | ky | kz | E_mf | E_qp | dE
    band_indices = np.unique(data[:, 1])
    nbnd = len(band_indices)

    first_band_mask = data[:, 1] == band_indices[0]
    kpoints = data[first_band_mask][:, 2:5]
    nk = len(kpoints)

    elda = data[:, 5].reshape((nbnd, nk))
    eqp = data[:, 6].reshape((nbnd, nk))

    return kpoints, elda, eqp, band_indices


# ---------------------------------------------------------------------------
# Label helpers
# ---------------------------------------------------------------------------

def parse_labels(label_str):
    return [_LABEL_MAP.get(t.upper(), t) for t in label_str.split()]


def get_hsym_tick_x(kpath, n_labels):
    """Evenly-spaced high-sym positions (standard QE crystal_b)."""
    if n_labels < 2:
        return [kpath[0]]
    idx = np.round(np.linspace(0, len(kpath) - 1, n_labels)).astype(int)
    return kpath[idx].tolist()


# ---------------------------------------------------------------------------
# Main plotting
# ---------------------------------------------------------------------------

def plot_gw_dft(
    dft_xml,
    gw_dat,
    nv,
    labels=None,
    erange=(-2, 6),
    out=None,
    title=None,
    sort_bands=True,
    dft_label="DFT",
    gw_label="GW",
):
    """Plot DFT vs GW band structure overlay."""

    # --- Read DFT ---
    kpath, enk, ef = read_dft_bands(dft_xml)
    nspin, nb_dft, nk_dft = enk.shape
    ispin = 0

    # --- Read GW ---
    kpoints_gw, elda, eqp, band_indices = read_gw_bands(gw_dat)
    nb_gw, nk_gw = eqp.shape

    # --- Align GW to VBM = 0 ---
    eqp_aligned = eqp - np.max(eqp[nv - 1])
    elda_aligned = elda - np.max(elda[nv - 1])

    # --- Scale GW k-path to match DFT k-path ---
    dk_gw = np.linalg.norm(np.diff(kpoints_gw, axis=0), axis=1)
    dk_gw = np.insert(dk_gw, 0, 0)
    x_gw = np.cumsum(dk_gw)
    x_gw_scaled = x_gw * (kpath[-1] / x_gw[-1])

    # --- Sort bands at each k-point (optional) ---
    if sort_bands:
        for col in range(nk_gw):
            sorted_idx = np.argsort(eqp_aligned[:, col])
            eqp_aligned[:, col] = eqp_aligned[sorted_idx, col]

    # --- DFT: align to Fermi ---
    enk_plot = enk[ispin] - ef  # (nb_dft, nk_dft)

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(6, 4))

    # DFT bands
    for ib in range(nb_dft):
        ax.plot(kpath, enk_plot[ib, :], ls="--", color="red", lw=1, alpha=0.5)

    # GW bands
    for ib in range(nb_gw):
        ax.plot(x_gw_scaled, eqp_aligned[ib], color="blue", ls="-", lw=1.5)

    # Legend
    legend_elements = [
        Line2D([0], [0], color="red", ls="--", lw=1.5, alpha=0.5, label=dft_label),
        Line2D([0], [0], color="blue", ls="-", lw=2.0, label=gw_label),
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper right",
        fontsize=10,
        frameon=True,
        fancybox=False,
        edgecolor="grey",
        framealpha=0.9,
    )

    # High-sym labels
    if labels is not None:
        tick_x = get_hsym_tick_x(kpath, len(labels))
        ax.set_xticks(tick_x)
        ax.set_xticklabels(labels, fontsize=12)
        ax.grid(True, axis="x", color="grey", ls="--", lw=0.5)

    ax.axhline(0, color="grey", ls=":")
    ax.set_ylabel("Energy (eV)")
    ax.set_ylim(erange[0], erange[1])
    ax.set_xlim(kpath[0], kpath[-1])
    ax.tick_params(axis="both", which="major", labelsize=12)

    if title:
        ax.set_title(title, fontsize=13, fontweight="bold")

    fig.tight_layout()

    # --- Output ---
    if out is None:
        stem = os.path.splitext(os.path.basename(gw_dat))[0]
        out = f"{stem}_gw_dft_bands.png"

    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # --- Band gap ---
    vbm_gw = np.max(eqp_aligned[nv - 1])
    cbm_gw = np.min(eqp_aligned[nv])
    gap_gw = cbm_gw - vbm_gw

    vbm_dft = np.max(enk_plot[nv - 1 + int(band_indices[0]) - 1, :]) if nb_dft > nv else None
    cbm_dft = np.min(enk_plot[nv + int(band_indices[0]) - 1, :]) if nb_dft > nv else None
    gap_dft = (cbm_dft - vbm_dft) if (vbm_dft is not None and cbm_dft is not None) else None

    print(f"Saved: {out}")
    print(f"GW band gap:  {gap_gw:.3f} eV  (VBM={vbm_gw:.3f}, CBM={cbm_gw:.3f})")
    if gap_dft is not None:
        print(f"DFT band gap: {gap_dft:.3f} eV  (VBM={vbm_dft:.3f}, CBM={cbm_dft:.3f})")

    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Plot DFT vs GW band structure overlay"
    )
    parser.add_argument("--dft", required=True, help="QE pw.x XML file")
    parser.add_argument("--gw", required=True, help="BerkeleyGW bandstructure.dat")

    nv_group = parser.add_mutually_exclusive_group(required=True)
    nv_group.add_argument(
        "--inteqp", type=str, default=None,
        help="inteqp.inp file (reads number_val_bands_fine for nv)",
    )
    nv_group.add_argument(
        "--nv", type=int, default=None,
        help="Number of valence bands in GW data (overrides --inteqp)",
    )

    parser.add_argument(
        "--labels", type=str, default=None,
        help='High-sym k-point labels, space-separated (e.g. "G A X G M R G Z")',
    )
    parser.add_argument(
        "--erange", type=float, nargs=2, default=[-2, 6],
        metavar=("EMIN", "EMAX"),
        help="Energy window in eV (default: -2 6)",
    )
    parser.add_argument("--out", type=str, default=None, help="Output PNG filename")
    parser.add_argument("--title", type=str, default=None, help="Plot title")
    parser.add_argument(
        "--no-sort-bands", dest="sort_bands", action="store_false",
        help="Disable band sorting at each k-point",
    )
    parser.add_argument(
        "--dft-label", type=str, default="DFT", help='DFT legend label (default: "DFT")'
    )
    parser.add_argument(
        "--gw-label", type=str, default="GW", help='GW legend label (default: "GW")'
    )

    args = parser.parse_args()

    # Resolve nv
    if args.nv is not None:
        nv = args.nv
    else:
        nv = read_nv_from_inteqp(args.inteqp)
        print(f"Read nv={nv} from {args.inteqp} (number_val_bands_fine)")

    labels = parse_labels(args.labels) if args.labels else None

    plot_gw_dft(
        dft_xml=args.dft,
        gw_dat=args.gw,
        nv=nv,
        labels=labels,
        erange=tuple(args.erange),
        out=args.out,
        title=args.title,
        sort_bands=args.sort_bands,
        dft_label=args.dft_label,
        gw_label=args.gw_label,
    )


if __name__ == "__main__":
    main()
