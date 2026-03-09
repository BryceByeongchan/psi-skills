---
name: psi-bgw-parabands
user-invokable: true
description: Generate parabands.inp to produce WFN_pb with many empty bands via stochastic pseudobands
argument-hint: "number_bands:N [parent:cNNN] [calc_id:cNNN] [options...]"
---

Generate `parabands.inp` for the `parabands.x` executable, which produces `WFN_pb` — a wavefunction file with a large number of empty bands using stochastic pseudobands compression.

## Usage

```
psi:bgw-parabands number_bands:N [parent:cNNN] [calc_id:cNNN] [options...]
```

- `number_bands:N` — **Required.** Target total number of bands in the output WFN_pb (e.g., 2000–6000).
- `parent:cNNN` — Parent pw2bgw calculation. Used to locate VSC and VKB files, and to read the number of bands in the input WFN to validate the constraint.
- `calc_id:cNNN` — Save `parabands.inp` to `calc_db/{calc_id}/input/`. If omitted, save to current directory.
- `protected_cond_bands:N` — Override the number of low-energy conduction bands kept exact (default: 10).
- `accumulation_window:X` — Override the fractional energy window for stochastic slicing (default: 0.02).
- `num_bands_per_slice:N` — Override the number of pseudobands per stochastic subspace (default: 2).

## Execution

### Step 1: (Optional) Read parent information

If `parent:cNNN` is given, look for:
- The pw2bgw calc directory to find `WFN`, `VSC`, `VKB` file locations.
- Read parent `pw.in` to get `nbnd` for validation.

### Step 2: Construct parabands.inp

```
input_wfn_file    WFN
output_wfn_file   WFN_pb
vsc_file          VSC
vkb_file          VKB

number_bands      {N}

use_pseudobands
protected_cond_bands   {protected_cond_bands}
accumulation_window    {accumulation_window}
num_bands_per_slice    {num_bands_per_slice}
```

Defaults:
- `protected_cond_bands` = 10
- `accumulation_window` = 0.02
- `num_bands_per_slice` = 2

### Step 3: Show and save

1. Show the complete `parabands.inp` to the user.
2. Ask for confirmation or modifications.
3. Save to `calc_db/{calc_id}/input/parabands.inp` if `calc_id` is given, or `./parabands.inp` otherwise.

## Validation

- `number_bands` must be > `nbnd` of the input WFN (the number of bands from the parent QE nscf). If the parent is known, check this and error if violated.
- `protected_cond_bands` should cover at least the bands used in sigma's `begin diag` block. Suggest this to the user.
- `use_pseudobands` is **always ON**. Never omit it.

## Physics Notes

- `use_pseudobands` compresses high-energy conduction bands stochastically. For example, 4000 explicit bands collapse to a smaller number of effective pseudobands, dramatically reducing memory and I/O.
- This is the standard approach for low-dimensional materials (2D materials, surfaces) that require many empty bands for convergence.
- `number_bands` sets the upper limit for epsilon/sigma convergence tests. A typical starting value is 2000–4000 for 2D materials; for bulk semiconductors 500–2000.
- `protected_cond_bands` keeps the lowest `N` conduction bands as exact KS states. These must cover the bands used in `begin diag` of sigma.inp.

## Rules

- **`use_pseudobands` is always written.** It is the purpose of this executable.
- **`number_bands` must exceed the parent nscf `nbnd`** — parabands.x cannot reduce bands, only add more.
- **Show the complete parabands.inp before saving.** Never write without user confirmation.
- **When saving to a psi calc directory**, always use the `input/` subdirectory: `calc_db/{calc_id}/input/parabands.inp`.
- If `number_bands` is not specified, ask the user for it. There is no reasonable default.
