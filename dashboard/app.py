"""Mérida for Sale · Dashboard v1. Una sola página con portada y cinco capítulos.

    streamlit run dashboard/app.py

Lee solo dashboard/data/ (generado por prep.py).
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

import charts as C
import theme as T

DATA = Path(__file__).resolve().parent / "data"
REPO_URL = "https://github.com/BradRobles/M-rida-for-Sale/blob/main"

st.set_page_config(page_title=T.APP_TITLE, layout="wide", initial_sidebar_state="collapsed")
st.html(T.css())


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
@st.cache_data
def csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name, encoding="utf-8")


@st.cache_data
def geojson(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@st.cache_data
def kpi() -> dict[str, float]:
    k = csv("kpis.csv")
    return dict(zip(k["key"], k["value"]))


K = kpi()


def minus(s: str) -> str:
    return s.replace("-", "−")


def pct(v: float, nd: int = 1, sign: bool = True) -> str:
    return minus(f"{v:+.{nd}f}%" if sign else f"{v:.{nd}f}%")


def chips(*names: str) -> str:
    return '<div class="mfs-chips">' + "".join(f"<span>{escape(n)}</span>" for n in names) + "</div>"


def card(label: str, big: str, sub: str, color: str) -> str:
    return (f'<div class="mfs-card"><span class="lbl">{label}</span>'
            f'<span class="big" style="color:{color}">{big}</span><span class="sub">{sub}</span></div>')


def fig_head(title: str, sub: str = "") -> None:
    st.html(f'<div><p class="mfs-fig-title">{title}</p><span class="mfs-fig-sub">{sub}</span></div>')


def section(anchor: str, number: str, title: str, body: str) -> None:
    st.html(f'<div id="{anchor}" class="mfs-section"><span class="mfs-eyebrow">Chapter {number}</span>'
            f'<h2 class="mfs-h2">{title}</h2><p class="mfs-body">{body}</p></div>')


def plot(fig, alt: str, key: str | None = None) -> None:
    st.plotly_chart(fig, config=C.PLOTLY_CONFIG, alt=alt, key=key)


# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------
nav = "".join(f'<a href="#{a}">{label}</a>' for a, label in T.CHAPTERS)
st.html(f'<nav class="mfs-nav" aria-label="Chapters"><a class="mfs-brand" href="#top">Mérida for Sale</a>'
        f'<div style="display:flex;flex-wrap:wrap;gap:0 18px">{nav}</div></nav>')

hero, panel = st.columns([1.7, 1], gap="large", vertical_alignment="bottom")
with hero:
    st.html(f'<div id="top"><span class="mfs-eyebrow">{T.EYEBROW}</span>'
            f'<div class="mfs-hero">Mérida<br>for Sale</div><p class="mfs-lede">{T.LEDE}</p>'
            f'<p class="mfs-byline">By <b>{"</b>, <b>".join(T.TEAM[:-1])}</b> and <b>{T.TEAM[-1]}</b></p></div>')
with panel:
    st.html(
        '<div class="mfs-kpi-panel"><span class="mfs-eyebrow">The story in four numbers</span><div class="mfs-kpi-grid">'
        f'<div><b>{pct(K["tourists_change_pct"], 0)}</b><span>hotel tourists, 2019 to 2025</span></div>'
        f'<div><b>{pct(K["centro_businesses_change_pct"])}</b><span>businesses in the Centro</span></div>'
        f'<div><b>×{K["tax_ratio"]:.1f}</b><span>lodging tax collected</span></div>'
        f'<div><b>{pct(K["shf_yucatan_vs_national_pct"], 0)}</b><span>Yucatán home prices above national</span></div>'
        '</div></div>')

# ---------------------------------------------------------------------------
# 01 The arrival
# ---------------------------------------------------------------------------
tour = csv("tourists_annual.csv")
air = csv("airports_annual.csv")
mid = air[(air["code"] == "MID") & (air["year"] == 2025)].iloc[0]

section("arrival", "01", "The arrival",
        f"Hotels in Mérida received {K['tourists_2025'] / 1e6:.2f} million tourists in 2025, "
        f"{K['tourists_change_pct']:.0f}% more than before the pandemic. One in five comes from abroad, a share that "
        "has barely moved: the growth is national and foreign alike.")
left, right = st.columns([1, 1.75], gap="large")
with left:
    st.html('<div class="mfs-cards">'
            + card("Hotel tourists, 2025", f"{K['tourists_2025'] / 1e6:.2f}M", f"{K['pct_foreign_2025']:.1f}% foreign",
                   T.COLOR_MERIDA)
            + card("MID airport, 2025", f"{mid['total'] / 1e6:.2f}M",
                   f"passengers, {pct(mid['index_2019'] - 100, 0)} vs 2019", T.COLOR_GROWTH)
            + "</div>" + chips("DataTur (datos.gob.mx)", "ASUR", "Sefotur"))
with right:
    fig_head("Tourists staying in Mérida hotels, per year", "Millions · 2026* = Jan to Sep")
    plot(C.tourists_stacked(tour),
         "Stacked bars of yearly hotel tourists in Mérida, 2015 to 2026, national and foreign. "
         f"From {tour.iloc[0]['total'] / 1e6:.2f} million in 2015 to a record {K['tourists_2025'] / 1e6:.2f} million in 2025.")

monthly = csv("tourists_monthly_category.csv")
fig_head("Monthly arrivals by hotel category", "DataTur, January 2015 to September 2026")
cat = st.segmented_control("Hotel category", ["All categories", "5 stars", "4 stars", "3 stars", "2 stars", "1 star"],
                           default="All categories", required=True, key="hotel_cat", label_visibility="collapsed")
plot(C.tourists_monthly(monthly, cat), f"Monthly national and foreign hotel arrivals in Mérida, {cat}.")

# ---------------------------------------------------------------------------
# 02 The Centro empties out
# ---------------------------------------------------------------------------
shops = csv("shops_change.csv")
cafes_mun = shops[(shops["area"] == "Municipality") & (shops["category"] == "Coffee shops")].iloc[0]
section("shops", "02", "The Centro empties out",
        f"Between 2019 and 2025 the Centro Histórico lost {abs(K['centro_businesses_2025'] - K['centro_businesses_2019']):,.0f} "
        f"businesses while the rest of the city gained them. Coffee shops are the exception: up "
        f"{cafes_mun['pct_change']:.0f}% citywide, spreading to {K['ageb_gained_cafes']:.0f} neighbourhoods (AGEBs) "
        "outside the old core.")
left, right = st.columns([1, 1.75], gap="large")
with left:
    area_label = st.segmented_control("Area", ["Centro Histórico", "Whole municipality"], default="Centro Histórico",
                                      required=True, key="area")
    area = "Centro" if area_label == "Centro Histórico" else "Municipality"
    tot = shops[(shops["area"] == area) & (shops["category"] == "All businesses")].iloc[0]
    st.html(chips("INEGI DENUE 2019 and 2025", "Ayuntamiento licenses", "GeoPortal de Mérida"))
with right:
    fig_head("Change in businesses, 2019 to 2025",
             f"{area_label}: {tot['n_2019']:,} → {tot['n_2025']:,} businesses · hover for counts")
    plot(C.shops_diverging(shops, area), f"Percent change in businesses by category, 2019 to 2025, {area_label}.")

left, right = st.columns([1.2, 1], gap="large")
with left:
    fig_head("Where coffee shops opened or closed", "Change in coffee shops per AGEB, 2019 to 2025 · black outline = Centro Histórico")
    plot(C.cafe_map(geojson("ageb_cafes.geojson"), csv("ageb_cafes.csv").astype({"cvegeo": str}),
                    geojson("centro_historico.geojson")),
         "Map of Mérida AGEBs coloured by the change in coffee shops between 2019 and 2025, with the Centro outlined.")
with right:
    lic = csv("licenses_centro.csv")
    fig_head("New operating licenses in the Centro, per year", "Fewer businesses, more turnover · 2026* = Jan to Sep")
    plot(C.licenses_stacked(lic), "New business licenses in the Centro by type, 2015 to 2026.")

# ---------------------------------------------------------------------------
# 03 The invisible hotel
# ---------------------------------------------------------------------------
lodging = shops[(shops["area"] == "Municipality") & (shops["category"] == "Lodging")].iloc[0]
section("homes", "03", "The invisible hotel",
        f"Registered lodging barely changed: {lodging['n_2019']} places in 2019, {lodging['n_2025']} in 2025. Yet the "
        f"state collected {K['tax_ratio']:.1f} times more lodging tax. The gap points to homes rented by the night, the "
        "part of the hotel industry the business directory cannot see.")
left, right = st.columns([1, 1.75], gap="large")
with left:
    st.html('<div class="mfs-cards">'
            + card("Median home price, 2025 Q3", pct(K["shf_yucatan_vs_national_pct"], 0),
                   f"Yucatán above the national median ({K['shf_yucatan_rank']:.0f}th of 32)", T.COLOR_GROWTH)
            + card("Low wages, 2026 Q2", f"{K['low_wage_pct']:.0f}%",
                   f"of Yucatán workers earn up to one minimum wage ({K['low_wage_workers']:,.0f} of "
                   f"{K['employed']:,.0f})", T.COLOR_MERIDA)
            + "</div>"
            + f'<p class="mfs-note">Also: {K["empty_homes_pct_2020"]:.1f}% of homes in Yucatán were empty or used only '
              "temporarily in 2020 (INEGI Census).</p>"
            + chips("AAFY lodging tax", "SHF home prices", "INEGI ENOE", "INEGI Census"))
with right:
    fig_head("Lodging tax vs hotel tourists", "Index, 2019 = 100")
    st.segmented_control("Prices", ["Nominal"], default="Nominal", required=True, key="prices",
                         label_visibility="collapsed",
                         help="Real (inflation-adjusted) values need the INPC annual average. No official INPC table "
                              "could be downloaded for this version, so only nominal pesos are shown.")
    plot(C.tax_index_lines(csv("tax_vs_tourists.csv")),
         f"Line chart, index 2019 = 100. Hotel tourists reach {K['tourists_index_2025']:.0f} in 2025; lodging tax "
         f"collected reaches {K['tax_index_2025']:.0f}.")
    st.html('<p class="mfs-note">Read with care: tax figures are nominal pesos (no inflation adjustment in v1), and the '
            "jump after 2021 also reflects digital platforms starting to collect the tax. The AAFY says platform "
            "collections are included in the totals but did not give a start date or a breakdown, so none is marked.</p>")

blocks = geojson("blocks_3d.geojson")
b = csv("blocks_3d.csv")
low_share = 100 * (b["altura_p90_m"] <= 8).mean()
st.html('<div class="mfs-ar"><span class="mfs-eyebrow">INEGI elevation model (2015)</span>'
        '<h3>Walk the low skyline of the Centro in 3D</h3>'
        f"<p>{len(blocks['features'])} Centro blocks extruded by the height of their buildings (90th percentile, "
        f"INEGI elevation model, 2015). In {low_share:.0f}% of them buildings stay under 8 m: one or two floors. "
        "Each block is coloured by businesses lost (green) or gained (ochre) since 2019. Heights are exaggerated "
        "×3. Drag to rotate, hover a block for details.</p></div>")
st.pydeck_chart(C.blocks_deck(blocks), height=520,
                alt="3D map of Centro blocks extruded by building height and coloured by net change in businesses.")
st.html('<p class="mfs-note">[QR CODE to AR scene] · Photogrammetric satellite model (INEGI, 2015), not airborne '
        "LiDAR.</p>")

# ---------------------------------------------------------------------------
# 04 Who tells the story
# ---------------------------------------------------------------------------
section("voices", "04", "Who tells the story",
        "Local newspapers write about speculation, fraud and rising rents. Online, the same city is sold as safe, "
        "beautiful and cheap.")
share = csv("press_share.csv")
left, right = st.columns([1, 1.75], gap="large")
with left:
    voice = st.segmented_control("Voice", ["Local press", "Seen from outside"], default="Local press",
                                 required=True, key="voice")
    if voice == "Local press":
        heads = csv("press_headlines.csv")
        items = "".join(f'<p>“{escape(h)}”<br><span class="mfs-note">{escape(o)}, {d}</span></p>'
                        for h, o, d in zip(heads["headline"], heads["outlet"], heads["date"]))
        st.html(f'<div class="mfs-quote"><p class="mfs-fig-sub"><b>Headlines from the corpus</b></p>'
                f'{items}<span class="mfs-note">{int(K["press_core_articles"])} core articles, 2018 to Nov 2026, '
                "Diario de Yucatán, Por Esto! and La Jornada Maya.</span></div>")
    else:
        vids = csv("youtube_top_videos.csv")
        items = "".join(f"<p>“{escape(t)}” · {v / 1000:,.0f}k views</p>" for t, v in zip(vids["title"], vids["views"]))
        st.html(f'<div class="mfs-quote"><p class="mfs-fig-sub"><b>Most watched videos</b></p>'
                f'{items}<span class="mfs-note">{K["yt_videos"]:.0f} videos about moving to Mérida, '
                f'{K["yt_views"] / 1e6:.2f}M views, {K["yt_pct_english"]:.0f}% in English.</span></div>')
    st.html(chips("Press scraping", "YouTube Data API", "GDELT (own pipeline)"))
with right:
    if voice == "Local press":
        fig_head("Housing and real estate in local news",
                 "Share of all scraped articles per year about the metro area · 2026* = to Nov")
        plot(C.press_share(share), "Share of local press articles per year that are core housing and real-estate "
             "stories about the Mérida metro area.", key="press_share")
        fig_head("Most mentioned neighbourhoods", "Articles that name each colonia or barrio")
        plot(C.hbars(csv("press_top_neighbourhoods.csv"), "neighbourhood", "articles", T.COLOR_MERIDA, 360),
             "Ten most mentioned neighbourhoods in local press articles.", key="press_colonias")
    else:
        fig_head("What YouTube comments talk about",
                 f"Comments mentioning each word, out of {K['yt_comments_read']:,.0f} read")
        plot(C.hbars(csv("youtube_keywords.csv"), "keyword", "mentions", T.COLOR_FOREIGN, 300),
             "Keyword mentions in YouTube comments.", key="yt_kw")
        vids = csv("youtube_top_videos.csv")
        st.dataframe(vids, hide_index=True, alt="Five most watched YouTube videos about moving to Mérida.",
                     column_config={"title": st.column_config.TextColumn("Title", width="large"),
                                    "channel": "Channel", "published": "Published",
                                    "views": st.column_config.NumberColumn("Views", format="localized"),
                                    "language": "Language"})
    gd = csv("gdelt_voices.csv").set_index("voice")
    total = int(gd["articles"].sum())
    st.html('<div class="mfs-strip">'
            f'<div><span>GDELT, Sep to Nov 2026, own collection pipeline</span><b>{total:,} articles</b></div>'
            f'<div><span>Local · national</span><b>{gd.loc["Local", "pct"]:.0f}% · {gd.loc["National", "pct"]:.0f}%</b></div>'
            f'<div><span>International</span><b>{gd.loc["International", "pct"]:.0f}%</b></div></div>')

# ---------------------------------------------------------------------------
# 05 Not Cancún, not yet
# ---------------------------------------------------------------------------
section("elsewhere", "05", "Not Cancún, not yet",
        "Mérida's airport is still mostly domestic and grows faster than Cancún's. But homes in Yucatán already cost "
        "more than in Quintana Roo or Oaxaca. The tourism is smaller; the pressure on housing is not.")
a25 = air[air["year"] == 2025].set_index("code")
names = {"MID": "Mérida (MID)", "CUN": "Cancún (CUN)", "OAX": "Oaxaca (OAX)"}
homes = csv("home_prices_2025T3.csv").set_index("state")
wiki = csv("wikipedia_index.csv")
growth = a25.sort_values("index_2019", ascending=False)
intl = a25.sort_values("pct_international", ascending=False)
states = ["Yucatán", "Oaxaca", "Quintana Roo", "Guanajuato"]
minis = [
    ("Airport growth", "Passengers 2025, index 2019 = 100",
     [names[c] for c in growth.index], list(growth["index_2019"]), [c == "MID" for c in growth.index],
     lambda v: f"{v:.0f}", 190),
    ("International passengers", "Share of airport traffic, 2025",
     [names[c] for c in intl.index], list(intl["pct_international"]), [c == "MID" for c in intl.index],
     lambda v: f"{v:.1f}%", 85),
    ("Median home price", "vs national median, SHF 2025 Q3",
     states, [homes.loc[s, "vs_national_pct"] for s in states], [s == "Yucatán" for s in states],
     lambda v: pct(v), 52),
    ("Online interest", "Wikipedia views 2025 (en + es), index 2019 = 100",
     list(wiki["city"]), list(wiki["index_2025"]), [c == "Mérida" for c in wiki["city"]],
     lambda v: f"{v:.0f}", 125),
]
for row in (minis[:2], minis[2:]):
    cols = st.columns(2, gap="medium")
    for col, (title, sub, n, v, h, fmt, scale) in zip(cols, row):
        with col:
            fig_head(title, sub)
            plot(C.compare_bars(n, v, h, fmt, scale), f"{title}: " + ", ".join(f"{a} {fmt(b)}" for a, b in zip(n, v)))

fig_head("Monthly passengers vs the same month of 2019", "ASUR, index same month 2019 = 100, Jan 2019 to Oct 2026")
plot(C.airports_monthly(csv("airports_monthly.csv")),
     "Monthly passenger index for Mérida, Cancún and Oaxaca airports, same month of 2019 = 100.")
st.html(chips("ASUR", "SHF", "Wikipedia pageviews"))

# ---------------------------------------------------------------------------
# Pie de página / metodología
# ---------------------------------------------------------------------------
SECTIONS = [("1-INEGI-DENUE", "INEGI DENUE and Census"), ("2-Datos-Gob-Mx", "DataTur and ASUR"),
            ("3-SIEGY-Yucatan", "Sefotur, SHF and ENOE"), ("4-GeoPortal-Merida", "GeoPortal de Mérida and INEGI maps"),
            ("5-Government-Data-Request", "AAFY lodging tax and Centro licenses"),
            ("6-Web-Scraping", "Local press, YouTube and Wikipedia"), ("7-Self-Produced", "GDELT (own pipeline)"),
            ("8-LiDAR", "INEGI elevation model (2015)"), ("9-Augmented-Reality", "AR scenes")]
with st.expander("Methodology and sources"):
    st.markdown("\n".join(f"- [{label}]({REPO_URL}/{folder}/README.md) (`{folder}`)" for folder, label in SECTIONS))
    st.markdown(
        "- **Boundaries:** press articles cover the Mérida metropolitan area (Mérida, Kanasín, Umán, Progreso, "
        "Conkal, Ucú); spatial data (DENUE, AGEBs, blocks) covers the municipality of Mérida.\n"
        "- **Money:** all peso figures are nominal. Real values need the INPC annual average, which v1 does not include.\n"
        "- **Press:** a core article mentions housing, rent, real estate, tourism pressure or foreigners and a "
        "metro-area place in its title or excerpt (rules in the section 6 README). The scraped articles are a "
        "targeted sample, not every article published.\n"
        "- **Wikipedia:** views fall worldwide after 2023, so compare cities, not years.\n"
        "- **YouTube:** search results are ordered by relevance at the time of the query (25 Nov 2026), which "
        "favours recent videos; some results are real-estate ads, not testimonials.\n"
        "- **3D scene:** INEGI's high-resolution elevation model for these map sheets is photogrammetric (satellite "
        "images, point cloud from 2015), not airborne LiDAR. Heights are the 90th percentile of the surface minus "
        "terrain model per block.\n"
        "- **2026** figures are partial (DataTur and AAFY to September, ASUR to October, press to November).")
st.html(f'<div class="mfs-footer">{T.FOOTER}<br><br>{T.APP_TITLE} · {T.COURSE} · {", ".join(T.TEAM)} · '
        '<a href="#top">Back to top</a></div>')
