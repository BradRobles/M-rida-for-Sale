"""
Limpieza y estandarización de datos para la sección 4-GeoPortal-Merida.

Incluye:
- Principal: GeoPortal de Mérida — Colonias (500), Zona de Monumentos Históricos
  (Centro Histórico) y Zonas Patrimoniales Culturales Municipales (73).
- Complemento A: OpenStreetMap (Overpass API) — hoteles, hostales, cafés y
  alojamiento turístico en Mérida.
- Complemento B: Marco Geoestadístico de INEGI — AGEBs urbanas y límite
  municipal de Mérida (reproyectados de MEXICO_ITRF_2008_LCC a WGS84 EPSG:4326).
"""

from pathlib import Path
import json
import zipfile
import pandas as pd
import pyproj
import shapefile

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
CLEAN_DIR = BASE_DIR / "clean"


def clean_str(val: object) -> str:
    if val is None or pd.isna(val):
        return ""
    return " ".join(str(val).strip().split())


def reproject_coords(coords, transformer: pyproj.Transformer):
    """Reproyecta recursivamente listas de coordenadas (anillos/multipolígonos)."""
    if isinstance(coords[0], (int, float)):
        lon, lat = transformer.transform(coords[0], coords[1])
        return [round(lon, 6), round(lat, 6)]
    return [reproject_coords(c, transformer) for c in coords]


def export_inegi_layer(
    zf: zipfile.ZipFile,
    layer_prefix: str,
    cve_mun_filter: str,
    out_geojson: Path,
    out_csv: Path | None = None,
) -> int:
    """Extrae una capa shapefile de INEGI, filtra Mérida y reproyecta a EPSG:4326."""
    prj_text = zf.read(f"conjunto_de_datos/{layer_prefix}.prj").decode("utf-8", errors="ignore")
    src_crs = pyproj.CRS.from_wkt(prj_text)
    transformer = pyproj.Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)

    features = []
    csv_rows = []

    with zf.open(f"conjunto_de_datos/{layer_prefix}.shp") as shp, zf.open(
        f"conjunto_de_datos/{layer_prefix}.dbf"
    ) as dbf:
        sf = shapefile.Reader(shp=shp, dbf=dbf, encoding="latin1")
        for sr in sf.iterShapeRecords():
            rec = sr.record.as_dict()
            if rec.get("CVE_MUN") != cve_mun_filter:
                continue

            geom = sr.shape.__geo_interface__
            geom["coordinates"] = reproject_coords(geom["coordinates"], transformer)

            # Centroide aproximado a partir del bbox reproyectado
            xmin, ymin, xmax, ymax = sr.shape.bbox
            lon_min, lat_min = transformer.transform(xmin, ymin)
            lon_max, lat_max = transformer.transform(xmax, ymax)
            c_lon = round((lon_min + lon_max) / 2, 6)
            c_lat = round((lat_min + lat_max) / 2, 6)

            props = {k.lower(): clean_str(v) for k, v in rec.items()}
            props["centroide_lat"] = c_lat
            props["centroide_lon"] = c_lon

            features.append({"type": "Feature", "geometry": geom, "properties": props})
            if out_csv is not None:
                csv_rows.append(props)

    fc = {
        "type": "FeatureCollection",
        "name": out_geojson.stem,
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }
    out_geojson.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")

    if out_csv is not None and csv_rows:
        pd.DataFrame(csv_rows).to_csv(out_csv, index=False)

    return len(features)


