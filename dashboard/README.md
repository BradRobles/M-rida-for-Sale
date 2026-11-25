# Mérida for Sale · Dashboard v1

Dashboard local en Streamlit (Visual Modeling for Information, UPY Data 9B; equipo: Julio César De Aquino Castellanos, Brad Robles García y Eliana Lorely Osorio Martinez) que cuenta la historia del booklet *Mérida for Sale* (turistificación y gentrificación en la Zona Metropolitana de Mérida) en una sola página: portada y cinco capítulos. Es la presentación de los datos ya limpios de las secciones `1-...` a `9-...`; no vuelve a limpiar fuentes.

**Versión:** v1 (aparece en el título de la app y en el pie de página). Narrativa, textos (en inglés), paleta y gráficas siguen el prototipo aprobado, [`reference/prototype_reference.html`](reference/prototype_reference.html) (formato `.dc.html`: sirve de referencia, no se ejecuta).

---

## Cómo instalarlo y correrlo (Windows, PowerShell, desde la raíz del repo)

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python dashboard/prep.py          # construye dashboard/data/ desde los clean/
pytest dashboard/tests            # valida las cifras clave
streamlit run dashboard/app.py    # abre http://localhost:8501
```

`dashboard/data/` ya va versionado, así que para solo abrir el dashboard basta con el último comando. `prep.py` usa `pyshp`, `pyproj` y `shapely` (ya están en `requirements.txt`) para leer las manzanas del Marco Geoestadístico. Probado con Python 3.13 y Streamlit 1.67, a 1280 px y a 390 px de ancho (en celular las columnas se apilan y no hay scroll horizontal).

## Estructura

```text
dashboard/
├── app.py                  # Streamlit: una página con scroll (portada + 5 capítulos); lee solo data/
├── prep.py                 # Tablas "gold": lee */clean/ (y el Marco Geoestadístico crudo) y escribe data/
├── charts.py               # Una función por gráfica (Plotly; pydeck para el 3D)
├── theme.py                # ÚNICO lugar con colores, fuentes y textos fijos
├── data/                   # Salidas de prep.py (CSV y GeoJSON chicos, versionados)
├── reference/prototype_reference.html
├── tests/test_gold.py      # pytest: cifras de validación + "ningún hex ni fuente fuera de theme.py"
└── README.md
```

### Cambiar colores o fuentes

Los colores y las fuentes **van a cambiar** cuando se integren las historias del resto del equipo. Todos viven en `theme.py`, con nombres por función: `BG`, `TEXT`, `COLOR_MERIDA`, `COLOR_FOREIGN`, `COLOR_GROWTH`, `COLOR_DECLINE`, `COLOR_MUTED`, `FONT_TITLE`, `FONT_BODY`, `FONTS_URL`, las escalas de mapa `MAP_DIVERGING` y `DECK_*`. Cambiar la paleta es editar solo ese archivo. `tests/test_gold.py::test_no_hardcoded_style_outside_theme` falla si aparece un hex o un nombre de fuente en `app.py`, `charts.py` o `prep.py`. Las fuentes de Google se cargan con CSS inyectado (`theme.css()`).

---

## Gráfica → tabla gold → archivo fuente → sección

| Capítulo | Gráfica / cifra | `data/` | Fuente (`clean/`) | Sección |
|---|---|---|---|---|
| Portada | 4 KPIs (+30%, −12.9%, ×3.2, +39%) | `kpis.csv` | las de abajo | 1, 3, 5, 9 |
| 01 The arrival | Barras apiladas de turistas nacionales vs. extranjeros, 2015–2026* | `tourists_annual.csv` | `9-Augmented-Reality/clean/ar2_datatur_merida_turistas_anual_2015_2026.csv` | [9](../9-Augmented-Reality/README.md) |
| 01 | Línea mensual con selector de categoría hotelera | `tourists_monthly_category.csv` | `2-Datos-Gob-Mx/clean/datatur_merida_llegadas_categoria_mensual_2015_2026.csv` | [2](../2-Datos-Gob-Mx/README.md) |
| 01 | KPI aeropuerto MID 2025 | `airports_annual.csv` | `9-Augmented-Reality/clean/ar3_asur_crecimiento_anual_mid_cun_oax.csv` | [9](../9-Augmented-Reality/README.md) |
| 02 The Centro empties out | Barras divergentes, Centro / municipio (tooltip con conteos) | `shops_change.csv` | `1-INEGI-DENUE/clean/denue_merida_conteos_categoria_2019_vs_2025.csv` | [1](../1-INEGI-DENUE/README.md) |
| 02 | Mapa de AGEB: cambio de cafeterías 2019→2025, con contorno del Centro | `ageb_cafes.geojson`, `ageb_cafes.csv`, `centro_historico.geojson` | `1-INEGI-DENUE/clean/denue_merida_resumen_ageb_2019_vs_2025.csv` + `4-GeoPortal-Merida/clean/inegi_agebs_merida.geojson` + `geoportal_centro_historico.geojson` | [1](../1-INEGI-DENUE/README.md), [4](../4-GeoPortal-Merida/README.md) |
| 02 | Licencias de funcionamiento en el Centro por año y giro | `licenses_centro.csv` | `5-Government-Data-Request/clean/ayuntamiento_licencias_resumen_anual_centro_2015_2026.csv` | [5](../5-Government-Data-Request/README.md) |
| 03 The invisible hotel | Índice 2019 = 100: impuesto al hospedaje vs. turistas de hotel | `tax_vs_tourists.csv` | `5-Government-Data-Request/clean/aafy_impuesto_hospedaje_anual_2015_2026.csv` + tabla DataTur anual | [5](../5-Government-Data-Request/README.md), [9](../9-Augmented-Reality/README.md) |
| 03 | KPIs de vivienda: SHF, ENOE, Censo | `home_prices_2025T3.csv`, `kpis.csv` | `3-SIEGY-Yucatan/clean/shf_precios_vivienda_trimestral_estados.csv`, `enoe_yucatan_2025T2_vs_2026T2.csv`, `1-INEGI-DENUE/clean/censo_merida_yucatan_2010_2020.csv` | [3](../3-SIEGY-Yucatan/README.md), [1](../1-INEGI-DENUE/README.md) |
| 03 | Escena 3D (pydeck): 831 manzanas extruidas por `altura_p90_m`, color por cambio neto de negocios | `blocks_3d.geojson`, `blocks_3d.csv` | `8-LiDAR/clean/lidar_alturas_manzanas_centro.csv` + `9-Augmented-Reality/clean/ar1_denue_resumen_manzanas_centro.csv` + polígonos de `4-GeoPortal-Merida/raw/inegi_marco_geo_31_yucatan.zip` (capa `31m`) | [8](../8-LiDAR/README.md), [9](../9-Augmented-Reality/README.md), [4](../4-GeoPortal-Merida/README.md) |
| 04 Who tells the story | % de notas núcleo de la ZM por año + 4 titulares reales | `press_share.csv`, `press_headlines.csv` | `6-Web-Scraping/clean/prensa_local_articulos.csv` (`nucleo_tema & zona_metropolitana`) | [6](../6-Web-Scraping/README.md) |
| 04 | 10 colonias más mencionadas | `press_top_neighbourhoods.csv` | `6-Web-Scraping/clean/prensa_local_menciones_colonia.csv` | [6](../6-Web-Scraping/README.md) |
| 04 | Palabras clave en comentarios de YouTube + 5 videos más vistos | `youtube_keywords.csv`, `youtube_top_videos.csv` | `6-Web-Scraping/clean/youtube_comentarios_palabras_clave.csv`, `youtube_videos_merida.csv` | [6](../6-Web-Scraping/README.md) |
| 04 | Franja GDELT: artículos y % por voz | `gdelt_voices.csv` | `7-Self-Produced/clean/gdelt_merida_articulos.csv` | [7](../7-Self-Produced/README.md) |
| 05 Not Cancún, not yet | Crecimiento de pasajeros 2025 (índice 2019) y % internacional | `airports_annual.csv` | `9-Augmented-Reality/clean/ar3_asur_crecimiento_anual_mid_cun_oax.csv` | [9](../9-Augmented-Reality/README.md) |
| 05 | Mediana de vivienda vs. nacional (SHF 2025T3) | `home_prices_2025T3.csv` | `3-SIEGY-Yucatan/clean/shf_precios_vivienda_trimestral_estados.csv` | [3](../3-SIEGY-Yucatan/README.md) |
| 05 | Vistas de Wikipedia 2025 (inglés + español), índice 2019 | `wikipedia_index.csv` | `6-Web-Scraping/clean/wikipedia_vistas_mensuales.csv` | [6](../6-Web-Scraping/README.md) |
| 05 | Pasajeros mensuales, índice mismo mes 2019 = 100 | `airports_monthly.csv` | `2-Datos-Gob-Mx/clean/asur_pasajeros_mensual_mid_cun_oax.csv` | [2](../2-Datos-Gob-Mx/README.md) |

---

## Validación (`pytest dashboard/tests`, 13 pruebas)

Coinciden todas las cifras de la tabla de validación del prompt, salvo una:

- **Notas núcleo de la ZM: 332, no 331.** La regla de `nucleo_tema` y `zona_metropolitana`, escrita tal como está en el README de la sección 6, da 332 notas. 2019 (11.2%) y 2025 (31.5%) coinciden; la diferencia es una sola nota de 2026 (40 de 179 = 22.3%, contra 21.8% del prototipo). No se pudo saber cuál nota excluía el cálculo original: poner `\b` también en el núcleo deja 2026 en 21.8%, pero baja el total a 329 y cambia 2020 y 2022. La prueba fija 332 y deja comentada la diferencia.
- **AGEB que ganaron cafeterías: 212** sobre las 575 AGEB del DENUE; 211 de ellas tienen polígono en el mapa (una no está en el Marco Geoestadístico urbano).

## Limitaciones

- **Solo pesos nominales.** El selector nominal / real necesita el INPC anual promedio de INEGI. No se pudo bajar de una fuente oficial con link: las páginas de INEGI y de Banxico (cuadro SIE CP154) solo devuelven la estructura en JavaScript, sin los valores. La v1 deja solo "Nominal" y una nota. Para agregar el real: guardar el INPC mensual 2015–2025 (base 2Q jul 2018) con su URL en un `clean/` y deflactar en `prep.py`.
- **Plataformas digitales y el impuesto.** El README de la sección 5 dice que la recaudación de plataformas (Airbnb) va incluida en los totales, pero la AAFY no dio desde cuándo ni el desglose. Por eso no hay línea vertical: va la nota del prototipo.
- **Escena 3D:** modelo de elevación fotogramétrico de INEGI (2015), **no LiDAR**. La altura es el percentil 90 del nDSM por manzana y se exagera ×3 para que se vea. 40 de las 871 manzanas de AR 1 quedan fuera del recorte de alturas (sección 8). El mapa base de CARTO necesita internet.
- **Delimitación:** la prensa cubre la Zona Metropolitana (Mérida, Kanasín, Umán, Progreso, Conkal, Ucú); los datos espaciales cubren el municipio de Mérida.
- **Prensa:** es una muestra dirigida de 1,495 notas, no el universo. La regla `renta` sin límite de palabra también atrapa palabras como "enfrenta" (se dejó así porque así está la regla). Los titulares que se muestran se eligen por frase en `prep.py` (`HEADLINE_PICKS`) dentro de las notas núcleo.
- **Wikipedia:** las vistas caen en todo el mundo después de 2023; hay que comparar ciudades, no años.
- **YouTube:** la búsqueda por relevancia (25 nov 2026) favorece videos recientes, y algunos resultados son anuncios inmobiliarios.
- **2026 es parcial:** DataTur y AAFY hasta septiembre, ASUR hasta octubre, prensa hasta noviembre. Se marca con `*` y color más claro.
- El **QR de la escena AR** sigue como marcador (`[QR CODE to AR scene]`), como en el prototipo.
