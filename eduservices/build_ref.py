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

# ============================================================ PIL + ALLOC
import warnings;warnings.filterwarnings("ignore")
import openpyxl,zipfile
from xml.sax.saxutils import unescape
REF=openpyxl.load_workbook("DESIGN_REF.xlsm")
_ss=zipfile.ZipFile("DESIGN_REF.xlsm").read("xl/sharedStrings.xml").decode("utf8")
_SI=re.findall(r'<si>(.*?)</si>',_ss,re.S)
def si_text(i): return unescape("".join(re.findall(r'<t[^>]*>(.*?)</t>',_SI[i],re.S)))
def cell_text(cp):
    if cp is None: return ""
    at,ct=cp; ct=ct or ""
    if 't="s"' in at:
        m=re.search(r'<v>(\d+)</v>',ct); return si_text(int(m.group(1))) if m else ""
    m=re.search(r'<t[^>]*>(.*?)</t>',ct,re.S); return unescape(m.group(1)) if m else ""
def exfill(sheet,ref):
    c=REF[sheet][ref]; f=c.fill
    try: return f.fgColor.rgb[2:] if (f and f.patternType=="solid" and isinstance(f.fgColor.rgb,str) and f.fgColor.rgb!="00000000") else None
    except: return None
def DX(sheet,ref,nf=None,color=None,bold=False,halign="right",keepfill=True):
    fill=exfill(sheet,ref) if keepfill else None
    return sb.xf(font=sb.font(11,bold,False,color or GREY),fill=(sb.fill(fill) if fill else 0),border=BI,numfmt=nf,halign=halign,valign="center")
def RSp(sh,ref,s):
    c=sh.get_cell(ref)
    if c is None: sh.put_cell(ref,' s="%d"'%s,None); return
    at,ct=c; at=re.sub(r'\ss="\d+"','',at); sh.put_cell(ref,' s="%d"'%s+at,ct)

CAP=[(1475,.110736,.021757,.814981,1.059705,.864731,1,68291),(1102,.118872,.016735,1.091242,1.137558,1.124198,1,41783),
 (964,.123795,.014610,1.247557,1.184675,1.287721,1,31533),(890,.126095,.014052,1.351311,1.206678,1.338853,1,24923),
 (1540,.077745,.020903,.780426,.743989,.900064,1,60800),(979,.081545,.014363,1.228416,.780356,1.309838,1,25220),
 (919,.082117,.013565,1.308010,.785827,1.386967,1,22083),(1216,.137885,.021344,.988345,1.319506,.881462,1,21760),
 (1041,.144781,.019104,1.155263,1.385501,.984783,1,14933),(1034,.144781,.019418,1.162606,1.385501,.968887,1,15178),
 (1705,.085003,.029280,.705063,.813451,.642556,1,36612),(1368,.087533,.024360,.878684,.837659,.772307,1,21968),
 (2193,.069519,.027841,.548183,.665268,.675746,1,30240),(1625,.072555,.021828,.739912,.694326,.861889,1,18850)]
CODES=["MBWAY_PAR","MBWAY_LYO","MBWAY_NAN","MBWAY_BOR","ISCOM_PAR","ISCOM_LIL","ISCOM_TLS","IPAC_NAN","IPAC_REN","IPAC_MTP","PIGIER_LYO","PIGIER_BOR","TUNON_PAR","TUNON_LYO"]

