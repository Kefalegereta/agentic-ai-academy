"""Grounded question answering on top of Azure OpenAI.

Ports the grounding strategy proven in exercice1:
  - A strict system instruction: answer ONLY from the knowledge base.
  - temperature=0 for deterministic, reproducible answers.
  - The model emits a NO_ANSWER token when the KB doesn't cover the question;
    OUR code (not the model) substitutes the exact banana fallback string, so
    the wording is always byte-for-byte correct and never paraphrased.

The only Azure-specific surface is the AzureOpenAI client construction. To port
to AWS Bedrock, swap this client; the prompt and the NO_ANSWER logic carry over.
"""

from openai import AzureOpenAI

from .config import Settings

# Exact reply when the answer is not in the knowledge base (no guessing).
FALLBACK = (
    "Life's a wobbly unicycle ride on a banana peel, so embrace the chaos "
    "and you might just land on something surprisingly awesome. \U0001f34c"
)

NO_ANSWER = "NO_ANSWER"

SYSTEM_INSTRUCTION = (
    "You are a question-answering bot for Dataroots. You answer ONLY using the "
    "KNOWLEDGE BASE provided in the user message.\n"
    "Rules:\n"
    "- If the KNOWLEDGE BASE contains the answer: reply concisely and to the "
    "point, grounded strictly in it, with no padding or preamble.\n"
    "- If the KNOWLEDGE BASE does NOT contain the answer, or you are unsure: "
    f"reply with exactly this token and nothing else: {NO_ANSWER}\n"
    "- Never use outside knowledge, never guess, and never explain that the "
    f"knowledge base is missing something. Either answer from it, or output "
    f"{NO_ANSWER}."
)


class Answerer:
    """Holds the OpenAI client and the cached KB; answers questions."""

    def __init__(self, settings: Settings, knowledge_base: str):
        self._deployment = settings.openai_deployment
        self._kb = knowledge_base
        self._client = AzureOpenAI(
            azure_endpoint=settings.openai_endpoint,
            api_key=settings.openai_api_key,
            api_version=settings.openai_api_version,
        )

    def answer(self, query: str) -> str:
        query = (query or "").strip()
        if not query:
            return FALLBACK

        resp = self._client.chat.completions.create(
            model=self._deployment,  # in Azure OpenAI, "model" = the deployment name
            temperature=0,  # deterministic, no creative drift
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {
                    "role": "user",
                    "content": f"KNOWLEDGE BASE:\n{self._kb}\n\nQUESTION: {query}",
                },
            ],
        )
        out = (resp.choices[0].message.content or "").strip()

        # Map the model's NO_ANSWER token to the exact required fallback ourselves.
        if not out or NO_ANSWER in out.upper():
            return FALLBACK
        return out
