"""
Limpieza de la sección 7-Self-Produced (Principal: noticias sobre Mérida con GDELT).

Fuentes cubiertas:
- Stream propio GDELT GKG 2.1 (grabado por `gdelt_stream_recorder.py` en `raw/gdelt_stream/`).
- Respaldo histórico GDELT DOC 2.0 API (`https://api.gdeltproject.org/api/v2/doc/doc`),
  últimos ~3 meses, consulta `("Mérida" OR "Merida") (Yucatán OR Yucatan)`:
  * `mode=timelinetone` y `mode=timelinevolraw` (serie diaria), total y por voz.
  * `mode=artlist` con `maxrecords=250` en ventanas semanales (si una semana llega a 250, se
    parte en días).
  Todas las respuestas se guardan en `raw/gdelt_doc/` (caché); una segunda corrida no repite
  peticiones. `--refrescar` borra el manifiesto de ventanas y vuelve a pedir todo.

Salidas en `clean/`:
- gdelt_merida_articulos.csv               (un artículo por fila, deduplicado por URL)
- gdelt_merida_tono_semanal_por_voz.csv    (semana ISO, voz, n_articulos, tono_promedio)
- gdelt_merida_temas_por_voz.csv           (voz, tema, n, porcentaje)
- gdelt_merida_timeline_diaria_por_voz.csv (serie diaria de la DOC API: volumen y tono)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
STREAM_DIR = RAW_DIR / "gdelt_stream"
DOC_DIR = RAW_DIR / "gdelt_doc"
CLEAN_DIR = BASE_DIR / "clean"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from clasificacion import DOMINIOS_LOCALES, limpiar_dominio, temas_resumidos, voz  # noqa: E402

DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
USER_AGENT = "MeridaForSale-UPY/1.0 (+https://github.com/BradRobles/M-rida-for-Sale)"
CONSULTA = '("Mérida" OR "Merida") (Yucatán OR Yucatan)'
PAUSA_S = 15.0  # la API pide máximo 1 petición cada 5 s; en la práctica devuelve 429 por debajo de ~15 s
_ultima = 0.0
SESSION = requests.Session()
SESSION.headers["User-Agent"] = USER_AGENT

# Filtros por voz para las series de la DOC API. Con más de ~3 dominios el servidor corta la
# conexión, así que "local" en las series usa solo los tres diarios principales de Yucatán
# (en la tabla de artículos la voz sí usa la lista completa de `clasificacion.py`).
_LOCALES_DOC = DOMINIOS_LOCALES[:3]
FILTRO_VOZ = {
    "todas": "",
    "local": "(" + " OR ".join(f"domainis:{d}" for d in _LOCALES_DOC) + ")",
    "nacional": "sourcecountry:mexico " + " ".join(f"-domainis:{d}" for d in _LOCALES_DOC),
    "internacional": "-sourcecountry:mexico",
}


def doc_get(params: dict, nombre: str) -> dict | None:
    """Petición a la DOC API con caché en disco, pausa y reintentos ante 429."""
    global _ultima
    destino = DOC_DIR / f"{nombre}.json"
    if destino.exists():
        return json.loads(destino.read_text(encoding="utf-8"))
    for intento in range(10):
        espera = PAUSA_S - (time.time() - _ultima)
        if espera > 0:
            time.sleep(espera)
        _ultima = time.time()
        try:
            r = SESSION.get(DOC_API, params={**params, "format": "json"}, timeout=90)
        except requests.RequestException as e:
            print(f"    error de red ({e}); reintento")
            time.sleep(min(60, 20 * (intento + 1)))
            if intento >= 4:
                break
            continue
        if r.status_code == 429 or "limit requests" in r.text[:200]:
            time.sleep(min(60, 15 * (intento + 1)))
            continue
        texto = r.content.decode("utf-8", errors="replace").strip()
        try:
            datos = json.loads(texto) if texto else {}
        except json.JSONDecodeError:
            print(f"    respuesta no JSON en {nombre}: {texto[:120]!r}")
            datos = {"_error": texto[:500]}
        datos["_params"] = params
        destino.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        return datos
    print(f"    sin respuesta tras reintentos: {nombre}")
    return None


def ventanas(refrescar: bool) -> dict:
    """Ventanas semanales fijas (lunes a lunes) de los últimos ~3 meses, guardadas en manifiesto."""
    manifiesto = DOC_DIR / "_ventanas.json"
    if manifiesto.exists() and not refrescar:
        return json.loads(manifiesto.read_text(encoding="utf-8"))
    hoy = date.today()
    fin = hoy  # la última semana va hasta hoy
    lunes = hoy - timedelta(days=hoy.weekday())
    inicio = lunes - timedelta(weeks=12)
    semanas = []
    d = inicio
    while d < fin:
        f = min(d + timedelta(days=7), fin)
        semanas.append([d.isoformat(), f.isoformat()])
        d = f
    m = {"generado": hoy.isoformat(), "consulta": CONSULTA, "semanas": semanas}
    manifiesto.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return m


def fmt(d: str) -> str:
    return d.replace("-", "") + "000000"


def descargar_doc(refrescar: bool) -> tuple[list[dict], list[dict]]:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    if refrescar:
        for p in DOC_DIR.glob("*.json"):
            p.unlink()
    m = ventanas(refrescar)
    ini, fin = m["semanas"][0][0], m["semanas"][-1][1]

    # 1) Series diarias por voz
    series = []
    for v, filtro in FILTRO_VOZ.items():
        q = f"{CONSULTA} {filtro}".strip()
        for modo in ("timelinetone", "timelinevolraw"):
            datos = doc_get({"query": q, "mode": modo, "startdatetime": fmt(ini),
                             "enddatetime": fmt(fin), "timelinesmooth": 0}, f"{modo}_{v}")
            for serie in (datos or {}).get("timeline", []):
                for p in serie.get("data", []):
                    series.append({"voz": v, "modo": modo, "serie": serie.get("series", ""),
                                   "fecha": p["date"][:8], "valor": p.get("value"),
                                   "norm": p.get("norm")})

    # 2) Artículos por semana (y por día si la semana se satura)
    articulos = []
    for a, b in m["semanas"]:
        nombre = f"artlist_{a}_{b}"
        print(f"  artlist {a} → {b}")
        datos = doc_get({"query": CONSULTA, "mode": "artlist", "maxrecords": 250, "sort": "datedesc",
                         "startdatetime": fmt(a), "enddatetime": fmt(b)}, nombre)
        arts = (datos or {}).get("articles", [])
        if len(arts) >= 250:
            arts = []
            d = date.fromisoformat(a)
            while d < date.fromisoformat(b):
                e = d + timedelta(days=1)
                dd = doc_get({"query": CONSULTA, "mode": "artlist", "maxrecords": 250, "sort": "datedesc",
                              "startdatetime": fmt(d.isoformat()), "enddatetime": fmt(e.isoformat())},
                             f"artlist_dia_{d.isoformat()}")
                arts += (dd or {}).get("articles", [])
                d = e
        articulos += arts
    return articulos, series


def leer_stream() -> pd.DataFrame:
    archivos = sorted(STREAM_DIR.glob("gkg_merida_*.csv"))
    if not archivos:
        return pd.DataFrame()
    df = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False) for p in archivos], ignore_index=True)
    return df


def construir_articulos(arts_doc: list[dict], stream: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for a in arts_doc:
        filas.append({
            "url": a.get("url", ""),
            "fecha_hora_utc": datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dominio": limpiar_dominio(a.get("domain")),
            "titulo": " ".join((a.get("title") or "").split()),
            "idioma": (a.get("language") or "").lower(),
            "pais_fuente": a.get("sourcecountry") or "",
            "tono": None, "positivo": None, "negativo": None, "temas_gkg": "",
            "fuente_datos": "doc_api",
        })
    for _, s in stream.iterrows():
        filas.append({
            "url": s["url"], "fecha_hora_utc": s["fecha_hora_utc"],
            "dominio": limpiar_dominio(s["dominio"]), "titulo": s.get("titulo", ""),
            "idioma": "english" if s["idioma_origen"] == "eng" else s["idioma_origen"],
            "pais_fuente": "",
            "tono": pd.to_numeric(s["tono"], errors="coerce"),
            "positivo": pd.to_numeric(s["positivo"], errors="coerce"),
            "negativo": pd.to_numeric(s["negativo"], errors="coerce"),
            "temas_gkg": s["temas"], "fuente_datos": "stream_gkg",
        })
    df = pd.DataFrame(filas)
    if df.empty:
        return df
    df = df[df["url"].str.startswith("http")].copy()
    df["url_norm"] = df["url"].str.replace(r"^https?://(www\.)?", "", regex=True).str.rstrip("/")
    # Combinar duplicados: el stream aporta tono y temas; la DOC API aporta país e idioma.
    df["_prioridad"] = (df["fuente_datos"] == "stream_gkg").astype(int)
    df = df.sort_values(["url_norm", "_prioridad"], ascending=[True, False])
    agg = df.groupby("url_norm", as_index=False).agg(
        url=("url", "first"), fecha_hora_utc=("fecha_hora_utc", "min"), dominio=("dominio", "first"),
        titulo=("titulo", lambda x: next((t for t in x if t), "")),
        idioma=("idioma", lambda x: next((t for t in x if t), "")),
        pais_fuente=("pais_fuente", lambda x: next((t for t in x if t), "")),
        tono=("tono", "first"), positivo=("positivo", "first"), negativo=("negativo", "first"),
        temas_gkg=("temas_gkg", "first"),
        fuente_datos=("fuente_datos", lambda x: "+".join(sorted(set(x)))),
    )
    agg["fecha"] = agg["fecha_hora_utc"].str[:10]
    iso = pd.to_datetime(agg["fecha"]).dt.isocalendar()
    agg["semana_iso"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
    agg["voz"] = [voz(d, p) for d, p in zip(agg["dominio"], agg["pais_fuente"])]
    agg["temas"] = [";".join(temas_resumidos(t, g)) for t, g in zip(agg["titulo"], agg["temas_gkg"])]
    for c in ("tono", "positivo", "negativo"):
        agg[c] = pd.to_numeric(agg[c], errors="coerce").round(3)
    cols = ["fecha", "fecha_hora_utc", "semana_iso", "voz", "dominio", "pais_fuente", "idioma",
            "titulo", "url", "temas", "tono", "positivo", "negativo", "fuente_datos"]
    return agg[cols].sort_values(["fecha_hora_utc", "dominio"]).reset_index(drop=True)


def tono_semanal(art: pd.DataFrame, series: list[dict]) -> pd.DataFrame:
    """n_articulos de la tabla de artículos; tono del stream si hay, si no de la DOC API."""
    base = art.groupby(["semana_iso", "voz"]).agg(
        n_articulos=("url", "size"),
        n_con_tono=("tono", "count"),
        tono_stream=("tono", "mean"),
    ).reset_index()
    s = pd.DataFrame(series)
    if not s.empty:
        s["fecha"] = pd.to_datetime(s["fecha"], format="%Y%m%d")
        iso = s["fecha"].dt.isocalendar()
        s["semana_iso"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
        tono = s[s["modo"] == "timelinetone"][["voz", "fecha", "semana_iso", "valor"]].rename(columns={"valor": "tono"})
        vol = s[(s["modo"] == "timelinevolraw")][["voz", "fecha", "valor"]].rename(columns={"valor": "vol"})
        tv = tono.merge(vol, on=["voz", "fecha"], how="left")
        tv = tv[tv["vol"].fillna(0) > 0]
        tv["tv"] = tv["tono"] * tv["vol"]
        doc = tv.groupby(["semana_iso", "voz"]).agg(tv=("tv", "sum"), vol=("vol", "sum")).reset_index()
        doc["tono_doc_api"] = doc["tv"] / doc["vol"]
        doc = doc.rename(columns={"vol": "n_articulos_doc_api"})[["semana_iso", "voz", "tono_doc_api", "n_articulos_doc_api"]]
        base = base.merge(doc[doc["voz"] != "todas"], on=["semana_iso", "voz"], how="outer")
    else:
        base["tono_doc_api"] = None
        base["n_articulos_doc_api"] = None
    base["n_articulos"] = base["n_articulos"].fillna(0).astype(int)
    base["n_con_tono"] = base["n_con_tono"].fillna(0).astype(int)
    usar_stream = base["n_con_tono"] >= 3
    base["tono_promedio"] = base["tono_doc_api"].where(~usar_stream, base["tono_stream"])
    base["fuente_tono"] = "doc_api_timelinetone"
    base.loc[usar_stream, "fuente_tono"] = "stream_gkg"
    base.loc[base["tono_promedio"].isna(), "fuente_tono"] = ""
    for c in ("tono_promedio", "tono_stream", "tono_doc_api"):
        base[c] = pd.to_numeric(base[c], errors="coerce").round(3)
    base["n_articulos_doc_api"] = pd.to_numeric(base["n_articulos_doc_api"], errors="coerce").astype("Int64")
    cols = ["semana_iso", "voz", "n_articulos", "tono_promedio", "fuente_tono", "n_con_tono",
            "tono_stream", "tono_doc_api", "n_articulos_doc_api"]
    return base[cols].sort_values(["semana_iso", "voz"]).reset_index(drop=True)


def temas_por_voz(art: pd.DataFrame) -> pd.DataFrame:
    e = art.assign(tema=art["temas"].str.split(";")).explode("tema")
    t = e.groupby(["voz", "tema"]).size().rename("n").reset_index()
    tot = art.groupby("voz").size().rename("n_articulos_voz")
    t = t.merge(tot, on="voz")
    t["porcentaje"] = (100 * t["n"] / t["n_articulos_voz"]).round(2)
    return t.sort_values(["voz", "n"], ascending=[True, False]).reset_index(drop=True)


def timeline_diaria(series: list[dict]) -> pd.DataFrame:
    s = pd.DataFrame(series)
    if s.empty:
        return s
    p = s.pivot_table(index=["fecha", "voz"], columns="modo", values="valor", aggfunc="first").reset_index()
    p["fecha"] = pd.to_datetime(p["fecha"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
    p = p.rename(columns={"timelinevolraw": "n_articulos", "timelinetone": "tono_promedio"})
    p.columns.name = None
    p["tono_promedio"] = pd.to_numeric(p.get("tono_promedio"), errors="coerce").round(3)
    return p[["fecha", "voz", "n_articulos", "tono_promedio"]].sort_values(["fecha", "voz"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refrescar", action="store_true", help="vuelve a pedir todo a la DOC API")
    args = ap.parse_args()
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    print("Descargando / leyendo caché de la DOC API…")
    arts_doc, series = descargar_doc(args.refrescar)
    stream = leer_stream()
    art = construir_articulos(arts_doc, stream)
    art.to_csv(CLEAN_DIR / "gdelt_merida_articulos.csv", index=False)
    ts = tono_semanal(art, series)
    ts.to_csv(CLEAN_DIR / "gdelt_merida_tono_semanal_por_voz.csv", index=False)
    tv = temas_por_voz(art)
    tv.to_csv(CLEAN_DIR / "gdelt_merida_temas_por_voz.csv", index=False)
    td = timeline_diaria(series)
    td.to_csv(CLEAN_DIR / "gdelt_merida_timeline_diaria_por_voz.csv", index=False)

    print("Limpieza Sección 7 (GDELT) completada:")
    print(f"  - artículos DOC API: {len(arts_doc)}; filas del stream: {len(stream)}")
    print(f"  - gdelt_merida_articulos.csv: {len(art)} artículos únicos")
    print("    por voz: " + ", ".join(f"{k}={v}" for k, v in art['voz'].value_counts().items()))
    print(f"  - gdelt_merida_tono_semanal_por_voz.csv: {len(ts)} filas")
    print(f"  - gdelt_merida_temas_por_voz.csv: {len(tv)} filas")
    print(f"  - gdelt_merida_timeline_diaria_por_voz.csv: {len(td)} filas")


if __name__ == "__main__":
    main()
