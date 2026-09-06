#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrige la navigation : les cles d'allocation ne pilotaient pas la maille car
les zones nommees ALLOC_* pointaient vers les helpers CODES (N1-N4 = REV_CA/
VOL_EFF/VOL_CLASS) alors que le moteur _CALC_ALLOC compare aux LIBELLES
(\"Chiffre d'affaires\"/\"Effectif\"/\"Nombre de classes\"). On repointe les zones
nommees vers les listes deroulantes C6-C9 (libelles), comme le prototype.
Chirurgical : seul workbook.xml change ; les 82 briques Tagetik restent intactes."""
import zipfile,re,os
SRC="TEST_NAV.xlsx"; OUT="TEST_NAV_corrige.xlsx"
# zone nommee -> cellule libelle (dropdown)
REMAP={"ALLOC_GRP_BRAND":"ALLOC!$C$6","ALLOC_GRP_MARQUE":"ALLOC!$C$7",
       "ALLOC_BRAND_CAMP":"ALLOC!$C$8","ALLOC_CAMP_CLASS":"ALLOC!$C$9"}

zin=zipfile.ZipFile(SRC); tmp=OUT+".tmp"
changed={}
with zipfile.ZipFile(tmp,"w") as zout:
    for it in zin.infolist():
        data=zin.read(it.filename)
        if it.filename=="xl/workbook.xml":
            txt=data.decode("utf8")
            for nm,newref in REMAP.items():
                def repl(m):
                    changed[nm]=(m.group(2),newref); return m.group(1)+newref+m.group(3)
                txt=re.sub(r'(<definedName name="%s"[^>]*>)([^<]*)(</definedName>)'%re.escape(nm),repl,txt)
            if "fullCalcOnLoad" not in txt:
                txt=re.sub(r'<calcPr\b','<calcPr fullCalcOnLoad="1"',txt,count=1)
            data=txt.encode("utf8")
        zout.writestr(it,data)
os.replace(tmp,OUT)
print("Zones nommees repointees :")
for nm,(old,new) in changed.items(): print("   %-18s %s -> %s"%(nm,old,new))
# verif
z2=zipfile.ZipFile(OUT)
tgk=[n for n in z2.namelist() if 'customProperty' in n or 'webext' in n or 'customXml' in n]
print("OUT:",OUT,round(os.path.getsize(OUT)/1024/1024,2),"Mo | briques Tagetik:",len(tgk),
      "| testzip:","OK" if z2.testzip() is None else "KO")
wbx=z2.read("xl/workbook.xml").decode("utf8")
for m in re.finditer(r'<definedName name="(ALLOC_[^"]+)"[^>]*>([^<]*)</definedName>',wbx):
    print("   verif %s = %s"%(m.group(1),m.group(2)))
