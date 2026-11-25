"""
Limpieza de la sección 8-LiDAR: altura aproximada de lo construido por manzana del Centro.

Fuentes cubiertas:
- Principal: INEGI, Modelos Digitales de Elevación de alta resolución 1:10 000, 5 m,
  tipo superficie (MDS) y terreno (MDT), edición 2016, cartas F16C52A1 y F16C52A2 (las únicas
  que tocan el polígono del Centro Histórico más 500 m). OJO: según sus metadatos, para estas
  cartas el modelo es fotogramétrico de imágenes ópticas de satélite (nube de puntos del
  2015-07-28), no LiDAR aerotransportado.
- Validación: mismo catálogo, MDS y MDT de 1.5 m, edición 2025 (imagen estereoscópica del
  2017-03-11), mismas cartas.
- Manzanas: INEGI Marco Geoestadístico (`4-GeoPortal-Merida/raw/inegi_marco_geo_31_yucatan.zip`,
  capa `31m`), Mérida localidad 0001.

La lista de archivos, URL y fechas está en `raw/lidar_metadatos_transcritos.csv`; el script
descarga a `raw/inegi_lidar/` lo que falte (caché) y lo extrae.

Salidas:
- clean/lidar_alturas_manzanas_centro.csv
- clean/lidar_ndsm_centro.tif (Cloud Optimized GeoTIFF, EPSG:4326, nDSM 5 m)
"""

from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rasterio
import requests
import shapefile
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject
import shapely
from shapely.geometry import box, shape

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
RAW_DIR = BASE_DIR / "raw"
LIDAR_DIR = RAW_DIR / "inegi_lidar"
CLEAN_DIR = BASE_DIR / "clean"
METADATOS = RAW_DIR / "lidar_metadatos_transcritos.csv"
CENTRO = ROOT_DIR / "4-GeoPortal-Merida" / "clean" / "geoportal_centro_historico.geojson"
MARCO = ROOT_DIR / "4-GeoPortal-Merida" / "raw" / "inegi_marco_geo_31_yucatan.zip"
AR1 = ROOT_DIR / "9-Augmented-Reality" / "clean" / "ar1_denue_resumen_manzanas_centro.csv"
USER_AGENT = "MeridaForSale-UPY/1.0 (+https://github.com/BradRobles/M-rida-for-Sale)"
MARGEN_M = 500
UMBRAL_M = 6.0


def shp_transform(func, geom):
    """Reproyecta una geometría shapely con una función (x, y) -> (x, y) de pyproj."""
    return shapely.transform(geom, lambda xy: np.column_stack(func(xy[:, 0], xy[:, 1])))


def descargar(meta: pd.DataFrame) -> None:
    LIDAR_DIR.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    for _, m in meta.iterrows():
        destino = LIDAR_DIR / Path(m["url"]).name
        if not destino.exists():
            print(f"  descargando {destino.name} ({m['carta_1_10000']} {m['modelo']} {m['resolucion_m']} m)")
            for i in range(4):
                try:
                    r = s.get(m["url"], timeout=300)
                    r.raise_for_status()
                    destino.write_bytes(r.content)
                    break
                except requests.RequestException as e:
                    print(f"    reintento {i + 1}: {e}")
                    time.sleep(10 * 2**i)
            time.sleep(2)
        carpeta = LIDAR_DIR / "extraido" / str(m["upc"])
        if not carpeta.exists():
            with zipfile.ZipFile(destino) as zf:
                for info in zf.infolist():
                    nombre = info.filename.replace("\\", "/")
                    if nombre.endswith("/"):
                        continue
                    out = carpeta / nombre
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(zf.read(info))


def raster_de(upc) -> Path:
    carpeta = LIDAR_DIR / "extraido" / str(upc) / "conjunto_de_datos"
    for ext in (".tif", ".bil"):
        hall = sorted(carpeta.glob(f"*{ext}"))
        if hall:
            return hall[0]
    raise FileNotFoundError(carpeta)


def mosaico(upcs: list, limites, res: float | None = None):
    fuentes = [rasterio.open(raster_de(u)) for u in upcs]
    crs = fuentes[0].crs
    arr, tr = merge(fuentes, bounds=limites, res=res, nodata=np.nan, dtype="float32")
    nod = fuentes[0].nodata
    for f in fuentes:
        f.close()
    a = arr[0].astype("float64")
    if nod is not None:
        a[np.isclose(a, nod) | (a < -1e30)] = np.nan
    a[(a < -100) | (a > 1000)] = np.nan
    return a, tr, crs


