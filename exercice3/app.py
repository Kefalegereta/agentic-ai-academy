"""
app.py  -  API del servicio RAG (FastAPI).

Expone el endpoint:
    GET /ask?query=<pregunta>   ->   {"answer": ..., "sources": [...]}

FastAPI genera ademas la documentacion interactiva en /docs automaticamente.

Arrancar en local (puerto 8000, el que espera el benchmark):
    uv run uvicorn app:app --reload
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel

import llm

app = FastAPI(
    title="QnA Bot RAG",
    description="Responde preguntas sobre una coleccion de libros usando RAG.",
    version="0.1.0",
)


# --- Modelos de respuesta ---------------------------------------------------
# Definirlos hace que /docs muestre el formato exacto de la respuesta y que
# FastAPI valide la salida. Es documentacion y contrato a la vez.
class Source(BaseModel):
    book: str
    chunk_index: int
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


# --- Endpoint principal -----------------------------------------------------
@app.get("/ask", response_model=AskResponse)
def ask(query: str = Query(..., min_length=1,
                           description="Pregunta sobre los libros indexados")):
    """Recupera los fragmentos relevantes y genera la respuesta con el LLM."""
    return llm.responder(query)


# --- Endpoint raiz (cortesia) -----------------------------------------------
@app.get("/")
def root():
    """Mensaje de bienvenida con un puntero a la documentacion."""
    return {"mensaje": "Servicio RAG activo. Documentacion en /docs",
            "ejemplo": "/ask?query=what is ale made of?"}
