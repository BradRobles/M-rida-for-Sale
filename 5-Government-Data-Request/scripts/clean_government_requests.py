"""
Limpieza y estandarización de datos para la sección 5-Government-Data-Request.

Fuentes:
1. AAFY (Folio 1191207426000093): Recaudación mensual del Impuesto por la
   Prestación de Servicios de Hospedaje (enero 2015 – septiembre 2026).
2. Ayuntamiento de Mérida (Folio 1190579126000609 / Dirección de Finanzas y
   Tesorería Municipal): Licencias de funcionamiento emitidas en la zona Centro
   (enero 2015 – septiembre 2026).

Este script únicamente realiza limpieza, validación y exportación de tablas
listas para su uso posterior en visualizaciones.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_EXCEL = BASE_DIR / "raw" / "609" / "licencias para transparencia 2015-2026.xls"
CLEAN_DIR = BASE_DIR / "clean"

MESES_ES = [
    (1, "enero"),
    (2, "febrero"),
    (3, "marzo"),
    (4, "abril"),
    (5, "mayo"),
    (6, "junio"),
    (7, "julio"),
    (8, "agosto"),
    (9, "septiembre"),
    (10, "octubre"),
    (11, "noviembre"),
    (12, "diciembre"),
]

# Transcripción exacta del oficio AAFY/DR/R/AD/0191/2026 (Folio 1191207426000093).
# Cifras en pesos mexicanos (MXN). 2015-2025: cifras definitivas; 2026: cifras previas (ene-sep).
AAFY_HOSPEDAJE_MXN = {
    2015: [2671270, 2293360, 2500664, 2510571, 2519391, 2249341, 2072006, 2623489, 2430260, 1964819, 2735715, 3050996],
    2016: [3478862, 3008627, 3010700, 3436027, 2855548, 2599029, 2378922, 3435065, 2883292, 2501561, 3117995, 3626932],
    2017: [4309991, 3643460, 3878524, 4008053, 3925767, 3148019, 3051234, 3951599, 3599896, 2932543, 3901152, 3712387],
    2018: [4348788, 3730599, 3964727, 4490365, 4065101, 3463288, 3576967, 5198780, 4458182, 3679945, 4341520, 5539003],
    2019: [5528974, 5071590, 5068500, 5472803, 5297079, 4579527, 4414835, 5546317, 4937849, 4530337, 5267831, 5728140],
    2020: [5657434, 8941985, 8835863, 461147, 61872, 51089, 127079, 2007068, 2024308, 2753666, 4096447, 3938567],
    2021: [5041360, 4508044, 4181724, 5994958, 5636804, 6463187, 6328670, 8779443, 7263749, 6535187, 8359429, 11809204],
    2022: [11202313, 10331060, 9922831, 11728077, 11134642, 9945803, 11196163, 12483656, 11366309, 10684532, 13488145, 13726595],
    2023: [14752778, 13587848, 14002882, 15588680, 13925231, 12505186, 11614864, 14680773, 13598870, 10779579, 13991546, 15324632],
    2024: [15308924, 15818473, 16090261, 16750094, 14844064, 13010031, 12399139, 13544517, 14205839, 12382829, 14878953, 17612137],
    2025: [17181838, 17239964, 16991252, 17746000, 15075887, 13542804, 14086552, 16086465, 18251188, 15865876, 15799923, 19031147],
    2026: [17577311, 17069014, 16121972, 17062489, 14528181, 13892942, 12281266, 14479025, 14591083, None, None, None],
}

GIROS_HOSPEDAJE = {
    "HOSTAL",
    "HOTEL",
    "HOTEL BOUTIQUE",
    "MOTEL",
    "POSADA",
}

GIROS_ALIMENTOS_BEBIDAS = {
    "BAR",
    "CAFETERIA",
    "RESTAURANTE DE COMIDA RAPIDA",
    "RESTAURANTE DE COMIDA TIPICA",
    "RESTAURANTE DE PRIMERA A",
    "RESTAURANTE DE PRIMERA B",
    "RESTAURANTE DE PRIMERA C",
    "RESTAURANTE DE SEGUNDA A",
    "RESTAURANTE DE SEGUNDA B",
    "RESTAURANTE DE SEGUNDA C",
    "VIDEO BAR",
}

GIRO_NORMALIZACION = {
    "LIBRERIA": "LIBRERÍA",
}


def clean_text(val: object) -> str:
    """Normaliza espacios en blanco y mayúsculas; devuelve cadena vacía para nulos."""
    if pd.isna(val):
        return ""
    return " ".join(str(val).strip().split())


def classify_giro(giro: str) -> str:
    """Asigna una macro-categoría útil para análisis de turistificación."""
    if giro in GIROS_HOSPEDAJE:
        return "Hospedaje"
    if giro in GIROS_ALIMENTOS_BEBIDAS:
        return "Alimentos y Bebidas"
    if giro == "NO ESPECIFICADO":
        return "No especificado"
    return "Comercio y otros servicios"


def build_aafy_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye las tablas mensual y anual del Impuesto sobre Hospedaje (AAFY)."""
    rows = []
    for anio, valores in sorted(AAFY_HOSPEDAJE_MXN.items()):
        tipo_cifra = "preliminar" if anio == 2026 else "definitiva"
        for (mes_num, mes_nombre), monto in zip(MESES_ES, valores):
            if monto is None:
                continue
            rows.append(
                {
                    "anio": anio,
                    "mes_num": mes_num,
                    "mes": mes_nombre,
                    "fecha": f"{anio:04d}-{mes_num:02d}-01",
                    "recaudacion_mxn": int(monto),
                    "tipo_cifra": tipo_cifra,
                }
            )

    df_mensual = pd.DataFrame(rows)

    df_anual = (
        df_mensual.groupby(["anio", "tipo_cifra"], as_index=False)
        .agg(
            meses_reportados=("mes_num", "count"),
            recaudacion_total_mxn=("recaudacion_mxn", "sum"),
            promedio_mensual_mxn=("recaudacion_mxn", "mean"),
        )
        .sort_values("anio")
    )
    df_anual["promedio_mensual_mxn"] = df_anual["promedio_mensual_mxn"].round(2)
    return df_mensual, df_anual


