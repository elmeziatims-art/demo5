#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEST3b (design Tagetik) : cles d'allocation + Reconciliation completee +
CHARTE COMMUNE (palette d'origine) sur cad, PIL et ALLOC. 100% chirurgical :
sheetData des 3 onglets + styles.xml + workbook.xml ; briques Tagetik intactes."""
import re,zipfile
from xml.sax.saxutils import unescape
from tgk_surgery import Book, num2col
from tgk_style import StyleBank

b=Book("TEST3b.xlsm")
# table des chaines partagees (pour relire les libelles de la maille)
_ss=zipfile.ZipFile("TEST3b.xlsm").read("xl/sharedStrings.xml").decode("utf8")
_SI=re.findall(r'<si>(.*?)</si>',_ss,re.S)
def si_text(i):
    return unescape("".join(re.findall(r'<t[^>]*>(.*?)</t>',_SI[i],re.S)))
def cell_text(cellpair):
    """texte d'une cellule (inline OU shared string)."""
    if cellpair is None: return ""
    attrs,content=cellpair; content=content or ""
    if 't="s"' in attrs:
        m=re.search(r'<v>(\d+)</v>',content)
        return si_text(int(m.group(1))) if m else ""
    m=re.search(r'<t[^>]*>(.*?)</t>',content,re.S)
    return unescape(m.group(1)) if m else ""
# ---- 1) cles d'allocation -> libelles C6-C9 ----
for nm,ref in {"ALLOC_GRP_BRAND":"ALLOC!$C$6","ALLOC_GRP_MARQUE":"ALLOC!$C$7",
               "ALLOC_BRAND_CAMP":"ALLOC!$C$8","ALLOC_CAMP_CLASS":"ALLOC!$C$9"}.items():
    b.retarget_name(nm,ref)
b.set_fullcalc()

# ---- 2) StyleBank (palette d'origine, partagee par les 3 onglets) ----
sb=StyleBank(b.styles_xml())
NF_EUR=sb.numfmt('#,##0\\ €;(#,##0\\ €);-'); NF_PCT=sb.numfmt('0.0\\ %')
NF_ECE=sb.numfmt('+#,##0\\ €;-#,##0\\ €;-'); NF_ECA=sb.numfmt('+#,##0;-#,##0;-')
NF_EFF=sb.numfmt('#,##0;(#,##0);-'); NF_COE=sb.numfmt('0.00')
BI =sb.border(top=("CBD5DA","thin"),bottom=("CBD5DA","thin"),left=("CBD5DA","thin"),right=("CBD5DA","thin"))
BSA=sb.border(top=("4A6FA5","thin"),bottom=("4A6FA5","thin"),left=("4A6FA5","thin"),right=("4A6FA5","thin"))
def F(sz=10,B=False,i=False,c="1C2733"): return sb.font(sz,B,i,c)
X={}
X["titre"]=sb.xf(font=F(14,True,c="FFFFFF"),fill=sb.fill("1C2733"),halign="centerContinuous",valign="center")
X["sous"] =sb.xf(font=F(9,i=True,c="5B6770"),halign="centerContinuous",valign="center")
X["sect"] =sb.xf(font=F(10,True,c="14586F"),fill=sb.fill("EAF0F3"),border=sb.border(top=("1C2733","medium")),halign="left",valign="center",indent=1)
X["ent"]  =sb.xf(font=F(10,True,c="FFFFFF"),fill=sb.fill("14586F"),border=sb.border(bottom=("1C2733","medium")),halign="center",valign="center",wrap=True)
X["lbl"]  =sb.xf(font=F(10),halign="left",valign="center")
X["lbold"]=sb.xf(font=F(10,True),halign="left",valign="center")
X["lbr"]  =sb.xf(font=F(10,True),halign="right",valign="center")
X["notec"]=sb.xf(font=F(9,i=True,c="5B6770"),halign="center",valign="center")
X["indic"]=sb.xf(font=F(10,True),border=BI,halign="left",valign="center")
X["lblb"] =sb.xf(font=F(10),border=BI,halign="left",valign="center")
X["lwrap"]=sb.xf(font=F(10),border=BI,halign="left",valign="center",wrap=True)
X["code"] =sb.xf(font=F(10,True,c="14586F"),border=BI,halign="left",valign="center")
X["codeg"]=sb.xf(font=F(10,c="5B6770"),border=BI,halign="left",valign="center")
# valeurs
X["eurI"]=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_EUR,halign="right",valign="center")
X["eurL"]=sb.xf(font=F(10),border=BI,numfmt=NF_EUR,halign="right",valign="center")
X["eurK"]=sb.xf(font=F(10,c="1B6B4F"),border=BI,numfmt=NF_EUR,halign="right",valign="center")
X["ece"] =sb.xf(font=F(10),border=BI,numfmt=NF_ECE,halign="right",valign="center")
X["pct"] =sb.xf(font=F(10),border=BI,numfmt=NF_PCT,halign="right",valign="center")
X["pctI"]=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_PCT,halign="right",valign="center")
X["pctK"]=sb.xf(font=F(10,c="1B6B4F"),border=BI,numfmt=NF_PCT,halign="right",valign="center")
X["effI"]=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_EFF,halign="right",valign="center")
X["effL"]=sb.xf(font=F(10),border=BI,numfmt=NF_EFF,halign="right",valign="center")
X["effK"]=sb.xf(font=F(10,c="1B6B4F"),border=BI,numfmt=NF_EFF,halign="right",valign="center")
X["coeI"]=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,numfmt=NF_COE,halign="center",valign="center")
X["coe"] =sb.xf(font=F(10),border=BI,numfmt=NF_COE,halign="right",valign="center")
X["empty"]=sb.xf(border=BI)
# totaux (anthracite)
X["totL"]=sb.xf(font=F(10,True,c="FFFFFF"),fill=sb.fill("1C2733"),border=sb.border(top=("1C2733","medium")),halign="left",valign="center")
X["totEUR"]=sb.xf(font=F(10,True,c="FFFFFF"),fill=sb.fill("1C2733"),border=sb.border(top=("1C2733","medium")),numfmt=NF_EUR,halign="right",valign="center")
X["totPCT"]=sb.xf(font=F(10,True,c="FFFFFF"),fill=sb.fill("1C2733"),border=sb.border(top=("1C2733","medium")),numfmt=NF_PCT,halign="right",valign="center")
X["totEFF"]=sb.xf(font=F(10,True,c="FFFFFF"),fill=sb.fill("1C2733"),border=sb.border(top=("1C2733","medium")),numfmt=NF_EFF,halign="right",valign="center")
X["totE0"]=sb.xf(font=F(10,True,c="FFFFFF"),fill=sb.fill("1C2733"),border=sb.border(top=("1C2733","medium")),halign="right",valign="center")
# bandes marque (ALLOC) + KPI (PIL)
X["band"] =sb.xf(font=F(10,True,c="14586F"),fill=sb.fill("EAF0F3"),border=sb.border(top=("CBD5DA","thin")),halign="left",valign="center")
X["bandN"]=sb.xf(font=F(10,True,c="1C2733"),fill=sb.fill("EAF0F3"),border=sb.border(top=("CBD5DA","thin")),numfmt=NF_EUR,halign="right",valign="center")
X["bandEFF"]=sb.xf(font=F(10,True,c="1C2733"),fill=sb.fill("EAF0F3"),border=sb.border(top=("CBD5DA","thin")),numfmt=NF_EFF,halign="right",valign="center")
X["bandPCT"]=sb.xf(font=F(10,True,c="1C2733"),fill=sb.fill("EAF0F3"),border=sb.border(top=("CBD5DA","thin")),numfmt=NF_PCT,halign="right",valign="center")
X["kpiL"]=sb.xf(font=F(9,True,c="5B6770"),fill=sb.fill("EAF0F3"),halign="centerContinuous",valign="center")
X["kpiEUR"]=sb.xf(font=F(17,True,c="14586F"),fill=sb.fill("EAF0F3"),border=sb.border(bottom=("1C2733","medium")),numfmt=NF_EUR,halign="centerContinuous",valign="center")
X["kpiPCT"]=sb.xf(font=F(17,True,c="14586F"),fill=sb.fill("EAF0F3"),border=sb.border(bottom=("1C2733","medium")),numfmt=NF_PCT,halign="centerContinuous",valign="center")
X["kpiEFF"]=sb.xf(font=F(17,True,c="14586F"),fill=sb.fill("EAF0F3"),border=sb.border(bottom=("1C2733","medium")),numfmt=NF_EFF,halign="centerContinuous",valign="center")
X["kpiB"]=sb.xf(fill=sb.fill("EAF0F3"),halign="centerContinuous")
X["kpiBb"]=sb.xf(fill=sb.fill("EAF0F3"),border=sb.border(bottom=("1C2733","medium")),halign="centerContinuous")
X["zeb"]=sb.fill  # placeholder

