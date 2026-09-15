"""Punto de entrada para reconstruir el único notebook y la copia de datos."""
from pathlib import Path
import runpy,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'docs/build_notebook_sections.py'),run_name='__main__')
manifest=json.loads((ROOT/'data/sources.json').read_text())
with zipfile.ZipFile(ROOT/'outputs/datos_colab.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in manifest:z.write(ROOT/'data/raw'/name,'data/raw/'+name)
