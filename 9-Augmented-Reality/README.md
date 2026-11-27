# 9. Augmented Reality (Escenas AR 1, 2 y 3)

Extracción y limpieza de las tres fuentes requeridas para las escenas de Realidad Aumentada del proyecto *Mérida for Sale*.

> **Nota:** Esta carpeta contiene únicamente los datos crudos descargados, el script de extracción/limpieza y las tablas CSV limpias listas para usarse en las escenas 3D/AR. No incluye visualizaciones ni modelos 3D.

---

## Estructura de la carpeta

```text
9-Augmented-Reality/
├── raw/
│   ├── denue_31_1119_csv.zip                   # INEGI DENUE Yucatán nov 2019
│   ├── denue_31_0525_csv.zip                   # INEGI DENUE Yucatán may 2025
│   ├── datatur_merida_turistas_2015_2026.html  # Respuesta DataTur (Mérida)
│   └── Trafico_de_pasajeros_ASUR.xlsx          # Tráfico de pasajeros ASUR
├── scripts/
│   └── clean_ar_scenes.py                      # Script reproducible de limpieza
├── clean/
│   ├── ar1_denue_merida_centro_2019_vs_2025.csv
│   ├── ar1_denue_resumen_manzanas_centro.csv
│   ├── ar2_datatur_merida_turistas_mensual_2015_2026.csv
│   ├── ar2_datatur_merida_turistas_anual_2015_2026.csv
│   ├── ar3_asur_trafico_mensual_mid_cun_oax.csv
│   └── ar3_asur_crecimiento_anual_mid_cun_oax.csv
└── README.md
```

---

## Escena AR 1 — Manzana del Centro con negocios 2019 vs. 2025

- **Fuente:** INEGI DENUE (`https://www.inegi.org.mx/app/descarga/?ti=6`), ediciones **noviembre 2019** (`denue_31_1119_csv.zip`) y **mayo 2025** (`denue_31_0525_csv.zip`), entidad Yucatán (`31`).
- **Filtrado y limpieza:**
  - Municipio `050` (Mérida), localidad `0001` (cabecera municipal) y asentamientos de la zona Centro (`CENTRO`, `CENTRO HISTORICO`, `MERIDA CENTRO`, `COL. CENTRO`, `COLONIA CENTRO`, `ZONA CENTRO`), excluyendo comisarías homónimas.
  - Cruce por `id` de establecimiento entre 2019 y 2025 para clasificar cada negocio en `Existia en 2019`, `Abrio despues de 2019` o `Cerro despues de 2019`.
  - Clasificación por código SCIAN en `sector_turistico` (`Hospedaje`, `Alimentos y bebidas`, `Tiendas de abarrotes`, `Comercio y otros servicios`).
- **Archivos limpios:**
  - `clean/ar1_denue_merida_centro_2019_vs_2025.csv` (14,207 registros georreferenciados con `ageb`, `manzana`, `clave_manzana`, `latitud`, `longitud` y `estado_cambio`).
  - `clean/ar1_denue_resumen_manzanas_centro.csv` (871 manzanas con conteos 2019 vs. 2025, cambio neto y centroide para elegir fácilmente la manzana de la escena AR).

---

## Escena AR 2 — Turistas nacionales vs. extranjeros como barras 3D

- **Fuente:** SECTUR / DataTur (`https://monitoreohotelero.sectur.gob.mx/Reportes/Menu.aspx`), reporte `481` (*Ocupación en hoteles y moteles por centro turístico, corte mensual*), centro turístico **Mérida** (`68`), indicadores *Llegadas de turistas*, *Llegadas de turistas residentes* (nacionales) y *Llegadas de turistas no residentes* (extranjeros), total de categorías hoteleras.
- **Cobertura:** Enero 2015 – septiembre 2026 (141 meses; 2026 es parcial).
- **Archivos limpios:**
  - `clean/ar2_datatur_merida_turistas_mensual_2015_2026.csv` (141 meses).
  - `clean/ar2_datatur_merida_turistas_anual_2015_2026.csv` (12 años, con `pct_extranjeros`).

---

## Escena AR 3 — Crecimiento aeroportuario Mérida vs. Cancún vs. Oaxaca

- **Fuente:** ASUR (`https://www.asur.com.mx/trafico-de-pasajeros-1`), archivo oficial `Trafico_de_pasajeros_ASUR.xlsx`, hojas `PAX MID` (Mérida), `PAX CUN` (Cancún) y `PAX OAX` (Oaxaca).
- **Cobertura:** Enero 2000 – octubre 2026 (966 filas aeropuerto-mes; 2026 es parcial ene–oct).
- **Archivos limpios:**
  - `clean/ar3_asur_trafico_mensual_mid_cun_oax.csv` (966 filas con `pasajeros_nacional`, `pasajeros_internacional`, `pasajeros_total`).
  - `clean/ar3_asur_crecimiento_anual_mid_cun_oax.csv` (81 filas aeropuerto-año con `crecimiento_anual_pct`, `indice_2015_100` e `indice_2019_100`).

---

## Cómo regenerar los archivos limpios

```bash
python 9-Augmented-Reality/scripts/clean_ar_scenes.py
```
