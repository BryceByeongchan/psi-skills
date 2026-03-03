---
name: psi-run-calc
user-invokable: true
description: Run a calculation on a remote HPC system
argument-hint: "<calc_id>"
---

Run a calculation through its full lifecycle: push files to remote, submit a job, monitor it, and pull results back.

## Usage

```
psi:run-calc <calc_id>
```

## Phases

Execute phases sequentially. The script handles file operations; **you** handle job script generation and user interaction.

### 1. Preflight

```bash
python {skill_dir}/run_calc.py preflight <calc_id>
```

Returns JSON with calc info, computer config, file lists, and SSH status. Verify:
- SSH is connected (if not, tell user to run `ssh -MNf <hostname>` and stop)
- `input/` is non-empty (warn if empty — the calc may have nothing to run)
- `status` is not already `completed`

**Resume support**: if status is `running` and `job_id` is set, skip to the **Monitor** phase.

### 2. Push

```bash
python {skill_dir}/run_calc.py push <calc_id>
```

Syncs `input/`, `code/`, and `README.md` to the remote `hpc_path`. Only these directories are pushed — never `output/`.

### 3. Submit

**You** generate a job script using the computer config from preflight (scheduler, account, queues, modules, job_template). Tailor it to the calc's `code` type:
- Use `job_template` as the starting point if available
- Set job name to the calc ID
- Load appropriate modules
- Set the working directory to `hpc_path`
- Add the correct run command for the code type

**Always show the job script to the user and get approval before submitting.**

Then submit:

```bash
python {skill_dir}/run_calc.py submit <calc_id> '<job_script>'
```

Returns JSON with `job_id`. The script stores `job_id` in frontmatter and sets status to `running`.

### 4. Monitor

```bash
python {skill_dir}/run_calc.py monitor <calc_id>
```

Returns JSON with queue state, output file list, and `job_finished` flag.

Poll repeatedly until `job_finished` is true. Between polls, **wait at least 60 seconds**. Report the queue state to the user each time.

If SSH disconnects during monitoring, **stop polling** and tell the user. They can resume later with `/psi-run-calc <calc_id>` (resume support will skip to monitor).

### 5. Pull

```bash
python {skill_dir}/run_calc.py pull <calc_id>
```

Pulls `output/` and scheduler logs from remote. Files >50MB are skipped by default. Use `--all` to pull everything.

After pulling, update status:

```bash
python {skill_dir}/run_calc.py update-status <calc_id> completed
```

If the job failed (check scheduler logs), set status to `error` instead.

## Rules

- **Always show the job script to the user before submitting.** Never auto-submit.
- **`input/` pushes up, `output/` pulls down — never reversed.** Do not pull input or push output.
- **60-second minimum polling interval.** Do not poll more frequently.
- **Stop monitoring on SSH disconnect.** Do not retry SSH in a loop.
- **Resume from current state.** If calc is already `running` with a `job_id`, skip directly to monitor.
- **Do not modify `input/` or `code/` contents.** Those are the user's responsibility.
