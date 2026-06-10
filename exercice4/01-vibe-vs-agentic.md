---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Data Quality Checker

## Step 1: Vibe vs Agentic

---

## Brief

Over these exercises you will build a **Data Quality Checker**: upload a CSV, profile it, score it, report on it.

Today you build the *first slice* twice — once on vibes, once with discipline.

The point is not the code. It is noticing the difference in how each one feels.

---

## The project, in one line

> Profile and evaluate the data quality of an uploaded CSV, and output a data quality report.

Sample data lives in this module's `assets/vgsales.csv` (16,598 rows, 11 columns). Use it.

---

## Pass 1 — Vibe it

Open a fresh agent. Prompt it lazily and keep nudging:

- *"Make me a web app that checks the quality of an uploaded CSV and shows a report."*
- *"Make it nicer."* · *"Add a score."* · *"Fix that error."*

Rules: don't read the code. Don't ask for tests. Just keep going until it *feels* right.

---

## Pass 1 — Ask yourself

- How fast did something appear on screen?
- Can you explain how the score is computed?
- If one weird column broke it, where would you even look?

---

## Pass 2 — Same slice, with intent

New session. This time, prompt the agent to:

> Inspect the existing code first. Propose a plan. Keep the public interface small. Write a test before the implementation. Add no new dependencies without explaining why. Run the test suite. Summarise the trade-offs.

Same feature. Different posture.

---

## Pass 2 — Ask yourself

- Was it slower to get going?
- What do you now understand about the code that you didn't after Pass 1?
- Who was in control each time — you, or the model?

---

## Output

A short note placing your two runs on this line:

| | Vibe | Agentic |
|---|---|---|
| Your role | asked for outcomes | … |
| Tests | … | … |
| Review | … | … |
| Risk | fast mess | … |

---

## Done

You can say:

- when vibe coding is the right tool
- when it would hurt you in a team codebase
- what "controlled delegation" felt like in Pass 2
