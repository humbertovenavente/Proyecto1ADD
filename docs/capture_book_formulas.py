"""Conserva dos recortes de fórmulas del texto de referencia del curso.

El libro no se redistribuye con el proyecto: hay que apuntar BOOK_PDF al archivo
propio. pdftoppm se toma del PATH, o de PDFTOPPM si está en otra ubicación.
"""
import os, shutil, subprocess
from pathlib import Path
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
source = Path(os.environ.get("BOOK_PDF", Path.home() / "Downloads/A First Course In Probability Goldsman (4).pdf"))
if not source.exists():
    raise SystemExit(f"No se encontró el libro en {source}. Defina BOOK_PDF con la ruta local.")
pdftoppm = os.environ.get("PDFTOPPM") or shutil.which("pdftoppm")
if not pdftoppm:
    raise SystemExit("No se encontró pdftoppm en el PATH. Instale poppler o defina PDFTOPPM.")

r = PdfReader(source)
target = ROOT / "assets/math"
target.mkdir(exist_ok=True)
(ROOT / ".build").mkdir(exist_ok=True)
for name, index, box in [("book_binomial", 133, (52, 646, 336, 672)), ("book_poisson", 139, (52, 648, 407, 671))]:
    w = PdfWriter()
    page = r.pages[index]
    page.cropbox.lower_left = box[:2]
    page.cropbox.upper_right = box[2:]
    w.add_page(page)
    file = ROOT / ".build" / f"{name}.pdf"
    w.write(file)
    subprocess.run([pdftoppm, "-cropbox", "-singlefile", "-r", "600", "-png", str(file), str(target / name)], check=True)
