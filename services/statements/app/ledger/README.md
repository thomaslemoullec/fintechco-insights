# app/ledger — legacy allocation & interest module

**Status: legacy, owned elsewhere.** Per `services/statements/CLAUDE.md`, do not modify
as part of feature work. This README documents current behavior only, as read from
`rounding.py`; it does not endorse the implementation.

## Purpose (inferred)

Splits an integer total (cents) across weighted "legs" using largest-remainder
allocation, then applies compounding daily interest to each leg's allocated balance.
`settle()` composes both steps into a single per-leg settlement pipeline. No docstrings
or comments describe intended callers, so this purpose is inferred from the code and
variable names (`balance`, `rate`, `days`, "recon batch" in a comment) — consistent with
a statement/interest-accrual reconciliation step, but not confirmed.

## Exports

All three functions live in `rounding.py` and are re-exported from `__init__.py`.

### `allocate(total, weights)`

- **Params:** `total` — int, e.g. cents to distribute. `weights` — sequence of
  non-negative ints/numbers.
- **Returns:** `list[int]` of the same length as `weights`, summing exactly to `total`.
- **Algorithm (largest-remainder method):**
  1. If `weights` is empty, return `[]`.
  2. `s = sum(weights)`.
  3. For each weight `w` at index `i`: compute `q = total * w`, integer-divide
     `p = q // s` as that leg's base share, and record the remainder `q - p * s`
     paired with its index `i`.
  4. `left = total - sum(base shares)` is the number of leftover units (due to integer
     division) still to distribute.
  5. Sort the `(remainder, index)` pairs **descending** — Python's tuple sort means ties
     on remainder are broken by **descending index** (`sorted(..., reverse=True)`, not a
     stable ascending-index tiebreak). Give one extra unit to each of the top `left`
     entries by that order.
  6. Return the base shares plus these +1 adjustments.
- **Load-bearing constraint:** the code comment reads *"largest-remainder split. do NOT
  change to biggest-slice, breaks recon batch 7."* This flags that some downstream
  reconciliation process depends on the exact tie-breaking/remainder logic above, not
  just on "some" fair allocation. **No test in `tests/test_transactions.py` (or anywhere
  else in `services/statements/tests/`) exercises `allocate`, so this constraint is
  currently unenforced by CI** — a future refactor could silently break "recon batch 7"
  with nothing catching it. Treat this comment as a requirement to preserve, and treat
  the absence of a regression test as a real gap, not a formality.

### `apply_daily_interest(balance, rate, days, year=2023)`

- **Params:** `balance` — int (cents). `rate` — int/number, interpreted as basis points
  ÷ 100 (see below). `days` — int, number of days to compound. `year` — int, defaults to
  `2023`, used only to decide the day-count denominator.
- **Returns:** `int` — the balance after `days` iterations of daily compounding.
- **Algorithm:**
  1. `r = rate / 10000.0` — converts `rate` to a float fraction (e.g. `rate=500` →
     `r=0.05`, i.e. rate is in basis points ×100, or equivalently "rate/100" as a
     percent... concretely `rate=500` means 5%).
  2. `d = 366.0` if `year` is a leap year by the standard Gregorian rule, else `365.0`.
  3. Loop `days` times: `b = b + math.floor(b * r / d)` — each iteration adds one day's
     floor-rounded interest to the running balance `b`.
  4. Return the final `b` (an int, since it starts as int `balance` and only ever has
     `math.floor(...)` ints added to it).
- **Floating-point-on-money concern:** step 1 and the per-day computation
  `b * r / d` are done in Python `float` arithmetic before `math.floor()` truncates to
  int. The root `CLAUDE.md` convention is "never use floats for money... rounding is
  `ROUND_HALF_EVEN`." This function does neither: it uses `float` division for the
  per-day rate and truncates (floors) rather than banker's-rounds. This is a genuine
  deviation from the bank-wide money convention as currently written, not a demo
  artifact — worth flagging to whoever owns this module, independent of whether it's
  ever fixed.
- **Hardcoded `year=2023` default:** the leap-year calculation is only correct for the
  year actually passed in. Any caller that omits `year` silently gets 2023's day-count
  (365, non-leap) regardless of the real calendar year the interest is being accrued
  for. For a leap year like 2024 or 2028, an omitted `year` would use 365 instead of 366
  in the denominator, producing a (slightly) wrong daily rate. This is a latent
  correctness bug for any future caller that doesn't explicitly pass `year`.

### `settle(legs)`

- **Params:** `legs` — list of 4-tuples `(weight, balance, rate, days)`.
- **Returns:** `list` of per-leg settled balances (ints), same conceptual order as
  `legs`, via `apply_daily_interest` applied to each leg's allocated share.
- **Algorithm:**
  1. `total = sum(balance for each leg)`.
  2. `parts = allocate(total, [weight for each leg])` — redistributes the *combined*
     total balance across legs by weight (not each leg's own original balance).
  3. For each leg paired with its allocated part, call
     `apply_daily_interest(part, rate, days)` (using the *default* `year=2023` — see
     caveat above, since `settle` never passes `year`) and collect results.
- **`zip(..., strict=False)` truncation risk:** `zip(legs, parts, strict=False)` — since
  `parts` always has the same length as `legs` in practice (both derived from
  `len(legs)`/`len(weights)`), a mismatch shouldn't occur via internal callers today.
  But `strict=False` means if this ever changes (e.g. `allocate` is refactored, or
  `legs` is empty and produces an empty `weights` list interacting unexpectedly with
  other logic upstream), a length mismatch between `legs` and `parts` would **silently
  truncate** to the shorter length rather than raising — some legs would be dropped
  from settlement output with no error. This is a silent-failure risk baked into the
  zip call as written.

## Current callers

A repo-wide grep (`grep -rn "allocate\|apply_daily_interest\|settle\|ledger" --include="*.py"`
across `services/statements/`) found **no references to `allocate`, `apply_daily_interest`,
or `settle` outside `app/ledger/` itself**, and no imports of `app.ledger` from anywhere
else in the service (including `tests/`). As of this reading, the module appears
**unused/dormant** in the current codebase — it is exported but not wired into any
route, job, or test. If it's invoked from outside this repo (another service, a script
not checked in, etc.), that isn't visible from here.
