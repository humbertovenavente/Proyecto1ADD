import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import {resolvePresentationFont,applyPresentationChartFont,finalizePresentation} from '/Users/pabloflores/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root=process.cwd();const R=JSON.parse(await fs.readFile(root+'/outputs/results.json','utf8'));const L=R.leverkusen,C=R.cape_verde,H=R.history;
const family=resolvePresentationFont({fontFamily:'Arial'});const pres=Presentation.create({slideSize:{width:1280,height:720}});const P=x=>(100*x).toFixed(2)+' %';const sci=x=>{const [m,e]=x.toExponential(3).split('e');return m+' × 10'+String(Number(e)).split('').map(c=>'⁻⁰¹²³⁴⁵⁶⁷⁸⁹'['-0123456789'.indexOf(c)]).join('');};const red='#B62835',blue='#176B9A',ink='#17242C';
let n=0;let part=1;const native=[];
function text(s,t,x,y,w,h,size=30,color=ink,bold=false){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={typeface:family,fontSize:size,color,bold,autoFit:'none'};return a;}
function variableSlides(which){
 const sections=JSON.parse(execFileSync('cat',[root+'/docs/variables.json'],{encoding:'utf8'}));
 for(const section of sections){if(section.part!==which)continue;const ss=slide(section.title,'https://clubelo.com/System · Goldsman, capítulos 1 y 4–6');prose(ss,section.paragraphs,{y:212,size:26,gap:212});}
}
function slide(title,source='',dark=false){
let s=pres.slides.add();n++;const accent=part===1?red:blue;s.background.fill=dark?'#101C29':(part===1?'#FAF7F1':'#F3F7FA');
 text(s,part===1?'PARTE I  /  LEVERKUSEN':(part===2?'PARTE II  /  CABO VERDE':'CONCLUSIONES Y REFERENCIAS'),66,26,940,30,17,dark?'#EDBCBF':accent,true);
 text(s,title,64,76,1150,108,title.length>62?37:44,dark?'#FFFFFF':ink,true);
 text(s,n.toString().padStart(2,'0'),1162,26,60,38,25,dark?'#FFFFFF':accent,true);
 text(s,'UNIVERSIDAD DEL ISTMO',66,668,740,24,15,dark?'#BAC9D3':'#687780');
 text(s,'ANÁLISIS DE DATOS',936,668,286,24,15,dark?'#BAC9D3':'#687780');
 s.speakerNotes.textFrame.setText(source);return s;
}
function paragraphs(s,arr,{x=64,y=212,w=1130,size=29,gap=101,color=ink}={}){
 arr.forEach((t,i)=>text(s,t,x,y+i*gap-3,w,gap-13,size,color));
}
function prose(s,arr,{y=212,size=27,gap=190}={}){
 arr.forEach((t,i)=>text(s,t,70,y+i*gap,1130,gap-20,size));
}
function chart(s,cats,values,{name='Probabilidad (%)',x=65,y=233,w=1140,h=340,color=red,horizontal=false}={}){
 text(s,name,66,189,1140,30,20,part===1?red:blue,true);
 const c=s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories:cats,series:[{name,values:values.map(v=>Number(v.toFixed(2))),valuesFormatCode:name.includes('Elo')?'0':'0.00',fill:color}],barOptions:{direction:horizontal?'bar':'column',grouping:'clustered',gapWidth:80},hasLegend:false,chartFill:part===1?'#FAF7F1':'#F3F7FA',plotAreaFill:part===1?'#FAF7F1':'#F3F7FA',xAxis:{textStyle:{fontSize:24,fill:ink}},yAxis:{numberFormatCode:'0',min:0,max:name.includes('(%)')?(Math.max(...values)<=2?2:Math.max(...values)<=25?25:Math.max(...values)<=50?50:100):undefined,textStyle:{fontSize:19,fill:ink},majorGridlines:{fill:'#DCE2E3',width:0.6}},dataLabels:{showValue:cats.length<10,position:'outEnd',textStyle:{fontSize:27,fill:ink,bold:true}}});
 applyPresentationChartFont(c,{fontFamily:family});native.push(n);return c;
}
async function image(s,file,x=0,y=0,w=1280,h=720){s.images.add({blob:new Uint8Array(await fs.readFile(root+'/assets/'+file)),contentType:'image/png',alt:'Ilustración editorial de fútbol',fit:'cover',position:{left:x,top:y,width:w,height:h}});}
async function equationImage(s,name,x,y,w,h){
 const bytes=await fs.readFile(root+'/assets/math/'+name+'.png');
 const iw=bytes.readUInt32BE(16),ih=bytes.readUInt32BE(20);
 // Preserve a common type size instead of enlarging short expressions to fill a box.
 const settings=JSON.parse(await fs.readFile(root+'/assets/math/render_settings.json','utf8'));
 const target=name.startsWith('notation_')?28:32;
 const nominalPixels=settings.font_size_pt*settings.dpi/72;
 const scale=name.startsWith('book_')?Math.min(w/iw,Math.min(h,86)/ih):Math.min(target/nominalPixels,w/iw,h/ih);
 const dw=iw*scale,dh=ih*scale;
 s.images.add({blob:new Uint8Array(bytes),contentType:'image/png',alt:'Fórmula o símbolo matemático: '+name,fit:'contain',position:{left:x+(w-dw)/2,top:y+(h-dh)/2,width:dw,height:dh}});
}
const sources={hist:'James P. Curley, engsoccerdata. https://github.com/jalapic/engsoccerdata . Cálculos en data/processed/champions_1964_2023.csv.',elo:'ClubElo mediante el archivo de Ádám Gábor. https://github.com/xgabora/Club-Football-Match-Data/blob/main/data/EloRatings.csv . Corte 2023-08-15. API original no disponible durante la consulta.',events:'Hudl StatsBomb Open Data. https://github.com/statsbomb/open-data . Competición 9, temporada 281, 34 partidos. Relojes de eventos con segundos.',nat:'World Football Elo Ratings. https://www.eloratings.net/ . Historiales TSV anteriores a 2023-11-15 y 2026-06-11.',rules:'CAF: https://www.cafonline.com/news/everything-you-need-to-know-about-2026-world-cup-qualifying-for-africa/ . FIFA: https://www.fifa.com/es/tournaments/mens/worldcup/canadamexicousa2026/articles/grupos-como-funcionan-clasificacion-criterios-desempate . Desempates residuales simulados por sorteo.',book:'Goldsman, David y Paul (2024). A First Course in Probability and Statistics. Capítulos 1, 4, 5 y 6.'};
async function notation(partNumber){
 const groups=JSON.parse(await fs.readFile(root+'/docs/notation.json','utf8'));
 for(let gi=0;gi<groups.length;gi++){
  const g=groups[gi];if(g.part!==partNumber)continue;
  const ss=slide(g.title,sources.book+' Glosario de símbolos del modelo.');
  text(ss,'NOTACIÓN',70,183,1110,26,17,part===1?red:blue,true);
  for(let ri=0;ri<g.rows.length;ri++){
   const y=222+ri*83;
   await equationImage(ss,'notation_'+gi+'_'+ri,70,y,380,61);
   text(ss,g.rows[ri][1],480,y,730,72,23);
  }
 }
}
function conclusion(which){
 const section=JSON.parse(execFileSync('cat',[root+'/docs/conclusions.json'],{encoding:'utf8'})).find(x=>x.part===which);
 const ss=slide(section.title,Object.values(sources).join('\n'));
 prose(ss,section.paragraphs,{y:212,size:28,gap:420});
}
async function numericalExamples(partNumber){
 const examples=JSON.parse(await fs.readFile(root+'/docs/numeric_examples.json','utf8'));
 for(let i=0;i<examples.length;i++){
  const e=examples[i];if(e.part!==partNumber)continue;
  const ss=slide(e.title,'Sustituciones calculadas desde outputs/results.json y los datos procesados.');
  await equationImage(ss,'numeric_'+i+'_0',70,196,1130,112);
  await equationImage(ss,'numeric_'+i+'_1',70,320,1130,112);
  text(ss,e.explanation,70,461,1130,164,25);
 }
}
async function development(partNumber){
 const sections=JSON.parse(await fs.readFile(root+'/docs/methodology.json','utf8'));
 for(let i=0;i<sections.length;i++){
  const section=sections[i];if(section.part!==partNumber)continue;
  let ss=slide(section.title,sources.book+'\n'+section.paragraphs.join('\n\n'));
  prose(ss,section.paragraphs.slice(0,2),{y:214,size:27,gap:210});
  ss=slide(section.title+' · desarrollo',sources.book+'\n'+section.paragraphs.join('\n\n'));
  await equationImage(ss,'method_'+i,68,184,1138,112);
  text(ss,'Desarrollo del modelo · fundamentos: Goldsman, caps. 1, 4–6; Skellam: SciPy',70,640,1120,23,15,'#687780');
  prose(ss,section.paragraphs.slice(2),{y:316,size:26,gap:168});
 }
}

