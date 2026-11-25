# 8. LiDAR (Modelos Digitales de Elevación de INEGI)

Extracción y limpieza del modelo de alturas para la sección **8. LiDAR** del proyecto *Mérida for Sale*: altura aproximada de lo construido por manzana del Centro Histórico, para dar volumen a la escena AR 1 (sección 9).

> **Nota:** Esta carpeta contiene el script, los metadatos transcritos y las salidas limpias. No incluye visualizaciones. Los rásters de INEGI (~330 MB con los extraídos) **no van en git**: el script los vuelve a descargar.

> ⚠️ **Hallazgo importante:** INEGI publica estos modelos dentro de su serie "alta resolución / LiDAR" (las URL están bajo `.../1_10_000/lidar/`), pero **para las cartas que cubren el Centro de Mérida el modelo no viene de LiDAR aerotransportado**: según los metadatos de cada ZIP, es **fotogrametría de imágenes ópticas de satélite**. Para el uso que buscamos (volumen aproximado por manzana) sirve, pero en el texto del proyecto hay que llamarlo "modelo de elevación de alta resolución de INEGI", no "LiDAR".

---

## Estructura de la carpeta

```text
8-LiDAR/
├── raw/
│   ├── lidar_metadatos_transcritos.csv     # Cartas, modelo, resolución, fechas de insumo y URL (fuente de verdad para las descargas)
│   └── inegi_lidar/                        # ZIP de INEGI y extraídos (en .gitignore; los baja el script)
├── scripts/
│   └── clean_lidar.py                      # Descarga, mosaico, recorte, nDSM y estadísticas por manzana
├── clean/
│   ├── lidar_alturas_manzanas_centro.csv
│   └── lidar_ndsm_centro.tif               # Cloud Optimized GeoTIFF, EPSG:4326, 5.0 MB
└── README.md
```

Crudos de otras secciones que usa:
- `4-GeoPortal-Merida/clean/geoportal_centro_historico.geojson` (polígono del Centro Histórico)
- `4-GeoPortal-Merida/raw/inegi_marco_geo_31_yucatan.zip` (capa `31m`, manzanas)
- `9-Augmented-Reality/clean/ar1_denue_resumen_manzanas_centro.csv` (para comprobar el cruce)

---

## Fuentes incluidas

### 1. Principal — INEGI, MDE de alta resolución 1:10 000 a 5 m, superficie (MDS) y terreno (MDT) ⚠️ (no es LiDAR)
- **Dónde se encontró:** pestaña *Descargas* de `https://www.inegi.org.mx/temas/relieve/continental/`, búsqueda `F16C52` (la carta 1:50 000 de Mérida). El catálogo sale de la API interna `https://www.inegi.org.mx/app/api/productos/interna_v2/componente/mapas/lista/resultados/`; la descarga es directa (no requiere registro).
- **Cartas que tocan el Centro + 500 m:** solo **F16C52A1** y **F16C52A2** (límite de A1: −89.668 a −89.610 de longitud y 20.936 a 21.001 de latitud; el Centro va de ~−89.64 a −89.60).
- **Archivos (edición 2016, formato BIL, `ITRF2008 UTM 16N`):**

| Carta | Modelo | UPC | URL |
|---|---|---|---|
| F16C52A1 | MDS | 702825010672 | `https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/imagen_cartografica/1_10_000/lidar/superficie_ASCII/702825010672_b.zip` |
| F16C52A2 | MDS | 702825010673 | `.../1_10_000/lidar/superficie_ASCII/702825010673_b.zip` |
| F16C52A1 | MDT | 702825010164 | `.../1_10_000/lidar/Terreno_ASCII/702825010164_b.zip` |
| F16C52A2 | MDT | 702825010165 | `.../1_10_000/lidar/Terreno_ASCII/702825010165_b.zip` |

- **Fecha:** la nube de puntos fotogramétrica se creó el **2015-07-28** (publicación 2016-03-31). INEGI no publica la fecha de toma de las imágenes. Es una **foto de 2015**, anterior al auge reciente de torres: sirve como línea base, no como cambio en el tiempo.
- **Validación con un segundo producto (1.5 m, edición 2025):** mismo catálogo, mismas cartas, MDS y MDT a **1.5 m** (UPC 794551133323, 794551133330, 794551140758 y 794551140765; imagen estereoscópica del **2017-03-11**, nube de puntos del 2023-07-05). También es fotogramétrico de satélite. Se usa como columnas `*_1_5m` para validar, no como dato principal, porque la especificación pide 5 m.
- **Plan B no usado:** el modelo continuo de superficie LiDAR de 15 m (`https://inegi.org.mx/contenidos/temas/relieve/continental/doc/lidar_superficie.pdf`) no hizo falta porque el producto de 5 m existe y se descarga solo.
- **Procesamiento (`clean_lidar.py`):**
  1. Descarga los 8 ZIP listados en `raw/lidar_metadatos_transcritos.csv` (caché en `raw/inegi_lidar/`) y los extrae.
  2. Mosaico A1 + A2 y recorte al polígono del Centro Histórico con **500 m** de margen (en metros, UTM 16N): 1,080 × 1,218 celdas de 5 m, 0% sin dato.
  3. **nDSM = MDS − MDT** (altura sobre el terreno).
  4. Manzanas del Marco Geoestadístico (capa `31m`, municipio `050`, localidad `0001`) que tocan el recorte, reproyectadas de `MEXICO_ITRF_2008_LCC` a la malla del ráster; cada celda se asigna a la manzana que contiene su centro.
  5. Por manzana: media, percentil 90, máximo, % de celdas > 6 m y número de celdas. Las celdas negativas (ruido, MDS < MDT) cuentan como 0 m en las alturas; su % se reporta aparte.
  6. Exporta el nDSM a COG en `EPSG:4326` (bilineal, compresión DEFLATE).
