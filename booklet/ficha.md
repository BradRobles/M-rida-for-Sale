# Ficha editorial · Capítulo: Mérida en venta

**Equipo 9 · UPY Data 9B** — Julio César De Aquino Castellanos, Brad Robles García y Eliana Lorely Osorio Martínez

---

## Título-hallazgo

**Mérida en venta: el turismo creció 30% y el impuesto al hospedaje se triplicó, mientras el Centro Histórico perdió 1,189 negocios**

---

## Tres cifras con fuente

1. **+30.2 % en turistas de hotel (2019 → 2025):** Mérida pasó de **1,737,810** a **2,261,866** llegadas anuales de turistas hospedados en hoteles (19.6 % extranjeros).  
   *Fuente:* SECTUR / DataTur, reporte mensual de ocupación en hoteles y moteles por centro turístico (corte 2015–septiembre 2026).

2. **−12.9 % en negocios dentro del Centro Histórico (2019 → 2025):** el polígono de la Zona de Monumentos Históricos bajó de **9,199** a **8,010** establecimientos (−1,189), mientras el conjunto del municipio de Mérida creció **+5.3 %** (**53,183 → 56,014**; universo municipal completo `cve_mun = 050`, todas las localidades, ediciones DENUE noviembre 2019 y mayo 2025) y las cafeterías aumentaron **+46.3 %** (641 → 938).  
   *Fuente:* INEGI DENUE (noviembre 2019 y mayo 2025) cruzado con el polígono oficial del Centro Histórico del GeoPortal de Mérida.

3. **×3.2 en recaudación del Impuesto sobre Hospedaje (2019 → 2025, pesos nominales):** la recaudación estatal subió de **$61.4 millones** a **$196.9 millones de pesos nominales** (índice 2019 = 100 → **320.5**), mientras los establecimientos de hospedaje registrados en el DENUE apenas pasaron de **304 a 311**. Al mismo tiempo, la mediana del precio de vivienda en Yucatán se ubicó **+39 % por encima de la mediana nacional** (4.º lugar de 32 estados, 3T 2025).  
   *Fuentes:* Agencia de Administración Fiscal de Yucatán (AAFY, solicitud de transparencia folio `1191207426000093`) y Sociedad Hipotecaria Federal (Índice SHF de Precios de la Vivienda, 3T 2025).

---

## Escenas propuestas para el impreso

1. **Turistas de hotel en Mérida por año (2015–2026\*):** barras apiladas en D3 (`d3@7.9.0`) diferenciando turistas nacionales y extranjeros, con la caída de 2020 y el récord de 2025 (+30.2 % frente a 2019).
2. **Negocios del Centro Histórico contra el municipio (2019 → 2025):** barras divergentes en D3 comparando la contracción comercial del casco histórico (−12.9 %) frente a la expansión del resto de Mérida (+5.3 % total; +46.3 % en cafeterías).
3. **Cafeterías que abrieron o cerraron por AGEB (2019 → 2025):** mapa coroplético interactivo/imprimible en D3 sobre las 541 AGEB urbanas con el contorno del Centro Histórico (212 AGEB ganaron cafeterías).
4. **Impuesto al hospedaje contra turistas de hotel (índice 2019 = 100, pesos nominales):** líneas en D3 evidenciando la brecha entre la recaudación (320.5) y las llegadas hoteleras (130.2), acompañada de la **imagen 3D de las 831 manzanas del Centro** (modelo de elevación INEGI 2015) con **código QR** hacia el visor de Realidad Aumentada (`https://bradrobles.github.io/Merida-for-Sale/booklet/ar/`).

---

## Lo que los datos no dicen

- **Inflación y desglose de plataformas digitales:** la recaudación de la AAFY se reporta en **pesos nominales** (sin deflactar con INPC). Además, la dependencia confirmó que el impuesto retenido por plataformas digitales (como Airbnb) está incluido en los totales, pero no entregó fecha de inicio ni desglose separado, por lo que no se puede aislar exactamente qué porcentaje del salto posterior a 2021 corresponde a renta de corto plazo frente a inflación y tarifas.
- **Alojamiento informal y desplazamientos:** el DENUE registra establecimientos económicos, no viviendas rentadas por noche en plataformas; tampoco mide directamente a cuántas familias residentes desplazó el alza de rentas ni los precios de renta informal.
- **Muestra de prensa y alcance geográfico:** las 1,495 notas recopiladas son una muestra dirigida sobre la Zona Metropolitana de Mérida (6 municipios), mientras que DENUE, AGEB y licencias cubren solo el municipio de Mérida.
- **Modelo de elevación y cortes parciales:** el modelo 3D de alturas del Centro es fotogramétrico satelital de 2015 (no LiDAR aerotransportado reciente) y las cifras de 2026 son parciales (DataTur y AAFY hasta septiembre; ASUR hasta octubre; prensa hasta noviembre).

---

## Frase puente al capítulo del Equipo 8 (Tren Maya)

> Si el flujo aéreo y hotelero ya tensó el precio de la vivienda y vació el comercio cotidiano del Centro Histórico antes de que la infraestructura ferroviaria operara a plena escala, la pregunta siguiente es qué ocurre cuando esa presión turística se conecta a toda la península: el **Tren Maya** abre el siguiente capítulo.