let s=pres.slides.add();n++;await image(s,'football_cover.png');
text(s,'Probabilidad de las\nhazañas del fútbol',65,80,1080,190,58,'#FFFFFF',true);
text(s,'Leverkusen y Cabo Verde',70,297,1080,62,35,'#FFFFFF');
text(s,'Didvin Nohel Estrada Pineda · 14092\nJose Humberto Najar Venavente · 13661\nPablo Rodolfo Alexander Flores Mollinedo · 14643',70,439,1130,132,28,'#FFFFFF');
text(s,'Análisis de Datos · Catedrático: Juan Andrés García Porres',70,580,1130,37,24,'#FFFFFF');
text(s,'Universidad del Istmo · Septiembre de 2026',70,635,1110,34,23,'#FFFFFF');
s.speakerNotes.textFrame.setText('Ilustración editorial. Integrantes del grupo y dos estudios probabilísticos.');
s=slide('Preguntas y estructura del análisis');paragraphs(s,['Leverkusen: probabilidad del invicto y diagnóstico de rescates','Cabo Verde: clasificación, escenarios de grupo y ruta al título','Desarrollo: eventos, supuestos, ecuaciones y cálculos','Conclusiones: estimaciones, incertidumbre y límites inferenciales'],{gap:101,size:28});
variableSlides(0);
s=slide('Una liga acostumbrada al mismo campeón',sources.hist);prose(s,['Antes de la temporada 2023/24, el Bayern acumulaba once campeonatos consecutivos. Ganar la Bundesliga significaba romper una continuidad que había definido la competencia durante más de una década.','La perspectiva histórica cambia con la ventana: otros clubes ganaron 28 de 60 títulos entre 1964 y 2023, pero apenas cuatro de los 19 títulos entre 2005 y 2023. Esa diferencia describe el contexto del desafío, aunque no determina por sí sola las posibilidades de Leverkusen.'],{gap:210});
s=slide('La hazaña contiene dos preguntas distintas',sources.hist+' '+sources.elo);prose(s,['El equipo dirigido por Xabi Alonso no solo terminó con esa secuencia de campeones. Completó las 34 jornadas sin derrotas: 28 victorias y seis empates. El campeonato y el invicto son dos logros relacionados, pero no equivalentes.','Para entender el invicto, volvemos al momento anterior al torneo. Usamos las fuerzas conocidas entonces y preguntamos cuántas temporadas simuladas habrían terminado sin perder. Después contrastamos ese cálculo con las derrotas de campeones históricos y con los goles tardíos que salvaron partidos.'],{gap:210});

