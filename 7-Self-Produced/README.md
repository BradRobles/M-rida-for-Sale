# 7. Self-produced (grabación propia de GDELT y trabajo de campo)

Datos producidos por el equipo para la sección **7. Self-produced** del proyecto *Mérida for Sale* (capítulo 4, *Quién cuenta la historia*): una grabación propia de noticias sobre Mérida con GDELT y la infraestructura lista para el trabajo de campo (letreros e "índice del americano").

> **Nota:** Esta carpeta contiene los scripts, los crudos producidos por nosotros (stream de GDELT y caché de la DOC API) y las tablas CSV limpias. No incluye visualizaciones. Los complementos A y B **no se simularon**: quedan las plantillas y el script de limpieza.

---

## Estructura de la carpeta

```text
7-Self-Produced/
├── raw/
│   ├── gdelt_stream/
│   │   ├── gkg_merida_YYYY-MM-DD.csv        # Grabación propia: documentos GKG de Mérida, un archivo por día UTC
│   │   ├── _procesados.txt                  # Archivos GKG ya leídos, para reanudar (estado local, en .gitignore)
│   │   └── _recorder.log / .pid / .lock     # Estado local del grabador (en .gitignore)
│   ├── gdelt_doc/                           # Respuestas JSON de la DOC API (caché) y _ventanas.json
│   └── campo/
│       ├── fotos_letreros/                  # Fotos geoetiquetadas de letreros (en .gitignore)
│       ├── fotos_menus/                     # Fotos de menús (en .gitignore)
│       ├── letreros_plantilla.csv           # foto, fecha, latitud, longitud, colonia, idioma_letrero, tipo, notas
│       └── americano_plantilla.csv          # fecha, negocio, colonia, latitud, longitud, precio_americano_mxn, tamano_ml, foto_menu
├── scripts/
│   ├── gdelt_stream_recorder.py             # Grabador: cada 15 min lee GKG 2.1 y guarda lo de Mérida
│   ├── clean_gdelt.py                       # DOC API (con caché) + limpieza y clasificación
│   ├── clasificacion.py                     # Reglas de voz (local/nacional/internacional) y temas; las usa también la sección 6
│   └── clean_field_audit.py                 # EXIF + punto en polígono + limpieza de las plantillas de campo
├── clean/
│   ├── gdelt_merida_articulos.csv
│   ├── gdelt_merida_tono_semanal_por_voz.csv
│   ├── gdelt_merida_temas_por_voz.csv
│   └── gdelt_merida_timeline_diaria_por_voz.csv
└── README.md
```

---

## Fuentes incluidas

### 1. Principal — Noticias sobre Mérida con GDELT ⚠️ (stream propio corriendo pero casi vacío; respaldo DOC API ✅)

#### 1a. Stream propio (lo que lo hace "self-produced") ⚠️
- **Fuente:** GDELT 2.0 Global Knowledge Graph 2.1, cada 15 minutos: `http://data.gdeltproject.org/gdeltv2/lastupdate.txt` (inglés) y `http://data.gdeltproject.org/gdeltv2/lastupdate-translation.txt` (traducido; ahí cae la prensa en español). Ambas redirigen a `https://`. Codebook: `http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf`.
- **Filtro:** documentos con una ubicación de `V2EnhancedLocations` con ADM1 = `MX31` (Yucatán) **y** que sea Mérida (nombre con "Merida" o coordenadas en lat 20.85–21.10, lon −89.75 a −89.50). Los `.zip` no se guardan.
- **Columnas de `raw/gdelt_stream/gkg_merida_YYYY-MM-DD.csv`:** `fecha_hora_utc`, `dominio`, `url`, `tono` (primer valor de `V1.5Tone`/"V2Tone"), `positivo`, `negativo`, `temas` (solo nombres de `V2Themes`), `idioma_origen` (`eng` o el código de origen de la traducción, p. ej. `spa`), `titulo` (de `<PAGE_TITLE>`), `ubicacion_merida`, `gkg_record_id`, `archivo_gkg`.
- **Tolerancia a cortes:** `_procesados.txt` registra cada archivo leído; al reanudar recupera hasta 24 h de cuartos de hora faltantes. Si GDELT anuncia un archivo que aún no existe (pasa seguido con el flujo traducido), lo reintenta en la siguiente pasada y solo lo da por perdido después de 3 h.
- **Estado (25 nov 2026):** arrancó el 24 nov a las 22:21 (hora local) con 24 h de recuperación y sigue vivo. Lleva ~200 archivos GKG leídos (mitad inglés, mitad traducido) y **0 documentos de Mérida**. No es un error del filtro: en archivos de muestra del flujo traducido hay ~100 menciones de México por archivo, pero **ninguna con `MX31` ni de diarios yucatecos**; el GKG público trae hoy ~1,500–3,000 documentos por cuarto de hora. Conviene dejarlo corriendo (cuesta poco) y revisar en unas semanas; mientras, **la DOC API es la fuente efectiva**.

