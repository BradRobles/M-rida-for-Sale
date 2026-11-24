"""
Limpieza y estandarización de datos para la sección 3-SIEGY-Yucatan.

Fuentes:
- Principal (respaldo de SIEGY): Sefotur, "Resultados de la actividad turística"
  (mensual, con datos de DataTur, ASUR y AAFY). Aporta lo que no está en el
  reporte de DataTur de la sección 2: ocupación hotelera de Mérida, turistas del
  estado por origen e ingreso hotelero estatal.
- Complemento A: SHF, Índice SHF de Precios de la Vivienda (precio promedio y
  percentiles por estado; fichas trimestrales del IIEG con datos de SHF).
- Complemento B: INEGI, ENOE y Pobreza Laboral, boletines de Yucatán 2T2026.

Los reportes oficiales son PDF; `raw/` guarda la transcripción de cada cifra con
el reporte y la URL de donde se copió. Además se validan las cifras de Sefotur
contra los crudos de DataTur y ASUR de la sección 2.

Este script únicamente limpia y exporta tablas CSV; no genera gráficos.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent
RAW_DIR = BASE_DIR / "raw"
CLEAN_DIR = BASE_DIR / "clean"
SEC2_CLEAN = REPO_DIR / "2-Datos-Gob-Mx" / "clean"


def load_sefotur() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "sefotur_cifras_transcritas.csv")
    assert not df.duplicated(["mes_referencia", "indicador", "geografia"]).any()
    df["fecha"] = df["mes_referencia"] + "-01"
    return df


def wide(df: pd.DataFrame, indicadores: list[str], geo: str) -> pd.DataFrame:
    sub = df[df.indicador.isin(indicadores) & (df.geografia == geo)]
    w = sub.pivot(index="fecha", columns="indicador", values="valor").reset_index()
    urls = sub.groupby("fecha")["url"].apply(lambda s: " | ".join(sorted(set(s))))
    w["fuente_url"] = w["fecha"].map(urls)
    w.columns.name = None
    return w.sort_values("fecha").reset_index(drop=True)


def build_sefotur(df: pd.DataFrame):
    ocup = wide(df, ["ocupacion_hotelera"], "Ciudad de Mérida").rename(columns={"ocupacion_hotelera": "ocupacion_hotelera_pct"})
    ocup.insert(0, "destino", "Mérida")
    # Validación: el promedio de los 12 meses de 2025 = 57.8, acumulado anual impreso por Sefotur
    assert round(ocup[ocup.fecha.str.startswith("2025")].ocupacion_hotelera_pct.mean(), 1) == 57.8

    origen = wide(df, ["turistas_pernocta_total", "turistas_pernocta_nacionales", "turistas_pernocta_internacionales",
                       "pct_turistas_internacionales"], "Yucatán (estado)")
    origen = origen.rename(columns={"turistas_pernocta_total": "turistas_total",
                                    "turistas_pernocta_nacionales": "turistas_nacionales",
                                    "turistas_pernocta_internacionales": "turistas_internacionales",
                                    "pct_turistas_internacionales": "pct_internacionales_publicado"})
    ok = origen.dropna(subset=["turistas_nacionales"])
    assert ((ok.turistas_nacionales + ok.turistas_internacionales) == ok.turistas_total).all()
    origen["pct_internacionales"] = (100 * origen.turistas_internacionales / origen.turistas_total).round(1)
    origen["pct_internacionales"] = origen["pct_internacionales"].fillna(origen["pct_internacionales_publicado"])
    origen["metodo_pct"] = [
        "calculado con conteos impresos" if pd.notna(i) else ("porcentaje impreso (sin conteo)" if pd.notna(p) else "sin desglose publicado")
        for i, p in zip(origen.turistas_internacionales, origen.pct_internacionales_publicado)]
    origen.insert(0, "geografia", "Yucatán (estado)")
    origen = origen[["geografia", "fecha", "turistas_total", "turistas_nacionales", "turistas_internacionales",
                     "pct_internacionales", "metodo_pct", "fuente_url"]]
    for c in ["turistas_total", "turistas_nacionales", "turistas_internacionales"]:
        origen[c] = origen[c].astype("Int64")

    ingreso = wide(df, ["ingreso_hotelero"], "Yucatán (estado)").rename(columns={"ingreso_hotelero": "ingreso_hotelero_mdp"})
    ingreso.insert(0, "geografia", "Yucatán (estado)")
    ingreso["nota"] = "Fuente original AAFY; Sefotur lo publica con un mes de rezago (aquí va en su mes real)"
    return ocup, origen, ingreso


def build_validacion(df: pd.DataFrame) -> pd.DataFrame:
    """Compara las cifras de Sefotur con los crudos oficiales de DataTur y ASUR (sección 2)."""
    filas = []
    cum = df[df.indicador == "turistas_pernocta_acumulado_ene_mes"].sort_values("fecha").copy()
    cum["anio"] = cum.fecha.str[:4]
    cum["valor_mes"] = cum.groupby("anio")["valor"].diff().fillna(cum["valor"])
    dt = pd.read_csv(SEC2_CLEAN / "datatur_merida_llegadas_categoria_mensual_2015_2026.csv")
    dt = dt[dt.categoria_hotelera == "Total categorías"].set_index("fecha")["turistas_total"]
    for f, v in zip(cum.fecha, cum.valor_mes):
        filas.append({"fecha": f, "indicador": "Turistas con pernocta, Mérida (Sefotur: diferencia de acumulados)",
                      "valor_sefotur": int(v), "valor_fuente_original": dt.get(f), "fuente_original": "DataTur reporte 481"})
    asur = pd.read_csv(SEC2_CLEAN / "asur_pasajeros_mensual_mid_cun_oax.csv")
    asur = asur[asur.aeropuerto_codigo == "MID"].set_index("fecha")["pasajeros_total"]
    for f, v in df[df.indicador == "pasajeros_aeropuerto_mid"][["fecha", "valor"]].values:
        filas.append({"fecha": f, "indicador": "Pasajeros aeropuerto MID", "valor_sefotur": int(v),
                      "valor_fuente_original": asur.get(f), "fuente_original": "ASUR Trafico_de_pasajeros_ASUR.xlsx"})
    val = pd.DataFrame(filas)
    val["valor_fuente_original"] = val["valor_fuente_original"].astype("Int64")
    val["diferencia"] = val["valor_sefotur"] - val["valor_fuente_original"]
    val["coincide"] = val["diferencia"] == 0
    return val.sort_values(["indicador", "fecha"]).reset_index(drop=True)


def build_shf() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "shf_iieg_cifras_transcritas.csv")
    assert (df.p25_mxn <= df.mediana_mxn).all() and (df.mediana_mxn <= df.p75_mxn).all()
    df["razon_p75_p25"] = (df.p75_mxn / df.p25_mxn).round(2)
    nac = df[df.entidad == "Nacional"].set_index("trimestre")["mediana_mxn"]
    df["mediana_vs_nacional_pct"] = (100 * (df.mediana_mxn / df.trimestre.map(nac) - 1)).round(1)
    df["lugar_nacional"] = df["lugar_nacional"].astype("Int64")
    df["nota"] = ("Precio promedio y percentiles dependen de qué viviendas se valuaron en el trimestre: "
                  "no usar como índice de tendencia. Ciudad comparada: Quintana Roo = Playa del Carmen, "
                  "Guanajuato = San Miguel de Allende, Oaxaca = Oaxaca de Juárez (solo hay dato estatal).")
    cols = ["trimestre", "entidad", "precio_promedio_mxn", "mediana_mxn", "p25_mxn", "p75_mxn", "razon_p75_p25",
            "mediana_vs_nacional_pct", "lugar_nacional", "fuente", "url", "nota"]
    return df[cols].sort_values(["entidad", "trimestre"]).reset_index(drop=True)


def build_enoe() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "inegi_enoe_cifras_transcritas.csv").rename(columns={"2025T2": "valor_2025T2", "2026T2": "valor_2026T2"})
    ocupados = df.set_index("indicador").loc["Población ocupada"]
    tramos = df.indicador.str.startswith("Ocupados")
    for t in ["valor_2025T2", "valor_2026T2"]:
        assert df.loc[tramos, t].sum() == ocupados[t], t  # tramos de ingreso suman la población ocupada
        df.loc[tramos, f"pct_ocupados_{t[-6:]}"] = (100 * df.loc[tramos, t] / ocupados[t]).round(1)
    df["cambio"] = (df.valor_2026T2 - df.valor_2025T2).round(2)
    for t in ["valor_2025T2", "valor_2026T2", "cambio"]:
        df[t] = df[t].map(lambda v: str(int(v)) if float(v).is_integer() else str(v))
    return df[["geografia", "indicador", "unidad", "valor_2025T2", "valor_2026T2", "cambio",
               "pct_ocupados_2025T2", "pct_ocupados_2026T2", "fuente", "url"]]


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    df = load_sefotur()
    ocup, origen, ingreso = build_sefotur(df)
    ocup.to_csv(CLEAN_DIR / "sefotur_merida_ocupacion_hotelera_mensual.csv", index=False)
    origen.to_csv(CLEAN_DIR / "sefotur_yucatan_turistas_origen_mensual.csv", index=False)
    ingreso.to_csv(CLEAN_DIR / "sefotur_yucatan_ingreso_hotelero_mensual.csv", index=False)
    val = build_validacion(df)
    val.to_csv(CLEAN_DIR / "sefotur_validacion_vs_datatur_asur.csv", index=False)
    build_shf().to_csv(CLEAN_DIR / "shf_precios_vivienda_trimestral_estados.csv", index=False)
    build_enoe().to_csv(CLEAN_DIR / "enoe_yucatan_2025T2_vs_2026T2.csv", index=False)
    print(val.groupby("indicador")["coincide"].agg(["sum", "count"]))


if __name__ == "__main__":
    main()
