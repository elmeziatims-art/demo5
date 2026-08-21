#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porte le MOTEUR COMPLET (calculs + zones nommees) sur le Design Tagetik,
par chirurgie (tgk_surgery). Modifie SEULEMENT cad/PIL/ALLOC + workbook.xml.
Feeds (PNL/Moteur/Allocation) jamais touches -> agregations SUMIFS pleine-colonne.
Applique le meme build a DESIGN.xlsm (livrable) et NAV.xlsx (banc d'essai)."""
import sys
from tgk_surgery import Book

def build(src,out):
    b=Book(src)
    cad=b.sheet("cad"); pil=b.sheet("PIL"); alloc=b.sheet("ALLOC")
    # styles reutilises (aucune modif de styles.xml)
    S_NUM=cad.get_style("C9") or cad.get_style("F3")
    S_PCT=cad.get_style("C11")
    S_HDR=cad.get_style("B7")
    S_LBL=cad.get_style("E3")
    VA="VERSION_ACTIVE"; EX='"2027"'

    # ================= ZONES NOMMEES =================
    defs={}
    defs["TEC_PL"]="cad!$F$3"; defs["TEC_EBITDA"]="cad!$F$4"
    LEV={18:"HYP_ACQ_BUD",19:"HYP_BRAND_BUD",20:"HYP_PRICE",21:"HYP_CONV_LEAD",
         22:"HYP_CONV_ADM",23:"HYP_PASSAGE",25:"HYP_INFL_EXT",26:"HYP_SALARY",
         27:"HYP_FTE_PERM",28:"HYP_PRODUCTIVITY",29:"HYP_STRUCT_COST",31:"HYP_FEE"}
    for r,nm in LEV.items():
        defs[nm+"_V01"]="cad!$C$%d"%r; defs[nm+"_V02"]="cad!$D$%d"%r; defs[nm+"_V03"]="cad!$E$%d"%r
    COEF={9:"MBWAY",10:"ISCOM",11:"IPAC",12:"PIGIER",13:"TUNON"}
    for r,m in COEF.items(): defs["HYP_PRICE_COEF_"+m]="cad!$K$%d"%r
    defs["SCENARIO_ACTIF"]="cad!$H$3"; defs["VERSION_ACTIVE"]="cad!$N$1"
    defs["HYP_CAP_RETENU"]="PIL!$M$13:$M$26"
    defs["ALLOC_BRAND_CAMP"]="ALLOC!$C$5"; defs["ALLOC_CAMP_CLASS"]="ALLOC!$C$6"; defs["ALLOC_GRP_HOLDING"]="ALLOC!$C$7"
    b.add_names(defs)

    # ================= cad : selecteur + version + ACTIF + reconciliation =================
    cad.set_text("G3","Scenario actif :",S_LBL)
    cad.set_text("H3","Cadrage",S_NUM)
    cad.set_formula("N1",'IF(H3="Optimiste","V02",IF(H3="Prudent","V03","V01"))')
    # colonne ACTIF (F) des leviers
    for r in list(range(18,24))+list(range(25,30))+[31]:
        cad.set_formula("F%d"%r,'IF($H$3="Optimiste",D%d,IF($H$3="Prudent",E%d,C%d))'%(r,r,r),S_NUM)
    # briques SUMIFS
    def ca(ent=None):
        f='SUMIFS(PNL!$G:$G,PNL!$B:$B,"7*",PNL!$D:$D,%s,PNL!$C:$C,%s'%(VA,EX)
        if ent: f+=',PNL!$A:$A,%s'%ent
        return f+')'
    def charges(cls,ent=None):
        f='SUMIFS(PNL!$G:$G,PNL!$B:$B,"%s",PNL!$D:$D,%s,PNL!$C:$C,%s'%(cls,VA,EX)
        if ent: f+=',PNL!$A:$A,%s'%ent
        return f+')'
    def ebitda(ent=None):  # CA - (charges6 - 6811)
        return "%s-%s+%s"%(ca(ent),charges("6*",ent),charges("6811",ent))
    def eff(ent=None):
        f='SUMIFS(Moteur!$K:$K,Moteur!$B:$B,%s,Moteur!$I:$I,%s'%(VA,EX)
        if ent: f+=',Moteur!$D:$D,%s'%ent
        return f+')'
    # Cible (D)
    cad.set_formula("D9","C9*(1+F3)",S_NUM)
    cad.set_formula("D10","D9*F4",S_NUM)
    cad.set_formula("D11","IFERROR(D10/D9,0)",S_PCT)
    # Construit (E)
    cad.set_formula("E9",ca(),S_NUM)
    cad.set_formula("E10",ebitda(),S_NUM)
    cad.set_formula("E11","IFERROR(E10/E9,0)",S_PCT)
    cad.set_formula("E12",eff(),S_NUM)
    # Ecart (F) et Ecart% (G)
    cad.set_formula("F9","E9-D9",S_NUM); cad.set_formula("G9","IFERROR(F9/D9,0)",S_PCT)
    cad.set_formula("F10","E10-D10",S_NUM); cad.set_formula("G10","IFERROR(F10/D10,0)",S_PCT)
    cad.set_formula("F11","E11-D11",S_PCT)
    cad.set_formula("F12","E12-C12",S_NUM); cad.set_formula("G12","IFERROR(F12/C12,0)",S_PCT)

    # ================= PIL : KPI + synthese campus + rejoue =================
    # KPI (valeurs sous les libelles ligne 5 -> ligne 6)
    pil.set_formula("B6",ca(),S_NUM)
    pil.set_formula("H6",ebitda(),S_NUM)
    pil.set_formula("K6","IFERROR(H6/B6,0)",S_PCT)
    pil.set_formula("N6",eff(),S_NUM)
    ca2026='SUMIFS(PNL!$G:$G,PNL!$B:$B,"7*",PNL!$D:$D,"ACT",PNL!$C:$C,"2026")'
    pil.set_formula("Q6","IFERROR(B6/%s-1,0)"%ca2026,S_PCT)
    # synthese par campus (rows 31-44, cap table entites en F13:F26)
    pil.set_text("B30","Marque",S_HDR); pil.set_text("C30","Ville",S_HDR); pil.set_text("D30","Entity",S_HDR)
    pil.set_text("E30","CA 2027",S_HDR); pil.set_text("F30","EBITDA (avant siege)",S_HDR)
    pil.set_text("G30","Marge %",S_HDR); pil.set_text("H30","Effectif",S_HDR)
    for j in range(14):
        cr=13+j; rr=31+j; ent="$D%d"%rr
        pil.set_formula("B%d"%rr,"B%d"%cr); pil.set_formula("C%d"%rr,"C%d"%cr); pil.set_formula("D%d"%rr,"F%d"%cr)
        pil.set_formula("E%d"%rr,ca(ent),S_NUM)
        pil.set_formula("F%d"%rr,ebitda(ent),S_NUM)
        pil.set_formula("G%d"%rr,"IFERROR(F%d/E%d,0)"%(rr,rr),S_PCT)
        pil.set_formula("H%d"%rr,eff(ent),S_NUM)
    # rejoue (col O du cap, somme groupe constante)
    pil.set_text("O12","Budget acq rejoue",S_HDR)
    for r in range(13,27):
        pil.set_formula("O%d"%r,"IFERROR(M%d*N%d/SUMPRODUCT($M$13:$M$26,$N$13:$N$26)*SUM($N$13:$N$26),0)"%(r,r),S_NUM)

    # ================= ALLOC : rollup marque (2026, cout complet) =================
    alloc.set_text("B10","Marque",S_HDR); alloc.set_text("C10","CA",S_HDR)
    alloc.set_text("D10","Cout complet",S_HDR); alloc.set_text("E10","Marge complete",S_HDR); alloc.set_text("F10","Marge %",S_HDR)
    MARQS=["MBWAY","ISCOM","IPAC","PIGIER","TUNON"]
    for i,mq in enumerate(MARQS):
        rr=11+i
        alloc.set_text("B%d"%rr,mq)
        alloc.set_formula("C%d"%rr,'SUMIFS(Allocation!$K:$K,Allocation!$E:$E,"%s",Allocation!$C:$C,"2026")'%mq,S_NUM)
        alloc.set_formula("D%d"%rr,'SUMIFS(Allocation!$S:$S,Allocation!$E:$E,"%s",Allocation!$C:$C,"2026")'%mq,S_NUM)
        alloc.set_formula("E%d"%rr,'SUMIFS(Allocation!$T:$T,Allocation!$E:$E,"%s",Allocation!$C:$C,"2026")'%mq,S_NUM)
        alloc.set_formula("F%d"%rr,"IFERROR(E%d/C%d,0)"%(rr,rr),S_PCT)
    alloc.set_text("B16","TOTAL",S_HDR)
    alloc.set_formula("C16","SUM(C11:C15)",S_NUM); alloc.set_formula("D16","SUM(D11:D15)",S_NUM)
    alloc.set_formula("E16","SUM(E11:E15)",S_NUM); alloc.set_formula("F16","IFERROR(E16/C16,0)",S_PCT)

    b.set_fullcalc()
    b.save(out)
    return len(defs)

if __name__=="__main__":
    n=build("DESIGN.xlsm","DESIGN_ENGINE.xlsm")
    build("NAV.xlsx","NAV_ENGINE.xlsx")
    print("OK moteur porte. zones nommees:",n)
