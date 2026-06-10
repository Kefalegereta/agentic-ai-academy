---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 9: Context is alignment

---

## Brief

The agent is only as aligned as its context.

> Too little, and it guesses. Too much, and the signal drowns.

You'll feel both failure modes — and practise the cure.

---

## Feel the bloat

Keep one long session running across several slices. Then run `/context`.

- Watch the *messages* share climb toward the ceiling.
- Notice the agent getting vaguer, repeating itself, "forgetting" earlier decisions.

---

## The compact trap

`/compact` summarises the conversation to make room. But:

- Each compact carries the agent's prior trajectory.
- Biases layer silently across rounds → **drift**.

A summary of a summary of a summary is not your spec.

---

## The cure — start fresh

Capture durable state *outside* the chat:

- Run `/handoff` to write a handoff document.
- Make sure `CLAUDE.md`, your PRD, and your issues hold the real decisions.
- Open a **clean session** and continue from those artifacts.

---

## Do this — compare

Continue the same slice two ways:

- **(a)** after a `/compact`
- **(b)** from a fresh session + your handoff doc

Judge the quality of each continuation.

---

## Ask yourself

- Which continuation stayed truer to your intent?
- What was living in your head that should have been in an artifact?

---

## Output

A handoff doc + a short note on where drift crept in.

---

## Done

A fresh session, fed your artifacts, is as capable as your bloated one — and far more predictable.
