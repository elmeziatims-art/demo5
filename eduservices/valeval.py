#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cree une copie a plages BORNEES (pour que la lib `formulas` la digere) et
calcule quelques cellules cles pour valider la chaine EBITDA de la synthese."""
import openpyxl, re, warnings, formulas
warnings.filterwarnings("ignore")
BOUND={"Socle":200,"Campagne":30,"Compta":700,"Moteur":200,"Pilotage":70,
       "PNL":1400,"_CALC_MOTEUR":200,"_CALC_PNL":1400,"_CALC_ALLOC":200,"Allocation":200,"cad":70}
wb=openpyxl.load_workbook("CAD_SAAD_LIVE.xlsx")
# regex: (Sheet!)?$COL:$COL  ->  bounded. Handle optional sheet, else default per current sheet.
full=re.compile(r"((?:'?[\w ]+'?!)?)\$([A-Z]{1,3}):\$([A-Z]{1,3})")
def bound_for(sheetref, cur):
    name=sheetref.strip("!'") if sheetref else cur
    return BOUND.get(name, 1400)
def fix(formula, cur):
    def rep(m):
        sr,c1,c2=m.group(1),m.group(2),m.group(3)
        n=bound_for(sr,cur)
        return "%s$%s$1:$%s$%d"%(sr,c1,c2,n)
    return full.sub(rep, formula)
for ws in wb.worksheets:
    if ws.sheet_state!="visible" and not ws.title.startswith("_CALC"):
        pass
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value,str) and c.value.startswith("=") and ":$" in c.value:
                c.value=fix(c.value, ws.title)
wb.save("/tmp/bounded.xlsx"); wb.close()
print("bounded copy saved")
xl=formulas.ExcelModel().loads("/tmp/bounded.xlsx").finish()
sol=xl.calculate()
def get(sheet,cell):
    for k in sol:
        if k.upper().endswith("]%s'!%s"%(sheet.upper(),cell)):
            v=sol[k].value
            try:return float(v[0,0])
            except:
                try:return float(v)
                except:return v
    return "NOTFOUND"
print("Moteur!R2 (CA live) =",get("Moteur","R2"))
print("Pilotage!H30 (synth CA MBWAY_PAR) =",get("Pilotage","H30"))
print("Pilotage!K30 (synth EBITDA MBWAY_PAR) =",get("Pilotage","K30"))
print("Pilotage!K44 (sous-total EBITDA) =",get("Pilotage","K44"))
print("Pilotage!K45 (siege) =",get("Pilotage","K45"))
print("Pilotage!K46 (GROUPE EBITDA) =",get("Pilotage","K46"))
print("cad!E8 (recon EBITDA) =",get("cad","E8"))
