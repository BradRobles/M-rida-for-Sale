# Mérida for Sale: Data Sources Checklist

**Topic:** touristification and gentrification in Mérida
**Checked on:** 29 Sep 2026

## Legend

- ✅ **Verified:** exists and is free
- ⚠️ **Exists, check one thing:** see the note
- 🕒 **Slow:** takes weeks, start now

## The story (5 chapters)

1. **The arrival:** more tourists and more foreign residents
2. **The shops change:** from corner stores to specialty cafés
3. **The houses change:** prices up, homes empty or rented to visitors
4. **Who tells the story:** local press vs. international media
5. **Where this ends:** Oaxaca, San Miguel de Allende, Playa del Carmen

---

## 🔥 Do these first (this week)

- [ ] File the 2 transparency requests (source 5). Answers take about 20 working days.
- [ ] Start the GDELT script (source 7). Every day it runs is more data.
- [ ] Open the GeoPortal and check if layers can be **downloaded** (source 4).
- [ ] Check INEGI LiDAR coverage and flight date for Mérida (source 8).

---

## 1. INEGI DENUE

**Main: DENUE editions over time** ✅
- What: businesses in Mérida by type and location. Compare lodging (SCIAN 721), restaurants and bars (722) vs. corner stores (461110).
- Map viewer: https://www.inegi.org.mx/app/mapa/denue/
- Bulk download (filter by period/year): https://www.inegi.org.mx/app/descarga/
- API: https://www.inegi.org.mx/servicios/api_denue.html

**Complement A: Census 2010 and 2020 by AGEB** ✅
- What: population change, empty homes, homes for temporary use in the Centro.
- 2020: https://www.inegi.org.mx/programas/ccpv/2020/
- 2010: https://www.inegi.org.mx/programas/ccpv/2010/

**Complement B: same DENUE extraction for other cities** ✅
- What: Oaxaca, San Miguel de Allende, Playa del Carmen. Divide by population to compare.
- Same links as Main.

---

## 2. datos.gob.mx

**Main: DataTur hotel activity** ✅
- What: monthly tourist arrivals (national vs. foreign), occupancy, by tourist center. Mérida is included.
- DataTur: https://www.datatur.sectur.gob.mx/
- Portal: https://datos.gob.mx/

**Complement A: ASUR monthly airport traffic** ✅
- What: passengers per month at Mérida (MID), domestic vs. international. Also Cancún and Oaxaca for comparison.
- ASUR: https://www.asur.com.mx/
- Example of a monthly release: https://www.barchart.com/story/news/36914859/asur-announces-total-passenger-traffic-for-december-2025

**Complement B: DataTur for the comparison cities** ✅
- What: same indicators for Oaxaca, San Miguel de Allende, Playa del Carmen.
- Same link as Main.

---

## 3. SIEGY (Yucatán)

**Main: state tourism indicators** ⚠️
- What: visitors, hotel rooms, tourism spending in Yucatán.
- ⚠️ SIEGY exists as the state statistics system, but I could not confirm a download portal. **Backup that is verified:** Sefotur monthly tourism reports (PDF, built on DataTur).
- Sefotur: https://sefotur.yucatan.gob.mx/
- Example report (May 2026): https://sefotur.yucatan.gob.mx/files-content/general/informe_mensual_actividad_turistica/9eee9c3e4221d877d31abfb647b03c2f.pdf

**Complement A: SHF Housing Price Index** ✅
- What: quarterly housing prices by state, metro area and selected municipalities. Yucatán roughly doubled between 2017 and 2025.
- SHF: https://www.gob.mx/shf (search "Índice SHF de Precios de la Vivienda")
- Readable summary example: https://iieg.gob.mx/ns/wp-content/uploads/2026/08/reporte_indice_precios_vivienda_mexico_2doT_2026.pdf

**Complement B: ENOE (INEGI employment survey)** ✅
- What: local income. Question: do wages keep up with house prices? Mérida is a self-represented city in ENOE.
- ENOE: https://www.inegi.org.mx/programas/enoe/15ymas/

---

## 4. GeoPortal de Mérida

**Main: Centro Histórico boundary, heritage zones, neighborhoods** ⚠️
- ⚠️ Free to view. Check that the layers can be downloaded, not only viewed.
- GeoPortal: https://geoportal.merida.gob.mx/

