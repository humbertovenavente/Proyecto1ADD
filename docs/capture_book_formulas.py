"""Conserva dos recortes de fórmulas del texto de referencia del curso."""
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import subprocess
ROOT=Path(__file__).resolve().parents[1]
source=Path('/Users/pabloflores/Downloads/A First Course In Probability Goldsman (4).pdf')
r=PdfReader(source);target=ROOT/'assets/math';target.mkdir(exist_ok=True)
for name,index,box in [('book_binomial',133,(52,646,336,672)),('book_poisson',139,(52,648,407,671))]:
 w=PdfWriter();page=r.pages[index];page.cropbox.lower_left=box[:2];page.cropbox.upper_right=box[2:];w.add_page(page)
 file=ROOT/'.build'/f'{name}.pdf';w.write(file)
 subprocess.run(['/Users/pabloflores/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm','-cropbox','-singlefile','-r','600','-png',str(file),str(target/name)],check=True)
