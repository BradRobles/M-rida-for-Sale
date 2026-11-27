/* Mérida en venta · Gráficas del Dashboard v1 portadas fielmente a D3.js v7 (en español) */

const T = {
  SURFACE: "#FFFFFF",
  TEXT: "#1E1B18",
  TEXT_SOFT: "#3B3631",
  TEXT_MUTED: "#5C554D",
  GRID: "#E6DFD4",
  MERIDA: "#1F5F5B",
  MERIDA_SOFT: "#9FC0BC",
  FOREIGN: "#C8892B",
  GROWTH: "#8A5A17",
  MUTED: "#9A9187",
};

const CAT_SHOPS_ES = {
  "All businesses": "Todos los negocios",
  "Corner stores": "Tiendas de abarrotes",
  "Coffee shops": "Cafeterías",
  "Lodging": "Hospedaje",
  "Restaurants and bars": "Restaurantes y bares",
};

const CAT_LIC_ES = {
  "Commerce and services": "Comercio y servicios",
  "Food and drink": "Alimentos y bebidas",
  "Lodging": "Hospedaje",
  "Not specified": "No especificado",
};

const fmtInt = (v) => Math.round(v).toLocaleString("es-MX");
const fmtPct = (v, d = 1) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v).toFixed(d)}%`;
const shortYear = (y, partial) => `'${String(y).slice(2)}${partial ? "*" : ""}`;

const tip = d3.select("#d3-tip");
function showTip(evt, html) {
  tip.html(html).style("opacity", 1);
  const x = Math.min(window.innerWidth - 260, evt.clientX + 14);
  const y = Math.max(10, evt.clientY - 24);
  tip.style("left", `${x}px`).style("top", `${y}px`);
}
function hideTip() {
  tip.style("opacity", 0);
}

function drawLegend(svg, items, x0, y0) {
  const g = svg.append("g").attr("transform", `translate(${x0},${y0})`);
  let cx = 0;
  items.forEach(({ label, color, type = "rect" }) => {
    if (type === "line") {
      g.append("line").attr("x1", cx).attr("x2", cx + 20).attr("y1", 6).attr("y2", 6)
        .attr("stroke", color).attr("stroke-width", 2.4);
      cx += 26;
    } else {
      g.append("rect").attr("x", cx).attr("y", 1).attr("width", 11).attr("height", 11).attr("rx", 2).attr("fill", color);
      cx += 17;
    }
    const t = g.append("text").attr("x", cx).attr("y", 10.5).attr("fill", T.TEXT_SOFT).attr("font-size", 12).text(label);
    cx += (t.node()?.getComputedTextLength?.() || label.length * 6.8) + 18;
  });
}

/* -------------------------------------------------------------------------
 * 01 · Turistas de hotel por año (barras apiladas, igual a 01_arrival.png)
 * ------------------------------------------------------------------------- */
function renderTouristsStacked(data) {
  const box = d3.select("#chart-tourists");
  box.selectAll("*").remove();
  const W = 680, H = 340, m = { top: 38, right: 12, bottom: 30, left: 42 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  drawLegend(svg, [
    { label: "Extranjeros", color: T.FOREIGN },
    { label: "Nacionales", color: T.MERIDA },
  ], m.left, 8);

  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  const rows = data.map((d) => ({
    label: shortYear(d.year, d.partial === "True"),
    year: +d.year,
    national: +d.national / 1e6,
    foreign: +d.foreign / 1e6,
    total: +d.total / 1e6,
    rawNac: +d.national,
    rawExt: +d.foreign,
    rawTot: +d.total,
    pctExt: +d.pct_foreign,
    partial: d.partial === "True",
  }));

  const x = d3.scaleBand().domain(rows.map((d) => d.label)).range([0, iw]).padding(0.25);
  const y = d3.scaleLinear().domain([0, 2.6]).range([ih, 0]);

  g.selectAll("line.grid").data([0, 0.5, 1, 1.5, 2, 2.5]).join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", T.GRID);

  g.selectAll("rect.nac").data(rows).join("rect")
    .attr("x", (d) => x(d.label)).attr("y", (d) => y(d.national))
    .attr("width", x.bandwidth()).attr("height", (d) => ih - y(d.national))
    .attr("fill", T.MERIDA).attr("opacity", (d) => (d.partial ? 0.55 : 1))
    .on("mousemove", (e, d) => showTip(e, `<b>${d.year}${d.partial ? "* (ene–sep)" : ""}</b><br>Nacionales: ${fmtInt(d.rawNac)}<br>Total: ${fmtInt(d.rawTot)}<br>% extranjeros: ${d.pctExt.toFixed(1)}%`))
    .on("mouseleave", hideTip);

  g.selectAll("rect.ext").data(rows).join("rect")
    .attr("x", (d) => x(d.label)).attr("y", (d) => y(d.total))
    .attr("width", x.bandwidth()).attr("height", (d) => y(d.national) - y(d.total))
    .attr("fill", T.FOREIGN).attr("opacity", (d) => (d.partial ? 0.55 : 1))
    .on("mousemove", (e, d) => showTip(e, `<b>${d.year}${d.partial ? "* (ene–sep)" : ""}</b><br>Extranjeros: ${fmtInt(d.rawExt)}<br>Total: ${fmtInt(d.rawTot)}<br>% extranjeros: ${d.pctExt.toFixed(1)}%`))
    .on("mouseleave", hideTip);

  g.selectAll("text.top").data(rows).join("text")
    .attr("x", (d) => x(d.label) + x.bandwidth() / 2).attr("y", (d) => y(d.total) - 5)
    .attr("text-anchor", "middle").attr("fill", T.TEXT_SOFT).attr("font-size", 10.5)
    .text((d) => d.total.toFixed(2));

  g.append("g").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", T.MUTED))
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);

  g.append("g")
    .call(d3.axisLeft(y).tickValues([0, 0.5, 1, 1.5, 2, 2.5]).tickSize(0).tickPadding(6).tickFormat((d) => `${d}M`))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);
}

