#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restructure Pilotage (v2): ligne1 vide; cap titre B12 (13 vide), header L14,
data 15-28, code en A. Synthese titre B31 (32 vide), header 33, data 34-47,
colonnes decalees D-O -> A-L (code campus en A). Refs cap bornees 15-28."""
from tgk_surgery import Book
import re as _re
from xml.sax.saxutils import unescape,escape
b=Book("MOTEUR_adapte.xlsx"); pil=b.sheet("Pilotage"); G=pil.get_cell
cap={}
for r in range(1,52):
    for c in "ABCDEFGHIJKLMNO":
        v=G("%s%d"%(c,r))
        if v is not None: cap[(c,r)]=v
for r in range(1,52):
    for c in "ABCDEFGHIJKLMNO": pil.clear("%s%d"%(c,r))
def raw(sc,sr): return cap.get((sc,sr))
def place(sc,sr,dst,content=None):
    v=raw(sc,sr)
    if v is None: return
    pil.put_cell(dst,v[0], v[1] if content is None else content)
def fml(sc,sr):
    v=raw(sc,sr)
    if not v: return None
    m=_re.search(r'<f>(.*?)</f>',v[1],_re.S) if isinstance(v[1],str) else None
    return unescape(m.group(1)) if m else None
def putf(dst,formula,style_from):
    v=raw(*style_from); pil.put_cell(dst, v[0] if v else "", "<f>"+escape(formula)+"</f>")
# remap synthese : refs internes Pilotage non-qualifiees col D-O -> -3, lignes 30-47 -> +4
def remap_s(f):
    return _re.sub(r'(^|[^A-Za-z0-9!$])(\$?)([D-O])(\$?)(\d+)',
        lambda m:m.group(1)+m.group(2)+chr(ord(m.group(3))-3)+m.group(4)+(str(int(m.group(5))+4) if 30<=int(m.group(5))<=47 else m.group(5)), f)

# ===== TOP (ligne 1 vide) =====
place("A",1,"A2"); place("A",2,"A3"); place("A",3,"A4"); place("B",1,"B2"); place("B",3,"B4")
for c in "BEHKN": place(c,4,"%s5"%c)
for c,f in {"B":"E50","E":"H50","H":"I50","K":"D50","N":"E50/22544725-1"}.items(): putf("%s6"%c,f,(c,5))

# ===== CAP : titre B12 (13 vide), header L14, data 15-28 =====
place("B",10,"B12")
HEAD={"A":"","B":"Marque","C":"Ville","D":"CAC marginal","E":"Croiss. leads","F":"Intensite mkt",
      "G":"Cap Eff","H":"Cap mom.","I":"Cap pot.","J":"Cap retenu","K":"Budget acq ref.","L":"Δ vs Tagetik"}
HSRC={"A":"B","B":"B","C":"C","D":"G","E":"H","F":"I","G":"J","H":"K","I":"L","J":"M","K":"N","L":"O"}
for dc,txt in HEAD.items():
    v=raw(HSRC[dc],12); st=_re.sub(r' t="[^"]*"','',v[0]) if v else ""
    pil.put_cell("%s14"%dc, st+' t="inlineStr"', '<is><t xml:space="preserve">%s</t></is>'%escape(txt))
COLMAP={"B":"B","C":"C","D":"G","E":"H","F":"I","G":"J","H":"K","I":"L","J":"M","K":"N"}
for i in range(14):
    osr=13+i; ntr=15+i
    styB=raw("B",osr); vF=raw("F",osr)
    if vF is not None: pil.put_cell("A%d"%ntr,(styB[0] if styB else ""),vF[1])   # code -> A (style Marque)
    for dc,sc in COLMAP.items(): place(sc,osr,"%s%d"%(dc,ntr))
    if raw("O",osr):
        f='IF($A%d="","",$K%d*$J%d*(SUM(BUD_REF_CAP)/SUMPRODUCT(BUD_REF_CAP,HYP_CAP_RETENU))-$K%d)'%(ntr,ntr,ntr,ntr)
        pil.put_cell("L%d"%ntr, raw("O",osr)[0], "<f>"+escape(f)+"</f>")

# ===== SYNTHESE : titre B31 (32 vide), header 33, data 34-47, colonnes D-O -> A-L =====
place("B",28,"B31")
HMAP={"A":"D","B":"E","C":"F","D":"G","E":"H","F":"I","G":"J","H":"K","I":"L","J":"M","K":"N","L":"O"}
for dc,sc in HMAP.items(): place(sc,29,"%s33"%dc)     # header
for i in range(14):
    osr=30+i; ntr=34+i
    place("D",osr,"A%d"%ntr); place("E",osr,"B%d"%ntr); place("F",osr,"C%d"%ntr)  # code/marque/ville
    for sc in "GHIJKLM":
        dc=chr(ord(sc)-3); f=fml(sc,osr)
        if f: putf("%s%d"%(dc,ntr), remap_s(f), (sc,osr))
    putf("K%d"%ntr,'SUMIFS(Pilotage!$K$15:$K$28,Pilotage!$A$15:$A$28,$A%d)+SUMIFS(Pilotage!$L$15:$L$28,Pilotage!$A$15:$A$28,$A%d)'%(ntr,ntr),("N",osr))
    putf("L%d"%ntr,'SUMIFS(Pilotage!$D$15:$D$28,Pilotage!$A$15:$A$28,$A%d)'%ntr,("O",osr))
# subtotal 44->48, siege 45->49, groupe 46->50, note 47->51
for sc in "DGHIJKLMN":
    dc=chr(ord(sc)-3); f=fml(sc,44)
    if f: putf("%s48"%dc, remap_s(f),(sc,44))
    else: place(sc,44,"%s48"%dc)
place("D",45,"A49"); 
if fml("K",45): putf("H49",fml("K",45),("K",45))
for sc in "DGHIJKLMN":
    dc=chr(ord(sc)-3); f=fml(sc,46)
    if f: putf("%s50"%dc, remap_s(f),(sc,46))
    else: place(sc,46,"%s50"%dc)
place("B",47,"B51")

pil.set_merges(["B2:H2"])
b.retarget_name("HYP_CAP_RETENU","Pilotage!$J$15:$J$28")
b.retarget_name("BUD_REF_CAP","Pilotage!$K$15:$K$28")
import os
b.set_fullcalc(); b.save("_tmp_pil.xlsx"); os.replace("_tmp_pil.xlsx","MOTEUR_adapte.xlsx")
print("OK Pilotage v2.")
