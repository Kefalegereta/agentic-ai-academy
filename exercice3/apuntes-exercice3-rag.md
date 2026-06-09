# Apuntes técnicos: QnA Bot RAG (Exercice 3)

Servicio RAG que responde preguntas sobre una colección de libros (.txt de Project Gutenberg) y se evalúa con un benchmark de la profesora. Construido desde cero en la Agentic AI Academy (Día 2).

## Qué hace, en una frase

Indexa los libros una vez (trocear, embeber, guardar en Postgres) y, en cada pregunta, recupera los fragmentos relevantes y se los pasa a un LLM para que redacte la respuesta basándose solo en ellos. Eso es RAG: el modelo nunca ve los libros enteros, solo los trozos pertinentes, así que escala aunque la colección crezca y puede citar fuentes.

## Arquitectura y flujo de datos

El sistema tiene dos mitades, igual que en el diagrama del ejercicio.

**Indexación (offline, se corre una vez):**

```
libros .txt  ->  limpiar cabecera Gutenberg  ->  trocear (tiktoken)
             ->  embeddings (text-embedding-3-large)  ->  Postgres + pgvector
```

**Consulta (en cada pregunta):**

```
pregunta  ->  embeber pregunta  ->  búsqueda por similitud coseno en Postgres
          ->  top-K fragmentos  ->  prompt con contexto  ->  gpt-5.4-mini  ->  respuesta + fuentes
```

## Stack

Python 3.11 y UV como gestor de dependencias. FastAPI para la API. PostgreSQL con la extensión pgvector como vector store (portable, corre en cualquier nube o en local). Azure OpenAI para los dos modelos: `text-embedding-3-large` (embeddings) y `gpt-5.4-mini` (generación). tiktoken para el troceo por tokens. psycopg (v3) como cliente de Postgres.

## Estructura de ficheros

```
exercice3/
├── pyproject.toml      # dependencias (UV)
├── .env                # credenciales (NO se sube a git)
├── .env.example        # plantilla de variables
├── config.py           # todos los parámetros en un sitio
├── db.py               # conexión a Postgres (con el fix de GSSAPI)
├── embeddings.py       # embeddings vía Azure (compartido index/consulta)
├── ingest.py           # script de indexación
├── retrieval.py        # búsqueda por similitud
├── llm.py              # prompt + generación
├── app.py              # API FastAPI (GET /ask, /docs)
├── check_db.py         # verificación rápida de la indexación
└── questions.yaml      # set de preguntas del benchmark
```

La lógica está separada por responsabilidad: `config.py` concentra los parámetros, `embeddings.py` y `db.py` son piezas compartidas, y cada paso del RAG (ingest, retrieval, llm) vive en su fichero. La API (`app.py`) es fina porque solo expone por HTTP lo que ya hacen los demás.

## Decisiones técnicas y el porqué

**Troceo por tokens con tiktoken, chunk 400 / overlap 40.** Se mide en tokens (no caracteres) usando la codificación `cl100k_base`. Cada chunk avanza 360 tokens (400 menos 40), lo que da un solape de ~10%. El solape evita cortar una idea justo en la frontera entre dos trozos. Estos números se alinearon con los del grupo de trabajo para que los resultados fueran comparables.

**Embeddings: `text-embedding-3-large` vía Azure.** Modelo obligatorio del ejercicio. Su ventana es de 8191 tokens, así que los chunks de 400 caben enteros sin truncado. Genera vectores de **3072 dimensiones**, número que tiene que cuadrar con la columna `vector(3072)` de la tabla. Importante: indexar y consultar deben usar el mismo modelo, por eso vive en un único módulo (`embeddings.py`); si embebes con un modelo y consultas con otro, los vectores no son comparables y la recuperación falla.

**Vector store: PostgreSQL + pgvector.** Más escalable y de producción que una solución en memoria, y portable (no ata a Azure). La base de datos del curso es compartida por toda la clase, así que se usó un nombre de tabla propio (`rag_libros_javi`) para no pisar los vectores de los compañeros. Se reindexa de forma idempotente con un `DROP TABLE IF EXISTS` al principio.

**Sin índice vectorial.** pgvector solo indexa hasta ~2000 dimensiones, y los vectores tienen 3072, así que no se puede crear índice ivfflat ni hnsw. No es problema: con dos libros (~1000 chunks) la búsqueda secuencial es instantánea. Si en el futuro se quisiera índice, se reducirían dimensiones con el parámetro `dimensions` de la API.

**TOP_K = 8.** Cuántos fragmentos se recuperan por pregunta. Se subió de 4 a 8 para mejorar el recall: más candidatos, más probabilidad de incluir el dato exacto. Fue clave para acertar preguntas de detalle.

