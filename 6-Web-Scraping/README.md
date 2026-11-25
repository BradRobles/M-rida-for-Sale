# 6. Web Scraping (prensa local, YouTube y Wikipedia)

Extracción y limpieza de fuentes web para la sección **6. Web scraping** del proyecto *Mérida for Sale* (capítulo 4, *Quién cuenta la historia*, y capítulo 1, *La llegada*).

> **Nota:** Por derechos de autor y datos personales, en `clean/` y en git van **solo metadatos, conteos y un extracto de máximo 200 caracteres** por nota. El HTML y el texto completo se quedan en `raw/html/` (en `.gitignore`). De YouTube nunca se guardan autores ni texto de comentarios. No incluye visualizaciones.

---

## Estructura de la carpeta

```text
6-Web-Scraping/
├── raw/
│   ├── robots/                              # robots.txt de cada diario, con fecha de consulta
│   ├── sitemaps/                            # Caché de sitemaps e índice CDX (en .gitignore, ~31 MB)
│   ├── html/                                # HTML de las notas seleccionadas (en .gitignore)
│   ├── youtube/                             # Respuestas de la API de YouTube (en .gitignore)
│   ├── wikipedia/                           # Respuestas JSON de la Pageviews API (caché)
│   └── wikipedia_titulos_resueltos.csv      # Título exacto de cada artículo según la API de MediaWiki
├── scripts/
│   └── clean_web_scraping.py                # Prensa local + YouTube + Wikipedia (--solo prensa|youtube|wikipedia)
├── clean/
│   ├── prensa_local_articulos.csv
│   ├── prensa_local_menciones_colonia.csv
│   ├── prensa_local_temas_anual.csv
│   ├── prensa_local_candidatos_url.csv
│   └── wikipedia_vistas_mensuales.csv
└── README.md
```

---

## Fuentes incluidas

### 1. Principal — Prensa local de Yucatán sobre rentas, desalojos y gentrificación (2018 a la fecha) ✅
- **Sitios y cómo se descubrieron las URL:**

| Diario | URL | robots.txt (24 nov 2026) | Descubrimiento | URL en índices |
|---|---|---|---|---|
| Diario de Yucatán | `https://www.yucatan.com.mx/` | ✅ solo prohíbe `/wp-admin/`, WooCommerce y `/100-joyas/` | `sitemap.xml` → `post-sitemapN.xml` | 494,047 |
| Por Esto! | `https://www.poresto.com/` | ✅ para `*` solo prohíbe `/buscar`; bloquea por nombre a bots comerciales (no a nosotros) | `sitemaps/poresto_map_index.xml` → mapas mensuales 2018–2026 | 500,168 |
| La Jornada Maya | `https://www.lajornadamaya.mx/` | ✅ sin restricciones | ⚠️ su sitemap solo trae las ~250 notas recientes y el buscador requiere JavaScript: se usó además el índice CDX de Internet Archive (`https://web.archive.org/cdx/search/cdx`, filtrado por palabras clave en la URL) **solo para descubrir URL**; el cuerpo se bajó del sitio | 1,152 |

