"""Construye las tablas "gold" del Dashboard v1 desde los clean/ de cada sección.

Lee solo archivos de `*/clean/` (más el Marco Geoestadístico crudo de la sección 4 para los
polígonos de manzana) y escribe en `dashboard/data/`. Uso:

    python dashboard/prep.py
"""
from __future__ import annotations

import io
import json
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import shapefile
import shapely
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"

S1 = ROOT / "1-INEGI-DENUE" / "clean"
S2 = ROOT / "2-Datos-Gob-Mx" / "clean"
S3 = ROOT / "3-SIEGY-Yucatan" / "clean"
S4 = ROOT / "4-GeoPortal-Merida" / "clean"
S5 = ROOT / "5-Government-Data-Request" / "clean"
S6 = ROOT / "6-Web-Scraping" / "clean"
S7 = ROOT / "7-Self-Produced" / "clean"
S8 = ROOT / "8-LiDAR" / "clean"
S9 = ROOT / "9-Augmented-Reality" / "clean"
MARCO_ZIP = ROOT / "4-GeoPortal-Merida" / "raw" / "inegi_marco_geo_31_yucatan.zip"

LAST_FULL_YEAR = 2025
BASE_YEAR = 2019


def read(path: Path, **kw) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", **kw)


def write(df: pd.DataFrame, name: str) -> pd.DataFrame:
    df.to_csv(DATA / name, index=False, encoding="utf-8")
    return df


def write_geojson(features: list[dict], name: str) -> None:
    fc = {"type": "FeatureCollection", "features": features}
    (DATA / name).write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def round_geom(geom, nd: int = 6):
    return shapely.transform(geom, lambda c: np.round(c, nd))


# ---------------------------------------------------------------------------
# 01 The arrival
# ---------------------------------------------------------------------------
def tourists() -> pd.DataFrame:
    t = read(S9 / "ar2_datatur_merida_turistas_anual_2015_2026.csv")
    out = pd.DataFrame({
        "year": t["anio"], "months": t["meses_reportados"],
        "national": t["turistas_nacionales"], "foreign": t["turistas_extranjeros"],
        "total": t["turistas_total"], "pct_foreign": t["pct_extranjeros"],
    })
    out["partial"] = out["months"] < 12
    return write(out, "tourists_annual.csv")


def tourists_monthly() -> pd.DataFrame:
    m = read(S2 / "datatur_merida_llegadas_categoria_mensual_2015_2026.csv")
    names = {"1 estrella": "1 star", "2 estrellas": "2 stars", "3 estrellas": "3 stars",
             "4 estrellas": "4 stars", "5 estrellas": "5 stars", "Total categorías": "All categories"}
    out = pd.DataFrame({
        "date": m["fecha"], "category": m["categoria_hotelera"].map(names),
        "national": m["turistas_nacionales"], "foreign": m["turistas_extranjeros"], "total": m["turistas_total"],
    })
    assert out["category"].notna().all(), "categoría hotelera sin traducción"
    return write(out, "tourists_monthly_category.csv")


def airports() -> tuple[pd.DataFrame, pd.DataFrame]:
    a = read(S9 / "ar3_asur_crecimiento_anual_mid_cun_oax.csv")
    a = a[a["anio"] >= 2015]
    annual = pd.DataFrame({
        "code": a["aeropuerto_codigo"], "airport": a["aeropuerto"], "year": a["anio"],
        "months": a["meses_reportados"], "total": a["pasajeros_total"],
        "international": a["pasajeros_internacional"],
        "pct_international": (100 * a["pasajeros_internacional"] / a["pasajeros_total"]).round(1),
        "index_2019": a["indice_2019_100"],
    })
    write(annual, "airports_annual.csv")
    m = read(S2 / "asur_pasajeros_mensual_mid_cun_oax.csv")
    m = m[m["anio"] >= BASE_YEAR]
    monthly = pd.DataFrame({"code": m["aeropuerto_codigo"], "date": m["fecha"], "total": m["pasajeros_total"],
                            "index_same_month_2019": m["indice_mismo_mes_2019_100"]})
    write(monthly, "airports_monthly.csv")
    return annual, monthly


