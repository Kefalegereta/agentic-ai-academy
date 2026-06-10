---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 6: Deep modules by design

---

## Brief

Vibe coding produces spaghetti by default.

You will make spaghetti *structurally impossible* — by designing interfaces before implementations.

---

## What "deep" means

A deep module hides a lot of behaviour behind a small interface.

The reference profiler is **one call**:

```python
profile(df) -> ProfileResult
```

…hiding null checks, type inference, outlier detection, format matching, and stats behind it.

---

## Design your interfaces

Write the *interface* of each module — name, input, output, one sentence of what it does. **No implementation yet.**

- Profiler · `profile(df) -> ProfileResult`
- Scorer · `score(profile) -> ScoreResult`
- Warning Engine · `warnings(profile) -> [Warning]`
- Report Builder · `build(profile, score, warnings) -> payload`

---

## The deletion test

For each module, imagine deleting it.

- Complexity *vanishes*? It was a pass-through — cut it.
- Complexity *reappears* across many callers? It earns its place.

---

## Contrast with spaghetti

Look at your vibe-coded Pass 1 (Step 1), or ask the agent for a "single file, no modules" version.

- Where would adding one new metric force you to touch five places?
- Where does a clean interface tell the agent *exactly* where a change goes?

---

## Ask yourself

- Can you hold each interface in your head without knowing the internals?
- Does every future feature have an obvious home?

---

## Output

A module sketch: 4 interfaces, signatures only, plus one line per module on why it passes the deletion test.

---

## Done

Every future feature enters through a known interface. No new dependency leaks across a boundary.
