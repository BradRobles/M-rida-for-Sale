"""
Limpieza y estandarización de datos para la sección 2-Datos-Gob-Mx.

Fuentes:
- Principal: SECTUR / DataTur, reporte 481 (ocupación en hoteles y moteles por
  centro turístico, corte mensual), centro turístico Mérida. Llegadas de
  turistas totales, residentes (nacionales) y no residentes (extranjeros),
  por categoría hotelera (1 a 5 estrellas, sin categoría, total).
- Complemento A: ASUR, `Trafico_de_pasajeros_ASUR.xlsx`, Mérida (MID),
  Cancún (CUN, aeropuerto de Playa del Carmen) y Oaxaca (OAX).

A diferencia de 9-Augmented-Reality (que usa solo el total de categorías y el
tráfico absoluto), aquí se conserva el desglose por categoría hotelera y se
calculan participación internacional, variación anual y crecimiento contra 2019.

Los crudos no se duplican: se leen de `2-Datos-Gob-Mx/raw/` y, si no están ahí,
de `9-Augmented-Reality/raw/`.
"""

from pathlib import Path
import html as htmllib
import re
import openpyxl
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent
RAW_DIR = BASE_DIR / "raw"
CLEAN_DIR = BASE_DIR / "clean"
RAW_FALLBACK = REPO_DIR / "9-Augmented-Reality" / "raw"

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
INDICADORES = {
    "Llegadas de turistas": "total",
    "Llegadas de turistas residentes": "nacionales",
    "Llegadas de turistas no residentes": "extranjeros",
}
AEROPUERTOS = {"MID": "Mérida", "CUN": "Cancún", "OAX": "Oaxaca"}


def raw_path(nombre: str) -> Path:
    for d in (RAW_DIR, RAW_FALLBACK):
        if (d / nombre).exists():
            return d / nombre
    raise FileNotFoundError(f"No se encontró {nombre} en {RAW_DIR} ni en {RAW_FALLBACK}")


