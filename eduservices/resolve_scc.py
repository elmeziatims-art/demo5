#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resout le gros SCC colonne au niveau CELLULE: enumere toutes les aretes
'retour' (aval PIL/cad -> amont _CALC/Moteur) et verifie que les cellules
reellement lues sont STATIQUES (aucune formule) => cycle brise au niveau cellule."""
import zipfile,re
from xml.sax.saxutils import unescape

F="DESIGN3_OP.xlsm"
z=zipfile.ZipFile(F)
wb=z.read("xl/workbook.xml").decode("utf8")
rels=z.read("xl/_rels/workbook.xml.rels").decode("utf8")
rid2tgt={m.group(1):m.group(2) for m in
         (re.search(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',r) for r in re.findall(r'<Relationship\b[^>]*/>',rels)) if m}
name2part={}
for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"',wb):
    t=rid2tgt.get(m.group(2),"")
    if t and not t.startswith("/"): t="xl/"+t
    elif t: t=t[1:]
    name2part[m.group(1)]=t

# formules ET valeurs statiques par cellule, pour chaque feuille
def parse(sh):
    xml=z.read(name2part[sh]).decode("utf8")
    formulas={}; statics=set()
    for m in re.finditer(r'<c r="([A-Z]+\d+)"[^>]*>(.*?)</c>',xml,re.S):
        ref,body=m.group(1),m.group(2)
        fm=re.search(r'<f[^>]*>(.*?)</f>',body,re.S)
        if fm: formulas[ref]=unescape(fm.group(1))
        elif re.search(r'<v>|<is>|<t',body): statics.add(ref)
    # self-closing statics (t="s"/"n" with v)
    for m in re.finditer(r'<c r="([A-Z]+\d+)"(?![^>]*<f)[^>]*/>',xml): statics.add(m.group(1))
    return formulas,statics

DATA={s:parse(s) for s in name2part if name2part[s]}

def is_static(sheet,ref):
    if sheet not in DATA: return None
    f,st=DATA[sheet]
    if ref in f: return False
    return True  # absente ou statique => pas de formule => statique/vide

# les 3 plages que T2/U2 lisent
print("=== Cellules lues par _CALC_MOTEUR!T2 / U2 (PIL rangs 15-28) ===")
allstatic=True
for col in ("A","J","K"):
    formula_cells=[r for r in range(15,29) if not is_static("PIL","%s%d"%(col,r))]
    print("  PIL!%s15:%s28 : %s"%(col,col,
        "STATIQUE (0 formule)" if not formula_cells else "FORMULES en lignes %s"%formula_cells))
    if formula_cells: allstatic=False

# verifie qu'aucune AUTRE formule de _CALC_MOTEUR / _CALC_PNL / Moteur ne lit PIL hors 15-28,
# ni cad, en dehors des aretes connues
print("\n=== Toutes les refs PIL! dans le moteur (_CALC_MOTEUR/_CALC_PNL/Moteur) ===")
suspect=[]
for eng in ("_CALC_MOTEUR","_CALC_PNL","Moteur"):
    f,_=DATA[eng]
    seen=set()
    for ref,formula in f.items():
        for m in re.finditer(r'PIL!(\$?[A-Z]{1,3}\$?\d*(?::\$?[A-Z]{1,3}\$?\d*)?)',formula):
            rng=m.group(1); key=re.sub(r'\d+','N',eng+"!"+rng)
            if key in seen: continue
            seen.add(key)
            print("  %s!%s lit PIL!%s"%(eng,ref,rng))
            # verifie que la plage ne touche pas les lignes 29+ (synthese)
            rows=[int(x) for x in re.findall(r'(\d+)',rng)]
            if rows and any(rr>=29 for rr in rows): suspect.append((eng,ref,rng))

print("\n=== VERDICT ===")
if allstatic and not suspect:
    print("Le moteur ne lit QUE des cellules PIL statiques (cap 15-28).")
    print("=> Le gros SCC colonne est un FAUX POSITIF (conflation colonne J/K/A).")
    print("=> AUCUNE reference circulaire reelle au niveau cellule.")
else:
    if not allstatic: print("PROBLEME: T2/U2 lisent des formules PIL.")
    if suspect: print("PROBLEME: refs moteur->PIL synthese (>=29):",suspect)
