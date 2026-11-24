"""
Limpieza y estandarización de datos para la sección 9-Augmented-Reality.

Escenas:
- Escena AR 1: Manzana del Centro con negocios 2019 vs. 2025 (INEGI DENUE).
- Escena AR 2: Turistas nacionales vs. extranjeros en Mérida (DataTur).
- Escena AR 3: Crecimiento aeroportuario Mérida vs. Cancún vs. Oaxaca (ASUR).

Este script únicamente extrae, limpia y exporta tablas CSV listas para
visualización; no genera gráficos ni escenas 3D.
"""

from pathlib import Path
import html as htmllib
import re
import unicodedata
import zipfile
import openpyxl
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw"
CLEAN_DIR = BASE_DIR / "clean"

MESES_ES = {
    "enero": 1, "ene": 1,
    "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6,
    "julio": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "sep": 9,
    "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}

MESES_NUM_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

ASENTAMIENTOS_CENTRO = {
    "CENTRO",
    "CENTRO HISTORICO",
    "MERIDA CENTRO",
    "COL. CENTRO",
    "COLONIA CENTRO",
    "ZONA CENTRO",
}


def norm_text(val: object) -> str:
    """Normaliza espacios, mayúsculas y elimina acentos para comparación."""
    if pd.isna(val):
        return ""
    s = " ".join(str(val).strip().upper().split())
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def clean_str(val: object) -> str:
    """Normaliza espacios en blanco manteniendo acentos."""
    if pd.isna(val):
        return ""
    return " ".join(str(val).strip().split())


def classify_scian(codigo: object) -> str:
    """Clasifica el código SCIAN en categorías clave de turistificación."""
    s = str(codigo).strip()
    if s.startswith("721"):
        return "Hospedaje"
    if s.startswith("722"):
        return "Alimentos y bebidas"
    if s.startswith("46111"):
        return "Tiendas de abarrotes"
    return "Comercio y otros servicios"


def load_denue_centro(zip_name: str, anio: int) -> pd.DataFrame:
    """Carga y filtra negocios de Mérida Centro desde un archivo ZIP del DENUE."""
    usecols = [
        "id", "nom_estab", "raz_social", "codigo_act", "nombre_act",
        "per_ocu", "nom_vial", "numero_ext", "nomb_asent", "cod_postal",
        "cve_mun", "cve_loc", "ageb", "manzana", "latitud", "longitud", "fecha_alta",
    ]
    zpath = RAW_DIR / zip_name
    with zipfile.ZipFile(zpath) as zf:
        with zf.open("conjunto_de_datos/denue_inegi_31_.csv") as f:
            df = pd.read_csv(f, usecols=usecols, encoding="latin1", low_memory=False)

    # Municipio 050 = Mérida, Localidad 0001 = Mérida cabecera municipal
    df = df[(df["cve_mun"] == 50) & (df["cve_loc"] == 1)].copy()
    df["asent_norm"] = df["nomb_asent"].map(norm_text)
    df = df[df["asent_norm"].isin(ASENTAMIENTOS_CENTRO)].copy()

    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["id", "latitud", "longitud"]).drop_duplicates(subset=["id"])

    df["nom_estab"] = df["nom_estab"].map(clean_str)
    df["raz_social"] = df["raz_social"].map(clean_str)
    df["codigo_act"] = df["codigo_act"].astype(str).str.strip()
    df["nombre_act"] = df["nombre_act"].map(clean_str)
    df["per_ocu"] = df["per_ocu"].map(clean_str)
    df["ageb"] = df["ageb"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(4)
    df["manzana"] = df["manzana"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(3)
    df["clave_manzana"] = df["ageb"] + "-" + df["manzana"]
    df["sector_turistico"] = df["codigo_act"].map(classify_scian)
    df["edicion_denue"] = anio
    return df


def build_ar1_denue() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compara negocios del Centro de Mérida entre DENUE 2019 y DENUE 2025."""
    df19 = load_denue_centro("denue_31_1119_csv.zip", 2019)
    df25 = load_denue_centro("denue_31_0525_csv.zip", 2025)

    ids19 = set(df19["id"])
    ids25 = set(df25["id"])

    # Tomamos atributos más recientes (2025) cuando existe en ambos; 2019 si cerró
    only19 = df19[~df19["id"].isin(ids25)].copy()
    combined = pd.concat([df25, only19], ignore_index=True)

    combined["en_2019"] = combined["id"].isin(ids19)
    combined["en_2025"] = combined["id"].isin(ids25)

    def estado(row: pd.Series) -> str:
        if row["en_2019"] and row["en_2025"]:
            return "Existia en 2019"
        if row["en_2025"]:
            return "Abrio despues de 2019"
        return "Cerro despues de 2019"

    combined["estado_cambio"] = combined.apply(estado, axis=1)

    cols_out = [
        "id", "nom_estab", "raz_social", "codigo_act", "nombre_act",
        "sector_turistico", "per_ocu", "ageb", "manzana", "clave_manzana",
        "asent_norm", "nom_vial", "numero_ext", "cod_postal",
        "latitud", "longitud", "fecha_alta",
        "en_2019", "en_2025", "estado_cambio",
    ]
    combined = combined[cols_out].rename(columns={"asent_norm": "colonia"})
    combined = combined.sort_values(["clave_manzana", "estado_cambio", "nom_estab"]).reset_index(drop=True)

    # Resumen por manzana para seleccionar bloque del Centro en la escena AR
    manzanas = (
        combined.groupby(["ageb", "manzana", "clave_manzana"], as_index=False)
        .agg(
            latitud_centro=("latitud", "mean"),
            longitud_centro=("longitud", "mean"),
            negocios_2019=("en_2019", "sum"),
            negocios_2025=("en_2025", "sum"),
            existian_2019=("estado_cambio", lambda s: int((s == "Existia en 2019").sum())),
            abrieron_despues_2019=("estado_cambio", lambda s: int((s == "Abrio despues de 2019").sum())),
            cerraron_despues_2019=("estado_cambio", lambda s: int((s == "Cerro despues de 2019").sum())),
            hospedaje_2025=("sector_turistico", lambda s: int(((s == "Hospedaje") & combined.loc[s.index, "en_2025"]).sum())),
            alimentos_bebidas_2025=("sector_turistico", lambda s: int(((s == "Alimentos y bebidas") & combined.loc[s.index, "en_2025"]).sum())),
        )
    )
    manzanas["cambio_neto"] = manzanas["negocios_2025"] - manzanas["negocios_2019"]
    manzanas["latitud_centro"] = manzanas["latitud_centro"].round(6)
    manzanas["longitud_centro"] = manzanas["longitud_centro"].round(6)
    manzanas = manzanas.sort_values(["abrieron_despues_2019", "negocios_2025"], ascending=[False, False]).reset_index(drop=True)

    return combined, manzanas


def parse_datatur_int(val: str) -> int | None:
    s = val.replace(",", "").strip()
    if not s or s == "-" or s.lower() == "n/d":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def build_ar2_datatur() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extrae llegadas de turistas nacionales vs. extranjeros en Mérida (DataTur)."""
    html = (RAW_DIR / "datatur_merida_turistas_2015_2026.html").read_text(encoding="utf-8", errors="ignore")
    tables = re.findall(r"<table.*?</table>", html, re.S)
    rows = re.findall(r"<tr.*?</tr>", tables[0], re.S)

    parsed_rows = []
    for r in rows:
        cells = [
            htmllib.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").strip()
            for c in re.findall(r"<t[hd][^>]*>.*?</t[hd]>", r, re.S)
        ]
        parsed_rows.append(cells)

    # Localizar fila de encabezado con Concepto | Total | Subtotal | Enero 2015 ...
    header_idx = next(i for i, c in enumerate(parsed_rows) if c and c[0] == "Concepto")
    headers = parsed_rows[header_idx]

    # Extraer únicamente las filas "Total categorias" de cada bloque de indicador
    blocks = {}
    current_indicator = None
    for cells in parsed_rows[header_idx + 1 :]:
        if not cells:
            continue
        label = " ".join(cells[0].split())
        if label in {
            "Llegadas de turistas",
            "Llegadas de turistas residentes",
            "Llegadas de turistas no residentes",
        }:
            current_indicator = label
        elif label == "Total categorias" and current_indicator:
            blocks[current_indicator] = cells

    month_cols = []
    for idx, col_name in enumerate(headers):
        parts = col_name.strip().lower().split()
        if len(parts) == 2 and parts[0] in MESES_ES and parts[1].isdigit():
            month_cols.append((idx, int(parts[1]), MESES_ES[parts[0]]))

    records = []
    for idx, anio, mes_num in month_cols:
        tot = parse_datatur_int(blocks["Llegadas de turistas"][idx])
        nac = parse_datatur_int(blocks["Llegadas de turistas residentes"][idx])
        ext = parse_datatur_int(blocks["Llegadas de turistas no residentes"][idx])
        if tot is None and nac is None and ext is None:
            continue
        pct_ext = round((ext / tot) * 100, 2) if (tot and ext is not None) else None
        records.append(
            {
                "destino": "Mérida",
                "anio": anio,
                "mes_num": mes_num,
                "mes": MESES_NUM_ES[mes_num],
                "fecha": f"{anio:04d}-{mes_num:02d}-01",
                "turistas_nacionales": nac,
                "turistas_extranjeros": ext,
                "turistas_total": tot,
                "pct_extranjeros": pct_ext,
            }
        )

    df_mensual = pd.DataFrame(records).sort_values(["anio", "mes_num"]).reset_index(drop=True)
    df_anual = (
        df_mensual.groupby(["destino", "anio"], as_index=False)
        .agg(
            meses_reportados=("mes_num", "count"),
            turistas_nacionales=("turistas_nacionales", "sum"),
            turistas_extranjeros=("turistas_extranjeros", "sum"),
            turistas_total=("turistas_total", "sum"),
        )
        .sort_values("anio")
        .reset_index(drop=True)
    )
    df_anual["pct_extranjeros"] = ((df_anual["turistas_extranjeros"] / df_anual["turistas_total"]) * 100).round(2)
    return df_mensual, df_anual


def build_ar3_asur() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extrae tráfico mensual y crecimiento anual de Mérida, Cancún y Oaxaca (ASUR)."""
    wb = openpyxl.load_workbook(RAW_DIR / "Trafico_de_pasajeros_ASUR.xlsx", data_only=True)
    airports = [
        ("PAX MID", "MID", "Mérida"),
        ("PAX CUN", "CUN", "Cancún"),
        ("PAX OAX", "OAX", "Oaxaca"),
    ]

    rows = []
    for sheet_name, code, city in airports:
        ws = wb[sheet_name]
        current_year = None
        for r in range(8, ws.max_row + 1):
            yr_cell = ws.cell(r, 2).value
            mo_cell = ws.cell(r, 3).value
            nac = ws.cell(r, 4).value
            intl = ws.cell(r, 5).value
            tot = ws.cell(r, 6).value

            if yr_cell is not None:
                yr_str = str(yr_cell).strip()
                if yr_str.startswith("Total"):
                    continue
                if yr_str.isdigit():
                    current_year = int(yr_str)

            if current_year is None or mo_cell is None or tot is None:
                continue

            mo_key = str(mo_cell).split("/")[0].strip().lower()
            mes_num = MESES_ES.get(mo_key)
            if mes_num is None:
                continue

            rows.append(
                {
                    "aeropuerto_codigo": code,
                    "aeropuerto": city,
                    "anio": current_year,
                    "mes_num": mes_num,
                    "mes": MESES_NUM_ES[mes_num],
                    "fecha": f"{current_year:04d}-{mes_num:02d}-01",
                    "pasajeros_nacional": int(round(nac)) if nac is not None else 0,
                    "pasajeros_internacional": int(round(intl)) if intl is not None else 0,
                    "pasajeros_total": int(round(tot)),
                }
            )

    df_mensual = pd.DataFrame(rows).sort_values(["aeropuerto_codigo", "anio", "mes_num"]).reset_index(drop=True)

    df_anual = (
        df_mensual.groupby(["aeropuerto_codigo", "aeropuerto", "anio"], as_index=False)
        .agg(
            meses_reportados=("mes_num", "count"),
            pasajeros_nacional=("pasajeros_nacional", "sum"),
            pasajeros_internacional=("pasajeros_internacional", "sum"),
            pasajeros_total=("pasajeros_total", "sum"),
        )
        .sort_values(["aeropuerto_codigo", "anio"])
        .reset_index(drop=True)
    )

    # Calcular crecimiento anual % e índice base 2015=100 y 2019=100 (solo años completos o indicando parcial)
    df_anual["crecimiento_anual_pct"] = (
        df_anual.groupby("aeropuerto_codigo")["pasajeros_total"].pct_change() * 100
    ).round(2)

    base_2015 = df_anual[df_anual["anio"] == 2015].set_index("aeropuerto_codigo")["pasajeros_total"]
    base_2019 = df_anual[df_anual["anio"] == 2019].set_index("aeropuerto_codigo")["pasajeros_total"]

    df_anual["indice_2015_100"] = (
        df_anual["pasajeros_total"] / df_anual["aeropuerto_codigo"].map(base_2015) * 100
    ).round(2)
    df_anual["indice_2019_100"] = (
        df_anual["pasajeros_total"] / df_anual["aeropuerto_codigo"].map(base_2019) * 100
    ).round(2)

    return df_mensual, df_anual


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    ar1_negocios, ar1_manzanas = build_ar1_denue()
    ar1_negocios.to_csv(CLEAN_DIR / "ar1_denue_merida_centro_2019_vs_2025.csv", index=False)
    ar1_manzanas.to_csv(CLEAN_DIR / "ar1_denue_resumen_manzanas_centro.csv", index=False)

    ar2_mensual, ar2_anual = build_ar2_datatur()
    ar2_mensual.to_csv(CLEAN_DIR / "ar2_datatur_merida_turistas_mensual_2015_2026.csv", index=False)
    ar2_anual.to_csv(CLEAN_DIR / "ar2_datatur_merida_turistas_anual_2015_2026.csv", index=False)

    ar3_mensual, ar3_anual = build_ar3_asur()
    ar3_mensual.to_csv(CLEAN_DIR / "ar3_asur_trafico_mensual_mid_cun_oax.csv", index=False)
    ar3_anual.to_csv(CLEAN_DIR / "ar3_asur_crecimiento_anual_mid_cun_oax.csv", index=False)

    print("Limpieza Sección 9 completada:")
    print(f"  - ar1_denue_merida_centro_2019_vs_2025.csv: {len(ar1_negocios)} filas")
    print(f"  - ar1_denue_resumen_manzanas_centro.csv: {len(ar1_manzanas)} manzanas")
    print(f"  - ar2_datatur_merida_turistas_mensual_2015_2026.csv: {len(ar2_mensual)} meses")
    print(f"  - ar2_datatur_merida_turistas_anual_2015_2026.csv: {len(ar2_anual)} años")
    print(f"  - ar3_asur_trafico_mensual_mid_cun_oax.csv: {len(ar3_mensual)} filas")
    print(f"  - ar3_asur_crecimiento_anual_mid_cun_oax.csv: {len(ar3_anual)} filas")


if __name__ == "__main__":
    main()