# ---- helpers ----
def RS(sh,ref,s):
    c=sh.get_cell(ref)
    if c is None: sh.put_cell(ref,' s="%d"'%s,None); return
    at,ct=c; at=re.sub(r'\ss="\d+"','',at); sh.put_cell(ref,' s="%d"'%s+at,ct)
def BL(sh,ref,s): sh.put_cell(ref,' s="%d"'%s,None)
def cols_letters(c1,c2): return [num2col(i) for i in range(_ci(c1),_ci(c2)+1)]
def _ci(col):
    n=0
    for ch in col: n=n*26+(ord(ch)-64)
    return n
def rowh(sh,r,h,extra=""):
    sh.rowattrs[r]=' ht="%d" customHeight="1"%s'%(h,extra); sh.rows.setdefault(r,{})

# ==================== CAD ====================
def format_cad():
    cad=b.sheet("cad")
    cad.set_text("B2","POSTE DE COMMANDE CFO   ·   Cadrage CA & EBITDA 2027",s=X["titre"])
    for col in "CDEFGHIJ": BL(cad,col+"2",X["titre"])
    cad.set_text("B3","EDUSERVICES GROUP  ·  MBway · ISCOM · Ipac · Pigier · Tunon  ·  Simulation budgétaire  ·  Montants en €",s=X["sous"])
    for col in "CDEFGHIJ": BL(cad,col+"3",X["sous"])
    cad.set_text("B5","Scénario actif",s=X["lbold"])
    RS(cad,"C5",sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,halign="center",valign="center"))
    cad.set_text("E5","Croissance CA cible",s=X["lbr"]); cad.set_number("F5",0.05,s=X["pctI"])
    cad.set_text("E6","Marge EBITDA cible",s=X["lbr"]);  cad.set_number("F6",0.15,s=X["pctI"])
    cad.set_text("B8","1 ·  Réconciliation   —   Référence · Cible · Construit (scénario actif)",s=X["sect"])
    for col in "CDEFG": BL(cad,col+"8",X["sect"])
    cad.set_text("I8","Coeff prix / marque",s=X["sect"]); BL(cad,"J8",X["sect"])
    for col,txt in [("B","Indicateur"),("C","Référence"),("D","Cible"),("E","Construit"),("F","Écart"),("G","Écart %")]:
        cad.set_text(col+"10",txt,s=X["ent"])
    cad.set_text("I10","Marque",s=X["ent"]); cad.set_text("J10","Coeff prix",s=X["ent"])
    cad.set_text("C11","2026",s=X["notec"]); cad.set_text("D11","2027",s=X["notec"]); cad.set_text("E11","2027",s=X["notec"])
    for r in (12,13,14,15): RS(cad,"B%d"%r,X["indic"])
    cad.set_number("C12",22544725,s=X["eurI"]); cad.set_formula("D12","C12*(1+TEC_PL)",s=X["eurL"])
    cad.set_formula("E12","SUMIFS(Moteur!$R:$R,Moteur!$B:$B,SCENARIO_CODE)",s=X["eurK"])
    cad.set_formula("F12","E12-D12",s=X["ece"]); cad.set_formula("G12","IFERROR(E12/D12-1,0)",s=X["pct"])
    cad.set_number("C13",3291530,s=X["eurI"]); cad.set_formula("D13","D12*TEC_EBITDA",s=X["eurL"])
    cad.set_formula("E13",'SUMIFS(_CALC_PNL!$T:$T,_CALC_PNL!$D:$D,SCENARIO_CODE,_CALC_PNL!$C:$C,"2027")',s=X["eurK"])
    cad.set_formula("F13","E13-D13",s=X["ece"]); cad.set_formula("G13","IFERROR(E13/D13-1,0)",s=X["pct"])
    cad.set_formula("C14","IFERROR(C13/C12,0)",s=X["pct"]); cad.set_formula("D14","TEC_EBITDA",s=X["pct"])
    cad.set_formula("E14","IFERROR(E13/E12,0)",s=X["pctK"]); cad.set_formula("F14","E14-D14",s=X["pct"]); BL(cad,"G14",X["pct"])
    cad.set_number("C15",3036,s=X["effI"]); BL(cad,"D15",X["empty"])
    cad.set_formula("E15","SUMIFS(Moteur!$P:$P,Moteur!$B:$B,SCENARIO_CODE)",s=X["effK"])
    BL(cad,"F15",X["empty"]); BL(cad,"G15",X["empty"])
    for i,co in enumerate([1.2,1.15,0.95,0.9,1.05]):
        r=12+i; RS(cad,"I%d"%r,X["lblb"]); cad.set_number("J%d"%r,co,s=X["coeI"])
    cad.set_text("B19","2 ·  Leviers de CROISSANCE / REVENUS",s=X["sect"])
    for col in "CDEF": BL(cad,col+"19",X["sect"])
    cad.set_text("B21","Paramètre",s=X["ent"]); RS(cad,"C21",X["ent"]); RS(cad,"D21",X["ent"]); RS(cad,"E21",X["ent"])
    cad.set_text("F21","ACTIF (scénario)",s=X["ent"])
    cad.rowattrs[22]=' hidden="1"'; cad.rows.setdefault(22,{})
    LEV={23:(0.08,0.15,-0.05),24:(0.1,0.2,-0.05),25:(0.002855,0.035,0.02),26:(0.01,0.03,0),
         27:(0.01,0.025,0),28:(0.005,0.015,-0.01),32:(0.02,0.015,0.03),33:(0.025,0.02,0.03),
         34:(0.04,0.03,0.05),35:(0.018697,0.03,0),36:(0,-0.03,0.04),39:(90,90,90)}
    for r,(v1,v2,v3) in LEV.items():
        eur=(r==39); RS(cad,"B%d"%r,X["lwrap"])
        xin=X["eurI"] if eur else X["pctI"]; xloc=X["eurL"] if eur else X["pct"]
        cad.set_number("C%d"%r,v1,s=xin); cad.set_number("D%d"%r,v2,s=xin); cad.set_number("E%d"%r,v3,s=xin)
        RS(cad,"F%d"%r,xloc)
    cad.set_text("B30","3 ·  Leviers de COÛTS",s=X["sect"])
    for col in "CDEF": BL(cad,col+"30",X["sect"])
    cad.set_text("B38","4 ·  Constante  —  frais de dossier",s=X["sect"])
    for col in "CDEF": BL(cad,col+"38",X["sect"])
    cad.set_cols('<cols><col min="1" max="1" width="2.6" customWidth="1"/><col min="2" max="2" width="40" customWidth="1"/>'
     '<col min="3" max="5" width="15.5" customWidth="1"/><col min="6" max="6" width="14" customWidth="1"/>'
     '<col min="7" max="7" width="11" customWidth="1"/><col min="8" max="8" width="3" customWidth="1"/>'
     '<col min="9" max="9" width="23" customWidth="1"/><col min="10" max="10" width="12" customWidth="1"/></cols>')
    for r,h in {1:6,2:30,3:16,4:6,7:6,8:20,9:6,10:28,11:13,17:6,18:6,20:6,21:28,29:6,31:6,37:6}.items(): rowh(cad,r,h)
    for r in list(range(12,17))+[23,24,25,26,27,28,32,33,34,35,36,39]: rowh(cad,r,17 if r<=16 else 28)
    cad.set_view(gridlines_off=True,freeze=(0,3,"A4"))

