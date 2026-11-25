"""Mérida for Sale · Dashboard v1: colores, fuentes y textos fijos.

Este es el ÚNICO archivo con colores (hex) y nombres de fuente. Para cambiar la
paleta o la tipografía del booklet, edita solo este archivo.
"""

VERSION = "v1"
APP_TITLE = f"Mérida for Sale · Dashboard {VERSION}"

# ---------------------------------------------------------------------------
# Colores por función
# ---------------------------------------------------------------------------
BG = "#F4EFE6"            # fondo de la página
SURFACE = "#FFFFFF"       # tarjetas y gráficas
TEXT = "#1E1B18"          # texto principal
TEXT_SOFT = "#3B3631"     # párrafos
TEXT_MUTED = "#5C554D"    # etiquetas, notas, ejes
BORDER = "#E0D8CB"        # líneas entre secciones
GRID = "#E6DFD4"          # cuadrícula de gráficas
TRACK = "#F1ECE3"         # fondo de barras de progreso

COLOR_MERIDA = "#1F5F5B"   # Mérida, nacional, Centro
COLOR_MERIDA_DARK = "#163F3C"
COLOR_MERIDA_SOFT = "#9FC0BC"  # años parciales
COLOR_MERIDA_TINT = "#E3EDEB"  # chips de fuente
COLOR_FOREIGN = "#C8892B"  # extranjero, otras ciudades
COLOR_GROWTH = "#8A5A17"   # crecimiento (texto/cifras)
COLOR_DECLINE = "#1F5F5B"  # caída
COLOR_MUTED = "#9A9187"    # gris neutro
COLOR_ACCENT_LIGHT = "#E8C27A"  # etiquetas sobre fondo verde
COLOR_ON_DARK = "#CFE0DD"       # texto secundario sobre verde
COLOR_ON_DARK_STRONG = BG

# Series categóricas (licencias por giro, categorías hoteleras)
CATEGORICAL = [COLOR_MERIDA, COLOR_FOREIGN, COLOR_MUTED, COLOR_GROWTH, COLOR_MERIDA_SOFT, COLOR_ACCENT_LIGHT]

# Escala divergente de mapas (pérdida → 0 → ganancia), centrada en 0
MAP_DIVERGING = [[0.0, "#1F5F5B"], [0.25, "#7FA9A4"], [0.5, "#F4EFE6"], [0.75, "#DDB067"], [1.0, "#8A5A17"]]
MAP_OUTLINE = TEXT
MAP_STYLE = "carto-positron"

# Escala divergente de la escena 3D (RGB), mismas anclas que MAP_DIVERGING
DECK_LOSS_RGB = (31, 95, 91)
DECK_NEUTRAL_RGB = (230, 223, 212)
DECK_GAIN_RGB = (200, 137, 43)
DECK_MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------
FONT_TITLE = "Space Grotesk"
FONT_BODY = "IBM Plex Sans"
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700"
             "&family=IBM+Plex+Sans:wght@400;500;600&display=swap")
FONT_STACK_TITLE = f"'{FONT_TITLE}', sans-serif"
FONT_STACK_BODY = f"'{FONT_BODY}', sans-serif"


