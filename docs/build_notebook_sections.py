"""Construye un Colab con dos bloques autónomos y datos incorporados."""
from pathlib import Path
import ast,base64,io,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/sources.json').read_text())
groups=json.loads((ROOT/'data/groups_2026.json').read_text())
reference=json.loads((ROOT/'outputs/results.json').read_text())
source=(ROOT/'src/analyze.py').read_text()
funcs={n.name:ast.get_source_segment(source,n) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
chart=funcs['charts'];split=chart.index('    cv = r["cape_verde"]');prefix=chart[:chart.index('    h = ch[')]
header=source[source.index('from pathlib'):source.index('def historical():')].replace('from models import goal_rates, probabilities, group_sim, summarize, interval','').replace('ROOT = Path(__file__).resolve().parents[1]','')
old = {'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}, 'colab': {'name': 'Futbol_probabilidad.ipynb'}}}
comparefunc = 'def compare(a, b, path="resultado"):\n    if isinstance(a, dict):\n        assert a.keys() == b.keys(), path\n        for key in a: compare(a[key], b[key], path + "." + key)\n    elif isinstance(a, list):\n        assert len(a) == len(b), path\n        for i, (x,y) in enumerate(zip(a,b)): compare(x,y,path+f"[{i}]")\n    elif isinstance(a, (int,float)):\n        assert np.isclose(a,b,rtol=1e-9,atol=1e-12), (path,a,b)\n    else: assert a == b, (path,a,b)\n\n'

# Proyección verificable: conserva exclusivamente las columnas y eventos utilizados.
# Los originales completos permanecen en el paquete del proyecto.
import hashlib
import pandas as pd
COMPACT = ROOT / '.build/colab_compact'
COMPACT.mkdir(parents=True, exist_ok=True)
for name in list(manifest):
    source_path = ROOT / 'data/raw' / name
    original_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if original_hash != manifest[name]['sha256']:
        raise ValueError('Cambió el original: ' + name)
    dest = COMPACT / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if name.startswith('events/'):
        events = json.loads(source_path.read_text())
        last = max((i for i,e in enumerate(events) if e['period']==2),
                   key=lambda i: events[i]['minute']*60+events[i]['second'])
        keep=[]
        for i,event in enumerate(events):
            if i==last or event.get('shot',{}).get('outcome',{}).get('name')=='Goal' or event['type']['name']=='Own Goal Against':
                keep.append({k:event[k] for k in ['type','shot','team','minute','second','period','player'] if k in event})
        dest.write_text(json.dumps(keep,separators=(',',':'),ensure_ascii=False))
        del events,keep
    elif name=='clubelo_archive.csv':
        chunks=pd.read_csv(source_path,chunksize=20000)
        pd.concat([c[(c.country=='GER') & (c.date=='2023-08-15')] for c in chunks]).to_csv(dest,index=False)
    elif name=='germany.csv':
        frame=pd.read_csv(source_path)
        frame[(frame.tier==1)&frame.Season.between(1963,2023)].to_csv(dest,index=False)
        del frame
    elif name=='leverkusen_matches_statsbomb.json':
        matches=json.loads(source_path.read_text())
        dest.write_text(json.dumps([{k:m[k] for k in ['match_id','match_date','home_team','away_team','home_score','away_score']} for m in matches],separators=(',',':')))
    else:
        dest.write_bytes(source_path.read_bytes())
    manifest[name] = {**manifest[name], 'original_sha256':original_hash,
                      'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
                      'representation':'Proyección de campos y registros usados; original disponible en el proyecto'}

def payload(names):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        for name in names:z.write(COMPACT/name,name)
    return base64.b64encode(b.getvalue()).decode()

def loader(names):
 return '''# Copia histórica incorporada: no se consulta ningún servidor de datos.
# Extrae solo los nombres del manifiesto y verifica cada archivo antes de analizarlo.
import base64, io, zipfile, hashlib, gc
MANIFEST = '''+repr({n:manifest[n] for n in names})+'''
DATA_ARCHIVE_BASE64 = '''+repr(payload(names))+'''
with zipfile.ZipFile(io.BytesIO(base64.b64decode(DATA_ARCHIVE_BASE64))) as archive:
    for name, meta in MANIFEST.items():
        data = archive.read(name)
        if hashlib.sha256(data).hexdigest() != meta["sha256"]:
            raise ValueError("Los datos incorporados no coinciden: " + name)
        dest = RAW / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
(ROOT / "data/sources.json").write_text(json.dumps(MANIFEST, indent=2))
print(f"{len(MANIFEST)} archivos restaurados y verificados; sin descarga HTTP.")
del DATA_ARCHIVE_BASE64, data, archive
gc.collect()
'''

def make(kind):
 iscv=kind=='cabo_verde';title='Cabo Verde' if iscv else 'Leverkusen y rescates tardíos';part=2 if iscv else 1
 names=[n for n in manifest if n.startswith('national/') or n=='elo_teams.tsv'] if iscv else [n for n in manifest if not n.startswith('national/') and n not in ['elo_teams.tsv','dsfs_bundesliga_history.pdf']]
 cells=[]
 def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
 def code(s):cells.append(dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=s.splitlines(True)))
 md(f'''# {title}
**Universidad del Istmo · Análisis de Datos**  
**Catedrático:** Juan Andrés García Porres

Didvin Nohel Estrada Pineda · 14092  
Jose Humberto Najar Venavente · 13661  
Pablo Rodolfo Alexander Flores Mollinedo · 14643

## Cómo ejecutarlo
Sube este archivo a [Google Colab](https://colab.research.google.com/) y selecciona **Entorno de ejecución → Ejecutar todas**. No requiere el otro notebook, ZIP externo, GitHub, credenciales ni GPU. Los datos necesarios de esta parte están comprimidos **dentro del notebook**. La primera celda instala las bibliotecas; la carga de datos no hace peticiones HTTP.

La celda de datos es larga porque conserva la copia del estudio, no por complejidad del análisis. Puedes mantenerla contraída. Se comprueba la huella SHA-256 de cada archivo antes de usarlo. Se conservan los cortes históricos y los supuestos del informe; no se reemplazan por valoraciones actuales.

Este cuaderno genera {3 if iscv else 6} gráficas PNG/SVG, tablas, resultados JSON y un ZIP descargable. La ejecución usa 10 000 simulaciones por escenario y semilla 14643.''')
 code('%pip -q install numpy pandas scipy matplotlib\n')
 code('''from pathlib import Path
import json, math
from IPython.display import display, Image, Markdown
import gc
# Evita que IPython conserve resultados grandes en su caché Out.
try:
    get_ipython().cache_size = 0
    get_ipython().displayhook.cache_size = 0
except NameError:
    pass
ROOT = Path.cwd() / "'''+kind+'''_colab"
RAW = ROOT / "data/raw"
OUT = ROOT / "outputs"
PROC = ROOT / "data/processed"
for directory in (RAW, PROC, OUT / "figures"):
    directory.mkdir(parents=True, exist_ok=True)
''')
 md('## Datos verificables\nSe restaura exclusivamente la copia de datos correspondiente a este caso. La procedencia se conserva en `data/sources.json`.')
 code(loader(names))
 if iscv:code('GROUPS = '+repr(groups)+'\n(ROOT / "data/groups_2026.json").write_text(json.dumps(GROUPS))')
 md('## Notación, variables y supuestos')
 for section in json.loads((ROOT/'docs/variables.json').read_text()):
  if section['part'] in [0,part]:md('### '+section['title']+'\n\n'+'\n\n'.join(section['paragraphs']))
 md(r'''### Enlace probabilístico
$\Delta=R_i-R_j+h$, $E=(1+10^{-\Delta/400})^{-1}$. Ajustamos las tasas de dos Poisson independientes para que $E=P(G_i>G_j)+\frac12P(G_i=G_j)$. La diferencia de goles sigue Skellam. El parámetro $\tau$ es la escala base de goles, no una suma fija de tasas para todos los rivales.

$N$ es el número de simulaciones, $K$ el número de éxitos y $\hat p=K/N$. Los intervalos exactos binomiales miden solamente precisión Monte Carlo. Las fuerzas quedan fijas; no modelamos incertidumbre de Elo.''')
 code((ROOT/'src/models.py').read_text())
 code(header)
 if iscv:
  for name,desc in [('national_ratings','Selecciona el último Elo anterior al corte.'),('national_goal_reference','Respalda τ=2.7 con el promedio de goles observado en partidos de selecciones.'),('qualify_world','Simula todos los grupos y la clasificación de terceros; admite tres empates condicionados.'),('cape_verde','Ejecuta la eliminatoria sin repechaje, el grupo mundialista y la ruta fija del ejercicio.')]:
   md('### '+desc);code(funcs[name])
  md('## Simulación completa de Cabo Verde\nLa ruta eliminatoria es contrafactual y supone avance en todos los empates. La condición de tres empates usa su propio denominador.')
  code('cape_result = cape_verde()\nr = {"seed": SEED, "n": N, "cape_verde": cape_result}\nprint(json.dumps(cape_result, indent=2, ensure_ascii=False))\ndisplay(pd.DataFrame(cape_result["scenarios"]).T)')
  plotcode=prefix.replace('def charts(df, ch, r):','def charts_case(r):')+chart[split:]
  call='charts_case(r)';ref={k:reference[k] for k in ['seed','n','cape_verde']}
 else:
  md('## Reconstrucción histórica\nSe calcula la tabla de cada temporada. La corrección de Stuttgart 1991/92 está documentada en el código porque el archivo de partidos es incompleto.')
  code(funcs['historical']);code('df, ch, history = historical()\ndisplay(pd.read_csv(PROC / "champions_1964_2023.csv"))\ndisplay(pd.DataFrame(history["fits"]))')
  md('## Invicto, Monte Carlo y extra de rescates\nSe reconstruyen las probabilidades por partido, 10 000 temporadas y los cuatro rescates. Q es un diagnóstico retrospectivo, no un efecto causal de la suerte.')
  code(funcs['leverkusen']);code('leverkusen_result = leverkusen(df, ch)\nr = {"seed": SEED, "n": N, "history": history, "leverkusen": leverkusen_result}\nprint(json.dumps(r, indent=2, ensure_ascii=False))\ndisplay(pd.DataFrame(leverkusen_result["rescues"]))')
  plotcode=chart[:split].replace('def charts(df, ch, r):','def charts_case(df, ch, r):');call='charts_case(df, ch, r)';ref={k:reference[k] for k in ['seed','n','history','leverkusen']}
 md('## Gráficas de esta parte\nEl código siguiente dibuja todas las figuras del caso y conserva versiones PNG y SVG.')
 code(plotcode)
 code('(OUT / "results.json").write_text(json.dumps(r, indent=2, ensure_ascii=False))\n'+call+'\nfor figure in sorted((OUT / "figures").glob("*.png")):\n    display(Markdown("### " + figure.stem.replace("_", " ")))\n    display(Image(filename=str(figure),width=800))')
 md('## Verificación numérica\nSe contrasta el resultado calculado con el del informe. Si cambias la semilla, N o el modelo, no se espera la misma realización Monte Carlo.')
 code('REFERENCE = '+repr(ref)+'\n'+comparefunc+'\ncompare(r, REFERENCE)\nassert len(list((OUT / "figures").glob("*.png"))) == '+str(3 if iscv else 6)+'\nprint("Resultados de esta parte verificados.")')
 md('## Fórmulas con datos, despejes y resultados')
 for example in json.loads((ROOT/'docs/numeric_examples.json').read_text()):
  if example['part'] == part:
   md('### '+example['title']+'\n\n'+'\n\n'.join(example['formulas'])+'\n\n'+example['explanation'])
   code('# Recalcula la sustitución numérica con los valores de esta parte.\n'+example['code'])
 md('## Conclusiones')
 for conclusion in json.loads((ROOT/'docs/conclusions.json').read_text()):
  if conclusion['part'] in [part,3]:
   md('### '+conclusion['title']+'\n\n'+'\n\n'.join(conclusion['paragraphs']))
 md('## Referencias\n'+('\n'.join(['- [World Football Elo Ratings](https://www.eloratings.net/)','- [CAF: formato clasificatorio](https://www.cafonline.com/news/everything-you-need-to-know-about-2026-world-cup-qualifying-for-africa/)','- [FIFA: clasificación y desempates](https://www.fifa.com/es/tournaments/mens/worldcup/canadamexicousa2026/articles/grupos-como-funcionan-clasificacion-criterios-desempate)']) if iscv else '\n'.join(['- [Curley: engsoccerdata](https://github.com/jalapic/engsoccerdata)','- [Archivo ClubElo](https://github.com/xgabora/Club-Football-Match-Data)','- [StatsBomb Open Data](https://github.com/statsbomb/open-data)','- [DSFS: tablas históricas](https://www.dsfs.de/wp-content/uploads/2024/01/Bundesliga_Geschichte_Tabellen.pdf)']))+'\n- [SciPy: Skellam](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skellam.html)\n- Goldsman y Goldsman, libro del curso, capítulos 1 y 4–6.\n\nLas URL documentan la procedencia; no se necesita acceder a ellas para ejecutar el análisis.')
 md('## Descargar tablas, datos y gráficas\nEl ZIP incluye los datos necesarios de esta parte, los procesados y los resultados.')
 code('''bundle = ROOT / "resultados_'''+kind+'''.zip"
with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
    for directory in (ROOT / "data", OUT):
        for file in directory.rglob("*"):
            if file.is_file(): z.write(file, file.relative_to(ROOT))
try:
    from google.colab import files
    files.download(str(bundle))
except ImportError:
    print("Resultados guardados en:", bundle)
''')
 for i,c in enumerate(cells):c['id']=f'{kind}-{i:03}'
 nb=dict(nbformat=4,nbformat_minor=5,metadata=old['metadata'],cells=cells)
 return nb

parts=[make('leverkusen'),make('cabo_verde')]
cells=[]
def markdown(s):
 return dict(cell_type='markdown',metadata={},source=s.splitlines(True))
cells.append(markdown("""# Probabilidad de las hazañas del fútbol
**Universidad del Istmo · Análisis de Datos**  
**Catedrático:** Juan Andrés García Porres

Didvin Nohel Estrada Pineda · 14092  
Jose Humberto Najar Venavente · 13661  
Pablo Rodolfo Alexander Flores Mollinedo · 14643

## Guía de ejecución
Este es un solo notebook con dos partes completas y claramente separadas:
1. **Leverkusen:** historia de la Bundesliga, invicto, simulación y extra de rescates, con sus seis gráficas.
2. **Cabo Verde:** eliminatoria, escenarios del grupo y ruta al título, con sus tres gráficas.

Sube este archivo a [Google Colab](https://colab.research.google.com/) y selecciona **Ejecutar todas**. No requiere GPU, credenciales ni subir un ZIP. Los datos necesarios están incorporados como una proyección compacta y se verifican con SHA-256. Se conservan todos los goles, autogoles y el último evento del segundo tiempo de cada partido, así como los registros históricos y Elo utilizados. Los originales completos y sus huellas permanecen en el paquete del proyecto. La instalación de bibliotecas necesita conexión; los cálculos y la carga de datos no consultan a los proveedores.

Cada parte mantiene su propio directorio de resultados y puede ejecutarse desde su encabezado después de la instalación. Al final se descarga un único ZIP con ambas carpetas. Las fuentes se filtran antes de incorporarlas; se libera la memoria al pasar de Leverkusen a Cabo Verde. El muestreo sigue usando 10 000 repeticiones y las mismas semillas.
"""))
cells.append(parts[0]['cells'][1])
for idx,nb in enumerate(parts):
 if idx:
  cells.append(dict(cell_type='code',execution_count=None,outputs=[],metadata={},source=[
   "# Los resultados ya están en disco; liberar objetos de Leverkusen antes de Cabo Verde.\n",
   "import gc\n",
   "import matplotlib.pyplot as plt\n",
   "plt.close('all')\n",
   "for variable in ['df','ch','history','leverkusen_result','r','REFERENCE','MANIFEST']:\n",
   "    globals().pop(variable, None)\n",
   "goal_rates.cache_clear()\n",
   "gc.collect()\n"] ))
 label='PARTE I · LEVERKUSEN Y EXTRA' if idx==0 else 'PARTE II · CABO VERDE'
 cells.append(markdown('# '+label+'\n\nEn este bloque se cargan los datos y se ejecutan exclusivamente los cálculos y las gráficas de esta parte.'))
 for c in nb['cells'][2:]:
  text=''.join(c['source'])
  if c['cell_type']=='code' and text.startswith('bundle = ROOT'):
   text=text[:text.index('try:')]+'print("Resultados de esta parte:", bundle)\n'
   c['source']=text.splitlines(True)
  cells.append(c)
cells.append(markdown('# Descarga final · ambas partes\nEl ZIP conserva carpetas distintas para Leverkusen y Cabo Verde, incluyendo fuentes, tablas y gráficas.'))
cells.append(dict(cell_type='code',execution_count=None,outputs=[],metadata={},source="""from pathlib import Path
import zipfile
combined = Path.cwd() / "resultados_futbol.zip"
with zipfile.ZipFile(combined, "w", zipfile.ZIP_DEFLATED) as archive:
    for case in ["leverkusen_colab", "cabo_verde_colab"]:
        for file in (Path.cwd() / case).rglob("*"):
            if file.is_file() and file.suffix != ".zip":
                archive.write(file, file.relative_to(Path.cwd()))
try:
    from google.colab import files
    files.download(str(combined))
except ImportError:
    print("Paquete completo:", combined)
""".splitlines(True)))
for i,c in enumerate(cells):c['id']=f'futbol-{i:03}'
nb=dict(nbformat=4,nbformat_minor=5,metadata=old['metadata'],cells=cells)
nb['metadata']['colab']={'name':'Futbol_probabilidad.ipynb'}
(ROOT/'notebooks/Futbol_probabilidad.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))
print('Un notebook:',len(cells),'celdas')