/* -------------------------------------------------------------------------
 * 01 · Llegadas mensuales por categoría hotelera (líneas, igual a 01_arrival)
 * ------------------------------------------------------------------------- */
function renderTouristsMonthly(allData, categoryKey) {
  const box = d3.select("#chart-tourists-monthly");
  box.selectAll("*").remove();
  const W = 1120, H = 260, m = { top: 34, right: 16, bottom: 28, left: 46 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  drawLegend(svg, [
    { label: "Nacionales", color: T.MERIDA, type: "line" },
    { label: "Extranjeros", color: T.FOREIGN, type: "line" },
  ], m.left, 6);

  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  const parseDate = d3.timeParse("%Y-%m-%d");
  const rows = allData
    .filter((d) => d.category === categoryKey)
    .map((d) => ({ date: parseDate(d.date), dateStr: d.date.slice(0, 7), nac: +d.national, ext: +d.foreign }))
    .sort((a, b) => a.date - b.date);

  const x = d3.scaleTime().domain(d3.extent(rows, (d) => d.date)).range([0, iw]);
  const y = d3.scaleLinear().domain([0, d3.max(rows, (d) => Math.max(d.nac, d.ext)) * 1.1]).nice().range([ih, 0]);

  g.selectAll("line.grid").data(y.ticks(4)).join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", T.GRID);

  const lNac = d3.line().x((d) => x(d.date)).y((d) => y(d.nac));
  const lExt = d3.line().x((d) => x(d.date)).y((d) => y(d.ext));

  g.append("path").datum(rows).attr("d", lNac).attr("fill", "none").attr("stroke", T.MERIDA).attr("stroke-width", 2);
  g.append("path").datum(rows).attr("d", lExt).attr("fill", "none").attr("stroke", T.FOREIGN).attr("stroke-width", 2);

  // Capa invisible para tooltip interactivo por mes
  const bisect = d3.bisector((d) => d.date).center;
  const hoverLine = g.append("line").attr("y1", 0).attr("y2", ih).attr("stroke", T.MUTED).attr("stroke-dasharray", "3,3").style("opacity", 0);
  g.append("rect").attr("width", iw).attr("height", ih).attr("fill", "transparent")
    .on("mousemove", (evt) => {
      const [mx] = d3.pointer(evt);
      const d = rows[bisect(rows, x.invert(mx))];
      if (!d) return;
      hoverLine.attr("x1", x(d.date)).attr("x2", x(d.date)).style("opacity", 1);
      showTip(evt, `<b>${d.dateStr}</b><br>Nacionales: ${fmtInt(d.nac)}<br>Extranjeros: ${fmtInt(d.ext)}`);
    })
    .on("mouseleave", () => { hoverLine.style("opacity", 0); hideTip(); });

  g.append("g").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).ticks(d3.timeYear.every(2)).tickFormat(d3.timeFormat("%Y")).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", T.MUTED))
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);

  g.append("g")
    .call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(6).tickFormat((d) => (d === 0 ? "0" : `${Math.round(d / 1000)}k`)))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);
}

/* -------------------------------------------------------------------------
 * 02 · Cambio de negocios (barras divergentes, igual a 02_shops.png)
 * ------------------------------------------------------------------------- */
