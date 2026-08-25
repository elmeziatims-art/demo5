#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Perfectionne le design DESIGN_REF en REPRENANT sa charte (couleurs douces par
role) : complete la Reconciliation (Reference/Cible/Construit/Ecart/Ecart% avec
fleches + vert/rouge conditionnel), style saisie creme, valeurs. Chirurgical,
briques Tagetik intactes, aucune fusion. cad d'abord."""
import re
from tgk_surgery import Book
from tgk_style import StyleBank

b=Book("DESIGN_REF.xlsm")
# cles d'allocation -> libelles
for nm,ref in {"ALLOC_GRP_BRAND":"ALLOC!$C$6","ALLOC_GRP_MARQUE":"ALLOC!$C$7",
               "ALLOC_BRAND_CAMP":"ALLOC!$C$8","ALLOC_CAMP_CLASS":"ALLOC!$C$9"}.items():
    b.retarget_name(nm,ref)
b.set_fullcalc()

sb=StyleBank(b.styles_xml())
# ---- palette DU FICHIER ----
BORD="D9D9D9"; NAVY="1F3864"; GREY="3B3B3B"; BLUE="0F5FB0"; GOLD="B8860B"
GREEN="2E7D42"; RED="C0392B"; CREAM="FFF2CC"; GOLDB="E0A800"
def F(sz=11,bold=False,it=False,color=GREY): return sb.font(sz,bold,it,color)
def bord(all=True):
    s=(BORD,"thin"); return sb.border(top=s,bottom=s,left=s,right=s) if all else 0
BI=sb.border(top=(BORD,"thin"),bottom=(BORD,"thin"),left=(BORD,"thin"),right=(BORD,"thin"))
# formats
NF_EUR=sb.numfmt('#,##0" €";-#,##0" €";"–"')
NF_PCT=sb.numfmt('0.0%;-0.0%;"–"')
NF_EFF=sb.numfmt('#,##0;-#,##0;"–"')
NF_ECE=sb.numfmt('"▲ "#,##0" €";"▼ "#,##0" €";"–"')
NF_ECP=sb.numfmt('"▲ "0.0%;"▼ "0.0%;"–"')
NF_COE=sb.numfmt('0.00')
# styles valeurs (base blanche, couleur = texte selon role)
XREF =sb.xf(font=F(11,color=GREY),border=BI,numfmt=NF_EUR,halign="right",valign="center")
XREFe=sb.xf(font=F(11,color=GREY),border=BI,numfmt=NF_EFF,halign="right",valign="center")
XREFp=sb.xf(font=F(11,color=GREY),border=BI,numfmt=NF_PCT,halign="right",valign="center")
XCIB =sb.xf(font=F(11,color=GOLD),border=BI,numfmt=NF_EUR,halign="right",valign="center")
XCIBp=sb.xf(font=F(11,color=GOLD),border=BI,numfmt=NF_PCT,halign="right",valign="center")
XCON =sb.xf(font=F(11,True,color=BLUE),border=BI,numfmt=NF_EUR,halign="right",valign="center")
XCONe=sb.xf(font=F(11,True,color=BLUE),border=BI,numfmt=NF_EFF,halign="right",valign="center")
XCONp=sb.xf(font=F(11,True,color=BLUE),border=BI,numfmt=NF_PCT,halign="right",valign="center")
XECE =sb.xf(font=F(11,color=GREY),border=BI,numfmt=NF_ECE,halign="right",valign="center")
XECP =sb.xf(font=F(11,color=GREY),border=BI,numfmt=NF_ECP,halign="right",valign="center")
XECPpts=sb.xf(font=F(11,color=GREY),border=BI,numfmt=sb.numfmt('"▲ "0.0" pt";"▼ "0.0" pt";"–"'),halign="right",valign="center")
XEMPTY=sb.xf(border=BI)
# saisie creme
XSAI_p=sb.xf(font=sb.font(11,True,False,"1B5FA6"),fill=sb.fill(CREAM),border=sb.border(top=(GOLDB,"thin"),bottom=(GOLDB,"thin"),left=(GOLDB,"thin"),right=(GOLDB,"thin")),numfmt=NF_PCT,halign="center",valign="center")
XSAI_e=sb.xf(font=sb.font(11,True,False,"1B5FA6"),fill=sb.fill(CREAM),border=sb.border(top=(GOLDB,"thin"),bottom=(GOLDB,"thin"),left=(GOLDB,"thin"),right=(GOLDB,"thin")),numfmt=NF_EUR,halign="center",valign="center")
XSAI_c=sb.xf(font=sb.font(11,True,False,"1B5FA6"),fill=sb.fill(CREAM),border=sb.border(top=(GOLDB,"thin"),bottom=(GOLDB,"thin"),left=(GOLDB,"thin"),right=(GOLDB,"thin")),numfmt=NF_COE,halign="center",valign="center")
# CF differentiels
DXG=sb.dxf(color=GREEN,bold=True); DXR=sb.dxf(color=RED,bold=True)

