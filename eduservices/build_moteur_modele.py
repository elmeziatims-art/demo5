#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE_MOTEUR_MODELE.xlsx — modèle VIVANT et transparent du moteur.
Les actuals sont en dur (seule donnée « en dur »), tout le reste est en FORMULES
Excel cliquables : élasticité = LN/LN, back-test, et l'effet d'un +Δ% acquisition
jusqu'à l'EBITDA (hypothèses modifiables → tout recalcule)."""
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

RAW=json.load(open('/tmp/moteur_raw.json'))
INK="152230"; TEAL="0D7A62"; TEALD="0A5A48"; TEALBG="E2EFEB"; CARD2="F5F7F9"
FAINT="7D8B98"; WHITE="FFFFFF"; OCHRE="B3641C"; OCHRED="8A4A12"; OCHREBG="F6E8D8"
GREEN="1E7A55"; GREENBG="E4F0E8"; RULE="C8D2DA"; SOFT="51606D"; NAVY="3D4F8F"; NAVYBG="E6E9F4"
INPUTBG="FFF6DA"; INPUTBD="D9B94A"
AR="Arial"
def F(sz=10,b=False,c=INK,it=False): return Font(name=AR,size=sz,bold=b,color=c,italic=it)
def fill(c): return PatternFill("solid",fgColor=c)
CTR=Alignment("center",vertical="center",wrap_text=True)
LFT=Alignment("left",vertical="center"); LFTW=Alignment("left",vertical="center",wrap_text=True)
RGT=Alignment("right",vertical="center")
thin=Side(style="thin",color=RULE); med=Side(style="medium",color=RULE)
inbd=Side(style="medium",color=INPUTBD)
EUR='#,##0 "€";-#,##0 "€";"-"'; NUM='#,##0'; PCT='0.0%'; DEC3='0.000'
NAME={'IPAC_MTP':'IPAC Montpellier','IPAC_NAN':'IPAC Nantes','IPAC_REN':'IPAC Rennes',
 'ISCOM_LIL':'ISCOM Lille','ISCOM_PAR':'ISCOM Paris','ISCOM_TLS':'ISCOM Toulouse',
 'MBWAY_BOR':'MBway Bordeaux','MBWAY_LYO':'MBway Lyon','MBWAY_NAN':'MBway Nantes','MBWAY_PAR':'MBway Paris',
 'PIGIER_BOR':'Pigier Bordeaux','PIGIER_LYO':'Pigier Lyon','TUNON_LYO':'Tunon Lyon','TUNON_PAR':'Tunon Paris'}

wb=openpyxl.Workbook(); ws=wb.active; ws.title="Le moteur (modèle)"
ws.sheet_view.showGridLines=False
def H(r,c,txt,**kw):
    cell=ws.cell(r,c,txt)
    cell.font=F(kw.get('sz',10),kw.get('b',False),kw.get('col',INK),kw.get('it',False))
    cell.alignment=kw.get('al',LFT)
    if kw.get('fmt'): cell.number_format=kw['fmt']
    if kw.get('fill'): cell.fill=fill(kw['fill'])
    return cell
def hdr(r,cols,widths=None):
    for j,h in enumerate(cols,1):
        c=ws.cell(r,j,h); c.font=F(9,True,WHITE); c.fill=fill(TEAL)
        c.alignment=LFT if j==1 else CTR; c.border=Border(bottom=med)

ws["A1"]="EDUSERVICES · budget 2027 · le moteur, à nu"; ws["A1"].font=F(9,True,TEALD)
ws["A2"]="Le moteur expliqué — données réelles + formules cliquables"; ws["A2"].font=F(16,True,INK)
ws["A3"]="Seuls les actuals (fond jaune = saisie) sont en dur. Tout le reste est une formule : cliquez une cellule pour voir le calcul. Changez une hypothèse → tout recalcule."; ws["A3"].font=F(9,False,SOFT)

# =================================================================
# BLOC ① + ② : DONNÉES BRUTES + ÉLASTICITÉ (formule LN/LN visible)
# =================================================================
H(5,1,"①  L'élasticité — la formule, sur vos vraies données",b=True,sz=12,col=TEALD)
H(6,1,"Élasticité  =  LN( leads payants 2026 ÷ leads payants 2024 )  ÷  LN( budget acq 2026 ÷ budget acq 2024 )",b=True,col=OCHRE,it=True)
H(7,1,"→ la colonne « Élasticité » ci-dessous EST cette formule. Cliquez une cellule pour la voir. 0,50 = +10 % budget → +5 % leads.",col=SOFT,it=True)
hrow=9
hdr(hrow,["Campus","Leads pay. 2024","Leads pay. 2026","Budget acq 2024","Budget acq 2026","Élasticité  =LN/LN","+10 % budget →"])
r=hrow+1; first=r
for d in RAW:
    H(r,1,NAME.get(d['campus'],d['campus']),sz=9)
    H(r,2,d['p24'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG); H(r,3,d['p26'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG)
    H(r,4,d['s24'],sz=9,al=RGT,fmt=EUR,fill=INPUTBG); H(r,5,d['s26'],sz=9,al=RGT,fmt=EUR,fill=INPUTBG)
    fc=ws.cell(r,6,f"=LN(C{r}/B{r})/LN(E{r}/D{r})"); fc.number_format=DEC3; fc.alignment=RGT; fc.font=F(9,True,TEALD)
    gc=ws.cell(r,7,f"=(1.1^F{r})-1"); gc.number_format=PCT; gc.alignment=RGT; gc.font=F(9,False,SOFT)
    for j in range(1,8): ws.cell(r,j).border=Border(bottom=thin)
    r+=1
last1=r-1
H(r,1,"Fond jaune = vos actuals (les seules valeurs saisies). Colonnes Élasticité / +10 % = formules.",sz=8,col=FAINT,it=True)
r+=2

# =================================================================
# BLOC ③ : BACK-TEST (formules) — calibré 24→25, prédit 26
# =================================================================
H(r,1,"②  La preuve — le back-test, en formules",b=True,sz=12,col=TEALD); r+=1
H(r,1,"On calcule l'élasticité sur 2024→2025 SEULEMENT, puis on prédit 2026 : leads₂₆ = leads₂₅ × (budget₂₆/budget₂₅) ^ élasticité(24→25).",col=SOFT,it=True); r+=2
hrow2=r
hdr(hrow2,["Campus","L.pay 24","L.pay 25","L.pay 26","Bud. 24","Bud. 25","Bud. 26","Élast. 24→25","Prédit 26  =formule","Réel 26","Écart"])
r=hrow2+1; first2=r
for d in RAW:
    H(r,1,NAME.get(d['campus'],d['campus']),sz=9)
    H(r,2,d['p24'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG); H(r,3,d['p25'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG); H(r,4,d['p26'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG)
    H(r,5,d['s24'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG); H(r,6,d['s25'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG); H(r,7,d['s26'],sz=9,al=RGT,fmt=NUM,fill=INPUTBG)
    e=ws.cell(r,8,f"=LN(C{r}/B{r})/LN(F{r}/E{r})"); e.number_format=DEC3; e.alignment=RGT; e.font=F(9,False,SOFT)
    p=ws.cell(r,9,f"=C{r}*(G{r}/F{r})^H{r}"); p.number_format=NUM; p.alignment=RGT; p.font=F(9,True,NAVY)
    H(r,10,d['p26'],sz=9,al=RGT,fmt=NUM)
    k=ws.cell(r,11,f"=I{r}/J{r}-1"); k.number_format='+0.0%;-0.0%;0.0%'; k.alignment=RGT; k.font=F(9,True,GREEN)
    for j in range(1,12): ws.cell(r,j).border=Border(bottom=thin)
    r+=1
last2=r-1
# total groupe
H(r,1,"GROUPE",b=True,col=TEALD)
tp=ws.cell(r,9,f"=SUM(I{first2}:I{last2})"); tp.number_format=NUM; tp.font=F(10,True,TEALD); tp.alignment=RGT
tr=ws.cell(r,10,f"=SUM(J{first2}:J{last2})"); tr.number_format=NUM; tr.font=F(10,True,TEALD); tr.alignment=RGT
tk=ws.cell(r,11,f"=I{r}/J{r}-1"); tk.number_format='+0.0%;-0.0%;0.0%'; tk.font=F(10,True,GREEN); tk.alignment=RGT
for j in range(1,12): ws.cell(r,j).fill=fill(GREENBG); ws.cell(r,j).border=Border(top=med,bottom=med)
r+=1
H(r,1,"Prédit 26 est une formule qui n'utilise QUE 2024–2025. Elle retrouve le réel 2026. (Données de démo → ~0 % ; en réel, quelques %.)",sz=8,col=OCHRE,it=True)
r+=2

# =================================================================
# BLOC ④ : EFFET D'UN +Δ% — modèle vivant (hypothèses modifiables)
# =================================================================
H(r,1,"③  L'effet d'un +Δ% d'acquisition — modèle vivant (changez les cases jaunes)",b=True,sz=12,col=TEALD); r+=2
# --- hypothèses (cellules d'entrée) ---
lab_col=1; val_col=2
def inrow(r,label,value,fmt,note=""):
    H(r,1,label,sz=10)
    c=ws.cell(r,2,value); c.number_format=fmt; c.alignment=RGT; c.font=F(10,True,INK)
    c.fill=fill(INPUTBG); c.border=Border(top=inbd,bottom=inbd,left=inbd,right=inbd)
    if note: H(r,3,note,sz=8,col=FAINT,it=True)
    return r
H(r,1,"HYPOTHÈSES (modifiables)",b=True,col=OCHRED); r+=1
row_delta=inrow(r,"Δ budget d'acquisition","0.08" and 0.08,PCT,"le geste : +8 %"); r+=1
row_elast=r; H(r,1,"Élasticité retenue (moyenne)",sz=10)
ce=ws.cell(r,2,f"=AVERAGE(F{first}:F{last1})"); ce.number_format=DEC3; ce.alignment=RGT; ce.font=F(10,True,TEALD)
H(r,3,"= moyenne des élasticités du bloc ① (formule)",sz=8,col=FAINT,it=True); r+=1
row_cvar=inrow(r,"Coût variable / élève","300" and 300,EUR,"marginal, classe existante"); r+=1
row_rev=inrow(r,"CA 1ʳᵉ année / inscrit","7608" and 7608,EUR,"votre référentiel"); r+=2
# --- bases (formules sur les tableaux) ---
H(r,1,"BASES (calculées)",b=True,col=TEALD); r+=1
row_bud=r; H(r,1,"Budget acq total 2026",sz=10)
cb=ws.cell(r,2,f"=SUM(E{first}:E{last1})"); cb.number_format=EUR; cb.alignment=RGT; cb.font=F(10,False,SOFT); H(r,3,"=SUM(budgets 2026)",sz=8,col=FAINT,it=True); r+=1
row_leads=r; H(r,1,"Leads payants total 2026",sz=10)
cl=ws.cell(r,2,f"=SUM(C{first}:C{last1})"); cl.number_format=NUM; cl.alignment=RGT; cl.font=F(10,False,SOFT); H(r,3,"=SUM(leads payants 2026)",sz=8,col=FAINT,it=True); r+=1
row_conv=inrow(r,"Conversion lead → inscrit","0.071" and 0.071,PCT,"funnel réel 2026"); r+=2
# --- le P&L marginal (tout en formules) ---
H(r,1,"LE P&L MARGINAL DU +Δ%",b=True,col=INK); r+=1
def calcrow(r,label,formula,fmt,col,note=""):
    H(r,1,label,sz=10,col=col,b=label.startswith("="))
    c=ws.cell(r,2,formula); c.number_format=fmt; c.alignment=RGT; c.font=F(10,label.startswith("="),col)
    if note: H(r,3,note,sz=8,col=SOFT,it=True)
    return r
DE=f"$B${row_delta}"; EL=f"$B${row_elast}"; CV=f"$B${row_cvar}"; RV=f"$B${row_rev}"
BU=f"$B${row_bud}"; LE=f"$B${row_leads}"; CO=f"$B${row_conv}"
row_dbud=calcrow(r,"Budget dépensé",f"={BU}*{DE}",EUR,OCHRED,f"= budget total × Δ"); r+=1
row_dlead=calcrow(r,"Leads payants gagnés",f"={LE}*((1+{DE})^{EL}-1)",NUM,INK,f"= leads × ((1+Δ)^élasticité − 1)"); r+=1
row_dnew=calcrow(r,"Inscrits gagnés",f"=B{row_dlead}*{CO}",NUM,INK,"= leads gagnés × conversion"); r+=1
row_dca=calcrow(r,"CA 1ʳᵉ année",f"=B{row_dnew}*{RV}",EUR,TEALD,"= inscrits gagnés × CA/inscrit"); r+=1
row_dvar=calcrow(r,"− Coût variable à servir",f"=-B{row_dnew}*{CV}",EUR,OCHRED,"= inscrits × coût variable"); r+=1
# EBITDA
H(r,1,"= EBITDA 1ʳᵉ année",b=True,col=GREEN)
ce=ws.cell(r,2,f"=B{row_dca}-B{row_dbud}+B{row_dvar}"); ce.number_format=EUR; ce.font=F(11,True,GREEN); ce.alignment=RGT
H(r,3,"= CA − budget − coût variable",sz=8,col=SOFT,it=True)
for j in range(1,4): ws.cell(r,j).fill=fill(GREENBG); ws.cell(r,j).border=Border(top=med,bottom=med)
r+=1
# CAC marginal
H(r,1,"CAC marginal (coût du prochain inscrit)",sz=10)
cc=ws.cell(r,2,f"=B{row_dbud}/B{row_dnew}"); cc.number_format=EUR; cc.alignment=RGT; cc.font=F(10,True,NAVY)
H(r,3,f"= budget dépensé ÷ inscrits gagnés  → à comparer aux {7608} €/an de valeur d'un inscrit",sz=8,col=OCHRE,it=True)
r+=2
H(r,1,"Changez Δ (8 % → 12 %), l'élasticité, ou le coût variable dans les cases jaunes : l'EBITDA et le CAC marginal se recalculent tout seuls.",sz=9,b=True,col=TEALD)

# largeurs
ws.column_dimensions['A'].width=30
for col,w in zip("BCDEFGHIJK",[13,13,12,12,15,12,13,15,11,11]): ws.column_dimensions[col].width=w

# forcer recalcul à l'ouverture
wb.calculation.fullCalcOnLoad=True
out="/home/user/demo5/eduservices/tagetik/LE_MOTEUR_MODELE.xlsx"
wb.save(out); print("SAVED",out)
