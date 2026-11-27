# 4. GeoPortal de Mérida (y Complementos Geográficos)

Extracción y limpieza de los insumos geográficos para la sección **4. GeoPortal de Mérida** del proyecto *Mérida for Sale*.

> **Nota:** Esta carpeta contiene únicamente los datos crudos, el script de limpieza y las capas GeoJSON/CSV listas para usarse en mapas y cruces espaciales. No incluye visualizaciones.

---

## Estructura de la carpeta

```text
4-GeoPortal-Merida/
├── raw/
│   ├── colonias.geojson                          # GeoPortal: Colonias de Mérida (500)
│   ├── z_monu_historicos_2040.geojson            # GeoPortal: Zona de Monumentos Históricos
│   ├── z_patri_cul_muni_merida_2040.geojson      # GeoPortal: Zonas Patrimoniales (73)
│   ├── osm_merida_pois.json                      # Respuesta cruda de Overpass API (OSM)
│   └── inegi_marco_geo_31_yucatan.zip            # Marco Geoestadístico INEGI (Yucatán)
├── scripts/
│   └── clean_geoportal_complements.py            # Script reproducible de limpieza y reproyección
├── clean/
│   ├── geoportal_colonias_merida.geojson
│   ├── geoportal_colonias_merida_catalogo.csv
│   ├── geoportal_centro_historico.geojson
│   ├── geoportal_zonas_patrimoniales.geojson
│   ├── geoportal_zonas_patrimoniales_catalogo.csv
│   ├── osm_merida_pois_turismo_cafes.csv
│   ├── osm_merida_pois_turismo_cafes.geojson
│   ├── inegi_agebs_merida.geojson
│   ├── inegi_agebs_merida_catalogo.csv
│   └── inegi_municipio_merida.geojson
└── README.md
```

---

## Fuentes incluidas

### 1. Principal — GeoPortal de Mérida (`geoportal.merida.gob.mx`) ✅
Descargado desde el visor oficial en coordenadas **WGS84 (`EPSG:4326`)** y limpiado en `clean/`:
- `geoportal_colonias_merida.geojson` y `geoportal_colonias_merida_catalogo.csv`: **500** colonias/fraccionamientos de Mérida.
- `geoportal_centro_historico.geojson`: polígono oficial de la **Zona de Monumentos Históricos** (Centro Histórico, ~9.30 km²).
- `geoportal_zonas_patrimoniales.geojson` y `geoportal_zonas_patrimoniales_catalogo.csv`: **73** polígonos de zonas patrimoniales culturales municipales.

### 2. Complemento A — OpenStreetMap (Overpass API) ✅
- **Cobertura:** Área urbana de Mérida (`20.85, -89.78` a `21.12, -89.48`), hoteles, hostales, casas de huéspedes, moteles y cafeterías.
- **Archivos limpios (`clean/`):**
  - `osm_merida_pois_turismo_cafes.csv` y `osm_merida_pois_turismo_cafes.geojson`: **404** puntos con `osm_id`, `nombre`, `categoria`, `subcategoria`, dirección, `sitio_web`, `latitud` y `longitud` (`EPSG:4326`).

### 3. Complemento B — Marco Geoestadístico de INEGI (AGEBs de Mérida) ✅
- **Fuente:** INEGI Marco Geoestadístico (`31_yucatan.zip`), capas `31a` (AGEBs urbanas) y `31mun` (municipios), filtradas a **Mérida** (`CVE_MUN = 050`) y reproyectadas de `MEXICO_ITRF_2008_LCC` a **WGS84 (`EPSG:4326`)**.
- **Archivos limpios (`clean/`):**
  - `inegi_agebs_merida.geojson` y `inegi_agebs_merida_catalogo.csv`: **541** AGEBs urbanas de Mérida (llave `cvegeo` / `cve_ageb`).
  - `inegi_municipio_merida.geojson`: límite municipal de Mérida.

---

## Cómo regenerar los archivos limpios

```bash
python 4-GeoPortal-Merida/scripts/clean_geoportal_complements.py
```