# ---------------------------------------------------------------------------
# 02 The Centro empties out
# ---------------------------------------------------------------------------
CATEGORY_EN = {
    "Todos los establecimientos": "All businesses",
    "Abarrotes / tienda de la esquina (SCIAN 461110)": "Corner stores",
    "Cafeterías (SCIAN 722515)": "Coffee shops",
    "Hospedaje (SCIAN 721)": "Lodging",
    "Restaurantes y bares, sin cafeterías (SCIAN 722)": "Restaurants and bars",
}


def shops() -> pd.DataFrame:
    c = read(S1 / "denue_merida_conteos_categoria_2019_vs_2025.csv")
    out = pd.DataFrame({
        "area": c["geografia"].map(lambda g: "Centro" if g.startswith("Centro") else "Municipality"),
        "category": c["categoria"].map(CATEGORY_EN),
        "n_2019": c["establecimientos_2019"], "n_2025": c["establecimientos_2025"],
        "change": c["cambio_absoluto"], "pct_change": c["cambio_pct"],
    })
    assert out["category"].notna().all(), "categoría DENUE sin traducción"
    order = list(CATEGORY_EN.values())
    out["order"] = out["category"].map(order.index)
    return write(out.sort_values(["area", "order"]).drop(columns="order"), "shops_change.csv")


def cafe_map() -> pd.DataFrame:
    r = read(S1 / "denue_merida_resumen_ageb_2019_vs_2025.csv", dtype={"cvegeo": str})
    r["cafes_change"] = r["cafeterias_2025"] - r["cafeterias_2019"]
    summary = pd.DataFrame({"cvegeo": r["cvegeo"], "cafes_2019": r["cafeterias_2019"],
                            "cafes_2025": r["cafeterias_2025"], "cafes_change": r["cafes_change"],
                            "total_2019": r["total_establecimientos_2019"],
                            "total_2025": r["total_establecimientos_2025"]})
    write(summary, "ageb_cafes.csv")
    by_key = summary.set_index("cvegeo")
    g = json.loads((S4 / "inegi_agebs_merida.geojson").read_text(encoding="utf-8"))
    feats = []
    for f in g["features"]:
        key = f["properties"]["cvegeo"]
        row = by_key.loc[key] if key in by_key.index else None
        geom = round_geom(shape(f["geometry"]).simplify(0.00005, preserve_topology=True), 5)
        feats.append({"type": "Feature", "id": key, "geometry": mapping(geom), "properties": {
            "cvegeo": key,
            "cafes_2019": int(row["cafes_2019"]) if row is not None else 0,
            "cafes_2025": int(row["cafes_2025"]) if row is not None else 0,
            "cafes_change": int(row["cafes_change"]) if row is not None else 0,
        }})
    write_geojson(feats, "ageb_cafes.geojson")
    (DATA / "centro_historico.geojson").write_text(
        (S4 / "geoportal_centro_historico.geojson").read_text(encoding="utf-8"), encoding="utf-8")
    return summary


GIRO_EN = {"Alimentos y Bebidas": "Food and drink", "Comercio y otros servicios": "Commerce and services",
           "Hospedaje": "Lodging", "No especificado": "Not specified"}


def licenses() -> pd.DataFrame:
    l = read(S5 / "ayuntamiento_licencias_resumen_anual_centro_2015_2026.csv")
    out = pd.DataFrame({"year": l["anio"], "category": l["categoria_giro"].map(GIRO_EN),
                        "licenses": l["licencias_emitidas"]})
    assert out["category"].notna().all(), "giro sin traducción"
    return write(out, "licenses_centro.csv")


