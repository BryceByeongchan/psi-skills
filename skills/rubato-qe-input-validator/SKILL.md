---
name: rubato-qe-input-validator
user-invokable: true
description: Validate Quantum Espresso input files against official flag definitions
argument-hint: "<input_file> [executable:pw] [qe_source:/path/to/qe]"
---

Validate a Quantum Espresso input file against the official variable definitions from QE source code.

## Prerequisites

No additional dependencies beyond Python 3.10+. Pre-generated reference files for QE 7.5 are bundled in `refs/`.

## Usage

```
rubato:qe-input-validator <input_file> [executable:pw|pp|dos|bands|projwfc|ph|pw2wannier90] [qe_source:/path/to/qe]
```

**You** parse the user's arguments:

- **input_file**: Path to QE input file (e.g., `pw.in`, `pp.in`).
- `executable:NAME` — Which QE executable the input is for. If not specified, **you** auto-detect by examining the namelist names in the input file (see Auto-Detection below).
- `qe_source:/path/to/qe` — Path to QE source tree. If provided, regenerate the reference JSON from the source's def file before validating. Otherwise, use the bundled `refs/` files.

## Execution

### Step 1: Determine executable and reference

Auto-detect the executable from namelist names if not specified:

| Namelist(s) found | Executable |
|---|---|
| &CONTROL, &SYSTEM, &ELECTRONS | pw.x |
| &INPUTPP, &PLOT | pp.x |
| &DOS | dos.x |
| &BANDS | bands.x |
| &PROJWFC | projwfc.x |
| &INPUTPH | ph.x |
| &INPUTPP (no &PLOT, has seedname) | pw2wannier90.x |

Map executable to reference file:
- `pw` → `{skill_dir}/refs/pw.json`
- `pp` → `{skill_dir}/refs/pp.json`
- `dos` → `{skill_dir}/refs/dos.json`
- `bands` → `{skill_dir}/refs/bands.json`
- `projwfc` → `{skill_dir}/refs/projwfc.json`
- `ph` → `{skill_dir}/refs/ph.json`
- `pw2wannier90` → `{skill_dir}/refs/pw2wannier90.json`

### Step 2: (Optional) Regenerate reference from QE source

If `qe_source` is provided, regenerate the reference first:

```bash
python {skill_dir}/qe_input_validator.py '{"mode": "parse_def", "def_file": "{qe_source}/PW/Doc/INPUT_PW.def", "output_file": "{skill_dir}/refs/pw.json"}'
```

The def file locations within QE source:
- pw: `PW/Doc/INPUT_PW.def`
- pp: `PP/Doc/INPUT_PP.def`
- dos: `PP/Doc/INPUT_DOS.def`
- bands: `PP/Doc/INPUT_BANDS.def`
- projwfc: `PP/Doc/INPUT_PROJWFC.def`
- ph: `PHonon/Doc/INPUT_PH.def`
- pw2wannier90: `PP/Doc/INPUT_pw2wannier90.def`

### Step 2b: Look up variable documentation

To look up official documentation for specific QE variables (useful when suggesting new flags or explaining variables not in the user's input):

```bash
python {skill_dir}/qe_input_validator.py '{"mode": "lookup", "ref_file": "<ref_path>", "variables": ["nspin", "vdw_corr", "assume_isolated"]}'
```

Returns JSON with:
- `results`: dict mapping each variable to `{namelist, type, default, options, info}` (or `{error: "not_found", suggestion: [...]}` if unknown)
- `not_found`: list of variables not found in the reference

Use this mode when:
- Suggesting flags that are not in the user's input (e.g., from Material Physics Analysis)
- The user asks "what does variable X do?"
- You need to verify exact options/defaults before recommending a value

### Step 3: Run validation

```bash
python {skill_dir}/qe_input_validator.py '{"mode": "validate", "input_file": "<path>", "ref_file": "<ref_path>"}'
```

The script returns JSON with:
- `namelists_found`: namelists detected in the input file
- `cards_found`: cards detected (ATOMIC_SPECIES, K_POINTS, etc.)
- `errors`: list of validation errors (each may include an `info` field with official QE documentation)
- `warnings`: list of warnings (each may include an `info` field)
- `variable_info`: dict mapping each recognized variable name to its official QE documentation text — use this for physics-aware suggestions in Step 4b
- `summary`: human-readable count

Error types:
- `unknown_variable` — variable not recognized (with suggestions for similar names)
- `wrong_namelist` — variable exists but in a different namelist
- `type_mismatch` — value doesn't match expected Fortran type
- `invalid_option` — for enumerated variables, value not in allowed set
- `unknown_namelist` — namelist name not recognized

### Step 4: Semantic validation (your judgment)

After the script's mechanical validation, **you** perform additional semantic checks:

**For pw.x:**
- `calculation = 'relax'` or `'md'` → &IONS namelist should be present
- `calculation = 'vc-relax'` or `'vc-md'` → &CELL namelist should be present
- `ecutrho` should generally be 4× `ecutwfc` for norm-conserving PPs (8-12× for ultrasoft/PAW)
- `nat` should match the number of atoms in ATOMIC_POSITIONS
- `ntyp` should match the number of species in ATOMIC_SPECIES
- `ibrav = 0` → CELL_PARAMETERS card should be present
- For bands/nscf: `nosym = .TRUE.` and `noinv = .TRUE.` are recommended

**For post-processing codes:**
- `prefix` and `outdir` should match the parent pw.x calculation

### Step 4b: Physics-aware suggestions (your judgment)

The reference JSON includes an `info` field for most variables, containing the official QE documentation (cleaned from the INPUT_*.def files). Use this to provide physics-informed feedback:

1. **When reporting errors/warnings**, cite the relevant `info` text to explain *why* a value is problematic or what the variable does. Do not just say "unknown variable" — give context.

2. **When the user asks "what does this variable do?"**, look up its `info` field in the reference JSON rather than relying solely on your training knowledge. This gives the canonical QE documentation.

3. **Proactive physics suggestions** — after validating, scan the input for common physics omissions:
   - Magnetic elements (Fe, Co, Ni, Mn, Cr, V, rare earths) present but no `nspin = 2` or `starting_magnetization`
   - Likely metallic system but no `occupations = 'smearing'` / `degauss`
   - Heavy elements (Z > 50) but no `lspinorb` / `noncolin` for SOC
   - Transition metal oxide but no DFT+U (HUBBARD card or `lda_plus_u`)
   - Present these as suggestions, not errors. Let the user decide.

4. **For variables with `options`**, cite the per-option descriptions from the `info` field to explain what each allowed value means.

### Step 5: Report results

Present the validation results clearly:
1. Show a summary (N errors, M warnings)
2. List each error with explanation and fix suggestion
3. List each warning
4. Add any semantic issues you found in Step 4
5. Add any physics suggestions from Step 4b (clearly marked as suggestions)
6. If the user wants, offer to fix the issues automatically

## Rules

- **Always auto-detect the executable** if not specified. Fall back to asking the user only if ambiguous.
- **Show all errors at once.** Do not stop at the first error.
- **Suggest fixes for every error.** Use the `suggestion` field from the script output, and add your own domain knowledge.
- **The bundled refs/ are for QE 7.5.** If the user's QE version differs significantly, recommend regenerating with `qe_source:`.
- **Do not modify the input file without user confirmation.** Show proposed fixes first.
- **For unknown variables with no suggestion**, check if it might be a deprecated variable or from a QE extension.
