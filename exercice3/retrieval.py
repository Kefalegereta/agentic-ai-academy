"""
retrieval.py  -  Recuperacion (parte que corre EN CADA pregunta).

Dada una pregunta:
    1) la embebe con el MISMO modelo que los chunks (text-embedding-3-large),
    2) busca en Postgres los TOP_K chunks mas parecidos por distancia coseno,
    3) los devuelve con su libro y posicion de origen (para citar fuentes).

Nota: probamos una version hibrida (semantica + BM25/full-text con RRF). En este
dataset mejoraba el recall de cifras exactas pero metia ruido en las preguntas
conceptuales y bajaba la nota global, asi que nos quedamos con la semantica pura.

Uso suelto (para probar la recuperacion sin la API ni el LLM):
    uv run python retrieval.py "what is ale made of?"
"""

from __future__ import annotations

import config
import db
import embeddings


def _vec_literal(vector: list[float]) -> str:
    """Convierte el vector de Python al literal de pgvector: '[0.1,0.2,...]'."""
    return "[" + ",".join(map(str, vector)) + "]"


def buscar(pregunta: str, top_k: int | None = None) -> list[dict]:
    """Devuelve los top_k chunks mas relevantes para la pregunta."""
    k = top_k or config.TOP_K
    vector = _vec_literal(embeddings.embed_query(pregunta))

    # <=> es la DISTANCIA coseno (0 = identico). Ordenamos ascendente y damos
    # un 'score' legible como 1 - distancia (1 = identico) para mostrarlo.
    sql = f"""
        SELECT book,
               chunk_index,
               content,
               1 - (embedding <=> %(v)s::vector) AS score
        FROM {config.TABLE_NAME}
        ORDER BY embedding <=> %(v)s::vector
        LIMIT %(k)s;
    """

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"v": vector, "k": k})
            filas = cur.fetchall()

    return [
        {"book": book, "chunk_index": idx, "content": contenido, "score": float(score)}
        for (book, idx, contenido, score) in filas
    ]


# Permite probar la recuperacion de forma aislada desde la terminal.
if __name__ == "__main__":
    import sys

    pregunta = " ".join(sys.argv[1:]) or "What is ale made of?"
    print(f"Pregunta: {pregunta}\n")
    for r in buscar(pregunta):
        print(f"[{r['book']} #{r['chunk_index']}  score={r['score']:.3f}]")
        print(r["content"][:220].strip(), "...\n")
