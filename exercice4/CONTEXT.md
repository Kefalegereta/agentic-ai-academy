# Data Quality Checker — Decisiones resueltas (CONTEXT)

> Resultado del grilling (Paso 4 — *grill out the ambiguity*). Estas son las decisiones de
> alto valor que el agente **no** podía adivinar y que tú has fijado. La parte mecánica
> (parsear, subir el fichero, renderizar la tabla HTML) queda delegada en la implementación.

## Problema, en una frase
Una web app a la que subo un CSV manualmente; lo perfila, evalúa su calidad según reglas
fijas y me devuelve un informe HTML con una puntuación global y los avisos relevantes.

## Modelo de puntuación
- **Escala:** 0–100.
- **Global = media ponderada** de las cuatro dimensiones.
- **Sub-score por dimensión:** fórmula uniforme y lineal `100 × (1 − tasa_de_defecto)`.
- **Pesos:** Completitud **30** · Validez **30** · Unicidad **20** · Distribución **20**.

## Las cuatro dimensiones (todas en v1)

### Completitud (peso 30)
- Defecto = valores **faltantes**.
- "Faltante" = celda vacía / solo-espacios **o** un token nulo de una lista fija,
  case-insensitive: `N/A`, `NA`, `null`, `NaN`, `none`, `-`.
- Los tokens nulos se **normalizan a faltante antes** de calcular validez (dimensiones desacopladas).

### Validez (peso 30)
- **Sin esquema de usuario:** las expectativas se **auto-infieren** del propio dato.
- El motor infiere el **tipo dominante** por columna (entero / float / fecha-o-año / categórico / texto libre).
- Regla de inferencia: si **≥90 %** de los valores **no faltantes** parsean como un tipo numérico/fecha,
  la columna **es** ese tipo; por debajo de 90 % se trata como texto libre (sin inválidos).
- Defecto = celda **no faltante** que **no parsea** como el tipo inferido. **Solo conformidad de tipo**
  (sin rangos ni chequeos semánticos). Los faltantes **no** cuentan como inválidos.

### Unicidad (peso 20)
- Defecto = **filas exactamente duplicadas** (todas las columnas iguales).
- **Sin** adivinar columnas-clave. Los conteos de distintos por columna se reportan como estadística, no puntúan.

### Distribución (peso 20)
- Chequea **outliers** (IQR, valores fuera de 1.5×IQR) en columnas numéricas **y**
  **columnas constantes / casi-constantes** (un valor ≥ 95 %).
- Tasa de defecto = proporción de celdas outlier **combinada** con la proporción de columnas degeneradas
  (mezcla exacta a documentar en el PRD y confirmar).

## Avisos (warning) vs. estadística
Todo número se reporta; un **aviso** es el subconjunto que el informe sube arriba como "mira aquí".
Disparadores por **umbral de tasa de defecto por columna**:

| Disparador | Umbral |
|---|---|
| % faltante en una columna | **> 5 %** |
| % inválido en una columna | **> 5 %** |
| % de celdas outlier en una columna | **> 1 %** |
| columna constante / casi-constante (≥95 % un valor) | siempre avisa |
| existen filas totalmente duplicadas (nivel dataset) | siempre avisa |

(Una sola banda warn; severidad por niveles warn/critical queda para v2.)

## Interfaz y entrega
- **Web app** (FastAPI, alineado con exercicios previos): página de subida → **informe HTML** en el navegador
  (score global, desglose por dimensión, lista de avisos priorizada, tabla de estadística por columna).

## Persistencia (en alcance v1)
- **Guardar y reabrir informes pasados.** Lista de histórico que permite reabrir cualquier informe previo.
  **Sin** comparación run-over-run ni tendencias (eso sería v2).
- **Almacén:** **SQLite** (fichero local). Se guarda el **informe computado como JSON + metadatos**
  (nombre de fichero, timestamp, nº filas, nº columnas, score global). **No** se guarda el CSV crudo.

## Ingestión (supuestos y límites)
- Primera fila = **cabeceras** (obligatorio).
- Delimitador **coma**, codificación **UTF-8** (con fallback tolerante).
- **Límite de tamaño ~50 MB**; ficheros mayores o malformados → **error claro**, no crash.

## Motor de perfilado
- **pandas** para parseo, inferencia de tipo y cómputo de faltantes / duplicados / outliers.

## Fuera de alcance (v1)
- **Limpieza / corrección** de datos (solo reporta; nunca modifica, imputa, deduplica ni exporta un CSV corregido).
- **Entradas no-CSV** (Excel/JSON/Parquet/BD). Solo CSV, un fichero, con cabecera.
- **Esquemas / reglas definidas por el usuario** (la validez es 100 % auto-inferida).
- Comparación run-over-run, tendencias, cuentas/usuarios, severidad por niveles.

## Detalles delegados en la implementación (no decididos por ti)
- Parseo concreto del CSV y manejo de errores de subida.
- Maquetación/estilo del HTML y de la tabla por columna.
- Mezcla exacta outlier-cells ↔ columnas degeneradas en el score de Distribución (a proponer en el PRD).
- Esquema de la tabla SQLite y serialización del JSON del informe.