def clean_osm_pois() -> int:
    """Limpia los POIs de OpenStreetMap y exporta CSV y GeoJSON."""
    raw = json.loads((RAW_DIR / "osm_merida_pois.json").read_text(encoding="utf-8"))
    rows = []
    features = []
    seen = set()

    for el in raw.get("elements", []):
        osm_key = (el.get("type"), el.get("id"))
        if osm_key in seen:
            continue
        seen.add(osm_key)

        lat = el.get("lat") if "lat" in el else el.get("center", {}).get("lat")
        lon = el.get("lon") if "lon" in el else el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue

        tags = el.get("tags", {})
        subcat = tags.get("tourism") or tags.get("amenity") or tags.get("office") or "otro"
        if subcat in {"hotel", "hostel", "guest_house", "motel"}:
            cat = "Hospedaje"
        elif subcat == "cafe":
            cat = "Cafeteria"
        elif subcat in {"coworking", "coworking_space"}:
            cat = "Coworking"
        else:
            cat = "Otro"

        props = {
            "osm_id": int(el["id"]),
            "osm_type": el["type"],
            "nombre": clean_str(tags.get("name")) or "SIN NOMBRE",
            "categoria": cat,
            "subcategoria": subcat,
            "calle": clean_str(tags.get("addr:street")),
            "numero": clean_str(tags.get("addr:housenumber")),
            "colonia": clean_str(tags.get("addr:suburb") or tags.get("addr:neighbourhood")),
            "codigo_postal": clean_str(tags.get("addr:postcode")),
            "sitio_web": clean_str(tags.get("website") or tags.get("contact:website")),
            "latitud": round(float(lat), 6),
            "longitud": round(float(lon), 6),
        }
        rows.append(props)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [props["longitud"], props["latitud"]]},
                "properties": props,
            }
        )

    df = pd.DataFrame(rows).sort_values(["categoria", "subcategoria", "nombre"]).reset_index(drop=True)
    df.to_csv(CLEAN_DIR / "osm_merida_pois_turismo_cafes.csv", index=False)

    fc = {
        "type": "FeatureCollection",
        "name": "osm_merida_pois_turismo_cafes",
        "features": features,
    }
    (CLEAN_DIR / "osm_merida_pois_turismo_cafes.geojson").write_text(
        json.dumps(fc, ensure_ascii=False), encoding="utf-8"
    )
    return len(df)


def iter_lon_lat(coords):
    """Genera pares (lon, lat) de cualquier geometría GeoJSON."""
    if not coords:
        return
    if isinstance(coords[0], (int, float)):
        yield coords[0], coords[1]
    else:
        for c in coords:
            yield from iter_lon_lat(c)


def bbox_centroid(geom: dict) -> tuple[float | None, float | None]:
    """Calcula el centroide aproximado del bounding box de una geometría GeoJSON."""
    pts = list(iter_lon_lat(geom.get("coordinates", [])))
    if not pts:
        return None, None
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return round((min(lats) + max(lats)) / 2, 6), round((min(lons) + max(lons)) / 2, 6)