def centro_y_limites(crs):
    fc = json.loads(CENTRO.read_text(encoding="utf-8"))
    poly4326 = shape(fc["features"][0]["geometry"])
    t = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    poly = shp_transform(t.transform, poly4326)
    minx, miny, maxx, maxy = poly.buffer(MARGEN_M).bounds
    return poly4326, poly, (minx, miny, maxx, maxy)


def manzanas(crs, limites, centro_utm) -> pd.DataFrame:
    """Manzanas de Mérida (loc 0001) que tocan el recorte, en el CRS del raster."""
    with zipfile.ZipFile(MARCO) as zf:
        prj = zf.read("conjunto_de_datos/31m.prj").decode("utf-8", errors="ignore")
        t = pyproj.Transformer.from_crs(pyproj.CRS.from_wkt(prj), crs, always_xy=True)
        t4326 = pyproj.Transformer.from_crs(pyproj.CRS.from_wkt(prj), "EPSG:4326", always_xy=True)
        caja = box(*limites)
        filas = []
        with zf.open("conjunto_de_datos/31m.shp") as shp, zf.open("conjunto_de_datos/31m.dbf") as dbf:
            sf = shapefile.Reader(shp=shp, dbf=dbf, encoding="latin1")
            for sr in sf.iterShapeRecords():
                rec = sr.record.as_dict()
                if rec["CVE_MUN"] != "050" or rec["CVE_LOC"] != "0001":
                    continue
                g = shape(sr.shape.__geo_interface__)
                gu = shp_transform(t.transform, g)
                if not gu.intersects(caja):
                    continue
                c = shp_transform(t4326.transform, g).representative_point()
                filas.append({
                    "cvegeo": rec["CVEGEO"], "cve_ageb": rec["CVE_AGEB"], "cve_mza": rec["CVE_MZA"],
                    "clave_manzana": f"{rec['CVE_AGEB']}-{rec['CVE_MZA']}",
                    "centroide_lat": round(c.y, 6), "centroide_lon": round(c.x, 6),
                    "area_m2": round(gu.area, 1),
                    "en_centro_historico": bool(centro_utm.contains(gu.representative_point())),
                    "geom": gu,
                })
    return pd.DataFrame(filas)


def estadisticas(ndsm: np.ndarray, tr, mz: pd.DataFrame, sufijo: str = "") -> pd.DataFrame:
    ids = rasterize(((g, i + 1) for i, g in enumerate(mz["geom"])), out_shape=ndsm.shape, transform=tr,
                    fill=0, dtype="int32", all_touched=False)
    filas = []
    for i in range(len(mz)):
        v = ndsm[ids == i + 1]
        v = v[~np.isnan(v)]
        if v.size == 0:
            filas.append({"n_celdas" + sufijo: 0})
            continue
        h = np.clip(v, 0, None)  # alturas negativas (ruido MDS < MDT) cuentan como 0 m
        filas.append({
            "altura_media_m" + sufijo: round(float(h.mean()), 2),
            "altura_p90_m" + sufijo: round(float(np.percentile(h, 90)), 2),
            "altura_max_m" + sufijo: round(float(h.max()), 2),
            "pct_celdas_mayor_6m" + sufijo: round(float(100 * (h > UMBRAL_M).mean()), 1),
            "n_celdas" + sufijo: int(v.size),
            "pct_celdas_negativas" + sufijo: round(float(100 * (v < 0).mean()), 1),
            "ndsm_min_m" + sufijo: round(float(v.min()), 2),
        })
    return pd.DataFrame(filas)


