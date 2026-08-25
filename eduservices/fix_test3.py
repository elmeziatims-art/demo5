#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrige les references circulaires de TEST3.xlsm CHIRURGICALEMENT :
- borne les lookups cap colonne-entiere de _CALC_MOTEUR (sheet11) aux lignes 15-28
- force le recalcul a l'ouverture (calcPr fullCalcOnLoad)
Toutes les autres parts (briques Tagetik, styles, autres onglets) restent
BYTE-IDENTIQUES (memes ZipInfo)."""
import zipfile,re,os
SRC="TEST3.xlsm"; OUT="TEST3_corrige.xlsm"
CALC_PART="xl/worksheets/sheet11.xml"     # _CALC_MOTEUR
WB_PART="xl/workbook.xml"

REPL=[("PIL!$K:$K","PIL!$K$15:$K$28"),
      ("PIL!$J:$J","PIL!$J$15:$J$28"),
      ("PIL!$A:$A","PIL!$A$15:$A$28")]

zin=zipfile.ZipFile(SRC)
tmp=OUT+".tmp"
counts={}
with zipfile.ZipFile(tmp,"w") as zout:
    for it in zin.infolist():
        data=zin.read(it.filename)
        if it.filename==CALC_PART:
            txt=data.decode("utf8")
            for a,b in REPL:
                counts[a]=txt.count(a); txt=txt.replace(a,b)
            data=txt.encode("utf8")
        elif it.filename==WB_PART:
            txt=data.decode("utf8")
            if "fullCalcOnLoad" not in txt:
                txt=re.sub(r'<calcPr\b','<calcPr fullCalcOnLoad="1"',txt,count=1)
            data=txt.encode("utf8")
        zout.writestr(it, data)     # reutilise le ZipInfo d'origine -> metadata preservee
os.replace(tmp,OUT)
print("Remplacements dans _CALC_MOTEUR:",counts)
# verif structurelle
z2=zipfile.ZipFile(OUT)
tgk=[n for n in z2.namelist() if 'customProperty' in n or 'webext' in n or 'customXml' in n]
print("OUT:",OUT,round(os.path.getsize(OUT)/1024/1024,2),"Mo | briques Tagetik:",len(tgk),
      "| testzip:", "OK" if z2.testzip() is None else "KO")
cx=z2.read(CALC_PART).decode("utf8")
print("reste PIL!$K:$K :",cx.count("PIL!$K:$K"),"| PIL!$J:$J :",cx.count("PIL!$J:$J"),
      "| PIL!$A:$A :",cx.count("PIL!$A:$A"))
print("nouvelles bornees PIL!$K$15:$K$28 :",cx.count("PIL!$K$15:$K$28"))
print("calcPr:",re.search(r'<calcPr[^>]*/?>',z2.read(WB_PART).decode("utf8")).group(0))