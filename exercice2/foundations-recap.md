---
marp: true
theme: dataroots
paginate: true
size: 16:9
---

<!-- _class: title -->
<!-- _paginate: skip -->

# Azure QnA bot

## Foundations recap

---

## The brief

Rebuild this morning's QnA bot, this time on Azure.

- Same Dataroots knowledge base, already sitting in an Azure Blob Storage container (read-only access is enough)
- The whole stack runs **inside Azure** this time
- Portable enough to redeploy on AWS later without a rewrite

When the answer isn't in the knowledge base, the bot replies:

> Life's a wobbly unicycle ride on a banana peel, so embrace the chaos and you might just land on something surprisingly awesome. 🍌

Not a hallucinated guess.

---

## The HTTP contract

Single `GET` endpoint that accepts a `query` parameter, returns JSON with one `answer` field, and ships browsable API documentation (OpenAPI / Swagger UI).

```bash
curl --get \
    --data-urlencode "query=What does the fox say?" \
    https://[your-deployment-url]
```

```json
{"answer": "Ring-ding-ding-ding-dingeringeding!"}
```

---

## Hard constraints

- **Everything runs inside Azure.** No direct calls to Gemini, OpenAI, Anthropic, etc. Source files only come from Azure.
- **Data and resources stay in the EU.** Every resource lives in an EU region (West Europe, North Europe, Sweden Central, France Central).

Beyond those two, you choose the shape.

---

## When you're done

Show me:

- A link to a **git repo** containing the project (personal GitHub/GitLab is fine)
- The deployed endpoint URL (and the API docs URL)
- A few notes on challenges, tradeoffs, and Azure gotchas you ran into

> 💡 **Be pragmatic.** We're not after perfect code or fancy retrieval logic. We want a working Azure deployment, packaged so we could move it to AWS if needed.

---

<!-- _class: section -->

# Action time

Sketch solution, pressure-test together, then code.

---

## Step 1: Sketch the architecture (10 min)

Before any code, sketch the solution **as a group**.

- One diagram per group (Excalidraw, whiteboard or large sheet of paper)
- Name the Azure services you'll commit to (no "some compute" or "some LLM")
- Show how data flows: `client → endpoint → LLM → blob`
- Make it detailed enough to walk a single `curl` request through end-to-end

Catch the wrong turns now, before you sink hours into code.

---

## Step 2: Rotate and critique (15 min)

One spokesperson stays at each table. Everyone else rotates to another group.

- **~5 min**: spokesperson presents their group's sketch to the visitors
- **~5 min**: visitors critique. Where would this break? What's missing? What feels over-engineered?
- **~5 min**: visitors return home; spokesperson reports back what landed

Stress-test each other's designs before anyone writes code.

---

## Step 3: Pressure-test against the guiding questions (10 min)

Walk your sketch against each question. If you can't answer one out loud, that's where you focus first.

- How will you call an LLM without leaving Azure?
- How do you make sure no data leaves the EU?
- How will you manage Python dependencies so future-you can reproduce the project?
- How will you expose the application over HTTP, with browsable API documentation?
- How will you package the code so it runs the same way locally, in Azure, and (later) on AWS?
- How will you deploy it so it accepts public GET requests and returns JSON?
- Which parts of the code touch Azure-specific APIs? How easy would it be to swap them for an AWS equivalent?
- How will you make the bot's behavior as predictable and reproducible as possible?

---

## What's already there for you

In your Azure subscription, an EU resource group is waiting:

- **`rg-agentic-ai-academy`** (EU region)
- Inside it: a storage account **`dragenticaiacademy`** holding the source markdown of the Dataroots website

Everything you build deploys into the same resource group.

---

<!-- _class: lead -->

# Good luck. ✨