cad=b.sheet("cad")
def SF(ref,f,s): cad.set_formula(ref,f,s=s)
def SN(ref,v,s): cad.set_number(ref,v,s=s)

# ---- cibles (saisie creme) ----
SN("F5",0.05,XSAI_p); SN("F6",0.15,XSAI_p)
# ---- RECONCILIATION ----
# CA (12)
SN("C12",22544725,XREF); SF("D12","C12*(1+TEC_PL)",XCIB)
SF("E12","SUMIFS(Moteur!$R:$R,Moteur!$B:$B,SCENARIO_CODE)",XCON)
SF("F12","E12-D12",XECE); SF("G12","IFERROR(E12/D12-1,0)",XECP)
# EBITDA (13)
SN("C13",3291530,XREF); SF("D13","D12*TEC_EBITDA",XCIB)
SF("E13",'SUMIFS(_CALC_PNL!$T:$T,_CALC_PNL!$D:$D,SCENARIO_CODE,_CALC_PNL!$C:$C,"2027")',XCON)
SF("F13","E13-D13",XECE); SF("G13","IFERROR(E13/D13-1,0)",XECP)
# Marge % (14)
SF("C14","IFERROR(C13/C12,0)",XREFp); SF("D14","TEC_EBITDA",XCIBp)
SF("E14","IFERROR(E13/E12,0)",XCONp); SF("F14","E14-D14",XECPpts); cad.put_cell("G14",' s="%d"'%XEMPTY,None)
# Effectif (15) : ecart vs reference (pas de cible)
SN("C15",3036,XREFe); cad.put_cell("D15",' s="%d"'%XEMPTY,None)
SF("E15","SUMIFS(Moteur!$P:$P,Moteur!$B:$B,SCENARIO_CODE)",XCONe)
SF("F15","E15-C15",sb.xf(font=F(11,color=GREY),border=BI,numfmt=sb.numfmt('"▲ "#,##0;"▼ "#,##0;"–"'),halign="right",valign="center"))
SF("G15","IFERROR(E15/C15-1,0)",XECP)
# CF vert/rouge sur les ecarts
cad.set_cf('<conditionalFormatting sqref="F12:G15">'
 '<cfRule type="cellIs" dxfId="%d" priority="1" operator="greaterThan"><formula>0</formula></cfRule>'
 '<cfRule type="cellIs" dxfId="%d" priority="2" operator="lessThan"><formula>0</formula></cfRule>'
 '</conditionalFormatting>'%(DXG,DXR))
# ---- coeff prix (saisie creme) ----
for i,co in enumerate([1.2,1.15,0.95,0.9,1.05]): SN("J%d"%(12+i),co,XSAI_c)
# ---- leviers (saisie creme) ----
cad.rowattrs[22]=' hidden="1"'; cad.rows.setdefault(22,{})
LEV={23:(0.08,0.15,-0.05),24:(0.1,0.2,-0.05),25:(0.002855,0.035,0.02),26:(0.01,0.03,0),
     27:(0.01,0.025,0),28:(0.005,0.015,-0.01),32:(0.02,0.015,0.03),33:(0.025,0.02,0.03),
     34:(0.04,0.03,0.05),35:(0.018697,0.03,0),36:(0,-0.03,0.04),39:(90,90,90)}
XACT =sb.xf(font=sb.font(11,True,False,NAVY),fill=sb.fill("EAF7EF"),border=BI,numfmt=NF_PCT,halign="center",valign="center")
XACTe=sb.xf(font=sb.font(11,True,False,NAVY),fill=sb.fill("EAF7EF"),border=BI,numfmt=NF_EUR,halign="center",valign="center")
def RS(ref,s):
    c=cad.get_cell(ref)
    if c is None: cad.put_cell(ref,' s="%d"'%s,None); return
    at,ct=c; at=re.sub(r'\ss="\d+"','',at); cad.put_cell(ref,' s="%d"'%s+at,ct)
for r,(v1,v2,v3) in LEV.items():
    xs=XSAI_e if r==39 else XSAI_p
    SN("C%d"%r,v1,xs); SN("D%d"%r,v2,xs); SN("E%d"%r,v3,xs)
    RS("F%d"%r, XACTe if r==39 else XACT)   # ACTIF (scenario) formate

b.set_styles(sb.render())
b.save("DESIGN_REF_v2.xlsm")
print("OK -> DESIGN_REF_v2.xlsm (cad)")
