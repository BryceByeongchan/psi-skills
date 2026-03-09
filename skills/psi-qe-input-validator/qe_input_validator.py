#!/usr/bin/env python3
"""QE input file validator.

Two modes:
  parse_def:  Parse QE INPUT_*.def → JSON reference
  validate:   Validate QE input against reference

Usage:
  python qe_input_validator.py '{"mode":"parse_def","def_file":"INPUT_PW.def","output_file":"pw.json"}'
  python qe_input_validator.py '{"mode":"validate","input_file":"pw.in","ref_file":"pw.json"}'
"""

from __future__ import annotations

import json
import re
import sys
from difflib import get_close_matches
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(payload: dict) -> str:
    return json.dumps({"status": "ok", **payload}, indent=2)


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message}, indent=2)


def _find_matching_brace(text: str, start: int) -> int:
    """Return index after the matching '}', given *start* is just past '{'."""
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return i


# ---------------------------------------------------------------------------
# DEF file parser  (mode: parse_def)
# ---------------------------------------------------------------------------

def parse_def_file(filepath: str) -> dict:
    """Parse a QE INPUT_*.def file into structured JSON."""
    text = Path(filepath).read_text(encoding="utf-8", errors="replace")

    # Program name from the header line
    m = re.search(r"-program\s+(\S+)", text)
    program = m.group(1) if m else "unknown"

    # Find every  namelist NAME { ... }  block
    namelists: dict[str, dict] = {}
    for m in re.finditer(r"^\s*namelist\s+(\w+)\s*\{", text, re.MULTILINE):
        name = m.group(1)
        block_end = _find_matching_brace(text, m.end())
        block = text[m.end() : block_end - 1]
        namelists[name] = _extract_variables(block)

    return {"program": program, "namelists": namelists}


def _extract_variables(block: str) -> dict:
    """Extract all variable definitions from a namelist block."""
    variables: dict[str, dict] = {}

    # 1. var NAME -type TYPE {  (also handles  var NAME(index) -type TYPE { )
    for m in re.finditer(
        r"(?:^|\n)\s*var\s+(\w+)(?:\([^)]*\))?([^{]*)\{", block
    ):
        var_name = m.group(1).lower()
        flags = m.group(2)
        tm = re.search(r"-type\s+(\w+)", flags)
        if not tm:
            continue
        var_type = tm.group(1).upper()
        body_end = _find_matching_brace(block, m.end())
        body = block[m.end() : body_end - 1]
        info = _parse_var_body(body, var_type)
        info["type"] = _normalize_type(var_type)
        variables[var_name] = info

    # 2. dimension NAME ... -type TYPE {
    for m in re.finditer(
        r"(?:^|\n)\s*dimension\s+(\w+)\b([^{]*)\{", block
    ):
        var_name = m.group(1).lower()
        flags = m.group(2)
        tm = re.search(r"-type\s+(\w+)", flags)
        if not tm:
            continue
        var_type = tm.group(1).upper()
        body_end = _find_matching_brace(block, m.end())
        body = block[m.end() : body_end - 1]
        info = _parse_var_body(body, var_type)
        info["type"] = _normalize_type(var_type)
        info["is_array"] = True
        variables[var_name] = info

    # 3. vargroup -type TYPE { var A  var B ... info { ... } }
    for m in re.finditer(r"(?:^|\n)\s*vargroup([^{]*)\{", block):
        flags = m.group(1)
        tm = re.search(r"-type\s+(\w+)", flags)
        if not tm:
            continue
        group_type = _normalize_type(tm.group(1).upper())
        body_end = _find_matching_brace(block, m.end())
        body = block[m.end() : body_end - 1]
        # Extract group-level info to attach to each variable
        group_info = None
        gim = re.search(r"\binfo\s*\{", body)
        if gim:
            gie = _find_matching_brace(body, gim.end())
            raw_gi = body[gim.end() : gie - 1].strip()
            if raw_gi:
                group_info = _clean_info_text(raw_gi)
        for vm in re.finditer(r"\bvar\s+(\w+)", body):
            vname = vm.group(1).lower()
            entry: dict = {"type": group_type}
            if group_info:
                entry["info"] = group_info
            variables[vname] = entry

    # 4. multidimension NAME ... -type TYPE {
    for m in re.finditer(
        r"(?:^|\n)\s*multidimension\s+(\w+)\b([^{]*)\{", block
    ):
        var_name = m.group(1).lower()
        flags = m.group(2)
        tm = re.search(r"-type\s+(\w+)", flags)
        if not tm:
            continue
        var_type = tm.group(1).upper()
        body_end = _find_matching_brace(block, m.end())
        body = block[m.end() : body_end - 1]
        md_info = _parse_var_body(body, var_type)
        md_info["type"] = _normalize_type(var_type)
        md_info["is_array"] = True
        variables[var_name] = md_info

    # 5. Recurse into choose / when / elsewhen / otherwise blocks
    for m in re.finditer(
        r"(?:^|\n)\s*(?:when|elsewhen|otherwise)\s*[^{]*\{", block
    ):
        body_end = _find_matching_brace(block, m.end())
        inner = block[m.end() : body_end - 1]
        for k, v in _extract_variables(inner).items():
            if k not in variables:
                variables[k] = v

    return variables


