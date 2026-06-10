"""Ingestion del CSV subido.

Supuestos fijados (CONTEXT.md): primera fila = cabeceras, delimitador coma,
UTF-8 con fallback tolerante, limite ~50 MB. Devuelve un DataFrame de strings
crudos (sin que pandas interprete nulos ni tipos): toda esa logica vive en el
profiler, para mantener las dimensiones desacopladas.
"""
from __future__ import annotations

import io

import pandas as pd

MAX_BYTES = 50 * 1024 * 1024  # ~50 MB


class IngestError(ValueError):
    """Fichero invalido o ilegible. El mensaje es apto para mostrar al usuario."""


def parse_csv(data: bytes, filename: str) -> pd.DataFrame:
    if not data:
        raise IngestError("El fichero esta vacio.")
    if len(data) > MAX_BYTES:
        mb = len(data) / (1024 * 1024)
        raise IngestError(f"El fichero pesa {mb:.0f} MB; el limite es 50 MB.")

    # UTF-8 primero; si falla, latin-1 (nunca lanza) como fallback tolerante.
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")

    try:
        df = pd.read_csv(
            io.StringIO(text),
            dtype=str,            # todo como string: el profiler infiere tipos
            keep_default_na=False,  # no convertir 'NA'/'' a NaN: lo hacemos nosotros
            na_filter=False,
            skip_blank_lines=True,
        )
    except pd.errors.ParserError as exc:
        raise IngestError(f"No se pudo parsear el CSV: {exc}") from exc
    except pd.errors.EmptyDataError as exc:
        raise IngestError("El fichero no contiene datos.") from exc

    if df.shape[1] == 0:
        raise IngestError("No se detectaron columnas (falta la fila de cabeceras?).")
    if df.shape[0] == 0:
        raise IngestError("El CSV tiene cabeceras pero ninguna fila de datos.")

    # Cabeceras vacias o duplicadas son senal de fichero sin cabecera real.
    cols = list(df.columns)
    if any(str(c).strip() == "" or str(c).startswith("Unnamed:") for c in cols):
        raise IngestError("Hay columnas sin nombre; revisa que la primera fila sean cabeceras.")

    return df
