# Día 2 — QnA Bot v2 (RAG sobre colección de libros)

## 1. Qué hay que construir (en una frase)
Un servicio web que responde preguntas sobre una colección de libros que **crece**. Como los textos ya no caben en el contexto del modelo, se usa **RAG** (Retrieval-Augmented Generation): se indexan los libros una vez, y en cada pregunta se recuperan solo los trozos relevantes y se le pasan al LLM para que redacte la respuesta.

**Dataset:** 2 libros de dominio público sobre historia de la cerveza (~265.000 palabras).

**Requisitos del enunciado:**
- Endpoint `GET /ask?query=<pregunta>` → `{"answer": "..."}`
- Extra deseable: devolver también las fuentes → `{"answer": "...", "sources": [...]}`
- Generación con el modelo **`gpt-5.4-mini`**
- Docs auto-generadas en **`/docs`** (Swagger de FastAPI)
- Componentes **portables** (que funcionen fuera de Azure / en local) → por eso vector store local tipo **Chroma**, nada de atarse a un servicio cloud propietario
- Arrancable en local: `uvicorn app:app --reload`

## 2. La arquitectura en palabras (dos flujos)

**A) Indexación (offline, una vez · se repite cuando se añaden libros)**
1. Colección de libros (.txt) — la fuente de conocimiento, que va creciendo.
2. **Chunking / troceado**: partir cada libro en fragmentos manejables (p. ej. ~500-1000 tokens con solapamiento), porque no se puede embeber un libro entero de golpe.
3. **Modelo de embeddings**: convierte cada fragmento en un vector (lista de números que captura su significado).
4. **Vector store (Chroma)**: guarda los vectores + el texto original de cada fragmento.

**B) Consulta (en vivo, cada vez que llega una pregunta)**
1. Usuario → `GET /ask?query=...` (HTTP) contra el servicio **FastAPI**.
2. FastAPI convierte la pregunta en un vector con **el mismo modelo de embeddings**.
3. **Búsqueda en el vector store**: recupera los *top-k* fragmentos más parecidos a la pregunta. *(Opcional/avanzado: combinar con búsqueda por palabra clave **BM25** → búsqueda híbrida, para acertar tanto con nombres de marca exactos como con descripciones vagas de sabor.)*
4. **Construir el prompt**: pregunta + fragmentos recuperados como contexto.
5. Enviar al **LLM `gpt-5.4-mini`**.
6. El LLM devuelve la respuesta redactada.
7. FastAPI responde `{"answer": "...", "sources": [...]}` en JSON. Docs en `/docs`.

> Idea clave: el LLM no "sabe" de los libros; solo redacta a partir de los fragmentos que el sistema le da. La calidad depende de recuperar buenos fragmentos.

---

## 3. Prompt para generar el diagrama (pegar en ChatGPT con generación de imagen)

> Copia todo el bloque siguiente en ChatGPT (modelo con generación de imágenes) para obtener un esquema con el mismo estilo que el de ayer.

