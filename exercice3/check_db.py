"""
check_db.py  -  Comprobacion rapida de que la indexacion funciono.

Cuenta cuantos chunks hay en la tabla, de cuantos libros, y muestra un ejemplo.
Uso:
    uv run python check_db.py
"""

import config
import db

with db.connect() as conn:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*), COUNT(DISTINCT book) FROM {config.TABLE_NAME};"
        )
        n_chunks, n_libros = cur.fetchone()
        print(f"Chunks en la tabla '{config.TABLE_NAME}': {n_chunks}")
        print(f"Libros distintos: {n_libros}")

        cur.execute(
            f"""SELECT book, chunk_index, LEFT(content, 200)
                FROM {config.TABLE_NAME} ORDER BY id LIMIT 1;"""
        )
        book, idx, muestra = cur.fetchone()
        print(f"\nEjemplo -> {book} [chunk {idx}]:\n{muestra}...")