#### 1b. Respaldo histórico: GDELT DOC 2.0 API ✅
- **Fuente:** `https://api.gdeltproject.org/api/v2/doc/doc`, consulta `("Mérida" OR "Merida") (Yucatán OR Yucatan)`, del **2026-08-31 al 2026-11-24** (la API solo cubre ~3 meses).
  - `mode=timelinetone` y `mode=timelinevolraw` (serie diaria) para todas las fuentes y por voz: local = `domainis:` de los tres diarios principales (con más dominios el servidor corta la conexión), nacional = `sourcecountry:mexico` sin esos tres, internacional = `-sourcecountry:mexico`.
  - `mode=artlist`, `maxrecords=250`, en 13 ventanas semanales (lunes a lunes; si una semana llegara a 250 se partiría en días; ninguna llegó).
- **Ritmo:** la API pide 1 petición cada 5 s, pero en la práctica respondía 429 por debajo de ~15 s; el script espera 15 s y reintenta con espera creciente. Todas las respuestas quedan en `raw/gdelt_doc/` (394 KB, sí van en git).
- **Huecos del propio GDELT** (la serie diaria no tiene datos): 14–19 sep, 3–14 oct y 28 oct – 2 nov 2026; además el volumen de noviembre es muy bajo (0–17 notas al día). Las semanas 5–12 oct y 26 oct – 2 nov devolvieron 0 artículos por eso.
- Las ventanas que fallan (16–23 nov falló dos veces) no se guardan en caché: la siguiente corrida de `clean_gdelt.py` las vuelve a pedir. Las 13 ventanas ya están completas.

#### Clasificación (`scripts/clasificacion.py`)
- **`voz`:** `local` si el dominio está en la lista de medios de Yucatán (los seis de la especificación: yucatan.com.mx, poresto.com, lajornadamaya.mx, laverdadnoticias.com, novedadesyucatan.com, sipse.com; más los encontrados o conocidos: yucatan.quadratin.com.mx, diariodelsureste.com.mx, yucatanahora.mx, lectormx.com, reporteroshoy.mx, infolliteras.com, notirasa.com, desdeelbalcon.com, yucatanmagazine.com, theyucatantimes.com y otros); `nacional` si el dominio es `.mx`, está en la lista de medios nacionales o la DOC API dice `sourcecountry = Mexico`; si no, `internacional`.
- **`temas`:** vivienda/rentas, bienes raíces, turismo, seguridad, migración/expats, servicios/agua u otros, a partir de temas GKG específicos (solo en el stream) y palabras del título.
- **Ojo:** en GDELT solo aparecen como "local" el Diario de Yucatán (255), Quadratín Yucatán (36) y La Verdad (5); **Por Esto! y La Jornada Maya no están indexados por la DOC API** (por eso la sección 6 los raspa directo). Como la DOC API solo da título, el **81–85%** de los artículos de cada voz queda en "otros": la cobertura de Mérida es mayormente clima, política y sucesos.

#### Validación
- Artículos deduplicados por URL normalizada (sin `http(s)://`, `www.` ni `/` final): 656 → **655**.
- `n_articulos` semanal por voz (tabla de artículos) se compara con el volumen de la serie diaria (`n_articulos_doc_api`); difieren poco y en las semanas con huecos de GDELT.
- Tono: con 0 filas del stream, el tono semanal sale de `timelinetone` ponderado por `timelinevolraw` (`fuente_tono = doc_api_timelinetone`). Cuando el stream tenga ≥ 3 artículos con tono en una semana y voz, se usará ese promedio (`stream_gkg`). Promedio de semanas: local −0.33, nacional −0.53, internacional −0.01.

#### Archivos limpios (`clean/`)
- `gdelt_merida_articulos.csv`: **655** artículos únicos (local 296, nacional 279, internacional 80; español 604, alemán 26, inglés 22), con `fecha`, `fecha_hora_utc`, `semana_iso`, `voz`, `dominio`, `pais_fuente`, `idioma`, `titulo`, `url`, `temas`, `tono`, `positivo`, `negativo` (vacíos si no vienen del stream) y `fuente_datos`.
- `gdelt_merida_tono_semanal_por_voz.csv`: **31** filas (`semana_iso`, `voz`, `n_articulos`, `tono_promedio`, `fuente_tono`, más columnas de control).
- `gdelt_merida_temas_por_voz.csv`: **19** filas (`voz`, `tema`, `n`, `n_articulos_voz`, `porcentaje`; un artículo puede tener varios temas).
- `gdelt_merida_timeline_diaria_por_voz.csv`: **252** filas (serie diaria de la DOC API: `fecha`, `voz` incluida `todas`, `n_articulos`, `tono_promedio`).

