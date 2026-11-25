"""Gráficas del Dashboard v1 (Plotly y pydeck). Una función por gráfica; colores y fuentes desde theme."""
from __future__ import annotations

import copy

import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk

import theme as T

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False}


def _fmt_int(v: float) -> str:
    return f"{v:,.0f}"


def _year_labels(years, partial) -> list[str]:
    """Etiquetas cortas ('15 … '26*) para que 12 barras quepan a 390 px."""
    return [f"'{str(y)[2:]}" + ("*" if p else "") for y, p in zip(years, partial)]


def _base(fig: go.Figure, height: int, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8 if not legend else 36, b=8),
        paper_bgcolor=T.SURFACE, plot_bgcolor=T.SURFACE,
        font=dict(family=T.FONT_STACK_BODY, color=T.TEXT_SOFT, size=12),
        hoverlabel=dict(bgcolor=T.SURFACE, bordercolor=T.BORDER, font=dict(family=T.FONT_STACK_BODY, color=T.TEXT)),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, xanchor="left", bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12)),
        bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, linecolor=T.COLOR_MUTED, tickfont=dict(color=T.TEXT_MUTED, size=11),
                     fixedrange=True, ticks="")
    fig.update_yaxes(gridcolor=T.GRID, zeroline=False, tickfont=dict(color=T.TEXT_MUTED, size=11), fixedrange=True)
    return fig


# ---------------------------------------------------------------------------
# 01 The arrival
# ---------------------------------------------------------------------------
def tourists_stacked(df: pd.DataFrame) -> go.Figure:
    labels = _year_labels(df["year"], df["partial"])
    opacity = [0.55 if p else 1.0 for p in df["partial"]]
    fig = go.Figure()
    for col, name, color in [("national", "National", T.COLOR_MERIDA), ("foreign", "Foreign", T.COLOR_FOREIGN)]:
        fig.add_bar(x=labels, y=df[col] / 1e6, name=name, marker=dict(color=color, opacity=opacity),
                    customdata=df[[col, "total", "pct_foreign"]],
                    hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{customdata[0]:,.0f}}"
                                  "<br>Total: %{customdata[1]:,.0f}<br>Foreign share: %{customdata[2]:.1f}%<extra></extra>")
    fig.add_scatter(x=labels, y=df["total"] / 1e6, mode="text", text=[f"{v / 1e6:.2f}" for v in df["total"]],
                    textposition="top center", textfont=dict(size=10, color=T.TEXT_SOFT), hoverinfo="skip",
                    showlegend=False)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title=None, ticksuffix="M", range=[0, 2.6])
    return _base(fig, 360, legend=True)


def tourists_monthly(df: pd.DataFrame, category: str) -> go.Figure:
    d = df[df["category"] == category]
    fig = go.Figure()
    for col, name, color in [("national", "National", T.COLOR_MERIDA), ("foreign", "Foreign", T.COLOR_FOREIGN)]:
        fig.add_scatter(x=d["date"], y=d[col], name=name, mode="lines", line=dict(color=color, width=2),
                        hovertemplate=f"%{{x|%b %Y}}<br>{name}: %{{y:,.0f}}<extra></extra>")
    fig.update_xaxes(type="date", dtick="M24", tickformat="%Y")
    fig.update_yaxes(tickformat="~s")
    return _base(fig, 280, legend=True)


# ---------------------------------------------------------------------------
# 02 The Centro empties out
# ---------------------------------------------------------------------------
def shops_diverging(df: pd.DataFrame, area: str) -> go.Figure:
    d = df[df["area"] == area].iloc[::-1]
    colors = [T.COLOR_FOREIGN if v > 0 else T.COLOR_DECLINE for v in d["pct_change"]]
    text = [f"{'+' if v > 0 else '−'}{abs(v):.1f}%" for v in d["pct_change"]]
    fig = go.Figure(go.Bar(
        x=d["pct_change"], y=d["category"], orientation="h", marker_color=colors, text=text,
        textposition="outside", cliponaxis=False, textfont=dict(color=T.TEXT, size=13),
        customdata=d[["n_2019", "n_2025", "change"]],
        hovertemplate="<b>%{y}</b><br>2019: %{customdata[0]:,}<br>2025: %{customdata[1]:,}"
                      "<br>Change: %{customdata[2]:+,} (%{x:+.1f}%)<extra></extra>",
    ))
    fig.update_xaxes(range=[-55, 55], zeroline=True, zerolinecolor=T.COLOR_MUTED, ticksuffix="%",
                     gridcolor=T.GRID, showgrid=True)
    fig.update_yaxes(showgrid=False, tickfont=dict(color=T.TEXT, size=13), automargin=True)
    return _base(fig, 300)


