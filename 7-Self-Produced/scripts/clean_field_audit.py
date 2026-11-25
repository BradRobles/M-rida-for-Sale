"""
Limpieza del trabajo de campo de la sección 7-Self-Produced.

Fuentes cubiertas (ambas levantadas por el equipo con el celular; aún NO existen datos):
- Complemento A: auditoría de paisaje lingüístico (letreros en inglés, "se vende", "se renta").
  * Entrada: fotos en `raw/campo/fotos_letreros/` (JPG/JPEG/HEIC convertidas a JPG) con GPS activo.
  * Paso 1: el script lee el EXIF (fecha y GPS) con Pillow, ubica cada foto en su colonia del
    GeoPortal por punto en polígono y AGREGA las fotos nuevas a `raw/campo/letreros_plantilla.csv`
    (columnas `foto, fecha, latitud, longitud, colonia, idioma_letrero, tipo, notas`).
  * Paso 2 (a mano): llenar `idioma_letrero` (es, en, bilingue, maya, otro) y `tipo`
    (comercio, se_vende, se_renta, otro). Lo que ya se llenó no se sobrescribe.
  * Salida: `clean/campo_letreros.csv` y `clean/campo_letreros_resumen_colonia.csv`.
- Complemento B: "índice del americano" (precio de un café americano por negocio).
  * Entrada: `raw/campo/americano_plantilla.csv` (`fecha, negocio, colonia, latitud, longitud,
    precio_americano_mxn, tamano_ml, foto_menu`); fotos de menús en `raw/campo/fotos_menus/`.
  * Salida: `clean/campo_americano.csv` (con precio por 355 ml y colonia del GeoPortal) y
    `clean/campo_americano_resumen_colonia.csv`.

Si no hay fotos ni filas, el script lo avisa y no genera archivos limpios vacíos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from PIL import ExifTags, Image
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
CAMPO = BASE_DIR / "raw" / "campo"
CLEAN_DIR = BASE_DIR / "clean"
COLONIAS = ROOT_DIR / "4-GeoPortal-Merida" / "clean" / "geoportal_colonias_merida.geojson"
CENTRO = ROOT_DIR / "4-GeoPortal-Merida" / "clean" / "geoportal_centro_historico.geojson"

PLANTILLA_LETREROS = CAMPO / "letreros_plantilla.csv"
PLANTILLA_AMERICANO = CAMPO / "americano_plantilla.csv"
COLS_LETREROS = ["foto", "fecha", "latitud", "longitud", "colonia", "idioma_letrero", "tipo", "notas"]
TIPOS = {"comercio", "se_vende", "se_renta", "otro"}
IDIOMAS = {"es", "en", "bilingue", "maya", "otro"}
EXT_FOTO = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
GPS_TAG = next(k for k, v in ExifTags.TAGS.items() if v == "GPSInfo")


class Colonias:
    """Índice espacial de colonias del GeoPortal (`unidad_habitacional`) y del Centro Histórico."""

    def __init__(self) -> None:
        fc = json.loads(COLONIAS.read_text(encoding="utf-8"))
        self.geoms = [shape(f["geometry"]) for f in fc["features"]]
        self.nombres = [f["properties"]["unidad_habitacional"] for f in fc["features"]]
        self.arbol = STRtree(self.geoms)
        ch = json.loads(CENTRO.read_text(encoding="utf-8"))
        self.centro = shape(ch["features"][0]["geometry"])

    def colonia(self, lat: float, lon: float) -> str:
        p = Point(lon, lat)
        for i in self.arbol.query(p):
            if self.geoms[i].contains(p):
                return self.nombres[i]
        return ""

    def en_centro(self, lat: float, lon: float) -> bool:
        return self.centro.contains(Point(lon, lat))


def _dms(valor, ref) -> float | None:
    try:
        g, m, s = (float(x) for x in valor)
    except (TypeError, ValueError):
        return None
    dec = g + m / 60 + s / 3600
    return -dec if ref in ("S", "W") else dec


def leer_exif(ruta: Path) -> tuple[str, float | None, float | None]:
    """Devuelve (fecha ISO, latitud, longitud) del EXIF de una foto."""
    with Image.open(ruta) as img:
        exif = img.getexif()
        fecha = exif.get(36867) or exif.get(306) or ""  # DateTimeOriginal o DateTime
        if not fecha:
            fecha = exif.get_ifd(0x8769).get(36867, "")
        gps = exif.get_ifd(GPS_TAG) if GPS_TAG in exif else {}
    lat = _dms(gps.get(2), gps.get(1)) if gps else None
    lon = _dms(gps.get(4), gps.get(3)) if gps else None
    if fecha:
        fecha = fecha[:10].replace(":", "-")
    return fecha, (round(lat, 6) if lat is not None else None), (round(lon, 6) if lon is not None else None)


def actualizar_plantilla_letreros(col: Colonias) -> pd.DataFrame:
    plantilla = pd.read_csv(PLANTILLA_LETREROS, dtype=str, keep_default_na=False) if PLANTILLA_LETREROS.exists() \
        else pd.DataFrame(columns=COLS_LETREROS)
    ya = set(plantilla["foto"])
    nuevas = []
    for ruta in sorted((CAMPO / "fotos_letreros").iterdir()):
        if ruta.suffix.lower() not in EXT_FOTO or ruta.name in ya:
            continue
        fecha, lat, lon = leer_exif(ruta)
        nuevas.append({
            "foto": ruta.name, "fecha": fecha,
            "latitud": "" if lat is None else lat, "longitud": "" if lon is None else lon,
            "colonia": col.colonia(lat, lon) if lat is not None else "",
            "idioma_letrero": "", "tipo": "", "notas": "" if lat is not None else "sin GPS en EXIF",
        })
    if nuevas:
        plantilla = pd.concat([plantilla, pd.DataFrame(nuevas)], ignore_index=True)
        plantilla[COLS_LETREROS].to_csv(PLANTILLA_LETREROS, index=False)
        print(f"  + {len(nuevas)} fotos nuevas agregadas a {PLANTILLA_LETREROS.name}")
    return plantilla


def limpiar_letreros(plantilla: pd.DataFrame, col: Colonias) -> int:
    if plantilla.empty:
        print("  letreros: no hay fotos en raw/campo/fotos_letreros/ (pendiente de campo)")
        return 0
    df = plantilla.copy()
    df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
    df["idioma_letrero"] = df["idioma_letrero"].str.strip().str.lower()
    df["tipo"] = df["tipo"].str.strip().str.lower()
    df["clasificado"] = df["idioma_letrero"].isin(IDIOMAS) & df["tipo"].isin(TIPOS)
    df["en_centro_historico"] = [
        bool(col.en_centro(a, o)) if pd.notna(a) else None for a, o in zip(df["latitud"], df["longitud"])
    ]
    df.to_csv(CLEAN_DIR / "campo_letreros.csv", index=False)
    ok = df[df["clasificado"]]
    if not ok.empty:
        res = ok.groupby("colonia").agg(
            n_letreros=("foto", "size"),
            n_en_ingles_o_bilingue=("idioma_letrero", lambda x: int(x.isin(["en", "bilingue"]).sum())),
            n_se_vende=("tipo", lambda x: int((x == "se_vende").sum())),
            n_se_renta=("tipo", lambda x: int((x == "se_renta").sum())),
        ).reset_index()
        res["pct_ingles_o_bilingue"] = (100 * res["n_en_ingles_o_bilingue"] / res["n_letreros"]).round(1)
        res.rename(columns={"colonia": "unidad_habitacional"}).to_csv(
            CLEAN_DIR / "campo_letreros_resumen_colonia.csv", index=False)
    print(f"  letreros: {len(df)} fotos ({int(df['clasificado'].sum())} clasificadas)")
    return len(df)


def limpiar_americano(col: Colonias) -> int:
    df = pd.read_csv(PLANTILLA_AMERICANO, dtype=str, keep_default_na=False)
    if df.empty:
        print("  americano: la plantilla está vacía (pendiente de campo)")
        return 0
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
    for c in ("latitud", "longitud", "precio_americano_mxn", "tamano_ml"):
        df[c] = pd.to_numeric(df[c].str.replace(",", "").str.replace("$", ""), errors="coerce")
    df["negocio"] = df["negocio"].str.strip()
    falta = df["colonia"].str.strip() == ""
    df.loc[falta & df["latitud"].notna(), "colonia"] = [
        col.colonia(a, o) for a, o in zip(df.loc[falta & df["latitud"].notna(), "latitud"],
                                          df.loc[falta & df["latitud"].notna(), "longitud"])
    ]
    df["unidad_habitacional"] = [
        col.colonia(a, o) if pd.notna(a) else "" for a, o in zip(df["latitud"], df["longitud"])
    ]
    df["en_centro_historico"] = [
        bool(col.en_centro(a, o)) if pd.notna(a) else None for a, o in zip(df["latitud"], df["longitud"])
    ]
    df["precio_por_355ml_mxn"] = (df["precio_americano_mxn"] / df["tamano_ml"] * 355).round(2)
    df = df.drop_duplicates(["fecha", "negocio"])
    df.to_csv(CLEAN_DIR / "campo_americano.csv", index=False)
    res = df.groupby(["unidad_habitacional", "en_centro_historico"], dropna=False).agg(
        n_negocios=("negocio", "nunique"),
        precio_mediano_mxn=("precio_americano_mxn", "median"),
        precio_mediano_355ml_mxn=("precio_por_355ml_mxn", "median"),
    ).reset_index()
    res.to_csv(CLEAN_DIR / "campo_americano_resumen_colonia.csv", index=False)
    print(f"  americano: {len(df)} precios en {df['negocio'].nunique()} negocios")
    return len(df)


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    col = Colonias()
    print("Limpieza Sección 7 (trabajo de campo):")
    plantilla = actualizar_plantilla_letreros(col)
    limpiar_letreros(plantilla, col)
    limpiar_americano(col)


if __name__ == "__main__":
    main()
