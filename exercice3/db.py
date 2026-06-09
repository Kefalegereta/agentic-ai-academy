"""
db.py  -  Conexion a PostgreSQL.

Centraliza la conexion para que ingest.py y retrieval.py la reutilicen.

Detalle importante con Azure: libpq (la libreria por debajo de psycopg) intenta
por defecto negociar cifrado GSSAPI antes que nada. El servidor de Azure corta
la conexion al recibir ese saludo, lo que produce el error
"server closed the connection unexpectedly". Desactivando GSSAPI
(gssencmode=disable) la conexion va por SSL normal y funciona.
"""

import psycopg

import config


def connect() -> psycopg.Connection:
    """Abre una conexion a Postgres con GSSAPI desactivado (necesario en Azure)."""
    conninfo = config.PG_URL
    if "gssencmode" not in conninfo:
        sep = "&" if "?" in conninfo else "?"
        conninfo = f"{conninfo}{sep}gssencmode=disable"
    return psycopg.connect(conninfo)
