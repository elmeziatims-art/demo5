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

    # ================= ALLOC : CASCADE VIVANTE JUSQU'A LA CLASSE (comme le prototype, adapte au feed) =================
    import json
    HIER=json.load(open("_hier.json"))
    VILLE={"MBWAY_PAR":"Paris","MBWAY_LYO":"Lyon","MBWAY_NAN":"Nantes","MBWAY_BOR":"Bordeaux",
     "ISCOM_PAR":"Paris","ISCOM_LIL":"Lille","ISCOM_TLS":"Toulouse","IPAC_NAN":"Nantes","IPAC_REN":"Rennes",
     "IPAC_MTP":"Montpellier","PIGIER_LYO":"Lyon","PIGIER_BOR":"Bordeaux","TUNON_PAR":"Paris","TUNON_LYO":"Lyon"}
    LIB={"MBWAY":"MBway","ISCOM":"ISCOM","IPAC":"Ipac","PIGIER":"Pigier","TUNON":"Tunon"}
    # --- resolveurs : label FR (N1..N3) + code REV_CA/VOL_EFF/VOL_CLASS (P1..P3) + siege total (P4) ---
    def vlabel(kname,dflt): return 'IFERROR(INDEX(ALLOC!$C:$C,MATCH("%s",ALLOC!$B:$B,0)),"%s")'%(kname,dflt)
    def code(v): return "IF(%s=\"Chiffre d'affaires\",\"REV_CA\",IF(%s=\"Nombre de classes\",\"VOL_CLASS\",\"VOL_EFF\"))"%(v,v)
    alloc.set_formula("N1",vlabel("ALLOC_GRP_HOLDING","Chiffre d'affaires"))
    alloc.set_formula("N2",vlabel("ALLOC_BRAND_CAMP","Effectif"))
    alloc.set_formula("N3",vlabel("ALLOC_CAMP_CLASS","Nombre de classes"))
    alloc.set_formula("P1",code("$N$1")); alloc.set_formula("P2",code("$N$2")); alloc.set_formula("P3",code("$N$3"))
    alloc.set_formula("P4",'SUMIFS(Allocation!$P:$P,Allocation!$C:$C,"2026")')
    b.add_names({"KC_HOLDING":"ALLOC!$P$1","KC_BRANDCAMP":"ALLOC!$P$2","KC_CAMPCLASS":"ALLOC!$P$3","SIEGE_TOTAL":"ALLOC!$P$4"})

    # --- onglet _CALC_ALLOC : moteur ligne a ligne (aligne au feed Allocation, 200 lignes) ---
    NROWS=200
    ca=b.add_sheet("_CALC_ALLOC")
    HDRC=["EX","ENT","MARQ","EFF","CLS","CA","DIRECT","SIEGEfeed","M_EFF","M_CLS","M_CA",
          "E_EFF","E_CLS","E_CA","G_EFF","G_CLS","G_CA","D1M","D1G","D2E","D2M","D3C","D3E","SIEGE_NEW","MARGE_NEW"]
    from openpyxl.utils import get_column_letter as GCL
    for i,h in enumerate(HDRC): ca.set_text(GCL(i+1),h) if False else ca.set_text("%s1"%GCL(i+1),h)
    def A(col,r): return "Allocation!$%s%d"%(col,r)
    def sifm(col,crit): return "SUMIFS(Allocation!$%s:$%s,%s)"%(col,col,crit)
    for r in range(2,NROWS+2):
        g=lambda expr:'IF(OR(Allocation!$D%d="",Allocation!$C%d<>"2026"),"",%s)'%(r,r,expr)
        ca.set_formula("A%d"%r,g('Allocation!$C%d'%r))
        ca.set_formula("B%d"%r,g('Allocation!$D%d'%r))
        ca.set_formula("C%d"%r,g('Allocation!$E%d'%r))
        ca.set_formula("D%d"%r,g('Allocation!$I%d'%r))
        ca.set_formula("E%d"%r,g('Allocation!$J%d'%r))
        ca.set_formula("F%d"%r,g('Allocation!$K%d'%r))
        ca.set_formula("G%d"%r,g('Allocation!$L%d+Allocation!$M%d+Allocation!$N%d+Allocation!$O%d'%(r,r,r,r)))
        ca.set_formula("H%d"%r,g('Allocation!$P%d'%r))
        # sommes hierarchiques par base (filtre 2026)
        mq='$C%d'%r; en='$B%d'%r
        ca.set_formula("I%d"%r,g('SUMIFS(Allocation!$I:$I,Allocation!$E:$E,_CALC_ALLOC!%s,Allocation!$C:$C,"2026")'%mq))
        ca.set_formula("J%d"%r,g('SUMIFS(Allocation!$J:$J,Allocation!$E:$E,_CALC_ALLOC!%s,Allocation!$C:$C,"2026")'%mq))
        ca.set_formula("K%d"%r,g('SUMIFS(Allocation!$K:$K,Allocation!$E:$E,_CALC_ALLOC!%s,Allocation!$C:$C,"2026")'%mq))
        ca.set_formula("L%d"%r,g('SUMIFS(Allocation!$I:$I,Allocation!$D:$D,_CALC_ALLOC!%s,Allocation!$C:$C,"2026")'%en))
        ca.set_formula("M%d"%r,g('SUMIFS(Allocation!$J:$J,Allocation!$D:$D,_CALC_ALLOC!%s,Allocation!$C:$C,"2026")'%en))
        ca.set_formula("N%d"%r,g('SUMIFS(Allocation!$K:$K,Allocation!$D:$D,_CALC_ALLOC!%s,Allocation!$C:$C,"2026")'%en))
        ca.set_formula("O%d"%r,g('SUMIFS(Allocation!$I:$I,Allocation!$C:$C,"2026")'))
        ca.set_formula("P%d"%r,g('SUMIFS(Allocation!$J:$J,Allocation!$C:$C,"2026")'))
        ca.set_formula("Q%d"%r,g('SUMIFS(Allocation!$K:$K,Allocation!$C:$C,"2026")'))
        # parts de cascade selon les codes de cle
        ca.set_formula("R%d"%r,g('IF(KC_HOLDING="REV_CA",K%d,IF(KC_HOLDING="VOL_CLASS",J%d,I%d))'%(r,r,r)))
        ca.set_formula("S%d"%r,g('IF(KC_HOLDING="REV_CA",Q%d,IF(KC_HOLDING="VOL_CLASS",P%d,O%d))'%(r,r,r)))
        ca.set_formula("T%d"%r,g('IF(KC_BRANDCAMP="REV_CA",N%d,IF(KC_BRANDCAMP="VOL_CLASS",M%d,L%d))'%(r,r,r)))
        ca.set_formula("U%d"%r,g('IF(KC_BRANDCAMP="REV_CA",K%d,IF(KC_BRANDCAMP="VOL_CLASS",J%d,I%d))'%(r,r,r)))
        ca.set_formula("V%d"%r,g('IF(KC_CAMPCLASS="REV_CA",F%d,IF(KC_CAMPCLASS="VOL_CLASS",E%d,D%d))'%(r,r,r)))
        ca.set_formula("W%d"%r,g('IF(KC_CAMPCLASS="REV_CA",N%d,IF(KC_CAMPCLASS="VOL_CLASS",M%d,L%d))'%(r,r,r)))
        ca.set_formula("X%d"%r,g('IFERROR(SIEGE_TOTAL*(R%d/S%d)*(T%d/U%d)*(V%d/W%d),0)'%(r,r,r,r,r,r)))
        ca.set_formula("Y%d"%r,g('F%d-G%d-X%d'%(r,r,r)))
    # --- colonnes live sur le feed Allocation (V=siege live, W=marge live) ---
    alloc_feed=b.sheet("Allocation")
    alloc_feed.set_text("V1","COST_SIEGE (live)"); alloc_feed.set_text("W1","MARGE (live)")
    for r in range(2,NROWS+2):
        alloc_feed.set_formula("V%d"%r,'IF(Allocation!$D%d="","",_CALC_ALLOC!X%d)'%(r,r))
        alloc_feed.set_formula("W%d"%r,'IF(Allocation!$D%d="","",_CALC_ALLOC!Y%d)'%(r,r))

    # --- maille marque > campus > classe (outline [+]) lisant les colonnes live ---
    mh=[("B","Effectif"),("C","CA"),("D","Cout direct"),("E","Siege (live)"),("F","Marge (live)"),("G","Marge %")]
    alloc.set_text("A24","Maille fine — deplie chaque marque -> campus -> classe (reagit aux cles)",S_HDR)
    for col,t in mh: alloc.set_text("%s25"%col,t,S_HDR)
    def mrow(rr,crit,ca_):
        alloc.set_formula("B%d"%rr,'SUMIFS(Allocation!$I:$I,Allocation!$C:$C,"2026"%s)'%crit,S_NUM)
        alloc.set_formula("C%d"%rr,'SUMIFS(Allocation!$K:$K,Allocation!$C:$C,"2026"%s)'%crit,S_NUM)
        alloc.set_formula("D%d"%rr,'SUMIFS(Allocation!$S:$S,Allocation!$C:$C,"2026"%s)-SUMIFS(Allocation!$P:$P,Allocation!$C:$C,"2026"%s)'%(crit,crit),S_NUM)
        alloc.set_formula("E%d"%rr,'SUMIFS(Allocation!$V:$V,Allocation!$C:$C,"2026"%s)'%crit,S_NUM)
        alloc.set_formula("F%d"%rr,'SUMIFS(Allocation!$W:$W,Allocation!$C:$C,"2026"%s)'%crit,S_NUM)
        alloc.set_formula("G%d"%rr,"IFERROR(F%d/C%d,0)"%(rr,rr),S_PCT)
    rr=26
    for mq in HIER:
        alloc.set_text("A%d"%rr,LIB[mq],S_HDR); alloc.set_row_outline(rr,0)
        mrow(rr,',Allocation!$E:$E,"%s"'%mq,None); rr+=1
        for ent in HIER[mq]:
            alloc.set_text("A%d"%rr,"   %s  (%s)"%(VILLE[ent],ent)); alloc.set_row_outline(rr,1)
            mrow(rr,',Allocation!$D:$D,"%s"'%ent,None); rr+=1
            for (prog,an,mod) in HIER[mq][ent]:
                alloc.set_text("A%d"%rr,"      %s %s %s"%(prog,an,mod)); alloc.set_row_outline(rr,2)
                crit=',Allocation!$D:$D,"%s",Allocation!$F:$F,"%s",Allocation!$G:$G,"%s",Allocation!$H:$H,"%s"'%(ent,prog,an,mod)
                mrow(rr,crit,None); rr+=1

    b.set_fullcalc()
    b.save(out)
    return len(defs)

if __name__=="__main__":
    n=build("DESIGN.xlsm","DESIGN_ENGINE.xlsm")
    build("NAV.xlsx","NAV_ENGINE.xlsx")
    print("OK moteur porte. zones nommees:",n)
