# Primer prompt — Ejercicio 4: Data Quality Checker

> Pegar como primer mensaje de la conversación nueva del proyecto.
> Método "agentic" (Paso 2), no vibe coding: inspeccionar → planificar → PRD → módulos profundos → vertical slices → TDD.

```
Vamos a construir juntos, paso a paso, el ejercicio "Data Quality Checker" de la Agentic AI Academy. Es un ejercicio de AI-native coding: lo importante no es ir rápido, es el método y que yo entienda y controle cada decisión. Trabaja en modo disciplinado (no "vibe coding"): inspecciona antes de escribir, planifica, y no avances de fase sin que yo lo valide.

EL PROYECTO, EN UNA FRASE
Una aplicación que perfila y evalúa la calidad de datos de un CSV subido manualmente, y produce un informe de calidad de datos.

DATOS
- Dataset de ejemplo: exercice4/vgsales.csv (16.598 filas, 11 columnas). Úsalo para probar.
- La carpeta de trabajo es exercice4 (ya creada).

CÓMO QUIERO TRABAJAR (importante)
1. Primero inspecciona la carpeta y el CSV, y proponme un plan. No escribas la app entera de golpe.
2. Antes de programar, ayúdame a fijar las decisiones de alto valor (lo que el agente NO puede adivinar): las reglas de scoring de calidad, los umbrales de warning, y los límites de los módulos. Pregúntame por ellas en vez de inventarlas. La parte mecánica (parsear el CSV, subir el fichero, renderizar una tabla) la delegas en ti sin pedirme detalle.
3. Sintetiza todo en un PRD.md: problema y solución en mis palabras, lista numerada de user stories, decisiones de implementación (los módulos), decisiones de testing y qué queda fuera de alcance. No metas requisitos que yo no haya acordado.
4. Diseña MÓDULOS PROFUNDOS: comportamiento rico detrás de una interfaz pequeña. Si un módulo es un simple "pasa-llamadas", dímelo y rediséñalo.
5. Corta el trabajo en VERTICAL SLICES (rebanadas finas de extremo a extremo: parsear → perfilar → puntuar → renderizar), no en capas horizontales. Ordénalas por dependencias e identifica cuál es el "tracer bullet" (la rebanada mínima que demuestra que todo el camino funciona).
6. Construimos slice a slice. Para cada una: escribe el test ANTES de la implementación (TDD), implementa, corre los tests, y resúmeme los trade-offs.
7. No añadas dependencias nuevas sin explicarme por qué.
8. Explícame cada bloque y cada decisión en castellano antes de pasar al siguiente. Soy técnico pero quiero entender el porqué, no solo el qué.

EMPIEZA POR AQUÍ
Inspecciona exercice4 y el CSV, y devuélveme: (a) un project.md de una o dos frases, (b) las 3-4 decisiones de este proyecto que merece la pena que yo especifique con detalle, y las preguntas concretas para resolverlas. Aún no escribas código de la app.
```

---

## Variante "Paso 1 — Vibe it" (opcional, para el contraste del ejercicio)
Si quieres hacer primero la pasada rápida y descuidada que pide el Paso 1 antes de la disciplinada:

```
Hazme una web app que comprueba la calidad de un CSV subido y muestra un informe. Usa exercice4/vgsales.csv para probar. Hazla funcionar ya.
```
(Y luego ir empujando: "hazla más bonita", "añade una nota", "arregla ese error" — sin leer el código ni pedir tests. El objetivo del ejercicio es notar la diferencia de sensación entre esta pasada y la disciplinada de arriba.)