# ---------------------------------------------------------------------------
# 03 The invisible hotel
# ---------------------------------------------------------------------------
def tax_vs_tourists(tour: pd.DataFrame) -> pd.DataFrame:
    tax = read(S5 / "aafy_impuesto_hospedaje_anual_2015_2026.csv")
    df = tax[["anio", "recaudacion_total_mxn", "meses_reportados"]].rename(
        columns={"anio": "year", "recaudacion_total_mxn": "tax_nominal_mxn", "meses_reportados": "tax_months"})
    df = df.merge(tour[["year", "total"]].rename(columns={"total": "tourists"}), on="year")
    df = df[df["year"] <= LAST_FULL_YEAR].copy()
    base = df.set_index("year").loc[BASE_YEAR]
    df["tax_index"] = (100 * df["tax_nominal_mxn"] / base["tax_nominal_mxn"]).round(1)
    df["tourists_index"] = (100 * df["tourists"] / base["tourists"]).round(1)
    return write(df, "tax_vs_tourists.csv")


def blocks_3d() -> pd.DataFrame:
    h = read(S8 / "lidar_alturas_manzanas_centro.csv", dtype={"clave_manzana": str, "cvegeo": str})
    ar = read(S9 / "ar1_denue_resumen_manzanas_centro.csv", dtype={"clave_manzana": str})
    b = h.merge(ar[["clave_manzana", "negocios_2019", "negocios_2025", "cambio_neto"]], on="clave_manzana")
    b = b[["clave_manzana", "cvegeo", "en_centro_historico", "centroide_lat", "centroide_lon",
           "altura_p90_m", "altura_media_m", "negocios_2019", "negocios_2025", "cambio_neto"]]
    write(b, "blocks_3d.csv")

    keys = set(b["cvegeo"])
    with zipfile.ZipFile(MARCO_ZIP) as zf:
        prj = zf.read("conjunto_de_datos/31m.prj").decode("utf-8", errors="ignore")
        tr = pyproj.Transformer.from_crs(pyproj.CRS.from_wkt(prj), "EPSG:4326", always_xy=True)
        to_wgs = lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1]))  # noqa: E731
        shp = io.BytesIO(zf.read("conjunto_de_datos/31m.shp"))
        dbf = io.BytesIO(zf.read("conjunto_de_datos/31m.dbf"))
        shx = io.BytesIO(zf.read("conjunto_de_datos/31m.shx"))
        sf = shapefile.Reader(shp=shp, dbf=dbf, shx=shx, encoding="latin1")
        geoms = {}
        for sr in sf.iterShapeRecords():
            rec = sr.record
            if rec["CVE_MUN"] != "050" or rec["CVE_LOC"] != "0001" or rec["CVEGEO"] not in keys:
                continue
            g = shapely.transform(shape(sr.shape.__geo_interface__), to_wgs)
            geoms[rec["CVEGEO"]] = round_geom(g.simplify(0.000015, preserve_topology=True), 6)
    feats = []
    for _, r in b.iterrows():
        g = geoms.get(r["cvegeo"])
        if g is None:
            continue
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        poly = max(polys, key=lambda p: p.area)  # pydeck extruye anillos exteriores
        feats.append({"type": "Feature", "geometry": mapping(poly), "properties": {
            "clave_manzana": r["clave_manzana"], "height_p90_m": float(r["altura_p90_m"]),
            "businesses_2019": int(r["negocios_2019"]), "businesses_2025": int(r["negocios_2025"]),
            "net_change": int(r["cambio_neto"]), "in_centro": bool(r["en_centro_historico"]),
        }})
    write_geojson(feats, "blocks_3d.geojson")
    size_mb = (DATA / "blocks_3d.geojson").stat().st_size / 1e6
    assert size_mb < 10, f"blocks_3d.geojson pesa {size_mb:.1f} MB"
    print(f"  blocks_3d.geojson: {len(feats)} manzanas, {size_mb:.2f} MB")
    return b


