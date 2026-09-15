"""Compone el informe a partir de los resultados y de los datos verificados."""

from pathlib import Path
import json, csv, re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT / "outputs/results.json").read_text())
L = r["leverkusen"]
C = r["cape_verde"]
H = r["history"]
P = lambda x: f"{100 * x:.2f} %"
def small(x):
    mantissa, exponent = f"{x:.3e}".split("e")
    return mantissa + " × 10" + str(int(exponent)).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.7)
sec.bottom_margin = Inches(0.7)
sec.left_margin = sec.right_margin = Inches(0.85)
sec.page_width = Inches(8.27)
sec.page_height = Inches(11.69)
for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2"]:
    st = doc.styles[name]
    st.font.name = "Calibri"
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.font.size = Pt(
        11
        if name == "Normal"
        else 23
        if name == "Title"
        else 17
        if name == "Heading 1"
        else 13
    )
    st.paragraph_format.space_after = Pt(7)
    for border in list(st.element.xpath(".//w:pBdr")):
        border.getparent().remove(border)
doc.styles["Normal"].paragraph_format.line_spacing = 1.12
footer = sec.footer.paragraphs[0]
footer.alignment = 2
footer.add_run("Análisis de Datos  |  ")
f = OxmlElement("w:fldSimple")
f.set(qn("w:instr"), "PAGE")
footer._p.append(f)
content = []



SUP = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "−0123456789")
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉ᵢₐᵣ₌", "0123456789iar=")

def math_runs(paragraph, value, equation=False):
    """Exponentes e índices reales de Word; fórmulas en Cambria Math."""
    value = value.replace("10^(−Δ/400)", "10⁽⁻Δ⁄⁴⁰⁰⁾")
    for token in re.split(r"([⁻⁰¹²³⁴⁵⁶⁷⁸⁹⁽⁾Δ⁄]+|[₀₁₂₃₄₅₆₇₈₉ᵢₐᵣ₌]+)", value):
        if not token:
            continue
        run = paragraph.add_run(token)
        if re.fullmatch(r"[⁻⁰¹²³⁴⁵⁶⁷⁸⁹⁽⁾Δ⁄]+", token) and any(c in token for c in "⁰¹²³⁴⁵⁶⁷⁸⁹"):
            run.text = token.translate(SUP).replace("⁽", "(").replace("⁾", ")").replace("⁄", "/")
            run.font.superscript = True
        elif re.fullmatch(r"[₀₁₂₃₄₅₆₇₈₉ᵢₐᵣ₌]+", token):
            run.text = token.translate(SUB)
            run.font.subscript = True
        if equation:
            run.font.name = "Cambria Math"
            run.font.size = Pt(11)


def title(t):
    doc.add_heading(t, 1)
    content.append({"title": t, "blocks": []})


def p(t):
    paragraph = doc.add_paragraph()
    math_runs(paragraph, t)
    content[-1]["blocks"].append({"type": "p", "text": t})


def eq(t):
    q = doc.add_paragraph()
    q.alignment = 1
    if t.startswith("P(invicto) =") or t.startswith("P(título |"):
        name = "invicto" if t.startswith("P(invicto)") else "ruta"
        q.add_run().add_picture(str(ROOT / f"assets/math/{name}.png"), width=Inches(6.3))
    elif t.startswith("E = 1 /"):
        from lxml import etree
        ns = "http://schemas.openxmlformats.org/officeDocument/2006/math"
        xml = '<m:oMath xmlns:m="'+ns+'"><m:r><m:t>E = </m:t></m:r><m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>1 + </m:t></m:r><m:sSup><m:e><m:r><m:t>10</m:t></m:r></m:e><m:sup><m:r><m:t>−Δ/400</m:t></m:r></m:sup></m:sSup></m:den></m:f><m:r><m:t> = P(victoria) + ½ P(empate)</m:t></m:r></m:oMath>'
        q._p.append(etree.fromstring(xml))
    else:
        math_runs(q, t, equation=True)
    content[-1]["blocks"].append({"type": "equation", "text": t})


def table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = True
    for c, x in zip(t.rows[0].cells, headers):
        math_runs(c.paragraphs[0], str(x))
    for row in rows:
        for c, x in zip(t.add_row().cells, row):
            math_runs(c.paragraphs[0], str(x))
    for ri, row in enumerate(t.rows):
        for c in row.cells:
            tcpr = c._tc.get_or_add_tcPr()
            b = OxmlElement("w:tcBorders")
            for side in ["top", "left", "bottom", "right"]:
                e = OxmlElement("w:" + side)
                e.set(qn("w:val"), "single")
                e.set(qn("w:sz"), "4")
                e.set(qn("w:color"), "D9D9D9")
                b.append(e)
            tcpr.append(b)
            shade = OxmlElement("w:shd")
            shade.set(
                qn("w:fill"),
                "E3E9ED" if ri == 0 else "F5F7F8" if ri % 2 == 0 else "FFFFFF",
            )
            tcpr.append(shade)
            for pp in c.paragraphs:
                pp.paragraph_format.space_after = Pt(3)
                pp.paragraph_format.space_before = Pt(3)
                for rr in pp.runs:
                    rr.font.size = Pt(9)
                    rr.bold = ri == 0
    rep = OxmlElement("w:tblHeader")
    t.rows[0]._tr.get_or_add_trPr().append(rep)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    content[-1]["blocks"].append({"type": "table", "headers": headers, "rows": rows})