from openpyxl.utils import get_column_letter as _GL, column_index_from_string as _CI
def cols_between(c1,c2): return [_GL(i) for i in range(_CI(c1),_CI(c2)+1)]
def format_pil():
    pil=b.sheet("PIL")
    # KPI : gros chiffre bleu centre sur toute la tuile (centerContinuous)
    for c1,c2,nf in [("B","G",NF_EUR),("H","J",NF_EUR),("K","M",NF_PCT),("N","O",NF_EFF)]:
        RSp(pil,c1+"7",sb.xf(font=sb.font(16,True,False,BLUE),numfmt=nf,halign="centerContinuous",valign="center"))
        for col in cols_between(c1,c2):
            if col!=c1: pil.put_cell(col+"7",' s="%d"'%sb.xf(halign="centerContinuous"),None)
    # cap 15-28
    for i in range(14):
        r=15+i; d=CAP[i]
        pil.set_number("D%d"%r,d[0],DX("PIL","D%d"%r,NF_EUR,GREY))
        pil.set_number("E%d"%r,d[1],DX("PIL","E%d"%r,NF_PCT,GREY)); pil.set_number("F%d"%r,d[2],DX("PIL","F%d"%r,NF_PCT,GREY))
        for j,cc in enumerate(("G","H","I")): pil.set_number("%s%d"%(cc,r),round(d[3+j],2),DX("PIL","%s%d"%(cc,r),NF_COE,GREY))
        pil.set_number("J%d"%r,d[6],DX("PIL","J%d"%r,NF_EFF,"1B5FA6",halign="center"))  # cap retenu = saisie
        pil.set_number("K%d"%r,d[7],DX("PIL","K%d"%r,NF_EUR,NAVY))
        if REF["PIL"]["L%d"%r].value is not None: pil.set_text("L%d"%r,CODES[i],DX("PIL","L%d"%r,None,"BFBFBF",halign="left"))
    # synthese 33-46 (formules)
    for r in range(33,47):
        RSp(pil,"D%d"%r,DX("PIL","D%d"%r,NF_EFF,GREY)); RSp(pil,"E%d"%r,DX("PIL","E%d"%r,NF_EUR,BLUE,bold=True))
        RSp(pil,"F%d"%r,DX("PIL","F%d"%r,NF_EUR,GREY)); RSp(pil,"G%d"%r,DX("PIL","G%d"%r,NF_PCT,GREY))
        RSp(pil,"H%d"%r,DX("PIL","H%d"%r,NF_EUR,BLUE,bold=True)); RSp(pil,"I%d"%r,DX("PIL","I%d"%r,NF_PCT,GREY))
        RSp(pil,"J%d"%r,DX("PIL","J%d"%r,NF_EUR,GREY)); RSp(pil,"K%d"%r,DX("PIL","K%d"%r,NF_EUR,GREY)); RSp(pil,"L%d"%r,DX("PIL","L%d"%r,NF_EUR,GREY))
    # totaux 47-49 (garde bandes, gras)
    for r in (47,48,49):
        for cc,nf in [("D",NF_EFF),("E",NF_EUR),("F",NF_EUR),("G",NF_PCT),("H",NF_EUR),("I",NF_PCT),("J",NF_EUR),("K",NF_EUR),("L",NF_EUR)]:
            if REF["PIL"]["%s%d"%(cc,r)].value is not None or cc in "DEFHIJKL":
                RSp(pil,"%s%d"%(cc,r),DX("PIL","%s%d"%(cc,r),nf,NAVY,bold=True))

def format_alloc():
    al=b.sheet("ALLOC")
    # cles : libelles (B) + valeurs saisie creme (C)
    KEYLAB={6:"Siège administratif  →  marque",7:"Publicité de marque  →  marque",8:"Marque  →  campus",9:"Campus  →  classe"}
    for r,lab in KEYLAB.items():
        al.set_text("B%d"%r,lab,sb.xf(font=sb.font(11,True,False,NAVY),halign="left",valign="center"))
    KEYS={6:"Chiffre d'affaires",7:"Effectif",8:"Effectif",9:"Nombre de classes"}
    xsai=sb.xf(font=sb.font(11,True,False,"1B5FA6"),fill=sb.fill(CREAM),border=sb.border(top=(GOLDB,"thin"),bottom=(GOLDB,"thin"),left=(GOLDB,"thin"),right=(GOLDB,"thin")),halign="center",valign="center",wrap=True)
    for r,v in KEYS.items(): al.set_text("C%d"%r,v,xsai)
    # maille 18-95 (garde bandes marque/campus, formate donnees)
    for r in range(18,96):
        c=al.get_cell("B%d"%r); lab=cell_text(c)
        if not lab: continue
        lvl=(len(lab)-len(lab.lstrip()))//3; name=lab.strip(); al.rows.setdefault(r,{})
        gold=(name=="GROUPE")
        bold=(lvl<=1 or gold)
        RSp(al,"C%d"%r,DX("ALLOC","C%d"%r,NF_EFF,NAVY if bold else GREY,bold=bold))
        for cc in "DEFGHIJ": RSp(al,"%s%d"%(cc,r),DX("ALLOC","%s%d"%(cc,r),NF_EUR,(NAVY if bold else GREY),bold=bold))
        RSp(al,"K%d"%r,DX("ALLOC","K%d"%r,NF_EUR,NAVY,bold=True))                 # cout complet
        RSp(al,"L%d"%r,DX("ALLOC","L%d"%r,NF_EUR,GREEN if not gold else NAVY,bold=bold))  # marge
        RSp(al,"M%d"%r,DX("ALLOC","M%d"%r,NF_PCT,(NAVY if bold else GREY),bold=bold))
        # deplie les classes masquees
        if REF["ALLOC"].row_dimensions[r].hidden:
            al.rowattrs[r]=' outlineLevel="%d"'%lvl if lvl else ''

format_pil(); format_alloc()

b.set_styles(sb.render())
b.save("DESIGN_REF_v2.xlsm")
print("OK -> DESIGN_REF_v2.xlsm (cad + PIL + ALLOC)")
