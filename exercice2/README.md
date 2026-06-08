# Azure QnA Bot — Agentic AI Academy (exercice 2)

A question-answering bot about Dataroots, rebuilt entirely on **Azure**. Same
behavior as exercice 1 (grounded answers, exact fallback when the answer isn't
in the knowledge base), but the whole stack runs inside Azure and is packaged so
it could move to AWS without a rewrite.

## HTTP contract

```bash
curl --get \
  --data-urlencode "query=What is Dataroots?" \
  https://<your-deployment-url>/
# -> {"answer": "..."}
```

Browsable API docs (Swagger UI) at `https://<your-deployment-url>/docs`.

When the answer is not in the knowledge base, the bot returns, verbatim:

> Life's a wobbly unicycle ride on a banana peel, so embrace the chaos and you might just land on something surprisingly awesome. 🍌

## Architecture

```
Client ──HTTPS GET ?query=──> Container Apps (FastAPI)
                                 │  reads .md (once, at startup)
                                 ├──────────────> Blob Storage (dragenticaiacademy / day1-foundations-recap)
                                 │  prompt + KB
                                 └──────────────> Azure OpenAI (openai-dr-bot / gpt-4.1-mini)
```

| Concern        | Choice                                              |
| -------------- | --------------------------------------------------- |
| Compute        | Azure Container Apps (env `cae-agentic-ai-academy`) |
| Image registry | Azure Container Registry (`acragenticaiacademy`)    |
| LLM            | Azure OpenAI, deployment `gpt-4.1-mini`             |
| Knowledge base | Azure Blob Storage (`day1-foundations-recap`)       |
| API            | FastAPI + Uvicorn, GET `/` → JSON, Swagger at `/docs` |
| Dependencies   | uv (locked via `uv.lock` for reproducibility)       |
| Region         | West Europe (all resources stay in the EU)          |

### Grounding strategy (ported from exercice 1)

The knowledge base is small enough to fit in the model's context window, so we
inject the whole thing into the prompt (no vector search). Determinism comes
from `temperature=0` plus a strict system instruction. Crucially, the model
emits a `NO_ANSWER` token when the KB doesn't cover the question, and **our
code** substitutes the exact fallback string, so the wording is never
paraphrased by the model.

## Run locally

```bash
cp .env.example .env        # then fill in the two keys (see below)
uv lock                     # resolve + lock dependencies
uv run uvicorn app.main:app --reload --port 8000
```

Test:

```bash
curl --get --data-urlencode "query=What is Dataroots?" http://localhost:8000/
```

### Getting the two keys for `.env`

```bash
# Azure OpenAI key
az cognitiveservices account keys list \
  -n openai-dr-bot -g rg-agentic-ai-academy --query key1 -o tsv

# Storage account key
az storage account keys list \
  -n dragenticaiacademy -g rg-agentic-ai-academy --query "[0].value" -o tsv
```

`.env` is gitignored. Never commit real keys.

## Deployed endpoint

- **Endpoint:** https://qna-bot.yellowsmoke-971f835a.westeurope.azurecontainerapps.io/
- **API docs (Swagger):** https://qna-bot.yellowsmoke-971f835a.westeurope.azurecontainerapps.io/docs

```bash
curl --get --data-urlencode "query=What is Dataroots?" \
  https://qna-bot.yellowsmoke-971f835a.westeurope.azurecontainerapps.io/
```

## How it was deployed

Everything lives in `rg-agentic-ai-academy` (West Europe), reusing resources that
were already provisioned: the registry `acragenticaiacademy`, the Container Apps
environment `cae-agentic-ai-academy`, the Azure OpenAI account `openai-dr-bot`,
and the storage account `dragenticaiacademy`.