def fig(name, caption, width=6.3):
    doc.add_picture(str(ROOT / f"outputs/figures/{name}.png"), width=Inches(width))
    q = doc.add_paragraph(caption)
    q.paragraph_format.space_after = Pt(6)
    for rr in q.runs:
        rr.font.size = Pt(9)
        rr.italic = True
    content[-1]["blocks"].append({"type": "figure", "name": name, "caption": caption})


def new(t):
    doc.add_page_break()
    title(t)



def variables(which):
    first = True
    for section in json.loads((ROOT / "docs/variables.json").read_text()):
        if section["part"] != which:
            continue
        if first:
            new(section["title"])
            first = False
        else:
            title(section["title"])
        for paragraph in section["paragraphs"]:
            p(paragraph)
        if which == 0:
            p("Referencia: ClubElo, explicación del sistema: https://clubelo.com/System. Arpad Elo, The Rating of Chessplayers, Past and Present (1978). Fundamentos de variables aleatorias: Goldsman y Goldsman, capítulos 4–6.")

def notation(part):
    groups = json.loads((ROOT / "docs/notation.json").read_text())
    for gi, group in enumerate(groups):
        if group["part"] != part:
            continue
        new("Notación: " + group["title"])
        p("Los símbolos se interpretan dentro de este caso. Cuando una letra cambia de significado entre secciones, se indica expresamente para evitar confundir eventos, parámetros y resultados.")
        t = doc.add_table(rows=0, cols=2)
        for ri, row in enumerate(group["rows"]):
            cells = t.add_row().cells
            cells[0].width = Inches(2.0)
            cells[1].width = Inches(4.45)
            from PIL import Image
            image_path = ROOT / f"assets/math/notation_{gi}_{ri}.png"
            with Image.open(image_path) as symbol_image:
                symbol_width = min(1.85, 0.45 * symbol_image.width / symbol_image.height)
            cells[0].paragraphs[0].add_run().add_picture(str(image_path), width=Inches(symbol_width))
            math_runs(cells[1].paragraphs[0], row[1])
            for cell in cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before = Pt(12)
                    paragraph.paragraph_format.space_after = Pt(16)

def conclusion(which):
    section = next(x for x in json.loads((ROOT / "docs/conclusions.json").read_text()) if x["part"] == which)
    new(section["title"])
    for paragraph in section["paragraphs"]:
        p(paragraph)

def numerical_examples(part):
    selected = 0
    from PIL import Image
    for ni, example in enumerate(json.loads((ROOT / 'docs/numeric_examples.json').read_text())):
        if example['part'] != part:
            continue
        if selected % 2 == 0:
            new('Cálculos con datos: ' + ('Leverkusen' if part == 1 else 'Cabo Verde'))
        title(example['title'])
        for fi in range(len(example['formulas'])):
            path = ROOT / f'assets/math/numeric_{ni}_{fi}.png'
            with Image.open(path) as im:
                width = min(6.2, im.width * 12 / (34 * 450))
            paragraph = doc.add_paragraph()
            paragraph.alignment = 1
            paragraph.add_run().add_picture(str(path), width=Inches(width))
        p(example['explanation'])
        selected += 1

def development(part):
    sections = json.loads((ROOT / "docs/methodology.json").read_text())
    for index, section in enumerate(sections):
        if section["part"] != part:
            continue
        new(section["title"])
        for paragraph in section["paragraphs"][:1]:
            p(paragraph)
        q = doc.add_paragraph()
        q.alignment = 1
        q.add_run().add_picture(str(ROOT / f"assets/math/method_{index}.png"), width=Inches(6.25))
        for paragraph in section["paragraphs"][1:]:
            p(paragraph)

# 1
content.append({"title": "Portada", "blocks": []})
doc.add_paragraph("Universidad del Istmo", style="Title")
doc.add_paragraph(
    "Ingeniería en Sistemas y Ciencias de la Computación", style="Subtitle"
)
doc.add_paragraph("\n\n")
doc.add_paragraph(
    "Probabilidad de las hazañas de Leverkusen y Cabo Verde", style="Title"
)
doc.add_paragraph(
    "Análisis de datos y simulación de temporadas de fútbol", style="Subtitle"
)
doc.add_paragraph("Curso: Análisis de Datos")
doc.add_paragraph("Catedrático: Juan Andrés García Porres")
doc.add_paragraph("")
for name, code in [
    ("Didvin Nohel Estrada Pineda", "14092"),
    ("Jose Humberto Najar Venavente", "13661"),
    ("Pablo Rodolfo Alexander Flores Mollinedo", "14643"),
]:
    doc.add_paragraph(f"{name}\nCarné {code}")