function renderShopsDiverging(allData, areaKey) {
  const box = d3.select("#chart-shops");
  box.selectAll("*").remove();
  const W = 680, H = 285, m = { top: 14, right: 20, bottom: 28, left: 155 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const rows = allData
    .filter((d) => d.area === areaKey)
    .map((d) => ({
      cat: CAT_SHOPS_ES[d.category] || d.category,
      n19: +d.n_2019,
      n25: +d.n_2025,
      change: +d.change,
      pct: +d.pct_change,
    }));

  const x = d3.scaleLinear().domain([-55, 55]).range([0, iw]);
  const y = d3.scaleBand().domain(rows.map((d) => d.cat)).range([0, ih]).padding(0.28);

  g.selectAll("line.grid").data([-40, -20, 0, 20, 40]).join("line")
    .attr("x1", (d) => x(d)).attr("x2", (d) => x(d)).attr("y1", 0).attr("y2", ih)
    .attr("stroke", (d) => (d === 0 ? T.MUTED : T.GRID)).attr("stroke-width", (d) => (d === 0 ? 1.4 : 1));

  g.selectAll("rect").data(rows).join("rect")
    .attr("x", (d) => (d.pct >= 0 ? x(0) : x(d.pct)))
    .attr("y", (d) => y(d.cat))
    .attr("width", (d) => Math.max(2, Math.abs(x(d.pct) - x(0))))
    .attr("height", y.bandwidth())
    .attr("fill", (d) => (d.pct > 0 ? T.FOREIGN : T.MERIDA))
    .on("mousemove", (e, d) => showTip(e, `<b>${d.cat}</b><br>2019: ${fmtInt(d.n19)}<br>2025: ${fmtInt(d.n25)}<br>Cambio: ${d.change > 0 ? "+" : ""}${fmtInt(d.change)} (${fmtPct(d.pct)})`))
    .on("mouseleave", hideTip);

  g.selectAll("text.val").data(rows).join("text")
    .attr("x", (d) => (d.pct >= 0 ? x(d.pct) + 6 : x(d.pct) - 6))
    .attr("y", (d) => y(d.cat) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", (d) => (d.pct >= 0 ? "start" : "end"))
    .attr("fill", T.TEXT).attr("font-size", 12.5)
    .text((d) => fmtPct(d.pct));

  g.append("g")
    .call(d3.axisLeft(y).tickSize(0).tickPadding(10))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT).attr("font-size", 12.5);

  g.append("g").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickValues([-40, -20, 0, 20, 40]).tickSize(0).tickPadding(8).tickFormat((d) => `${d < 0 ? "−" : ""}${Math.abs(d)}%`))
    .call((s) => s.select(".domain").attr("stroke", T.MUTED))
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);
}

/* -------------------------------------------------------------------------
 * 02 · Mapa de AGEB de cafeterías (D3, escala divergente + barra de color)
 * ------------------------------------------------------------------------- */
function renderAgebMap(agebGeo, centroGeo) {
  const box = d3.select("#chart-ageb-map");
  box.selectAll("*").remove();
  const W = 600, H = 460;
  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);

  const cosLat = Math.cos((20.97 * Math.PI) / 180);
  const allPts = [];
  agebGeo.features.forEach((f) => {
    const walk = (c) => (typeof c[0] === "number" ? allPts.push([c[0] * cosLat, -c[1]]) : c.forEach(walk));
    walk(f.geometry.coordinates);
  });
  const minX = d3.min(allPts, (p) => p[0]), maxX = d3.max(allPts, (p) => p[0]);
  const minY = d3.min(allPts, (p) => p[1]), maxY = d3.max(allPts, (p) => p[1]);
  const pad = 18;
  const scale = Math.min((W - 70 - pad) / (maxX - minX), (H - 2 * pad) / (maxY - minY));
  const tx = (W - 55 - (maxX - minX) * scale) / 2 - minX * scale;
  const ty = (H - (maxY - minY) * scale) / 2 - minY * scale;

  const proj = d3.geoTransform({
    point(lon, lat) { this.stream.point(lon * cosLat * scale + tx, -lat * scale + ty); },
  });
  const path = d3.geoPath().projection(proj);

  const color = d3.scaleLinear()
    .domain([-5, -2.5, 0, 2.5, 5])
    .range(["#1F5F5B", "#7FA9A4", "#F4EFE6", "#DDB067", "#8A5A17"])
    .clamp(true);

  svg.append("rect").attr("width", W).attr("height", H).attr("fill", "#F8F6F1");

  svg.append("g").selectAll("path").data(agebGeo.features).join("path")
    .attr("d", path)
    .attr("fill", (d) => color(+d.properties.cafes_change || 0))
    .attr("stroke", "#FFFFFF").attr("stroke-width", 0.45)
    .on("mousemove", (e, d) => {
      const p = d.properties;
      const ch = +p.cafes_change;
      showTip(e, `<b>AGEB ${p.cvegeo}</b><br>Cafeterías 2019: ${p.cafes_2019}<br>2025: ${p.cafes_2025}<br>Cambio: <b>${ch > 0 ? "+" : ""}${ch}</b>`);
    })
    .on("mouseleave", hideTip);

  svg.append("g").selectAll("path").data(centroGeo.features).join("path")
    .attr("d", path).attr("fill", "none").attr("stroke", T.TEXT).attr("stroke-width", 2.2)
    .style("pointer-events", "none");

  // Barra de color vertical a la derecha (igual a 02_shops.png)
  const defs = svg.append("defs");
  const grad = defs.append("linearGradient").attr("id", "agebGrad").attr("x1", "0%").attr("y1", "100%").attr("x2", "0%").attr("y2", "0%");
  [[0, "#1F5F5B"], [25, "#7FA9A4"], [50, "#F4EFE6"], [75, "#DDB067"], [100, "#8A5A17"]].forEach(([o, c]) =>
    grad.append("stop").attr("offset", `${o}%`).attr("stop-color", c)
  );
  const cb = svg.append("g").attr("transform", `translate(${W - 52}, 95)`);
  cb.append("rect").attr("x", -8).attr("y", -24).attr("width", 52).attr("height", 268).attr("rx", 4).attr("fill", "rgba(255,255,255,0.85)");
  cb.append("text").attr("x", 0).attr("y", -8).attr("fill", T.TEXT_SOFT).attr("font-size", 11).text("Cambio");
  cb.append("rect").attr("width", 11).attr("height", 230).attr("fill", "url(#agebGrad)");
  const cbScale = d3.scaleLinear().domain([-5, 5]).range([230, 0]);
  cb.append("g").attr("transform", "translate(13,0)")
    .call(d3.axisRight(cbScale).tickValues([-4, -2, 0, 2, 4]).tickSize(0).tickPadding(4).tickFormat((d) => `${d < 0 ? "−" : ""}${Math.abs(d)}`))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 10);
}

