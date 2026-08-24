#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repositionne le cad de MON fichier sur le layout du Design (screenshots):
reconciliation 10-13 (header 7-8, gap 9), coeff MBway J10..J14, leviers en
colonnes C/D/E (Cadrage/Optimiste/Prudent)+F(ACTIF) avec espaces:
revenus 20-25, couts 30-34, frais 37. Chirurgie -> graphes/images preserves."""
from tgk_surgery import Book
b=Book("EDUSERVICES_Simulateur_CFO.xlsx")
cad=b.sheet("cad")
# --- step 1 (cibles) integre : Marge EBITDA cible G3/H3 -> E4/F4 ---
sl=cad.get_style("G3"); sv=cad.get_style("H3")
cad.set_text("E4","Marge EBITDA cible :",sl); cad.set_number("F4",0.15,sv)
cad.clear("G3"); cad.clear("H3"); b.retarget_name("TEC_EBITDA","cad!$F$4")
G=cad.get_cell   # (attrs, content)
# ---------- capture des cellules sources ----------
cap={}
for r in range(5,46):
    for c in "BCDEFGHJKL":
        v=G("%s%d"%(c,r))
        if v is not None: cap[(c,r)]=v
def style(ref):
    v=G(ref); 
    import re
    m=re.search(r's="(\d+)"',v[0]) if v else None
    return int(m.group(1)) if m else None
S_recon_hdr=style("B6"); S_lever_hdr=style("B15")
# ---------- nettoyage de la zone (rows 5-31) ----------
for r in range(5,46):
    for c in "ABCDEFGHIJKL":
        cad.clear("%s%d"%(c,r))
# ---------- helper: reposer une cellule capturee a une nouvelle ref ----------
def place(src_c,src_r,dst,newcontent=None):
    v=cap.get((src_c,src_r))
    if v is None: return
    cad.put_cell(dst,v[0], v[1] if newcontent is None else newcontent)

# ================= RECONCILIATION =================
place("B",5,"B6")                       # titre
for c in "BCDEFG": place(c,6,"%s8"%c)   # header -> ligne 8 (non fusionne), ligne 7 vide
# data 7->10, 8->11, 9->12, 10->13 (refs internes +3)
def shift3(f):
    import re
    # decale les refs locales colonnes C-G lignes 7-10 de +3 ; ne touche pas $..$, ni autres feuilles
    return re.sub(r'(?<![A-Z$!])([C-G])(7|8|9|10)\b', lambda m:m.group(1)+str(int(m.group(2))+3), f)
for sr,tr in [(7,10),(8,11),(9,12),(10,13)]:
    for c in "BCDEFG":
        v=cap.get((c,sr))
        if v is None: continue
        content=v[1]
        import re as _re
        from xml.sax.saxutils import unescape,escape
        m=_re.search(r'<f>(.*?)</f>',content,_re.S) if isinstance(content,str) else None
        if m:
            content="<f>"+escape(shift3(unescape(m.group(1))))+"</f>"  # formule decalee, cache jete
        cad.put_cell("%s%d"%(c,tr),v[0],content)

# ================= COEFF PRIX =================
place("J",5,"J6")                       # titre
place("J",6,"J8"); place("K",6,"K8")    # header
for i in range(5):                       # marques J7..J11 -> J10..J14
    place("J",7+i,"J%d"%(10+i)); place("K",7+i,"K%d"%(10+i))

# ================= LEVIERS =================
place("B",14,"B16")                     # titre revenus
# header ligne 15 -> ligne 17, colonnes remappees (E->C,F->D,G->E,H->F ; drop Unite/Ref)
place("B",15,"B18"); place("E",15,"C18"); place("F",15,"D18"); place("G",15,"E18"); place("H",15,"F18")
def actif(tr): return "<f>"+"INDEX(C%d:E%d,MATCH(SCENARIO_ACTIF,$C$18:$E$18,0))"%(tr,tr)+"</f>"
def lever(sr,tr):
    place("B",sr,"B%d"%tr)              # label
    place("E",sr,"C%d"%tr)             # Cadrage (V01)
    place("F",sr,"D%d"%tr)             # Optimiste (V02)
    place("G",sr,"E%d"%tr)             # Prudent (V03)
    v=cap.get(("H",sr))
    if v is not None: cad.put_cell("F%d"%tr, v[0], actif(tr))   # ACTIF recalibre
# revenus 16-21 -> 20-25
for i,sr in enumerate(range(16,22)): lever(sr,20+i)
# couts 23-27 -> 30-34 (titre 22->28)
place("B",22,"B28")
for i,sr in enumerate(range(23,28)): lever(sr,30+i)
# frais 30 -> 37 (titre 28->36)
place("B",28,"B36"); lever(30,37)

# ================= MERGES =================
merges=["B1:H2","B6:H6","J6:L6","B16:H16","B28:H28","B36:H36"]
cad.set_merges(merges)

# ================= ZONES NOMMEES repointees =================
d={}
# leviers: V01->C, V02->D, V03->E aux nouvelles lignes
LEVROW={"ACQ_BUD":20,"BRAND_BUD":21,"PRICE":22,"CONV_LEAD":23,"CONV_ADM":24,"PASSAGE":25,
        "INFL_EXT":30,"SALARY":31,"FTE_PERM":32,"PRODUCTIVITY":33,"STRUCT_COST":34,"FEE":37}
for p,r in LEVROW.items():
    d["HYP_%s_V01"%p]="cad!$C$%d"%r; d["HYP_%s_V02"%p]="cad!$D$%d"%r; d["HYP_%s_V03"%p]="cad!$E$%d"%r
for m,r in {"MBWAY":10,"ISCOM":11,"IPAC":12,"PIGIER":13,"TUNON":14}.items():
    d["HYP_PRICE_COEF_%s"%m]="cad!$K$%d"%r
for nm,ref in d.items(): b.retarget_name(nm,ref)

# --- trajectoire deplacee plus bas (etait ecrasee par leviers/frais) ---
for i,sr in enumerate(range(33,39)):
    for c in "BCDE": place(c,sr,"%s%d"%(c,40+i))
b.set_fullcalc(); b.save("MOTEUR_adapte.xlsx")
print("OK cad repositionne.")
