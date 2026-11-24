# 5. Government Data Request (Solicitudes de Transparencia)

Limpieza y estandarización de las respuestas oficiales obtenidas vía la Plataforma Nacional de Transparencia (PNT) para la visualización de **Data Request** del proyecto *Mérida for Sale*.

> **Nota:** Esta carpeta contiene únicamente los datos crudos, el script de limpieza y las tablas limpias listas para graficar. No incluye visualizaciones.

---

## Estructura de la carpeta

```text
5-Government-Data-Request/
├── raw/
│   ├── Resp. Fol. 1191207426000093 (1).pdf       # Respuesta oficial AAFY (Impuesto sobre Hospedaje)
│   └── 609/
│       ├── 1190579126000609 PROYECTO LIC. DEL CENTRO.pdf  # Respuesta Desarrollo Urbano (Ayuntamiento)
│       ├── 609_fnz.pdf                                    # Respuesta Finanzas y Tesorería (Ayuntamiento)
│       └── licencias para transparencia 2015-2026.xls     # Padrón de licencias de funcionamiento
├── scripts/
│   └── clean_government_requests.py               # Script reproducible de limpieza
├── clean/
│   ├── aafy_impuesto_hospedaje_mensual_2015_2026.csv
│   ├── aafy_impuesto_hospedaje_anual_2015_2026.csv
│   ├── ayuntamiento_licencias_funcionamiento_centro_2015_2026.csv
│   ├── ayuntamiento_licencias_excluidas_fuera_centro.csv
│   └── ayuntamiento_licencias_resumen_anual_centro_2015_2026.csv
└── README.md
```

---

## 1. AAFY — Impuesto por Prestación de Servicios de Hospedaje

- **Fuente:** Oficio `AAFY/DR/R/AD/0191/2026`, Solicitud Folio `1191207426000093` (14 de octubre de 2026).
- **Cobertura:** Enero 2015 – septiembre 2026 (141 meses).
  - `2015–2025`: cifras definitivas.
  - `2026` (ene–sep): cifras preliminares (`preliminar`). Octubre–diciembre 2026 no están disponibles aún.
- **Limitación documentada por la AAFY:** La recaudación de plataformas digitales de alojamiento (p. ej. Airbnb) está **incluida en los montos totales**; la dependencia indicó no contar con el desglose separado.
- **Archivos limpios:**
  - `clean/aafy_impuesto_hospedaje_mensual_2015_2026.csv`: serie mensual ordenada (`anio`, `mes_num`, `mes`, `fecha`, `recaudacion_mxn`, `tipo_cifra`).
  - `clean/aafy_impuesto_hospedaje_anual_2015_2026.csv`: resumen anual (`anio`, `tipo_cifra`, `meses_reportados`, `recaudacion_total_mxn`, `promedio_mensual_mxn`).

---

## 2. Ayuntamiento de Mérida — Licencias de Funcionamiento (Centro)

- **Fuente:** Solicitud Folio `1190579126000609`:
  - **Dirección de Finanzas y Tesorería Municipal** (`609_fnz.pdf`, oficio `DFT/SCA/1639/2026`): entregó `licencias para transparencia 2015-2026.xls` con el padrón de licencias de funcionamiento en la zona Centro (enero 2015 – septiembre 2026).
  - **Dirección de Desarrollo Urbano** (`1190579126000609 PROYECTO LIC. DEL CENTRO.pdf`, oficio `DDU/SJ/DCIU/AT-490/2026`): remitió a consulta manual en la PNT para licencias de construcción/remodelación (no incluidas en el Excel).
- **Reglas de limpieza aplicadas (`scripts/clean_government_requests.py`):**
  1. **Unificación de 12 hojas (`2015`–`2026`):** se corrigió el encabezado de la hoja `2026`, cuya primera columna venía nombrada `2026` en lugar de `Fecha Registro`.
  2. **Normalización de texto:** se eliminaron espacios múltiples y el relleno de ancho fijo (~250 caracteres) en `Giro Desarrollo Urbano`, además de unificar la variante `LIBRERIA` → `LIBRERÍA`.
  3. **Valores nulos en giro:** los 2 registros de 2025 sin giro (`NIDUM FROZEN YOGURT Y COFFE BAR` y `LA KEECH`) se conservaron marcados como `NO ESPECIFICADO`.
  4. **Titular y tipo de persona:** se derivó `tipo_persona` (`FISICA` vs `MORAL`) a partir de los apellidos y se consolidó `titular`.
  5. **Filtrado geográfico de Centro:** se excluyó 1 registro de 2021 cuya colonia es `CENTRO POBLACION DZUNUNCAN` (`MOTEL EL BOSQUE`, en la comisaría de Dzununcán, fuera del Centro de Mérida) y se guardó aparte en `clean/ayuntamiento_licencias_excluidas_fuera_centro.csv` para trazabilidad.
  6. **Clasificación analítica (`categoria_giro`):** agrupa los giros en `Hospedaje`, `Alimentos y Bebidas`, `Comercio y otros servicios` y `No especificado`.
- **Archivos limpios:**
  - `clean/ayuntamiento_licencias_funcionamiento_centro_2015_2026.csv` (1,254 registros).
  - `clean/ayuntamiento_licencias_excluidas_fuera_centro.csv` (1 registro).
  - `clean/ayuntamiento_licencias_resumen_anual_centro_2015_2026.csv` (conteo por año y `categoria_giro`).

---

## Cómo regenerar los archivos limpios

```bash
/Users/bradechio/Developer/data-lab/merida-gentrificada/.venv/bin/python \
  /Users/bradechio/Developer/data-lab/merida-gentrificada/5-Government-Data-Request/scripts/clean_government_requests.py
```
