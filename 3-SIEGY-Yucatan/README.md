# 3. SIEGY Yucatán (Sefotur, SHF y ENOE)

Extracción y limpieza de los indicadores estatales para la sección **3. SIEGY (Yucatán)** del proyecto *Mérida for Sale* (capítulos 1 y 3).

> **Nota:** SIEGY no tiene un portal de descarga confirmado; se usó el respaldo verificado del checklist (reportes mensuales de Sefotur). Los reportes oficiales son PDF, así que `raw/` guarda **cada cifra transcrita con el reporte y la URL de donde se copió**. No incluye visualizaciones.

---

## Estructura de la carpeta

```text
3-SIEGY-Yucatan/
├── raw/
│   ├── sefotur_cifras_transcritas.csv            # 154 cifras de 22 reportes Sefotur (meses de 2024 a sep 2026)
│   ├── shf_iieg_cifras_transcritas.csv           # Precios SHF por estado, 3T2025 – 2T2026
│   └── inegi_enoe_cifras_transcritas.csv         # Boletines INEGI ENOE y Pobreza Laboral, Yucatán 2T2026
├── scripts/
│   └── clean_siegy_complements.py                # Script reproducible de limpieza y validación
├── clean/
│   ├── sefotur_merida_ocupacion_hotelera_mensual.csv
│   ├── sefotur_yucatan_turistas_origen_mensual.csv
│   ├── sefotur_yucatan_ingreso_hotelero_mensual.csv
│   ├── sefotur_validacion_vs_datatur_asur.csv
│   ├── shf_precios_vivienda_trimestral_estados.csv
│   └── enoe_yucatan_2025T2_vs_2026T2.csv
└── README.md
```

---

## Fuentes incluidas

### 1. Principal — Sefotur, *Resultados de la actividad turística* ⚠️ (respaldo de SIEGY)
- **Fuente:** `https://sefotur.yucatan.gob.mx/secciones/dinamicas/18` (con datos de DataTur, ASUR y AAFY).
- **Solo lo que no está en la sección 2:**
  - `sefotur_merida_ocupacion_hotelera_mensual.csv`: ocupación hotelera de la Ciudad de Mérida (%), 26 meses (todo 2025 y ene–sep 2026; 2024 parcial).
  - `sefotur_yucatan_turistas_origen_mensual.csv`: turistas con pernocta del **estado**, nacionales vs. internacionales. En abr–sep 2026 Sefotur publica solo el porcentaje; se deja así (`metodo_pct`) sin inventar conteos.
  - `sefotur_yucatan_ingreso_hotelero_mensual.csv`: ingreso hotelero estatal (millones de pesos corrientes, fuente AAFY), en su mes real (Sefotur lo publica con un mes de rezago).
- **Validación contra crudos:** `sefotur_validacion_vs_datatur_asur.csv` compara 53 cifras de Sefotur con DataTur y ASUR de la sección 2: **53 de 53 coinciden exactamente**. También se comprueba que nacionales + internacionales = total y que el promedio mensual de ocupación 2025 (57.8%) = acumulado anual impreso.

### 2. Complemento A — Índice SHF de Precios de la Vivienda ⚠️ (parcial)
- **Fuente:** SHF, vía fichas trimestrales del IIEG Jalisco (cifras preliminares), 3T2025 – 2T2026.
- **Archivo limpio:** `shf_precios_vivienda_trimestral_estados.csv`: precio promedio, mediana, percentiles 25/75, `razon_p75_p25`, `mediana_vs_nacional_pct` y lugar nacional para Yucatán, Quintana Roo (Playa del Carmen), Oaxaca, Guanajuato (San Miguel de Allende) y Nacional.
- **Ojo:** precio promedio y percentiles dependen de qué viviendas se valuaron cada trimestre; **no son un índice**. Para la tendencia 2017–2025 falta el nivel del Índice SHF por estado y municipio (`gob.mx/shf`, tabulado del índice), que no se pudo leer con certeza.

### 3. Complemento B — ENOE (INEGI) ⚠️ (estatal)
- **Fuente:** INEGI, boletines *ENOE Yucatán* y *Pobreza Laboral Yucatán*, 2T2026 (publicados en agosto de 2026).
- **Archivo limpio:** `enoe_yucatan_2025T2_vs_2026T2.csv`: PEA, ocupados, desocupación, informalidad, subocupación, ocupados por tramo de salario mínimo (con % de ocupados), pobreza laboral y masa salarial real.
- **Validación:** la suma de los tramos de ingreso = población ocupada en ambos trimestres.
- **Pendiente:** indicadores de la **ciudad** de Mérida (ciudad autorrepresentada) desde los tabulados de ENOE; en el PDF de INEGI no se pudo asignar cada valor a su ciudad con certeza, así que no se incluyeron.

---

## Cómo regenerar los archivos limpios

Correr después de la sección 2 (la validación usa sus archivos limpios):

```bash
python 2-Datos-Gob-Mx/scripts/clean_datatur_asur.py
python 3-SIEGY-Yucatan/scripts/clean_siegy_complements.py
```