/* -------------------------------------------------------------------------
 * 02 · Licencias de funcionamiento en el Centro por año (apiladas)
 * ------------------------------------------------------------------------- */
function renderLicensesStacked(data) {
  const box = d3.select("#chart-licenses");
  box.selectAll("*").remove();
  const W = 500, H = 310, m = { top: 48, right: 10, bottom: 28, left: 36 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  drawLegend(svg, [
    { label: "Comercio y servicios", color: T.MERIDA },
    { label: "Alimentos y bebidas", color: T.FOREIGN },
  ], m.left, 6);
  drawLegend(svg, [
    { label: "Hospedaje", color: T.GROWTH },
    { label: "No especificado", color: T.MUTED },
  ], m.left, 22);

  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  const order = ["Commerce and services", "Food and drink", "Lodging", "Not specified"];
  const colors = { "Commerce and services": T.MERIDA, "Food and drink": T.FOREIGN, "Lodging": T.GROWTH, "Not specified": T.MUTED };

  const years = Array.from(new Set(data.map((d) => +d.year))).sort((a, b) => a - b);
  const byYear = years.map((yr) => {
    const obj = { year: yr, label: shortYear(yr, yr > 2025), total: 0 };
    order.forEach((c) => { obj[c] = 0; });
    data.filter((d) => +d.year === yr).forEach((d) => {
      obj[d.category] = (obj[d.category] || 0) + (+d.licenses);
      obj.total += +d.licenses;
    });
    return obj;
  });

  const stacked = d3.stack().keys(order)(byYear);
  const x = d3.scaleBand().domain(byYear.map((d) => d.label)).range([0, iw]).padding(0.25);
  const y = d3.scaleLinear().domain([0, d3.max(byYear, (d) => d.total) * 1.18]).range([ih, 0]);

  g.selectAll("line.grid").data(y.ticks(4)).join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d)).attr("stroke", T.GRID);

  g.selectAll("g.layer").data(stacked).join("g")
    .attr("fill", (d) => colors[d.key])
    .selectAll("rect").data((d) => d.map((p) => ({ ...p, key: d.key }))).join("rect")
    .attr("x", (d) => x(d.data.label)).attr("y", (d) => y(d[1]))
    .attr("width", x.bandwidth()).attr("height", (d) => Math.max(0, y(d[0]) - y(d[1])))
    .on("mousemove", (e, d) => showTip(e, `<b>${d.data.year}${d.data.year > 2025 ? "*" : ""}</b><br>${CAT_LIC_ES[d.key]}: ${d[1] - d[0]}<br>Total año: ${d.data.total}`))
    .on("mouseleave", hideTip);

  g.selectAll("text.top").data(byYear).join("text")
    .attr("x", (d) => x(d.label) + x.bandwidth() / 2).attr("y", (d) => y(d.total) - 5)
    .attr("text-anchor", "middle").attr("fill", T.TEXT_SOFT).attr("font-size", 10.5)
    .text((d) => d.total);

  g.append("g").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", T.MUTED))
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 10.5);

  g.append("g")
    .call(d3.axisLeft(y).ticks(4).tickSize(0).tickPadding(6))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);
}