s=slide('Leverkusen completó 34 partidos sin perder',sources.hist+' https://www.bundesliga.com/en/bundesliga/news/bayer-leverkusen-record-unbeaten-run-xabi-alonso-26289',true);text(s,'28 victorias   6 empates   0 derrotas',65,218,1150,90,46,'#FFFFFF',true);paragraphs(s,['90 puntos, 89 goles a favor y 24 en contra','Primer campeón invicto de la Bundesliga','Fin de once títulos consecutivos del Bayern'],{y:348,gap:90,size:30,color:'#FFFFFF'});
s=slide('Un campeón distinto del Bayern',sources.hist);chart(s,['1964–2023\n28 de 60','2005–2023\n4 de 19'],[46.67,21.05]);text(s,'La referencia reciente baja 25.61 puntos porcentuales',75,605,1120,45,26);
s=slide('Qué datos entran al modelo',[sources.hist,sources.elo,sources.events,sources.nat].join('\n'));paragraphs(s,['60 temporadas de campeones, sin incluir 2023/24','18 valoraciones ClubElo previas al torneo','34 partidos y sus eventos para identificar rescates','Historiales Elo de selecciones antes de cada competición'],{gap:104,size:28});
s=slide('Elo de pretemporada',sources.elo);chart(s,['Bayern','Dortmund','Leipzig','Leverkusen','Union Berlin','Freiburg'],[1935.63,1840.54,1825.38,1748.23,1738.94,1732.67],{name:'Elo al 15 de agosto de 2023'});text(s,'Se congelan las fuerzas para evitar usar resultados futuros',65,605,1140,48,25);
await notation(1);
variableSlides(1);
s=slide('De Elo a victoria, empate y derrota',sources.book+' Modelo propio de enlace Elo–Poisson.');paragraphs(s,['E = P(victoria) + ½ P(empate)','Goles independientes con distribuciones Poisson','Se ajustan las tasas para reproducir la expectativa Elo'],{y:303,gap:93,size:31});await equationImage(s,'elo',130,207,1000,73);text(s,'τ Bundesliga = 3.142 · τ selecciones = 2.7 · localía Elo = 60 / 100',65,618,1150,36,23);
await development(1);
await numericalExamples(1);
s=slide('El invicto requiere superar todo el calendario',sources.elo+' Cálculo en outputs/results.json.');text(s,'P(inv icto) = P(Bayern × 2) × P(otros × 32)'.replace('inv icto','invicto'),65,207,1150,80,36);paragraphs(s,[`Dos partidos ante Bayern: ${P(L.p_bayern2)}`,`Otros 32 partidos: ${sci(L.p_other32)}`,`Temporada completa: ${sci(L.p_unbeaten)}`],{y:319,gap:96,size:31});
s=slide('La binomial en el texto de referencia',sources.book+' Página impresa 118, página 134 del PDF. Recorte de la fórmula original.');
await equationImage(s,'book_binomial',78,214,1120,104);
text(s,'Goldsman y Goldsman · capítulo 4 · p. 118 (p. 134 del PDF)',78,337,1120,34,19);
prose(s,['El teorema establece que la suma de indicadores Bernoulli independientes con la misma probabilidad de éxito tiene distribución binomial. En nuestro caso, cada indicador representa una temporada invicta.','La fórmula se aplica a las 10 000 temporadas repetidas, no directamente a los 34 partidos: los rivales tienen probabilidades distintas. Esta diferencia explica por qué primero calculamos el producto del calendario y después modelamos el número de temporadas invictas.'],{y:391,gap:126,size:25});
s=slide('10 000 temporadas y ningún invicto',sources.elo+' Semilla 14643. outputs/leverkusen_10000.csv.');
const csv=(await fs.readFile(root+'/outputs/leverkusen_10000.csv','utf8')).trim().split('\n').slice(1).map(x=>Number(x.split(',')[3]));let counts=Array(25).fill(0);csv.forEach(x=>counts[x]++);chart(s,counts.map((_,i)=>String(i)),counts,{name:'Temporadas por número de derrotas'});text(s,`Esperábamos solo ${L.expected_unbeaten_10000.toFixed(4)} invictos en 10 000 repeticiones`,66,612,1150,40,25);
s=slide('Cero observaciones no significa imposibilidad',sources.book);paragraphs(s,[`Producto analítico: ${sci(L.p_unbeaten)}`,`IC binomial del 95 %: 0 a ${P(L.simulation.ci95[1])}`,`P(no observar un invicto) = ${P((1-L.p_unbeaten)**10000)}`,'El intervalo mide error de simulación, no error del modelo'],{y:211,gap:101,size:29});
s=slide('La fórmula Poisson y las cero derrotas',sources.book+' Página impresa 124, página 140 del PDF. Recorte de la fórmula original.');
await equationImage(s,'book_poisson',78,214,1120,95);
text(s,'Goldsman y Goldsman · capítulo 4 · p. 124 (p. 140 del PDF)',78,330,1120,34,19);
prose(s,['El texto proporciona la función de masa de Poisson. Para estudiar un campeón invicto sustituimos k = 0: la potencia λ⁰ y el factorial 0! valen uno, de modo que queda P(D = 0) = exp(−λ).','Después sustituimos λ por la media histórica de derrotas. La operación es una estimación bajo el supuesto Poisson; no convierte la media observada en un parámetro conocido ni garantiza que esa distribución describa perfectamente todas las temporadas.'],{y:391,gap:126,size:25});
s=slide('Cero derrotas de un campeón histórico',sources.hist+' '+sources.book);chart(s,H.fits.map(x=>x.group),H.fits.map(x=>100*x.p_zero),{name:'P de cero derrotas (%)'});await equationImage(s,'poisson',65,604,1130,52);
s=slide('Un equipo antes del torneo y un campeón histórico',sources.hist+' '+sources.elo);paragraphs(s,['Elo: un equipo concreto antes de disputar 34 partidos','Poisson histórico: un equipo que ya sabemos que fue campeón',`Bayern promedia ${H.fits[1].mean.toFixed(2)} derrotas y otros campeones, ${H.fits[2].mean.toFixed(2)}`,'La muestra tiene subdispersión: la binomial negativa no la corrige'],{y:211,gap:101,size:28});
s=slide('Cuatro partidos salvaron el invicto',sources.events);paragraphs(s,['Bayern · Palacios · 93:46 · empate 2–2','Hoffenheim · Andrich · 87:24 · victoria 2–1','Dortmund · Stanišić · 96:52 · empate 1–1','Stuttgart · Andrich · 95:59 · empate 2–2'],{y:211,gap:101,size:30});
s=slide('La fragilidad de los rescates',sources.events+' Tasas históricas de liga 2018/19–2022/23. Duración restante observada.');chart(s,['Bayern','Hoffenheim','Dortmund','Stuttgart'],L.rescues.map(x=>100*x.q),{name:'Probabilidad de rescate (%)'});await equationImage(s,'rescues',65,590,1130,69);
s=slide('Suerte y capacidad no se separan con cuatro casos',sources.events);paragraphs(s,[`Índice del ejercicio: P(inv icto) × Q = ${sci(L.adjusted)}`.replace('inv icto','invicto'),'Es un ajuste heurístico, con riesgo de contar dos veces la dificultad','La presión, los cambios y la calidad también pueden producir goles tardíos','El análisis mide fragilidad, sin atribuirla exclusivamente a la suerte'],{y:211,gap:101,size:27});
conclusion(1);
part=2;s=pres.slides.add();n++;await image(s,'cape_verde.png');text(s,'Cabo Verde',65,180,590,110,67,'#FFFFFF',true);text(s,'La eliminatoria y\nel escenario mundialista',65,340,610,180,41,'#FFFFFF');s.speakerNotes.textFrame.setText('Ilustración editorial. La ruta eliminatoria del ejercicio se trata como contrafactual.');
s=slide('Cabo Verde: una historia en varias etapas',sources.nat+' '+sources.rules);prose(s,['El segundo caso cambia la escala: pasamos de un club que disputa una liga a una selección que debe superar etapas sucesivas. La primera pregunta se sitúa antes de la eliminatoria africana: ¿qué probabilidad tiene Cabo Verde de terminar por encima de los otros cinco equipos de su grupo?','El ejercicio excluye el repechaje. El éxito se define como ganar directamente el grupo, no como obtener una plaza por cualquier vía. Debemos simular todos los partidos: la clasificación también depende de lo que hagan Camerún, Angola, Libia, Esuatini y Mauricio.'],{gap:210});
s=slide('Del grupo mundialista a la ruta propuesta',sources.nat+' '+sources.rules);prose(s,['En el escenario planteado, Cabo Verde comparte grupo con España, Uruguay y Arabia Saudita. Distinguimos dos cuestiones: la probabilidad de obtener tres empates y la probabilidad de avanzar una vez que esos tres empates ya ocurrieron.','La parte final es un contrafactual con rivales fijados y avance garantizado por penales al empatar. La narración del enunciado sobre el arbitraje no se toma como evidencia histórica ni como variable estadística. El cálculo evalúa la ruta deportiva bajo sus supuestos.'],{gap:210});

