#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restructure Pilotage sur le Design: ligne 1 vide, cap title B13, header L14
(code en A, colonnes du screen, sans SCENARIO/PERIODE, Delta vs Tagetik en L),
data 15-28, synthese decalee +2. Remap complet formules + noms. Sans grise."""
from tgk_surgery import Book
import re as _re
from xml.sax.saxutils import unescape,escape
b=Book("MOTEUR_adapte.xlsx")
pil=b.sheet("Pilotage")
G=pil.get_cell
cap={}
for r in range(1,50):
    for c in "ABCDEFGHIJKLMNO":
        v=G("%s%d"%(c,r))
        if v is not None: cap[(c,r)]=v
for r in range(1,50):
    for c in "ABCDEFGHIJKLMNO": pil.clear("%s%d"%(c,r))
def raw(sc,sr): return cap.get((sc,sr))
def place(sc,sr,dst,content=None):
    v=raw(sc,sr)
    if v is None: return
    pil.put_cell(dst,v[0], v[1] if content is None else content)
def fml(sc,sr):  # extrait la formule (sans <v> cache)
    v=raw(sc,sr)
    if not v: return None
    m=_re.search(r'<f>(.*?)</f>',v[1],_re.S) if isinstance(v[1],str) else None
    return unescape(m.group(1)) if m else None
def shiftrows(f,delta,lo,hi):
    return _re.sub(r'(\$?[A-Z]{1,2}\$?)(\d+)',
      lambda m:m.group(1)+(str(int(m.group(2))+delta) if lo<=int(m.group(2))<=hi else m.group(2)), f)
def putf(dst,formula,style_from):
    v=raw(*style_from)
    pil.put_cell(dst, v[0] if v else "", "<f>"+escape(formula)+"</f>")

# ===== TOP (ligne 1 vide) =====
place("A",1,"A2"); place("A",2,"A3"); place("A",3,"A4")
place("B",1,"B2"); place("B",3,"B4")
# KPI labels row4 -> row5 ; values row5 -> row6 (H46->H48 etc.)
for c in "BEHKN": place(c,4,"%s5"%c)
KPIf={"B":"H48","E":"K48","H":"L48","K":"G48","N":"H48/22544725-1"}
for c,f in KPIf.items(): putf("%s6"%c,f,(c,5))

# ===== CAP : titre B13, header L14, data 15-28 =====
place("B",10,"B13")
HEAD={"A":"","B":"Marque","C":"Ville","D":"CAC marginal","E":"Croiss. leads","F":"Intensite mkt",
      "G":"Cap Eff","H":"Cap mom.","I":"Cap pot.","J":"Cap retenu","K":"Budget acq ref.","L":"Δ vs Tagetik"}
# styles header : reutiliser le style de l'ancien header (row 12)
HSRC={"A":"F","B":"B","C":"C","D":"G","E":"H","F":"I","G":"J","H":"K","I":"L","J":"M","K":"N","L":"O"}
for dc,txt in HEAD.items():
    sc=("B" if dc=="A" else HSRC[dc]); v=raw(sc,12)
    st=v[0] if v else ""
    st=_re.sub(r' t="[^"]*"','',st)  # sera inlineStr
    pil.put_cell("%s14"%dc, st+' t="inlineStr"', '<is><t xml:space="preserve">%s</t></is>'%escape(txt))
# data : old rows 13-26 -> new 15-28, colonnes remappees
COLMAP={"A":"F","B":"B","C":"C","D":"G","E":"H","F":"I","G":"J","H":"K","I":"L","J":"M","K":"N"}  # L traite a part (Delta)
for i in range(14):
    osr=13+i; ntr=15+i
    for dc,sc in COLMAP.items():
        if dc=="A":
            styB=raw("B",osr); vF=raw("F",osr)
            if vF is not None: pil.put_cell("A%d"%ntr, (styB[0] if styB else ""), vF[1])
        else:
            place(sc,osr,"%s%d"%(dc,ntr))
    # L = Delta vs Tagetik = rejoue - ref
    vO=raw("O",osr)
    if vO:
        f='IF($A%d="","",$K%d*$J%d*(SUM(BUD_REF_CAP)/SUMPRODUCT(BUD_REF_CAP,HYP_CAP_RETENU))-$K%d)'%(ntr,ntr,ntr,ntr)
        pil.put_cell("L%d"%ntr, vO[0], "<f>"+escape(f)+"</f>")

# ===== SYNTHESE : decalage +2 (28->30 ... 47->49) =====
place("B",28,"B30")
for c in "DEFGHIJKLMNO": place(c,29,"%s31"%c)   # header synthese
for i in range(14):  # data 30-43 -> 32-45
    osr=30+i; ntr=32+i
    for c in "DEF": place(c,osr,"%s%d"%(c,ntr))  # code/marque/ville (valeurs)
    for c in "GHIJKLM":  # formules internes, shift +2
        f=fml(c,osr)
        if f: putf("%s%d"%(c,ntr), shiftrows(f,2,30,46), (c,osr))
    # N (Rejoue) = ref + Delta par entity ; O (CAC marg) depuis cap D
    putf("N%d"%ntr, 'SUMIFS(Pilotage!$K:$K,Pilotage!$A:$A,$D%d)+SUMIFS(Pilotage!$L:$L,Pilotage!$A:$A,$D%d)'%(ntr,ntr),("N",osr))
    putf("O%d"%ntr, 'SUMIFS(Pilotage!$D:$D,Pilotage!$A:$A,$D%d)'%ntr,("O",osr))
# subtotal 44->46, siege 45->47, groupe 46->48, note 47->49
for c in "DGHIJKLMN":
    f=fml(c,44)
    if f: putf("%s46"%c, shiftrows(f,2,30,46),(c,44))
    else: place(c,44,"%s46"%c)
place("D",45,"D47"); 
f=fml("K",45); 
if f: putf("K47",f,("K",45))
for c in "DGHIJKLMN":
    f=fml(c,46)
    if f: putf("%s48"%c, shiftrows(f,2,30,46),(c,46))
    else: place(c,46,"%s48"%c)
place("B",47,"B49")

# ===== MERGES (retirer anciennes zones, garder titre) =====
pil.set_merges(["B2:H2"])

# ===== NOMS =====
b.retarget_name("HYP_CAP_RETENU","Pilotage!$J$15:$J$28")
b.retarget_name("BUD_REF_CAP","Pilotage!$K$15:$K$28")
import os
b.set_fullcalc(); b.save("_tmp_pil.xlsx"); os.replace("_tmp_pil.xlsx","MOTEUR_adapte.xlsx")
print("OK Pilotage restructure.")