/* -------------------------------------------------------------------------
 * 03 · Impuesto de hospedaje vs. turistas (índice 2019=100, pesos nominales)
 * ------------------------------------------------------------------------- */
function renderTaxIndex(data) {
  const box = d3.select("#chart-tax");
  box.selectAll("*").remove();
  const W = 680, H = 330, m = { top: 38, right: 44, bottom: 28, left: 36 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  drawLegend(svg, [
    { label: "Turistas de hotel (DataTur)", color: T.MERIDA, type: "line" },
    { label: "Impuesto al hospedaje (AAFY, pesos nominales)", color: T.FOREIGN, type: "line" },
  ], m.left, 8);

  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  const rows = data.map((d) => ({
    year: +d.year,
    tax: +d.tax_nominal_mxn,
    tourists: +d.tourists,
    taxIdx: +d.tax_index,
    tourIdx: +d.tourists_index,
  }));

  const x = d3.scaleLinear().domain([2014.7, 2025.6]).range([0, iw]);
  const y = d3.scaleLinear().domain([0, 360]).range([ih, 0]);

  g.selectAll("line.grid").data([0, 50, 100, 150, 200, 250, 300, 350]).join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", (d) => (d === 100 ? T.MUTED : T.GRID))
    .attr("stroke-dasharray", (d) => (d === 100 ? "3,3" : null));

  const lTour = d3.line().x((d) => x(d.year)).y((d) => y(d.tourIdx));
  const lTax = d3.line().x((d) => x(d.year)).y((d) => y(d.taxIdx));
  g.append("path").datum(rows).attr("d", lTour).attr("fill", "none").attr("stroke", T.MERIDA).attr("stroke-width", 2.5);
  g.append("path").datum(rows).attr("d", lTax).attr("fill", "none").attr("stroke", T.FOREIGN).attr("stroke-width", 2.5);

  g.selectAll("circle.t").data(rows).join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.tourIdx)).attr("r", 3.5).attr("fill", T.MERIDA)
    .on("mousemove", (e, d) => showTip(e, `<b>${d.year} · Turistas de hotel</b><br>Índice: ${d.tourIdx.toFixed(1)}<br>Valor: ${fmtInt(d.tourists)}`))
    .on("mouseleave", hideTip);

  g.selectAll("circle.x").data(rows).join("circle")
    .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.taxIdx)).attr("r", 3.5).attr("fill", T.FOREIGN)
    .on("mousemove", (e, d) => showTip(e, `<b>${d.year} · Impuesto al hospedaje (nominal)</b><br>Índice: ${d.taxIdx.toFixed(1)}<br>Recaudación: $${fmtInt(d.tax)} MXN`))
    .on("mouseleave", hideTip);

  const last = rows[rows.length - 1];
  g.append("text").attr("x", x(last.year) + 7).attr("y", y(last.taxIdx) + 4)
    .attr("fill", T.GROWTH).attr("font-size", 13).attr("font-weight", 700).text(Math.round(last.taxIdx));
  g.append("text").attr("x", x(last.year) + 7).attr("y", y(last.tourIdx) + 4)
    .attr("fill", T.MERIDA).attr("font-size", 13).attr("font-weight", 700).text(Math.round(last.tourIdx));

  g.append("g").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickValues([2016, 2018, 2020, 2022, 2024]).tickFormat(d3.format("d")).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", T.MUTED))
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);

  g.append("g")
    .call(d3.axisLeft(y).tickValues([0, 50, 100, 150, 200, 250, 300, 350]).tickSize(0).tickPadding(6))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);
}

/* -------------------------------------------------------------------------
 * 04 · Prensa local (%) + barras horizontales (colonias / palabras YouTube)
 * ------------------------------------------------------------------------- */
