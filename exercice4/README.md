# Data Quality Checker (exercice4)

Web app que perfila un CSV subido manualmente y devuelve un **informe de calidad de
datos**: una puntuación global 0–100, el desglose por dimensión y los avisos relevantes.
Las decisiones de diseño (qué se mide, cómo puntúa, qué dispara un aviso) están fijadas
en [CONTEXT.md](CONTEXT.md).

## Qué evalúa

| Dimensión | Peso | Defecto que cuenta |
|---|---|---|
| Completitud | 30 | celdas faltantes (vacío o token nulo: `N/A`, `null`, `NaN`, `none`, `-`) |
| Validez | 30 | celdas no faltantes que no conforman el tipo inferido (≥90% parsea → ese tipo) |
| Unicidad | 20 | filas exactamente duplicadas |
| Distribución | 20 | outliers IQR (1.5×) + columnas constantes (≥95% un valor) |

Sub-score = `100 × (1 − tasa_de_defecto)`. Global = media ponderada.
Un **aviso** salta cuando una columna cruza un umbral: faltante >5%, inválido >5%,
outliers >1%, columna constante, o existen filas duplicadas.

## Arquitectura (módulos profundos)

- [app/ingest.py](app/ingest.py) — parsea el CSV a strings crudos (cabecera, coma, UTF-8, ≤50 MB).
- [app/profiler.py](app/profiler.py) — el módulo central: `profile(df, filename) → Report`.
- [app/store.py](app/store.py) — persistencia SQLite (informe JSON + metadatos; reabrir histórico).
- [app/report.py](app/report.py) — modelo de datos compartido (`Report`).
- [app/main.py](app/main.py) — capa web fina: subir → perfilar → guardar → render HTML.

## Uso

```bash
uv sync                         # instala dependencias
uv run uvicorn app.main:app --reload   # arranca en http://127.0.0.1:8000
uv run pytest                   # 23 tests
```

Abre el navegador, sube `vgsales.csv` (incluido) y verás el informe. El histórico
queda en `reports.db` (SQLite local, ignorado por git).

## Fuera de alcance (v1)

Limpieza/corrección de datos · entradas no-CSV · esquemas o reglas definidas por el
usuario (la validez es 100% auto-inferida) · comparación entre runs / tendencias.
