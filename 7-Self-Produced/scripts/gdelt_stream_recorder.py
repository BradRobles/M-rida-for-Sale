"""
Grabador propio del stream GDELT GKG 2.1 para la sección 7-Self-Produced.

Fuente cubierta:
- Principal (stream): GDELT 2.0 Global Knowledge Graph, actualizado cada 15 minutos.
  * Inglés:     http://data.gdeltproject.org/gdeltv2/lastupdate.txt
  * Traducido:  http://data.gdeltproject.org/gdeltv2/lastupdate-translation.txt

Qué hace:
- Cada 15 minutos lee los dos `lastupdate*.txt`, descarga el GKG nuevo (en memoria; los
  .zip NO se guardan) y conserva solo los documentos cuyo `V2EnhancedLocations` tenga una
  ubicación con ADM1 = `MX31` (Yucatán) y que sea Mérida (nombre con "Merida" o coordenadas
  dentro de lat 20.85–21.10, lon −89.75 a −89.50).
- Agrega filas a `raw/gdelt_stream/gkg_merida_YYYY-MM-DD.csv` (fecha UTC del archivo GKG).
- Tolera cortes: guarda en `raw/gdelt_stream/_procesados.txt` cada archivo GKG ya leído y,
  al reanudar, recupera los intervalos de 15 minutos que faltan (hasta `--max-recuperar-horas`).

Uso:
    python 7-Self-Produced/scripts/gdelt_stream_recorder.py            # bucle infinito
    python 7-Self-Produced/scripts/gdelt_stream_recorder.py --once     # una sola pasada
    python 7-Self-Produced/scripts/gdelt_stream_recorder.py --backfill-horas 48
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import re
import sys
import time
import unicodedata
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
STREAM_DIR = BASE_DIR / "raw" / "gdelt_stream"
PROCESADOS = STREAM_DIR / "_procesados.txt"
LOG_FILE = STREAM_DIR / "_recorder.log"
PID_FILE = STREAM_DIR / "_recorder.pid"

USER_AGENT = "MeridaForSale-UPY/1.0 (+https://github.com/BradRobles/M-rida-for-Sale)"
LASTUPDATE = {
    "ingles": "https://data.gdeltproject.org/gdeltv2/lastupdate.txt",
    "traducido": "https://data.gdeltproject.org/gdeltv2/lastupdate-translation.txt",
}
GKG_URL = {
    "ingles": "https://data.gdeltproject.org/gdeltv2/{ts}.gkg.csv.zip",
    "traducido": "https://data.gdeltproject.org/gdeltv2/{ts}.translation.gkg.csv.zip",
}
INTERVALO_S = 15 * 60
PAUSA_S = 2.0
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 20.85, 21.10, -89.75, -89.50

COLUMNAS = [
    "fecha_hora_utc", "dominio", "url", "tono", "positivo", "negativo", "temas",
    "idioma_origen", "titulo", "ubicacion_merida", "gkg_record_id", "archivo_gkg",
]

SESSION = requests.Session()
SESSION.headers["User-Agent"] = USER_AGENT
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
log = logging.getLogger("gdelt_stream")


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def get(url: str, intentos: int = 4, timeout: int = 120) -> requests.Response | None:
    """GET con reintentos y espera exponencial. Devuelve None si el archivo no existe (404)."""
    for i in range(intentos):
        try:
            r = SESSION.get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            time.sleep(PAUSA_S)
            return r
        except requests.RequestException as e:
            espera = 10 * 2**i
            log.warning("Error %s en %s (intento %d); espero %ds", e, url, i + 1, espera)
            time.sleep(espera)
    return None


def ubicacion_merida(v2_locations: str) -> str:
    """Devuelve el nombre de la primera ubicación de Mérida (MX31) o '' si no hay."""
    for loc in (v2_locations or "").split(";"):
        partes = loc.split("#")
        if len(partes) < 7 or partes[3] != "MX31":
            continue
        nombre = partes[1]
        try:
            lat, lon = float(partes[5]), float(partes[6])
        except ValueError:
            lat = lon = None
        en_caja = lat is not None and LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX
        if "merida" in normalizar(nombre) or en_caja:
            return nombre
    return ""


def temas_nombres(v2_themes: str) -> str:
    vistos: list[str] = []
    for t in (v2_themes or "").split(";"):
        nombre = t.split(",")[0].strip()
        if nombre and nombre not in vistos:
            vistos.append(nombre)
    return ";".join(vistos)


def idioma(translation_info: str) -> str:
    m = re.search(r"srclc:([a-z]{3})", translation_info or "")
    return m.group(1) if m else "eng"


def titulo(extras_xml: str) -> str:
    m = re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", extras_xml or "", re.S)
    return " ".join(m.group(1).split()) if m else ""


def procesar_gkg(contenido: bytes, archivo: str) -> list[dict]:
    filas = []
    with zipfile.ZipFile(io.BytesIO(contenido)) as zf:
        nombre = zf.namelist()[0]
        texto = zf.read(nombre).decode("utf-8", errors="replace")
    for linea in texto.split("\n"):
        c = linea.split("\t")
        if len(c) < 27 or "MX31" not in c[10]:
            continue
        ubic = ubicacion_merida(c[10])
        if not ubic:
            continue
        tono = (c[15] or "").split(",")
        fecha = datetime.strptime(c[1][:14], "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")
        filas.append({
            "fecha_hora_utc": fecha,
            "dominio": c[3],
            "url": c[4],
            "tono": tono[0] if len(tono) > 0 else "",
            "positivo": tono[1] if len(tono) > 1 else "",
            "negativo": tono[2] if len(tono) > 2 else "",
            "temas": temas_nombres(c[8] or c[7]),
            "idioma_origen": idioma(c[25]),
            "titulo": titulo(c[26]),
            "ubicacion_merida": ubic,
            "gkg_record_id": c[0],
            "archivo_gkg": archivo,
        })
    return filas


def escribir(filas: list[dict], ts: str) -> None:
    if not filas:
        return
    destino = STREAM_DIR / f"gkg_merida_{ts[:4]}-{ts[4:6]}-{ts[6:8]}.csv"
    nuevo = not destino.exists()
    with destino.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            w.writeheader()
        w.writerows(filas)


def leer_procesados() -> set[str]:
    if not PROCESADOS.exists():
        return set()
    return set(PROCESADOS.read_text(encoding="utf-8").split())


def marcar(clave: str) -> None:
    with PROCESADOS.open("a", encoding="utf-8") as f:
        f.write(clave + "\n")


def ultimo_ts(flujo: str) -> str | None:
    r = get(LASTUPDATE[flujo], timeout=60)
    if r is None:
        return None
    m = re.search(r"/(\d{14})\.(?:translation\.)?gkg\.csv\.zip", r.text)
    return m.group(1) if m else None


def timestamps_pendientes(ultimo: str, procesados: set[str], flujo: str, horas: float) -> list[str]:
    fin = datetime.strptime(ultimo, "%Y%m%d%H%M%S")
    inicio = fin - timedelta(hours=horas)
    ts, t = [], fin
    while t > inicio:
        clave = f"{flujo}:{t:%Y%m%d%H%M%S}"
        if clave not in procesados:
            ts.append(t.strftime("%Y%m%d%H%M%S"))
        t -= timedelta(minutes=15)
    return sorted(ts)


def pasada(horas_recuperar: float) -> int:
    procesados = leer_procesados()
    total = 0
    for flujo in ("ingles", "traducido"):
        ultimo = ultimo_ts(flujo)
        if ultimo is None:
            log.warning("No pude leer lastupdate de %s", flujo)
            continue
        for ts in timestamps_pendientes(ultimo, procesados, flujo, horas_recuperar):
            r = get(GKG_URL[flujo].format(ts=ts))
            clave = f"{flujo}:{ts}"
            if r is None:
                # GDELT a veces publica el aviso antes que el archivo (o el CDN cachea un 404):
                # solo se da por perdido si tiene más de 3 horas; si no, se reintenta después.
                edad = datetime.now(timezone.utc).replace(tzinfo=None) - datetime.strptime(ts, "%Y%m%d%H%M%S")
                if edad > timedelta(hours=3):
                    log.info("%s no existe; se marca como perdido", clave)
                    marcar(clave + ":sin_archivo")
                else:
                    log.info("%s aún no disponible; se reintenta en la siguiente pasada", clave)
                continue
            try:
                filas = procesar_gkg(r.content, f"{ts}.{'translation.' if flujo == 'traducido' else ''}gkg")
            except zipfile.BadZipFile:
                log.warning("Zip dañado en %s", clave)
                continue
            escribir(filas, ts)
            marcar(clave)
            total += len(filas)
            log.info("%s: %d documentos de Mérida", clave, len(filas))
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="una sola pasada y salir")
    ap.add_argument("--max-recuperar-horas", type=float, default=24.0,
                    help="horas hacia atrás que se recuperan tras un corte")
    ap.add_argument("--backfill-horas", type=float, default=0.0,
                    help="en la primera pasada, bajar también estas horas hacia atrás")
    args = ap.parse_args()

    STREAM_DIR.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
    if sys.stderr is not None:  # con pythonw.exe no hay consola
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)

    # Una sola instancia a la vez (sirve para la tarea programada): candado sobre un archivo
    # que el sistema libera solo si el proceso muere.
    candado = open(STREAM_DIR / "_recorder.lock", "a+")
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(candado.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(candado.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log.info("Ya hay otro grabador corriendo; esta instancia termina.")
        return
    PID_FILE.write_text(str(os.getpid()), encoding="ascii")
    horas = max(args.backfill_horas, 0.0)
    while True:
        try:
            n = pasada(horas if horas > 0 else args.max_recuperar_horas)
            log.info("Pasada terminada: %d filas nuevas", n)
        except Exception:  # noqa: BLE001 — el grabador no debe morir por un error puntual
            log.exception("Error inesperado en la pasada")
        horas = 0.0
        if args.once:
            break
        time.sleep(INTERVALO_S - (time.time() % INTERVALO_S) + 120)  # ~2 min después del cuarto de hora


if __name__ == "__main__":
    main()