def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def css() -> str:
    """CSS que se inyecta una vez en app.py (fuentes de Google y estilos del prototipo)."""
    return f"""
<style>
@import url('{FONTS_URL}');
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: {BG}; }}
.stApp {{ color: {TEXT}; }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp td, .stApp th, .stApp button,
.stApp span:not([data-testid="stIconMaterial"]) {{ font-family: {FONT_STACK_BODY}; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{ font-family: {FONT_STACK_TITLE}; color: {TEXT}; letter-spacing: -0.02em; }}
.stApp a {{ color: {COLOR_MERIDA}; }}
.stApp a:hover {{ color: {COLOR_MERIDA_DARK}; }}
.block-container {{ max-width: 1200px; padding-top: 3.5rem; }}
[class*="st-key-"] button[aria-checked="true"] {{ background: {COLOR_MERIDA} !important; border-color: {COLOR_MERIDA} !important; }}
[class*="st-key-"] button[aria-checked="false"] {{ background: {SURFACE} !important; border-color: {COLOR_MERIDA} !important; }}
[class*="st-key-"] button[aria-checked="true"] * {{ color: {SURFACE} !important; }}
[class*="st-key-"] button[aria-checked="false"] * {{ color: {COLOR_MERIDA} !important; }}
[class*="st-key-"] button:focus-visible {{ outline: 2px solid {COLOR_GROWTH}; }}
.mfs-nav {{ display: flex; flex-wrap: wrap; gap: 4px 18px; align-items: center; justify-content: space-between;
  border-bottom: 1px solid {BORDER}; padding: 6px 0 10px; }}
.mfs-nav a {{ text-decoration: none; font-weight: 600; font-size: 14px; }}
.mfs-brand {{ font-family: {FONT_STACK_TITLE}; font-weight: 700; font-size: 18px; color: {TEXT} !important; }}
.mfs-eyebrow {{ font-size: 13px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: {TEXT_MUTED}; }}
.mfs-hero {{ font-family: {FONT_STACK_TITLE}; font-size: clamp(56px, 11vw, 136px); line-height: 0.9; font-weight: 700;
  letter-spacing: -0.03em; margin: 12px 0 20px; color: {TEXT}; }}
.mfs-byline {{ font-size: 15px; line-height: 1.5; color: {TEXT_MUTED}; margin-top: 18px; }}
.mfs-byline b {{ color: {TEXT}; font-weight: 600; }}
.mfs-lede {{ font-size: 21px; line-height: 1.45; color: {TEXT_SOFT}; max-width: 620px; }}
.mfs-h2 {{ font-family: {FONT_STACK_TITLE}; font-size: clamp(36px, 6vw, 52px); line-height: 1; font-weight: 700;
  letter-spacing: -0.02em; margin: 8px 0 16px; color: {TEXT}; }}
.mfs-body {{ font-size: 18px; line-height: 1.55; color: {TEXT_SOFT}; }}
.mfs-note {{ font-size: 13px; line-height: 1.45; color: {TEXT_MUTED}; }}
.mfs-section {{ border-top: 1px solid {BORDER}; margin-top: 56px; padding-top: 48px; scroll-margin-top: 16px; }}
.mfs-kpi-panel {{ background: {COLOR_MERIDA}; border-radius: 10px; padding: 28px; }}
.mfs-kpi-panel .mfs-eyebrow {{ color: {COLOR_ACCENT_LIGHT}; }}
.mfs-kpi-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px 16px; margin-top: 16px; }}
.mfs-kpi-grid b {{ display: block; font-family: {FONT_STACK_TITLE}; font-size: 34px; color: {COLOR_ON_DARK_STRONG}; }}
.mfs-kpi-grid span {{ font-size: 13px; color: {COLOR_ON_DARK}; }}
.mfs-card {{ background: {SURFACE}; border-radius: 8px; padding: 18px; height: 100%; box-sizing: border-box; }}
.mfs-card .lbl {{ font-size: 13px; font-weight: 600; color: {TEXT_MUTED}; display: block; }}
.mfs-card .big {{ font-family: {FONT_STACK_TITLE}; font-size: 32px; font-weight: 700; display: block; }}
.mfs-card .sub {{ font-size: 13px; color: {TEXT_SOFT}; }}
.mfs-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 8px 0; }}
.mfs-chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }}
.mfs-chips span {{ font-size: 12px; font-weight: 600; padding: 6px 10px; border-radius: 999px; background: {COLOR_MERIDA_TINT}; color: {COLOR_MERIDA}; }}
.mfs-fig-title {{ font-family: {FONT_STACK_TITLE}; font-size: 20px; font-weight: 700; margin: 0; color: {TEXT}; }}
.mfs-fig-sub {{ font-size: 13px; color: {TEXT_MUTED}; }}
.mfs-quote {{ background: {SURFACE}; border-radius: 8px; padding: 16px 18px; }}
.mfs-quote p {{ margin: 0 0 8px; font-size: 15px; line-height: 1.45; }}
.mfs-ar {{ background: {COLOR_MERIDA}; border-radius: 8px; padding: 24px; }}
.mfs-ar .mfs-eyebrow {{ color: {COLOR_ACCENT_LIGHT}; }}
.mfs-ar h3 {{ color: {COLOR_ON_DARK_STRONG} !important; margin: 4px 0 8px; font-size: 24px; }}
.mfs-ar p {{ color: {COLOR_ON_DARK} !important; font-size: 15px; line-height: 1.5; margin: 0; }}
.mfs-strip {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; border-top: 1px solid {BORDER}; padding-top: 12px; }}
.mfs-strip b {{ display: block; font-family: {FONT_STACK_TITLE}; font-size: 22px; }}
.mfs-strip span {{ font-size: 12px; color: {TEXT_MUTED}; }}
.mfs-legend {{ display: inline-flex; align-items: center; gap: 6px; margin-right: 16px; font-size: 13px; color: {TEXT_SOFT}; }}
.mfs-legend i {{ width: 22px; height: 10px; display: inline-block; border-radius: 2px; }}
.mfs-footer {{ border-top: 1px solid {BORDER}; margin-top: 48px; padding-top: 20px; font-size: 13px; color: {TEXT_MUTED}; }}
[data-testid="stPlotlyChart"], [data-testid="stDeckGlJsonChart"] {{ background: {SURFACE}; border-radius: 8px; }}
</style>
"""


# ---------------------------------------------------------------------------
# Textos fijos (inglés, iguales al prototipo)
# ---------------------------------------------------------------------------
CHAPTERS = [("arrival", "01 Arrival"), ("shops", "02 Shops"), ("homes", "03 Homes"),
            ("voices", "04 Voices"), ("elsewhere", "05 Elsewhere")]
EYEBROW = "Visual Modeling for Information · UPY Data 9B"
LEDE = ("More visitors every year, fewer shops in the Centro, and a lodging tax that tripled. "
        "A story of what tourism is quietly buying in the Mérida metropolitan area.")
TEAM = ["Julio César De Aquino Castellanos", "Brad Robles García", "Eliana Lorely Osorio Martinez"]
COURSE = "Visual Modeling for Information · UPY Data 9B"
FOOTER = ("All figures come from the project's cleaned datasets (repo M-rida-for-Sale). Press articles cover the "
          "Mérida metropolitan area (Mérida, Kanasín, Umán, Progreso, Conkal, Ucú); spatial data covers the "
          "municipality of Mérida. Money in nominal pesos. Wikipedia views fall worldwide after 2023, so compare "
          "cities, not years.")
