#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST3b (design Tagetik) : (1) repointe les cles d'allocation sur C6-C9,
(2) complete la Reconciliation (Reference/Cible/Construit/Ecart/Ecart%) + cibles +
coeff + leviers, (3) applique la charte graphique a cad. 100% chirurgical :
seuls sheetData de cad + styles.xml + workbook.xml changent ; briques Tagetik
(customProperty/customXml/webextensions/_TGK_HIDDEN) intactes."""
import re
from tgk_surgery import Book
from tgk_style import StyleBank

b=Book("TEST3b.xlsm")

# ===== 1) cles d'allocation -> libelles C6-C9 =====
for nm,ref in {"ALLOC_GRP_BRAND":"ALLOC!$C$6","ALLOC_GRP_MARQUE":"ALLOC!$C$7",
               "ALLOC_BRAND_CAMP":"ALLOC!$C$8","ALLOC_CAMP_CLASS":"ALLOC!$C$9"}.items():
    b.retarget_name(nm,ref)
b.set_fullcalc()

# ===== 2) styles (charte) =====
sb=StyleBank(b.styles_xml())
NF_EUR=sb.numfmt('#,##0\\ €;(#,##0\\ €);-')
NF_PCT=sb.numfmt('0.0\\ %')
NF_ECE=sb.numfmt('+#,##0\\ €;-#,##0\\ €;-')
NF_ECA=sb.numfmt('+#,##0;-#,##0;-')
NF_EFF=sb.numfmt('#,##0;(#,##0);-')
NF_COE=sb.numfmt('0.00')
BI =sb.border(top=("CBD5DA","thin"),bottom=("CBD5DA","thin"),left=("CBD5DA","thin"),right=("CBD5DA","thin"))
BSA=sb.border(top=("4A6FA5","thin"),bottom=("4A6FA5","thin"),left=("4A6FA5","thin"),right=("4A6FA5","thin"))
def F(sz=10,b_=False,i=False,c="1C2733"): return sb.font(sz,b_,i,c)
XF_TITRE=sb.xf(font=F(14,True,c="FFFFFF"),fill=sb.fill("1C2733"),halign="centerContinuous",valign="center")
XF_SOUS =sb.xf(font=F(9,i=True,c="5B6770"),halign="centerContinuous",valign="center")
XF_SECT =sb.xf(font=F(10,True,c="14586F"),fill=sb.fill("EAF0F3"),border=sb.border(top=("1C2733","medium")),halign="left",valign="center",indent=1)
XF_ENT  =sb.xf(font=F(10,True,c="FFFFFF"),fill=sb.fill("14586F"),border=sb.border(bottom=("1C2733","medium")),halign="center",valign="center",wrap=True)
XF_LBL  =sb.xf(font=F(10),halign="left",valign="center")
XF_LBOLD=sb.xf(font=F(10,True),halign="left",valign="center")
XF_LBR  =sb.xf(font=F(10,True),halign="right",valign="center")   # label a droite
XF_NOTEC=sb.xf(font=F(9,i=True,c="5B6770"),halign="center",valign="center")
XF_INDIC=sb.xf(font=F(10,True),border=BI,halign="left",valign="center")     # libelle indicateur
XF_LBLB =sb.xf(font=F(10),border=BI,halign="left",valign="center")          # libelle bordé
XF_LWRAP=sb.xf(font=F(10),border=BI,halign="left",valign="center",wrap=True)# libelle levier
# valeurs
XF_EUR_I=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_EUR,halign="right",valign="center")
XF_EUR_L=sb.xf(font=F(10),border=BI,numfmt=NF_EUR,halign="right",valign="center")
XF_EUR_K=sb.xf(font=F(10,c="1B6B4F"),border=BI,numfmt=NF_EUR,halign="right",valign="center")
XF_ECE  =sb.xf(font=F(10),border=BI,numfmt=NF_ECE,halign="right",valign="center")
XF_PCT  =sb.xf(font=F(10),border=BI,numfmt=NF_PCT,halign="right",valign="center")
XF_PCT_I=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_PCT,halign="right",valign="center")
XF_PCT_K=sb.xf(font=F(10,c="1B6B4F"),border=BI,numfmt=NF_PCT,halign="right",valign="center")
XF_EFF_I=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_EFF,halign="right",valign="center")
XF_EFF_K=sb.xf(font=F(10,c="1B6B4F"),border=BI,numfmt=NF_EFF,halign="right",valign="center")
XF_ECA  =sb.xf(font=F(10),border=BI,numfmt=NF_ECA,halign="right",valign="center")
XF_COE_I=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_COE,halign="center",valign="center")
XF_EMPTY=sb.xf(border=BI)

cad=b.sheet("cad")
def restyle(ref,s):
    c=cad.get_cell(ref)
    if c is None: cad.put_cell(ref,' s="%d"'%s,None); return
    at,ct=c
    at=re.sub(r'\ss="\d+"','',at); at=' s="%d"'%s+at
    cad.put_cell(ref,at,ct)
def blank(ref,s): cad.put_cell(ref,' s="%d"'%s,None)

# ---- bandeau + sous-titre ----
cad.set_text("B2","POSTE DE COMMANDE CFO   ·   Cadrage CA & EBITDA 2027",s=XF_TITRE)
for col in "CDEFGHIJ": blank(col+"2",XF_TITRE)
cad.set_text("B3","EDUSERVICES GROUP  ·  MBway · ISCOM · Ipac · Pigier · Tunon  ·  Simulation budgétaire  ·  Montants en €",s=XF_SOUS)
for col in "CDEFGHIJ": blank(col+"3",XF_SOUS)
# ---- cibles ----
cad.set_text("B5","Scénario actif",s=XF_LBOLD); restyle("C5",sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,halign="center",valign="center"))
cad.set_text("E5","Croissance CA cible",s=XF_LBR); cad.set_number("F5",0.05,s=XF_PCT_I)
cad.set_text("E6","Marge EBITDA cible",s=XF_LBR);  cad.set_number("F6",0.15,s=XF_PCT_I)
# ---- sections ligne 8 ----
cad.set_text("B8","1 ·  Réconciliation   —   Référence · Cible · Construit (scénario actif)",s=XF_SECT)
for col in "CDEFG": blank(col+"8",XF_SECT)
cad.set_text("I8","Coeff prix / marque",s=XF_SECT); blank("J8",XF_SECT)
# ---- entetes ligne 10 ----
for col,txt in [("B","Indicateur"),("C","Référence"),("D","Cible"),("E","Construit"),("F","Écart"),("G","Écart %")]:
    cad.set_text(col+"10",txt,s=XF_ENT)
cad.set_text("I10","Marque",s=XF_ENT); cad.set_text("J10","Coeff prix",s=XF_ENT)
# ---- captions annee ----
cad.set_text("C11","2026",s=XF_NOTEC); cad.set_text("D11","2027",s=XF_NOTEC); cad.set_text("E11","2027",s=XF_NOTEC)
# ---- RECONCILIATION data 12-15 ----
restyle("B12",XF_INDIC); restyle("B13",XF_INDIC); restyle("B14",XF_INDIC); restyle("B15",XF_INDIC)
# CA (12)
cad.set_number("C12",22544725,s=XF_EUR_I)
cad.set_formula("D12","C12*(1+TEC_PL)",s=XF_EUR_L)
cad.set_formula("E12","SUMIFS(Moteur!$R:$R,Moteur!$B:$B,SCENARIO_CODE)",s=XF_EUR_K)
cad.set_formula("F12","E12-D12",s=XF_ECE); cad.set_formula("G12","IFERROR(E12/D12-1,0)",s=XF_PCT)
# EBITDA (13)
cad.set_number("C13",3291530,s=XF_EUR_I)
cad.set_formula("D13","D12*TEC_EBITDA",s=XF_EUR_L)
cad.set_formula("E13",'SUMIFS(_CALC_PNL!$T:$T,_CALC_PNL!$D:$D,SCENARIO_CODE,_CALC_PNL!$C:$C,"2027")',s=XF_EUR_K)
cad.set_formula("F13","E13-D13",s=XF_ECE); cad.set_formula("G13","IFERROR(E13/D13-1,0)",s=XF_PCT)
# Marge % (14)
cad.set_formula("C14","IFERROR(C13/C12,0)",s=XF_PCT)
cad.set_formula("D14","TEC_EBITDA",s=XF_PCT)
cad.set_formula("E14","IFERROR(E13/E12,0)",s=XF_PCT_K)
cad.set_formula("F14","E14-D14",s=XF_PCT); blank("G14",XF_PCT)
# Effectif (15)
cad.set_number("C15",3036,s=XF_EFF_I)
blank("D15",XF_EMPTY)
cad.set_formula("E15","SUMIFS(Moteur!$P:$P,Moteur!$B:$B,SCENARIO_CODE)",s=XF_EFF_K)
blank("F15",XF_EMPTY); blank("G15",XF_EMPTY)
# ---- coeff prix 12-16 ----
for i,co in enumerate([1.2,1.15,0.95,0.9,1.05]):
    r=12+i; restyle("I%d"%r,XF_LBLB); cad.set_number("J%d"%r,co,s=XF_COE_I)
# ---- LEVIERS ----
cad.set_text("B19","2 ·  Leviers de CROISSANCE / REVENUS",s=XF_SECT)
for col in "CDEF": blank(col+"19",XF_SECT)
cad.set_text("B21","Paramètre",s=XF_ENT); restyle("C21",XF_ENT); restyle("D21",XF_ENT); restyle("E21",XF_ENT)
cad.set_text("F21","ACTIF (scénario)",s=XF_ENT)
cad.rowattrs[22]=' hidden="1"'; cad.rows.setdefault(22,{})
LEV={23:(0.08,0.15,-0.05),24:(0.1,0.2,-0.05),25:(0.002855,0.035,0.02),26:(0.01,0.03,0),
     27:(0.01,0.025,0),28:(0.005,0.015,-0.01),32:(0.02,0.015,0.03),33:(0.025,0.02,0.03),
     34:(0.04,0.03,0.05),35:(0.018697,0.03,0),36:(0,-0.03,0.04),39:(90,90,90)}
for r,(v1,v2,v3) in LEV.items():
    eur=(r==39)
    restyle("B%d"%r,XF_LWRAP)
    xin=XF_EUR_I if eur else XF_PCT_I; xloc=XF_EUR_L if eur else XF_PCT
    cad.set_number("C%d"%r,v1,s=xin); cad.set_number("D%d"%r,v2,s=xin); cad.set_number("E%d"%r,v3,s=xin)
    restyle("F%d"%r,xloc)
cad.set_text("B30","3 ·  Leviers de COÛTS",s=XF_SECT)
for col in "CDEF": blank(col+"30",XF_SECT)
cad.set_text("B38","4 ·  Constante  —  frais de dossier",s=XF_SECT)
for col in "CDEF": blank(col+"38",XF_SECT)

# ---- largeurs de colonnes ----
cad.set_cols('<cols>'
 '<col min="1" max="1" width="2.6" customWidth="1"/>'
 '<col min="2" max="2" width="40" customWidth="1"/>'
 '<col min="3" max="5" width="15.5" customWidth="1"/>'
 '<col min="6" max="6" width="14" customWidth="1"/>'
 '<col min="7" max="7" width="11" customWidth="1"/>'
 '<col min="8" max="8" width="3" customWidth="1"/>'
 '<col min="9" max="9" width="23" customWidth="1"/>'
 '<col min="10" max="10" width="12" customWidth="1"/></cols>')
# ---- hauteurs de lignes ----
for r,h in {1:6,2:30,3:16,4:6,7:6,8:20,9:6,10:28,11:13,17:6,18:6,20:6,21:28,29:6,31:6,37:6}.items():
    cad.rowattrs[r]=' ht="%d" customHeight="1"'%h; cad.rows.setdefault(r,{})
for r in list(range(12,17))+[23,24,25,26,27,28,32,33,34,35,36,39]:
    h=17 if r<=16 else 28
    cad.rowattrs[r]=(cad.rowattrs.get(r,'') or '')  # garde hidden si pose (row22 non ici)
    cad.rowattrs[r]=' ht="%d" customHeight="1"'%h; cad.rows.setdefault(r,{})

b.set_styles(sb.render())
b.save("TEST3b_corrige.xlsm")
print("OK -> TEST3b_corrige.xlsm")