**Complement A: OpenStreetMap** ✅
- What: hotels, hostels, cafés, coworkings today. Also the backup if GeoPortal does not allow downloads.
- Query tool: https://overpass-turbo.eu/
- Docs: https://wiki.openstreetmap.org/wiki/Overpass_API

**Complement B: INEGI Geostatistical Framework** ✅
- What: AGEB boundaries. This is the key that joins every source.
- https://www.inegi.org.mx/temas/mg/

---

## 5. Government data request 🕒

**Main: Ayuntamiento de Mérida** 🕒
- Ask for: construction, remodeling and business licenses in the Centro, per year 2015 to 2025, grouped by neighborhood.
- Platform: https://www.plataformadetransparencia.org.mx/

**Complement A: AAFY (Yucatán tax agency)** 🕒
- Ask for: monthly lodging tax revenue, split by digital platforms if available. Airbnb collects this tax in Yucatán and pays it to the state, so the data exists.
- Same platform as Main.

**Complement B: Migration Policy Unit bulletins** ✅ (public, no request needed)
- What: residence cards issued by state. Compare Yucatán vs. Quintana Roo and Oaxaca.
- http://portales.segob.gob.mx/es/PoliticaMigratoria/Boletines_Estadisticos
- If the link moved, search "Boletín Mensual de Estadísticas Migratorias".

---

## 6. Web scraping

**Main: local press** ✅
- What: articles on rent, evictions and gentrification since 2018. Extract topics and neighborhoods.
- ⚠️ Check each site's robots.txt first and add pauses between requests.
- https://www.yucatan.com.mx/
- https://www.poresto.com/
- https://www.lajornadamaya.mx/
- ❌ Avoid: real estate portals and Airbnb. Their terms forbid scraping.

**Complement A: YouTube Data API** ✅
- What: titles and comments of "moving to Mérida" videos. Shows how the city is sold abroad.
- Free daily quota, needs a Google API key.
- Docs: https://developers.google.com/youtube/v3

**Complement B: Wikipedia pageviews** ✅
- What: daily views of the Mérida article in English and Spanish. Measures international interest.
- No key needed.
- Docs: https://wikitech.wikimedia.org/wiki/Analytics/AQS/Pageviews
- Quick viewer: https://pageviews.wmcloud.org/

---

## 7. Self-produced (no surveys)

**Main: your own GDELT stream recording** ✅ (tested live on 29 Sep 2026)
- What: national and international news about Mérida, every 15 minutes, with tone and themes.
- No account, no key, no limit.
- Latest files: http://data.gdeltproject.org/gdeltv2/lastupdate.txt
- Spanish news goes here: http://data.gdeltproject.org/gdeltv2/lastupdate-translation.txt
- Codebook: http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf
- Tip: filter by location code `MX31` (Yucatán), not by text.

**Complement A: linguistic landscape field audit** ✅
- What: walk set streets in the Centro and one control neighborhood. Take geotagged phone photos. Count signs in English and "For sale" signs.
- Tools: phone camera with location on. Coordinates come from photo metadata (EXIF).

**Complement B: "Americano index"** ✅
- What: price of a black coffee in cafés of the Centro vs. working class neighborhoods, taken from menus in person.
- Tools: phone photos of menus, one spreadsheet.

---

## 8. LiDAR

**Main: INEGI high resolution LiDAR elevation models** ⚠️
- What: surface model minus terrain model gives building heights. Use it to model the low colonial skyline of the Centro in 3D.
- ⚠️ Coverage is partial: confirm Mérida is covered. Check the flight date in the metadata; it may predate the recent tower boom, so treat it as a snapshot, not a change over time.
- Technical sheet: https://inegi.org.mx/contenidos/temas/relieve/continental/doc/lidar_alta_resolucion.pdf
- Backup: national continuous LiDAR surface model at 15 m: https://inegi.org.mx/contenidos/temas/relieve/continental/doc/lidar_superficie.pdf

---

## 9. Augmented reality

**Main: 3D block of the Centro, opened from a QR code** ✅
- What: the LiDAR block with DENUE businesses colored by "existed in 2015" vs. "opened after". The reader walks the change.
- Tool: model-viewer (free, open source, runs in the phone browser, no app).
- https://modelviewer.dev/
