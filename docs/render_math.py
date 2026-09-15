"""Fórmulas LaTeX para la presentación, renderizadas con MathText."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
L=json.loads((ROOT/'outputs/results.json').read_text())['leverkusen']
q=f"{L['Q']:.3e}".split('e')
formulas={'elo':r'$E=\frac{1}{1+10^{-\Delta/400}}$', 'poisson':r'$P(D=0)=e^{-\lambda}$', 'rescues':r'$Q=\prod_{i=1}^{4}q_i='+q[0]+r'\times 10^{'+str(int(q[1]))+r'}\qquad 1/Q\approx '+str(round(L['inverse_Q']))+'$'}
formulas['invicto'] = r'$P(\mathrm{invicto})=\prod_{j=1}^{34}p_j=P(\mathrm{no\ perder\ ante\ Bayern\ dos\ veces})\prod_{j\in\mathrm{otros}}p_j$'
formulas['ruta'] = r'$P(\mathrm{t\acute itulo}\mid\mathrm{supera\ Argentina\ y\ ruta\ fija})=\prod_{i=1}^{4}[P(G_i)+P(E_i)]$'
for idx, section in enumerate(json.loads((ROOT/'docs/methodology.json').read_text())):
    formulas['method_'+str(idx)] = section['formula'].replace(r'\mathcal I',r'\mathcal{I}').replace(r'\frac12',r'\frac{1}{2}').replace(r'\overline D',r'\overline{D}').replace(r'\#(A\cap B)',r'n_{A\cap B}').replace(r'\#B',r'n_B')
for gi, group in enumerate(json.loads((ROOT/'docs/notation.json').read_text())):
    for ri, row in enumerate(group['rows']):
        formulas[f'notation_{gi}_{ri}'] = '$'+row[0]+'$'
for ni, example in enumerate(json.loads((ROOT/'docs/numeric_examples.json').read_text())):
    for fi, formula in enumerate(example['formulas']):
        formulas[f'numeric_{ni}_{fi}'] = formula.replace(r'\frac12',r'\frac{1}{2}')
(ROOT/'assets/math').mkdir(exist_ok=True)
for name,formula in formulas.items():
    formula = formula.replace(r'\overline D',r'\overline{D}')
    fig=plt.figure(figsize=(9,1.2))
    fig.text(.5,.5,formula,ha='center',va='center',fontsize=34,color='#17242C')
    fig.savefig(ROOT/f'assets/math/{name}.png',dpi=450,transparent=True,bbox_inches='tight',pad_inches=.04)
    plt.close(fig)

(ROOT / "assets/math/render_settings.json").write_text(json.dumps({"dpi":450,"font_size_pt":34}))
