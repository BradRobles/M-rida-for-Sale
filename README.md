# 1. INEGI DENUE (y Censo de Población y Vivienda)

Extracción y limpieza de los insumos de INEGI para la sección **1. INEGI DENUE** del proyecto *Mérida for Sale* (capítulo 2, *Las tiendas cambian*).

> **Nota:** Esta carpeta contiene únicamente el script de limpieza, las cifras crudas que no venían en un archivo descargable y las tablas CSV limpias. No incluye visualizaciones. Los ZIP del DENUE **no se duplican**: el script los lee de `9-Augmented-Reality/raw/`.

---

## Estructura de la carpeta

```text
1-INEGI-DENUE/
├── raw/
│   └── inegi_censo_cifras_publicadas.csv               # Cifras del Censo 2010/2020 transcritas de publicaciones INEGI (con URL)
├── scripts/
│   └── clean_inegi_denue.py                            # Script reproducible de limpieza
├── clean/
│   ├── denue_merida_conteos_categoria_2019_vs_2025.csv
│   ├── denue_merida_conteos_scian_2019_vs_2025.csv
│   ├── denue_merida_establecimientos_clave_2019_vs_2025.csv
│   ├── denue_merida_resumen_ageb_2019_vs_2025.csv
│   └── censo_merida_yucatan_2010_2020.csv
└── README.md
```

Crudos que usa y que ya están en el repositorio:
- `9-Augmented-Reality/raw/denue_31_1119_csv.zip` (DENUE Yucatán, noviembre 2019)
- `9-Augmented-Reality/raw/denue_31_0525_csv.zip` (DENUE Yucatán, mayo 2025)
- `4-GeoPortal-Merida/clean/geoportal_centro_historico.geojson` (polígono oficial del Centro Histórico)

---

## Fuentes incluidas

### 1. Principal — DENUE, ediciones 2019 y 2025 ✅
- **Fuente:** INEGI DENUE (`https://www.inegi.org.mx/app/descarga/?ti=6`), entidad Yucatán (`31`).
- **Filtrado y limpieza:**
  - Municipio `050` (Mérida), todas las localidades; duplicados por `id` eliminados.
  - Categorías del checklist por código SCIAN: **Hospedaje** (`721`), **Restaurantes y bares** (`722`, sin cafeterías), **Cafeterías** (`722515`) y **Abarrotes / tienda de la esquina** (`461110`).
  - **Centro Histórico por geometría, no por nombre de colonia:** cada establecimiento se ubica dentro o fuera del polígono de la *Zona de Monumentos Históricos* del GeoPortal (~9.30 km²). Así entran negocios del Centro registrados con otro nombre de asentamiento (por eso las cifras difieren de AR 1, que filtra por `nomb_asent`).
  - Cruce por `id` para marcar `Existia en 2019`, `Abrio despues de 2019` o `Cerro despues de 2019`.
  - Llave `cvegeo` de AGEB (13 dígitos), compatible con `4-GeoPortal-Merida/clean/inegi_agebs_merida_catalogo.csv` (520 de 575 AGEB cruzan; las demás son AGEB rurales o de comisarías).
- **Validación:** el total de Mérida en 2025 (**56,014** establecimientos) coincide con la cifra difundida por INEGI para el municipio.
- **Archivos limpios (`clean/`):**
  - `denue_merida_conteos_categoria_2019_vs_2025.csv`: conteos 2019 vs. 2025, cambio absoluto y %, para el municipio y para el Centro Histórico (10 filas).
  - `denue_merida_conteos_scian_2019_vs_2025.csv`: detalle por clase SCIAN dentro de cada categoría (21 clases).
  - `denue_merida_establecimientos_clave_2019_vs_2025.csv`: **16,936** establecimientos de las categorías clave con coordenadas, AGEB, `en_centro_historico` y `estado_cambio`.
  - `denue_merida_resumen_ageb_2019_vs_2025.csv`: **575** AGEB con conteos por categoría y total, por edición.

| Categoría | Municipio 2019 → 2025 | Centro Histórico 2019 → 2025 |
|---|---|---|
| Todos los establecimientos | 53,183 → 56,014 (+5.3%) | 9,199 → 8,010 (−12.9%) |
| Cafeterías (722515) | 641 → 938 (+46.3%) | 184 → 190 (+3.3%) |
| Restaurantes y bares (722) | 6,765 → 6,892 (+1.9%) | 891 → 829 (−7.0%) |
| Abarrotes (461110) | 3,429 → 3,676 (+7.2%) | 229 → 214 (−6.6%) |
| Hospedaje (721) | 304 → 311 (+2.3%) | 198 → 194 (−2.0%) |

> **Ojo al interpretar hospedaje:** el DENUE registra establecimientos, no anuncios de plataformas; las casas rentadas por Airbnb casi no aparecen como `721`.

### 2. Complemento A — Censo de Población y Vivienda 2010 y 2020 ⚠️ (parcial)
- **Incluido:** población de Mérida 2010 y 2020, viviendas particulares habitadas 2020 y viviendas deshabitadas y de uso temporal de Yucatán 2020, transcritas de publicaciones de INEGI (URL en cada fila).
- **Validación:** habitadas + deshabitadas y de uso temporal = viviendas visitadas (Yucatán 2020).
- **Archivo limpio:** `censo_merida_yucatan_2010_2020.csv`.
- **Pendiente:** *Principales resultados por AGEB y manzana urbana* 2010 y 2020 (Yucatán) en `https://www.inegi.org.mx/programas/ccpv/2020/` para tener viviendas deshabitadas y de uso temporal por AGEB del Centro. Guardar en `raw/` y unir por `cvegeo`.

### 3. Complemento B — DENUE de Oaxaca, San Miguel de Allende y Playa del Carmen ❌ (pendiente)
- No hay crudos en el repositorio. Descargar el DENUE de Oaxaca (`20`), Guanajuato (`11`) y Quintana Roo (`23`) para las mismas ediciones y reutilizar `load_denue()` cambiando entidad y municipio (Oaxaca de Juárez `067`, San Miguel de Allende `003`, Solidaridad `008`).

---

## Cómo regenerar los archivos limpios

```bash
python 1-INEGI-DENUE/scripts/clean_inegi_denue.py
```