- **Llaves de unión:** `clave_manzana` (`AGEB-MZA`, mismo formato que AR 1), `cvegeo` de 16 dígitos (los 13 primeros = `cvegeo` de AGEB del GeoPortal) y `centroide_lat` / `centroide_lon`.

### Validación
- **Cruce con AR 1:** **831 de 871** manzanas de `ar1_denue_resumen_manzanas_centro.csv` (**95.4%**) cruzan por `clave_manzana` con dato de altura. Las 40 que faltan están **fuera del Centro + 500 m** (AR 1 filtra por el nombre de asentamiento "Centro", que incluye registros lejanos, p. ej. AGEB 2644, 6492, 3549); no es un problema de llaves.
- **Sentido común (462 manzanas dentro del polígono del Centro):**

| Medida (Centro) | 5 m (principal) | 1.5 m (validación) |
|---|---|---|
| Mediana de `altura_media_m` | 2.58 m | 3.93 m |
| Mediana de `altura_p90_m` | 4.20 m | 6.83 m |
| % de manzanas con p90 entre 3 y 8 m | 67.1% | 72.7% |
| Correlación de `altura_media_m` entre productos | 0.90 | |

  - La **media** sale por debajo de 3 m en 276 manzanas porque mezcla techos con patios, jardines y calles angostas; a 5 m el borde del edificio se suaviza. Para extruir la escena AR conviene **`altura_p90_m`** (altura típica de lo construido), que cae mayormente entre 3 y 8 m, como se esperaba para casas de uno o dos niveles. El producto de 1.5 m da alturas entre 1.3 m (media) y 2.6 m (p90) mayores, con la misma geografía (correlación 0.90).
  - **Mayores de 40 m (2 manzanas, revisadas):** `0224-010` (máx. 61.9 m; Av. Colón y Paseo de Montejo, donde están los hoteles de ~17 pisos) y `0440-003` (máx. 42.0 m; una sola celda alta, probablemente torre o antena; su p90 es 18.6 m a 5 m y 10.3 m a 1.5 m). Se dejan, no son errores de llave.
  - **Valores negativos:** ninguna manzana tiene media negativa; 347 tienen alguna celda negativa (mínimo −3.56 m, máximo 20% de celdas en una manzana pequeña). Es ruido fotogramétrico y se trunca a 0.
  - 40 manzanas del recorte tienen menos de 20 celdas (manzanas muy pequeñas o en el borde); usar con cuidado.

### Archivos limpios (`clean/`)
- `lidar_alturas_manzanas_centro.csv`: **2,389** manzanas del recorte (Centro + 500 m), **462** dentro del polígono del Centro (`en_centro_historico`), con `en_ar1`, `clave_manzana`, `cvegeo`, centroide, `area_m2`, `altura_media_m`, `altura_p90_m`, `altura_max_m`, `pct_celdas_mayor_6m`, `n_celdas`, `pct_celdas_negativas`, `ndsm_min_m` y las columnas de validación `altura_media_m_1_5m`, `altura_p90_m_1_5m`, `n_celdas_1_5m`.
- `lidar_ndsm_centro.tif`: nDSM de 5 m en `EPSG:4326`, Cloud Optimized GeoTIFF de **5.0 MB**.

---

## Pendientes
- Confirmar con INEGI (atención a usuarios) si existe LiDAR aerotransportado real para Mérida; en el catálogo no aparece para estas cartas.
- Si la escena AR necesita más detalle, el nDSM de 1.5 m ya está calculado en memoria por el script; se puede exportar igual que el de 5 m (son ~14.6 millones de celdas; comprobar que el COG quede bajo 50 MB).

---

## Cómo regenerar los archivos limpios

```bash
python 8-LiDAR/scripts/clean_lidar.py
```

La primera corrida descarga ~165 MB de INEGI; las siguientes usan la caché de `raw/inegi_lidar/`.