# ==================== PIL ====================
CAP=[(1475.012,0.110736,0.021757,0.814981,1.059705,0.864731,1,68291),
 (1101.595,0.118872,0.016735,1.091242,1.137558,1.124198,1,41783),
 (963.569,0.123795,0.014610,1.247557,1.184675,1.287721,1,31533),
 (889.585,0.126095,0.014052,1.351311,1.206678,1.338853,1,24923),
 (1540.321,0.077745,0.020903,0.780426,0.743989,0.900064,1,60800),
 (978.583,0.081545,0.014363,1.228416,0.780356,1.309838,1,25220),
 (919.035,0.082117,0.013565,1.308010,0.785827,1.386967,1,22083),
 (1216.283,0.137885,0.021344,0.988345,1.319506,0.881462,1,21760),
 (1040.548,0.144781,0.019104,1.155263,1.385501,0.984783,1,14933),
 (1033.976,0.144781,0.019418,1.162606,1.385501,0.968887,1,15178),
 (1704.964,0.085003,0.029280,0.705063,0.813451,0.642556,1,36612),
 (1368.076,0.087533,0.024360,0.878684,0.837659,0.772307,1,21968),
 (2192.893,0.069519,0.027841,0.548183,0.665268,0.675746,1,30240),
 (1624.661,0.072555,0.021828,0.739912,0.694326,0.861889,1,18850)]
