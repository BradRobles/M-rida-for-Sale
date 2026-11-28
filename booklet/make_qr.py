"""
Genera el código QR en SVG y PNG para las escenas AR del booklet Mérida for Sale.

Uso:
    python booklet/make_qr.py
    python booklet/make_qr.py https://otra-url.github.io/ruta/al/ar/
"""
from __future__ import annotations

import sys
from pathlib import Path
import qrcode
import qrcode.image.svg

DEFAULT_URL = "https://bradrobles.github.io/Merida-for-Sale/booklet/ar/"
ASSETS = Path(__file__).resolve().parent / "assets"


def generate_qr(url: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    # PNG de alta resolución (paleta verde Mérida sobre blanco)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=14,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1F5F5B", back_color="#FFFFFF")
    png_path = ASSETS / "qr_ar.png"
    img.save(png_path)

    # SVG vectorial limpio para impresión y web
    qr_svg = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
        image_factory=qrcode.image.svg.SvgPathImage,
    )
    qr_svg.add_data(url)
    qr_svg.make(fit=True)
    svg_img = qr_svg.make_image(fill_color="#1F5F5B", back_color="#FFFFFF")
    svg_path = ASSETS / "qr_ar.svg"
    svg_img.save(svg_path)
    # Colorear el path SVG en verde Mérida
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_text = svg_text.replace('fill="#000000"', 'fill="#1F5F5B"')
    svg_path.write_text(svg_text, encoding="utf-8")

    print(f"QR generado para: {url}")
    print(f"  - {png_path}")
    print(f"  - {svg_path}")


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    generate_qr(target_url)