function renderPressShare(data) {
  const box = d3.select("#chart-press-share");
  box.selectAll("*").remove();
  const W = 680, H = 300, m = { top: 20, right: 12, bottom: 28, left: 40 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const rows = data.map((d) => ({
    label: d.partial === "True" ? `${d.year}*` : String(d.year),
    pct: +d.pct_core,
    core: +d.core,
    articles: +d.articles,
    partial: d.partial === "True",
  }));

  const x = d3.scaleBand().domain(rows.map((d) => d.label)).range([0, iw]).padding(0.25);
  const y = d3.scaleLinear().domain([0, 38]).range([ih, 0]);

  g.selectAll("line.grid").data([0, 5, 10, 15, 20, 25, 30, 35]).join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d)).attr("stroke", T.GRID);

  g.selectAll("rect").data(rows).join("rect")
    .attr("x", (d) => x(d.label)).attr("y", (d) => y(d.pct))
    .attr("width", x.bandwidth()).attr("height", (d) => ih - y(d.pct))
    .attr("fill", (d) => (d.partial ? T.MERIDA_SOFT : T.MERIDA))
    .on("mousemove", (e, d) => showTip(e, `<b>${d.label}</b><br>${d.core} de ${d.articles} notas (${d.pct.toFixed(1)}%)`))
    .on("mouseleave", hideTip);

  g.selectAll("text.top").data(rows).join("text")
    .attr("x", (d) => x(d.label) + x.bandwidth() / 2).attr("y", (d) => y(d.pct) - 5)
    .attr("text-anchor", "middle").attr("fill", T.TEXT).attr("font-size", 11.5)
    .text((d) => `${Math.round(d.pct)}%`);

  g.append("g").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", T.MUTED))
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);

  g.append("g")
    .call(d3.axisLeft(y).tickValues([0, 5, 10, 15, 20, 25, 30, 35]).tickSize(0).tickPadding(6).tickFormat((d) => `${d}%`))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);
}

function renderHbars(selector, data, labelKey, valKey, color, height = 340) {
  const box = d3.select(selector);
  box.selectAll("*").remove();
  const W = 680, H = height, m = { top: 10, right: 54, bottom: 10, left: 155 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const rows = data.map((d) => ({ lbl: d[labelKey], val: +d[valKey] }));
  const x = d3.scaleLinear().domain([0, d3.max(rows, (d) => d.val) * 1.15]).range([0, iw]);
  const y = d3.scaleBand().domain(rows.map((d) => d.lbl)).range([0, ih]).padding(0.24);

  g.selectAll("rect").data(rows).join("rect")
    .attr("x", 0).attr("y", (d) => y(d.lbl))
    .attr("width", (d) => x(d.val)).attr("height", y.bandwidth()).attr("fill", color)
    .on("mousemove", (e, d) => showTip(e, `<b>${d.lbl}</b>: ${fmtInt(d.val)}`))
    .on("mouseleave", hideTip);

  g.selectAll("text.val").data(rows).join("text")
    .attr("x", (d) => x(d.val) + 6).attr("y", (d) => y(d.lbl) + y.bandwidth() / 2 + 4)
    .attr("fill", T.TEXT).attr("font-size", 11.5).text((d) => fmtInt(d.val));

  g.append("g")
    .call(d3.axisLeft(y).tickSize(0).tickPadding(10))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT).attr("font-size", 12.5);
}

/* -------------------------------------------------------------------------
 * 05 · Cuatro mini-barras comparativas + línea mensual de pasajeros ASUR
 * ------------------------------------------------------------------------- */
