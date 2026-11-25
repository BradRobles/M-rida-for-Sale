"""
Reglas compartidas de clasificación para las secciones 6 (Web Scraping) y 7 (Self-produced).

- `voz(dominio, pais_fuente)`: `local` (medios de Yucatán), `nacional` (otros medios mexicanos)
  o `internacional`.
- `temas_resumidos(titulo, temas_gkg, texto)`: categorías resumidas
  vivienda_rentas, bienes_raices, turismo, seguridad, migracion_expats, servicios_agua, otros.

La sección 6 importa este archivo (ver `6-Web-Scraping/scripts/clean_prensa_local.py`).
"""

from __future__ import annotations

import re
import unicodedata

# Medios con sede en Yucatán. Los seis primeros vienen de la especificación; el resto se
# encontró en los datos de GDELT y se anota en el README de la sección 7.
DOMINIOS_LOCALES = [
    "yucatan.com.mx", "poresto.com", "lajornadamaya.mx", "laverdadnoticias.com",
    "novedadesyucatan.com", "sipse.com",
    "diariodelsureste.com.mx", "yucatanahora.mx", "lectormx.com", "reporteroshoy.mx",
    "infolliteras.com", "notirasa.com", "desdeelbalcon.com", "yucatan.gob.mx",
    "merida.gob.mx", "yucatan.quadratin.com.mx", "elchilambalam.com", "sintesistv.com.mx",
    "yucatanmagazine.com", "theyucatantimes.com", "peninsulardigital.com",
    "noticiasyucatan.com", "trotamundosyucatan.com", "yucatanalamano.com",
    "diariodeyucatan.com", "candela.com.mx", "megamedia.com.mx", "yucatan.mx",
    "mayaonline.com", "notisureste.com", "lajornadamaya.com", "reportero24.com",
    "grilloporteno.com", "yucatanalinstante.com", "yucatanenlinea.com",
]

# Medios mexicanos con dominio .com/.net/.us (los .mx se reconocen por terminación).
DOMINIOS_NACIONALES = [
    "milenio.com", "infobae.com/mexico", "sdpnoticias.com", "aristeguinoticias.com",
    "mexiconewsdaily.com", "nmas.com.mx", "tvazteca.com", "elsoldemexico.com.mx",
    "jornada.com.mx", "excelsior.com.mx", "eluniversal.com.mx", "proceso.com.mx",
    "elfinanciero.com.mx", "eleconomista.com.mx", "latinus.us", "lasillarota.com",
    "elheraldodemexico.com", "heraldodemexico.com.mx", "unotv.com", "televisa.com",
    "msn.com/es-mx", "debate.com.mx", "razon.com.mx", "24-horas.mx", "contrareplica.mx",
    "elimparcial.com", "elsiglodetorreon.com.mx", "informador.mx", "politico.mx",
    "mvsnoticias.com", "radioformula.com.mx", "adn40.mx", "noticieros.televisa.com",
    "posta.com.mx", "quadratin.com.mx", "cronica.com.mx", "ejecentral.com.mx",
    "expansion.mx", "forbes.com.mx", "animalpolitico.com", "elpais.com/mexico",
    "reforma.com", "elnorte.com", "mural.com", "am.com.mx", "vanguardia.com.mx",
    "zocalo.com.mx", "cambio22.mx", "quintanaroohoy.com", "noticaribe.com.mx",
    "riviera-maya-news.com", "lopezdoriga.com", "codigoqro.mx", "diariodexalapa.com.mx",
]


def normalizar(texto: str | None) -> str:
    """Minúsculas y sin acentos (para comparar texto)."""
    t = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def limpiar_dominio(dominio_o_url: str | None) -> str:
    d = (dominio_o_url or "").strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = re.sub(r"^www\d?\.", "", d)
    return d


def _coincide(d: str, lista: list[str]) -> bool:
    return any(d == x or d.endswith("." + x) or d.startswith(x) for x in lista)


def voz(dominio_o_url: str | None, pais_fuente: str | None = None) -> str:
    d = limpiar_dominio(dominio_o_url)
    if _coincide(d, DOMINIOS_LOCALES):
        return "local"
    host = d.split("/")[0]
    if host.endswith(".mx") or _coincide(d, DOMINIOS_NACIONALES) or (pais_fuente or "").lower() == "mexico":
        return "nacional"
    return "internacional"


