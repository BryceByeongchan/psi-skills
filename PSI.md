# Using psi skills

Add this to your project's `CLAUDE.md`:

```markdown
## psi — Provenance Tracking

This project uses psi skills (`skills/psi-*`) for computation provenance tracking.

### Setup

Skills are in `skills/psi-*/`. Each has a SKILL.md prompt and a self-contained Python script (requires PyYAML).

### Quick Reference

- `/psi-init` — Initialize `calc_db/` and `reports/` directories
- `/psi-new-calc <title> <code> [parents:...] [tags:...] [computer:...] [type:multi] [subjobs:400,500,600]` — Create calculation
- `/psi-update-calc <id> field=value ...` — Update calculation (supports dot notation: `key_results.energy=-5.43`, `subjobs.500.status=completed`)
- `/psi-new-report <title> [calcs:...] [tags:...]` — Create report
- `/psi-update-report <id> field=value ...` — Update report
- `/psi-status` — Project summary
- `/psi-graph [id]` — Provenance DAG
- `/psi-rebuild-index` — Rebuild indexes from front matter
- `/psi-run-calc <calc_id>` — Push, submit, monitor, and pull a calculation on remote HPC
- `/psi-add-computer`, `/psi-list-computers`, `/psi-update-computer`, `/psi-remove-computer` — Computer registry
- `/psi-fetch-struct <query> [output_dir:path]` — Fetch structure from Materials Project
- `/psi-qe-input-generator <structure_file> <calc_type> [options...]` or `<executable> [parent:cNNN] [options...]` — Generate QE input with physics-aware suggestions (pw.x, pp.x, dos.x, bands.x, projwfc.x, ph.x, pw2wannier90.x)
- `/psi-qe-input-validator <input_file> [executable:...] [qe_source:...]` — Validate QE input with physics context from official documentation
- `/psi-qe-plotbands <xml_file> [--labels "G M K G"] [--erange -4 4] [--out bands.png]` — Plot band structure from QE bands.x XML output

### BerkeleyGW GW Workflow

- `/psi-bgw-pw2bgw [parent:cNNN] [calc_id:cNNN]` — Generate `pw2bgw.inp` for QE → BGW format conversion (WFN, RHO, VXC, VSC, VKB)
- `/psi-bgw-parabands number_bands:N [parent:cNNN] [calc_id:cNNN]` — Generate `parabands.inp` for many empty bands via stochastic pseudobands (WFN_pb)
- `/psi-bgw-epsilon epsilon_cutoff:Ry number_bands:N [parent:cNNN] [calc_id:cNNN]` — Generate `epsilon.inp` for dielectric function calculation
- `/psi-bgw-sigma screened_coulomb_cutoff:Ry number_bands:N [parent_epsilon:cNNN] [calc_id:cNNN]` — Generate `sigma.inp` for self-energy (QP correction) calculation
- `/psi-bgw-gw-conv-sigma sweep:param values:v1,v2,... parent_epsilon:cNNN vbm:ik=N,n=M cbm:ik=N,n=M` — Set up sigma-only convergence sweep (reuses fixed epsmat)
- `/psi-bgw-gw-conv-epsilon sweep:param values:v1,v2,... vbm:ik=N,n=M cbm:ik=N,n=M qgrid:Nx,Ny,Nz` — Set up epsilon+sigma convergence sweep (re-runs epsilon.x with coarse q-grid)
- `/psi-bgw-gw-conv-analyze calcs:dir1,dir2,... vbm:ik=N,n=M cbm:ik=N,n=M sweep:param [threshold:0.05]` — Parse sigma.out → QP gap convergence table (Eqp1)

### Key Rules

- Run `/psi-init` before any other psi skill.
- Create calcs with the same parent **sequentially**, not in parallel.
- Computer registry is project-local at `calc_db/computers.yaml`.
- Do not manually edit `index.md` files — use the skills.
- **Do NOT access other project directories.** Stay within the current project.
- Directory names include tags: `c001_mos2_bulk_relax/`, `r001_mos2_stability/`. The `id` in frontmatter stays bare (`c001`). Always reference calcs/reports by their `id`, not the directory name.

### Creating Reports

- Before creating a report, check `calc_db/index.md` for existing calculations that are relevant.
- If suitable calculations exist, reference them with `calcs:c001,c002,...` when creating the report.
- If no suitable calculation exists, create one first with `/psi-new-calc`, then create the report referencing it.
- Reports must always be grounded in actual calculation data with provenance links maintained.

### Multi-Job Calculations

Use `type:multi` for systematic parameter variations (convergence tests, parameter sweeps) where jobs share the same code but vary parameters:

\`\`\`
/psi-new-calc "ENCUT Convergence" VASP type:multi subjobs:400,500,600 tags:encut,convergence
\`\`\`

This creates a single calc with shared `code/` and per-subjob `{label}/input/`, `{label}/output/` directories. Sub-job statuses are tracked individually and auto-aggregated to the top-level status.

Update sub-job status with dot notation:
\`\`\`
/psi-update-calc c002 subjobs.500.status=completed
\`\`\`

Run multi-job calcs with `/psi-run-calc` — sub-jobs are submitted sequentially with approval per script.

### Post-Processing

- When asked to do post-processing or analysis, create a report with `/psi-new-report` linking the relevant calculations.
- Save any scripts used for post-processing in the report directory.
\`\`\`
