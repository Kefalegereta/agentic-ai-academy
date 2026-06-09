"""
embeddings.py  -  Generacion de vectores con text-embedding-3-large (Azure).

Modulo COMPARTIDO entre indexacion (cada chunk) y consulta (la pregunta).
Es importante que ambos usen exactamente el mismo modelo: si indexas con un
modelo y consultas con otro, los vectores no son comparables y el retrieval
falla. Por eso vive en un unico sitio.
"""

from __future__ import annotations

from openai import AzureOpenAI

import config

# Cliente unico de Azure OpenAI, reutilizado en todas las llamadas.
_client = AzureOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
)


def embed_texts(textos: list[str], batch_size: int = 64) -> list[list[float]]:
    """
    Devuelve un vector por cada texto de entrada.
    Se envia en lotes (batch_size) para no superar los limites de la API en una
    sola peticion. Si llegaras a topar con un limite de tokens por peticion,
    baja batch_size.
    """
    vectores: list[list[float]] = []
    for i in range(0, len(textos), batch_size):
        lote = textos[i:i + batch_size]
        resp = _client.embeddings.create(
            model=config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input=lote,
        )
        # resp.data viene en el mismo orden que el lote enviado.
        vectores.extend(d.embedding for d in resp.data)
    return vectores


def embed_query(texto: str) -> list[float]:
    """Embebe una sola pregunta. Atajo sobre embed_texts para la fase de consulta."""
    return embed_texts([texto])[0]