```bash
# 1. Build the image in the cloud (amd64) and push it to ACR
az acr build --registry acragenticaiacademy \
  --image azure-qna-bot:v1 --platform linux/amd64 .

# 2. Create the Container App (secrets injected as container secrets)
az containerapp create \
  --name qna-bot --resource-group rg-agentic-ai-academy \
  --environment cae-agentic-ai-academy \
  --image acragenticaiacademy.azurecr.io/azure-qna-bot:v1 \
  --target-port 8000 --ingress external \
  --registry-server acragenticaiacademy.azurecr.io \
  --secrets openai-key="$OPENAI_KEY" storage-key="$STORAGE_KEY" \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=https://openai-dr-bot.openai.azure.com/ \
    AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini \
    AZURE_OPENAI_API_VERSION=2024-10-21 \
    AZURE_STORAGE_ACCOUNT=dragenticaiacademy \
    AZURE_STORAGE_CONTAINER=day1-foundations-recap \
    AZURE_OPENAI_API_KEY=secretref:openai-key \
    AZURE_STORAGE_KEY=secretref:storage-key \
  --min-replicas 1 --max-replicas 2

# 3. Point the registry at admin credentials (see gotcha #2 below)
az containerapp registry set -n qna-bot -g rg-agentic-ai-academy \
  --server acragenticaiacademy.azurecr.io \
  --username "$ACR_USER" --password "$ACR_PASS"

# Redeploy a new image build later with:
az acr build --registry acragenticaiacademy --image azure-qna-bot:v2 --platform linux/amd64 .
az containerapp update -n qna-bot -g rg-agentic-ai-academy \
  --image acragenticaiacademy.azurecr.io/azure-qna-bot:v2
```

## Portability to AWS

Only two files touch Azure-specific SDKs: `app/kb.py` (Blob) and `app/llm.py`
(Azure OpenAI). Everything else (FastAPI app, config, Dockerfile) is
cloud-neutral. To run on AWS: swap `kb.py` for an S3 reader (boto3), swap
`llm.py` for Bedrock, and deploy the same image on ECS / App Runner. Credentials
already come from environment variables, which map directly to AWS task
definitions / Secrets Manager.

## Challenges, tradeoffs & Azure gotchas

**Tenant / subscription mix-up.** `az login` defaulted to the wrong tenant
(`talan.com` / "ABO AZURE PARTNER GOLD"). The academy resources live in the
`dataroots.io` tenant under "Microsoft Azure Sponsorship 2". Had to
`az account set --subscription <id>` before anything was visible. Easy to lose
20 minutes here if you don't check `az account show` first.

**ACR pull without rights to assign roles (the big one).** `az containerapp
create` tries to wire up the image pull using a managed identity, which requires
creating an `acrpull` role assignment. My account lacks
`Microsoft.Authorization/roleAssignments/write` on the resource group, so that
step failed, and Container Apps silently fell back to Microsoft's
`mcr.microsoft.com/k8se/quickstart` placeholder image. The symptom was a
crash-loop with `Probe of StartUp failed` and a console log saying
`Listening on :80` (the placeholder), not our app. Fix: enable the ACR admin
user and attach username/password credentials with
`az containerapp registry set`, then `az containerapp update --image <ours>`.
Admin credentials need no role assignment, so this works even with limited RBAC.

**Apple Silicon vs Container Apps architecture.** Building locally on an M-series
Mac produces an `arm64` image; Azure Container Apps runs `amd64`. Rather than
fight with `docker buildx`, I used `az acr build --platform linux/amd64`, which
builds in the cloud and pushes in one step, no local Docker needed.

**Azure OpenAI: deployment name, not model name.** You call the *deployment*
(`gpt-4.1-mini`), not the public model id. Picked `gpt-4.1-mini` over the newer
`gpt-5.4-mini` because the grounding strategy depends on `temperature=0`, and the
4.1 family honours it cleanly.

**Secrets handling.** Used API keys via environment variables / container secrets
rather than managed identity. This is the pragmatic and the more *portable*
choice (env vars map 1:1 to AWS), and given the role-assignment limitation above,
managed identity wasn't even available. Tradeoff: keys are secrets that must be
rotated and kept out of git (`.env` is gitignored).

**Scale-to-zero vs warm.** Set `--min-replicas 1` so the demo responds instantly.
For cost, set it to `0` (scale-to-zero) and accept a cold start on the first
request after idle.

**EU residency.** Every resource is in West Europe, satisfying the brief's
constraint that data and compute stay in the EU.
