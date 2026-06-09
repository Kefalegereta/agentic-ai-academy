"""
Configuracion central del servicio RAG.

Aqui viven TODOS los parametros que querras ajustar (tamano de chunk, modelo,
top-k, conexiones). La logica (ingest, retrieval, llm, app) los importa desde
aqui, asi afinas el sistema sin tocar el codigo.

Stack: embeddings BERT en local + Postgres/pgvector como vector store +
Azure OpenAI para la generacion.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carga las variables del fichero .env al entorno.
load_dotenv()

# --- Rutas del proyecto -----------------------------------------------------
# Todo cuelga de BASE_DIR: ni una ruta absoluta a mano, proyecto portable.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"   # aqui se descargan los .txt

# --- Dataset ----------------------------------------------------------------
# Para anadir libros, sumas URLs y reindexas.
BOOK_URLS = [
    "https://www.gutenberg.org/files/55602/55602-0.txt",
    "https://www.gutenberg.org/cache/epub/76262/pg76262.txt",
]

# --- Troceo (chunking) ------------------------------------------------------
# Medido en TOKENS (con tiktoken), alineado con el grupo: chunk 400 / overlap 40.
# Cada chunk avanza 400-40 = 360 tokens, lo que supone ~10% de solape.
CHUNK_SIZE = 400
CHUNK_OVERLAP = 40

# --- Embeddings (text-embedding-3-large via Azure OpenAI) -------------------
# Modelo obligatorio del ejercicio. Ventana de 8191 tokens (los chunks de 400
# caben enteros, sin truncado). Genera vectores de 3072 dimensiones; ese numero
# DEBE coincidir con la columna vector(3072) de la tabla en Postgres.
# tiktoken usa la codificacion cl100k_base para contar tokens al trocear.
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072
TIKTOKEN_ENCODING = "cl100k_base"

# --- Vector store: PostgreSQL + pgvector ------------------------------------
# La cadena de conexion la lee del .env (PG_URL). La DB del curso es
# COMPARTIDA por toda la clase, asi que usamos un nombre de tabla propio para
# no pisar los vectores de tus companeros. Cambialo si hace falta.
PG_URL = os.getenv("PG_URL")
TABLE_NAME = "rag_libros_javi"

# --- Recuperacion -----------------------------------------------------------
# Cuantos fragmentos relevantes se recuperan por pregunta. Subido a 8 para
# mejorar el recall (mas candidatos -> mas probabilidad de incluir el dato exacto).
TOP_K = 8

# --- Azure OpenAI (embeddings + generacion) ---------------------------------
# En Azure el modelo se invoca por el NOMBRE DEL DEPLOYMENT, no por el del
# modelo. Hay DOS deployments: uno para embeddings y otro para generacion.
# Confirma los nombres en Azure OpenAI Studio -> Deployments.
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

# Deployment del modelo de embeddings (text-embedding-3-large).
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"
)
# Deployment del modelo de generacion (gpt-5.4-mini).
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4-mini")