function renderCompareBars(selector, rows, fmt, scaleMax) {
  const box = d3.select(selector);
  box.selectAll("*").remove();
  const H = 56 + 38 * rows.length;
  const W = 520, m = { top: 10, right: 56, bottom: 10, left: 145 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const lo = Math.min(0, d3.min(rows, (d) => d.val)) * 2.4;
  const x = d3.scaleLinear().domain([lo, scaleMax]).range([0, iw]);
  const y = d3.scaleBand().domain(rows.map((d) => d.name)).range([0, ih]).padding(0.24);

  if (lo < 0) {
    g.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", 0).attr("y2", ih).attr("stroke", T.MUTED);
  }

  g.selectAll("rect").data(rows).join("rect")
    .attr("x", (d) => (d.val >= 0 ? x(0) : x(d.val)))
    .attr("y", (d) => y(d.name))
    .attr("width", (d) => Math.max(2, Math.abs(x(d.val) - x(0))))
    .attr("height", y.bandwidth())
    .attr("fill", (d) => (d.highlight ? T.MERIDA : d.val < 0 ? T.MUTED : T.FOREIGN))
    .on("mousemove", (e, d) => showTip(e, `<b>${d.name}</b>: ${fmt(d.val)}`))
    .on("mouseleave", hideTip);

  g.selectAll("text.val").data(rows).join("text")
    .attr("x", (d) => (d.val >= 0 ? x(d.val) + 6 : x(d.val) - 6))
    .attr("y", (d) => y(d.name) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", (d) => (d.val >= 0 ? "start" : "end"))
    .attr("fill", T.TEXT).attr("font-size", 11.5)
    .text((d) => fmt(d.val));

  g.append("g")
    .call(d3.axisLeft(y).tickSize(0).tickPadding(10))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT).attr("font-size", 12);
}

function renderAirportsMonthly(data) {
  const box = d3.select("#chart-airports-monthly");
  box.selectAll("*").remove();
  const W = 1120, H = 280, m = { top: 36, right: 16, bottom: 28, left: 40 };
  const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

  const svg = box.append("svg").attr("viewBox", `0 0 ${W} ${H}`);
  drawLegend(svg, [
    { label: "Mérida (MID)", color: T.MERIDA, type: "line" },
    { label: "Cancún (CUN)", color: T.FOREIGN, type: "line" },
    { label: "Oaxaca (OAX)", color: T.MUTED, type: "line" },
  ], m.left, 8);

  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  const parseDate = d3.timeParse("%Y-%m-%d");
  const rows = data.map((d) => ({
    code: d.code,
    date: parseDate(d.date),
    dateStr: d.date.slice(0, 7),
    idx: +d.index_same_month_2019,
  })).sort((a, b) => a.date - b.date);

  const x = d3.scaleTime().domain(d3.extent(rows, (d) => d.date)).range([0, iw]);
  const y = d3.scaleLinear().domain([0, 210]).range([ih, 0]);

  g.selectAll("line.grid").data([0, 50, 100, 150, 200]).join("line")
    .attr("x1", 0).attr("x2", iw).attr("y1", (d) => y(d)).attr("y2", (d) => y(d))
    .attr("stroke", (d) => (d === 100 ? T.MUTED : T.GRID))
    .attr("stroke-dasharray", (d) => (d === 100 ? "3,3" : null));

  const line = d3.line().x((d) => x(d.date)).y((d) => y(d.idx));
  const styles = [
    { code: "OAX", name: "Oaxaca (OAX)", color: T.MUTED, w: 1.8 },
    { code: "CUN", name: "Cancún (CUN)", color: T.FOREIGN, w: 1.8 },
    { code: "MID", name: "Mérida (MID)", color: T.MERIDA, w: 3 },
  ];
  const byCode = {};
  styles.forEach((s) => {
    const sub = rows.filter((d) => d.code === s.code);
    byCode[s.code] = sub;
    g.append("path").datum(sub).attr("d", line).attr("fill", "none").attr("stroke", s.color).attr("stroke-width", s.w);
  });

  const bisect = d3.bisector((d) => d.date).center;
  const hoverLine = g.append("line").attr("y1", 0).attr("y2", ih).attr("stroke", T.MUTED).attr("stroke-dasharray", "3,3").style("opacity", 0);
  g.append("rect").attr("width", iw).attr("height", ih).attr("fill", "transparent")
    .on("mousemove", (evt) => {
      const [mx] = d3.pointer(evt);
      const dt = x.invert(mx);
      const dm = byCode.MID[bisect(byCode.MID, dt)];
      const dc = byCode.CUN[bisect(byCode.CUN, dt)];
      const dox = byCode.OAX[bisect(byCode.OAX, dt)];
      if (!dm) return;
      hoverLine.attr("x1", x(dm.date)).attr("x2", x(dm.date)).style("opacity", 1);
      showTip(evt, `<b>${dm.dateStr}</b> (2019 = 100)<br>Mérida: <b>${dm.idx.toFixed(0)}</b><br>Oaxaca: ${dox ? dox.idx.toFixed(0) : "—"}<br>Cancún: ${dc ? dc.idx.toFixed(0) : "—"}`);
    })
    .on("mouseleave", () => { hoverLine.style("opacity", 0); hideTip(); });

  g.append("g").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).ticks(d3.timeYear.every(1)).tickFormat(d3.timeFormat("%Y")).tickSize(0).tickPadding(8))
    .call((s) => s.select(".domain").attr("stroke", T.MUTED))
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);

  g.append("g")
    .call(d3.axisLeft(y).tickValues([0, 50, 100, 150, 200]).tickSize(0).tickPadding(6))
    .call((s) => s.select(".domain").remove())
    .selectAll("text").attr("fill", T.TEXT_MUTED).attr("font-size", 11);
}

/* -------------------------------------------------------------------------
 * Arranque y selectores interactivos
 * ------------------------------------------------------------------------- */