def _normalize_type(t: str) -> str:
    if t == "STRING":
        return "CHARACTER"
    return t


_MAX_INFO_LEN = 2000


def _clean_info_text(raw: str) -> str:
    """Clean QE def-file markup from info text."""
    text = raw
    text = re.sub(r"@ref\s+(\w+)", r"\1", text)
    text = re.sub(r"@b\s*\{([^}]*)\}", r"\1", text)
    text = re.sub(r"@b\s+(?!\{)(\S+)", r"\1", text)
    text = re.sub(r"@i\s*\{([^}]*)\}", r"\1", text)
    text = re.sub(r"@tt\s+(\S+)", r"\1", text)
    text = re.sub(r"@br\b", "\n", text)
    lines = text.splitlines()
    cleaned = [" ".join(ln.split()) for ln in lines]
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if len(text) > _MAX_INFO_LEN:
        text = text[:_MAX_INFO_LEN] + " [truncated]"
    return text


def _extract_opt_descriptions(body: str) -> list[tuple[list[str], str]]:
    """Extract (values, description) pairs from opt blocks, handling nested braces."""
    results: list[tuple[list[str], str]] = []
    for m in re.finditer(r"opt\s+-val\s+", body):
        pos = m.end()
        # Parse the value part: 'val' or {'v1','v2'}
        vals: list[str] = []
        if pos < len(body) and body[pos] == "'":
            vm = re.match(r"'([^']*)'", body[pos:])
            if vm:
                vals = [vm.group(1).strip()]
                pos += vm.end()
        elif pos < len(body) and body[pos] == "{":
            brace_end = _find_matching_brace(body, pos + 1)
            val_text = body[pos + 1 : brace_end - 1]
            vals = [v.strip() for v in re.findall(r"'([^']*)'", val_text)]
            pos = brace_end
        if not vals:
            continue
        # Parse the description block: { ... }
        rest = body[pos:].lstrip()
        if rest.startswith("{"):
            desc_start = pos + (len(body[pos:]) - len(rest)) + 1
            desc_end = _find_matching_brace(body, desc_start)
            desc = body[desc_start : desc_end - 1].strip()
            results.append((vals, desc))
        else:
            results.append((vals, ""))
    return results


