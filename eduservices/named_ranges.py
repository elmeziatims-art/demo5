#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nomme toutes les saisies (nom = code Tagetik) et reecrit les formules _CALC pour
utiliser les NOMS au lieu des cellules brutes. Noms STATIQUES (aucun OFFSET/INDIRECT)
-> zero surcout perf. Le classeur devient une spec executable."""
import openpyxl
from openpyxl.workbook.defined_name import DefinedName
wb=openpyxl.load_workbook("CAD_SAAD_LIVE.xlsx")

# ---------- 1) definitions des noms ----------
defs={}  # name -> refers_to
LEV={16:"HYP_ACQ_BUD",17:"HYP_BRAND_BUD",18:"HYP_PRICE",19:"HYP_CONV_LEAD",20:"HYP_CONV_ADM",
     21:"HYP_PASSAGE",23:"HYP_INFL_EXT",24:"HYP_SALARY",25:"HYP_FTE_PERM",26:"HYP_PRODUCTIVITY",
     27:"HYP_STRUCT_COST",30:"HYP_FEE"}
for row,nm in LEV.items():
    defs["%s_V01"%nm]="cad!$E$%d"%row; defs["%s_V02"%nm]="cad!$F$%d"%row; defs["%s_V03"%nm]="cad!$G$%d"%row
COEF={7:"MBWAY",8:"ISCOM",9:"IPAC",10:"PIGIER",11:"TUNON"}
for row,m in COEF.items(): defs["HYP_PRICE_COEF_%s"%m]="cad!$K$%d"%row
defs["ALLOC_GRP_BRAND"]="'3_Allocation'!$C$5"; defs["ALLOC_GRP_MARQUE"]="'3_Allocation'!$C$6"
defs["ALLOC_BRAND_CAMP"]="'3_Allocation'!$C$7"; defs["ALLOC_CAMP_CLASS"]="'3_Allocation'!$C$8"
defs["TEC_PL"]="cad!$F$3"; defs["TEC_EBITDA"]="cad!$H$3"
defs["SCENARIO_ACTIF"]="cad!$D$3"; defs["SCENARIO_CODE"]="cad!$P$1"
defs["HYP_CAP_RETENU"]="Pilotage!$M$13:$M$26"; defs["BUD_REF_CAP"]="Pilotage!$N$13:$N$26"
for nm,ref in defs.items():
    wb.defined_names[nm]=DefinedName(nm,attr_text=ref)
print("noms definis:",len(defs))

# ---------- 2) map de substitution (ref brute -> nom) ----------
sub={}
for row,nm in LEV.items():
    sub["cad!$E$%d"%row]="%s_V01"%nm; sub["cad!$F$%d"%row]="%s_V02"%nm; sub["cad!$G$%d"%row]="%s_V03"%nm
for row,m in COEF.items(): sub["cad!$K$%d"%row]="HYP_PRICE_COEF_%s"%m
sub["'3_Allocation'!$C$5"]="ALLOC_GRP_BRAND"; sub["'3_Allocation'!$C$6"]="ALLOC_GRP_MARQUE"
sub["'3_Allocation'!$C$7"]="ALLOC_BRAND_CAMP"; sub["'3_Allocation'!$C$8"]="ALLOC_CAMP_CLASS"
sub["cad!$P$1"]="SCENARIO_CODE"
keys_sorted=sorted(sub,key=len,reverse=True)  # longs d'abord
def apply(v):
    if not isinstance(v,str) or not v.startswith("="): return v
    for k in keys_sorted:
        if k in v: v=v.replace(k,sub[k])
    return v

n=0
for tab in ["_CALC_MOTEUR","_CALC_PNL","_CALC_ALLOC","Pilotage"]:
    ws=wb[tab]
    for row in ws.iter_rows():
        for c in row:
            nv=apply(c.value)
            if nv is not c.value and nv!=c.value: c.value=nv; n+=1
print("cellules calc reecrites (cross-sheet):",n)

# ---------- 3) cad interne + Pilotage rejoue (refs locales) ----------
cad=wb["cad"]
cad["D7"]="=C7*(1+TEC_PL)"; cad["D8"]="=D7*TEC_EBITDA"; cad["D9"]="=TEC_EBITDA"
for c in ("E7","E8","E10"): cad[c]=cad[c].value.replace("$P$1","SCENARIO_CODE")
for r in range(16,31):
    c=cad["H%d"%r]
    if isinstance(c.value,str) and "$D$3" in c.value: c.value=c.value.replace("$D$3","SCENARIO_ACTIF")
ps=wb["Pilotage"]
for r in range(13,27):
    c=ps["Q%d"%r]
    if isinstance(c.value,str):
        c.value=c.value.replace("$N$13:$N$26","BUD_REF_CAP").replace("$M$13:$M$26","HYP_CAP_RETENU")

wb.calculation.fullCalcOnLoad=True
wb.save("CAD_SAAD_LIVE.xlsx")
print("OK plages nommees + formules reecrites.")
