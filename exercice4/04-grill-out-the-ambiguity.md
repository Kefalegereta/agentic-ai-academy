---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 4: Grill out the ambiguity

---

## Brief

A plan in your head feels complete. It isn't.

Before you write a single prompt to *build*, get interrogated about what you actually want.

---

## Do this

Run `/grill-me` (or `/grill-with-docs`) with your `project.md` as the subject.

- Answer one question at a time.
- For each, the agent proposes a recommended answer.
- **You decide.** A recommendation is a proposal to accept or reject — never a default to rubber-stamp.

---

## What the grilling should pin down

- What exactly is a "quality score"? On what scale?
- Which dimensions? (completeness · uniqueness · validity · distribution)
- What makes something a *warning* versus just a statistic?
- What is firmly out of scope?

---

## "Plan mode is not enough"

Plan mode plans the *build*. Grilling resolves *what you want* before there's anything to plan.

Notice the difference: one organises work, the other removes ambiguity.

---

## Ask yourself

- Which answer surprised you?
- Which decision didn't you realise was still open?
- Where did you *almost* let the agent decide something that was yours to own?

---

## Output

The resolved decisions, captured durably — a `CONTEXT.md` or a decisions list in your repo.

---

## Done

There is no major *"wait — what did we mean by that?"* left in the design.