def _parse_var_body(body: str, var_type: str) -> dict:
    """Extract default, options, and info from a variable body block."""
    result: dict = {}

    # Default value
    dm = re.search(r"\bdefault\s*\{", body)
    if dm:
        de = _find_matching_brace(body, dm.end())
        raw = body[dm.end() : de - 1].strip()
        if raw:
            parsed = _try_parse_default(raw, var_type)
            if parsed is not None:
                result["default"] = parsed

    # Check for options { ... } block (find position first to scope info search)
    opts_m = re.search(r"\boptions\s*\{", body)

    # Top-level info block (only before options block, not inside it)
    search_body = body[:opts_m.start()] if opts_m else body
    im = re.search(r"\binfo\s*\{", search_body)
    if im:
        ie = _find_matching_brace(body, im.end())
        raw_info = body[im.end() : ie - 1].strip()
        if raw_info:
            cleaned = _clean_info_text(raw_info)
            if cleaned:
                result["info"] = cleaned

    # Enumerated options + descriptions
    options: list[str] = []
    opt_descs: list[str] = []
    if opts_m:
        opts_end = _find_matching_brace(body, opts_m.end())
        opts_body = body[opts_m.end() : opts_end - 1]

        # Options-level info (e.g., "Available options are:")
        opts_info_m = re.search(r"\binfo\s*\{", opts_body)
        opts_preamble = ""
        if opts_info_m:
            oi_end = _find_matching_brace(opts_body, opts_info_m.end())
            opts_preamble = opts_body[opts_info_m.end() : oi_end - 1].strip()

        # Per-option values and descriptions
        for vals, desc in _extract_opt_descriptions(opts_body):
            for v in vals:
                options.append(v)
            if desc:
                label = "/".join(f"'{v}'" for v in vals)
                opt_descs.append(f"{label}: {_clean_info_text(desc)}")

        # Build assembled info from options if no top-level info
        if "info" not in result and (opts_preamble or opt_descs):
            parts = []
            if opts_preamble:
                parts.append(_clean_info_text(opts_preamble))
            parts.extend(opt_descs)
            assembled = "\n".join(parts)
            if assembled:
                result["info"] = assembled
    else:
        # Fallback: scan body directly for opt patterns (outside options block)
        for om in re.finditer(r"opt\s+-val\s+'([^']*)'", body):
            options.append(om.group(1).strip())
        for om in re.finditer(r"opt\s+-val\s+\{([^}]*)\}", body):
            for part in re.findall(r"'([^']*)'", om.group(1)):
                options.append(part.strip())

    if options:
        result["options"] = sorted(set(options))

    return result


def _try_parse_default(text: str, var_type: str):
    """Return a Python value if the default is a simple literal, else None."""
    text = text.strip()
    # Skip conditional / descriptive defaults
    if any(kw in text.lower() for kw in ["if ", "value of", "see ", "same as"]):
        return None

    clean = text.strip("'\"")
    vt = var_type.upper()
    if vt == "INTEGER":
        try:
            return int(clean)
        except ValueError:
            return None
    if vt == "REAL":
        try:
            return float(clean.replace("D", "E").replace("d", "e"))
        except ValueError:
            return None
    if vt == "LOGICAL":
        up = clean.upper()
        if ".TRUE." in up or up in ("T", ".T."):
            return True
        if ".FALSE." in up or up in ("F", ".F."):
            return False
        return None
    if vt in ("CHARACTER", "STRING"):
        return clean if clean else None
    return None


# ---------------------------------------------------------------------------
# QE input file parser  (mode: validate)
# ---------------------------------------------------------------------------

def parse_qe_input(filepath: str) -> dict:
    """Parse a Fortran-namelist QE input file.

    Returns {"namelists": {NAME: {var: raw_value, ...}}, "cards": [...]}.
    """
    text = Path(filepath).read_text(encoding="utf-8", errors="replace")

    namelists: dict[str, dict] = {}
    for name, body in _find_namelist_blocks(text):
        namelists[name] = _parse_namelist_body(body)

    cards = _detect_cards(text)
    return {"namelists": namelists, "cards": cards}


def _find_namelist_blocks(text: str) -> list[tuple[str, str]]:
    """Find &NAME … / blocks, correctly handling quoted strings."""
    blocks: list[tuple[str, str]] = []
    i = 0
    while i < len(text):
        m = re.search(r"&(\w+)", text[i:])
        if not m:
            break

        match_pos = i + m.start()
        # Skip if '&' is inside a comment on its line
        line_start = text.rfind("\n", 0, match_pos) + 1
        if _is_in_comment(text[line_start:match_pos]):
            i = match_pos + 1
            continue

        name = m.group(1).upper()
        body_start = i + m.end()

        j = body_start
        in_quote = False
        qchar = ""
        while j < len(text):
            c = text[j]
            if in_quote:
                if c == qchar:
                    in_quote = False
            elif c in ("'", '"'):
                in_quote = True
                qchar = c
            elif c == "!":
                # skip comment to end of line
                while j < len(text) and text[j] != "\n":
                    j += 1
                continue
            elif c == "/":
                blocks.append((name, text[body_start:j]))
                i = j + 1
                break
            j += 1
        else:
            break
    return blocks