def format_pil():
    pil=b.sheet("PIL")
    pil.set_text("B2","PILOTAGE   ·   Cockpit de décision CA / EBITDA 2027",s=X["titre"])
    for col in cols_letters("C","O"): BL(pil,col+"2",X["titre"])
    pil.set_text("B3","EDUSERVICES GROUP  ·  14 campus  ·  Scénario : Cadrage (V01)  ·  Montants en €  ·  Exercice 2027",s=X["sous"])
    for col in cols_letters("C","O"): BL(pil,col+"3",X["sous"])
    # KPI band 6-7 : NE PAS effacer les cellules-valeur (formules B7/H7/K7/N7)
    VAL={"B":"kpiEUR","H":"kpiEUR","K":"kpiPCT","N":"kpiEFF"}
    LAB={"B":"CA 2027","H":"EBITDA après siège","K":"Marge EBITDA","N":"Effectif"}
    for col in cols_letters("B","O"):
        if col in LAB: pil.set_text(col+"6",LAB[col],s=X["kpiL"])
        else: BL(pil,col+"6",X["kpiB"])
        if col in VAL: RS(pil,col+"7",X[VAL[col]])   # garde la formule =E49 etc.
        else: BL(pil,col+"7",X["kpiBb"])
    rowh(pil,6,18); rowh(pil,7,32)
    # section 1 cap
    pil.set_text("B12","1 ·  Cap stratégique par campus   —   capacités & budget d'acquisition",s=X["sect"])
    for col in cols_letters("A","L"):
        if col!="B": BL(pil,col+"12",X["sect"])
    RS(pil,"A12",X["sect"])
    CAPH=[("A","Campus"),("B","Marque"),("C","Ville"),("D","CAC marginal"),("E","Croiss. leads"),("F","Intensité mkt"),
          ("G","Cap. effectifs"),("H","Cap. moment."),("I","Cap. potentiel"),("J","Cap retenu"),("K","Budget acq. réf."),("L","Entity")]
    for col,txt in CAPH: pil.set_text(col+"14",txt,s=X["ent"])
    CODES=["MBWAY_PAR","MBWAY_LYO","MBWAY_NAN","MBWAY_BOR","ISCOM_PAR","ISCOM_LIL","ISCOM_TLS",
           "IPAC_NAN","IPAC_REN","IPAC_MTP","PIGIER_LYO","PIGIER_BOR","TUNON_PAR","TUNON_LYO"]
    for i in range(14):
        r=15+i; d=CAP[i]
        RS(pil,"A%d"%r,X["code"]); RS(pil,"B%d"%r,X["lblb"]); RS(pil,"C%d"%r,X["lblb"])
        pil.set_number("D%d"%r,round(d[0]),s=X["eurL"]); pil.set_number("E%d"%r,d[1],s=X["pct"]); pil.set_number("F%d"%r,d[2],s=X["pct"])
        pil.set_number("G%d"%r,round(d[3],2),s=X["coe"]); pil.set_number("H%d"%r,round(d[4],2),s=X["coe"]); pil.set_number("I%d"%r,round(d[5],2),s=X["coe"])
        pil.set_number("J%d"%r,d[6],s=X["effI"]); pil.set_number("K%d"%r,d[7],s=X["eurL"])
        pil.set_text("L%d"%r,CODES[i],s=X["codeg"])   # Entity = code entité
        rowh(pil,r,17)
    # section 2 synthese
    pil.set_text("B30","2 ·  Synthèse par campus   —   résultats reconstruits (scénario actif)",s=X["sect"])
    for col in cols_letters("A","L"):
        if col!="B": BL(pil,col+"30",X["sect"])
    RS(pil,"A30",X["sect"])
    SYNH=[("A","Campus"),("B","Marque"),("C","Ville"),("D","Effectif"),("E","CA 2027"),("F","Prix moyen"),
          ("G","Part CA"),("H","EBITDA campus"),("I","Mrg EBITDA"),("J","EBITDA / étud."),("K","Rejoué"),("L","CAC marg.")]
    for col,txt in SYNH: pil.set_text(col+"32",txt,s=X["ent"])
    for r in range(33,47):
        RS(pil,"A%d"%r,X["codeg"]); RS(pil,"B%d"%r,X["lblb"]); RS(pil,"C%d"%r,X["lblb"])
        RS(pil,"D%d"%r,X["effK"]); RS(pil,"E%d"%r,X["eurK"]); RS(pil,"F%d"%r,X["eurL"])
        RS(pil,"G%d"%r,X["pct"]); RS(pil,"H%d"%r,X["eurK"]); RS(pil,"I%d"%r,X["pct"])
        RS(pil,"J%d"%r,X["eurL"]); RS(pil,"K%d"%r,X["eurL"]); RS(pil,"L%d"%r,X["eurL"])
        rowh(pil,r,17)
    for r in (47,48,49):
        RS(pil,"A%d"%r,X["totL"])
        RS(pil,"D%d"%r,X["totEFF"]); RS(pil,"E%d"%r,X["totEUR"]); RS(pil,"F%d"%r,X["totEUR"])
        RS(pil,"G%d"%r,X["totPCT"]); RS(pil,"H%d"%r,X["totEUR"]); RS(pil,"I%d"%r,X["totPCT"])
        RS(pil,"J%d"%r,X["totEUR"]); RS(pil,"K%d"%r,X["totEUR"]); RS(pil,"L%d"%r,X["totE0"])
        for col in ("B","C"): BL(pil,col+str(r),X["totL"])
        rowh(pil,r,19)
    pil.set_cols('<cols><col min="1" max="1" width="13" customWidth="1"/><col min="2" max="2" width="9" customWidth="1"/>'
     '<col min="3" max="3" width="13" customWidth="1"/><col min="4" max="4" width="11" customWidth="1"/>'
     '<col min="5" max="5" width="16" customWidth="1"/><col min="6" max="6" width="11" customWidth="1"/>'
     '<col min="7" max="7" width="10.5" customWidth="1"/><col min="8" max="8" width="15" customWidth="1"/>'
     '<col min="9" max="9" width="11" customWidth="1"/><col min="10" max="10" width="11" customWidth="1"/>'
     '<col min="11" max="11" width="13" customWidth="1"/><col min="12" max="12" width="12" customWidth="1"/>'
     '<col min="13" max="13" width="3" customWidth="1"/><col min="14" max="14" width="9" customWidth="1"/>'
     '<col min="15" max="15" width="6" customWidth="1"/></cols>')
    for r,h in {1:6,4:7,5:7,8:7,9:7,10:7,11:7,12:20,29:7,30:20,31:7}.items(): rowh(pil,r,h)
    rowh(pil,14,28); rowh(pil,32,28)
    pil.set_view(gridlines_off=True,freeze=(3,4,"D5"))

