"""
llm.py  -  Generacion de la respuesta con gpt-5.4-mini (Azure OpenAI).

Une las dos mitades del RAG:
    1) pide a retrieval.py los chunks relevantes,
    2) los mete como CONTEXTO en el prompt,
    3) gpt-5.4-mini redacta la respuesta basandose solo en ese contexto.

Devuelve {"answer": ..., "sources": [...]}.

Uso suelto (RAG completo en la terminal, sin API):
    uv run python llm.py "what is ale made of?"
"""

from __future__ import annotations

from openai import AzureOpenAI

import config
import retrieval

# Cliente de Azure OpenAI para chat (la generacion).
_client = AzureOpenAI(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
)

# Instruccion de sistema: el modelo debe ceñirse al contexto y no inventar.
# Esto es lo que diferencia un RAG de un chatbot normal: respondemos con los
# libros, no con el conocimiento general del modelo.
_SYSTEM = (
    "You are a helpful assistant that answers questions about a collection of "
    "books. Use ONLY the provided context to answer; never use outside "
    "knowledge. If the answer is not in the context, say you don't know based "
    "on the available books. Answer ONLY what the question asks: be concise, "
    "stick to the specific facts requested, and do NOT add extra details or "
    "claims beyond what is needed, even if they appear in the context. "
    "Answer in the same language as the question."
)


def _formatear_contexto(chunks: list[dict]) -> str:
    """Junta los chunks en un bloque de texto, etiquetando su origen."""
    bloques = [f"[{c['book']} #{c['chunk_index']}]\n{c['content']}" for c in chunks]
    return "\n\n---\n\n".join(bloques)


def responder(pregunta: str, top_k: int | None = None) -> dict:
    """Recupera contexto, genera la respuesta y devuelve answer + sources."""
    chunks = retrieval.buscar(pregunta, top_k)
    if not chunks:
        return {"answer": "No hay datos indexados para responder.", "sources": []}

    mensajes = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user",
         "content": f"Context:\n{_formatear_contexto(chunks)}\n\nQuestion: {pregunta}"},
    ]

    resp = _client.chat.completions.create(
        model=config.AZURE_OPENAI_DEPLOYMENT,   # nombre del DEPLOYMENT en Azure
        messages=mensajes,
        temperature=0,                          # 0 = respuestas fieles, no creativas
        seed=42,                                # reproducibilidad: misma entrada -> misma salida
    )
    answer = resp.choices[0].message.content.strip()

    # Fuentes: de que libro y chunk salio cada fragmento usado como contexto.
    sources = [
        {"book": c["book"], "chunk_index": c["chunk_index"],
         "score": round(c["score"], 4)}
        for c in chunks
    ]
    return {"answer": answer, "sources": sources}


# Permite probar el RAG completo desde la terminal, sin levantar la API.
if __name__ == "__main__":
    import sys

    pregunta = " ".join(sys.argv[1:]) or "What is ale made of?"
    resultado = responder(pregunta)
    print("\nRESPUESTA:\n", resultado["answer"])
    print("\nFUENTES:")
    for s in resultado["sources"]:
        print(f"  - {s['book']} #{s['chunk_index']} (score {s['score']})")