def _parse_namelist_body(body: str) -> dict:
    """Parse key = value pairs from a Fortran namelist body."""
    # Remove comments
    cleaned_lines = [_strip_fortran_comment(ln) for ln in body.splitlines()]
    flat = " ".join(cleaned_lines)

    # Mask quoted strings so '=' inside them won't confuse the scanner
    masked = _mask_quoted_strings(flat)

    variables: dict[str, str] = {}
    pattern = re.compile(r"(\w+)(?:\([^)]*\))?\s*=\s*")
    matches = list(pattern.finditer(masked))
    for idx, m in enumerate(matches):
        key = m.group(1).lower()
        val_start = m.end()
        val_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(flat)
        raw = flat[val_start:val_end].strip().rstrip(",").strip()
        variables[key] = raw
    return variables


def _strip_fortran_comment(line: str) -> str:
    in_quote = False
    qchar = ""
    for i, c in enumerate(line):
        if in_quote:
            if c == qchar:
                in_quote = False
        elif c in ("'", '"'):
            in_quote = True
            qchar = c
        elif c == "!":
            return line[:i]
    return line


def _is_in_comment(text_before: str) -> bool:
    """Check if there is an unquoted '!' before the current position."""
    in_quote = False
    qchar = ""
    for c in text_before:
        if in_quote:
            if c == qchar:
                in_quote = False
        elif c in ("'", '"'):
            in_quote = True
            qchar = c
        elif c == "!":
            return True
    return False


def _mask_quoted_strings(text: str) -> str:
    """Replace quoted string contents with spaces, preserving positions."""
    result = list(text)
    in_quote = False
    qchar = ""
    for i, c in enumerate(text):
        if in_quote:
            if c == qchar:
                in_quote = False
            else:
                result[i] = " "
        elif c in ("'", '"'):
            in_quote = True
            qchar = c
    return "".join(result)


_KNOWN_CARDS = {
    "ATOMIC_SPECIES",
    "ATOMIC_POSITIONS",
    "K_POINTS",
    "CELL_PARAMETERS",
    "OCCUPATIONS",
    "CONSTRAINTS",
    "ATOMIC_VELOCITIES",
    "ATOMIC_FORCES",
    "ADDITIONAL_K_POINTS",
    "SOLVENTS",
    "HUBBARD",
}


def _detect_cards(text: str) -> list[str]:
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("!"):
            continue
        word = stripped.split()[0].upper()
        for card in _KNOWN_CARDS:
            if word == card or word.startswith(card + "(") or word.startswith(card + "{"):
                if card not in found:
                    found.append(card)
                break
    return found


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def _lookup_var_info(ref_nls: dict, var_to_nls: dict, varname: str) -> str | None:
    """Look up the info text for a variable across all namelists."""
    for nl in var_to_nls.get(varname, []):
        info = ref_nls[nl].get(varname, {}).get("info")
        if info:
            return info
    return None


