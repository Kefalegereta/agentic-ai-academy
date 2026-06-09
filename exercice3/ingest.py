"""
ingest.py  -  Indexacion (parte OFFLINE del RAG).

Se ejecuta UNA vez (y cada vez que anades libros). Hace, en orden:

    descargar  ->  limpiar Gutenberg  ->  trocear (tiktoken)  ->  embeddings  ->  Postgres

Al terminar, la tabla en Postgres/pgvector queda poblada con, por cada chunk:
su texto, de que libro viene, y su vector de 3072 dimensiones.

Uso:
    python ingest.py
"""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
import requests
import tiktoken
from pgvector.psycopg import register_vector

import config
import db
import embeddings

# Codificador de tiktoken para contar/trocear por tokens.
_enc = tiktoken.get_encoding(config.TIKTOKEN_ENCODING)


# ---------------------------------------------------------------------------
# 1) DESCARGA
# ---------------------------------------------------------------------------
def descargar_libros() -> list[Path]:
    """Descarga cada URL a data/books/ si no esta ya en disco. Devuelve las rutas."""
    config.BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    rutas = []
    for url in config.BOOK_URLS:
        nombre = url.split("/")[-1]            # p. ej. "55602-0.txt"
        destino = config.BOOKS_DIR / nombre
        if not destino.exists():
            print(f"Descargando {url} ...")
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            destino.write_text(resp.text, encoding="utf-8")
        else:
            print(f"Ya existe, no se descarga: {destino.name}")
        rutas.append(destino)
    return rutas


# ---------------------------------------------------------------------------
# 2) LIMPIEZA DE GUTENBERG
# ---------------------------------------------------------------------------
def limpiar_gutenberg(texto: str) -> str:
    """
    Recorta la cabecera de licencia y el pie legal de Project Gutenberg.
    El contenido real esta entre las marcas:
        *** START OF THE PROJECT GUTENBERG EBOOK ... ***
        *** END OF THE PROJECT GUTENBERG EBOOK ... ***
    Si no encuentra las marcas, devuelve el texto tal cual (por seguridad).
    """
    inicio = re.search(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*",
                       texto, re.IGNORECASE)
    fin = re.search(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*",
                    texto, re.IGNORECASE)
    desde = inicio.end() if inicio else 0
    hasta = fin.start() if fin else len(texto)
    return texto[desde:hasta].strip()


# ---------------------------------------------------------------------------
# 3) TROCEO POR TOKENS (tiktoken)
# ---------------------------------------------------------------------------
def trocear(texto: str) -> list[str]:
    """
    Ventana deslizante sobre los TOKENS del texto (no caracteres).
    1) Codifica el texto a ids de token con tiktoken.
    2) Recorre con ventana de CHUNK_SIZE tokens, avanzando
       (CHUNK_SIZE - CHUNK_OVERLAP) en cada paso -> chunks consecutivos
       comparten CHUNK_OVERLAP tokens.
    3) Decodifica cada ventana de vuelta a texto para guardarla.
    """
    tokens = _enc.encode(texto)
    size = config.CHUNK_SIZE
    paso = config.CHUNK_SIZE - config.CHUNK_OVERLAP
    chunks = []
    for i in range(0, len(tokens), paso):
        ventana = tokens[i:i + size]
        if not ventana:
            continue
        trozo = _enc.decode(ventana).strip()
        if trozo:
            chunks.append(trozo)
    return chunks


# ---------------------------------------------------------------------------
# 4) CONEXION Y ESQUEMA EN POSTGRES
# ---------------------------------------------------------------------------
def preparar_tabla(conn: psycopg.Connection) -> None:
    """
    Activa pgvector y (re)crea la tabla desde cero.
    El DROP hace que reindexar sea idempotente: cada ejecucion deja la tabla
    limpia y coherente con el contenido actual de los libros.
    """
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

    # register_vector necesita que la extension exista ya: por eso va despues.
    register_vector(conn)

    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {config.TABLE_NAME};")
        cur.execute(f"""
            CREATE TABLE {config.TABLE_NAME} (
                id          BIGSERIAL PRIMARY KEY,
                book        TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content     TEXT NOT NULL,
                embedding   VECTOR({config.EMBEDDING_DIM}) NOT NULL
            );
        """)
    conn.commit()


def crear_indice(conn: psycopg.Connection) -> None:
    """
    Indice ivfflat para acelerar la busqueda por coseno. OJO: pgvector solo
    indexa hasta ~2000 dimensiones, y nuestros vectores tienen 3072, asi que
    aqui FALLARA y seguiremos con scan secuencial (perfecto para 2 libros).
    Lo dejamos para que el codigo escale si algun dia reduces dimensiones.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {config.TABLE_NAME}_emb_idx
                ON {config.TABLE_NAME}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
        conn.commit()
        print("Indice ivfflat creado.")
    except Exception as e:  # noqa: BLE001
        conn.rollback()
        print(f"Aviso: sin indice ({e}). Se usara scan secuencial.")


# ---------------------------------------------------------------------------
# 5) PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------
def main() -> None:
    # a) Descargar y trocear todos los libros, recordando de cual viene cada chunk.
    libros = descargar_libros()
    registros: list[tuple[str, int, str]] = []   # (book, chunk_index, content)
    for ruta in libros:
        texto = limpiar_gutenberg(ruta.read_text(encoding="utf-8"))
        trozos = trocear(texto)
        print(f"{ruta.name}: {len(trozos)} chunks")
        for idx, trozo in enumerate(trozos):
            registros.append((ruta.name, idx, trozo))

    print(f"Total de chunks: {len(registros)}")

    # b) Calcular embeddings via Azure OpenAI (text-embedding-3-large).
    print("Generando embeddings con Azure OpenAI ...")
    textos = [r[2] for r in registros]
    vectores = embeddings.embed_texts(textos)

    # c) Guardar todo en Postgres.
    print("Conectando a Postgres ...")
    with db.connect() as conn:
        preparar_tabla(conn)
        with conn.cursor() as cur:
            cur.executemany(
                f"""INSERT INTO {config.TABLE_NAME}
                        (book, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s);""",
                [
                    (book, idx, content, vec)
                    for (book, idx, content), vec in zip(registros, vectores)
                ],
            )
        conn.commit()
        crear_indice(conn)

    print(f"Listo. Tabla '{config.TABLE_NAME}' poblada con {len(registros)} chunks.")


if __name__ == "__main__":
    main()