def escribir_cog(ndsm: np.ndarray, tr, crs, destino: Path) -> None:
    h, w = ndsm.shape
    left, top = tr.c, tr.f
    right, bottom = left + tr.a * w, top + tr.e * h
    dst_tr, dw, dh = calculate_default_transform(crs, "EPSG:4326", w, h, left, bottom, right, top)
    out = np.full((dh, dw), np.nan, dtype="float32")
    reproject(ndsm.astype("float32"), out, src_transform=tr, src_crs=crs, dst_transform=dst_tr,
              dst_crs="EPSG:4326", resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
    out = np.round(out, 2)
    perfil = {"driver": "COG", "width": dw, "height": dh, "count": 1, "dtype": "float32", "crs": "EPSG:4326",
              "transform": dst_tr, "nodata": np.nan, "compress": "DEFLATE", "predictor": 3}
    with rasterio.open(destino, "w", **perfil) as dst:
        dst.write(out, 1)
        dst.update_tags(descripcion="nDSM = MDS - MDT (m), INEGI 5 m, cartas F16C52A1-A2, Centro Histórico + 500 m")


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    meta = pd.read_csv(METADATOS, dtype={"upc": str})
    descargar(meta)
    ppal = meta[meta["uso"] == "principal"]
    val = meta[meta["uso"] == "validacion"]

    with rasterio.open(raster_de(ppal["upc"].iloc[0])) as r0:
        crs = r0.crs
    poly4326, centro_utm, limites = centro_y_limites(crs)

    mds, tr, _ = mosaico(list(ppal[ppal["modelo"] == "MDS"]["upc"]), limites, res=5.0)
    mdt, tr2, _ = mosaico(list(ppal[ppal["modelo"] == "MDT"]["upc"]), limites, res=5.0)
    assert mds.shape == mdt.shape and tr == tr2
    ndsm = mds - mdt
    print(f"  nDSM 5 m: {ndsm.shape[1]}×{ndsm.shape[0]} celdas; {np.isnan(ndsm).mean():.1%} sin dato")

    mz = manzanas(crs, limites, centro_utm)
    st = estadisticas(ndsm, tr, mz)

    mds15, tr15, _ = mosaico(list(val[val["modelo"] == "MDS"]["upc"]), limites, res=1.5)
    mdt15, _, _ = mosaico(list(val[val["modelo"] == "MDT"]["upc"]), limites, res=1.5)
    st15 = estadisticas(mds15 - mdt15, tr15, mz, sufijo="_1_5m")
    st15 = st15[[c for c in st15.columns if c in ("altura_media_m_1_5m", "altura_p90_m_1_5m", "n_celdas_1_5m")]]

    out = pd.concat([mz.drop(columns="geom").reset_index(drop=True), st, st15], axis=1)
    out["n_celdas"] = out["n_celdas"].fillna(0).astype(int)
    ar1 = pd.read_csv(AR1, dtype=str)
    out["en_ar1"] = out["clave_manzana"].isin(set(ar1["clave_manzana"]))
    cols = ["clave_manzana", "cvegeo", "cve_ageb", "cve_mza", "en_centro_historico", "en_ar1",
            "centroide_lat", "centroide_lon", "area_m2", "altura_media_m", "altura_p90_m", "altura_max_m",
            "pct_celdas_mayor_6m", "n_celdas", "pct_celdas_negativas", "ndsm_min_m",
            "altura_media_m_1_5m", "altura_p90_m_1_5m", "n_celdas_1_5m"]
    out = out[cols].sort_values("clave_manzana").reset_index(drop=True)
    out.to_csv(CLEAN_DIR / "lidar_alturas_manzanas_centro.csv", index=False)

    destino_tif = CLEAN_DIR / "lidar_ndsm_centro.tif"
    escribir_cog(ndsm, tr, crs, destino_tif)
    mb = destino_tif.stat().st_size / 1e6
    if mb > 50:
        destino_tif.unlink()
        print(f"  lidar_ndsm_centro.tif pesaba {mb:.1f} MB (> 50 MB); no se guarda")

    # ---- Validación ----
    ch = out[out["en_centro_historico"] & (out["n_celdas"] > 0)]
    ar1_ok = ar1["clave_manzana"].isin(set(out.loc[out["n_celdas"] > 0, "clave_manzana"]))
    corr = ch[["altura_media_m", "altura_media_m_1_5m"]].dropna().corr().iloc[0, 1]
    print("Limpieza Sección 8 (LiDAR / MDE INEGI) completada:")
    print(f"  - lidar_alturas_manzanas_centro.csv: {len(out)} manzanas en el recorte "
          f"({int(out['en_centro_historico'].sum())} dentro del Centro Histórico)")
    if destino_tif.exists():
        print(f"  - lidar_ndsm_centro.tif: {mb:.1f} MB")
    print(f"  - Cruce con AR 1: {ar1_ok.sum()} de {len(ar1)} manzanas ({100 * ar1_ok.mean():.1f}%)")
    print(f"  - Centro: mediana de altura media {ch['altura_media_m'].median():.2f} m; "
          f"{100 * ch['altura_media_m'].between(3, 8).mean():.1f}% entre 3 y 8 m; "
          f"p10–p90 {ch['altura_media_m'].quantile(.1):.2f}–{ch['altura_media_m'].quantile(.9):.2f} m")
    print(f"  - Manzanas con altura_max > 40 m: {(out['altura_max_m'] > 40).sum()} "
          f"(Centro: {(ch['altura_max_m'] > 40).sum()}); con media < 0: {(out['altura_media_m'] < 0).sum()}")
    print(f"  - Correlación altura media 5 m vs 1.5 m (Centro): {corr:.2f}; "
          f"mediana 1.5 m {ch['altura_media_m_1_5m'].median():.2f} m")


if __name__ == "__main__":
    main()