def housing() -> tuple[pd.DataFrame, dict]:
    shf = read(S3 / "shf_precios_vivienda_trimestral_estados.csv")
    shf_q = shf[shf["trimestre"] == "2025T3"]
    homes = pd.DataFrame({"state": shf_q["entidad"], "quarter": shf_q["trimestre"], "median_mxn": shf_q["mediana_mxn"],
                          "vs_national_pct": shf_q["mediana_vs_nacional_pct"], "rank": shf_q["lugar_nacional"]})
    write(homes, "home_prices_2025T3.csv")
    enoe = read(S3 / "enoe_yucatan_2025T2_vs_2026T2.csv").set_index("indicador")
    low = enoe.loc["Ocupados: hasta 1 salario mínimo"]
    employed = enoe.loc["Población ocupada", "valor_2026T2"]
    censo = read(S1 / "censo_merida_yucatan_2010_2020.csv")
    empty = censo[censo["indicador"] == "% viviendas deshabitadas y de uso temporal"]["valor"].iloc[0]
    return homes, {"low_wage_workers": float(low["valor_2026T2"]), "employed": float(employed),
                   "low_wage_pct": float(low["pct_ocupados_2026T2"]), "empty_homes_pct_2020": float(empty)}


# ---------------------------------------------------------------------------
# 04 Who tells the story
# ---------------------------------------------------------------------------
HEADLINE_PICKS = ["especuladores invaden", "grupo inverco", "encarece rentas y desplaza",
                  "decima ciudad con mas alojamientos"]