```
Crea un diagrama de arquitectura técnica, limpio y profesional, en formato horizontal (16:9), estilo infografía moderna con fondo blanco, cajas redondeadas con iconos y colores suaves, flechas claras y numeradas. Mismo estilo visual que un diagrama de arquitectura de software corporativo.

TÍTULO (arriba, grande y en negrita): "QnA Bot v2 — Arquitectura RAG"
SUBTÍTULO: "Un servicio que indexa una colección de libros y responde preguntas con IA, recuperando solo los fragmentos relevantes."

Divide el lienzo en DOS ZONAS claramente etiquetadas:

ZONA 1 (arriba) — "INDEXACIÓN (offline · se ejecuta una vez y al añadir libros)". Contiene en fila, conectadas por flechas:
- Caja verde "Colección de libros (.txt)" con icono de libros. Nota: "La base de conocimiento, va creciendo".
- Caja azul "Chunking / Troceado" con icono de tijeras o bloques. Nota: "Parte cada libro en fragmentos (~500-1000 tokens con solapamiento)".
- Caja morada "Modelo de Embeddings" con icono de vectores. Nota: "Convierte cada fragmento en un vector numérico".
- Caja naranja "Vector Store (Chroma)" con icono de base de datos. Nota: "Guarda los vectores + el texto original. Portable, corre en local".

ZONA 2 (abajo) — "CONSULTA (en vivo · en cada pregunta)". Flujo con pasos numerados:
- Caja verde "USUARIO" con icono de persona/navegador a la izquierda.
- Flecha (1) "GET /ask?query=... (HTTP)" hacia la caja central.
- Caja azul central grande "Servicio FastAPI (en contenedor Docker)" con icono. Dentro lista: "Endpoint GET /ask", "Docs en /docs (Swagger)", "Devuelve JSON".
- Flecha (2) "Convierte la pregunta en vector" desde FastAPI hacia el "Modelo de Embeddings".
- Flecha (3) "Busca top-k fragmentos" desde FastAPI hacia el "Vector Store (Chroma)". Añade una caja pequeña gris opcional con borde discontinuo "BM25 (búsqueda por palabra clave)" etiquetada "Opcional: búsqueda híbrida".
- Flecha (4) "Pregunta + fragmentos como contexto" desde FastAPI hacia la caja morada "LLM gpt-5.4-mini" con icono. Nota: "Redacta la respuesta a partir del contexto".
- Flecha (5) "Devuelve la respuesta" desde el LLM de vuelta a FastAPI.
- Flecha (6) "{\"answer\": \"...\", \"sources\": [...]} (JSON)" desde FastAPI de vuelta al USUARIO.

PANEL LATERAL DERECHO "¿Qué es qué?" con una línea por componente:
- Servicio FastAPI: framework de Python que expone la API y las docs.
- Embeddings: convierten texto en vectores para comparar significado.
- Vector Store (Chroma): guarda y busca fragmentos por similitud. Portable.
- BM25: búsqueda clásica por palabra clave; útil para nombres exactos.
- LLM (gpt-5.4-mini): redacta la respuesta usando los fragmentos recuperados.

PANEL "¿Cómo fluye una pregunta?" con los 6 pasos numerados en una frase cada uno.

BANNER inferior con icono de candado/maleta: "Portable — sin atarse a Azure. Todos los componentes pueden correr en local o en cualquier cloud."

Texto en español, etiquetas técnicas (FastAPI, embeddings, Chroma, BM25, gpt-5.4-mini, top-k, JSON) en inglés. Colores: verde para datos/usuario, azul para la app, morado para IA/modelos, naranja para almacenamiento. Alta legibilidad, sin saturar.
```

*(Si prefieres las etiquetas en inglés como el de ayer, cambia la última línea a "Texto en inglés".)*

---

## 4. Prompt para arrancar el desarrollo conmigo (Claude)

> Pega esto en una conversación nueva de Claude (o Claude Code) cuando vayas a empezar a programar. Está pensado para ir paso a paso, planificando primero.

```
Vamos a construir un servicio RAG en Python, paso a paso. NO escribas todo el código de golpe: primero proponme un plan y la estructura de ficheros, lo valido, y luego vamos archivo por archivo.

OBJETIVO
Un servicio que responde preguntas sobre una colección de libros (.txt) que crece. Usa RAG: indexar los libros una vez (trocear → embeddings → vector store), y en cada pregunta recuperar los fragmentos relevantes y pasárselos al LLM.

REQUISITOS
- API con FastAPI. Endpoint: GET /ask?query=<pregunta> que devuelve {"answer": "..."} y, si es posible, {"answer": "...", "sources": [...]}.
- Docs auto-generadas en /docs.
- Generación con el modelo gpt-5.4-mini.
- Vector store PORTABLE que corra en local: usa Chroma. Nada de servicios cloud propietarios.
- Arrancable con: uvicorn app:app --reload.
- Gestión de dependencias con UV.

DATASET (descargar de estas URLs)
- https://www.gutenberg.org/files/55602/55602-0.txt
- https://www.gutenberg.org/cache/epub/76262/pg76262.txt

CÓMO QUIERO TRABAJAR
1. Primero: propón la arquitectura y la estructura de carpetas/ficheros, y explícame las decisiones (tamaño de chunk, modelo de embeddings, top-k). Pregúntame lo que necesites.
2. Luego construimos por partes: (a) script de indexación, (b) la lógica de recuperación, (c) la API FastAPI, (d) probarlo en local.
3. Explícame cada bloque de código en castellano antes de pasar al siguiente. Soy técnico pero quiero entender bien cada decisión.
4. Cuando algo tenga alternativas (p. ej. añadir búsqueda híbrida con BM25), dímelo y recomiéndame una opción por defecto.

Empieza por el paso 1: el plan.
```
