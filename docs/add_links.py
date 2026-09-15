"""Añade hipervínculos externos a las referencias visibles del PowerPoint."""
import json,sys,zipfile
from lxml import etree as E
from pathlib import Path
p=Path(sys.argv[1]);links=json.loads(Path(sys.argv[2]).read_text())
A='http://schemas.openxmlformats.org/drawingml/2006/main';R='http://schemas.openxmlformats.org/officeDocument/2006/relationships';P='http://schemas.openxmlformats.org/package/2006/relationships'
with zipfile.ZipFile(p) as z: files={n:z.read(n) for n in z.namelist()}
for n in list(files):
 if not n.startswith('ppt/slides/slide') or not n.endswith('.xml'):continue
 root=E.fromstring(files[n]);relname='ppt/slides/_rels/'+Path(n).name+'.rels';rels=E.fromstring(files[relname]) if relname in files else E.Element('{'+P+'}Relationships',nsmap={None:P})
 for run in root.findall('.//{'+A+'}r'):
  t=run.find('{'+A+'}t')
  if t is None or t.text not in links:continue
  rid='rIdLink'+str(len(rels)+1);E.SubElement(rels,'{'+P+'}Relationship',Id=rid,Type=R+'/hyperlink',Target=links[t.text],TargetMode='External')
  props=run.find('{'+A+'}rPr')
  if props is None:props=E.Element('{'+A+'}rPr');run.insert(0,props)
  E.SubElement(props,'{'+A+'}hlinkClick',{'{'+R+'}id':rid})
 files[n]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True);files[relname]=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for n,b in files.items():z.writestr(n,b)
