#!/usr/bin/env python3
"""
Parse sigma.out from BerkeleyGW and extract Eqp1 for VBM and CBM.

Usage:
    python bgw_conv_analyze.py '<json>'

JSON input fields:
    sigma_out : str   - path to sigma.out file
    vbm_ik    : int   - VBM k-point index (1-based, matches "ik =" in sigma.out)
    vbm_n     : int   - VBM band index (1-based)
    cbm_ik    : int   - CBM k-point index (1-based)
    cbm_n     : int   - CBM band index (1-based)

JSON output:
    vbm_eqp1  : float | None
    cbm_eqp1  : float | None
    gap       : float | None
    found_vbm : bool
    found_cbm : bool
    error     : str | None
"""

import sys
import json
import re


def parse_sigma_out(path, vbm_ik, vbm_n, cbm_ik, cbm_n):
    """
    Parse sigma.out and extract Eqp1 for the requested (ik, n) pairs.

    sigma.out format (from write_result.f90):

        k =  0.000000  0.000000  0.000000 ik =   1 spin =  1

             n       Emf        Eo       Vxc         X       Cor      Eqp0      Eqp1       Znk
             8     -3.000    -3.000    -5.123    -7.234     1.234    -1.123    -1.045     0.756

    Header format: a6 + 8*(a9)   => columns: n Emf Eo Vxc X Cor Eqp0 Eqp1 Znk
    Data format:   i6 + 10*f9.3  => Eqp1 is column index 8 (0-based: 7)
    """
    # column positions: n(0) Emf(1) Eo(2) Vxc(3) X(4) Cor(5) Eqp0(6) Eqp1(7) Znk(8)
    EQPC1_COL = 7  # 0-based index

    results = {}  # key: (ik, n) -> eqp1

    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except OSError as exc:
        return None, None, str(exc)

    current_ik = None
    in_diag_block = False

    for line in lines:
        # Detect k-point header: "       k =  0.000  0.000  0.000 ik =   1 spin =  1"
        m = re.search(r"ik\s*=\s*(\d+)", line)
        if m and "k =" in line:
            current_ik = int(m.group(1))
            in_diag_block = False
            continue

        # Detect header line (contains "Eqp1")
        if "Eqp1" in line:
            in_diag_block = True
            continue

        # End of diag block: blank line or line with non-numeric start
        if in_diag_block and current_ik is not None:
            stripped = line.strip()
            if not stripped:
                in_diag_block = False
                continue

            # Skip lines that look like off-diagonal entries ("real" or "imag" keyword)
            if "real" in stripped or "imag" in stripped:
                continue

            # Try to parse a data line: first token is band index (integer)
            parts = stripped.split()
            if not parts:
                in_diag_block = False
                continue

            try:
                band_n = int(parts[0])
            except ValueError:
                in_diag_block = False
                continue

            # Extract Eqp1 (column index 7 in 0-based, or 8th token)
            if len(parts) > EQPC1_COL:
                try:
                    eqp1 = float(parts[EQPC1_COL])
                    results[(current_ik, band_n)] = eqp1
                except ValueError:
                    pass

    vbm_eqp1 = results.get((vbm_ik, vbm_n))
    cbm_eqp1 = results.get((cbm_ik, cbm_n))

    found_vbm = vbm_eqp1 is not None
    found_cbm = cbm_eqp1 is not None

    gap = None
    if found_vbm and found_cbm:
        gap = cbm_eqp1 - vbm_eqp1

    errors = []
    if not found_vbm:
        errors.append(f"VBM (ik={vbm_ik}, n={vbm_n}) not found in {path}")
    if not found_cbm:
        errors.append(f"CBM (ik={cbm_ik}, n={cbm_n}) not found in {path}")

    error_msg = "; ".join(errors) if errors else None

    return {
        "vbm_eqp1": vbm_eqp1,
        "cbm_eqp1": cbm_eqp1,
        "gap": gap,
        "found_vbm": found_vbm,
        "found_cbm": found_cbm,
        "error": error_msg,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: bgw_conv_analyze.py '<json>'"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON input: {exc}"}))
        sys.exit(1)

    sigma_out = args.get("sigma_out")
    vbm_ik = args.get("vbm_ik")
    vbm_n = args.get("vbm_n")
    cbm_ik = args.get("cbm_ik")
    cbm_n = args.get("cbm_n")

    missing = [k for k in ("sigma_out", "vbm_ik", "vbm_n", "cbm_ik", "cbm_n") if args.get(k) is None]
    if missing:
        print(json.dumps({"error": f"Missing required fields: {missing}"}))
        sys.exit(1)

    result = parse_sigma_out(sigma_out, int(vbm_ik), int(vbm_n), int(cbm_ik), int(cbm_n))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
