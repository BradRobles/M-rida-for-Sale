# 2. datos.gob.mx (DataTur y ASUR)

Extracción y limpieza de los insumos de turismo y aviación para la sección **2. datos.gob.mx** del proyecto *Mérida for Sale* (capítulo 1, *La llegada*).

> **Nota:** Esta carpeta contiene únicamente el script de limpieza y las tablas CSV limpias. Los crudos **no se duplican**: el script los lee de `9-Augmented-Reality/raw/`. No incluye visualizaciones.

---

## Estructura de la carpeta

```text
2-Datos-Gob-Mx/
├── raw/                                                     # (vacía: crudos en 9-Augmented-Reality/raw/)
├── scripts/
│   └── clean_datatur_asur.py                                # Script reproducible de limpieza
├── clean/
│   ├── datatur_merida_llegadas_categoria_mensual_2015_2026.csv
│   ├── datatur_merida_llegadas_categoria_anual_2015_2026.csv
│   ├── asur_pasajeros_mensual_mid_cun_oax.csv
│   ├── asur_pasajeros_acumulado_mismo_periodo_mid_cun_oax.csv
│   └── asur_validacion_totales_anuales.csv
└── README.md
```

Crudos que usa: `9-Augmented-Reality/raw/datatur_merida_turistas_2015_2026.html` y `9-Augmented-Reality/raw/Trafico_de_pasajeros_ASUR.xlsx`.

---

## Fuentes incluidas

### 1. Principal — DataTur, actividad hotelera de Mérida ✅
- **Fuente:** SECTUR / DataTur (`https://monitoreohotelero.sectur.gob.mx/Reportes/Menu.aspx`), reporte `481`, centro turístico **Mérida**.
- **Qué agrega frente a AR 2:** el desglose por **categoría hotelera** (1 a 5 estrellas y total), con nacionales (residentes), extranjeros (no residentes), `pct_extranjeros` y `pct_del_total_mes` (qué parte de las llegadas capta cada categoría).
- **Validaciones:** nacionales + extranjeros = total en cada categoría y mes; la suma de las cinco categorías = total en los 141 meses.
- **Cobertura:** enero 2015 – septiembre 2026 (2026 parcial).
- **Archivos limpios:**
  - `datatur_merida_llegadas_categoria_mensual_2015_2026.csv` (846 filas = 141 meses × 6 categorías).
  - `datatur_merida_llegadas_categoria_anual_2015_2026.csv` (72 filas, con `meses_reportados`).
- **Ojo:** algunos meses de hoteles de 1 estrella reportan 0 extranjeros (p. ej., todo 2025). Así viene en DataTur; no se corrigió.

### 2. Complemento A — ASUR, tráfico mensual de pasajeros ✅
- **Fuente:** ASUR (`https://www.asur.com.mx/trafico-de-pasajeros-1`), hojas `PAX MID`, `PAX CUN` y `PAX OAX`. Cancún (`CUN`) es el aeropuerto de Playa del Carmen.
- **Qué agrega frente a AR 3:** `pct_internacional`, `variacion_anual_pct` mes contra mismo mes del año anterior e `indice_mismo_mes_2019_100`, más una tabla acumulada enero–octubre de cada año para comparar 2026 (parcial) en igualdad de meses.
- **Validación:** la suma de los meses se compara con el renglón `Total AAAA` del propio archivo (`asur_validacion_totales_anuales.csv`). Cuadra en todos los años, salvo **2008**, donde el renglón total de ASUR no coincide con sus meses (se reporta, no se corrige).
- **Archivos limpios:** `asur_pasajeros_mensual_mid_cun_oax.csv` (966 filas aeropuerto-mes, ene 2000 – oct 2026), `asur_pasajeros_acumulado_mismo_periodo_mid_cun_oax.csv` y `asur_validacion_totales_anuales.csv`.

### 3. Complemento B — DataTur de Oaxaca, San Miguel de Allende y Playa del Carmen ❌ (pendiente)
- Descargar el mismo reporte `481` para esos centros turísticos, guardarlo en `raw/` y reutilizar `build_datatur()` cambiando el nombre del archivo.

---

## Cómo regenerar los archivos limpios

```bash
python 2-Datos-Gob-Mx/scripts/clean_datatur_asur.py
```