def validate_input(input_data: dict, ref_data: dict) -> dict:
    """Compare parsed QE input against a reference and return a report."""
    errors: list[dict] = []
    warnings: list[dict] = []
    variable_info: dict[str, str] = {}

    ref_nls = ref_data.get("namelists", {})
    inp_nls = input_data.get("namelists", {})

    # Build global variable → namelist(s) lookup
    var_to_nls: dict[str, list[str]] = {}
    for nl, nl_vars in ref_nls.items():
        for vname in nl_vars:
            var_to_nls.setdefault(vname, []).append(nl)
    all_ref_vars = set(var_to_nls.keys())

    for nl_name, nl_vars in inp_nls.items():
        # --- check namelist name ---
        if nl_name not in ref_nls:
            close = get_close_matches(nl_name, list(ref_nls.keys()), n=3, cutoff=0.5)
            entry: dict = {
                "type": "unknown_namelist",
                "namelist": nl_name,
                "known": sorted(ref_nls.keys()),
            }
            if close:
                entry["suggestion"] = close
            errors.append(entry)
            continue

        ref_vars = ref_nls[nl_name]

        for var_name, var_value in nl_vars.items():
            vl = var_name.lower()

            # --- check variable exists in this namelist ---
            if vl not in ref_vars:
                if vl in all_ref_vars:
                    entry = {
                        "type": "wrong_namelist",
                        "namelist": nl_name,
                        "variable": var_name,
                        "correct_namelist": var_to_nls[vl],
                    }
                    info = _lookup_var_info(ref_nls, var_to_nls, vl)
                    if info:
                        entry["info"] = info
                    errors.append(entry)
                else:
                    close = get_close_matches(vl, all_ref_vars, n=3, cutoff=0.6)
                    entry = {
                        "type": "unknown_variable",
                        "namelist": nl_name,
                        "variable": var_name,
                    }
                    if close:
                        entry["suggestion"] = close
                    errors.append(entry)
                continue

            ref_info = ref_vars[vl]

            # Collect info for all recognized variables
            info_text = ref_info.get("info")
            if info_text:
                variable_info[vl] = info_text

            # --- type check ---
            expected = ref_info.get("type")
            if expected:
                issue = _check_type(var_value, expected)
                if issue:
                    entry = {
                        "type": "type_mismatch",
                        "namelist": nl_name,
                        "variable": var_name,
                        "expected": expected,
                        "got": var_value,
                        "detail": issue,
                    }
                    if info_text:
                        entry["info"] = info_text
                    warnings.append(entry)

            # --- option check ---
            opts = ref_info.get("options")
            if opts:
                clean_val = var_value.strip().strip("'\"").lower()
                lower_opts = [o.lower() for o in opts]
                if clean_val and clean_val not in lower_opts:
                    close = get_close_matches(clean_val, lower_opts, n=3, cutoff=0.5)
                    entry = {
                        "type": "invalid_option",
                        "namelist": nl_name,
                        "variable": var_name,
                        "value": clean_val,
                        "allowed": opts,
                    }
                    if close:
                        entry["suggestion"] = close
                    if info_text:
                        entry["info"] = info_text
                    errors.append(entry)

    ne = len(errors)
    nw = len(warnings)
    return {
        "executable": ref_data.get("program", "unknown"),
        "namelists_found": sorted(inp_nls.keys()),
        "cards_found": input_data.get("cards", []),
        "errors": errors,
        "warnings": warnings,
        "variable_info": variable_info,
        "summary": f"{ne} error{'s' if ne != 1 else ''}, {nw} warning{'s' if nw != 1 else ''}",
    }


def _check_type(value_str: str, expected: str) -> str | None:
    """Return None if value matches expected type, else a description."""
    v = value_str.strip().rstrip(",").strip()
    if not v:
        return None
    expected = expected.upper()

    # Strip Fortran kind specifier (e.g., 60.0_dp → 60.0)
    v_num = re.sub(r"_\w+$", "", v)

    if expected == "INTEGER":
        try:
            int(v_num)
            return None
        except ValueError:
            try:
                f = float(v_num.replace("d", "e").replace("D", "E"))
                int_f = int(f)  # OverflowError if inf/nan
                if f == int_f:
                    return f"'{v}' looks like a float; use {int_f} for INTEGER"
            except (ValueError, OverflowError):
                pass
            return f"'{v}' is not a valid INTEGER"

    if expected == "REAL":
        try:
            float(v_num.replace("d", "e").replace("D", "E"))
            return None
        except ValueError:
            return f"'{v}' is not a valid REAL"

    if expected == "LOGICAL":
        if v.upper().strip(".") in ("TRUE", "FALSE", "T", "F"):
            return None
        return f"'{v}' is not a valid LOGICAL (.TRUE. or .FALSE.)"

    return None  # CHARACTER — any value is fine