**Generación con `temperature=0` y `seed=42`.** Temperatura 0 para respuestas fieles al contexto, no creativas. La seed fija la salida ante la misma entrada: reproducibilidad, un takeaway de LLMOps. Estabilizó el resultado del benchmark por nuestro lado.

**Prompt anclado al contexto.** El system prompt instruye al modelo a usar solo el contexto, decir "no lo sé" si la respuesta no está, y no añadir datos de más. Eso es lo que convierte un chatbot normal en un RAG: responde con los libros, no con su conocimiento general, y por eso no alucina sobre temas fuera de la colección.

## Búsqueda híbrida: probada y descartada

Se implementó una versión híbrida (semántica + full-text/BM25 de Postgres, fusionadas con Reciprocal Rank Fusion) para atacar las preguntas de cifras y nombres exactos. Resultado medido: **bajó la nota de 9/10 a 7/10**. Ganaba recall en una pregunta concreta, pero a cambio arrastraba fragmentos tangenciales que hacían que el modelo añadiera afirmaciones de más en las preguntas conceptuales, y el juez las penalizaba. Además, el `ts_rank` de Postgres no pondera por rareza del término (no es BM25 real con IDF), así que la palabra discriminante no se imponía. Conclusión: en este dataset, más recuperación no era mejor recuperación. Se revirtió a la búsqueda semántica pura. Decisión tomada con datos, no por intuición.

## Cómo correrlo

```bash
# 1. Instalar dependencias
uv sync

# 2. Crear el .env (copiar la plantilla y rellenar credenciales)
cp .env.example .env

# 3. Indexar los libros (una vez)
uv run python ingest.py
uv run python check_db.py        # verificar: debe haber ~1000 chunks de 2 libros

# 4. Arrancar la API (puerto 8000)
uv run uvicorn app:app --port 8000

# 5. Probar
#    Navegador: http://127.0.0.1:8000/docs
#    o:         http://127.0.0.1:8000/ask?query=what is ale made of?

# 6. Benchmark (en otra terminal, con la API encendida)
set -a; source .env; set +a
uv run bench.py http://127.0.0.1:8000 -v
```

## Problemas que aparecieron y cómo se resolvieron

**Conexión a Postgres fallaba con VPN.** El firewall de la base de datos compartida no permitía la IP de salida de la VPN. Solución: desconectar la VPN y usar la wifi del aula (cuya IP sí está permitida).

**`server closed the connection unexpectedly`.** Síntoma típico de Azure Postgres con psycopg. Se centralizó la conexión en `db.py` añadiendo `gssencmode=disable`, que evita que libpq intente primero cifrado GSSAPI. (En este caso la causa raíz era la VPN, pero el ajuste es buena práctica con Azure.)

**El benchmark daba 404 en casi todas las preguntas.** Había un servidor `http.server` fantasma de una prueba anterior escuchando en `localhost` por IPv6 (`::1`), mientras uvicorn escuchaba por IPv4 (`127.0.0.1`). El navegador funcionaba (iba por IPv4) pero el benchmark usaba `localhost` y caía en el fantasma. Solución: matar el proceso fantasma (`lsof -nP -iTCP:8000 -sTCP:LISTEN` para localizarlo, luego `kill PID`) y apuntar el benchmark a `127.0.0.1`.

**El benchmark fallaba con `--reload`.** Ese flag reinicia el servidor al detectar cambios en archivos (incluidos los `.pyc`), y mientras reinicia las peticiones caen. Para evaluar se arranca sin `--reload`. Recordar reiniciar uvicorn a mano tras cada cambio de código.

## Resultados del benchmark

El benchmark lanza 10 preguntas contra `/ask` y un LLM juez compara cada respuesta con una de referencia. Recorrido de la nota:

- Arranque con TOP_K=4: 7/10.
- Subir TOP_K a 8 y apretar el prompt: **9/10**.
- Probar híbrida con RRF: bajó a 7/10 (descartada).
- Volver a semántica y añadir seed: estable en **8-9/10**.

Los fallos restantes no son bugs del sistema:

- **Q4 (porcentaje de alcohol del whisky irlandés):** único fallo de contenido real. El libro contiene cifras ambiguas (una en tabla, otra en prosa) y el modelo elige la que no coincide con la referencia.
- **Q8 (argumentos contra las bebidas de malta):** depende del juez. La respuesta del bot es estable (gracias a la seed), pero el evaluador a veces la penaliza por incluir detalles que sí están en el libro pero no en la respuesta de referencia. Es severidad/variabilidad del juez, no un fallo del bot.

Lección de fondo: el resultado de un benchmark con LLM-as-judge es ruidoso. Un `ERROR` (el juez se cae, p. ej. por el filtro de contenido de Azure) no es lo mismo que un `FAIL` (tu sistema responde mal). Conviene correrlo varias veces y leer los motivos, no solo el número.
