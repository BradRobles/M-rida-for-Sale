"""Valida las cifras clave del Dashboard v1 contra las tablas gold de dashboard/data/.

Correr antes: python dashboard/prep.py
"""
import json
from pathlib import Path

import pandas as pd
import pytest

DATA = Path(__file__).resolve().parent.parent / "data"


def csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name, encoding="utf-8")


@pytest.fixture(scope="module")
def k() -> dict:
    t = csv("kpis.csv")
    return dict(zip(t["key"], t["value"]))


def test_hotel_tourists(k):
    assert k["tourists_2019"] == 1_737_810
    assert k["tourists_2025"] == 2_261_866
    assert round(k["tourists_change_pct"], 1) == 30.2
    assert k["pct_foreign_2025"] == pytest.approx(19.6)


def test_airports():
    a = csv("airports_annual.csv")
    a25 = a[a["year"] == 2025].set_index("code")
    assert a25.loc["MID", "total"] == 3_939_692
    assert round(a25.loc["MID", "index_2019"], 1) == 141.2
    assert round(a25.loc["OAX", "index_2019"], 1) == 155.9
    assert round(a25.loc["CUN", "index_2019"], 1) == 115.2
    assert a25.loc["MID", "pct_international"] == pytest.approx(10.2)
    assert a25.loc["OAX", "pct_international"] == pytest.approx(14.6)
    assert a25.loc["CUN", "pct_international"] == pytest.approx(66.3)


def test_businesses():
    s = csv("shops_change.csv").set_index(["area", "category"])
    centro = s.loc[("Centro", "All businesses")]
    assert (centro["n_2019"], centro["n_2025"], centro["pct_change"]) == (9199, 8010, -12.9)
    cafes = s.loc[("Municipality", "Coffee shops")]
    assert (cafes["n_2019"], cafes["n_2025"], cafes["pct_change"]) == (641, 938, 46.3)
    lodging = s.loc[("Municipality", "Lodging")]
    assert (lodging["n_2019"], lodging["n_2025"]) == (304, 311)


def test_ageb_cafes(k):
    assert k["ageb_gained_cafes"] == 212
    g = json.loads((DATA / "ageb_cafes.geojson").read_text(encoding="utf-8"))
    assert len(g["features"]) == 541


def test_licenses():
    lic = csv("licenses_centro.csv").groupby("year")["licenses"].sum()
    assert lic[2015] == 56
    assert lic[2025] == 195


def test_lodging_tax(k):
    assert k["tax_2019"] == 61_443_782
    assert k["tax_2025"] == 196_898_896
    assert k["tax_index_2025"] == pytest.approx(320.5)
    assert round(k["tax_ratio"], 1) == 3.2


def test_housing(k):
    assert k["shf_yucatan_vs_national_pct"] == pytest.approx(39.0)
    assert k["shf_yucatan_rank"] == 4
    assert k["low_wage_workers"] == 619_805
    assert k["employed"] == 1_255_687
    assert k["low_wage_pct"] == pytest.approx(49.4)


def test_press():
    p = csv("press_share.csv").set_index("year")
    assert p.loc[2019, "pct_core"] == pytest.approx(11.2)
    assert p.loc[2025, "pct_core"] == pytest.approx(31.5)
    # El prompt esperaba 331 notas. La regla escrita tal cual da 332: la diferencia es una nota de 2026
    # (40 de 179 = 22.3% contra 21.8% del prototipo). 2019 y 2025 sí coinciden. Ver dashboard/README.md.
    assert p["core"].sum() == 332


def test_youtube(k):
    assert k["yt_videos"] == 349
    assert k["yt_views"] == 5_352_564
    assert k["yt_comments_read"] == 6216


def test_gdelt():
    g = csv("gdelt_voices.csv").set_index("voice")["articles"]
    assert (g["Local"], g["National"], g["International"]) == (296, 279, 80)


def test_blocks_3d():
    b = csv("blocks_3d.csv")
    assert len(b) == 831
    assert round(100 * (b["altura_p90_m"] <= 8).mean(), 1) == 92.2
    g = json.loads((DATA / "blocks_3d.geojson").read_text(encoding="utf-8"))
    assert len(g["features"]) == 831
    assert (DATA / "blocks_3d.geojson").stat().st_size < 10e6


def test_wikipedia():
    w = csv("wikipedia_index.csv").set_index("city")["index_2025"].round(0)
    assert (w["Mérida"], w["Oaxaca"], w["San Miguel de Allende"], w["Playa del Carmen"]) == (95, 85, 57, 52)


def test_no_hardcoded_style_outside_theme():
    """Colores (hex) y nombres de fuente viven solo en theme.py."""
    import re
    import sys
    root = DATA.parent
    sys.path.insert(0, str(root))
    import theme
    for f in ["app.py", "charts.py", "prep.py"]:
        src = (root / f).read_text(encoding="utf-8")
        assert not re.search(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b", src), f"hex en {f}"
        assert theme.FONT_TITLE not in src and theme.FONT_BODY not in src, f"fuente en {f}"
