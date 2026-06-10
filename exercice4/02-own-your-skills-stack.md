---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 2: Own your skills stack

---

## Brief

A **skill** is a markdown file that injects extra context to steer the agent — reusable, project-specific or global.

You are about to lean on several of them. Before you run any, you install and read them yourself.

---

## Install them yourself

- Create a working repo for your build (e.g. `my-dqc/`).
- Install these skills into it, from the source — Matt Pocock's public skills (`mattpocock/skills` on GitHub):

  `grill-me` · `grill-with-docs` · `to-prd` · `to-issues` · `tdd` · `handoff`

- Fetch your own copy. Don't borrow someone else's.

These are the engines of every step that follows.

---

## Read `/tdd` closely

- What *philosophy* does it inject into the agent?
- What loop does it enforce (the three words)?
- What does it explicitly forbid — and why is "all tests, then all code" a trap?

A skill is context-nudging. You should be able to predict how it bends the output.

---

## Audit for trust

Skim one skill as if a stranger sent it to you.

- Is there any instruction you would *not* want silently shaping your agent?
- Auto-commits? Network calls? File deletion? A hidden agenda in the prose?

This is why "read your skills first" is a security posture, not a courtesy.

---

## Make them yours

- Read every skill before you run it.
- Edit one line of one skill so it fits how *you* work.

You installed them, you've read them — you own them now.

---

## Ask yourself

- What would "owning your entire skills stack" buy you?
- A skill from an untrusted source could steer you how, exactly?

---

## Output

- A one-paragraph summary: *"what `/tdd` injects."*
- One line in any skill you'd change, and why.

---

## Done

Every skill in your repo is one you have installed, read, and would defend out loud.