def _outline_traces(geojson: dict) -> go.Scattermap:
    lons, lats = [], []
    for f in geojson["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            ring = poly[0]
            lons += [c[0] for c in ring] + [None]
            lats += [c[1] for c in ring] + [None]
    return go.Scattermap(lon=lons, lat=lats, mode="lines", line=dict(color=T.MAP_OUTLINE, width=2.5),
                         name="Centro Histórico", hoverinfo="skip")


def cafe_map(ageb_geojson: dict, df: pd.DataFrame, centro_geojson: dict) -> go.Figure:
    lim = max(5, int(df["cafes_change"].abs().quantile(0.98)))
    fig = go.Figure(go.Choroplethmap(
        geojson=ageb_geojson, locations=df["cvegeo"], featureidkey="properties.cvegeo", z=df["cafes_change"],
        zmin=-lim, zmax=lim, zmid=0, colorscale=T.MAP_DIVERGING, marker=dict(line=dict(width=0.3, color=T.SURFACE),
                                                                             opacity=0.85),
        customdata=df[["cafes_2019", "cafes_2025"]],
        hovertemplate="AGEB %{location}<br>Coffee shops 2019: %{customdata[0]}<br>2025: %{customdata[1]}"
                      "<br>Change: %{z:+}<extra></extra>",
        colorbar=dict(title=dict(text="Change", font=dict(size=11)), thickness=10, len=0.6, x=0.99, xanchor="right",
                      tickfont=dict(size=10), bgcolor=T.rgba(T.SURFACE, 0.8)),
    ))
    fig.add_trace(_outline_traces(centro_geojson))
    fig.update_layout(map=dict(style=T.MAP_STYLE, center=dict(lat=20.985, lon=-89.62), zoom=10.3),
                      margin=dict(l=0, r=0, t=0, b=0), height=460, paper_bgcolor=T.SURFACE, showlegend=False,
                      font=dict(family=T.FONT_STACK_BODY, color=T.TEXT_SOFT))
    return fig


def licenses_stacked(df: pd.DataFrame) -> go.Figure:
    order = ["Commerce and services", "Food and drink", "Lodging", "Not specified"]
    colors = dict(zip(order, [T.COLOR_MERIDA, T.COLOR_FOREIGN, T.COLOR_GROWTH, T.COLOR_MUTED]))
    pv = df.pivot_table(index="year", columns="category", values="licenses", aggfunc="sum", fill_value=0)
    labels = _year_labels(pv.index, [y > 2025 for y in pv.index])
    fig = go.Figure()
    for cat in order:
        if cat in pv:
            fig.add_bar(x=labels, y=pv[cat], name=cat, marker_color=colors[cat],
                        hovertemplate=f"%{{x}} · {cat}: %{{y}}<extra></extra>")
    tot = pv.sum(axis=1)
    fig.add_scatter(x=labels, y=tot, mode="text", text=[str(v) for v in tot], textposition="top center",
                    textfont=dict(size=11, color=T.TEXT_SOFT), hoverinfo="skip", showlegend=False)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(type="category")
    fig.update_yaxes(range=[0, tot.max() * 1.18])
    return _base(fig, 300, legend=True)


# ---------------------------------------------------------------------------
# 03 The invisible hotel
# ---------------------------------------------------------------------------
def tax_index_lines(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    series = [("tourists_index", "Hotel tourists (DataTur)", T.COLOR_MERIDA, "tourists"),
              ("tax_index", "Lodging tax collected (AAFY, nominal pesos)", T.COLOR_FOREIGN, "tax_nominal_mxn")]
    for col, name, color, raw in series:
        fig.add_scatter(x=df["year"], y=df[col], name=name, mode="lines+markers",
                        line=dict(color=color, width=2.5), marker=dict(size=5), customdata=df[[raw]],
                        hovertemplate=f"%{{x}} · {name}<br>Index: %{{y:.1f}}<br>Value: %{{customdata[0]:,.0f}}<extra></extra>")
        last = df.iloc[-1]
        fig.add_annotation(x=last["year"], y=last[col], text=f"<b>{last[col]:.0f}</b>", showarrow=False,
                           xanchor="left", xshift=6, font=dict(color=T.COLOR_GROWTH if col == "tax_index" else color,
                                                               size=13))
    fig.add_hline(y=100, line=dict(color=T.COLOR_MUTED, width=1, dash="dot"))
    fig.update_xaxes(dtick=2, range=[df["year"].min() - 0.3, df["year"].max() + 0.9])
    fig.update_yaxes(range=[0, 360])
    return _base(fig, 340, legend=True)


def _lerp(a: tuple, b: tuple, t: float) -> list[int]:
    return [round(x + (y - x) * t) for x, y in zip(a, b)]


def blocks_deck(geojson: dict, exaggeration: float = 3.0) -> pdk.Deck:
    gj = copy.deepcopy(geojson)
    changes = sorted(abs(f["properties"]["net_change"]) for f in gj["features"])
    lim = max(1, changes[int(0.95 * (len(changes) - 1))])
    for f in gj["features"]:
        p = f["properties"]
        t = max(-1.0, min(1.0, p["net_change"] / lim))
        rgb = _lerp(T.DECK_NEUTRAL_RGB, T.DECK_GAIN_RGB if t > 0 else T.DECK_LOSS_RGB, abs(t))
        p["fill"] = rgb + [235]
        p["elev"] = p["height_p90_m"] * exaggeration
        p["change_txt"] = f"{p['net_change']:+d}"
    layer = pdk.Layer(
        "GeoJsonLayer", gj, extruded=True, filled=True, stroked=False, wireframe=False, pickable=True,
        get_fill_color="properties.fill", get_elevation="properties.elev", material=True,
    )
    view = pdk.ViewState(latitude=20.9695, longitude=-89.6215, zoom=14.2, pitch=55, bearing=-20)
    tooltip = {"html": "<b>Block {clave_manzana}</b><br>Height (p90): {height_p90_m} m"
                       "<br>Businesses 2019 → 2025: {businesses_2019} → {businesses_2025} ({change_txt})",
               "style": {"backgroundColor": T.SURFACE, "color": T.TEXT, "fontFamily": T.FONT_STACK_BODY,
                         "fontSize": "12px"}}
    return pdk.Deck(layers=[layer], initial_view_state=view, map_provider="carto", map_style=T.DECK_MAP_STYLE,
                    tooltip=tooltip)


# ---------------------------------------------------------------------------
# 04 Who tells the story
# ---------------------------------------------------------------------------
def press_share(df: pd.DataFrame) -> go.Figure:
    labels = [f"{y}*" if p else str(y) for y, p in zip(df["year"], df["partial"])]
    colors = [T.COLOR_MERIDA_SOFT if p else T.COLOR_MERIDA for p in df["partial"]]
    fig = go.Figure(go.Bar(
        x=labels, y=df["pct_core"], marker_color=colors, text=[f"{v:.0f}%" for v in df["pct_core"]],
        textposition="outside", cliponaxis=False, textfont=dict(color=T.TEXT, size=12),
        customdata=df[["core", "articles"]],
        hovertemplate="%{x}: %{customdata[0]} of %{customdata[1]} articles (%{y:.1f}%)<extra></extra>",
    ))
    fig.update_xaxes(type="category")
    fig.update_yaxes(ticksuffix="%", range=[0, 38])
    return _base(fig, 320)


def hbars(df: pd.DataFrame, label: str, value: str, color: str, height: int = 300) -> go.Figure:
    d = df.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=d[value], y=d[label], orientation="h", marker_color=color, text=[_fmt_int(v) for v in d[value]],
        textposition="outside", cliponaxis=False, textfont=dict(color=T.TEXT, size=12),
        hovertemplate="%{y}: %{x:,}<extra></extra>",
    ))
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, d[value].max() * 1.15])
    fig.update_yaxes(showgrid=False, tickfont=dict(color=T.TEXT, size=13), automargin=True)
    return _base(fig, height)


