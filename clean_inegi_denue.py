"""
Limpieza y estandarización de datos para la sección 1-INEGI-DENUE.

Fuentes:
- Principal: INEGI DENUE, ediciones noviembre 2019 y mayo 2025 (Yucatán, 31).
  Compara hospedaje (SCIAN 721), restaurantes y bares (722) y tiendas de
  abarrotes (461110) en el municipio de Mérida y dentro del polígono oficial
  del Centro Histórico (Zona de Monumentos Históricos, GeoPortal de Mérida).
- Complemento A: INEGI Censo de Población y Vivienda 2010 y 2020 (cifras
  publicadas para Mérida y Yucatán).

Los ZIP del DENUE no se duplican: se leen de `1-INEGI-DENUE/raw/` y, si no
están ahí, de `9-Augmented-Reality/raw/`. El polígono del Centro se lee de
`4-GeoPortal-Merida/clean/geoportal_centro_historico.geojson`.

Este script únicamente extrae, limpia y exporta tablas CSV; no genera gráficos.
"""

from pathlib import Path
import json
import zipfile
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent
RAW_DIR = BASE_DIR / "raw"
CLEAN_DIR = BASE_DIR / "clean"
RAW_FALLBACK = REPO_DIR / "9-Augmented-Reality" / "raw"
CENTRO_GEOJSON = REPO_DIR / "4-GeoPortal-Merida" / "clean" / "geoportal_centro_historico.geojson"

EDICIONES = {2019: "denue_31_1119_csv.zip", 2025: "denue_31_0525_csv.zip"}

USECOLS = [
    "id", "nom_estab", "codigo_act", "nombre_act", "per_ocu", "nomb_asent",
    "cve_ent", "cve_mun", "cve_loc", "ageb", "manzana", "latitud", "longitud", "fecha_alta",
]


def categoria(codigo: str) -> str | None:
    """Categorías del checklist (sección 1). None = fuera del análisis."""
    if codigo.startswith("721"):
        return "Hospedaje (SCIAN 721)"
    if codigo == "722515":
        return "Cafeterías (SCIAN 722515)"
    if codigo.startswith("722"):
        return "Restaurantes y bares, sin cafeterías (SCIAN 722)"
    if codigo == "461110":
        return "Abarrotes / tienda de la esquina (SCIAN 461110)"
    return None


def raw_path(nombre: str) -> Path:
    for d in (RAW_DIR, RAW_FALLBACK):
        if (d / nombre).exists():
            return d / nombre
    raise FileNotFoundError(f"No se encontró {nombre} en {RAW_DIR} ni en {RAW_FALLBACK}")