# ==================== ALLOC ====================
def format_alloc():
    al=b.sheet("ALLOC")
    al.set_text("B2","ALLOCATION & RENTABILITÉ   ·   coûts complets & marge par maille",s=X["titre"])
    for col in cols_letters("C","M"): BL(al,col+"2",X["titre"])
    al.set_text("B3","EDUSERVICES GROUP  ·  Marque ▸ Campus ▸ Classe  ·  Exercice 2026  ·  Montants en €",s=X["sous"])
    for col in cols_letters("C","M"): BL(al,col+"3",X["sous"])
    al.set_text("B5","Clés d'allocation & inducteurs de répartition (saisie)",s=X["sect"])
    for col in cols_letters("C","M"): BL(al,col+"5",X["sect"])
    KEYS={6:("Siège administratif  →  marque","Chiffre d'affaires"),7:("Publicité de marque  →  marque","Effectif"),
          8:("Marque  →  campus","Effectif"),9:("Campus  →  classe","Nombre de classes")}
    for r,(lab,val) in KEYS.items():
        al.set_text("B%d"%r,lab,s=X["lbold"]); al.set_text("C%d"%r,val,s=sb.xf(font=F(10,c="1F3D7A"),fill=sb.fill("E4ECFA"),border=BSA,halign="center",valign="center",wrap=True))
        rowh(al,r,24)
    al.set_text("B14","Maille fine   —   déplié campus / classe, coût complet et marge",s=X["sect"])
    for col in cols_letters("C","M"): BL(al,col+"14",X["sect"])
    HED=[("B","Marque ▸ Campus ▸ Classe"),("C","Effectif"),("D","CA"),("E","VAC"),("F","PERM"),("G","ODIR"),
         ("H","STRUCT"),("I","Frais marque"),("J","Holding"),("K","Coût complet"),("L","Marge complète"),("M","Marge %")]
    for col,txt in HED: al.set_text(col+"17",txt,s=X["ent"])
    band_xf=sb.xf(font=F(10,True,c="14586F"),fill=sb.fill("EAF0F3"),border=sb.border(top=("CBD5DA","thin")),halign="left",valign="center")
    for r in range(18,96):
        c=al.get_cell("B%d"%r)
        if c is None: continue
        lab=cell_text(c)
        if not lab: continue
        lead=len(lab)-len(lab.lstrip()); lvl=lead//3; name=lab.strip()
        al.rowattrs[r]=(' outlineLevel="%d"'%lvl if lvl else ''); al.rows.setdefault(r,{})
        if name=="GROUPE":
            al.set_text("B%d"%r,"GROUPE  —  EDUSERVICES",s=X["totL"])
            RS(al,"C%d"%r,X["totEFF"])
            for col in "DEFGHIJKL": RS(al,col+str(r),X["totEUR"])
            RS(al,"M%d"%r,X["totPCT"]); rowh(al,r,20); continue
        if lvl==0:                                   # marque = bande sous-total
            al.set_text("B%d"%r,name,s=band_xf)
            RS(al,"C%d"%r,X["bandEFF"])
            for col in "DEFGHIJKL": RS(al,col+str(r),X["bandN"])
            RS(al,"M%d"%r,X["bandPCT"]); rowh(al,r,18)
        else:                                        # campus (1) / classe (2)
            bxf=sb.xf(font=(F(10,True) if lvl==1 else F(10)),border=BI,halign="left",valign="center",indent=lvl*2)
            al.set_text("B%d"%r,name,s=bxf)
            RS(al,"C%d"%r,X["effL"])
            for col in "DEFGHIJKL": RS(al,col+str(r),X["eurL"])
            RS(al,"M%d"%r,X["pct"]); rowh(al,r,16)
    al.set_cols('<cols><col min="1" max="1" width="2.6" customWidth="1"/><col min="2" max="2" width="30" customWidth="1"/>'
     '<col min="3" max="3" width="12" customWidth="1"/><col min="4" max="4" width="14" customWidth="1"/>'
     '<col min="5" max="10" width="13" customWidth="1"/><col min="11" max="11" width="14" customWidth="1"/>'
     '<col min="12" max="12" width="14" customWidth="1"/><col min="13" max="13" width="9" customWidth="1"/></cols>')
    for r,h in {1:6,4:7,10:7,11:7,12:7,13:7,15:7,16:7}.items(): rowh(al,r,h)
    rowh(al,17,28)
    al.set_view(gridlines_off=True,freeze=(2,17,"C18"))

format_cad(); format_pil(); format_alloc()
b.set_styles(sb.render())
b.save("TEST3b_corrige.xlsm")
print("OK -> TEST3b_corrige.xlsm (cad+PIL+ALLOC)")
