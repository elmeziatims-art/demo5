#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE_MOTEUR_MODELE.xlsx — modèle VIVANT du moteur (formules cliquables).
Paramètres en haut (Δ, CA/inscrit, coût var) pilotent tout.
① élasticité → leads → inscrits → CA gagné, PAR CAMPUS (piloté par Δ)
② back-test complet : paid ET organique PRÉDITS (calibré ≤2025) → inscrits 2026
③ décision PAR MARQUE : EBITDA gagné + CAC marginal (piloté par Δ)."""
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

D=json.load(open('/tmp/moteur_full.json')); CAMP=D['camp']; BRAND=D['brand']
INK="152230"; TEAL="0D7A62"; TEALD="0A5A48"; TEALBG="E2EFEB"
FAINT="7D8B98"; WHITE="FFFFFF"; OCHRE="B3641C"; OCHRED="8A4A12"
GREEN="1E7A55"; GREENBG="E4F0E8"; RULE="C8D2DA"; SOFT="51606D"; NAVY="3D4F8F"
INPUTBG="FFF6DA"; INPUTBD="D9B94A"
AR="Arial"
def F(sz=10,b=False,c=INK,it=False): return Font(name=AR,size=sz,bold=b,color=c,italic=it)
def fill(c): return PatternFill("solid",fgColor=c)
LFT=Alignment("left",vertical="center"); RGT=Alignment("right",vertical="center")
CTR=Alignment("center",vertical="center",wrap_text=True)
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
def head(r,cols):
    for j,h in enumerate(cols,1):
        c=ws.cell(r,j,h); c.font=F(8.5,True,WHITE); c.fill=fill(TEAL)
        c.alignment=LFT if j==1 else CTR; c.border=Border(bottom=med)
def IN(r,c,v,fmt):
    cell=ws.cell(r,c,v); cell.number_format=fmt; cell.alignment=RGT; cell.font=F(10,True,INK)
    cell.fill=fill(INPUTBG); cell.border=Border(top=inbd,bottom=inbd,left=inbd,right=inbd); return cell

put(1,1,"EDUSERVICES · budget 2027 · le moteur, à nu",sz=9,b=True,col=TEALD)
put(2,1,"Le moteur — données réelles + formules cliquables",sz=16,b=True)
put(3,1,"Jaune = actuals ou hypothèse (saisie). Tout le reste = formule. Changez une case jaune → tout recalcule.",sz=9,col=SOFT)

# ============================== PARAMÈTRES ==============================
put(5,1,"PARAMÈTRES  (les 3 leviers de lecture)",sz=11,b=True,col=OCHRED)
put(6,1,"Δ budget d'acquisition (le geste testé)",sz=10); IN(6,2,0.08,PCT); put(6,3,"passez 8 % → 12 %, tout suit",sz=8,col=FAINT,it=True)
put(7,1,"CA 1ʳᵉ année / inscrit",sz=10); IN(7,2,7608,EUR); put(7,3,"votre référentiel",sz=8,col=FAINT,it=True)
put(8,1,"Coût variable / élève",sz=10); IN(8,2,300,EUR); put(8,3,"marginal, classe existante",sz=8,col=FAINT,it=True)
DE="$B$6"; RV="$B$7"; CV="$B$8"

# ============================== ① ÉLASTICITÉ → CA (par campus) ==============================
put(10,1,"①  De l'élasticité au CA — par campus (piloté par Δ)",sz=12,b=True,col=TEALD)
put(11,1,"Élasticité = LN(leads pay.26 ÷ leads pay.24) ÷ LN(budget26 ÷ budget24). Puis : leads gagnés → inscrits → CA, pour le Δ ci-dessus.",sz=9,b=True,col=OCHRE,it=True)
hr=13
head(hr,["Campus","L.pay24","L.pay26","Bud.24","Bud.26","Élasticité","Leads 2026","Inscrits 2026","Conv.",
         "Leads gagnés","Inscrits gagnés","CA gagné (+Δ)"])
r=hr+1; e1=r
for d in CAMP:
    put(r,1,NAME[d['campus']],sz=9)
    put(r,2,d['p24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put(r,3,d['p26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,4,d['s24'],sz=9,al=RGT,fmt=EUR,bg=INPUTBG); put(r,5,d['s26'],sz=9,al=RGT,fmt=EUR,bg=INPUTBG)
    put(r,6,f"=LN(C{r}/B{r})/LN(E{r}/D{r})",sz=9,b=True,col=TEALD,al=RGT,fmt=DEC3)   # F élast
    lead26=d['p26']+d['o26']
    put(r,7,lead26,sz=9,al=RGT,fmt=NUM,bg=INPUTBG)                                    # G leads26 (actual)
    put(r,8,d['n26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)                                  # H inscrits26 (actual)
    put(r,9,f"=H{r}/G{r}",sz=9,col=SOFT,al=RGT,fmt=PCT)                               # I conv
    put(r,10,f"=C{r}*((1+{DE})^F{r}-1)",sz=9,al=RGT,fmt=NUM)                          # J leads gagnés (sur payants)
    put(r,11,f"=J{r}*I{r}",sz=9,al=RGT,fmt=NUM)                                       # K inscrits gagnés
    put(r,12,f"=K{r}*{RV}",sz=9,b=True,col=TEALD,al=RGT,fmt=EUR)                      # L CA gagné
    for j in range(1,13): ws.cell(r,j).border=Border(bottom=thin)
    r+=1
l1=r-1
put(r,1,"GROUPE",sz=9,b=True,col=TEALD)
for cc,fm in [(10,NUM),(11,NUM),(12,EUR)]:
    L=chr(64+cc); ws.cell(r,cc,f"=SUM({L}{e1}:{L}{l1})").number_format=fm; ws.cell(r,cc).font=F(9,True,TEALD); ws.cell(r,cc).alignment=RGT
for j in range(1,13): ws.cell(r,j).fill=fill(GREENBG); ws.cell(r,j).border=Border(top=med,bottom=med)
put(r+1,1,"Cliquez « Élasticité » : =LN(…)/LN(…) sur les chiffres réels. Cliquez « CA gagné » : la chaîne complète jusqu'au CA.",sz=8,col=FAINT,it=True)
r+=3

# ============================== ② BACK-TEST (paid + org prédits → inscrits) ==============================
put(r,1,"②  La preuve — back-test complet : leads payants ET organiques PRÉDITS, jusqu'aux inscrits",sz=12,b=True,col=TEALD); r+=1
put(r,1,"Rien de 2026 en entrée. Payants : élasticité 24→25 × budget26. Organiques : leur propre tendance 24→25. Puis × conversion 2025 → inscrits.",sz=9,col=SOFT,it=True); r+=2
hr=r
head(hr,["Campus","L.pay24","L.pay25","Bud.24","Bud.25","Bud.26","Élast 24→25","Préd. pay.26",
         "Org.24","Org.25","Préd. org.26","= Leads26 préd.","Leads25","Inscrits25","Conv.25","Inscrits26 préd.","Inscrits26 réel","Écart"])
r=hr+1; e2=r
for d in CAMP:
    put(r,1,NAME[d['campus']],sz=8)
    put(r,2,d['p24'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG); put(r,3,d['p25'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,4,d['s24'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG); put(r,5,d['s25'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG); put(r,6,d['s26'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,7,f"=LN(C{r}/B{r})/LN(E{r}/D{r})",sz=8,col=SOFT,al=RGT,fmt=DEC3)            # G élast24-25
    put(r,8,f"=C{r}*(F{r}/E{r})^G{r}",sz=8,col=NAVY,al=RGT,fmt=NUM)                   # H préd paid26
    put(r,9,d['o24'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG); put(r,10,d['o25'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG)  # I,J org24,25
    put(r,11,f"=J{r}*(J{r}/I{r})",sz=8,col=NAVY,al=RGT,fmt=NUM)                       # K préd org26 (tendance)
    put(r,12,f"=H{r}+K{r}",sz=8,b=True,col=NAVY,al=RGT,fmt=NUM)                       # L leads26 préd
    put(r,13,d['l25'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG); put(r,14,d['n25'],sz=8,al=RGT,fmt=NUM,bg=INPUTBG) # M,N leads25,new25
    put(r,15,f"=N{r}/M{r}",sz=8,col=SOFT,al=RGT,fmt=PCT)                              # O conv25
    put(r,16,f"=L{r}*O{r}",sz=8,b=True,col=NAVY,al=RGT,fmt=NUM)                       # P inscrits préd
    put(r,17,d['n26'],sz=8,al=RGT,fmt=NUM)                                            # Q réel
    put(r,18,f"=P{r}/Q{r}-1",sz=8,b=True,col=GREEN,al=RGT,fmt=SPCT)                   # R écart
    for j in range(1,19): ws.cell(r,j).border=Border(bottom=thin)
    r+=1
l2=r-1
put(r,1,"GROUPE",sz=9,b=True,col=TEALD)
for cc,fm in [(12,NUM),(16,NUM),(17,NUM)]:
    L=chr(64+cc); ws.cell(r,cc,f"=SUM({L}{e2}:{L}{l2})").number_format=fm; ws.cell(r,cc).font=F(9,True,TEALD); ws.cell(r,cc).alignment=RGT
ws.cell(r,18,f"=P{r}/Q{r}-1").number_format=SPCT; ws.cell(r,18).font=F(9,True,GREEN); ws.cell(r,18).alignment=RGT
for j in range(1,19): ws.cell(r,j).fill=fill(GREENBG); ws.cell(r,j).border=Border(top=med,bottom=med)
put(r+1,1,"Tout est prédit à partir de ≤2025 : le moteur retrouve les inscrits 2026 qu'il n'a jamais vus. (Données de démo → très serré ; en réel, quelques %.)",sz=8,col=OCHRE,it=True)
r+=3

# ============================== ③ DÉCISION PAR MARQUE ==============================
put(r,1,"③  L'effet d'un +Δ% d'acquisition — la décision, par marque",sz=12,b=True,col=TEALD); r+=1
put(r,1,"Même Δ que là-haut. On va jusqu'à l'EBITDA et au CAC marginal : la marque au CAC marginal le plus BAS mérite l'euro suivant (→ le cap).",sz=9,col=SOFT,it=True); r+=2
hr=r
head(hr,["Marque","L.pay24","L.pay26","Bud.24","Bud.26","Élasticité","Leads 2026","Inscrits 2026","Conv.",
         "Δ budget","Inscrits gagnés","CA gagné","EBITDA gagné","CAC marg."])
r=hr+1; e3=r
for b in BRAND:
    put(r,1,b['marque'],sz=9,b=True)
    put(r,2,b['p24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put(r,3,b['p26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,4,b['s24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put(r,5,b['s26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put(r,6,f"=LN(C{r}/B{r})/LN(E{r}/D{r})",sz=9,b=True,col=TEALD,al=RGT,fmt=DEC3)   # F élast
    put(r,7,b['lead26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)                               # G leads26
    put(r,8,b['new26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)                                # H inscrits26
    put(r,9,f"=H{r}/G{r}",sz=9,col=SOFT,al=RGT,fmt=PCT)                               # I conv
    put(r,10,f"=E{r}*{DE}",sz=9,col=OCHRED,al=RGT,fmt=EUR)                            # J Δbudget
    put(r,11,f"=C{r}*((1+{DE})^F{r}-1)*I{r}",sz=9,al=RGT,fmt=NUM)                     # K inscrits gagnés
    put(r,12,f"=K{r}*{RV}",sz=9,col=TEALD,al=RGT,fmt=EUR)                             # L CA gagné
    put(r,13,f"=L{r}-J{r}-K{r}*{CV}",sz=9,b=True,col=GREEN,al=RGT,fmt=EUR)            # M EBITDA
    put(r,14,f"=J{r}/K{r}",sz=9,col=NAVY,al=RGT,fmt=EUR)                              # N CAC marg
    for j in range(1,15): ws.cell(r,j).border=Border(bottom=thin)
    r+=1
l3=r-1
put(r,1,"GROUPE",sz=10,b=True,col=TEALD)
for cc,fm in [(10,EUR),(11,NUM),(12,EUR),(13,EUR)]:
    L=chr(64+cc); ws.cell(r,cc,f"=SUM({L}{e3}:{L}{l3})").number_format=fm; ws.cell(r,cc).font=F(10,True,TEALD); ws.cell(r,cc).alignment=RGT
ws.cell(r,14,f"=J{r}/K{r}").number_format=EUR; ws.cell(r,14).font=F(10,True,NAVY); ws.cell(r,14).alignment=RGT
for j in range(1,15): ws.cell(r,j).fill=fill(GREENBG); ws.cell(r,j).border=Border(top=med,bottom=med)
put(r+2,1,"Le CAC marginal diverge d'une marque à l'autre → c'est ce qui ouvre l'arbitrage du cap (réallouer vers les CAC marginaux les plus bas).",sz=9,b=True,col=OCHRE)

ws.column_dimensions['A'].width=22
for col in "BCDEFGHIJKLMNOPQR": ws.column_dimensions[col].width=9.5
ws.freeze_panes="B4"

# ================================================================
# ONGLET 2 — LE BUDGET DE MARQUE (ORGANIQUE), en miroir
# ================================================================
ORG=json.load(open('/tmp/moteur_org.json'))
w2=wb.create_sheet("Budget de marque (organique)")
w2.sheet_view.showGridLines=False
def put2(r,c,v,sz=10,b=False,col=INK,it=False,al=LFT,fmt=None,bg=None,box=None):
    cell=w2.cell(r,c,v); cell.font=F(sz,b,col,it); cell.alignment=al
    if fmt: cell.number_format=fmt
    if bg: cell.fill=fill(bg)
    if box: cell.border=box
    return cell
def head2(r,cols):
    for j,h in enumerate(cols,1):
        c=w2.cell(r,j,h); c.font=F(8.5,True,WHITE); c.fill=fill(TEAL); c.alignment=LFT if j==1 else CTR; c.border=Border(bottom=med)
put2(1,1,"EDUSERVICES · budget 2027 · le moteur, à nu",sz=9,b=True,col=TEALD)
put2(2,1,"Le budget de marque → les leads organiques",sz=16,b=True)
put2(3,1,"Même méthode que l'acquisition, autre levier : le budget de marque nourrit les leads ORGANIQUES (bouche-à-oreille, notoriété), avec sa propre élasticité — plus basse, car l'effet est plus diffus.",sz=9,col=SOFT)
# param
put2(5,1,"PARAMÈTRE",sz=11,b=True,col=OCHRED)
put2(6,1,"Δ budget de marque (le geste testé)",sz=10)
c=w2.cell(6,2,0.10); c.number_format=PCT; c.alignment=RGT; c.font=F(10,True,INK); c.fill=fill(INPUTBG); c.border=Border(top=inbd,bottom=inbd,left=inbd,right=inbd)
put2(6,3,"organique = jeu plus lent, effet plus faible",sz=8,col=FAINT,it=True)
DM="$B$6"
# BLOC A : élasticité marque + org gagnés
put2(8,1,"①  L'élasticité de marque — et ce qu'un +Δ% de budget de marque rapporte en leads",sz=12,b=True,col=TEALD)
put2(9,1,"Élasticité marque = LN(organiques 2026 ÷ organiques 2024) ÷ LN(budget marque 2026 ÷ budget marque 2024)",sz=9,b=True,col=OCHRE,it=True)
hr=11
head2(hr,["Campus","Bud. marque 24","Bud. marque 26","Organiques 24","Organiques 26","Élasticité marque","Org. gagnés (+Δ)"])
r=hr+1; ea=r
for d in ORG:
    put2(r,1,NAME[d['campus']],sz=9)
    put2(r,2,d['b24'],sz=9,al=RGT,fmt=EUR,bg=INPUTBG); put2(r,3,d['b26'],sz=9,al=RGT,fmt=EUR,bg=INPUTBG)
    put2(r,4,d['o24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put2(r,5,d['o26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put2(r,6,f"=LN(E{r}/D{r})/LN(C{r}/B{r})",sz=9,b=True,col=TEALD,al=RGT,fmt=DEC3)
    put2(r,7,f"=E{r}*((1+{DM})^F{r}-1)",sz=9,al=RGT,fmt=NUM)
    for j in range(1,8): w2.cell(r,j).border=Border(bottom=thin)
    r+=1
la=r-1
put2(r,1,"GROUPE",sz=9,b=True,col=TEALD)
w2.cell(r,7,f"=SUM(G{ea}:G{la})").number_format=NUM; w2.cell(r,7).font=F(9,True,TEALD); w2.cell(r,7).alignment=RGT
for j in range(1,8): w2.cell(r,j).fill=fill(GREENBG); w2.cell(r,j).border=Border(top=med,bottom=med)
put2(r+1,1,"Élasticité ~0,3 (vs ~0,5 pour l'acquisition) : le budget de marque agit, mais moins directement.",sz=8,col=FAINT,it=True)
r+=3
# BLOC B : back-test organique
put2(r,1,"②  La preuve — back-test organique (calibré 24→25, prédit 26)",sz=12,b=True,col=TEALD); r+=1
put2(r,1,"organiques 2026 prédits = organiques 2025 × (budget marque 2026 ÷ budget marque 2025) ^ élasticité(24→25)",sz=9,col=SOFT,it=True); r+=2
hr=r
head2(hr,["Campus","Org.24","Org.25","Bud.mq 24","Bud.mq 25","Bud.mq 26","Élast 24→25","Org.26 prédit","Org.26 réel","Écart"])
r=hr+1; eb=r
for d in ORG:
    put2(r,1,NAME[d['campus']],sz=9)
    put2(r,2,d['o24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put2(r,3,d['o25'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put2(r,4,d['b24'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put2(r,5,d['b25'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG); put2(r,6,d['b26'],sz=9,al=RGT,fmt=NUM,bg=INPUTBG)
    put2(r,7,f"=LN(C{r}/B{r})/LN(E{r}/D{r})",sz=9,col=SOFT,al=RGT,fmt=DEC3)
    put2(r,8,f"=C{r}*(F{r}/E{r})^G{r}",sz=9,b=True,col=NAVY,al=RGT,fmt=NUM)
    put2(r,9,d['o26'],sz=9,al=RGT,fmt=NUM)
    put2(r,10,f"=H{r}/I{r}-1",sz=9,b=True,col=GREEN,al=RGT,fmt=SPCT)
    for j in range(1,11): w2.cell(r,j).border=Border(bottom=thin)
    r+=1
lb=r-1
put2(r,1,"GROUPE",sz=9,b=True,col=TEALD)
w2.cell(r,8,f"=SUM(H{eb}:H{lb})").number_format=NUM; w2.cell(r,8).font=F(9,True,TEALD); w2.cell(r,8).alignment=RGT
w2.cell(r,9,f"=SUM(I{eb}:I{lb})").number_format=NUM; w2.cell(r,9).font=F(9,True,TEALD); w2.cell(r,9).alignment=RGT
w2.cell(r,10,f"=H{r}/I{r}-1").number_format=SPCT; w2.cell(r,10).font=F(9,True,GREEN); w2.cell(r,10).alignment=RGT
for j in range(1,11): w2.cell(r,j).fill=fill(GREENBG); w2.cell(r,j).border=Border(top=med,bottom=med)
put2(r+2,1,"Les deux leviers (acquisition + marque) alimentent le MÊME funnel. Total leads = payants + organiques → candidatures → inscrits → CA.",sz=9,b=True,col=OCHRE)
w2.column_dimensions['A'].width=22
for col in "BCDEFGHIJ": w2.column_dimensions[col].width=12
w2.freeze_panes="B4"

wb.calculation.fullCalcOnLoad=True
out="/home/user/demo5/eduservices/tagetik/LE_MOTEUR_MODELE.xlsx"
wb.save(out); print("SAVED",out)
