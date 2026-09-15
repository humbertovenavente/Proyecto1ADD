# Probabilidad de las hazañas de Leverkusen y Cabo Verde

Proyecto del curso **Análisis de Datos** de la Universidad del Istmo.

**Catedrático:** Juan Andrés García Porres.

- Didvin Nohel Estrada Pineda · 14092
- Jose Humberto Najar Venavente · 13661
- Pablo Rodolfo Alexander Flores Mollinedo · 14643

## Archivos principales

- `outputs/trabajo_escrito.docx` y `outputs/trabajo_escrito.pdf`: informe de 58 páginas con ambas partes, desarrollo matemático, supuestos, extra, conclusiones estadísticas, referencias y anexos. El PDF es la versión para entregar.
- `outputs/presentacion.pptx`: presentación narrativa de 96 diapositivas con los integrantes en portada, imágenes, desarrollo matemático, gráficas nativas y transiciones.
- `outputs/presentacion.pdf`: versión para lectura, sin animaciones.
- `outputs/results.json`: resultados numéricos completos.
- `outputs/leverkusen_10000.csv` y `outputs/cape_verde_10000.csv`: simulaciones por repetición.
- `outputs/figures/`: gráficas en PNG y SVG.

## Repetir el análisis

Instalar [uv](https://docs.astral.sh/uv/getting-started/installation/) y ejecutar desde esta carpeta:

```sh
uv sync --frozen
uv run python src/analyze.py
uv run pytest -q
```

`uv sync` crea `.venv`. No hace falta activarlo al usar `uv run`. La primera ejecución descarga las dependencias. Los datos de la entrega permiten ejecutar el análisis sin volver a consultar los proveedores.

Si faltan los archivos originales:

```sh
uv run python src/fetch_data.py
```

Para recomponer el informe editable:

```sh
uv sync --frozen --group documents
uv run python docs/expand_methodology.py
uv run python docs/build_numeric_examples.py
uv run python docs/render_math.py
uv run --group documents python docs/build_report.py
```

## Organización

- `src/models.py`: enlace Elo–Poisson, intervalos y simulación de grupos.
- `src/analyze.py`: parte I Leverkusen, extra, parte II Cabo Verde y gráficas.
- `src/fetch_data.py`: descarga de fuentes públicas y registro de huellas SHA-256.
- `data/raw/`: copias de los datos consultados.
- `data/processed/`: campeones, ratings históricos, probabilidades por partido, goles y auditoría del minuto 85.
- `data/groups_2026.json`: composición de los doce grupos. Los códigos pertenecen a World Football Elo Ratings; Escocia es `SQ`.
- `data/sources.json`: procedencia de los archivos de datos.
- `tests/`: comprobaciones de probabilidades, calendarios, escenarios condicionados y datos.

## Decisiones que afectan la interpretación

La muestra histórica termina en 2022/23. El modelo de partidos usa ClubElo del 15 de agosto de 2023, conservado en el archivo de Ádám Gábor, porque la API original no respondió. La temporada 1991/92 de Curley contiene 340 de 380 partidos. Su registro de campeón se corrige con la tabla de DSFS: Stuttgart, 38 partidos, 21 victorias, 10 empates y 7 derrotas.

Elo expresa `P(victoria) + 0.5 P(empate)`. Los goles se modelan con dos Poisson independientes cuyas tasas se ajustan a esa expectativa. Las fuerzas permanecen fijas. El parámetro de goles es el nivel base de equipos de igual fuerza. Los intervalos cubren error Monte Carlo y no incertidumbre del modelo.

El extra incluye cuatro rescates: Bayern, Hoffenheim, Dortmund y Stuttgart. Ante Bayern la desventaja comienza a 85:21. El cálculo central condiciona por duración observada y utiliza tasas históricas de la liga. `P(invicto) × Q` se reporta como índice heurístico del ejercicio, no como una corrección causal de suerte.

Cabo Verde usa ratings anteriores al 15/11/2023 para la eliminatoria y al 11/06/2026 para el Mundial. Se simulan los doce grupos para determinar los mejores terceros. Los empates residuales se resuelven por sorteo, sin tarjetas ni ranking FIFA. La ruta eliminatoria es fija y todo empate implica avanzar en penales, tal como supone el ejercicio. La narración sobre arbitraje no se adopta como hecho.

## Fuentes

James P. Curley, **engsoccerdata**: https://github.com/jalapic/engsoccerdata

Ádám Gábor, **Club Football Match Data**, datos de ClubElo: https://github.com/xgabora/Club-Football-Match-Data

Hudl **StatsBomb Open Data**: https://github.com/statsbomb/open-data . El uso de sus datos debe conservar la atribución a StatsBomb y respetar su licencia.

**World Football Elo Ratings**: https://www.eloratings.net/

**DSFS**, tablas históricas: https://www.dsfs.de/wp-content/uploads/2024/01/Bundesliga_Geschichte_Tabellen.pdf

**CAF** y **FIFA**: formatos y grupos. Las referencias completas están en el informe.

David y Paul Goldsman (2024), **A First Course in Probability and Statistics**, capítulos 1, 4, 5 y 6. El libro completo no se redistribuye.

La fuente de las diapositivas está en `docs/build_slides.mjs` y utiliza `@oai/artifact-tool`. Las fórmulas LaTeX de la presentación están en `docs/render_math.py`; los exponentes del texto permanecen legibles en PowerPoint y PDF.

`docs/notation.json` contiene los glosarios previos a la formulación matemática de Leverkusen y Cabo Verde. Los símbolos se conservan como imágenes matemáticas para mantener índices y exponentes.

## Ejecutar en Google Colab

1. Abre https://colab.research.google.com/ y selecciona **Archivo → Subir notebook**.
2. Sube `notebooks/Futbol_probabilidad.ipynb`.
3. Selecciona **Entorno de ejecución → Ejecutar todas**. No necesitas GPU ni cargar un ZIP.

Es **un único notebook**, organizado en dos bloques: Leverkusen con el extra y seis gráficas; Cabo Verde con sus escenarios y tres gráficas. Cada bloque contiene sus datos, variables, modelos, ejecución, comprobaciones y conclusiones. Los archivos se guardan en `leverkusen_colab` y `cabo_verde_colab`. La última celda descarga un ZIP que contiene ambas carpetas.

El notebook incorpora una proyección compacta de los datos: registros históricos pertinentes, Elo del corte, goles, autogoles y último evento del segundo tiempo. Cada archivo tiene su SHA-256 y la huella del original; los datos originales completos permanecen en `data/raw` y en el ZIP opcional. La carga de datos no consulta servidores externos: evita errores 404, cambios de fuente y la necesidad de subir archivos adicionales. La instalación inicial de bibliotecas sí necesita conexión. `outputs/datos_colab.zip` es una copia opcional para otros usos; el notebook no la requiere.

La URL correcta del historial de RD Congo es `https://www.eloratings.net/DR_Congo.tsv`; se comprobó que responde con el mismo SHA-256 que la copia utilizada. El manifiesto y el descargador del proyecto ya usan esa dirección.

Validación de memoria: ejecución de las 47 celdas de código en un kernel Jupyter nuevo mediante nbclient, con dependencias preinstaladas. Pico observado de memoria residente del kernel y sus procesos: **282.2 MiB**; duración local: 20 segundos; cero errores, seis gráficas de Leverkusen y tres de Cabo Verde, con resultados numéricos contrastados. Las siete pruebas del proyecto pasan. No es una medición realizada en Google Colab ni una garantía para cualquier entorno; el detalle está en `docs/validacion_colab_memoria.json`.

Para reemplazar la versión que falló, reinicia la sesión de Colab y abre el notebook actualizado antes de usar **Ejecutar todas**. El archivo ahora pesa aproximadamente 1.2 MB. La extracción usa la copia compacta, los grupos se procesan secuencialmente, las figuras se cierran al guardarse y los objetos de Leverkusen se liberan antes de Cabo Verde. No se redujeron las 10 000 repeticiones ni se cambiaron las semillas.

`docs/build_notebook.py` reconstruye el único notebook mediante `docs/build_notebook_sections.py`, y la copia opcional de datos. `docs/add_links.py` incorpora enlaces de referencias al PowerPoint.

`docs/numeric_examples.json` contiene 19 sustituciones y derivaciones compartidas por el informe, la presentación y el notebook. Sus celdas recalculan los resultados con los datos de cada parte.
