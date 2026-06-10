---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 8: TDD a deep module

---

## Brief

Feedback loops are the engine that drives the agent. The test suite *is* the loop.

Build it, then let it pull the implementation out of the agent — one behaviour at a time.

---

## Do this

Pick your **profiler** slice. Run `/tdd`.

```
RED   → write ONE failing test
GREEN → minimal code to pass
        repeat
```

Not all tests then all code — that's horizontal slicing, and it produces tests of *imagined* behaviour.

---

## Test behaviour, not internals

Good test:

> a column that is 50% null reports `null_pct == 0.5`

Bad test:

> the function calls `isna()` internally

A good test survives an internal rewrite.

---

## Build a real signal

Use `assets/vgsales.csv` to sanity-check:

- `Year` has real nulls
- `Platform`, `Genre` have low cardinality

For exact-value assertions, construct **tiny DataFrames inline** in the test.

---

## Human in the loop

After each green test, *you* evaluate: is this the behaviour you meant?

Let the next test be shaped by what the last cycle taught you.

---

## Ask yourself

- Which of your tests would still pass if the agent rewrote the whole implementation? (That's a good one.)
- Which broke when nothing behavioural changed? (Fix or delete it.)

---

## Output

A green test suite + one tested deep module.

---

## Done

You can refactor the internals freely and the tests still hold.