def build_ayuntamiento_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Limpia y estandariza el padrón de licencias de funcionamiento (2015-2026)."""
    xls = pd.ExcelFile(RAW_EXCEL)
    frames = []
    for sheet in xls.sheet_names:
        df_sheet = pd.read_excel(xls, sheet_name=sheet)
        # La hoja 2026 tiene '2026' como nombre de la primera columna en lugar de 'Fecha Registro'
        if 2026 in df_sheet.columns:
            df_sheet = df_sheet.rename(columns={2026: "Fecha Registro"})
        df_sheet["anio_hoja"] = int(sheet)
        frames.append(df_sheet)

    raw_df = pd.concat(frames, ignore_index=True)

    fecha_reg = pd.to_datetime(raw_df["Fecha Registro"])
    vigencia = pd.to_datetime(raw_df["Vigencia"])

    nombre = raw_df["Nombre"].map(clean_text)
    ap_pat = raw_df["Apell Paterno"].map(clean_text)
    ap_mat = raw_df["Apell Materno"].map(clean_text)

    tipo_persona = pd.Series(
        ["FISICA" if (p or m) else "MORAL" for p, m in zip(ap_pat, ap_mat)],
        index=raw_df.index,
    )

    giro = raw_df["Giro Desarrollo Urbano"].map(clean_text).replace("", "NO ESPECIFICADO")
    giro = giro.replace(GIRO_NORMALIZACION)

    cleaned = pd.DataFrame(
        {
            "fecha_registro": fecha_reg.dt.strftime("%Y-%m-%d"),
            "anio": fecha_reg.dt.year,
            "mes_num": fecha_reg.dt.month,
            "fecha_mes": fecha_reg.dt.strftime("%Y-%m-01"),
            "vigencia": vigencia.dt.strftime("%Y-%m-%d"),
            "tipo_persona": tipo_persona,
            "direccion_catastro": raw_df["Dirección Catastro"].map(clean_text),
            "colonia": raw_df["Colonia"].map(clean_text),
            "denominacion": raw_df["Denominacion"].map(clean_text),
            "giro_desarrollo_urbano": giro,
            "categoria_giro": giro.map(classify_giro),
        }
    )

    # Separar registros fuera de la colonia Centro (ej. CENTRO POBLACION DZUNUNCAN)
    mask_centro = cleaned["colonia"] == "CENTRO"
    df_centro = cleaned[mask_centro].sort_values(["fecha_registro", "denominacion"]).reset_index(drop=True)
    df_excluidas = cleaned[~mask_centro].reset_index(drop=True)

    df_resumen_anual = (
        df_centro.groupby(["anio", "categoria_giro"], as_index=False)
        .agg(licencias_emitidas=("denominacion", "count"))
        .sort_values(["anio", "categoria_giro"])
        .reset_index(drop=True)
    )

    return df_centro, df_excluidas, df_resumen_anual


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    aafy_mensual, aafy_anual = build_aafy_datasets()
    aafy_mensual.to_csv(CLEAN_DIR / "aafy_impuesto_hospedaje_mensual_2015_2026.csv", index=False)
    aafy_anual.to_csv(CLEAN_DIR / "aafy_impuesto_hospedaje_anual_2015_2026.csv", index=False)

    lic_centro, lic_excluidas, lic_resumen = build_ayuntamiento_datasets()
    lic_centro.to_csv(CLEAN_DIR / "ayuntamiento_licencias_funcionamiento_centro_2015_2026.csv", index=False)
    lic_excluidas.to_csv(CLEAN_DIR / "ayuntamiento_licencias_excluidas_fuera_centro.csv", index=False)
    lic_resumen.to_csv(CLEAN_DIR / "ayuntamiento_licencias_resumen_anual_centro_2015_2026.csv", index=False)

    print("Limpieza completada:")
    print(f"  - aafy_impuesto_hospedaje_mensual_2015_2026.csv: {len(aafy_mensual)} filas")
    print(f"  - aafy_impuesto_hospedaje_anual_2015_2026.csv: {len(aafy_anual)} filas")
    print(f"  - ayuntamiento_licencias_funcionamiento_centro_2015_2026.csv: {len(lic_centro)} filas")
    print(f"  - ayuntamiento_licencias_excluidas_fuera_centro.csv: {len(lic_excluidas)} filas")
    print(f"  - ayuntamiento_licencias_resumen_anual_centro_2015_2026.csv: {len(lic_resumen)} filas")


if __name__ == "__main__":
    main()
