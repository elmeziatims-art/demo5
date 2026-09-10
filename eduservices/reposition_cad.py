#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repositionne cad sur le layout Design (v2): ligne 1 vide, titre L2, 2 lignes
vides, scenario actif B5 + dropdown C5, cibles E5/F5 & E6/F6, reconciliation
8/10/12-15, coeff J12-J16, leviers 22-27/32-36/39, trajectoire 42-47."""
from tgk_surgery import Book
import re as _re
from xml.sax.saxutils import unescape,escape
b=Book("EDUSERVICES_Simulateur_CFO.xlsx")
cad=b.sheet("cad")
G=cad.get_cell
# capture large (title + zone + trajectoire)
cap={}
for r in range(1,46):
    for c in "BCDEFGHJKL":
        v=G("%s%d"%(c,r))
        if v is not None: cap[(c,r)]=v
for r in range(1,46):
    for c in "ABCDEFGHIJKL": cad.clear("%s%d"%(c,r))
def place(sc,sr,dst,newcontent=None):
    v=cap.get((sc,sr))
    if v is None: return
    cad.put_cell(dst,v[0], v[1] if newcontent is None else newcontent)
def shift(f,delta,lo,hi):
    return _re.sub(r'(?<![A-Z$!])([C-H])(\d+)\b',
        lambda m:m.group(1)+(str(int(m.group(2))+delta) if lo<=int(m.group(2))<=hi else m.group(2)), f)
def move_shift(sc,sr,dst,delta,lo,hi):
    v=cap.get((sc,sr))
    if v is None: return
    content=v[1]
    m=_re.search(r'<f>(.*?)</f>',content,_re.S) if isinstance(content,str) else None
    if m: content="<f>"+escape(shift(unescape(m.group(1)),delta,lo,hi))+"</f>"
    cad.put_cell(dst,v[0],content)

# ===== TOP =====
place("B",1,"B2")                                   # titre -> ligne 2
place("B",3,"B5"); place("D",3,"C5")                # scenario actif B5, dropdown C5
place("E",3,"E5"); place("F",3,"F5")                # Croissance CA cible E5/F5
place("G",3,"E6", cap[("G",3)][1]); place("H",3,"F6")  # Marge EBITDA cible E6/F6

# ===== RECONCILIATION (title B5->B8, header r6->r10, data r7-10 -> r12-15 : +5) =====
place("B",5,"B8")
for c in "BCDEFG": place(c,6,"%s10"%c)
for sr,tr in [(7,12),(8,13),(9,14),(10,15)]:
    for c in "BCDEFG": move_shift(c,sr,"%s%d"%(c,tr),+5,7,10)

# ===== COEFF (title J5->J8, header r6->r10, marques J7-11 -> J12-16) =====
place("J",5,"J8"); place("J",6,"J10"); place("K",6,"K10")
for i in range(5): place("J",7+i,"J%d"%(12+i)); place("K",7+i,"K%d"%(12+i))

# ===== LEVIERS (col E/F/G/H -> C/D/E/F ; +6 lignes) =====
place("B",14,"B18")                                 # titre revenus
place("B",15,"B20"); place("E",15,"C20"); place("F",15,"D20"); place("G",15,"E20"); place("H",15,"F20")
def actif(tr): return "<f>INDEX(C%d:E%d,MATCH(SCENARIO_ACTIF,$C$20:$E$20,0))</f>"%(tr,tr)
def lever(sr,tr):
    place("B",sr,"B%d"%tr); place("E",sr,"C%d"%tr); place("F",sr,"D%d"%tr); place("G",sr,"E%d"%tr)
    if cap.get(("H",sr)) is not None: cad.put_cell("F%d"%tr, cap[("H",sr)][0], actif(tr))
for i,sr in enumerate(range(16,22)): lever(sr,22+i)   # revenus 22-27
place("B",22,"B30")                                   # titre couts
for i,sr in enumerate(range(23,28)): lever(sr,32+i)   # couts 32-36
place("B",28,"B38"); lever(30,39)                     # frais titre 38, frais 39

# ===== TRAJECTOIRE (33-38 -> 42-47) =====
for i,sr in enumerate(range(33,39)):
    for c in "BCDE": place(c,sr,"%s%d"%(c,42+i))

# ===== MERGES =====
cad.set_merges(["B2:H2","B8:H8","J8:L8","B18:H18","B30:H30","B38:H38"])

# ===== CIBLES/SCENARIO steps integres =====
cad.put_cell("E6", cad.get_cell("E6")[0], "<is><t>Marge EBITDA cible :</t></is>") if cad.get_cell("E6") else None

# ===== NOMS repointes =====
d={"SCENARIO_ACTIF":"cad!$C$5","TEC_PL":"cad!$F$5","TEC_EBITDA":"cad!$F$6"}
LEVROW={"ACQ_BUD":22,"BRAND_BUD":23,"PRICE":24,"CONV_LEAD":25,"CONV_ADM":26,"PASSAGE":27,
        "INFL_EXT":32,"SALARY":33,"FTE_PERM":34,"PRODUCTIVITY":35,"STRUCT_COST":36,"FEE":39}
for p,r in LEVROW.items():
    d["HYP_%s_V01"%p]="cad!$C$%d"%r; d["HYP_%s_V02"%p]="cad!$D$%d"%r; d["HYP_%s_V03"%p]="cad!$E$%d"%r
for m,r in {"MBWAY":12,"ISCOM":13,"IPAC":14,"PIGIER":15,"TUNON":16}.items():
    d["HYP_PRICE_COEF_%s"%m]="cad!$K$%d"%r
for nm,ref in d.items(): b.retarget_name(nm,ref)
b.set_fullcalc(); b.save("MOTEUR_adapte.xlsx")
print("OK cad v2 repositionne.")
