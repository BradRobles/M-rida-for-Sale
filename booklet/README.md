# Mérida en venta · Booklet final (D3.js + AR)

Versión final en español del booklet **Mérida en venta** (*Visual Modeling for Information*, UPY Data 9B — Equipo 9: Julio César De Aquino Castellanos, Brad Robles García y Eliana Lorely Osorio Martínez).

Todas las gráficas están construidas en **D3.js v7**, las cifras clave se alimentan de las tablas limpias en `booklet/data/`, y la escena 3D del Centro entra como **imagen estática con código QR** (además de incluir las 3 escenas AR interactivas en `<model-viewer>` para exploración móvil).

## Estructura

```text
booklet/
├── index.html                  # Booklet completo en español (prólogo + 5 capítulos, D3.js v7)
├── styles.css                  # Paleta editorial Mérida en venta + estilos @media print
├── charts.js                   # Gráficas interactivas en D3.js v7
├── data/                       # Tablas CSV y GeoJSON autocontenidas
├── ar/
│   ├── index.html              # Visor AR móvil (<model-viewer>) al que apunta el código QR
│   └── models/
│       ├── escena_1_centro_manzana.glb
│       ├── escena_2_turistas_barras3d.glb
│       └── escena_3_aeropuertos_cordilleras.glb
├── assets/
│   ├── centro_3d.png           # Imagen estática del 3D del Centro (831 manzanas, INEGI 2015)
│   ├── qr_ar.svg               # Código QR vectorial hacia GitHub Pages (booklet/ar/)
│   └── qr_ar.png               # Código QR PNG en alta resolución
├── make_qr.py                  # Script para regenerar el QR si cambia la URL de despliegue
└── README.md
```

## Cómo abrirlo localmente

Como D3 carga los archivos CSV y GeoJSON con `fetch()`, ábrelo con un servidor HTTP local desde la raíz del repo:

```bash
python -m http.server 8000
```

Y abre en tu navegador:
- Booklet completo: `http://localhost:8000/booklet/`
- Visor AR dedicado (destino del QR): `http://localhost:8000/booklet/ar/`

## Publicación del QR (GitHub Pages)

El código QR incluido apunta a:

`https://bradrobles.github.io/M-rida-for-Sale/booklet/ar/`

Para activarlo en GitHub: **Settings → Pages → Build and deployment → Deploy from a branch (`main`, `/ (root)`)**. Si se aloja en otra URL (por ejemplo un repositorio grupal), regenera el QR ejecutando:

```bash
python booklet/make_qr.py https://TU_DOMINIO/ruta/al/ar/
```
