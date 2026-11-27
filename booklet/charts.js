/* Mérida en venta · Gráficas interactivas en D3.js v7 (100% español) */

const COLORS = {
  bg: "#F4EFE6",
  surface: "#FFFFFF",
  text: "#1E1B18",
  soft: "#3B3631",
  muted: "#5C554D",
  grid: "#E6DFD4",
  merida: "#1F5F5B",
  meridaSoft: "#9FC0BC",
  foreign: "#C8892B",
  foreignSoft: "#E8C27A",
  growth: "#8A5A17",
  oaxaca: "#D96B43",
  cancun: "#2E6F9E",
};

const CAT_ES = {
  "All businesses": "Todos los negocios",
  "Corner stores": "Tiendas de abarrotes",
  "Coffee shops": "Cafeterías",
  "Lodging": "Hospedaje",
  "Restaurants and bars": "Restaurantes y bares",
};

const fmtInt = (n) => Math.round(n).toLocaleString("es-MX");
const fmtM = (n) => `${(n / 1e6).toFixed(2)} M`;
const fmtPct = (v, d = 1) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toFixed(d)}%`;

const tip = d3.select("#d3-tip");
function showTip(evt, html) {
  tip.html(html).style("opacity", 1);
  const pad = 14;
  const x = Math.min(window.innerWidth - 270, evt.clientX + pad);
  const y = Math.max(10, evt.clientY - 28);
  tip.style("left", `${x}px`).style("top", `${y}px`);
}
function hideTip() {
  tip.style("opacity", 0);
}

/* -------------------------------------------------------------------------
 * ESCENA 1 · Turistas de hotel por año (barras apiladas D3)
 * ------------------------------------------------------------------------- */
function renderTouristsChart(data) {
  const box = d3.select("#chart-tourists");
  box.selectAll("*").remove();

  const W = 680, H = 350;
  const m = { top: 28, right: 20, bottom: 38, left: 48 };
  const iw = W - m.left - m.right;
  const ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const rows = data.map((d) => ({
    year: +d.year,
    label: d.partial === "True" ? `${d.year}*` : `${d.year}`,
    national: +d.national,
    foreign: +d.foreign,
    total: +d.total,
    pctForeign: +d.pct_foreign,
    partial: d.partial === "True",
  }));

  const x = d3.scaleBand().domain(rows.map((d) => d.label)).range([0, iw]).padding(0.24);
  const y = d3.scaleLinear().domain([0, 2.5e6]).range([ih, 0]);

  // Cuadrícula horizontal
  g.append("g")
    .selectAll("line")
    .data(y.ticks(5))
    .join("line")
    .attr("x1", 0).attr("x2", iw)
    .attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", COLORS.grid).attr("stroke-width", 1);

  // Línea de referencia 2019 (1.74M)
  const r2019 = rows.find((d) => d.year === 2019);
  if (r2019) {
    g.append("line")
      .attr("x1", 0).attr("x2", iw)
      .attr("y1", y(r2019.total)).attr("y2", y(r2019.total))
      .attr("stroke", COLORS.muted).attr("stroke-dasharray", "4,4").attr("stroke-width", 1.2);
    g.append("text")
      .attr("x", 4).attr("y", y(r2019.total) - 6)
      .attr("fill", COLORS.muted).attr("font-size", 11).attr("font-weight", 600)
      .text("Nivel 2019 (1.74 M)");
  }

  // Segmento nacional (abajo)
  g.selectAll(".bar-nac")
    .data(rows)
    .join("rect")
    .attr("x", (d) => x(d.label))
    .attr("y", (d) => y(d.national))
    .attr("width", x.bandwidth())
    .attr("height", (d) => ih - y(d.national))
    .attr("rx", 2)
    .attr("fill", (d) => (d.partial ? COLORS.meridaSoft : COLORS.merida))
    .on("mousemove", (evt, d) =>
      showTip(evt, `<b>${d.label}</b>${d.partial ? " (ene–sep)" : ""}<br>Total: <b>${fmtM(d.total)}</b><br>Nacionales: ${fmtInt(d.national)}<br>Extranjeros: ${fmtInt(d.foreign)} (${d.pctForeign.toFixed(1)}%)`)
    )
    .on("mouseleave", hideTip);

  // Segmento extranjero (arriba)
  g.selectAll(".bar-ext")
    .data(rows)
    .join("rect")
    .attr("x", (d) => x(d.label))
    .attr("y", (d) => y(d.total))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(d.national) - y(d.total))
    .attr("rx", 2)
    .attr("fill", (d) => (d.partial ? COLORS.foreignSoft : COLORS.foreign))
    .on("mousemove", (evt, d) =>
      showTip(evt, `<b>${d.label}</b>${d.partial ? " (ene–sep)" : ""}<br>Total: <b>${fmtM(d.total)}</b><br>Nacionales: ${fmtInt(d.national)}<br>Extranjeros: ${fmtInt(d.foreign)} (${d.pctForeign.toFixed(1)}%)`)
    )
    .on("mouseleave", hideTip);

  // Etiquetas sobre años clave (2019, 2020, 2025)
  rows.filter((d) => [2019, 2020, 2025].includes(d.year)).forEach((d) => {
    g.append("text")
      .attr("x", x(d.label) + x.bandwidth() / 2)
      .attr("y", y(d.total) - 7)
      .attr("text-anchor", "middle")
      .attr("fill", d.year === 2025 ? COLORS.growth : COLORS.text)
      .attr("font-family", "'Space Grotesk', sans-serif")
      .attr("font-size", 11.5).attr("font-weight", 700)
      .text(`${(d.total / 1e6).toFixed(2)}M`);
  });

  // Ejes
  g.append("g")
    .attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", COLORS.grid))
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);

  g.append("g")
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8).tickFormat((d) => (d === 0 ? "0" : `${(d / 1e6).toFixed(1)}M`)))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);
}

/* -------------------------------------------------------------------------
 * ESCENA 2 · Negocios del Centro contra el municipio (barras divergentes D3)
 * ------------------------------------------------------------------------- */
function renderShopsChart(allRows, mode = "comparar") {
  const box = d3.select("#chart-shops");
  box.selectAll("*").remove();

  const W = 680, H = mode === "comparar" ? 330 : 280;
  const m = { top: 20, right: 64, bottom: 34, left: 162 };
  const iw = W - m.left - m.right;
  const ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const order = ["Coffee shops", "Lodging", "Corner stores", "Restaurants and bars", "All businesses"];
  const parsed = allRows.map((d) => ({
    area: d.area,
    areaEs: d.area === "Centro" ? "Centro Histórico" : "Todo el municipio",
    cat: d.category,
    catEs: CAT_ES[d.category] || d.category,
    n19: +d.n_2019,
    n25: +d.n_2025,
    change: +d.change,
    pct: +d.pct_change,
  }));

  const filtered = mode === "comparar"
    ? parsed
    : parsed.filter((d) => (mode === "centro" ? d.area === "Centro" : d.area === "Municipality"));

  const minV = Math.min(-18, d3.min(filtered, (d) => d.pct) - 3);
  const maxV = Math.max(12, d3.max(filtered, (d) => d.pct) + 6);

  const x = d3.scaleLinear().domain([minV, maxV]).range([0, iw]);
  const y0 = d3.scaleBand().domain(order.map((c) => CAT_ES[c])).range([0, ih]).padding(0.24);
  const ySub = d3.scaleBand().domain(["Centro", "Municipality"]).range([0, y0.bandwidth()]).padding(0.14);

  // Cuadrícula vertical
  g.append("g")
    .selectAll("line")
    .data(x.ticks(6))
    .join("line")
    .attr("x1", (d) => x(d)).attr("x2", (d) => x(d))
    .attr("y1", 0).attr("y2", ih)
    .attr("stroke", (d) => (d === 0 ? COLORS.text : COLORS.grid))
    .attr("stroke-width", (d) => (d === 0 ? 1.4 : 1));

  const barY = (d) => (mode === "comparar" ? y0(d.catEs) + ySub(d.area) : y0(d.catEs));
  const barH = mode === "comparar" ? ySub.bandwidth() : y0.bandwidth();
  const barColor = (d) => {
    if (mode === "comparar") return d.area === "Centro" ? COLORS.merida : COLORS.foreign;
    return d.pct >= 0 ? COLORS.foreign : COLORS.merida;
  };

  g.selectAll("rect.bar")
    .data(filtered)
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => (d.pct >= 0 ? x(0) : x(d.pct)))
    .attr("y", barY)
    .attr("width", (d) => Math.max(2, Math.abs(x(d.pct) - x(0))))
    .attr("height", barH)
    .attr("rx", 3)
    .attr("fill", barColor)
    .on("mousemove", (evt, d) =>
      showTip(evt, `<b>${d.catEs}</b> · ${d.areaEs}<br>2019: ${fmtInt(d.n19)} → 2025: ${fmtInt(d.n25)}<br>Cambio: <b>${d.change > 0 ? "+" : ""}${fmtInt(d.change)} (${fmtPct(d.pct)})</b>`)
    )
    .on("mouseleave", hideTip);

  // Etiquetas de porcentaje
  g.selectAll("text.val")
    .data(filtered)
    .join("text")
    .attr("x", (d) => (d.pct >= 0 ? x(d.pct) + 6 : x(d.pct) - 6))
    .attr("y", (d) => barY(d) + barH / 2 + 4)
    .attr("text-anchor", (d) => (d.pct >= 0 ? "start" : "end"))
    .attr("fill", COLORS.text)
    .attr("font-family", "'Space Grotesk', sans-serif")
    .attr("font-size", 11.5).attr("font-weight", 700)
    .text((d) => fmtPct(d.pct));

  // Ejes
  g.append("g")
    .call(d3.axisLeft(y0).tickSize(0).tickPadding(10))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", COLORS.text).attr("font-size", 12.5).attr("font-weight", 600);

  g.append("g")
    .attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).ticks(6).tickSize(0).tickPadding(8).tickFormat((d) => `${d > 0 ? "+" : ""}${d}%`))
    .call((s) => s.select(".domain").attr("stroke", COLORS.grid))
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);
}

/* -------------------------------------------------------------------------
 * ESCENA 3 · Cafeterías que abrieron o cerraron por AGEB (Mapa D3.js)
 * ------------------------------------------------------------------------- */
function renderAgebCafesMap(agebGeo, centroGeo) {
  const box = d3.select("#chart-ageb-map");
  box.selectAll("*").remove();

  const W = 680, H = 500;
  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);

  // Proyección plana con relación de aspecto métrica exacta para Mérida (20.97° N)
  // Inmune al sentido horario/antihorario de anillos GeoJSON
  const cosLat = Math.cos((20.97 * Math.PI) / 180);
  const projectPoint = ([lon, lat]) => [lon * cosLat, -lat];
  const allPts = [];
  agebGeo.features.forEach((f) => {
    const pushCoords = (c) => {
      if (typeof c[0] === "number") allPts.push(projectPoint(c));
      else c.forEach(pushCoords);
    };
    pushCoords(f.geometry.coordinates);
  });

  const minX = d3.min(allPts, (p) => p[0]), maxX = d3.max(allPts, (p) => p[0]);
  const minY = d3.min(allPts, (p) => p[1]), maxY = d3.max(allPts, (p) => p[1]);
  const pad = 20;
  const scale = Math.min((W - 2 * pad) / (maxX - minX), (H - 2 * pad) / (maxY - minY));
  const tx = (W - (maxX - minX) * scale) / 2 - minX * scale;
  const ty = (H - (maxY - minY) * scale) / 2 - minY * scale;

  const transform = d3.geoTransform({
    point(lon, lat) {
      this.stream.point(lon * cosLat * scale + tx, -lat * scale + ty);
    },
  });
  const path = d3.geoPath().projection(transform);

  // Escala divergente centrada en 0 (verde pérdida -> crema -> ámbar ganancia)
  const color = d3.scaleLinear()
    .domain([-4, -1.5, 0, 2, 6])
    .range(["#1F5F5B", "#7FA9A4", "#EFE9DE", "#DDB067", "#8A5A17"])
    .clamp(true);

  svg.append("rect").attr("width", W).attr("height", H).attr("fill", "#FAF7F2").attr("rx", 8);

  svg.append("g")
    .selectAll("path")
    .data(agebGeo.features)
    .join("path")
    .attr("d", path)
    .attr("fill", (d) => color(+d.properties.cafes_change || 0))
    .attr("stroke", "#FFFFFF")
    .attr("stroke-width", 0.55)
    .on("mousemove", (evt, d) => {
      const p = d.properties;
      const ch = +p.cafes_change;
      showTip(evt, `<b>AGEB ${p.cvegeo.slice(-4)}</b> (${p.cvegeo})<br>Cafeterías 2019: ${p.cafes_2019}<br>Cafeterías 2025: ${p.cafes_2025}<br>Cambio neto: <b>${ch > 0 ? "+" : ""}${ch}</b>`);
    })
    .on("mouseleave", hideTip);

  // Contorno del Centro Histórico encima
  svg.append("g")
    .selectAll("path")
    .data(centroGeo.features)
    .join("path")
    .attr("d", path)
    .attr("fill", "none")
    .attr("stroke", COLORS.text)
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", "5,3")
    .style("pointer-events", "none");

  // Etiqueta del Centro Histórico
  const chCentroid = path.centroid(centroGeo.features[0]);
  svg.append("text")
    .attr("x", chCentroid[0]).attr("y", chCentroid[1] + 54)
    .attr("text-anchor", "middle")
    .attr("fill", COLORS.text)
    .attr("font-family", "'Space Grotesk', sans-serif")
    .attr("font-size", 11.5).attr("font-weight", 700)
    .attr("paint-order", "stroke").attr("stroke", "#FFFFFF").attr("stroke-width", 3.5)
    .text("Centro Histórico");
}

/* -------------------------------------------------------------------------
 * ESCENA 4 · Impuesto de hospedaje vs. turistas (índice 2019 = 100, NOMINAL)
 * ------------------------------------------------------------------------- */
function renderTaxVsTouristsChart(data) {
  const box = d3.select("#chart-tax");
  box.selectAll("*").remove();

  const W = 680, H = 340;
  const m = { top: 26, right: 64, bottom: 38, left: 46 };
  const iw = W - m.left - m.right;
  const ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const rows = data.map((d) => ({
    year: +d.year,
    taxMxn: +d.tax_nominal_mxn,
    tourists: +d.tourists,
    taxIdx: +d.tax_index,
    tourIdx: +d.tourists_index,
  }));

  const x = d3.scaleLinear().domain(d3.extent(rows, (d) => d.year)).range([0, iw]);
  const y = d3.scaleLinear().domain([0, 350]).range([ih, 0]);

  g.append("g")
    .selectAll("line")
    .data([0, 50, 100, 150, 200, 250, 300, 350])
    .join("line")
    .attr("x1", 0).attr("x2", iw)
    .attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", (d) => (d === 100 ? COLORS.muted : COLORS.grid))
    .attr("stroke-dasharray", (d) => (d === 100 ? "4,4" : null))
    .attr("stroke-width", (d) => (d === 100 ? 1.3 : 1));

  // Área sombreada entre las dos curvas desde 2020 (la brecha del «hotel invisible»)
  const post = rows.filter((d) => d.year >= 2019);
  const gapArea = d3.area()
    .x((d) => x(d.year))
    .y0((d) => y(d.tourIdx))
    .y1((d) => y(d.taxIdx));
  g.append("path").datum(post).attr("d", gapArea).attr("fill", COLORS.foreign).attr("opacity", 0.12);

  const lineTax = d3.line().x((d) => x(d.year)).y((d) => y(d.taxIdx));
  const lineTour = d3.line().x((d) => x(d.year)).y((d) => y(d.tourIdx));

  g.append("path").datum(rows).attr("d", lineTour).attr("fill", "none").attr("stroke", COLORS.merida).attr("stroke-width", 2.8);
  g.append("path").datum(rows).attr("d", lineTax).attr("fill", "none").attr("stroke", COLORS.foreign).attr("stroke-width", 3);

  // Puntos interactivos
  g.selectAll(".pt-tour")
    .data(rows)
    .join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.tourIdx)).attr("r", 4.5)
    .attr("fill", COLORS.merida).attr("stroke", "#fff").attr("stroke-width", 1.5)
    .on("mousemove", (evt, d) =>
      showTip(evt, `<b>${d.year}</b><br>Turistas de hotel: <b>${fmtM(d.tourists)}</b> (índice ${d.tourIdx.toFixed(1)})<br>Impuesto (pesos nominales): <b>$${(d.taxMxn / 1e6).toFixed(1)} M</b> (índice ${d.taxIdx.toFixed(1)})`)
    )
    .on("mouseleave", hideTip);

  g.selectAll(".pt-tax")
    .data(rows)
    .join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.taxIdx)).attr("r", 4.5)
    .attr("fill", COLORS.foreign).attr("stroke", "#fff").attr("stroke-width", 1.5)
    .on("mousemove", (evt, d) =>
      showTip(evt, `<b>${d.year}</b><br>Impuesto (pesos nominales): <b>$${(d.taxMxn / 1e6).toFixed(1)} M</b> (índice ${d.taxIdx.toFixed(1)})<br>Turistas de hotel: <b>${fmtM(d.tourists)}</b> (índice ${d.tourIdx.toFixed(1)})`)
    )
    .on("mouseleave", hideTip);

  // Etiquetas finales 2025
  const last = rows[rows.length - 1];
  g.append("text").attr("x", x(last.year) + 8).attr("y", y(last.taxIdx) + 4)
    .attr("fill", COLORS.growth).attr("font-family", "'Space Grotesk', sans-serif")
    .attr("font-size", 13).attr("font-weight", 700).text(`${Math.round(last.taxIdx)} (×3.2)`);
  g.append("text").attr("x", x(last.year) + 8).attr("y", y(last.tourIdx) + 4)
    .attr("fill", COLORS.merida).attr("font-family", "'Space Grotesk', sans-serif")
    .attr("font-size", 13).attr("font-weight", 700).text(`${Math.round(last.tourIdx)} (+30%)`);

  // Ejes
  g.append("g")
    .attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format("d")).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", COLORS.grid))
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);

  g.append("g")
    .call(d3.axisLeft(y).ticks(7).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);
}

/* -------------------------------------------------------------------------
 * CAPÍTULO 4 · Prensa local: % de notas núcleo sobre vivienda e inmobiliarias
 * ------------------------------------------------------------------------- */
function renderPressChart(data) {
  const box = d3.select("#chart-press");
  box.selectAll("*").remove();

  const W = 680, H = 260;
  const m = { top: 24, right: 16, bottom: 34, left: 44 };
  const iw = W - m.left - m.right;
  const ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const rows = data.map((d) => ({
    label: d.partial === "True" ? `${d.year}*` : `${d.year}`,
    pct: +d.pct_core,
    core: +d.core,
    articles: +d.articles,
    partial: d.partial === "True",
  }));

  const x = d3.scaleBand().domain(rows.map((d) => d.label)).range([0, iw]).padding(0.28);
  const y = d3.scaleLinear().domain([0, 36]).range([ih, 0]);

  g.append("g")
    .selectAll("line")
    .data([0, 10, 20, 30])
    .join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", COLORS.grid);

  g.selectAll("rect")
    .data(rows)
    .join("rect")
    .attr("x", (d) => x(d.label)).attr("y", (d) => y(d.pct))
    .attr("width", x.bandwidth()).attr("height", (d) => ih - y(d.pct))
    .attr("rx", 3)
    .attr("fill", (d) => (d.partial ? COLORS.meridaSoft : COLORS.merida))
    .on("mousemove", (evt, d) =>
      showTip(evt, `<b>${d.label}</b><br>Notas núcleo: <b>${d.core}</b> de ${d.articles} (${d.pct.toFixed(1)}%)`)
    )
    .on("mouseleave", hideTip);

  g.selectAll("text.val")
    .data(rows)
    .join("text")
    .attr("x", (d) => x(d.label) + x.bandwidth() / 2)
    .attr("y", (d) => y(d.pct) - 6)
    .attr("text-anchor", "middle")
    .attr("fill", COLORS.text).attr("font-family", "'Space Grotesk', sans-serif")
    .attr("font-size", 11).attr("font-weight", 700)
    .text((d) => `${d.pct.toFixed(1)}%`);

  g.append("g")
    .attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", COLORS.grid))
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);

  g.append("g")
    .call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(8).tickFormat((d) => `${d}%`))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);
}

/* -------------------------------------------------------------------------
 * CAPÍTULO 5 · Crecimiento aeroportuario Mérida vs. Oaxaca vs. Cancún (D3)
 * ------------------------------------------------------------------------- */
function renderAirportsChart(data) {
  const box = d3.select("#chart-airports");
  box.selectAll("*").remove();

  const W = 680, H = 310;
  const m = { top: 24, right: 86, bottom: 36, left: 46 };
  const iw = W - m.left - m.right;
  const ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const rows = data
    .filter((d) => +d.year >= 2015 && +d.year <= 2025)
    .map((d) => ({
      code: d.code,
      airport: d.airport,
      year: +d.year,
      total: +d.total,
      pctIntl: +d.pct_international,
      idx: +d.index_2019,
    }));

  const x = d3.scaleLinear().domain([2015, 2025]).range([0, iw]);
  const y = d3.scaleLinear().domain([35, 168]).range([ih, 0]);

  g.append("g")
    .selectAll("line")
    .data([50, 75, 100, 125, 150])
    .join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", (d) => (d === 100 ? COLORS.muted : COLORS.grid))
    .attr("stroke-dasharray", (d) => (d === 100 ? "4,4" : null));

  const series = [
    { code: "OAX", name: "Oaxaca", color: COLORS.oaxaca },
    { code: "MID", name: "Mérida", color: COLORS.merida },
    { code: "CUN", name: "Cancún", color: COLORS.cancun },
  ];

  const line = d3.line().x((d) => x(d.year)).y((d) => y(d.idx));

  series.forEach((s) => {
    const sub = rows.filter((d) => d.code === s.code).sort((a, b) => a.year - b.year);
    g.append("path")
      .datum(sub).attr("d", line).attr("fill", "none")
      .attr("stroke", s.color).attr("stroke-width", s.code === "MID" ? 3.2 : 2.4);

    g.selectAll(`.pt-${s.code}`)
      .data(sub)
      .join("circle")
      .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.idx)).attr("r", 3.8)
      .attr("fill", s.color).attr("stroke", "#fff").attr("stroke-width", 1.2)
      .on("mousemove", (evt, d) =>
        showTip(evt, `<b>${d.airport} (${d.year})</b><br>Índice 2019=100: <b>${d.idx.toFixed(1)}</b><br>Pasajeros: ${fmtM(d.total)} (${d.pctIntl.toFixed(1)}% intl.)`)
      )
      .on("mouseleave", hideTip);

    const last = sub[sub.length - 1];
    g.append("text")
      .attr("x", x(last.year) + 8).attr("y", y(last.idx) + 4)
      .attr("fill", s.color).attr("font-family", "'Space Grotesk', sans-serif")
      .attr("font-size", 12).attr("font-weight", 700)
      .text(`${s.name} ${last.idx.toFixed(0)}`);
  });

  g.append("g")
    .attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d3.format("d")).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", COLORS.grid))
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);

  g.append("g")
    .call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", COLORS.muted).attr("font-size", 11.5);
}

/* -------------------------------------------------------------------------
 * Inicialización de datos
 * ------------------------------------------------------------------------- */
Promise.all([
  d3.csv("data/tourists_annual.csv"),
  d3.csv("data/shops_change.csv"),
  d3.json("data/ageb_cafes.geojson"),
  d3.json("data/centro_historico.geojson"),
  d3.csv("data/tax_vs_tourists.csv"),
  d3.csv("data/press_share.csv"),
  d3.csv("data/press_headlines.csv"),
  d3.csv("data/airports_annual.csv"),
]).then(([tourists, shops, agebCafes, centroGeo, taxTour, pressShare, headlines, airports]) => {
  renderTouristsChart(tourists);
  renderShopsChart(shops, "comparar");
  renderAgebCafesMap(agebCafes, centroGeo);
  renderTaxVsTouristsChart(taxTour);
  renderPressChart(pressShare);
  renderAirportsChart(airports);

  // Selector interactivo de Escena 2 (Comparar / Centro / Municipio)
  document.querySelectorAll("#shops-toggle button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#shops-toggle button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderShopsChart(shops, btn.dataset.mode);
    });
  });

  // Renderizar titulares reales en Capítulo 4
  const qBox = document.getElementById("press-headlines");
  if (qBox) {
    qBox.innerHTML = headlines
      .map(
        (h) => `
      <div class="quote">
        <p>«${h.headline}»</p>
        <span>${h.outlet} · ${h.date}</span>
      </div>`
      )
      .join("");
  }
});
