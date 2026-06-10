---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 7: Vertical slices → issues

---

## Brief

You don't hand the agent the whole PRD and say "go."

You hand it one thin slice that goes all the way through — and grow from there.

---

## Vertical, not horizontal

A **vertical slice** cuts through every layer — parse → profile → score → render — narrow but complete and demoable.

A **horizontal slice** ("build the entire profiler") is not demoable on its own. Avoid it.

> Prefer many thin slices over a few thick ones.

---

## Do this

Run `/to-issues`. Break your PRD into tracer-bullet slices. For each:

- **Title** — short and descriptive
- **Type** — HITL (needs you) or AFK (agent can run alone)
- **Blocked by** — which slices come first
- **User stories covered**

---

## A good slice ladder

A healthy breakdown looks like:

`01` scaffold → upload/parse → completeness → validity → distribution → scoring → warnings → charts → report.

Each rung is independently shippable. Each builds on a named blocker.

---

## Ask yourself

- Which slice is your **tracer bullet** — the thinnest end-to-end thing that proves the whole path works?
- Which slices need a human in the loop (a threshold, a design call), and which can run AFK?

---

## Output

A set of issue files in your repo, written in dependency order (blockers first).

---

## Done

You could hand slice #1 to someone — or an agent — and get something demoable back.
