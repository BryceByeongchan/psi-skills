#!/usr/bin/env python3
"""Validate a BerkeleyGW input file against official keyword definitions.

Usage:
    python bgw_validate.py '{"mode": "validate", "input_file": "<path>", "ref_file": "<path>"}'
    python bgw_validate.py '{"mode": "lookup", "ref_file": "<path>", "variables": ["epsilon_cutoff", ...]}'

Modes:
    validate  — Parse input file, check keywords against refs JSON, return errors/warnings.
    lookup    — Look up documentation for specific keywords.
"""

import json
import os
import re
import sys
from difflib import get_close_matches


def _ok(payload: dict) -> str:
    return json.dumps({"status": "ok", **payload}, indent=2)


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message}, indent=2)


def load_ref(ref_path: str) -> dict:
    with open(ref_path, "r") as f:
        return json.load(f)


def parse_bgw_input(path: str) -> dict:
    """Parse a BerkeleyGW input file into keywords and blocks.

    Returns:
        {
            "keywords": [{"name": str, "value": str, "line": int}, ...],
            "blocks": [{"name": str, "lines": [str], "start_line": int}, ...],
            "raw_lines": [str, ...]
        }
    """
    with open(path, "r") as f:
        lines = f.readlines()

    keywords = []
    blocks = []
    current_block = None
    i = 0

    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # strip inline comments
        if "#" in line:
            line = line[:line.index("#")].strip()

        lower = line.lower()

        # block start
        if lower.startswith("begin "):
            block_name = lower.split(None, 1)[1].strip()
            current_block = {"name": block_name, "lines": [], "start_line": i}
            continue

        # block end
        if lower == "end" or lower.startswith("end "):
            if current_block is not None:
                blocks.append(current_block)
                current_block = None
            continue

        # inside a block
        if current_block is not None:
            current_block["lines"].append(line)
            continue

        # keyword-value pair
        parts = line.split(None, 1)
        keyword = parts[0].lower()
        value = parts[1].strip() if len(parts) > 1 else ""
        keywords.append({"name": keyword, "value": value, "line": i})

    return {"keywords": keywords, "blocks": blocks, "raw_lines": lines}


def check_type(value: str, expected_type: str) -> bool:
    """Check if a value string matches the expected type."""
    if not value:
        return True  # flags with no value are ok for LOGICAL

    if expected_type == "LOGICAL":
        return value.lower() in (
            ".true.", ".false.", "true", "false", "0", "1",
        )
    elif expected_type == "INTEGER":
        try:
            int(value)
            return True
        except ValueError:
            return False
    elif expected_type == "REAL":
        try:
            float(value.replace("d", "e").replace("D", "E"))
            return True
        except ValueError:
            return False
    elif expected_type == "STRING":
        return True
    elif expected_type in ("INTEGER_ARRAY", "REAL_ARRAY"):
        return True  # arrays are hard to validate generically
    elif expected_type == "BLOCK_INLINE":
        return True
    return True


def validate(input_path: str, ref: dict) -> dict:
    """Validate input file against reference."""
    parsed = parse_bgw_input(input_path)
    ref_keywords = ref.get("keywords", {})
    ref_blocks = [b.lower() for b in ref.get("blocks", [])]
    aliases = ref.get("aliases", {})

    errors = []
    warnings = []
    recognized = {}

    all_ref_names = list(ref_keywords.keys())

    for kw in parsed["keywords"]:
        name = kw["name"]
        value = kw["value"]
        line = kw["line"]

        # resolve aliases
        resolved = aliases.get(name, name)

        if resolved in ref_keywords:
            info = ref_keywords[resolved]
            recognized[resolved] = value

            # type check
            if not check_type(value, info.get("type", "STRING")):
                errors.append({
                    "type": "type_mismatch",
                    "keyword": name,
                    "line": line,
                    "expected_type": info["type"],
                    "value": value,
                    "info": info.get("info", ""),
                })
        else:
            # unknown keyword
            suggestions = get_close_matches(name, all_ref_names, n=3, cutoff=0.6)
            errors.append({
                "type": "unknown_keyword",
                "keyword": name,
                "line": line,
                "suggestions": suggestions,
            })

    # check blocks
    for block in parsed["blocks"]:
        if block["name"] not in ref_blocks:
            known_blocks = ref_blocks if ref_blocks else ["(none)"]
            errors.append({
                "type": "unknown_block",
                "block": block["name"],
                "line": block["start_line"],
                "known_blocks": known_blocks,
            })

    # check for deprecated keywords
    for kw in parsed["keywords"]:
        name = kw["name"]
        resolved = aliases.get(name, name)
        if resolved in ref_keywords:
            info_text = ref_keywords[resolved].get("info", "")
            if "DEPRECATED" in info_text.upper():
                warnings.append({
                    "type": "deprecated",
                    "keyword": name,
                    "line": kw["line"],
                    "info": info_text,
                })

    summary = f"{len(errors)} error(s), {len(warnings)} warning(s)"

    return {
        "keywords_found": [kw["name"] for kw in parsed["keywords"]],
        "blocks_found": [b["name"] for b in parsed["blocks"]],
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def lookup(ref: dict, variables: list) -> dict:
    """Look up keyword documentation."""
    ref_keywords = ref.get("keywords", {})
    all_names = list(ref_keywords.keys())
    results = {}
    not_found = []

    for var in variables:
        var_lower = var.lower()
        if var_lower in ref_keywords:
            results[var_lower] = ref_keywords[var_lower]
        else:
            suggestions = get_close_matches(var_lower, all_names, n=3, cutoff=0.6)
            results[var_lower] = {"error": "not_found", "suggestions": suggestions}
            not_found.append(var_lower)

    return {"results": results, "not_found": not_found}


def main():
    if len(sys.argv) < 2:
        print(_error("Usage: python bgw_validate.py '<json>'"))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(_error(f"Invalid JSON input: {exc}"))
        sys.exit(1)

    mode = args.get("mode", "validate")
    ref_file = args.get("ref_file")

    if not ref_file:
        print(_error("'ref_file' is required"))
        sys.exit(1)

    if not os.path.exists(ref_file):
        print(_error(f"Reference file not found: {ref_file}"))
        sys.exit(1)

    ref = load_ref(ref_file)

    if mode == "validate":
        input_file = args.get("input_file")
        if not input_file:
            print(_error("'input_file' is required for validate mode"))
            sys.exit(1)
        if not os.path.exists(input_file):
            print(_error(f"Input file not found: {input_file}"))
            sys.exit(1)
        result = validate(input_file, ref)
        print(_ok(result))

    elif mode == "lookup":
        variables = args.get("variables", [])
        if not variables:
            print(_error("'variables' list is required for lookup mode"))
            sys.exit(1)
        result = lookup(ref, variables)
        print(_ok(result))

    else:
        print(_error(f"Unknown mode: {mode}. Use 'validate' or 'lookup'."))
        sys.exit(1)


if __name__ == "__main__":
    main()
