#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE_MOTEUR_MODELE.xlsx — modèle VIVANT du moteur (formules cliquables).
① élasticité = LN/LN sur les actuals · ② back-test MUSCLÉ jusqu'aux inscrits
(calibré 24→25, prédit 26) · ③ effet d'un +Δ% PAR MARQUE, piloté par des cases
jaunes modifiables (change Δ → tout recalcule)."""
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

D=json.load(open('/tmp/moteur_full.json')); CAMP=D['camp']; BRAND=D['brand']
INK="152230"; TEAL="0D7A62"; TEALD="0A5A48"; TEALBG="E2EFEB"
FAINT="7D8B98"; WHITE="FFFFFF"; OCHRE="B3641C"; OCHRED="8A4A12"; OCHREBG="F6E8D8"
GREEN="1E7A55"; GREENBG="E4F0E8"; RULE="C8D2DA"; SOFT="51606D"; NAVY="3D4F8F"
INPUTBG="FFF6DA"; INPUTBD="D9B94A"
AR="Arial"
def F(sz=10,b=False,c=INK,it=False): return Font(name=AR,size=sz,bold=b,color=c,italic=it)
def fill(c): return PatternFill("solid",fgColor=c)
CTR=Alignment("center",vertical="center",wrap_text=True)
LFT=Alignment("left",vertical="center"); LFTW=Alignment("left",vertical="center",wrap_text=True)
RGT=Alignment("right",vertical="center")
thin=Side(style="thin",color=RULE); med=Side(style="medium",color=RULE); inbd=Side(style="medium",color=INPUTBD)
EUR='#,##0 "€";-#,##0 "€";"-"'; NUM='#,##0'; PCT='0.0%'; DEC3='0.000'; SPCT='+0.0%;-0.0%;0.0%'
NAME={'IPAC_MTP':'IPAC Montpellier','IPAC_NAN':'IPAC Nantes','IPAC_REN':'IPAC Rennes',
 'ISCOM_LIL':'ISCOM Lille','ISCOM_PAR':'ISCOM Paris','ISCOM_TLS':'ISCOM Toulouse',
 'MBWAY_BOR':'MBway Bordeaux','MBWAY_LYO':'MBway Lyon','MBWAY_NAN':'MBway Nantes','MBWAY_PAR':'MBway Paris',
 'PIGIER_BOR':'Pigier Bordeaux','PIGIER_LYO':'Pigier Lyon','TUNON_LYO':'Tunon Lyon','TUNON_PAR':'Tunon Paris'}

wb=openpyxl.Workbook(); ws=wb.active; ws.title="Le moteur (modèle)"
ws.sheet_view.showGridLines=False
def put(r,c,v,sz=10,b=False,col=INK,it=False,al=LFT,fmt=None,bg=None,box=None):
    cell=ws.cell(r,c,v); cell.font=F(sz,b,col,it); cell.alignment=al
    if fmt: cell.number_format=fmt
    if bg: cell.fill=fill(bg)
    if box: cell.border=box
    return cell
def head(r,cols,frm=1):
    for j,h in enumerate(cols,frm):
        c=ws.cell(r,j,h); c.font=F(8.5,True,WHITE); c.fill=fill(TEAL)
        c.alignment=LFT if j==frm else CTR; c.border=Border(bottom=med)
def IN(r,c,v,fmt):  # cellule d'entrée (jaune)
    cell=ws.cell(r,c,v); cell.number_format=fmt; cell.alignment=RGT; cell.font=F(10,True,INK)
    cell.fill=fill(INPUTBG); cell.border=Border(top=inbd,bottom=inbd,left=inbd,right=inbd); return cell

put(1,1,"EDUSERVICES · budget 2027 · le moteur, à nu",sz=9,b=True,col=TEALD)
put(2,1,"Le moteur — données réelles + formules cliquables",sz=16,b=True)
put(3,1,"Fond jaune = actuals (seule saisie). Tout le reste = formule : cliquez pour voir le calcul, ou changez une case jaune → tout recalcule.",sz=9,col=SOFT)

# ============================== ① ÉLASTICITÉ ==============================
put(5,1,"①  L'élasticité — la formule, sur vos vraies données",sz=12,b=True,col=TEALD)
put(6,1,"Élasticité = LN(leads pay. 2026 ÷ leads pay. 2024) ÷ LN(budget acq 2026 ÷ budget acq 2024)   — la pente log-log",sz=9,b=True,col=OCHRE,it=True)
hr=8
head(hr,["Campus","Leads pay 2024","Leads pay 2026","Budget acq 2024","Budget acq 2026","Élasticité =LN/LN","+10% budget→"])
r=hr+1; e1=r
for d in CAMP:
    put(r,1,NAME[d['campus']],sz=9)
    put(r,2,d['p24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put(r,3,d['p26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,4,d['s24'],sz=9,al=RGT,fmt=EUR,bg=INPUTBG); put(r,5,d['s26'],sz=9,al=RGT,fmt=EUR,bg=INPUTBG)
    put(r,6,f"=LN(C{r}/B{r})/LN(E{r}/D{r})",sz=9,b=True,col=TEALD,al=RGT,fmt=DEC3)
    put(r,7,f"=(1.1^F{r})-1",sz=9,col=SOFT,al=RGT,fmt=PCT)
    for j in range(1,8): ws.cell(r,j).border=Border(bottom=thin)
    r+=1
l1=r-1
put(r,1,"Cliquez une cellule « Élasticité » : vous verrez =LN(…)/LN(…) sur les chiffres réels du campus.",sz=8,col=FAINT,it=True)
r+=2

# ============================== ② BACK-TEST MUSCLÉ ==============================
put(r,1,"②  La preuve — back-test complet : du budget jusqu'aux INSCRITS, sur l'année cachée",sz=12,b=True,col=TEALD); r+=1
put(r,1,"Élasticité calculée sur 2024→2025 seulement, puis on prédit 2026 : leads, PUIS inscrits (× conversion 2025). Tout en formules.",sz=9,col=SOFT,it=True); r+=2
hr=r
head(hr,["Campus","L.pay24","L.pay25","Bud24","Bud25","Bud26","Élast 24→25","Préd. leads pay26","+ org.26",
         "= leads26 préd.","Conv.25","Inscrits26 préd.","Inscrits26 réel","Écart inscrits"])
r=hr+1; e2=r
for d in CAMP:
    put(r,1,NAME[d['campus']],sz=8.5)
    put(r,2,d['p24'],sz=8.5,al=RGT,fmt=NUM,bg=INPUTBG); put(r,3,d['p25'],sz=8.5,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,4,d['s24'],sz=8.5,al=RGT,fmt=NUM,bg=INPUTBG); put(r,5,d['s25'],sz=8.5,al=RGT,fmt=NUM,bg=INPUTBG); put(r,6,d['s26'],sz=8.5,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,7,f"=LN(C{r}/B{r})/LN(E{r}/D{r})",sz=8.5,col=SOFT,al=RGT,fmt=DEC3)
    put(r,8,f"=C{r}*(F{r}/E{r})^G{r}",sz=8.5,col=NAVY,al=RGT,fmt=NUM)
    put(r,9,d['org26'],sz=8.5,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,10,f"=H{r}+I{r}",sz=8.5,col=NAVY,al=RGT,fmt=NUM)
    put(r,11,f"=L_{r}",sz=8.5)  # placeholder replaced below
    # conv25 = n25/l25  (colonnes K raw ? on met n25,l25 en note-cellules cachées à droite)
    r+=1
l2=r-1
# on ajoute conv25 proprement : colonnes cachées R=l25, S=n25 ; conv en K
for i,d in enumerate(CAMP):
    rr=e2+i
    put(rr,18,d['l25'],sz=8,al=RGT,fmt=NUM,col=FAINT)   # R = leads tot 2025 (réf)
    put(rr,19,d['n25'],sz=8,al=RGT,fmt=NUM,col=FAINT)   # S = inscrits 2025 (réf)
    ws.cell(rr,11,f"=S{rr}/R{rr}").number_format=PCT; ws.cell(rr,11).alignment=RGT; ws.cell(rr,11).font=F(8.5,False,SOFT)  # K conv25
    ws.cell(rr,12,f"=J{rr}*K{rr}").number_format=NUM; ws.cell(rr,12).alignment=RGT; ws.cell(rr,12).font=F(8.5,True,NAVY)   # L inscrits préd
    ws.cell(rr,13,CAMP[i]['n26']).number_format=NUM; ws.cell(rr,13).alignment=RGT; ws.cell(rr,13).font=F(8.5)             # M réel
    ws.cell(rr,14,f"=L{rr}/M{rr}-1").number_format=SPCT; ws.cell(rr,14).alignment=RGT; ws.cell(rr,14).font=F(8.5,True,GREEN)# N écart
    for j in range(1,15): ws.cell(rr,j).border=Border(bottom=thin)
put(e2-1+len(CAMP)+0,1,"",)  # noop
# total groupe back-test
r=l2+1
put(r,1,"GROUPE",sz=9,b=True,col=TEALD)
ws.cell(r,10,f"=SUM(J{e2}:J{l2})").number_format=NUM; ws.cell(r,10).font=F(9,True,TEALD); ws.cell(r,10).alignment=RGT
ws.cell(r,12,f"=SUM(L{e2}:L{l2})").number_format=NUM; ws.cell(r,12).font=F(9,True,TEALD); ws.cell(r,12).alignment=RGT
ws.cell(r,13,f"=SUM(M{e2}:M{l2})").number_format=NUM; ws.cell(r,13).font=F(9,True,TEALD); ws.cell(r,13).alignment=RGT
ws.cell(r,14,f"=L{r}/M{r}-1").number_format=SPCT; ws.cell(r,14).font=F(9,True,GREEN); ws.cell(r,14).alignment=RGT
for j in range(1,15): ws.cell(r,j).fill=fill(GREENBG); ws.cell(r,j).border=Border(top=med,bottom=med)
put(r+1,1,"Colonnes R/S (gris, à droite) = leads & inscrits 2025, pour la conversion. Le moteur retrouve les inscrits 2026 qu'il n'a jamais vus.",sz=8,col=OCHRE,it=True)
r+=3

# ============================== ③ EFFET +Δ% PAR MARQUE ==============================
put(r,1,"③  L'effet d'un +Δ% d'acquisition — modèle vivant (changez les cases jaunes)",sz=12,b=True,col=TEALD); r+=1
# hypothèses globales
put(r,1,"HYPOTHÈSES",sz=10,b=True,col=OCHRED)
put(r,4,"↓ modifiables (jaune)",sz=8,col=FAINT,it=True); r+=1
row_d=r;  put(r,1,"Δ budget d'acquisition",sz=10);       IN(r,2,0.08,PCT);  put(r,3,"le geste",sz=8,col=FAINT,it=True); r+=1
row_rv=r; put(r,1,"CA 1ʳᵉ année / inscrit",sz=10);        IN(r,2,7608,EUR);  put(r,3,"référentiel",sz=8,col=FAINT,it=True); r+=1
row_cv=r; put(r,1,"Coût variable / élève",sz=10);         IN(r,2,300,EUR);   put(r,3,"marginal, classe existante",sz=8,col=FAINT,it=True); r+=2
DE=f"$B${row_d}"; RV=f"$B${row_rv}"; CV=f"$B${row_cv}"
hr=r
head(hr,["Marque","L.pay24","L.pay26","Bud.24","Bud.26","Élasticité","Conv.","Δ budget",
         "Leads gagnés","Inscrits gagnés","CA gagné","EBITDA gagné","CAC marg."])
r=hr+1; e3=r
for b in BRAND:
    put(r,1,b['marque'],sz=9,b=True)
    put(r,2,b['p24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put(r,3,b['p26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,4,b['s24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put(r,5,b['s26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,20,b['lead26'],sz=8,al=RGT,fmt=NUM,col=FAINT)  # T lead26 réf
    put(r,21,b['new26'],sz=8,al=RGT,fmt=NUM,col=FAINT)   # U new26 réf
    put(r,6,f"=LN(C{r}/B{r})/LN(E{r}/D{r})",sz=9,b=True,col=TEALD,al=RGT,fmt=DEC3)   # F élast
    put(r,7,f"=U{r}/T{r}",sz=9,col=SOFT,al=RGT,fmt=PCT)                               # G conv
    put(r,8,f"=E{r}*{DE}",sz=9,col=OCHRED,al=RGT,fmt=EUR)                             # H Δbudget
    put(r,9,f"=C{r}*((1+{DE})^F{r}-1)",sz=9,al=RGT,fmt=NUM)                           # I leads gagnés
    put(r,10,f"=I{r}*G{r}",sz=9,al=RGT,fmt=NUM)                                       # J inscrits gagnés
    put(r,11,f"=J{r}*{RV}",sz=9,col=TEALD,al=RGT,fmt=EUR)                             # K CA gagné
    put(r,12,f"=K{r}-H{r}-J{r}*{CV}",sz=9,b=True,col=GREEN,al=RGT,fmt=EUR)            # L EBITDA
    put(r,13,f"=H{r}/J{r}",sz=9,col=NAVY,al=RGT,fmt=EUR)                              # M CAC marg
    for j in range(1,14): ws.cell(r,j).border=Border(bottom=thin)
    r+=1
l3=r-1
# total
put(r,1,"GROUPE",sz=10,b=True,col=TEALD)
for cc,fm in [(8,EUR),(9,NUM),(10,NUM),(11,EUR),(12,EUR)]:
    L=chr(64+cc)
    ws.cell(r,cc,f"=SUM({L}{e3}:{L}{l3})").number_format=fm; ws.cell(r,cc).font=F(10,True,TEALD); ws.cell(r,cc).alignment=RGT
ws.cell(r,13,f"=H{r}/J{r}").number_format=EUR; ws.cell(r,13).font=F(10,True,NAVY); ws.cell(r,13).alignment=RGT
for j in range(1,14): ws.cell(r,j).fill=fill(GREENBG); ws.cell(r,j).border=Border(top=med,bottom=med)
r+=2
put(r,1,"Change la case Δ (8 % → 12 %) : les 5 marques recalculent. La marque au CAC marginal le plus BAS mérite l'euro suivant → c'est ce qui ouvrira la question du cap (réallocation).",sz=9,b=True,col=OCHRE)

# largeurs
ws.column_dimensions['A'].width=22
for col in "BCDEFGHIJKLMN": ws.column_dimensions[col].width=10
for col in "RSTU": ws.column_dimensions[col].width=8
ws.freeze_panes="B4"
wb.calculation.fullCalcOnLoad=True
out="/home/user/demo5/eduservices/tagetik/LE_MOTEUR_MODELE.xlsx"
wb.save(out); print("SAVED",out)