- **Filtro 1 (sin descargar, por palabras del slug de la URL, normalizado sin acentos):** `gentrific`, `turistific`, `renta(s)`, `alquil`, `desaloj`, `despoj`, `airbnb`, `plusval`, `inmobiliari`, `vivienda`, `extranjer`, `nomada digital`, `centro historico`, fechas desde 2018. Resultado: **9,339** candidatas (`prensa_local_candidatos_url.csv`), de las cuales **3,838** están en secciones de Mérida/Yucatán (se descartan Quintana Roo, Campeche, nacional, internacional, deportes, etc.).
- **Filtro 2 (tope de 1,500 descargas):** entran **todas** las candidatas con una palabra "fuerte" (gentrific, turistific, desalojo, despojo, airbnb, plusvalía, alquiler, inmobiliaria, nómada digital): **1,282**; las otras **218** se sortean (semilla 2026) entre las que solo dicen renta, vivienda, extranjero o centro histórico. Por fuente: Diario de Yucatán 660, Por Esto! 648, La Jornada Maya 192.
- **Descarga:** `User-Agent` del proyecto, ≥ 2.5 s entre peticiones al mismo sitio, reintentos con espera, caché gzip en `raw/html/` (fuera de git).
- **Extracción:** título, fecha y sección desde JSON-LD / metadatos (fecha de la URL como respaldo); cuerpo de `articleBody` o de los `<p>` del artículo. `palabras_clave_detectadas` se busca en título y cuerpo; `temas` usa las reglas de `7-Self-Produced/scripts/clasificacion.py` (basta una palabra en el título, o **dos** en el cuerpo); `colonias_mencionadas` cruza el texto normalizado contra el catálogo de colonias del GeoPortal (exigiendo "colonia / fraccionamiento / barrio + nombre") y una lista de barrios tradicionales (Centro Histórico, Santiago, Santa Ana, San Sebastián, La Mejorada, San Juan, San Cristóbal, Santa Lucía, La Ermita, Paseo de Montejo, Itzimná, García Ginerés, Chuburná, Alemán, Col. México…), **solo si la nota menciona Mérida**.
- **Validación:** 1,493 de 1,495 notas con cuerpo (las 2 sin cuerpo son de la sección `editorial` del Diario de Yucatán); el extracto nunca pasa de 200 caracteres; 1 nota sin fecha. 5 notas de La Jornada Maya halladas por CDX resultaron anteriores a 2018 y se excluyeron.
- **Ojo al interpretar:**
  - "despojo" en la prensa yucateca también significa **robo** ("despojan a productor de $50 mil") y "desalojo" incluye desalojos de ambulantes: por eso "seguridad" aparece en 476 notas.
  - Las notas descargadas son una **muestra dirigida**, no el universo: para tendencias anuales del volumen usa `prensa_local_candidatos_url.csv` (todas las URL que pasan el filtro 1, con su fecha).
  - Las colonias son menciones en el texto, no la ubicación del hecho; el Centro Histórico domina (98 notas).
- **Archivos limpios (`clean/`):**
  - `prensa_local_articulos.csv`: **1,495** notas (Diario de Yucatán 660, Por Esto! 648, La Jornada Maya 187; de 2018 a noviembre de 2026) con `fuente`, `url`, `fecha_publicacion`, `anio`, `titulo`, `seccion`, `palabras_clave_detectadas`, `temas`, `colonias_mencionadas`, `unidades_habitacionales`, `n_palabras`, `extracto` (≤ 200 caracteres) y `estado_descarga`.
  - `prensa_local_menciones_colonia.csv`: **163** filas (`colonia`, `unidad_habitacional` del GeoPortal, `anio`, `n_articulos`); 244 notas mencionan al menos una de 88 unidades habitacionales.
  - `prensa_local_temas_anual.csv`: **171** filas (`anio`, `fuente`, `tema`, `n_articulos`, `n_articulos_fuente_anio`, `porcentaje`; una nota puede tener varios temas).
  - `prensa_local_candidatos_url.csv`: **9,339** URL candidatas con fecha, sección, palabras de la URL, `seccion_relevante` y `seleccionado` (solo metadatos).