# ---------------------------------------------------------------------------
# 05 Not Cancún, not yet
# ---------------------------------------------------------------------------
def compare_bars(names: list[str], values: list[float], highlight: list[bool], fmt, scale: float) -> go.Figure:
    colors = [T.COLOR_MERIDA if h else (T.COLOR_MUTED if v < 0 else T.COLOR_FOREIGN) for v, h in zip(values, highlight)]
    fig = go.Figure(go.Bar(
        x=values[::-1], y=names[::-1], orientation="h", marker_color=colors[::-1],
        text=[fmt(v) for v in values[::-1]], textposition="outside", cliponaxis=False,
        textfont=dict(color=T.TEXT, size=12), hovertemplate="%{y}: %{text}<extra></extra>",
    ))
    lo = min(0, min(values)) * 2.6
    fig.update_xaxes(showticklabels=False, showgrid=False, range=[lo, scale], zeroline=True,
                     zerolinecolor=T.COLOR_MUTED)
    fig.update_yaxes(showgrid=False, tickfont=dict(color=T.TEXT, size=12), automargin=True)
    return _base(fig, 60 + 38 * len(names))


def airports_monthly(df: pd.DataFrame) -> go.Figure:
    colors = {"MID": T.COLOR_MERIDA, "CUN": T.COLOR_FOREIGN, "OAX": T.COLOR_MUTED}
    names = {"MID": "Mérida (MID)", "CUN": "Cancún (CUN)", "OAX": "Oaxaca (OAX)"}
    fig = go.Figure()
    for code in ["MID", "CUN", "OAX"]:
        d = df[df["code"] == code]
        fig.add_scatter(x=d["date"], y=d["index_same_month_2019"], name=names[code], mode="lines",
                        line=dict(color=colors[code], width=3 if code == "MID" else 1.8),
                        hovertemplate=f"{names[code]} · %{{x|%b %Y}}: %{{y:.0f}}<extra></extra>")
    fig.add_hline(y=100, line=dict(color=T.COLOR_MUTED, width=1, dash="dot"))
    fig.update_xaxes(type="date", tickformat="%Y")
    return _base(fig, 300, legend=True)