def clean_geoportal_layers() -> tuple[int, int, int]:
    """Limpia las capas descargadas del GeoPortal de Mérida (Colonias, Centro, Patrimonio)."""
    # 1. Colonias
    col_raw = json.loads((RAW_DIR / "colonias.geojson").read_text(encoding="utf-8"))
    col_feats, col_rows = [], []
    for f in col_raw.get("features", []):
        geom = f.get("geometry", {})
        p = f.get("properties", {})
        c_lat, c_lon = bbox_centroid(geom)
        props = {
            "idgeo": p.get("idgeo"),
            "idcolonia": p.get("idcolonia"),
            "nombre": clean_str(p.get("nombre")),
            "unidad_habitacional": clean_str(p.get("unidadhabi")),
            "localidad": clean_str(p.get("localidad")),
            "codigo_postal": clean_str(p.get("cp")),
            "centroide_lat": c_lat,
            "centroide_lon": c_lon,
        }
        col_feats.append({"type": "Feature", "geometry": geom, "properties": props})
        col_rows.append(props)

    (CLEAN_DIR / "geoportal_colonias_merida.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "name": "geoportal_colonias_merida", "features": col_feats}, ensure_ascii=False),
        encoding="utf-8",
    )
    pd.DataFrame(col_rows).sort_values("nombre").to_csv(
        CLEAN_DIR / "geoportal_colonias_merida_catalogo.csv", index=False
    )

    # 2. Centro Histórico (Zona de Monumentos Históricos)
    ch_raw = json.loads((RAW_DIR / "z_monu_historicos_2040.geojson").read_text(encoding="utf-8"))
    ch_feats = []
    for f in ch_raw.get("features", []):
        geom = f.get("geometry", {})
        p = f.get("properties", {})
        c_lat, c_lon = bbox_centroid(geom)
        props = {
            "idgeo": p.get("idgeo"),
            "nombre": clean_str(p.get("nombre")) or "ZONA DE MONUMENTOS HISTÓRICOS",
            "capa_origen": clean_str(p.get("layer")),
            "area_m2": round(float(p["shape_area"]), 2) if p.get("shape_area") is not None else None,
            "perimetro_m": round(float(p["shape_len"]), 2) if p.get("shape_len") is not None else None,
            "centroide_lat": c_lat,
            "centroide_lon": c_lon,
        }
        ch_feats.append({"type": "Feature", "geometry": geom, "properties": props})

    (CLEAN_DIR / "geoportal_centro_historico.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "name": "geoportal_centro_historico", "features": ch_feats}, ensure_ascii=False),
        encoding="utf-8",
    )

    # 3. Zonas Patrimoniales Culturales Municipales
    pat_raw = json.loads((RAW_DIR / "z_patri_cul_muni_merida_2040.geojson").read_text(encoding="utf-8"))
    pat_feats, pat_rows = [], []
    for f in pat_raw.get("features", []):
        geom = f.get("geometry", {})
        p = f.get("properties", {})
        c_lat, c_lon = bbox_centroid(geom)
        nombre = clean_str(p.get("nombre")) or clean_str(p.get("layer")) or f"ZONA_{p.get('idgeo')}"
        props = {
            "idgeo": p.get("idgeo"),
            "nombre": nombre,
            "capa_origen": clean_str(p.get("layer")),
            "area_m2": round(float(p["shape_area"]), 2) if p.get("shape_area") is not None else None,
            "perimetro_m": round(float(p["shape_len"]), 2) if p.get("shape_len") is not None else None,
            "centroide_lat": c_lat,
            "centroide_lon": c_lon,
        }
        pat_feats.append({"type": "Feature", "geometry": geom, "properties": props})
        pat_rows.append(props)

    (CLEAN_DIR / "geoportal_zonas_patrimoniales.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "name": "geoportal_zonas_patrimoniales", "features": pat_feats}, ensure_ascii=False),
        encoding="utf-8",
    )
    pd.DataFrame(pat_rows).sort_values("nombre").to_csv(
        CLEAN_DIR / "geoportal_zonas_patrimoniales_catalogo.csv", index=False
    )

    return len(col_feats), len(ch_feats), len(pat_feats)


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    col_count, ch_count, pat_count = clean_geoportal_layers()
    osm_count = clean_osm_pois()

    with zipfile.ZipFile(RAW_DIR / "inegi_marco_geo_31_yucatan.zip") as zf:
        ageb_count = export_inegi_layer(
            zf,
            layer_prefix="31a",
            cve_mun_filter="050",
            out_geojson=CLEAN_DIR / "inegi_agebs_merida.geojson",
            out_csv=CLEAN_DIR / "inegi_agebs_merida_catalogo.csv",
        )
        mun_count = export_inegi_layer(
            zf,
            layer_prefix="31mun",
            cve_mun_filter="050",
            out_geojson=CLEAN_DIR / "inegi_municipio_merida.geojson",
            out_csv=None,
        )

    print("Limpieza Sección 4 completada:")
    print(f"  - geoportal_colonias_merida (.geojson / _catalogo.csv): {col_count} colonias")
    print(f"  - geoportal_centro_historico.geojson: {ch_count} polígono")
    print(f"  - geoportal_zonas_patrimoniales (.geojson / _catalogo.csv): {pat_count} zonas")
    print(f"  - osm_merida_pois_turismo_cafes (.csv / .geojson): {osm_count} puntos")
    print(f"  - inegi_agebs_merida (.geojson / _catalogo.csv): {ageb_count} AGEBs urbanas")
    print(f"  - inegi_municipio_merida.geojson: {mun_count} polígono municipal")


if __name__ == "__main__":
    main()