### 2. Complemento A — Auditoría de paisaje lingüístico (letreros) ❌ pendiente de campo
- **Qué falta:** levantar las fotos. El script ya lee el EXIF (fecha y GPS con Pillow), ubica cada foto en su colonia del GeoPortal (punto en polígono contra `geoportal_colonias_merida.geojson`, columna `unidad_habitacional`) y la agrega a `raw/campo/letreros_plantilla.csv` sin borrar lo que ya se llenó.
- **Cómo levantarlo con el celular:**
  1. Activa la ubicación de la cámara (iPhone: *Ajustes → Privacidad → Localización → Cámara → Al usar la app*; Android: *Cámara → Ajustes → Etiquetas de ubicación*). En iPhone usa *Formato: Más compatible* (JPG) o convierte los HEIC a JPG antes de copiarlos.
  2. Recorre las mismas calles en el Centro y en una colonia de control. Una foto por letrero, de frente.
  3. **No compartas las fotos por WhatsApp** (borra el EXIF): cópialas por cable o Drive a `raw/campo/fotos_letreros/`.
  4. Corre `python 7-Self-Produced/scripts/clean_field_audit.py`; llena en la plantilla `idioma_letrero` (`es`, `en`, `bilingue`, `maya`, `otro`) y `tipo` (`comercio`, `se_vende`, `se_renta`, `otro`); vuelve a correr el script.
- **Salidas que generará:** `clean/campo_letreros.csv` (con `en_centro_historico`) y `clean/campo_letreros_resumen_colonia.csv` (n de letreros, % en inglés o bilingüe, n "se vende" y "se renta" por `unidad_habitacional`).
- **Probado** con una foto sintética con GPS (20.9678, −89.6236): la asignó a `COL. CENTRO` y `en_centro_historico = True`; la prueba se borró.

### 3. Complemento B — "Índice del americano" ❌ pendiente de campo
- **Qué falta:** visitar cafeterías del Centro y de colonias populares y anotar el precio del café americano del menú.
- **Cómo levantarlo:** una fila por negocio en `raw/campo/americano_plantilla.csv` (`fecha` en `AAAA-MM-DD`, `negocio`, `colonia` si se sabe, `latitud`/`longitud` desde Google Maps → mantener presionado el punto, `precio_americano_mxn`, `tamano_ml` del vaso o taza, `foto_menu` con el nombre del archivo en `raw/campo/fotos_menus/`).
- **Limpieza:** convierte precios y tamaños a número, completa la colonia por punto en polígono, marca `en_centro_historico` y calcula `precio_por_355ml_mxn` (12 oz) para comparar tamaños distintos.
- **Salidas que generará:** `clean/campo_americano.csv` y `clean/campo_americano_resumen_colonia.csv` (mediana de precio por colonia y por Centro/no Centro).

---

## Pendientes
- Mantener vivo el grabador y revisar si GDELT vuelve a traer documentos de Mérida al GKG público.
- Trabajo de campo de los complementos A y B.

---

## Cómo mantener vivo el grabador de GDELT (Windows, PowerShell)

Desde la raíz del repo. El grabador sólo permite **una instancia** (candado en `raw/gdelt_stream/_recorder.lock`), así que es seguro combinar las opciones.

**Opción A — en segundo plano mientras la sesión de Windows esté abierta:**

```powershell
Start-Process -FilePath ".venv\Scripts\pythonw.exe" -ArgumentList "7-Self-Produced\scripts\gdelt_stream_recorder.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden
```

**Opción B — tarea programada cada 15 minutos (sobrevive reinicios; cada corrida recupera hasta 24 h de huecos):**

```powershell
$repo = (Get-Location).Path; schtasks /Create /SC MINUTE /MO 15 /TN "MeridaForSale-GDELT" /TR "`"$repo\.venv\Scripts\pythonw.exe`" `"$repo\7-Self-Produced\scripts\gdelt_stream_recorder.py`" --once" /F
```

**Ver si está vivo y qué ha grabado:**

```powershell
Get-Content 7-Self-Produced\raw\gdelt_stream\_recorder.log -Tail 20
```

**Detener:**

```powershell
Stop-Process -Id (Get-Content 7-Self-Produced\raw\gdelt_stream\_recorder.pid) -Force
```

```powershell
schtasks /Delete /TN "MeridaForSale-GDELT" /F
```

(El segundo comando sólo si se usó la opción B.)

---

## Cómo regenerar los archivos limpios

```bash
python 7-Self-Produced/scripts/clean_gdelt.py          # usa la caché de raw/gdelt_doc/ y todo lo grabado en raw/gdelt_stream/
python 7-Self-Produced/scripts/clean_field_audit.py    # trabajo de campo (hoy sólo avisa que está pendiente)
```

`clean_gdelt.py --refrescar` vuelve a pedir todo a la DOC API, pero **la API sólo cubre los últimos ~3 meses**: si se refresca después, se pierden las semanas viejas. Por eso la caché de `raw/gdelt_doc/` sí va en git.