await notation(2);
variableSlides(2);
s=slide('Clasificación directa desde el grupo D',sources.nat+' '+sources.rules);chart(s,['Camerún','Cabo Verde','Angola','Libia','Esuatini','Mauricio'],[1625,1474,1388,1331,1286,1031],{name:'Elo previo a la eliminatoria',color:blue});text(s,'Seis selecciones · ida y vuelta · solo clasifica el primero',65,610,1140,45,25);
s=slide('Cabo Verde gana el grupo en el 12.88 %',sources.nat+' Modelo propio. 10 000 simulaciones.');paragraphs(s,['30 partidos por grupo y 10 por selección',`${C.qualifying.successes} clasificaciones directas de 10 000`,`IC 95 %: ${P(C.qualifying.ci95[0])} a ${P(C.qualifying.ci95[1])}`,'Sin repechaje y con 100 puntos Elo de ventaja local'],{y:211,gap:101,size:30});
s=slide('El grupo H se evalúa dentro de los doce grupos',sources.nat+' '+sources.rules);chart(s,['España','Uruguay','Arabia Saudita','Cabo Verde'],['ES','UY','SA','CV'].map(x=>C.world_elo[x]),{name:'Elo anterior al 11 de junio de 2026',color:blue});text(s,'Pasan los dos primeros y los ocho mejores terceros',65,610,1150,45,27);
s=slide('Tres empates cambian la probabilidad de avanzar',sources.nat+' '+sources.rules);chart(s,['Sin condiciones','Tres empates','Tres empates +\nUruguay no pierde','Tres empates +\ntercer puesto'],['grupo_sin_condicionar','tres_empates','tres_empates_y_uruguay_no_pierde','tres_empates_y_tercero'].map(x=>100*C.scenarios[x].p),{color:blue});text(s,'Cada barra usa el denominador de su condición',65,610,1140,45,27);
s=slide('Obtener los empates y avanzar después',sources.nat+' Modelo condicionado a marcadores k–k.');paragraphs(s,[`P(empatar los tres partidos) = ${P(C.p_three_draws)}`,`P(avanzar | tres empates) = ${P(C.scenarios.tres_empates.p)}`,'Tres empates dejan tres puntos y diferencia de goles cero','No equivalen a una victoria y dos derrotas'],{y:211,gap:101,size:30});
s=slide('La ruta a partir de Egipto',sources.nat+' Supuesto del ejercicio: todo empate implica avanzar en penales.');chart(s,['Egipto','Suiza','Inglaterra','España'],C.knockouts.slice(1).map(x=>100*x.p_advance),{name:'P de victoria o empate (%)',color:blue});text(s,'Se supone que Cabo Verde ya superó a Argentina',65,610,1140,45,26);
s=slide('La probabilidad depende del punto de partida',sources.nat+' Productos para la ruta fija del ejercicio.');paragraphs(s,[`Después de Argentina: ${P(C.title_given_pass_argentina)}`,`Incluyendo Argentina: ${(100*C.title_from_argentina).toFixed(5)} %`,`Desde el grupo H: ${(100*C.title_from_group_fixed_route).toFixed(6)} %`,'La ruta está fijada y los penales siempre favorecen a Cabo Verde'],{y:211,gap:101,size:30});
await development(2);
await numericalExamples(2);
conclusion(2);
part=3;
const refs=[
 ['El sistema de valoración Elo', [['ClubElo · explicación del sistema','https://clubelo.com/System'],['Arpad Elo · The Rating of Chessplayers','https://gwern.net/doc/statistics/order/comparison/1978-elo-theratingofchessplayerspastandpresent.pdf']]],
 ['Datos de clubes y partidos',[
  ['Curley · resultados históricos','https://github.com/jalapic/engsoccerdata'],
  ['ClubElo · archivo de valoraciones','https://github.com/xgabora/Club-Football-Match-Data/blob/main/data/EloRatings.csv'],
  ['StatsBomb · eventos de los partidos','https://github.com/statsbomb/open-data']]],
 ['Selecciones y reglas de clasificación',[
  ['World Football Elo Ratings · historiales','https://www.eloratings.net/'],
  ['CAF · eliminatoria africana','https://www.cafonline.com/news/everything-you-need-to-know-about-2026-world-cup-qualifying-for-africa/'],
  ['FIFA · clasificación y desempates','https://www.fifa.com/es/tournaments/mens/worldcup/canadamexicousa2026/articles/grupos-como-funcionan-clasificacion-criterios-desempate']]],
 ['Fundamentos y contraste histórico',[
  ['SciPy · distribución Skellam','https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skellam.html'],
  ['SciPy · distribución Poisson','https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.poisson.html'],
  ['DSFS · tablas históricas de Bundesliga','https://www.dsfs.de/wp-content/uploads/2024/01/Bundesliga_Geschichte_Tabellen.pdf']]]
];
const linkMap={};
for(const [title,rows] of refs){s=slide(title,rows.map(x=>x[1]).join('\n'));rows.forEach(([label,url],i)=>{text(s,label,70,210+i*133,1130,46,29,blue,true);text(s,url,70,262+i*133,1125,72,19,ink);linkMap[label]=url;linkMap[url]=url;});}
s=slide('Referencia del curso');prose(s,['David Goldsman y Paul Goldsman. A First Course in Probability. Versión del libro proporcionada para el curso: fundamentos de probabilidad, variables aleatorias y distribuciones discretas.','Capítulos 1 y 4–6. Las capturas de las fórmulas binomial y Poisson corresponden a las páginas impresas 118 y 124. Las ecuaciones del enlace Elo–Poisson y los productos de eventos desarrollan el modelo utilizado en este estudio.'],{gap:210});
s=pres.slides.add();n++;await image(s,'football_cover.png');text(s,'Gracias',70,190,1120,110,76,'#FFFFFF',true);text(s,'Preguntas y discusión',75,332,1100,70,37,'#FFFFFF');text(s,'Leverkusen y Cabo Verde\nUniversidad del Istmo',75,525,1100,90,28,'#FFFFFF');
await fs.writeFile(root+'/.build/deck/links.json',JSON.stringify(linkMap));
const skill='/Users/pabloflores/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';await fs.mkdir(root+'/.build/deck',{recursive:true});const candidate=root+'/.build/deck/candidate.pptx';await(await PresentationFile.exportPptx(pres)).save(candidate);
execFileSync('/Users/pabloflores/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',[root+'/docs/add_transitions.py',candidate]);
execFileSync('/Users/pabloflores/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',[root+'/docs/add_links.py',candidate,root+'/.build/deck/links.json']);
for(let i=0;i<pres.slides.items.length;i++){const s=pres.slides.items[i];const png=await pres.export({slide:s,format:'png',scale:1});await fs.writeFile(root+`/.build/deck/slide-${i+1}.png`,new Uint8Array(await png.arrayBuffer()));}
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:root+'/outputs/presentacion_glosario.pptx',pythonExecutable:'/Users/pabloflores/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],requiredNativeChartOwnerSlides:native,materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[family]},verifyArtifactToolImport:true,receiptPath:root+'/.build/deck/validation-'+Date.now()+'.json'});console.log('Slides',n,'font',family);