def to_int(val: str):
    s = val.replace(",", "").strip()
    if not s or s in {"-", "N/D", "n/d", "ND"}:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def build_datatur() -> tuple[pd.DataFrame, pd.DataFrame]:
    html = raw_path("datatur_merida_turistas_2015_2026.html").read_text(encoding="utf-8", errors="ignore")
    table = re.findall(r"<table.*?</table>", html, re.S)[0]
    rows = []
    for r in re.findall(r"<tr.*?</tr>", table, re.S):
        cells = [" ".join(htmllib.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").split())
                 for c in re.findall(r"<t[hd][^>]*>.*?</t[hd]>", r, re.S)]
        if cells:
            rows.append(cells)
    h = next(i for i, c in enumerate(rows) if c[0] == "Concepto")
    headers = rows[h]
    meses = []
    for idx, name in enumerate(headers):
        p = name.lower().split()
        if len(p) == 2 and p[0] in MESES and p[1].isdigit():
            meses.append((idx, int(p[1]), MESES[p[0]]))

    registros, indicador = [], None
    for cells in rows[h + 1:]:
        label = cells[0]
        if label in INDICADORES:
            indicador = INDICADORES[label]
            continue
        if indicador is None or len(cells) < len(headers):
            continue
        categoria = "Total categorías" if label.lower().startswith("total categor") else label
        for idx, anio, mes in meses:
            registros.append({"anio": anio, "mes_num": mes, "categoria_hotelera": categoria,
                              "indicador": indicador, "valor": to_int(cells[idx])})
    df = pd.DataFrame(registros).dropna(subset=["valor"])
    df = df.pivot_table(index=["anio", "mes_num", "categoria_hotelera"], columns="indicador",
                        values="valor", aggfunc="first").reset_index()
    df.columns.name = None
    df = df.rename(columns={"total": "turistas_total", "nacionales": "turistas_nacionales",
                            "extranjeros": "turistas_extranjeros"})
    df["fecha"] = pd.to_datetime(dict(year=df.anio, month=df.mes_num, day=1)).dt.strftime("%Y-%m-%d")
    df["destino"] = "Mérida"
    df["pct_extranjeros"] = (100 * df["turistas_extranjeros"] / df["turistas_total"]).round(2)
    df = df[["destino", "fecha", "anio", "mes_num", "categoria_hotelera", "turistas_nacionales",
             "turistas_extranjeros", "turistas_total", "pct_extranjeros"]]

    # Validación: nacionales + extranjeros = total
    ok = df.dropna(subset=["turistas_nacionales", "turistas_extranjeros", "turistas_total"])
    diff = (ok["turistas_nacionales"] + ok["turistas_extranjeros"] - ok["turistas_total"]).abs()
    assert (diff <= 1).all(), ok[diff > 1]

    # Participación de cada categoría en el total del mes
    tot = df[df["categoria_hotelera"] == "Total categorías"].set_index("fecha")["turistas_total"]
    df["pct_del_total_mes"] = (100 * df["turistas_total"] / df["fecha"].map(tot)).round(2)
    df = df.sort_values(["fecha", "categoria_hotelera"]).reset_index(drop=True)

    anual = (df.groupby(["destino", "anio", "categoria_hotelera"], as_index=False)
             .agg(meses_reportados=("mes_num", "nunique"), turistas_nacionales=("turistas_nacionales", "sum"),
                  turistas_extranjeros=("turistas_extranjeros", "sum"), turistas_total=("turistas_total", "sum")))
    for c in ["turistas_nacionales", "turistas_extranjeros", "turistas_total"]:
        anual[c] = anual[c].astype("Int64")
        df[c] = df[c].astype("Int64")
    anual["pct_extranjeros"] = (100 * anual["turistas_extranjeros"] / anual["turistas_total"]).round(2)
    return df, anual


def build_asur() -> tuple[pd.DataFrame, pd.DataFrame]:
    wb = openpyxl.load_workbook(raw_path("Trafico_de_pasajeros_ASUR.xlsx"), read_only=True, data_only=True)
    abrev = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8,
             "sep": 9, "oct": 10, "nov": 11, "dic": 12}
    registros, totales = [], []
    for code, nombre in AEROPUERTOS.items():
        ws = wb[f"PAX {code}"]
        anio = None
        for row in ws.iter_rows(min_row=8, values_only=True):
            _, c_anio, c_mes, nac, intl, tot = (list(row) + [None] * 6)[:6]
            if c_anio is not None:
                txt = str(c_anio).strip()
                if txt.startswith("Total"):
                    if tot is not None:
                        totales.append((code, int(txt.split()[-1]), int(round(tot))))
                    continue
                if txt.isdigit():
                    anio = int(txt)
            if anio is None or c_mes is None or tot is None:
                continue
            m = abrev.get(str(c_mes).split("/")[0].strip().lower()[:3])
            if m is None:
                continue
            registros.append({"aeropuerto_codigo": code, "aeropuerto": nombre, "anio": anio, "mes_num": m,
                              "pasajeros_nacional": int(round(nac or 0)), "pasajeros_internacional": int(round(intl or 0)),
                              "pasajeros_total": int(round(tot))})
    df = pd.DataFrame(registros).drop_duplicates(["aeropuerto_codigo", "anio", "mes_num"], keep="last")
    assert len(df), "No se pudo leer el formato de ASUR"
    assert ((df.pasajeros_nacional + df.pasajeros_internacional - df.pasajeros_total).abs() <= 1).all()
    # Validación: la suma de los meses = renglón "Total AAAA" que trae el propio archivo de ASUR
    #             (se reporta, no se corrige: en algunos años el renglón del archivo no cuadra con sus meses)
    suma = df.groupby(["aeropuerto_codigo", "anio"])["pasajeros_total"].sum()
    qa = pd.DataFrame(totales, columns=["aeropuerto_codigo", "anio", "total_renglon_asur"])
    qa["suma_de_meses"] = [int(suma.get((c, a), 0)) for c, a in zip(qa.aeropuerto_codigo, qa.anio)]
    qa["diferencia"] = qa.suma_de_meses - qa.total_renglon_asur
    qa["cuadra"] = qa.diferencia.abs() <= 2
    qa.to_csv(CLEAN_DIR / "asur_validacion_totales_anuales.csv", index=False)
    df = df[df.pasajeros_total > 0].sort_values(["aeropuerto_codigo", "anio", "mes_num"]).reset_index(drop=True)
    df["fecha"] = pd.to_datetime(dict(year=df.anio, month=df.mes_num, day=1)).dt.strftime("%Y-%m-%d")
    df["pct_internacional"] = (100 * df.pasajeros_internacional / df.pasajeros_total).round(2)
    prev = df.set_index(["aeropuerto_codigo", "anio", "mes_num"])["pasajeros_total"]
    df["variacion_anual_pct"] = [
        round(100 * (t / prev[(c, a - 1, m)] - 1), 2) if (c, a - 1, m) in prev.index else None
        for c, a, m, t in zip(df.aeropuerto_codigo, df.anio, df.mes_num, df.pasajeros_total)]
    base19 = df[df.anio == 2019].set_index(["aeropuerto_codigo", "mes_num"])["pasajeros_total"]
    df["indice_mismo_mes_2019_100"] = [
        round(100 * t / base19[(c, m)], 1) if (c, m) in base19.index else None
        for c, m, t in zip(df.aeropuerto_codigo, df.mes_num, df.pasajeros_total)]
    df = df[["aeropuerto_codigo", "aeropuerto", "fecha", "anio", "mes_num", "pasajeros_nacional",
             "pasajeros_internacional", "pasajeros_total", "pct_internacional", "variacion_anual_pct",
             "indice_mismo_mes_2019_100"]]

    # Comparación año contra año usando solo los meses disponibles del último año (2026 es parcial)
    ultimo = df.anio.max()
    meses_ult = set(df[df.anio == ultimo].mes_num)
    ytd = (df[df.mes_num.isin(meses_ult)].groupby(["aeropuerto_codigo", "aeropuerto", "anio"], as_index=False)
           .agg(meses=("mes_num", "nunique"), pasajeros_nacional=("pasajeros_nacional", "sum"),
                pasajeros_internacional=("pasajeros_internacional", "sum"), pasajeros_total=("pasajeros_total", "sum")))
    ytd = ytd[ytd.meses == len(meses_ult)]
    ytd["periodo"] = f"enero-{[k for k, v in MESES.items() if v == max(meses_ult)][0]}"
    ytd["pct_internacional"] = (100 * ytd.pasajeros_internacional / ytd.pasajeros_total).round(2)
    ytd["variacion_anual_pct"] = ytd.groupby("aeropuerto_codigo")["pasajeros_total"].pct_change().mul(100).round(2)
    return df, ytd


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    mensual, anual = build_datatur()
    mensual.to_csv(CLEAN_DIR / "datatur_merida_llegadas_categoria_mensual_2015_2026.csv", index=False)
    anual.to_csv(CLEAN_DIR / "datatur_merida_llegadas_categoria_anual_2015_2026.csv", index=False)
    asur, ytd = build_asur()
    asur.to_csv(CLEAN_DIR / "asur_pasajeros_mensual_mid_cun_oax.csv", index=False)
    ytd.to_csv(CLEAN_DIR / "asur_pasajeros_acumulado_mismo_periodo_mid_cun_oax.csv", index=False)
    print(mensual.categoria_hotelera.value_counts().to_string())
    print(anual[anual.categoria_hotelera == "Total categorías"].tail(4).to_string(index=False))
    print(ytd[ytd.anio >= 2024].to_string(index=False))


if __name__ == "__main__":
    main()