### 2. Complemento A — YouTube Data API v3 ⚠️ (script listo, falta la llave)
- **Fuente:** `https://www.googleapis.com/youtube/v3` (`search.list`, `videos.list`, `commentThreads.list`). Docs: `https://developers.google.com/youtube/v3`.
- **Estado:** la variable de entorno `YOUTUBE_API_KEY` no existe en esta máquina, así que esta parte **no se corrió**. Para correrla: crear una llave en Google Cloud Console (habilitar *YouTube Data API v3*), definirla en PowerShell con `$env:YOUTUBE_API_KEY = "<tu llave>"` y correr `python 6-Web-Scraping/scripts/clean_web_scraping.py --solo youtube`.
- **Qué hace:** 5 búsquedas ("moving to Merida", "living in Merida Mexico", "Merida Yucatan expat", "cost of living Merida Mexico", "mudarse a Mérida"), 2 páginas de 50 resultados cada una. **Cuota:** 10 × `search.list` = 1,000 unidades, más ~1 unidad por lote de videos y por video comentado (~1,200 de las 10,000 diarias).
- **Salidas que generará:** `youtube_videos_merida.csv` (`video_id`, `titulo`, `canal`, `fecha_publicacion`, `vistas`, `likes`, `n_comentarios`, `idioma`, `consulta`, `temas`) y `youtube_comentarios_palabras_clave.csv` (por video: comentarios leídos y cuántos mencionan precio, cheap, safe, rent, gentrification, locals). **Nunca** se guardan autores ni texto de comentarios: los JSON de comentarios se borran al terminar de contar.

### 3. Complemento B — Vistas de Wikipedia ✅
- **Fuente:** Wikimedia Pageviews API, `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{idioma}.wikipedia/all-access/user/{artículo}/monthly/2016010100/...` (solo usuarios, sin bots). Docs: `https://wikitech.wikimedia.org/wiki/Analytics/AQS/Pageviews`.
- **Títulos exactos** resueltos con la API de MediaWiki (`action=query&redirects=1`) y guardados en `raw/wikipedia_titulos_resueltos.csv`: Mérida → *Mérida, Yucatán* (en) y *Mérida (México)* (es); Oaxaca de Juárez → *Oaxaca City* (en) y *Oaxaca de Juárez* (es); San Miguel de Allende y Playa del Carmen con el mismo título en ambos idiomas.
- **Limpieza:** solo meses completos (enero 2016 – octubre 2026); `indice_2019_100` = vistas del mes / promedio mensual de 2019 del mismo artículo × 100.
- **Validación rápida (vistas anuales 2025 con 2019 = 100):** Mérida en inglés 128.3 (sube) y en español 62.2; Oaxaca en inglés 168.5; San Miguel de Allende en inglés 62.2; Playa del Carmen en inglés 54.7. Wikipedia en español cae en general, así que conviene comparar ciudades entre sí, no contra 2019 a secas.
- **Archivo limpio:** `wikipedia_vistas_mensuales.csv`: **1,040** filas (`mes`, `ciudad`, `idioma`, `articulo`, `vistas`, `indice_2019_100`).
- **Actualizar:** las respuestas quedan en caché en `raw/wikipedia/`; para sumar meses nuevos, borra esa carpeta y corre `--solo wikipedia`.

### Nota sobre Sefotur
El informe mensual de Sefotur que en la tabla U3 aparecía como fuente de scraping **ya lo cubre la sección 3** (`3-SIEGY-Yucatan/`, cifras transcritas con URL en `raw/sefotur_cifras_transcritas.csv`); aquí no se repite.

---

## Pendientes
- YouTube: conseguir la llave y correr `--solo youtube` (ver arriba).
- Volumen completo de La Jornada Maya: hoy depende de lo que Internet Archive haya guardado; se podría pedir al diario un sitemap histórico.

---

## Cómo regenerar los archivos limpios

```bash
python 6-Web-Scraping/scripts/clean_web_scraping.py                  # todo
python 6-Web-Scraping/scripts/clean_web_scraping.py --solo prensa    # o youtube / wikipedia
```

La prensa usa la caché de `raw/sitemaps/` y `raw/html/`; en una copia nueva del repo (sin esas carpetas) el script vuelve a descargar todo respetando `robots.txt` y las pausas: ~1,000 sitemaps y 1,500 notas, alrededor de 1.5 horas. La selección de notas es reproducible (semilla 2026), pero los sitemaps cambian con el tiempo, así que una descarga nueva puede traer algunas notas distintas. Sección 6 importa las reglas de temas de `7-Self-Produced/scripts/clasificacion.py`.
