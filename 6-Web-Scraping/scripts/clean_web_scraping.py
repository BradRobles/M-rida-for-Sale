"""
Extracción y limpieza de la sección 6-Web-Scraping.

Fuentes cubiertas:
- Principal: prensa local de Yucatán sobre rentas, desalojos y gentrificación (2018 a la fecha).
  * Diario de Yucatán (`https://www.yucatan.com.mx/`): sitemaps `post-sitemapN.xml`.
  * Por Esto! (`https://www.poresto.com/`): sitemaps mensuales `sitemaps/AAAA/poresto_map_AAAA_MM.xml`.
  * La Jornada Maya (`https://www.lajornadamaya.mx/`): su sitemap solo trae las ~250 notas más
    recientes y el buscador interno funciona con JavaScript, así que las URL históricas se
    descubren con el índice CDX de Internet Archive (solo para descubrir; el cuerpo se baja del
    sitio original) más el sitemap y el RSS actuales.
  Se respeta `robots.txt` (copia fechada en `raw/robots/`), pausa ≥ 2 s por sitio, reintentos y
  caché en `raw/sitemaps/` y `raw/html/` (ambos fuera de git). En `clean/` solo van metadatos,
  conteos y un extracto de ≤ 200 caracteres.
- Complemento A: YouTube Data API v3 (videos "moving to Merida"). Requiere la variable de entorno
  `YOUTUBE_API_KEY`; sin ella esta parte se salta. De comentarios solo se guardan conteos.
- Complemento B: Wikimedia Pageviews API, vistas mensuales desde 2016 de Mérida (en/es) y de
  Oaxaca de Juárez, San Miguel de Allende y Playa del Carmen, con índice 2019 = 100.

Uso:
    python 6-Web-Scraping/scripts/clean_web_scraping.py                 # todo
    python 6-Web-Scraping/scripts/clean_web_scraping.py --solo prensa   # prensa | youtube | wikipedia
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html as html_lib
import importlib.util
import json
import os
import random
import re
import threading
import time
import urllib.robotparser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
RAW_DIR = BASE_DIR / "raw"
CLEAN_DIR = BASE_DIR / "clean"
ROBOTS_DIR = RAW_DIR / "robots"
SITEMAP_DIR = RAW_DIR / "sitemaps"
HTML_DIR = RAW_DIR / "html"
YT_DIR = RAW_DIR / "youtube"
WIKI_DIR = RAW_DIR / "wikipedia"
COLONIAS_CSV = ROOT_DIR / "4-GeoPortal-Merida" / "clean" / "geoportal_colonias_merida_catalogo.csv"

# Reglas de temas compartidas con la sección 7.
_spec = importlib.util.spec_from_file_location(
    "clasificacion", ROOT_DIR / "7-Self-Produced" / "scripts" / "clasificacion.py")
clasificacion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(clasificacion)
normalizar = clasificacion.normalizar
temas_resumidos = clasificacion.temas_resumidos

USER_AGENT = "MeridaForSale-UPY/1.0 (+https://github.com/BradRobles/M-rida-for-Sale)"
PAUSA_S = 2.5
TOPE_TOTAL = 1500
ANIO_INICIO = 2018

# ---------------------------------------------------------------------------
# HTTP con pausa por sitio, reintentos y caché
# ---------------------------------------------------------------------------
_locks: dict[str, threading.Lock] = {}
_ultima: dict[str, float] = {}
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "es-MX,es;q=0.9"})


def http_get(url: str, pausa: float = PAUSA_S, intentos: int = 4, **kw) -> requests.Response | None:
    host = urlparse(url).netloc
    lock = _locks.setdefault(host, threading.Lock())
    timeout = kw.pop("timeout", 60)
    for i in range(intentos):
        with lock:
            espera = pausa - (time.time() - _ultima.get(host, 0))
            if espera > 0:
                time.sleep(espera)
            _ultima[host] = time.time()
            try:
                r = SESSION.get(url, timeout=timeout, **kw)
            except requests.RequestException:
                r = None
        if r is not None and r.status_code == 200:
            return r
        if r is not None and r.status_code in (404, 410, 403):
            return r
        time.sleep(5 * 2**i)
    return None


def cache_get(url: str, destino: Path, pausa: float = PAUSA_S, **kw) -> str | None:
    """Descarga con caché gzip en disco. Devuelve el texto o None."""
    if destino.exists():
        return gzip.decompress(destino.read_bytes()).decode("utf-8", errors="replace")
    r = http_get(url, pausa=pausa, **kw)
    if r is None or r.status_code != 200:
        return None
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        texto = r.content.decode("utf-8")
    except UnicodeDecodeError:
        texto = r.content.decode(r.encoding or "latin-1", errors="replace")
    destino.write_bytes(gzip.compress(texto.encode("utf-8")))
    return texto


# ---------------------------------------------------------------------------
# Principal: prensa local
# ---------------------------------------------------------------------------
SITIOS = {
    "diario_de_yucatan": {"host": "www.yucatan.com.mx", "robots": "yucatan.com.mx"},
    "por_esto": {"host": "www.poresto.com", "robots": "poresto.com"},
    "la_jornada_maya": {"host": "www.lajornadamaya.mx", "robots": "lajornadamaya.mx"},
}

# Palabras clave (se buscan como prefijo de cada palabra del slug/título, ya normalizado).
PALABRAS_CLAVE = {
    "gentrific": "gentrific", "turistific": "turistific", "renta": "renta", "rentas": "renta",
    "rentar": "renta", "alquil": "alquiler", "desaloj": "desalojo", "despoj": "despojo",
    "airbnb": "airbnb", "plusval": "plusvalia", "inmobiliari": "inmobiliari", "vivienda": "vivienda",
    "extranjer": "extranjer",
}
FRASES_CLAVE = {"nomada digital": "nomada digital", "nomadas digitales": "nomada digital",
                "centro historico": "centro historico"}
FUERTES = {"gentrific", "turistific", "desalojo", "despojo", "airbnb", "plusvalia", "nomada digital",
           "alquiler", "inmobiliari"}
# Palabras que empiezan como una clave pero no son del tema.
FALSOS = {"rentabilidad", "rentable", "rentables", "renta-car"}


def palabras_clave(texto: str) -> list[str]:
    t = re.sub(r"[^a-z0-9]+", " ", normalizar(texto))
    tokens = t.split()
    hallados = set()
    for tok in tokens:
        if tok in FALSOS:
            continue
        for pref, clave in PALABRAS_CLAVE.items():
            if tok.startswith(pref) and not (pref.startswith("renta") and tok.startswith("rentab")):
                if pref in ("renta", "rentas", "rentar") and tok not in ("renta", "rentas", "rentar", "rentan", "rentado", "rentados", "rentada", "rentadas"):
                    continue
                hallados.add(clave)
    unido = " ".join(tokens)
    for frase, clave in FRASES_CLAVE.items():
        if f" {frase} " in f" {unido} ":
            hallados.add(clave)
    return sorted(hallados)


def guardar_robots() -> dict[str, urllib.robotparser.RobotFileParser]:
    ROBOTS_DIR.mkdir(parents=True, exist_ok=True)
    hoy = date.today().isoformat()
    parsers = {}
    for fuente, s in SITIOS.items():
        previos = sorted(ROBOTS_DIR.glob(f"{s['robots']}_robots_*.txt"))
        if previos:
            texto = previos[-1].read_text(encoding="utf-8")
        else:
            r = http_get(f"https://{s['host']}/robots.txt")
            texto = r.text if r is not None and r.status_code == 200 else ""
            (ROBOTS_DIR / f"{s['robots']}_robots_{hoy}.txt").write_text(texto, encoding="utf-8")
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(texto.splitlines())
        parsers[fuente] = rp
    return parsers


def _locs(xml: str) -> list[str]:
    return [html_lib.unescape(u).strip() for u in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml or "")]


def descubrir_diario() -> list[str]:
    host = SITIOS["diario_de_yucatan"]["host"]
    idx = cache_get(f"https://{host}/sitemap.xml", SITEMAP_DIR / "diario_de_yucatan" / "sitemap.xml.gz")
    urls = []
    for sm in _locs(idx):
        if "post-sitemap" not in sm:
            continue
        xml = cache_get(sm, SITEMAP_DIR / "diario_de_yucatan" / (Path(urlparse(sm).path).name + ".gz"))
        if xml is None:
            print(f"  AVISO: no se pudo leer {sm}; vuelve a correr el script para completarlo")
        urls += _locs(xml)
    return urls


def descubrir_porresto() -> list[str]:
    host = SITIOS["por_esto"]["host"]
    idx = cache_get(f"https://{host}/sitemaps/poresto_map_index.xml",
                    SITEMAP_DIR / "por_esto" / "poresto_map_index.xml.gz")
    urls = []
    for sm in _locs(idx):
        m = re.search(r"poresto_map_(\d{4})_(\d{2})\.xml", sm)
        if not m or int(m.group(1)) < ANIO_INICIO:
            continue
        xml = cache_get(sm, SITEMAP_DIR / "por_esto" / (Path(urlparse(sm).path).name + ".gz"))
        if xml is None:
            print(f"  AVISO: no se pudo leer {sm}; vuelve a correr el script para completarlo")
        urls += _locs(xml)
    return urls


def descubrir_jornada() -> list[str]:
    host = SITIOS["la_jornada_maya"]["host"]
    urls = _locs(cache_get(f"https://{host}/sitemap.xml",
                           SITEMAP_DIR / "la_jornada_maya" / f"sitemap_{date.today():%Y-%m}.xml.gz"))
    rss = cache_get(f"https://{host}/feed_rss.xml", SITEMAP_DIR / "la_jornada_maya" / f"rss_{date.today():%Y-%m}.xml.gz")
    urls += [html_lib.unescape(u) for u in re.findall(r"<link>\s*(https://www\.lajornadamaya\.mx/[^<]+?)\s*</link>", rss or "")]
    # Índice CDX de Internet Archive, filtrado por palabras clave en la URL (una consulta por sección).
    regex = ".*(gentrific|turistific|renta|alquil|desaloj|despoj|airbnb|plusval|inmobiliari|vivienda|extranjer|nomada|centro-historico).*"
    for seccion in ("yucatan", "merida", "opinion", "quintana-roo", "nacional", "cultura", "economia"):
        destino = SITEMAP_DIR / "la_jornada_maya" / f"cdx_{seccion}.txt.gz"
        params = (f"url=lajornadamaya.mx/{seccion}/&matchType=prefix&fl=original&collapse=urlkey"
                  f"&filter=statuscode:200&filter=original:{quote(regex)}&limit=50000")
        texto = cache_get(f"https://web.archive.org/cdx/search/cdx?{params}", destino, pausa=5.0, timeout=180)
        if texto and "<html" not in texto[:200].lower():
            urls += [u.strip() for u in texto.splitlines() if u.strip()]
    limpias = []
    for u in urls:
        u = re.sub(r"^http://", "https://", u.split("?")[0].split("#")[0])
        u = re.sub(r"^https://lajornadamaya", "https://www.lajornadamaya", u)
        u = re.sub(r":80/", "/", u)
        if re.match(r"https://www\.lajornadamaya\.mx/[a-z-]+/\d{4,}/[^/]+$", u):
            limpias.append(u)
    return limpias


def info_url(fuente: str, url: str) -> dict | None:
    """Fecha, sección y slug desde la URL (sin descargar)."""
    p = urlparse(url).path
    if fuente == "diario_de_yucatan":
        m = re.match(r"/([a-z0-9-]+(?:/[a-z0-9-]+)*)/(\d{4})/(\d{1,2})/(\d{1,2})/([^/]+?)(?:\.html)?/?$", p)
        if not m:
            return None
        return {"seccion": m.group(1), "fecha": f"{m.group(2)}-{int(m.group(3)):02d}-{int(m.group(4)):02d}",
                "slug": m.group(5)}
    if fuente == "por_esto":
        m = re.match(r"/([a-z0-9-]+(?:/[a-z0-9-]+)*)/(\d{4})/(\d{1,2})/(\d{1,2})/([^/]+?)(?:\.html)?/?$", p)
        if not m:
            return None
        return {"seccion": m.group(1), "fecha": f"{m.group(2)}-{int(m.group(3)):02d}-{int(m.group(4)):02d}",
                "slug": m.group(5)}
    m = re.match(r"/([a-z-]+)/(\d{4,})/([^/]+)$", p)
    if not m:
        return None
    return {"seccion": m.group(1), "fecha": "", "slug": m.group(3), "id": int(m.group(2))}


def seccion_relevante(fuente: str, seccion: str) -> bool:
    """Solo secciones de Mérida/Yucatán (y opinión/local), no Quintana Roo, Campeche ni internacional."""
    s = seccion.split("/")[0]
    if fuente == "diario_de_yucatan":
        return s in {"merida", "yucatan", "imagen", "local", "editorial", "opinion", "sociedad", "economia",
                     "negocios", "yucatan-ahora", "actualidad"}
    if fuente == "por_esto":
        return s in {"yucatan", "merida", "opinion", "economia", "mundo-yucatan"} or s.startswith("yucatan")
    return s in {"yucatan", "merida", "opinion", "economia", "cultura"}


def candidatos(parsers) -> pd.DataFrame:
    filas = []
    descubridores = {"diario_de_yucatan": descubrir_diario, "por_esto": descubrir_porresto,
                     "la_jornada_maya": descubrir_jornada}
    with ThreadPoolExecutor(max_workers=3) as ex:
        resultados = {f: ex.submit(fn) for f, fn in descubridores.items()}
    for fuente, fut in resultados.items():
        urls = sorted(set(fut.result()))
        print(f"  {fuente}: {len(urls)} URL en sitemaps/índices")
        for u in urls:
            inf = info_url(fuente, u)
            if inf is None:
                continue
            if inf["fecha"] and int(inf["fecha"][:4]) < ANIO_INICIO:
                continue
            if not parsers[fuente].can_fetch(USER_AGENT, u):
                continue
            claves = palabras_clave(inf["slug"].replace("-", " "))
            if not claves:
                continue
            filas.append({"fuente": fuente, "url": u, "fecha_url": inf["fecha"], "seccion": inf["seccion"],
                          "palabras_clave_url": ";".join(claves),
                          "seccion_relevante": seccion_relevante(fuente, inf["seccion"]),
                          "n_fuertes": len(FUERTES & set(claves)), "id_url": inf.get("id")})
    df = pd.DataFrame(filas).drop_duplicates("url")
    return df


def seleccionar(df: pd.DataFrame) -> pd.DataFrame:
    """Tope de ~1,500: primero todas las notas con claves fuertes; el resto por muestreo
    aleatorio reproducible (semilla 2026), repartido entre fuentes."""
    rel = df[df["seccion_relevante"]].copy()
    fuertes = rel[rel["n_fuertes"] > 0]
    debiles = rel[rel["n_fuertes"] == 0]
    if len(fuertes) >= TOPE_TOTAL:
        sel = fuertes.sample(TOPE_TOTAL, random_state=2026)
    else:
        resto = TOPE_TOTAL - len(fuertes)
        por_fuente = max(resto // max(debiles["fuente"].nunique(), 1), 1)
        partes = [g.sample(min(len(g), por_fuente), random_state=2026) for _, g in debiles.groupby("fuente")]
        sel = pd.concat([fuertes] + partes)
        faltan = TOPE_TOTAL - len(sel)
        if faltan > 0:
            sobrante = debiles.drop(sel.index, errors="ignore")
            sel = pd.concat([sel, sobrante.sample(min(faltan, len(sobrante)), random_state=2026)])
    df["seleccionado"] = df.index.isin(sel.index)
    return df


# ------------------------------- extracción --------------------------------
def _jsonld(soup: BeautifulSoup) -> dict:
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        cands = d if isinstance(d, list) else d.get("@graph", [d]) if isinstance(d, dict) else []
        for c in cands:
            if isinstance(c, dict) and ("NewsArticle" in str(c.get("@type")) or "Article" in str(c.get("@type"))):
                return c
    return {}


def _fecha(texto: str) -> str:
    texto = (texto or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", texto)
    if m:
        return m.group(0)
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", texto)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return ""


def extraer(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    ld = _jsonld(soup)
    meta = lambda prop: (soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop}) or {}).get("content", "")  # noqa: E731
    titulo = ld.get("headline") or meta("og:title") or (soup.title.string if soup.title else "")
    fecha = _fecha(ld.get("datePublished", "")) or _fecha(meta("article:published_time"))
    seccion = ld.get("articleSection") or meta("article:section")
    if isinstance(seccion, list):
        seccion = ",".join(seccion)
    cuerpo = ld.get("articleBody") or ""
    if len(cuerpo) < 200:
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()
        cont = soup.find("article") or soup.find("div", class_=re.compile("entry-content|article-body|nota|content-body|cuerpo")) or soup
        cuerpo = " ".join(p.get_text(" ", strip=True) for p in cont.find_all("p"))
    cuerpo = " ".join(html_lib.unescape(cuerpo).split())
    return {"titulo": " ".join(html_lib.unescape(titulo or "").split()), "fecha": fecha,
            "seccion_html": str(seccion or "").split("/")[-1], "cuerpo": cuerpo}


# --------------------------- colonias mencionadas ---------------------------
PREFIJOS_CATALOGO = r"^(col\.?|fracc\.?|u\.?\s*hab\.?|unidad habitacional|residencial|privada|res\.?|barrio)\s+"
CONTEXTO = r"(?:colonia|col\.|fraccionamiento|fracc\.|barrio(?: de)?|residencial|unidad habitacional)\s+(?:de\s+)?(?:la\s+|el\s+|los\s+|las\s+)?"
# Barrios tradicionales y colonias muy conocidas: (patrón, nombre, unidad_habitacional del GeoPortal)
BARRIOS = [
    (r"centro historico(?! de (?:campeche|la ciudad de mexico|cdmx|valladolid|izamal))|centro de merida", "Centro Histórico", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|templo|mercado|plaza) de santiago", "Santiago", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|templo|plaza|arco) de santa ana", "Santa Ana", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|templo|plaza|arco) de san sebastian", "San Sebastián", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|templo|plaza) de (?:la )?mejorada|\bla mejorada\b", "La Mejorada", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|templo|plaza|arco) de san juan(?! grande)", "San Juan", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|templo|plaza) de san cristobal(?! de las casas)", "San Cristóbal", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|templo|plaza) de santa lucia", "Santa Lucía", "COL. CENTRO"),
    (r"(?:barrio|parque|iglesia|ermita) de (?:la )?ermita|ermita de santa isabel", "La Ermita", "COL. CENTRO"),
    (r"paseo (?:de )?montejo", "Paseo de Montejo", "COL. CENTRO"),
    (r"\bitzimna\b", "Itzimná", "COL. ITZIMNA"),
    (r"garcia gineres", "García Ginerés", "COL. GARCIA GINERES"),
    (r"\bchuburna\b(?! de hidalgo)|chuburna de hidalgo", "Chuburná", "COL. CHUBURNA DE HIDALGO"),
    (r"\bcolonia aleman\b|\bla aleman\b|miguel aleman", "Miguel Alemán", "COL. MIGUEL ALEMAN"),
    (r"\bcolonia mexico\b(?! norte| oriente)", "México", "COL. MEXICO"),
    (r"\bbenito juarez norte\b", "Benito Juárez Norte", "COL. BENITO JUAREZ NORTE"),
]


def patrones_colonias() -> list[tuple[re.Pattern, str, str]]:
    cat = pd.read_csv(COLONIAS_CSV, dtype=str)
    pats = [(re.compile(p), n, u) for p, n, u in BARRIOS]
    ya = {u for _, _, u in BARRIOS}
    for uh in sorted(cat["unidad_habitacional"].dropna().unique()):
        base = re.sub(PREFIJOS_CATALOGO, "", normalizar(uh)).strip()
        base = re.sub(r"\s*\(.*?\)", "", base).strip()
        base = re.sub(r"[^a-z0-9 ]", " ", base)
        base = " ".join(base.split())
        if len(base) < 4 or base in {"centro", "mexico", "yucatan", "merida"}:
            continue
        if uh in ya and uh != "COL. MEXICO":
            continue
        pats.append((re.compile(r"\b" + CONTEXTO + re.escape(base) + r"\b"), uh.split(". ", 1)[-1].title(), uh))
    return pats


def colonias_en(texto: str, pats) -> list[tuple[str, str]]:
    """Colonias del GeoPortal y barrios mencionados. Solo cuenta si la nota menciona Mérida
    (muchos nombres de colonias se repiten en Campeche, Quintana Roo y otros municipios)."""
    t = re.sub(r"[^a-z0-9.\s]", " ", normalizar(texto))
    t = " ".join(t.split())
    if not re.search(r"\bmerida\b", t):
        return []
    vistos = {}
    for p, nombre, uh in pats:
        if p.search(t) and uh not in vistos:
            vistos[uh] = nombre
    return [(n, u) for u, n in vistos.items()]


def descargar_articulos(sel: pd.DataFrame) -> dict[str, str]:
    def uno(url: str) -> tuple[str, str | None]:
        h = hashlib.sha1(url.encode()).hexdigest()[:16]
        host = urlparse(url).netloc.replace("www.", "")
        return url, cache_get(url, HTML_DIR / host / f"{h}.html.gz")
    out = {}
    urls = list(sel["url"])
    with ThreadPoolExecutor(max_workers=3) as ex:
        # una cola por sitio para que la pausa por host no bloquee a los demás
        por_sitio = {}
        for u in urls:
            por_sitio.setdefault(urlparse(u).netloc, []).append(u)
        def trabajar(lista):
            res = []
            for i, u in enumerate(lista, 1):
                res.append(uno(u))
                if i % 100 == 0:
                    print(f"    {urlparse(u).netloc}: {i}/{len(lista)}")
            return res
        for fut in [ex.submit(trabajar, l) for l in por_sitio.values()]:
            for u, h in fut.result():
                out[u] = h
    return out


def prensa() -> None:
    print("Prensa local:")
    parsers = guardar_robots()
    for f, rp in parsers.items():
        print(f"  robots {f}: puede leer artículos = {rp.can_fetch(USER_AGENT, 'https://' + SITIOS[f]['host'] + '/yucatan/x')}")
    cand = candidatos(parsers)
    cand = seleccionar(cand)
    meta = cand.drop(columns=["n_fuertes", "id_url"]).rename(columns={"fecha_url": "fecha_publicacion_url"})
    meta.to_csv(CLEAN_DIR / "prensa_local_candidatos_url.csv", index=False)
    sel = cand[cand["seleccionado"]]
    print(f"  candidatos por URL: {len(cand)} (secciones de Yucatán: {int(cand['seccion_relevante'].sum())}); "
          f"seleccionados: {len(sel)}")
    htmls = descargar_articulos(sel)
    pats = patrones_colonias()
    filas = []
    for _, c in sel.iterrows():
        h = htmls.get(c["url"])
        if not h:
            filas.append({"fuente": c["fuente"], "url": c["url"], "fecha_publicacion": c["fecha_url"],
                          "estado_descarga": "fallo"})
            continue
        e = extraer(h)
        texto = f"{e['titulo']} {e['cuerpo']}"
        claves = sorted(set(palabras_clave(texto)) | set(c["palabras_clave_url"].split(";")))
        cols = colonias_en(texto, pats)
        filas.append({
            "fuente": c["fuente"], "url": c["url"],
            "fecha_publicacion": e["fecha"] or c["fecha_url"],
            "titulo": e["titulo"], "seccion": c["seccion"],
            "palabras_clave_detectadas": ";".join(claves),
            "temas": ";".join(temas_resumidos(e["titulo"], "", e["cuerpo"][:3000], min_hits_texto=2)),
            "colonias_mencionadas": ";".join(n for n, _ in cols),
            "unidades_habitacionales": ";".join(u for _, u in cols),
            "n_palabras": len(e["cuerpo"].split()),
            "extracto": (e["cuerpo"][:197] + "...") if len(e["cuerpo"]) > 200 else e["cuerpo"],
            "estado_descarga": "ok" if len(e["cuerpo"]) > 100 else "sin_cuerpo",
        })
    art = pd.DataFrame(filas)
    art["anio"] = pd.to_numeric(art["fecha_publicacion"].str[:4], errors="coerce").astype("Int64")
    art = art[(art["anio"].isna()) | (art["anio"] >= ANIO_INICIO)]
    art = art.sort_values(["fecha_publicacion", "fuente"]).reset_index(drop=True)
    cols = ["fuente", "url", "fecha_publicacion", "anio", "titulo", "seccion", "palabras_clave_detectadas",
            "temas", "colonias_mencionadas", "unidades_habitacionales", "n_palabras", "extracto", "estado_descarga"]
    art = art[cols]
    art.to_csv(CLEAN_DIR / "prensa_local_articulos.csv", index=False)

    ok = art[art["estado_descarga"] == "ok"]
    men = ok.assign(par=[list(zip(a.split(";"), b.split(";"))) if a else [] for a, b in
                         zip(ok["colonias_mencionadas"].fillna(""), ok["unidades_habitacionales"].fillna(""))]).explode("par")
    men = men.dropna(subset=["par"])
    men["colonia"] = men["par"].str[0]
    men["unidad_habitacional"] = men["par"].str[1]
    mc = men.groupby(["colonia", "unidad_habitacional", "anio"]).agg(n_articulos=("url", "nunique")).reset_index()
    mc.sort_values(["colonia", "anio"]).to_csv(CLEAN_DIR / "prensa_local_menciones_colonia.csv", index=False)

    t = ok.assign(tema=ok["temas"].str.split(";")).explode("tema")
    ta = t.groupby(["anio", "fuente", "tema"]).agg(n_articulos=("url", "nunique")).reset_index()
    tot = ok.groupby(["anio", "fuente"]).agg(n_articulos_fuente_anio=("url", "nunique")).reset_index()
    ta = ta.merge(tot, on=["anio", "fuente"])
    ta["porcentaje"] = (100 * ta["n_articulos"] / ta["n_articulos_fuente_anio"]).round(2)
    ta.sort_values(["anio", "fuente", "tema"]).to_csv(CLEAN_DIR / "prensa_local_temas_anual.csv", index=False)

    print(f"  - prensa_local_candidatos_url.csv: {len(meta)} filas")
    print(f"  - prensa_local_articulos.csv: {len(art)} artículos "
          f"({(art['estado_descarga'] == 'ok').sum()} con cuerpo)")
    print("    por fuente: " + ", ".join(f"{k}={v}" for k, v in art["fuente"].value_counts().items()))
    print(f"  - prensa_local_menciones_colonia.csv: {len(mc)} filas")
    print(f"  - prensa_local_temas_anual.csv: {len(ta)} filas")


# ---------------------------------------------------------------------------
# Complemento A: YouTube Data API v3
# ---------------------------------------------------------------------------
YT_API = "https://www.googleapis.com/youtube/v3"
YT_CONSULTAS = ["moving to Merida", "living in Merida Mexico", "Merida Yucatan expat",
                "cost of living Merida Mexico", "mudarse a Mérida"]
YT_PALABRAS = {"precio": r"\bprecios?\b", "cheap": r"\bcheap(er|est)?\b", "safe": r"\bsafe(ty|st|r)?\b",
               "rent": r"\brent(s|ed|ing|al)?\b", "gentrification": r"gentrifica", "locals": r"\blocals?\b"}


def youtube() -> None:
    clave = os.environ.get("YOUTUBE_API_KEY", "").strip()
    YT_DIR.mkdir(parents=True, exist_ok=True)
    if not clave:
        print("YouTube: falta YOUTUBE_API_KEY; se salta (⚠️ en el README).")
        return

    def yt(recurso: str, params: dict, nombre: str) -> dict:
        destino = YT_DIR / f"{nombre}.json"
        if destino.exists():
            return json.loads(destino.read_text(encoding="utf-8"))
        r = http_get(f"{YT_API}/{recurso}", pausa=1.0, params={**params, "key": clave})
        d = r.json() if r is not None else {}
        if r is not None and r.status_code == 200:
            destino.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        else:
            print(f"  error YouTube {recurso}: {str(d)[:200]}")
        return d

    # Cuota: 5 consultas × 2 páginas × 100 unidades = 1,000; videos.list y commentThreads 1 c/u.
    videos: dict[str, dict] = {}
    for q in YT_CONSULTAS:
        token = None
        for pagina in range(2):
            p = {"part": "snippet", "q": q, "type": "video", "maxResults": 50, "order": "relevance"}
            if token:
                p["pageToken"] = token
            d = yt("search", p, f"search_{normalizar(q).replace(' ', '_')}_p{pagina}")
            for it in d.get("items", []):
                vid = it["id"]["videoId"]
                videos.setdefault(vid, {"consulta": q})
                if q not in videos[vid]["consulta"].split(";"):
                    videos[vid]["consulta"] += ";" + q
            token = d.get("nextPageToken")
            if not token:
                break
    ids = list(videos)
    filas = []
    for i in range(0, len(ids), 50):
        lote = ids[i:i + 50]
        d = yt("videos", {"part": "snippet,statistics", "id": ",".join(lote)}, f"videos_{i // 50:03d}")
        for it in d.get("items", []):
            sn, st = it["snippet"], it.get("statistics", {})
            filas.append({
                "video_id": it["id"], "titulo": sn.get("title", ""), "canal": sn.get("channelTitle", ""),
                "fecha_publicacion": sn.get("publishedAt", "")[:10],
                "vistas": int(st.get("viewCount", 0)), "likes": int(st["likeCount"]) if "likeCount" in st else None,
                "n_comentarios": int(st["commentCount"]) if "commentCount" in st else None,
                "idioma": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "",
                "consulta": videos[it["id"]]["consulta"],
            })
    vids = pd.DataFrame(filas).sort_values("vistas", ascending=False)
    vids["temas"] = [";".join(temas_resumidos(t)) for t in vids["titulo"]]
    vids.to_csv(CLEAN_DIR / "youtube_videos_merida.csv", index=False)

    # Comentarios: hasta 100 comentarios principales de los 150 videos más vistos; solo conteos.
    agregados = []
    for vid in vids[vids["n_comentarios"].fillna(0) > 0]["video_id"].head(150):
        d = yt("commentThreads", {"part": "snippet", "videoId": vid, "maxResults": 100, "order": "relevance",
                                  "textFormat": "plainText"}, f"comments_{vid}")
        textos = [normalizar(it["snippet"]["topLevelComment"]["snippet"].get("textDisplay", ""))
                  for it in d.get("items", [])]
        fila = {"video_id": vid, "n_comentarios_leidos": len(textos)}
        for k, rx in YT_PALABRAS.items():
            fila[f"n_menciona_{k}"] = sum(1 for t in textos if re.search(rx, t))
        agregados.append(fila)
    pd.DataFrame(agregados).to_csv(CLEAN_DIR / "youtube_comentarios_palabras_clave.csv", index=False)
    # Los JSON de comentarios traen autores y texto completo: se borran tras agregarlos.
    for p in YT_DIR.glob("comments_*.json"):
        p.unlink()
    print(f"YouTube: {len(vids)} videos; comentarios agregados de {len(agregados)} videos")


# ---------------------------------------------------------------------------
# Complemento B: vistas de Wikipedia
# ---------------------------------------------------------------------------
WIKI_ARTICULOS = [  # (ciudad, idioma, título buscado)
    ("Mérida", "en", "Mérida, Yucatán"), ("Mérida", "es", "Mérida (México)"),
    ("Oaxaca de Juárez", "en", "Oaxaca City"), ("Oaxaca de Juárez", "es", "Oaxaca de Juárez"),
    ("San Miguel de Allende", "en", "San Miguel de Allende"), ("San Miguel de Allende", "es", "San Miguel de Allende"),
    ("Playa del Carmen", "en", "Playa del Carmen"), ("Playa del Carmen", "es", "Playa del Carmen"),
]


def wikipedia() -> None:
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    filas = []
    resueltos = []
    for ciudad, lang, titulo in WIKI_ARTICULOS:
        r = http_get(f"https://{lang}.wikipedia.org/w/api.php", pausa=1.0,
                     params={"action": "query", "titles": titulo, "redirects": 1, "format": "json"})
        pag = next(iter(r.json()["query"]["pages"].values()))
        exacto = pag["title"]
        resueltos.append({"ciudad": ciudad, "idioma": lang, "titulo_buscado": titulo, "articulo": exacto,
                          "pageid": pag.get("pageid")})
        art = quote(exacto.replace(" ", "_"), safe="")
        fin = date.today().replace(day=1).strftime("%Y%m%d")
        url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lang}.wikipedia/"
               f"all-access/user/{art}/monthly/2016010100/{fin}00")
        destino = WIKI_DIR / f"pageviews_{lang}_{art[:60]}.json"
        if destino.exists():
            d = json.loads(destino.read_text(encoding="utf-8"))
        else:
            rr = http_get(url, pausa=1.0)
            d = rr.json() if rr is not None and rr.status_code == 200 else {"items": []}
            destino.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        for it in d.get("items", []):
            ts = it["timestamp"]
            filas.append({"mes": f"{ts[:4]}-{ts[4:6]}", "ciudad": ciudad, "idioma": lang, "articulo": exacto,
                          "vistas": int(it["views"])})
    pd.DataFrame(resueltos).to_csv(RAW_DIR / "wikipedia_titulos_resueltos.csv", index=False)
    df = pd.DataFrame(filas)
    df = df[df["mes"] < date.today().strftime("%Y-%m")]  # solo meses completos
    base = df[df["mes"].str.startswith("2019")].groupby(["ciudad", "idioma"])["vistas"].mean().rename("prom_2019")
    df = df.merge(base, on=["ciudad", "idioma"], how="left")
    df["indice_2019_100"] = (100 * df["vistas"] / df["prom_2019"]).round(1)
    df = df.drop(columns="prom_2019").sort_values(["ciudad", "idioma", "mes"])
    df.to_csv(CLEAN_DIR / "wikipedia_vistas_mensuales.csv", index=False)
    print(f"Wikipedia: {len(df)} filas ({df['mes'].min()} a {df['mes'].max()}), {df['articulo'].nunique()} artículos")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=["prensa", "youtube", "wikipedia"])
    args = ap.parse_args()
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(2026)
    if args.solo in (None, "wikipedia"):
        wikipedia()
    if args.solo in (None, "youtube"):
        youtube()
    if args.solo in (None, "prensa"):
        prensa()


if __name__ == "__main__":
    main()