# ---------------------------------------------------------------------------
# Lookup  (mode: lookup)
# ---------------------------------------------------------------------------

def lookup_variables(ref_data: dict, variables: list[str]) -> dict:
    """Look up variable definitions from the reference JSON."""
    ref_nls = ref_data.get("namelists", {})

    # Build variable → (namelist, info_dict) index
    var_index: dict[str, tuple[str, dict]] = {}
    for nl, nl_vars in ref_nls.items():
        for vname, vinfo in nl_vars.items():
            var_index[vname] = (nl, vinfo)

    results: dict[str, dict] = {}
    not_found: list[str] = []

    for var in variables:
        vl = var.lower().strip()
        if not vl:
            continue
        if vl in var_index:
            nl, vinfo = var_index[vl]
            entry: dict = {"namelist": nl}
            for field in ("type", "default", "options", "info"):
                if field in vinfo and vinfo[field] is not None:
                    entry[field] = vinfo[field]
            results[vl] = entry
        else:
            close = get_close_matches(vl, list(var_index.keys()), n=3, cutoff=0.6)
            entry = {"error": "not_found"}
            if close:
                entry["suggestion"] = close
            results[vl] = entry
            not_found.append(vl)

    return {
        "program": ref_data.get("program", "unknown"),
        "results": results,
        "not_found": not_found,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

VALID_MODES = ("parse_def", "validate", "lookup")


def main() -> None:
    if len(sys.argv) < 2:
        print(_error("Usage: python qe_input_validator.py '<json>'"))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(_error(f"Invalid JSON: {exc}"))
        sys.exit(1)

    mode = args.get("mode", "").strip()
    if mode not in VALID_MODES:
        print(_error(f"Invalid mode '{mode}'. Use one of: {', '.join(VALID_MODES)}"))
        sys.exit(1)

    if mode == "parse_def":
        def_file = args.get("def_file", "").strip()
        if not def_file or not Path(def_file).exists():
            print(_error(f"def_file not found: {def_file}"))
            sys.exit(1)

        try:
            result = parse_def_file(def_file)
        except Exception as exc:
            print(_error(f"Failed to parse def file: {exc}"))
            sys.exit(1)

        output_file = args.get("output_file", "").strip()
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            Path(output_file).write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            total_vars = sum(len(v) for v in result["namelists"].values())
            print(_ok({
                "output_file": output_file,
                "program": result["program"],
                "namelists": sorted(result["namelists"].keys()),
                "total_variables": total_vars,
            }))
        else:
            print(_ok(result))

    elif mode == "validate":
        input_file = args.get("input_file", "").strip()
        ref_file = args.get("ref_file", "").strip()

        if not input_file or not Path(input_file).exists():
            print(_error(f"input_file not found: {input_file}"))
            sys.exit(1)
        if not ref_file or not Path(ref_file).exists():
            print(_error(f"ref_file not found: {ref_file}"))
            sys.exit(1)

        try:
            input_data = parse_qe_input(input_file)
        except Exception as exc:
            print(_error(f"Failed to parse input file: {exc}"))
            sys.exit(1)

        try:
            ref_data = json.loads(Path(ref_file).read_text(encoding="utf-8"))
        except Exception as exc:
            print(_error(f"Failed to load reference: {exc}"))
            sys.exit(1)

        report = validate_input(input_data, ref_data)
        print(_ok(report))

    elif mode == "lookup":
        ref_file = args.get("ref_file", "").strip()
        if not ref_file or not Path(ref_file).exists():
            print(_error(f"ref_file not found: {ref_file}"))
            sys.exit(1)

        variables = args.get("variables", [])
        if not variables or not isinstance(variables, list):
            print(_error("'variables' must be a non-empty list of variable names"))
            sys.exit(1)

        try:
            ref_data = json.loads(Path(ref_file).read_text(encoding="utf-8"))
        except Exception as exc:
            print(_error(f"Failed to load reference: {exc}"))
            sys.exit(1)

        result = lookup_variables(ref_data, variables)
        print(_ok(result))


if __name__ == "__main__":
    main()