doc.add_paragraph("\nGuatemala, septiembre de 2026")
# 2
new("Resumen")
p(
    f"El campeonato invicto de Bayer Leverkusen en la Bundesliga 2023–2024 combina dos hechos diferentes: terminar con el dominio del Bayern Múnich y completar 34 jornadas sin derrotas. Entre 1964 y 2023, otros clubes ganaron {P(H['non_bayern_all'])} de los campeonatos. La proporción baja a {P(H['non_bayern_recent'])} al considerar solamente 2005–2023. Estas frecuencias describen el pasado, pero no constituyen un pronóstico individual para Leverkusen."
)
p(
    f"Elo es un sistema de puntuación de fuerza relativa, denominado por Arpad Elo. Un modelo de marcadores basado en el Elo de pretemporada estima una probabilidad de invicto de {small(L['p_unbeaten'])}. Las 10 000 temporadas simuladas no produjeron ningún invicto, resultado compatible con la pequeña probabilidad calculada. El modelo histórico de derrotas de los campeones produce {P(H['fits'][0]['p_zero'])} para cero derrotas. Las cifras difieren porque responden a preguntas y poblaciones distintas."
)
p(
    f"El segundo estudio analiza a Cabo Verde en la eliminatoria africana y en el escenario mundialista planteado. La probabilidad simulada de clasificación directa es {P(C['qualifying']['p'])}. Una vez en el grupo H, la probabilidad de avanzar es {P(C['scenarios']['grupo_sin_condicionar']['p'])}. Condicionar sus tres partidos a empates eleva esta última a {P(C['scenarios']['tres_empates']['p'])}. Superar después a Egipto, Suiza, Inglaterra y España, avanzando siempre por penales cuando hay empate, tiene probabilidad {P(C['title_given_pass_argentina'])}."
)
p(
    "Los resultados dependen de la valoración Elo escogida, de la distribución de goles y de supuestos de independencia. Los goles tardíos permiten estudiar la fragilidad del invicto, pero no separar de manera causal la suerte de la capacidad del equipo."
)
title("Objetivos y organización")
p(
    "Estimar las probabilidades solicitadas, comparar los modelos y explicar qué significa cada resultado. La primera parte estudia la Bundesliga y los cuatro rescates de Leverkusen. La segunda desarrolla la eliminatoria y el Mundial de Cabo Verde. El cierre reúne las limitaciones, las conclusiones y el registro de campeones."
)
# 3
variables(0)
notation(1)
variables(1)
new("Datos y fundamentos del modelo")
table(
    ["Fuente", "Información utilizada", "Corte del análisis"],
    [
        ["Curley, engsoccerdata [1]", "Resultados de Bundesliga", "1963/64–2023/24"],
        [
            "ClubElo vía archivo de Gábor [2]",
            "Elo de los 18 clubes",
            "15 de agosto de 2023",
        ],
        ["StatsBomb Open Data [3]", "Eventos de los 34 partidos", "Bundesliga 2023/24"],
        [
            "World Football Elo Ratings [4]",
            "Historial de selecciones",
            "Antes de 15/11/2023 y 11/06/2026",
        ],
        [
            "CAF y FIFA [5–7]",
            "Grupos y formato competitivo",
            "Eliminatoria y Mundial 2026",
        ],
    ],
)
p(
    "La temporada 1991/92 aparece incompleta en la base de partidos: 340 de 380 encuentros. Se sustituyó su registro del campeón por el de Stuttgart, con 38 partidos y siete derrotas, verificado en DSFS y Sportschau [11]."
)
p(
    "El año de cada campeón es el de finalización de la temporada. Se usan dos puntos por victoria hasta 1994/95 y tres desde 1995/96. Las valoraciones permanecen fijas durante cada simulación. La copia histórica de ClubElo se utiliza porque el servicio original no permitió recuperar el corte solicitado. No se sustituye por el ranking actual."
)
p(
    "Elo expresa puntuación esperada, no directamente probabilidad de victoria. Por ello distinguimos victoria, empate y derrota mediante dos variables de goles Poisson independientes [8]."
)
eq("E = 1 / (1 + 10^(−Δ/400)) = P(victoria) + ½ P(empate)")
eq("G₁ ∼ Poisson(λ₁), G₂ ∼ Poisson(λ₂)")
eq("λ₁ = (τ/2) exp(t), λ₂ = (τ/2) exp(−t)")
p(
    f"El parámetro t se resuelve numéricamente para igualar la puntuación esperada Elo. τ representa los goles esperados cuando las fuerzas son iguales, no un total fijo para cualquier cruce. En Bundesliga τ={L['total_goals']:.3f}, media de goles por partido de 2018/19–2022/23. Para selecciones se adopta τ=2.7 como supuesto. La localía suma 60 puntos Elo en Bundesliga y 100 en la eliminatoria africana. El Mundial se modela en campo neutral."
)
development(1)
numerical_examples(1)
# 4
new("Parte I La Bundesliga antes de Leverkusen")
p(
    "La Bundesliga comenzó en 1963/64. El análisis termina en 2022/23 para excluir el resultado que queremos explicar. Bayern ganó 32 de esos 60 títulos. Los otros 28 se distribuyen entre once clubes. La racha de once campeonatos consecutivos del Bayern abarca 2012/13–2022/23 [1, 9]."
)
eq("P̂(otro campeón | 1964–2023) = 28/60 = 46.67 %")
eq("P̂(otro campeón | 2005–2023) = 4/19 = 21.05 %")
p(
    "La diferencia es de 25.61 puntos porcentuales. En el período reciente, los cuatro títulos restantes corresponden a Stuttgart en 2007, Wolfsburg en 2009 y Dortmund en 2011 y 2012. Reducir la ventana cambia la referencia histórica y muestra un dominio más marcado del Bayern."
)
fig(
    "champions",
    "Figura 1. Campeonatos obtenidos. Elaboración propia con los resultados de Curley [1] y la corrección de 1991/92 [11].",
    6.1,
)
p(
    "La frecuencia de otros campeones no equivale a la probabilidad de que un club específico sea campeón, ni a la de ganar invicto. Tampoco se interpreta como una proporción estable en el tiempo."
)
# 5
new("El punto de partida de los clubes")
p(
    "El 15 de agosto de 2023, Leverkusen tenía 1748.23 puntos Elo, por debajo del Bayern, Dortmund y Leipzig. Se utiliza este corte previo al primer partido del 18 de agosto para formular una estimación ex ante [2]."
)
fig(
    "elo",
    "Figura 2. Ranking de los participantes de la Bundesliga 2023/24. ClubElo mediante archivo histórico [2].",
    6.0,
)
p(
    "El modelo mantiene constantes esas diferencias durante la campaña. Por tanto, no incorpora el crecimiento posterior de Leverkusen ni aprende de sus victorias. Esta elección evita usar el resultado final como información predictiva, pero puede subestimar a un equipo que mejora rápidamente."
)
# 6
new("Probabilidad de completar los 34 partidos invicto")
p(
    "Leverkusen juega dos veces contra cada uno de sus 17 rivales. Para cada encuentro calculamos pⱼ = P(victoria) + P(empate). La probabilidad de no perder toda la temporada se obtiene multiplicando los 34 valores bajo independencia condicional a las fuerzas y la localía."
)
eq(
    "P(inv icto) = ∏ⱼ pⱼ = P(no perder ante Bayern dos veces) × ∏otros pⱼ".replace(
        "inv icto", "invicto"
    )
)
table(
    ["Componente", "Probabilidad"],
    [
        ["Dos encuentros contra Bayern", P(L["p_bayern2"])],
        ["Otros 32 encuentros", small(L["p_other32"])],
        ["Temporada completa", small(L["p_unbeaten"])],
        ["Equivalencia aproximada", f"1 en {1 / L['p_unbeaten']:,.0f} temporadas"],
    ],
)
p(
    "No se emplea una única probabilidad promedio elevada a 34. El calendario distingue adversarios y sede, aunque congela las fuerzas. La dificultad acumulada de los otros 32 partidos también es considerable: evitar una derrota durante una temporada exige repetir muchos resultados favorables."
)
title("Sensibilidad a la fuerza de Leverkusen")
table(
    ["Cambio de Elo de Leverkusen", "Localía", "P de invicto"],
    [
        [f"+{x['leverkusen_elo_boost']}", str(x["hfa"]), small(x["p"])]
        for x in L["elo_sensitivity"]
        if x["hfa"] == 60
    ],
)
p(
    "Los aumentos de 100 y 200 puntos son escenarios de sensibilidad, no estimaciones observadas de talento. Una diferencia grande entre esos escenarios advierte que la cifra central depende fuertemente del punto de partida."
)
# 7
new("Simulación de 10 000 temporadas")
p(
    "Cada repetición produce 34 resultados independientes con las probabilidades de victoria, empate y derrota del calendario. La semilla 14643 fija una secuencia reproducible. Los puntos se asignan como 3 por victoria y 1 por empate."
)
fig(
    "montecarlo",
    "Figura 3. Distribución simulada de derrotas de Leverkusen con Elo de pretemporada.",
    6.1,
)
p(
    f"Se observaron {L['simulation']['successes']} temporadas invictas de 10 000, con {L['mean_losses']:.2f} derrotas promedio. La cantidad esperada de invictos era apenas {L['expected_unbeaten_10000']:.4f}. No observar el evento es lo esperable: la probabilidad de cero invictos es (1−p)^10000 = {P((1 - L['p_unbeaten']) ** 10000)}."
)
p(
    f"El intervalo binomial exacto bilateral del 95 % para la frecuencia simulada es [0, {P(L['simulation']['ci95'][1])}]. Por eso, cero simulaciones exitosas no demuestra que el invicto sea imposible. El producto analítico ofrece mayor resolución para un suceso tan raro. El intervalo solo mide error Monte Carlo, no incertidumbre sobre Elo ni sobre el modelo."
)
# 8
new("Derrotas históricas de los campeones")
p(
    "Ahora la unidad de análisis es la temporada de un equipo que ya sabemos que fue campeón. Ajustamos D ∼ Poisson(λ), con λ igual a la media histórica de derrotas. La probabilidad buscada es P(D=0)=exp(−λ) [8]."
)
table(
    ["Campeones", "n", "Media D", "Varianza D", "P de 0 derrotas"],
    [
        [x["group"], x["n"], f"{x['mean']:.3f}", f"{x['variance']:.3f}", P(x["p_zero"])]
        for x in H["fits"]
    ],
)
fig(
    "poisson",
    "Figura 4. Distribuciones ajustadas a las derrotas de los campeones de 1964–2023.",
    5.8,
)
p(
    "Las tres varianzas son menores que sus medias. Una binomial negativa estándar, cuya varianza supera la media, no corrige esta subdispersión. Poisson se conserva como aproximación sencilla solicitada, no como un ajuste perfecto. Ningún campeón de la muestra tuvo cero derrotas."
)
p(
    "Las primeras dos campañas tuvieron 30 jornadas y 1991/92 tuvo 38. Normalizando la tasa de derrotas a 34 partidos, el resultado para todos los campeones es "
    + P(H["fits"][0]["p_zero_34"])
    + ". La corrección de exposición cambia poco la conclusión."
)
# 9
new("Comparación entre Bayern y los demás campeones")
p(
    f"Condicionado a que el campeón sea Bayern, el modelo asigna {P(H['fits'][1]['p_zero'])} a una campaña invicta. Si el campeón pertenece al conjunto de otros clubes, estima {P(H['fits'][2]['p_zero'])}. La relación es {H['fits'][1]['p_zero'] / H['fits'][2]['p_zero']:.2f} a favor de Bayern. Se comparan dos categorías de campeones, no Bayern contra un rival individual elegido de antemano."
)
eq("P(Bayern campeón e invicto) ≈ (32/60) exp(−4.125)")
eq("P(otro campeón e invicto) ≈ (28/60) exp(−5.0357)")
table(
    ["Evento conjunto histórico", "Estimación"],
    [
        ["Bayern campeón e invicto", P(32 / 60 * H["fits"][1]["p_zero"])],
        ["Otro campeón e invicto", P(28 / 60 * H["fits"][2]["p_zero"])],
    ],
)
p(
    "Esta combinación usa frecuencias históricas como pesos y modelos de derrotas condicionados al campeón. No permite identificar la probabilidad de que Leverkusen, concretamente, gane invicto. El modelo de partidos sí parte de un equipo concreto y de sus 34 rivales."
)
p(
    "El valor Poisson resulta mucho mayor que el producto de partidos. La selección de campeones excluye de antemano las campañas mediocres. Además, mezcla épocas, entrenadores y estados de forma. En cambio, el modelo Elo de pretemporada conserva una valoración de Leverkusen anterior a su mejora. No hay razón para que ambas probabilidades coincidan."
)
p(
    "Por último, el evento «invicto» no exige ser campeón: un equipo podría empatar sus 34 partidos y no ganar la liga. Esta distinción impide multiplicar sin más la frecuencia de campeones ajenos al Bayern por la probabilidad de invicto de Leverkusen."
)
# 10
new("Extra Los cuatro partidos rescatados")
p(
    "Se reconstruyó el marcador ordenando los goles de los 34 encuentros de Bundesliga, incluidos los autogoles. Se considera rescate un gol desde el minuto 85 que convierte una desventaja en empate o ventaja y evita la derrota final. La auditoría excluye las competiciones de copa y los goles que solamente convierten un empate en victoria [3]."
)
table(
    ["Fecha", "Rival", "Gol de empate", "Resultado"],
    [[x["date"], x["opponent"], x["minute"], x["final"]] for x in L["rescues"]],
)
p(
    "Los anotadores fueron Exequiel Palacios ante Bayern, Robert Andrich ante Hoffenheim, Josip Stanišić ante Dortmund y Andrich ante Stuttgart. Los tiempos anteriores son el reloj de eventos de StatsBomb. Por ejemplo, 93:46 se anuncia habitualmente como minuto 90+4. No deben confundirse segundos transcurridos con la etiqueta redondeada del minuto."
)
p(
    "Ante Bayern el marcador era 1–1 al minuto 85. El 2–1 del rival llegó a 85:21. Ese partido sí cumple «iba perdiendo después del minuto 85», aunque no «perdía exactamente al 85». La definición literal produce k=4. Una definición estricta del estado exactamente al minuto 85 dejaría k=3."
)
p(
    "Para estimar cada rescate usamos el estado al 85 o, si la desventaja comienza después, el primer estado desfavorable posterior. Se usan tasas históricas de goles por localía de toda la liga en 2018/19–2022/23 y la duración restante hasta el cierre observado del partido. Esto condiciona retrospectivamente por duración y supone una tasa uniforme de gol."
)
eq("qᵢ = P(Xᵢ − Yᵢ ≥ déficitᵢ), Xᵢ ∼ Pois(rₐ Tᵢ/90), Yᵢ ∼ Pois(rᵣ Tᵢ/90)")
table(
    ["Rival", "Estado inicial", "Minutos restantes", "qᵢ"],
    [
        [x["opponent"], x["state_score"], f"{x['remaining']:.2f}", P(x["q"])]
        for x in L["rescues"]
    ],
)
# 11
new("Extra Fragilidad y discusión de la suerte")
eq("Q = q₁ × q₂ × q₃ × q₄ = " + small(L["Q"]))
eq("1/Q = " + f"{L['inverse_Q']:,.1f}")
eq(
    "Índice ajustado solicitado = P(inv icto) × Q = ".replace("inv icto", "invicto")
    + small(L["adjusted"])
)
p(
    "Q resume la probabilidad conjunta de rescatar los cuatro estados desfavorables bajo independencia. El producto P(invicto)×Q se reporta como el índice heurístico solicitado por el ejercicio. No constituye una nueva probabilidad predictiva calibrada: el modelo inicial ya admite resultados salvados por goles tardíos, por lo que multiplicar puede contabilizar dos veces parte de la dificultad."
)
p(
    "El recíproco 1/Q expresa rareza conjunta dentro del modelo. No identifica cuántas veces tuvo «más suerte» el equipo en sentido causal. Para medir ese efecto sería necesario un contrafactual que sustituyera las probabilidades de los partidos rescatados sin duplicar su contribución."
)
title("Sensibilidad al tiempo añadido")
table(
    ["Añadido supuesto", "Q", "Índice P × Q"],
    [
        [x["added_minutes"], small(x["Q"]), small(x["adjusted"])]
        for x in L["late_sensitivity"]
    ],
)
p(
    "La tabla fija horizontes comunes, mientras que el valor central usa el cierre observado de cada partido. Los horizontes cortos describen escenarios alternativos y pueden terminar antes de alguno de los goles reales. No son reconstrucciones exactas de esos encuentros."
)
p(
    "Nuestra postura es que llamar suerte a todos los rescates simplifica demasiado el fenómeno. La presión sostenida, la profundidad del plantel, las sustituciones y la capacidad de generar ocasiones pueden aumentar la probabilidad de un gol tardío. También existe variabilidad impredecible en cada remate y rebote. Cuatro casos no bastan para separar ambas explicaciones. El análisis cuantifica dependencia de rescates, sin probar que se deban exclusivamente al azar."
)
# 12
conclusion(1)
notation(2)
variables(2)
new("Parte II La clasificación de Cabo Verde")
p(
    "La eliminatoria africana ubica a Cabo Verde en el grupo D con Camerún, Angola, Libia, Esuatini y Mauricio [5]. Simulamos el grupo completo a ida y vuelta: 30 partidos, 10 por selección. La clasificación directa corresponde exclusivamente al primer puesto, sin repechaje, como establece el ejercicio."
)
table(
    ["Selección", "Elo anterior al inicio"],
    [
        [
            {
                "CV": "Cabo Verde",
                "CM": "Camerún",
                "AO": "Angola",
                "LY": "Libia",
                "SZ": "Esuatini",
                "MU": "Mauricio",
            }[k],
            v,
        ]
        for k, v in C["qualifying_elo"].items()
    ],
)
p(
    "Las fuerzas proceden del último partido anterior al 15 de noviembre de 2023 en World Football Elo Ratings [4]. Se congelan antes de la eliminatoria. No se emplean ratings posteriores a la clasificación. Se aplica la misma conversión Elo–Poisson y una ventaja local de 100 puntos."
)
p(
    f"Cabo Verde terminó primero en {C['qualifying']['successes']} de 10 000 simulaciones: {P(C['qualifying']['p'])}. El intervalo Monte Carlo del 95 % es [{P(C['qualifying']['ci95'][0])}, {P(C['qualifying']['ci95'][1])}]. Bajo estos supuestos, la clasificación ocurre aproximadamente una vez cada {1 / C['qualifying']['p']:.1f} eliminatorias simuladas."
)
p(
    "Camerún parte con mayor Elo, pero el formato de diez partidos permite que empates y derrotas del favorito abran una oportunidad. El resultado mide la dificultad antes de empezar. No condiciona el cálculo a los resultados reales conocidos de la eliminatoria."
)
p(
    "El desempate simulado usa puntos, diferencia de goles y goles anotados, seguido por el desempeño entre empatados. La igualdad residual se resuelve al azar. La simulación no incorpora tarjetas ni decisiones disciplinarias, por lo que los desempates finales son una aproximación explícita."
)
# 13
new("El grupo H y los mejores terceros")
p(
    "El grupo H reúne a España, Cabo Verde, Arabia Saudita y Uruguay. Se simulan también los otros once grupos. Avanzan los dos primeros de cada grupo y los ocho mejores terceros, para formar los dieciseisavos [6, 7]. Tener tres puntos no garantiza el pase: también importan la diferencia de goles y los goles anotados."
)
p(
    "Se usa el último Elo de cada selección anterior al 11 de junio de 2026. Dentro del grupo se prioriza la minitabla de enfrentamientos directos entre equipos igualados a puntos, seguida de diferencia de goles y goles totales. Entre terceros se comparan puntos, diferencia de goles y goles anotados. La igualdad restante se sortea porque no se modela conducta deportiva ni ranking FIFA residual. Los porcentajes son aproximaciones del formato bajo esa simplificación."
)
table(
    ["Selección", "Elo previo al Mundial"],
    [
        [
            {
                "ES": "España",
                "CV": "Cabo Verde",
                "SA": "Arabia Saudita",
                "UY": "Uruguay",
            }[k],
            C["world_elo"][k],
        ]
        for k in ["ES", "CV", "SA", "UY"]
    ],
)
fig(
    "cape_scenarios",
    "Figura 5. Probabilidades con denominadores distintos. Los escenarios con empates están condicionados a ellos.",
    6.0,
)
p(
    f"Sin imponer sus resultados, Cabo Verde avanza en {P(C['scenarios']['grupo_sin_condicionar']['p'])} de las simulaciones. La probabilidad analítica de empatar sus tres partidos es {P(C['p_three_draws'])}. Este evento es poco frecuente, pero, una vez que ocurre, ofrece una posición relativamente favorable frente a otros terceros."
)
# 14
new("Tres empates y los escenarios condicionados")
p(
    "Para imponer tres empates no se fijan artificialmente tres marcadores 0–0. En cada duelo se muestrea k–k según la distribución de goles condicionada a la igualdad. Esto conserva la incertidumbre en goles anotados, relevante para los desempates."
)
eq("P(k–k | empate) ∝ P(G₁=k) P(G₂=k)")
labels = {
    "grupo_sin_condicionar": "Sin imponer resultados",
    "tres_empates": "Con tres empates",
    "tres_empates_y_uruguay_no_pierde": "Tres empates y Uruguay no pierde ante España",
    "tres_empates_y_tercero": "Tres empates y tercer lugar",
}
table(
    ["Escenario", "Casos", "P de avanzar", "IC 95 %"],
    [
        [
            labels[k],
            v["n"],
            P(v["p"]),
            f"{100 * v['ci95'][0]:.1f}–{100 * v['ci95'][1]:.1f} %",
        ]
        for k, v in C["scenarios"].items()
        if k in labels
    ],
)
p(
    "El tercer escenario considera que Uruguay gana o empata contra España y que Cabo Verde empata sus tres encuentros. Su denominador incluye únicamente las simulaciones que cumplen ambas condiciones. El cuarto responde directamente a la posibilidad de avanzar como mejor tercero con tres puntos obtenidos por tres empates."
)
table(
    ["Posición de Cabo Verde con tres empates", "Frecuencia"],
    [[str(i + 1), P(v)] for i, v in enumerate(C["positions_three_draws"])],
)
p(
    "No debe confundirse la probabilidad de obtener tres empates con la probabilidad de avanzar después de conseguirlos. Tampoco debe generalizarse el resultado a cualquier tercer lugar con tres puntos: una victoria y dos derrotas pueden dejar una diferencia de goles negativa, mientras que tres empates dejan diferencia cero."
)
p(
    f"Si la condición «Uruguay no pierde ante España» se interpreta sin imponer empates de Cabo Verde, el pase estimado es {P(C['scenarios']['uruguay_no_pierde_sin_condicionar_empates']['p'])}. Se presenta por separado para evitar mezclar las dos interpretaciones."
)
# 15
new("La ruta eliminatoria propuesta")
p(
    "El relato del ejercicio se trata como un contrafactual deportivo. Las afirmaciones sobre decisiones arbitrales no se adoptan como hechos ni se incluyen como variables del modelo. La ruta principal comienza después de superar a Argentina y exige no perder en 90 minutos ante Egipto, Suiza, Inglaterra y España. En todos los empates se supone que Cabo Verde avanza por penales, como pide el enunciado."
)
table(
    ["Rival", "P victoria", "P empate", "P avance"],
    [
        [
            {
                "AR": "Argentina",
                "EG": "Egipto",
                "CH": "Suiza",
                "EN": "Inglaterra",
                "ES": "España",
            }[x["opponent"]],
            P(x["p_win"]),
            P(x["p_draw"]),
            P(x["p_advance"]),
        ]
        for x in C["knockouts"]
    ],
)
eq("P(título | supera Argentina y ruta fija) = ∏ᵢ₌₁⁴ [P(Gᵢ) + P(Eᵢ)]")
p(
    f"El producto da {P(C['title_given_pass_argentina'])}: aproximadamente una posibilidad en {1 / C['title_given_pass_argentina']:,.0f}. La simulación independiente produjo {C['knockout_mc']['successes']} éxitos de 10 000. Su intervalo binomial es amplio y contiene el producto analítico. Se prioriza este último para describir un evento poco frecuente."
)
fig(
    "route",
    "Figura 6. Probabilidad acumulada de superar la ruta desde Egipto. Escala logarítmica.",
    5.7,
)
# 16
new("Alcance de la probabilidad de ganar el Mundial")
table(
    ["Punto de partida con ruta fija", "Probabilidad"],
    [
        ["Después de superar Argentina", P(C["title_given_pass_argentina"])],
        ["Antes de jugar contra Argentina", f"{100 * C['title_from_argentina']:.5f} %"],
        ["Desde el grupo H", f"{100 * C['title_from_group_fixed_route']:.6f} %"],
        [
            "Desde la eliminatoria africana",
            f"{100 * C['title_from_qualifiers_fixed_route']:.6f} %",
        ],
    ],
)
p(
    "La primera fila responde a los cuatro rivales expresamente solicitados. La segunda añade el partido contra Argentina con la misma regla favorable de avanzar en cualquier empate. Las últimas dos combinan etapas bajo independencia y mantienen la ruta de rivales fijada por el ejercicio. No representan una simulación completa de todos los cruces posibles del Mundial."
)
p(
    "Garantizar la victoria en penales favorece mucho a Cabo Verde. Si cada empate se resolviera con una moneda equilibrada y se ignorara la prórroga, cada factor sería P(victoria)+0.5 P(empate). El supuesto del ejercicio, por tanto, constituye una condición optimista, no una estimación empírica de su capacidad de ejecutar penales."
)
title("Limitaciones comunes")
p(
    "Elo resume resultados pasados y no describe lesiones, alineaciones ni evolución táctica. Congelar fuerzas descarta cambios durante torneos largos. Los modelos Poisson independientes simplifican la dependencia entre ambos marcadores, y la tasa base de 2.7 para selecciones es una elección de modelación. La localía del Mundial se considera neutral para todos, incluso para anfitriones."
)
p(
    "Los intervalos presentados describen únicamente la variación Monte Carlo. No cubren incertidumbre en parámetros, en desempates residuales ni en las fuentes. El escenario de mejores terceros depende de la composición completa de los grupos. Las probabilidades calculadas no se interpretan como certezas ni como evidencia de irregularidades deportivas."
)
development(2)
numerical_examples(2)
# 17
conclusion(2)
# 18
new("Referencias")
refs = [
    "[1] Curley, J. P. (2016, datos actualizados en 2026). engsoccerdata. Resultados de ligas europeas. https://github.com/jalapic/engsoccerdata",
    "[2] ClubElo. Football Club Elo Ratings. https://clubelo.com/ . Archivo histórico de valoraciones publicado por Ádám Gábor en Club Football Match Data. Corte utilizado: 15/08/2023. https://github.com/xgabora/Club-Football-Match-Data/blob/main/data/EloRatings.csv",
    "[3] Hudl StatsBomb. Open Data. Competición 9, temporada 281. Partidos y eventos de Bayer Leverkusen en Bundesliga 2023/24. https://github.com/statsbomb/open-data",
    "[4] World Football Elo Ratings. Historiales de selecciones y datos TSV. https://www.eloratings.net/ . Ejemplo: https://www.eloratings.net/Cape_Verde.tsv",
    "[5] Confederation of African Football. Everything you need to know about 2026 World Cup qualifying for Africa. https://www.cafonline.com/news/everything-you-need-to-know-about-2026-world-cup-qualifying-for-africa/",
    "[6] FIFA. FIFA World Cup 2026 match schedule, fixtures and stadiums. https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums",
    "[7] FIFA. Grupos de la Copa Mundial 2026 y criterios de desempate. https://www.fifa.com/es/tournaments/mens/worldcup/canadamexicousa2026/articles/grupos-como-funcionan-clasificacion-criterios-desempate",
    "[8] Goldsman, D., y Goldsman, P. (2024). A First Course in Probability and Statistics. Versión 201127.241225. Capítulos 1 (independencia y probabilidad condicional), 4 (distribuciones), 5 (estimación) y 6 (intervalos). Texto proporcionado para el curso.",
    "[9] Bundesliga (2024). Xabi Alonso’s Bayer Leverkusen become first Bundesliga team to go unbeaten throughout a season. https://www.bundesliga.com/en/bundesliga/news/bayer-leverkusen-record-unbeaten-run-xabi-alonso-26289",
    "[10] NumPy, pandas, SciPy y Matplotlib. Documentación de las bibliotecas utilizadas: https://numpy.org/doc/ ; https://pandas.pydata.org/docs/ ; https://docs.scipy.org/doc/scipy/ ; https://matplotlib.org/stable/ . Las versiones exactas se conservan en uv.lock.",
]
refs.append(
    "[11] Deutscher Sportclub für Fußball-Statistiken. Die Bundesliga seit 1963. https://www.dsfs.de/wp-content/uploads/2024/01/Bundesliga_Geschichte_Tabellen.pdf . Contraste: Sportschau, tabla final 1991/92. https://www.sportschau.de/live-und-ergebnisse/fussball/deutschland-bundesliga/se2613/1991-1992/tabelle"
)
for x in refs:
    p(x)
