---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 5: Conversation → PRD

---

## Brief

You've grilled the decisions out of your head. Now freeze them into a spec the agent can build from — and that you can hold a build accountable to.

---

## Do this

Run `/to-prd`.

It synthesises the current conversation (no new interview) into a PRD:

- Problem & solution, in the user's words
- A long, numbered list of user stories
- Implementation decisions — the modules
- Testing decisions · out of scope

---

## Watch the module section

It should sketch **deep modules** — rich behaviour behind a small interface.

If it proposes shallow pass-throughs (a module that just forwards a call), push back. You'll design these properly in Step 6.

---

## Pressure-test it

- Does every decision you resolved in Step 4 appear in the PRD?
- Did the agent invent any requirement you never agreed to?
- If a peer is nearby, swap PRDs and red-team each other's.

---

## Ask yourself

- Which user stories did the agent surface that you'd forgotten?
- Does every "out of scope" line protect you from a tempting rabbit hole?

---

## Output

`PRD.md` in your repo.

---

## Done

A stranger could read your PRD and build roughly the right thing.