def load_centro_polygon() -> list[list[tuple[float, float]]]:
    """Anillos (exterior y huecos) del polígono del Centro Histórico, en (lon, lat)."""
    gj = json.loads(CENTRO_GEOJSON.read_text(encoding="utf-8"))
    geom = gj["features"][0]["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [[tuple(p[:2]) for p in ring] for poly in polys for ring in poly]


def dentro(lon: float, lat: float, anillos) -> bool:
    """Ray casting con regla par-impar: los huecos quedan excluidos."""
    inside = False
    for ring in anillos:
        n = len(ring)
        j = n - 1
        for i in range(n):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
    return inside


def load_denue(anio: int, anillos) -> pd.DataFrame:
    with zipfile.ZipFile(raw_path(EDICIONES[anio])) as zf:
        with zf.open("conjunto_de_datos/denue_inegi_31_.csv") as f:
            df = pd.read_csv(f, usecols=USECOLS, dtype=str, encoding="latin1", low_memory=False)
    df = df.apply(lambda s: s.str.strip())
    df = df[df["cve_mun"].str.zfill(3) == "050"].copy()
    total_municipio = df["id"].nunique()
    df = df.drop_duplicates(subset="id")
    df["codigo_act"] = df["codigo_act"].str.zfill(6)
    df["categoria"] = df["codigo_act"].map(categoria)
    df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
    df["cvegeo_ageb"] = (
        "31050" + df["cve_loc"].str.zfill(4) + df["ageb"].str.replace(r"\.0$", "", regex=True).str.zfill(4)
    )
    df["en_centro_historico"] = [
        bool(pd.notna(lo) and pd.notna(la) and dentro(lo, la, anillos))
        for lo, la in zip(df["longitud"], df["latitud"])
    ]
    df["edicion"] = anio
    df.attrs["total_municipio"] = total_municipio
    return df


def build_denue():
    anillos = load_centro_polygon()
    d = {a: load_denue(a, anillos) for a in EDICIONES}

    # 1) Conteos por categoría, municipio y Centro Histórico
    filas = []
    for geo, filtro in [("Mérida (municipio)", None), ("Centro Histórico (Zona de Monumentos)", "en_centro_historico")]:
        for anio, df in d.items():
            sub = df if filtro is None else df[df[filtro]]
            filas.append({"geografia": geo, "categoria": "Todos los establecimientos", "edicion": anio, "establecimientos": len(sub)})
            for cat, n in sub["categoria"].value_counts().items():
                filas.append({"geografia": geo, "categoria": cat, "edicion": anio, "establecimientos": int(n)})
    conteos = pd.DataFrame(filas).pivot_table(index=["geografia", "categoria"], columns="edicion",
                                               values="establecimientos", fill_value=0).reset_index()
    conteos.columns = ["geografia", "categoria", "establecimientos_2019", "establecimientos_2025"]
    conteos[["establecimientos_2019", "establecimientos_2025"]] = conteos[["establecimientos_2019", "establecimientos_2025"]].astype(int)
    conteos["cambio_absoluto"] = conteos["establecimientos_2025"] - conteos["establecimientos_2019"]
    conteos["cambio_pct"] = (100 * conteos["cambio_absoluto"] / conteos["establecimientos_2019"]).round(1)

    # 2) Detalle por clase SCIAN dentro de las categorías
    clave = pd.concat([df[df["categoria"].notna()] for df in d.values()], ignore_index=True)
    nombres = clave.sort_values("edicion").groupby("codigo_act")["nombre_act"].last()
    scian = (clave.groupby(["codigo_act", "categoria", "edicion"]).size().unstack("edicion", fill_value=0)
             .reset_index().rename(columns={2019: "establecimientos_2019", 2025: "establecimientos_2025"}))
    scian.insert(1, "nombre_act", scian["codigo_act"].map(nombres))
    scian["cambio_absoluto"] = scian["establecimientos_2025"] - scian["establecimientos_2019"]
    scian = scian.sort_values(["categoria", "establecimientos_2025"], ascending=[True, False])

    # 3) Establecimientos de las categorías clave, con su estado 2019 → 2025
    ids19, ids25 = set(d[2019]["id"]), set(d[2025]["id"])
    reg = pd.concat([d[2025][d[2025]["categoria"].notna()],
                     d[2019][d[2019]["categoria"].notna() & ~d[2019]["id"].isin(ids25)]], ignore_index=True)
    reg["en_2019"] = reg["id"].isin(ids19)
    reg["en_2025"] = reg["id"].isin(ids25)
    reg["estado_cambio"] = reg.apply(lambda r: "Existia en 2019" if r["en_2019"] and r["en_2025"]
                                     else ("Abrio despues de 2019" if r["en_2025"] else "Cerro despues de 2019"), axis=1)
    reg = reg[["id", "nom_estab", "codigo_act", "nombre_act", "categoria", "per_ocu", "nomb_asent",
               "cvegeo_ageb", "manzana", "latitud", "longitud", "en_centro_historico", "fecha_alta",
               "en_2019", "en_2025", "estado_cambio"]].rename(columns={"nomb_asent": "colonia"})
    reg = reg.sort_values(["categoria", "cvegeo_ageb", "nom_estab"]).reset_index(drop=True)

    # 4) Resumen por AGEB (llave cvegeo, compatible con 4-GeoPortal-Merida/clean/inegi_agebs_merida_catalogo.csv)
    abrev = {
        "Hospedaje (SCIAN 721)": "hospedaje",
        "Cafeterías (SCIAN 722515)": "cafeterias",
        "Restaurantes y bares, sin cafeterías (SCIAN 722)": "restaurantes_bares",
        "Abarrotes / tienda de la esquina (SCIAN 461110)": "abarrotes",
    }
    piv = []
    for anio, df in d.items():
        p = pd.crosstab(df["cvegeo_ageb"], df["categoria"].map(abrev).fillna("otros"))
        p = p.reindex(columns=list(abrev.values()), fill_value=0)
        p.columns = [f"{c}_{anio}" for c in p.columns]
        p[f"total_establecimientos_{anio}"] = df.groupby("cvegeo_ageb").size()
        piv.append(p)
    ageb = pd.concat(piv, axis=1).fillna(0).astype(int).reset_index().rename(columns={"index": "cvegeo", "cvegeo_ageb": "cvegeo"})
    ageb = ageb[["cvegeo"] + sorted([c for c in ageb.columns if c != "cvegeo"], key=lambda c: (c[-4:], c))]
    centro = pd.concat([df[["cvegeo_ageb", "en_centro_historico"]] for df in d.values()]).groupby("cvegeo_ageb")["en_centro_historico"].mean()
    ageb["pct_establecimientos_en_centro_historico"] = ageb["cvegeo"].map((100 * centro).round(1))
    ageb = ageb[ageb["cvegeo"].str.len() == 13].sort_values("cvegeo")

    # Validaciones
    for anio, df in d.items():
        assert df["id"].is_unique
        assert int(conteos.query("geografia == 'Mérida (municipio)' and categoria == 'Todos los establecimientos'")[f"establecimientos_{anio}"].iloc[0]) == len(df)
        assert ageb[f"total_establecimientos_{anio}"].sum() <= len(df)  # sin AGEB válida quedan fuera
    return conteos, scian, reg, ageb


def build_censo() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "inegi_censo_cifras_publicadas.csv", dtype={"cve_geo": str})
    yuc = df[df["geografia"] == "Yucatán (estado)"].set_index("indicador")["valor"]
    assert yuc["Viviendas habitadas"] + yuc["Viviendas deshabitadas y de uso temporal"] == yuc["Viviendas visitadas en el levantamiento"]
    extra = pd.DataFrame([
        {"geografia": "Yucatán (estado)", "cve_geo": "31", "indicador": "% viviendas deshabitadas y de uso temporal", "anio": 2020,
         "valor": round(100 * yuc["Viviendas deshabitadas y de uso temporal"] / yuc["Viviendas visitadas en el levantamiento"], 1),
         "unidad": "%", "fuente": "Calculado con las dos filas anteriores", "url": df["url"].iloc[-1]},
    ])
    mer = df[(df["cve_geo"] == "31050") & (df["indicador"] == "Población total")].set_index("anio")["valor"]
    extra = pd.concat([extra, pd.DataFrame([{
        "geografia": "Mérida (municipio)", "cve_geo": "31050", "indicador": "Crecimiento de población 2010-2020", "anio": 2020,
        "valor": round(100 * (mer[2020] / mer[2010] - 1), 1), "unidad": "%", "fuente": "Calculado con las filas de población", "url": ""}])])
    out = pd.concat([df, extra], ignore_index=True).sort_values(["geografia", "indicador", "anio"])
    out["valor"] = out["valor"].map(lambda v: str(int(v)) if float(v).is_integer() else str(v))
    return out


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    conteos, scian, reg, ageb = build_denue()
    conteos.to_csv(CLEAN_DIR / "denue_merida_conteos_categoria_2019_vs_2025.csv", index=False)
    scian.to_csv(CLEAN_DIR / "denue_merida_conteos_scian_2019_vs_2025.csv", index=False)
    reg.to_csv(CLEAN_DIR / "denue_merida_establecimientos_clave_2019_vs_2025.csv", index=False)
    ageb.to_csv(CLEAN_DIR / "denue_merida_resumen_ageb_2019_vs_2025.csv", index=False)
    build_censo().to_csv(CLEAN_DIR / "censo_merida_yucatan_2010_2020.csv", index=False)
    print(conteos.to_string(index=False))
    print(f"\nRegistros clave: {len(reg):,} | AGEB con establecimientos: {len(ageb):,}")


if __name__ == "__main__":
    main()
