---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 3: The one-sentence kickoff

---

## Brief

This whole build starts from **one sentence** in `project.md`.

Watch how much you can kick off with how little — then decide where to actually spend your words.

---

## Write your `project.md`

One or two sentences, no more. The reference was:

> I want to make an application that profiles and evaluates the data quality of a given dataset; the dataset is a CSV uploaded manually. The output is a data quality report.

Make it yours. Keep it to the essence.

---

## The intentionality dial

Every part of the project sits on a line:

```
0 ───────────────────────────────── 100
let the agent decide        you specify exactly
```

The agent already knows how to parse a CSV, accept an upload, render a table. It does **not** know your scoring rules, module boundaries, or warning thresholds.

---

## Map your project

Place each part on the dial:

- Parsing the upload → ?
- Computing the quality score → ?
- The module boundaries → ?
- The warning thresholds → ?
- Rendering a table → ?

Maximise intent for **domain logic, architecture, interfaces**. Minimise it for boilerplate.

---

## Ask yourself

- Where would over-specifying just waste your effort?
- Where would under-specifying let the agent guess wrong in a way you'd regret?

---

## Output

- `project.md` (one or two sentences)
- An intentionality map: what you'll spell out vs what you'll delegate

---

## Done

You can point to the **3–4 decisions** in this project worth spending real intent on.