Promise.all([
  d3.csv("data/tourists_annual.csv"),
  d3.csv("data/tourists_monthly_category.csv"),
  d3.csv("data/shops_change.csv"),
  d3.json("data/ageb_cafes.geojson"),
  d3.json("data/centro_historico.geojson"),
  d3.csv("data/licenses_centro.csv"),
  d3.csv("data/tax_vs_tourists.csv"),
  d3.csv("data/press_share.csv"),
  d3.csv("data/press_headlines.csv"),
  d3.csv("data/press_top_neighbourhoods.csv"),
  d3.csv("data/youtube_keywords.csv"),
  d3.csv("data/youtube_top_videos.csv"),
  d3.csv("data/airports_annual.csv"),
  d3.csv("data/home_prices_2025T3.csv"),
  d3.csv("data/wikipedia_index.csv"),
  d3.csv("data/airports_monthly.csv"),
]).then(([
  tourAnn, tourMon, shops, agebGeo, centroGeo, licenses, taxTour,
  pressShare, pressHeads, pressCols, ytKw, ytVids, airAnn, homes, wiki, airMon,
]) => {
  // 01
  renderTouristsStacked(tourAnn);
  renderTouristsMonthly(tourMon, "All categories");
  document.querySelectorAll("#cat-seg button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#cat-seg button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      renderTouristsMonthly(tourMon, btn.dataset.cat);
    });
  });

  // 02
  const updateShops = (areaKey, areaLabel) => {
    const tot = shops.find((d) => d.area === areaKey && d.category === "All businesses");
    document.getElementById("shops-sub").textContent =
      `${areaLabel}: ${fmtInt(+tot.n_2019)} → ${fmtInt(+tot.n_2025)} negocios · pasa el cursor para ver conteos`;
    renderShopsDiverging(shops, areaKey);
  };
  updateShops("Centro", "Centro Histórico");
  document.querySelectorAll("#area-seg button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#area-seg button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      updateShops(btn.dataset.area, btn.textContent.trim());
    });
  });
  renderAgebMap(agebGeo, centroGeo);
  renderLicensesStacked(licenses);

  // 03
  renderTaxIndex(taxTour);

  // 04
  renderPressShare(pressShare);
  renderHbars("#chart-press-cols", pressCols, "neighbourhood", "articles", T.MERIDA, 340);
  renderHbars("#chart-yt-kw", ytKw, "keyword", "mentions", T.FOREIGN, 290);

  document.getElementById("press-quotes").innerHTML =
    `<p class="mfs-fig-sub"><b>Titulares del corpus</b></p>` +
    pressHeads.map((h) => `<p>«${h.headline}»<br><span class="mfs-note">${h.outlet}, ${h.date}</span></p>`).join("") +
    `<span class="mfs-note">332 notas núcleo, 2018 a nov 2026, Diario de Yucatán, Por Esto! y La Jornada Maya.</span>`;

  document.getElementById("yt-quotes").innerHTML =
    `<p class="mfs-fig-sub"><b>Videos más vistos</b></p>` +
    ytVids.map((v) => `<p>«${v.title}» · ${Math.round(+v.views / 1000).toLocaleString("es-MX")}k vistas</p>`).join("") +
    `<span class="mfs-note">349 videos sobre mudarse a Mérida, 5.35M vistas, 73% en inglés.</span>`;

  document.getElementById("yt-table-body").innerHTML = ytVids
    .map((v) => `<tr><td>${v.title}</td><td class="num">${fmtInt(+v.views)}</td><td>${v.published}</td><td>${v.channel}</td></tr>`)
    .join("");

  document.querySelectorAll("#voice-seg button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#voice-seg button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const isLocal = btn.dataset.voice === "local";
      document.getElementById("voice-local-left").classList.toggle("hidden", !isLocal);
      document.getElementById("voice-local-right").classList.toggle("hidden", !isLocal);
      document.getElementById("voice-ext-left").classList.toggle("hidden", isLocal);
      document.getElementById("voice-ext-right").classList.toggle("hidden", isLocal);
    });
  });

  // 05
  const a25 = airAnn.filter((d) => +d.year === 2025);
  const nameMap = { MID: "Mérida (MID)", CUN: "Cancún (CUN)", OAX: "Oaxaca (OAX)" };
  renderCompareBars(
    "#chart-cmp-growth",
    [...a25].sort((a, b) => +b.index_2019 - +a.index_2019).map((d) => ({ name: nameMap[d.code], val: +d.index_2019, highlight: d.code === "MID" })),
    (v) => `${Math.round(v)}`, 190
  );
  renderCompareBars(
    "#chart-cmp-intl",
    [...a25].sort((a, b) => +b.pct_international - +a.pct_international).map((d) => ({ name: nameMap[d.code], val: +d.pct_international, highlight: d.code === "MID" })),
    (v) => `${v.toFixed(1)}%`, 85
  );
  const stateOrder = ["Yucatán", "Oaxaca", "Quintana Roo", "Guanajuato"];
  const homeByState = Object.fromEntries(homes.map((d) => [d.state, +d.vs_national_pct]));
  renderCompareBars(
    "#chart-cmp-homes",
    stateOrder.map((s) => ({ name: s, val: homeByState[s], highlight: s === "Yucatán" })),
    (v) => fmtPct(v), 52
  );
  renderCompareBars(
    "#chart-cmp-wiki",
    wiki.map((d) => ({ name: d.city, val: +d.index_2025, highlight: d.city === "Mérida" })),
    (v) => `${Math.round(v)}`, 125
  );
  renderAirportsMonthly(airMon);
});
