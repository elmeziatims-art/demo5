#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copie A L'IDENTIQUE le prototype dans le DESIGN : transplante le sheetData
(+ largeurs colonnes + fusions + STYLES fusionnes) de chaque onglet, reprend les
zones nommees exactes, garde la coquille Tagetik (_TGK_HIDDEN, customProperty,
customXml, webextensions) intacte. Renomme Pilotage->PIL, 3_Allocation->ALLOC."""
import zipfile,re
from tgk_surgery import Book
from style_merge import StyleMerger
PROTO="CAD_SAAD_LIVE.xlsx"

def REMAP(f):
    return (f.replace("'3_Allocation'!","ALLOC!").replace("3_Allocation!","ALLOC!")
             .replace("'Pilotage'!","PIL!").replace("Pilotage!","PIL!"))
def extract(xml):
    m=re.search(r'<sheetData>(.*?)</sheetData>',xml,re.S)
    inner=m.group(1) if m else ""
    cols=re.search(r'<cols>.*?</cols>',xml,re.S); cols=cols.group(0) if cols else None
    mc=re.search(r'<mergeCells count="\d+">.*?</mergeCells>|<mergeCells count="\d+"/>',xml,re.S); mc=mc.group(0) if mc else None
    dim=re.search(r'<dimension ref="([^"]+)"',xml); dim=dim.group(1) if dim else None
    return inner,cols,mc,dim
def xform(inner,map_xf):
    inner=re.sub(r'\bs="(\d+)"', lambda m:'s="%d"'%map_xf(int(m.group(1))), inner)
    return REMAP(inner)
def xcols(cols,map_xf):
    return re.sub(r'style="(\d+)"', lambda m:'style="%d"'%map_xf(int(m.group(1))), cols) if cols else None

# onglets DESIGN <- onglets prototype
INPLACE={"cad":"cad","PIL":"Pilotage","ALLOC":"3_Allocation","Socle":"Socle",
         "Campagne":"Campagne","Moteur":"Moteur","Compta":"Compta","PNL":"PNL","Allocation":"Allocation"}
ADD=["_CALC_MOTEUR","_CALC_PNL","_CALC_ALLOC","00_Cartographie"]

def build(design_src,out):
    b=Book(design_src)
    pz=zipfile.ZipFile(PROTO)
    sm=StyleMerger(b.styles_xml(), pz.read("xl/styles.xml").decode("utf8"))
    b.set_styles(sm.merged())
    pwb=pz.read("xl/workbook.xml").decode("utf8")
    prels=pz.read("xl/_rels/workbook.xml.rels").decode("utf8")
    prid={}
    for rel in re.findall(r'<Relationship\b[^>]*/>',prels):
        rid=re.search(r'Id="(rId\d+)"',rel); tgt=re.search(r'Target="([^"]*worksheets/sheet\d+\.xml)"',rel)
        if rid and tgt: prid[rid.group(1)]=tgt.group(1).split("worksheets/")[-1]
    p2x={n:prid[r] for n,r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"',pwb) if r in prid}
    px=lambda name: pz.read("xl/worksheets/"+p2x[name]).decode("utf8")
    # transplant sur place
    for dest,src in INPLACE.items():
        inner,cols,mc,dim=extract(px(src))
        b.sheet(dest).set_raw(xform(inner,sm.map_xf),xcols(cols,sm.map_xf),mc,dim)
    # onglets ajoutes
    for name in ADD:
        inner,cols,mc,dim=extract(px(name))
        b.add_sheet(name).set_raw(xform(inner,sm.map_xf),xcols(cols,sm.map_xf),mc,dim)
    # zones nommees exactes (remap noms de feuille, skip #REF!)
    defs={}
    for m in re.finditer(r'<definedName name="([^"]+)"[^>]*>([^<]*)</definedName>',pwb):
        nm,ref=m.group(1),m.group(2)
        if "#REF!" in ref: continue
        defs[nm]=REMAP(ref)
    b.add_names(defs)
    b.set_fullcalc(); b.save(out)
    return len(defs)

n=build("DESIGN.xlsm","DESIGN_IDENT.xlsm")
print("OK. zones nommees:",n)