def press() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    a = read(S6 / "prensa_local_articulos.csv")
    a["core"] = a["nucleo_tema"].astype(bool) & a["zona_metropolitana"].astype(bool)
    y = a.dropna(subset=["anio"]).astype({"anio": int})
    share = y.groupby("anio").agg(articles=("url", "size"), core=("core", "sum")).reset_index()
    share = share.rename(columns={"anio": "year"})
    share["pct_core"] = (100 * share["core"] / share["articles"]).round(1)
    share["partial"] = share["year"] > LAST_FULL_YEAR
    write(share, "press_share.csv")

    core = a[a["core"]].copy()
    norm = core["titulo"].fillna("").map(
        lambda s: "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower())
    picks = []
    for p in HEADLINE_PICKS:
        hit = core[norm.str.contains(p, regex=False)]
        if len(hit):
            picks.append(hit.iloc[0])
    heads = pd.DataFrame(picks)[["fecha_publicacion", "fuente", "titulo", "url"]]
    heads.columns = ["date", "outlet", "headline", "url"]
    heads["outlet"] = heads["outlet"].map({"diario_de_yucatan": "Diario de Yucatán", "por_esto": "Por Esto!",
                                           "la_jornada_maya": "La Jornada Maya"})
    write(heads, "press_headlines.csv")

    mc = read(S6 / "prensa_local_menciones_colonia.csv")
    top = mc.groupby("colonia", as_index=False)["n_articulos"].sum().nlargest(10, "n_articulos")
    top.columns = ["neighbourhood", "articles"]
    write(top, "press_top_neighbourhoods.csv")
    return share, heads, top


KEYWORDS = ["rent", "safe", "cheap", "locals", "precio", "gentrification"]


def youtube() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    v = read(S6 / "youtube_videos_merida.csv")
    k = read(S6 / "youtube_comentarios_palabras_clave.csv")
    kw = pd.DataFrame({"keyword": [w if w != "precio" else "price" for w in KEYWORDS],
                       "mentions": [int(k[f"n_menciona_{w}"].sum()) for w in KEYWORDS]})
    kw = kw.sort_values("mentions", ascending=False)
    write(kw, "youtube_keywords.csv")
    top = v.nlargest(5, "vistas")[["titulo", "canal", "fecha_publicacion", "vistas", "idioma"]]
    top.columns = ["title", "channel", "published", "views", "language"]
    write(top, "youtube_top_videos.csv")
    stats = {"videos": int(v["video_id"].nunique()), "views": int(v["vistas"].sum()),
             "comments_read": int(k["n_comentarios_leidos"].sum()),
             "pct_english": round(100 * v["idioma"].fillna("").str.startswith("en").mean(), 1)}
    return kw, top, stats


def gdelt() -> pd.DataFrame:
    g = read(S7 / "gdelt_merida_articulos.csv")
    out = g["voz"].value_counts().rename_axis("voice").reset_index(name="articles")
    out["voice"] = out["voice"].map({"local": "Local", "nacional": "National", "internacional": "International"})
    out["pct"] = (100 * out["articles"] / out["articles"].sum()).round(1)
    out["first_date"] = g["fecha"].min()
    out["last_date"] = g["fecha"].max()
    return write(out, "gdelt_voices.csv")


# ---------------------------------------------------------------------------
# 05 Not Cancún, not yet
# ---------------------------------------------------------------------------
def wikipedia() -> pd.DataFrame:
    w = read(S6 / "wikipedia_vistas_mensuales.csv")
    w["year"] = w["mes"].str[:4].astype(int)
    y = w.groupby(["ciudad", "year"])["vistas"].sum().unstack()
    out = pd.DataFrame({"city": y.index, "views_2019": y[BASE_YEAR].values, "views_2025": y[LAST_FULL_YEAR].values})
    out["index_2025"] = (100 * out["views_2025"] / out["views_2019"]).round(1)
    out["city"] = out["city"].replace({"Oaxaca de Juárez": "Oaxaca"})
    return write(out.sort_values("index_2025", ascending=False), "wikipedia_index.csv")


# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------
def kpis(tour, air, sh, tax, homes, hous, share, yt, cafes) -> pd.DataFrame:
    t = tour.set_index("year")
    shop = sh.set_index(["area", "category"])
    centro = shop.loc[("Centro", "All businesses")]
    taxi = tax.set_index("year")
    yuc = homes.set_index("state").loc["Yucatán"]
    mid = air.set_index(["code", "year"]).loc[("MID", LAST_FULL_YEAR)]
    rows = [
        ("tourists_2019", t.loc[BASE_YEAR, "total"]),
        ("tourists_2025", t.loc[LAST_FULL_YEAR, "total"]),
        ("tourists_change_pct", 100 * (t.loc[LAST_FULL_YEAR, "total"] / t.loc[BASE_YEAR, "total"] - 1)),
        ("pct_foreign_2025", t.loc[LAST_FULL_YEAR, "pct_foreign"]),
        ("mid_passengers_2025", mid["total"]),
        ("mid_index_2025", mid["index_2019"]),
        ("centro_businesses_2019", centro["n_2019"]),
        ("centro_businesses_2025", centro["n_2025"]),
        ("centro_businesses_change_pct", centro["pct_change"]),
        ("ageb_gained_cafes", int((cafes["cafes_change"] > 0).sum())),
        ("tax_2019", taxi.loc[BASE_YEAR, "tax_nominal_mxn"]),
        ("tax_2025", taxi.loc[LAST_FULL_YEAR, "tax_nominal_mxn"]),
        ("tax_ratio", taxi.loc[LAST_FULL_YEAR, "tax_nominal_mxn"] / taxi.loc[BASE_YEAR, "tax_nominal_mxn"]),
        ("tourists_index_2025", taxi.loc[LAST_FULL_YEAR, "tourists_index"]),
        ("tax_index_2025", taxi.loc[LAST_FULL_YEAR, "tax_index"]),
        ("shf_yucatan_vs_national_pct", yuc["vs_national_pct"]),
        ("shf_yucatan_rank", yuc["rank"]),
        ("low_wage_workers", hous["low_wage_workers"]),
        ("employed", hous["employed"]),
        ("low_wage_pct", hous["low_wage_pct"]),
        ("empty_homes_pct_2020", hous["empty_homes_pct_2020"]),
        ("press_core_articles", share["core"].sum()),
        ("yt_videos", yt["videos"]), ("yt_views", yt["views"]), ("yt_comments_read", yt["comments_read"]),
        ("yt_pct_english", yt["pct_english"]),
    ]
    return write(pd.DataFrame(rows, columns=["key", "value"]), "kpis.csv")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    print("Construyendo tablas gold en dashboard/data/ ...")
    tour = tourists()
    tourists_monthly()
    air, _ = airports()
    sh = shops()
    cafes = cafe_map()
    licenses()
    tax = tax_vs_tourists(tour)
    blocks_3d()
    homes, hous = housing()
    share, _, _ = press()
    _, _, yt = youtube()
    gdelt()
    wikipedia()
    kpis(tour, air, sh, tax, homes, hous, share, yt, cafes)
    for p in sorted(DATA.iterdir()):
        print(f"  - {p.name} ({p.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