p(
    "Fecha de consulta de fuentes en línea: 14 de septiembre de 2026. Las tablas y gráficas presentan cálculos propios a partir de las fuentes indicadas. Las fórmulas de conversión Elo–Poisson y los supuestos de simulación corresponden al modelo de este estudio."
)
# 19-21
rows = list(csv.DictReader((ROOT / "data/processed/champions_1964_2023.csv").open()))
for i in range(0, 60, 20):
    new(f"Anexo Campeones de {1964 + i} a {1983 + i}")
    table(
        ["Año", "Campeón", "PJ", "G", "E", "D"],
        [
            [x["end_year"], x["team"], x["played"], x["wins"], x["draws"], x["losses"]]
            for x in rows[i : i + 20]
        ],
    )
    p(
        "Fuente: reconstrucción de clasificaciones con los resultados de Curley [1] y la corrección de 1991/92 [11]. PJ: partidos jugados. G: victorias. E: empates. D: derrotas. Los nombres conservan la normalización utilizada para enlazar las bases de datos."
    )
# 22
new("Anexo Grupos mundialistas y reproducibilidad")
names = {
    x.split("\t")[0]: x.split("\t")[1]
    for x in (ROOT / "data/raw/elo_teams.tsv").read_text().splitlines()
}
groups = json.loads((ROOT / "data/groups_2026.json").read_text())
table(
    ["Grupo", "Selecciones"],
    [[g, ", ".join(names[c] for c in cs)] for g, cs in groups.items()],
)
p(
    "El análisis utiliza Python y un entorno virtual administrado con uv. Para repetirlo con los datos conservados se ejecuta uv sync --frozen y después uv run python src/analyze.py. Las simulaciones producen tablas completas por repetición. Los archivos de datos incluyen fecha de corte y fuente, y la descarga original se registra con una huella SHA-256."
)
p(
    "La reproducción no requiere volver a consultar ratings actuales. Se conservaron las instantáneas utilizadas, evitando que una actualización posterior altere la interpretación temporal. La reconstrucción de eventos verificó los marcadores finales de los 34 encuentros y la tabla histórica verificó 60 campeones, incluidos 32 del Bayern."
)
(ROOT / "outputs").mkdir(exist_ok=True)
doc.save(ROOT / "outputs/trabajo_escrito.docx")
(ROOT / "docs/report_content.json").write_text(
    json.dumps(content, ensure_ascii=False, indent=2)
)
print("Informe con desarrollo matemático compuesto")
