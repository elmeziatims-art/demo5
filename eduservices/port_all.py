#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rend le DESIGN identique au prototype : AJOUTE tous les onglets manquants
(_CALC_MOTEUR/_CALC_PNL/_CALC_ALLOC, 3_Allocation, Pilotage, 00_Cartographie)
+ colonnes live des feeds, sans deplacer une ligne/colonne existante ni toucher
aux briques Tagetik. Noms repointes sur le cad du DESIGN. Schemas feeds identiques."""
import warnings;warnings.filterwarnings("ignore")
import openpyxl
from openpyxl.utils import get_column_letter as GCL
from tgk_surgery import Book

PROTO="CAD_SAAD_LIVE.xlsx"
P=openpyxl.load_workbook(PROTO)
ADD_TABS=["_CALC_MOTEUR","_CALC_PNL","_CALC_ALLOC","3_Allocation","Pilotage","00_Cartographie"]
FEEDS={"Socle":29,"Campagne":14,"Moteur":13,"Compta":6,"PNL":9,"Allocation":20}

def put(sh,ref,v):
    if isinstance(v,str) and v.startswith("="): sh.set_formula(ref,v[1:])
    elif isinstance(v,str): sh.set_text(ref,v)
    elif isinstance(v,bool): sh.set_number(ref,1 if v else 0)
    else: sh.set_number(ref,v)

def build(src,out):
    b=Book(src)
    # ---- 1) zones nommees repointees sur le cad du DESIGN ----
    d={}
    LEV={"ACQ_BUD":18,"BRAND_BUD":19,"PRICE":20,"CONV_LEAD":21,"CONV_ADM":22,"PASSAGE":23,
         "INFL_EXT":25,"SALARY":26,"FTE_PERM":27,"PRODUCTIVITY":28,"STRUCT_COST":29,"FEE":31}
    for p,r in LEV.items():
        d["HYP_%s_V01"%p]="cad!$C$%d"%r; d["HYP_%s_V02"%p]="cad!$D$%d"%r; d["HYP_%s_V03"%p]="cad!$E$%d"%r
    for m,r in {"MBWAY":9,"ISCOM":10,"IPAC":11,"PIGIER":12,"TUNON":13}.items():
        d["HYP_PRICE_COEF_%s"%m]="cad!$K$%d"%r
    d["TEC_PL"]="cad!$F$3"; d["TEC_EBITDA"]="cad!$F$4"
    d["SCENARIO_ACTIF"]="cad!$H$3"; d["SCENARIO_CODE"]="cad!$N$1"
    d["ALLOC_GRP_BRAND"]="'3_Allocation'!$C$5"; d["ALLOC_GRP_MARQUE"]="'3_Allocation'!$C$6"
    d["ALLOC_BRAND_CAMP"]="'3_Allocation'!$C$7"; d["ALLOC_CAMP_CLASS"]="'3_Allocation'!$C$8"
    d["HYP_CAP_RETENU"]="Pilotage!$M$13:$M$26"; d["BUD_REF_CAP"]="Pilotage!$N$13:$N$26"
    b.add_names(d)
    # ---- 2) cellules de pilotage scenario dans le cad du DESIGN (additif) ----
    cad=b.sheet("cad")
    cad.set_text("G3","Scenario actif :"); cad.set_text("H3","Cadrage")
    cad.set_formula("N1",'IF(H3="Optimiste","V02",IF(H3="Prudent","V03","V01"))')
    # ---- 3) onglets manquants, transplantes fidelement ----
    for s in ADD_TABS:
        ws=P[s]; sh=b.add_sheet(s)
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None: put(sh,c.coordinate,c.value)
        for rr,dim in ws.row_dimensions.items():
            if dim.outline_level: sh.set_row_outline(rr,dim.outline_level,bool(dim.hidden))
    # ---- 4) colonnes LIVE des feeds (= colonnes contenant des formules dans le proto) ----
    for feed in FEEDS:
        pws=P[feed]; fsh=b.sheet(feed)
        livecols=set()
        for r in range(2,pws.max_row+1):
            for c in range(1,pws.max_column+1):
                v=pws.cell(r,c).value
                if isinstance(v,str) and v.startswith("="): livecols.add(c)
        for c in sorted(livecols):
            h=pws.cell(1,c).value
            if h is not None: put(fsh,"%s1"%GCL(c),h)
            for r in range(2,pws.max_row+1):
                v=pws.cell(r,c).value
                if v is not None: put(fsh,"%s%d"%(GCL(c),r),v)
    b.set_fullcalc(); b.save(out)
    return len(d),livecols

n,_=build("DESIGN.xlsm","DESIGN_FULL.xlsm")
build("NAV.xlsx","NAV_FULL.xlsx")
print("OK. zones nommees:",n)
