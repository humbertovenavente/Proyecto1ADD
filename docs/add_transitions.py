"""Añade fundidos y desplazamientos suaves a una presentación PPTX."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import sys, re
from lxml import etree

p = Path(sys.argv[1])
tmp = p.with_suffix(".transitioned.pptx")
ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
with ZipFile(p) as source, ZipFile(tmp, "w", ZIP_DEFLATED) as dest:
    for entry in source.infolist():
        data = source.read(entry.filename)
        m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", entry.filename)
        if m:
            root = etree.fromstring(data)
            for old in root.findall("p:transition", ns):
                root.remove(old)
            t = etree.Element("{" + ns["p"] + "}transition", spd="slow", advClick="1")
            etree.SubElement(
                t,
                "{" + ns["p"] + "}" + ("push" if False else "fade"),
                **({"dir": "l"} if False else {}),
            )
            anchor = root.find("p:clrMapOvr", ns)
            at = root.index(anchor) + 1 if anchor is not None else 1
            root.insert(at, t)
            data = etree.tostring(
                root, xml_declaration=True, encoding="UTF-8", standalone=True
            )
        dest.writestr(entry, data)
tmp.replace(p)