# Reglas de temas: (palabras en título/texto normalizado, prefijos de temas GKG).
# Los temas GKG se toman solo si son específicos; los genéricos (p. ej. TAX_FNCACT_POLICE)
# aparecen en casi cualquier nota y inflarían "seguridad".
REGLAS_TEMAS: dict[str, tuple[list[str], list[str]]] = {
    "vivienda_rentas": (
        ["vivienda", "renta", "rentas", "alquiler", "desalojo", "desaloj", "despojo", "gentrific",
         "housing", "rent ", "rents", "renters", "eviction", "infonavit", "casa habitacion",
         "casas habitacion", "viviendas"],
        ["ECON_HOUSING_PRICES", "WB_1041_HOUSING", "HOUSING", "EVICTION", "GENTRIFICATION",
         "TAX_FNCACT_TENANTS", "UNGP_AFFORDABLE_HOUSING"],
    ),
    "bienes_raices": (
        ["inmobiliari", "bienes raices", "real estate", "plusvalia", "desarrollo inmobiliario",
         "desarrolladora", "condominio", "terreno", "terrenos", "fraccionamiento",
         "property", "properties", "realtor", "torre de departamentos"],
        ["ECON_REAL_ESTATE", "REAL_ESTATE", "WB_1052_REAL_ESTATE", "ECON_PROPERTY"],
    ),
    "turismo": (
        ["turis", "touris", "hotel", "hoteler", "crucero", "cruise", "tren maya", "vacacion",
         "vacation", "travel", "viajer", "visitante", "airbnb", "hospedaje", "gastronom"],
        ["TOURISM", "WB_1921_TOURISM", "ECON_TOURISM", "TAX_FNCACT_TOURIST", "TRAVEL"],
    ),
    "seguridad": (
        ["seguridad", "insegur", "segura", "safe", "safest", "crimen", "delito", "homicid",
         "asesin", "detenid", "robo", "violencia", "narco", "polic", "crime", "murder", "cartel",
         "fiscalia"],
        ["CRIME", "KILL", "ARREST", "WB_2433_CONFLICT", "VIOLENT_CRIME", "CRIME_ILLEGAL_DRUGS",
         "SECURITY_SERVICES"],
    ),
    "migracion_expats": (
        ["expat", "extranjer", "migrant", "migracion", "nomada digital", "digital nomad",
         "jubilad", "retire", "retirement", "americanos", "estadounidense", "canadiense",
         "moving to", "living in", "mudarse", "foreigner", "gringo"],
        ["IMMIGRATION", "MIGRATION", "TAX_FNCACT_MIGRANTS", "TAX_FNCACT_IMMIGRANTS",
         "TAX_FNCACT_EXPATRIATES", "WB_2837_IMMIGRATION"],
    ),
    "servicios_agua": (
        ["agua", "japay", "apagon", "cfe", "drenaje", "basura", "luz electrica", "energia electrica",
         "water", "electricity", "blackout", "power outage", "desabasto", "pozo", "acuifero",
         "cenote"],
        ["WATER_SECURITY", "WB_137_WATER", "ENV_WATERWAYS", "POWER_OUTAGE", "WB_1350_ELECTRICITY",
         "UNGP_CLEAN_WATER_SANITATION", "ENV_WATER", "INFRASTRUCTURE_BAD_ROADS"],
    ),
}


def _preparar(texto: str | None) -> str:
    t = re.sub(r"[^a-z0-9 ]", " ", normalizar(texto))
    return f" {' '.join(t.split())} "


def temas_resumidos(titulo: str | None = "", temas_gkg: str | None = "", texto: str | None = "",
                    min_hits_texto: int = 1) -> list[str]:
    """Temas por título (basta 1 palabra), por temas GKG o por texto (al menos
    `min_hits_texto` apariciones de palabras del tema; la sección 6 usa 2 sobre el cuerpo)."""
    tit = _preparar(titulo)
    cuerpo = _preparar(texto)
    gkg = [t.strip().upper() for t in re.split(r"[;,]", temas_gkg or "") if t.strip()]
    salida = []
    for tema, (palabras, prefijos) in REGLAS_TEMAS.items():
        por_titulo = any((" " + p) in tit for p in palabras)
        hits = sum(cuerpo.count(" " + p) for p in palabras) if texto else 0
        por_texto = hits >= min_hits_texto
        por_gkg = any(any(t.startswith(pref) for pref in prefijos) for t in gkg)
        if por_titulo or por_texto or por_gkg:
            salida.append(tema)
    return salida or ["otros"]
