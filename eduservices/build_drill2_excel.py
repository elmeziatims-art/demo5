#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_drill2_excel.py — le drill 2, "de quoi cet EBITDA est-il fait".

CE QUI CHANGE : LE CHIFFRE D'AFFAIRES EST OUVERT EN TROIS COMPTES.

Il tenait sur une ligne, prise au socle CRM. Il en tient maintenant trois --
706 scolarite des initiaux, 7062 scolarite des alternants, 708 frais
d'inscription -- lues sur les comptes de produit comme les douze comptes de
charge. Le tableau est donc un VRAI compte d'exploitation : quinze lignes qui
sont toutes de vraies ecritures, plus le siege qui est une allocation et le
dit. Seize lignes.

C'est possible depuis le realignement du 06/09 : comptes de produit et socle
CRM disent le meme montant au centime. Le rapprochement du bas de page le
verifie a chaque ouverture, en lisant la restitution de Q_D3_CA_CRM.

LE TABLEAU NE CONTIENT AUCUNE VALEUR EN DUR. Il va chercher chaque ligne dans
la zone de restitution avec une RECHERCHEV sur le numero de compte. Le classeur
ne subit donc pas l'ordre de la requete : il le FIXE, par la sequence des
comptes en colonne B. Chaque formule est enveloppee dans un SIERREUR qui rend
0, donc un compte absent laisse une ligne a zero, jamais un #N/A.

ORDRE DE LECTURE :
  1  la reponse en une phrase
  2  le graphe : ou part l'argent, treize postes en barres horizontales
  3  le tableau : seize lignes, du chiffre d'affaires a l'EBITDA
  4  le controle, puis le rapprochement des deux chaines

openpyxl ecrit les noms de fonctions en ANGLAIS : c'est ce que stocke le format
OOXML. Excel affiche RECHERCHEV et SIERREUR a l'ouverture.
"""
import csv, openpyxl
from collections import defaultdict
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import CellIsRule, Rule, DataBarRule
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.chart.series import SeriesLabel
from openpyxl.utils import get_column_letter as GL

OUT="DRILL2_EXCEL.xlsx"; N,P=2026,2025
NAVY="172033"; SLATE="526071"; INK="202733"; MUTED="69778B"; ONDARK="B8C6DA"
CANVAS="F3F6FA"; PANEL="FFFFFF"; SEP="E9EDF3"; SOFT="EAF2FC"; PARENT="D9E2EF"
GOOD="1E9E89"; CRIT="D64545"; BLUE="2A78D6"; BLUE3="B8CFEC"
UI="Arial"; DISPLAY="Fira Sans Medium"
def F(sz=8.5,b=False,c=INK,i=False,f=None): return Font(name=f or UI,size=sz,bold=b,color=c,italic=i)
fill=lambda c: PatternFill("solid",fgColor=c)
sd=lambda c=SEP,st="thin": Side(style=st,color=c)
R=Alignment("right",vertical="center"); Cn=Alignment("center",vertical="center")
WRAP=Alignment("center",vertical="center",wrap_text=True)
ind=lambda n: Alignment("left",vertical="center",indent=n)

# ============================================================================
# CE QUE LES REQUETES RENVERRONT — simule ici pour que le classeur livre soit
# deja rempli. En production, Tagetik ecrase ces deux zones.
# ============================================================================
num=lambda v: float(v.replace(",",".")) if v else 0.0
lire=lambda n: list(csv.DictReader(open("data/"+n,encoding="utf-8-sig"),delimiter=";"))
cpt=defaultdict(lambda: defaultdict(float))
for r in lire("compta.csv"):
    ex=int(r["EXERCICE"])
    if ex in (P,N) and r["ENTITY"]!="GRP": cpt[r["ACCOUNT"]][ex]+=num(r["AMOUNT"])
from socle_reel import construire
C=construire()

#  Q_D2_SOCLE : quinze comptes signes, plus le siege
COMPTES=[("706", "Produits",     "Scolarité des étudiants en initial","Scolarité initial",    1),
         ("7062","Produits",     "Scolarité des alternants",          "Scolarité alternance", 1),
         ("708", "Produits",     "Frais d'inscription",               "Frais d'inscription",  1),
         ("621", "Coût variable","Personnel extérieur (vacataires)",  "Vacataires",          -1),
         ("604", "Coût variable","Achats d'études",                   "Achats d'études",     -1),
         ("6063","Coût variable","Fournitures",                       "Fournitures",         -1),
         ("6231","Coût variable","Publicité et acquisition",          "Acquisition",         -1),
         ("6411","Coûts directs","Salaires des permanents",           "Salaires",            -1),
         ("6413","Coûts directs","Primes",                            "Primes",              -1),
         ("645", "Coûts directs","Charges sociales",                  "Charges sociales",    -1),
         ("613", "Coûts directs","Loyers",                            "Loyers",              -1),
         ("615", "Coûts directs","Entretien",                         "Entretien",           -1),
         ("616", "Coûts directs","Assurances",                        "Assurances",          -1),
         ("625", "Coûts directs","Déplacements",                      "Déplacements",        -1),
         ("63511","Coûts directs","Taxes",                            "Taxes",               -1)]
S=lambda a,e: sum(c[a][e] for c in C)
RESTIT=[(a,f,l,ct,s*cpt[a][P],s*cpt[a][N]) for a,f,l,ct,s in COMPTES]
RESTIT+=[("SIEGE","Siège","Siège redescendu (allocation, pas une écriture)","Siège",
          -S("csiege",P),-S("csiege",N))]

#  Q_D3_CA_CRM : trois lignes, cote inducteurs
crm=defaultdict(lambda: defaultdict(float))
for r in lire("socle_crm.csv"):
    ex=int(r["EXERCICE"])
    if ex not in (P,N): continue
    a="7062" if r["MODALITE"]=="ALT" else "706"
    crm[a]["v%d"%ex]+=num(r["VOL_EFF"]); crm[a]["m%d"%ex]+=num(r["VOL_EFF"])*num(r["REV_STUD"])
    crm["708"]["v%d"%ex]+=num(r["VOL_NEW"]); crm["708"]["m%d"%ex]+=num(r["VOL_NEW"])*num(r["REV_FRAIS_INS"])
CRM=[(a,l,ct,u,crm[a]["v%d"%P],crm[a]["v%d"%N],crm[a]["m%d"%P],crm[a]["m%d"%N])
     for a,l,ct,u in (("706","Scolarité des étudiants en initial","Scolarité initial","Effectifs"),
                      ("7062","Scolarité des alternants","Scolarité alternance","Effectifs"),
                      ("708","Frais d'inscription","Frais d'inscription","Nouveaux inscrits"))]

# L'ORDRE D'AFFICHAGE — c'est le classeur qui le tient, plus la requete.
SEQUENCE=[a for a,_,_,_,_ in COMPTES]+["SIEGE"]
NPROD=3                                   # les trois premieres lignes sont des produits

# ============================================================================
# L'OSSATURE
# ============================================================================
ZONE0, ZONEN = 7, 28        # zone Q_D2_SOCLE : 22 emplacements pour 16 lignes
ZCRM0        = 31           # zone Q_D3_CA_CRM : trois lignes
ZC0, ZCN     = 14, 21       # colonnes N..U, masquees
GRAPH0, TAB0 = 8, 33
L0    = TAB0+1
LN    = L0+len(SEQUENCE)-1
CH0   = L0+NPROD            # premiere ligne de charge, debut du graphe
CTRL  = LN+2
ZR="$%s$%d:$%s$%d"%(GL(ZC0),ZONE0,GL(ZC0+5),ZONEN)     # $N$7:$S$28

wb=openpyxl.Workbook(); ws=wb.active; ws.title="Drill par compte"
ws.sheet_view.showGridLines=False
for col,w in (("A",2.5),("B",9),("C",16),("D",36),("E",15),("F",15),("G",14),("H",15)):
    ws.column_dimensions[col].width=w
for c in list(range(10,14))+list(range(ZC0,ZCN+1)):
    ws.column_dimensions[GL(c)].hidden=True
for r in range(1,CTRL+16):
    for c in range(1,10): ws.cell(r,c).fill=fill(CANVAS)
for r in (1,2,3):
    for c in range(1,10): ws.cell(r,c).fill=fill(NAVY)
ws.cell(2,2,"DE QUOI CET EBITDA EST-IL FAIT").font=F(15,True,"FFFFFF",f=DISPLAY)
ws.cell(2,2).alignment=ind(0)
ws.cell(3,2,"drill sur la cellule cliquée · 2026 contre 2025 · quinze comptes lus dans "
            "AW_002_000004_000001, plus le siège redescendu").font=F(8,False,ONDARK)
ws.cell(3,2).alignment=ind(0)
for r,h in ((1,8),(2,26),(3,15),(4,10),(5,24),(6,14),(7,8),(TAB0-1,20)): ws.row_dimensions[r].height=h

def entete(row,c0,titres,titre,note=""):
    t=ws.cell(row-1,c0,titre); t.font=F(10,True,INK,f=DISPLAY); t.alignment=ind(0)
    if note:
        x=ws.cell(row-1,c0+len(titres)-1,note+"  "); x.font=F(7.5,False,MUTED,i=True); x.alignment=R
    for j,lab in enumerate(titres):
        c=ws.cell(row,c0+j,lab); c.fill=fill(SLATE); c.font=F(8,True,"FFFFFF",f=DISPLAY)
        c.alignment=WRAP if j>2 else ind(1); c.border=Border(*[sd(SLATE)]*4)
    ws.row_dimensions[row].height=26

# ============================================================================
# LES DEUX ZONES DE RESTITUTION — colonnes N..T, masquees
# ============================================================================
for j,lab in enumerate(("Compte","Famille","Poste","Poste court","Montant 2025","Montant 2026")):
    ws.cell(ZONE0-1,ZC0+j,lab).font=F(8,True,MUTED)
for i,ligne in enumerate(RESTIT):
    for j,v in enumerate(ligne): ws.cell(ZONE0+i,ZC0+j,v)
for j,lab in enumerate(("Compte","Poste","Poste court","Unite comptee","Volume 2025",
                        "Volume 2026","Montant 2025","Montant 2026")):
    ws.cell(ZCRM0-1,ZC0+j,lab).font=F(8,True,MUTED)
for i,ligne in enumerate(CRM):
    for j,v in enumerate(ligne): ws.cell(ZCRM0+i,ZC0+j,v)

# ============================================================================
# 1. LA REPONSE, EN UNE PHRASE
# ============================================================================
ws.cell(5,2,'="Sur "&TEXT(SUM(F{p0}:F{p1}),"#,##0 €")&" de chiffre d\'affaires, "'
            '&TEXT(-SUM(F{c1}:F{cn}),"#,##0 €")&" partent en charges. '
            'Il reste "&TEXT(SUM(F{p0}:F{cn}),"#,##0 €")&" d\'EBITDA, soit "'
            '&TEXT(SUM(F{p0}:F{cn})/SUM(F{p0}:F{p1}),"0.0%")&" du chiffre d\'affaires."'
            .format(p0=L0,p1=L0+NPROD-1,c1=CH0,cn=LN)).font=F(13,True,INK,f=DISPLAY)
ws.cell(5,2).alignment=ind(0)
ws.cell(6,2,"les charges sont signées en négatif : leur somme avec les produits donne l'EBITDA")
ws.cell(6,2).font=F(8.5,False,MUTED,i=True); ws.cell(6,2).alignment=ind(0)

# ============================================================================
# 3. LE TABLEAU — seize lignes, aucune valeur en dur
# ============================================================================
entete(TAB0,2,("Compte","Famille","Poste","Montant 2025","Montant 2026",
               "Variation","Part des charges"),
       "LE COMPTE D'EXPLOITATION, POSTE PAR POSTE",
       "colonnes C à F lues dans la restitution par RECHERCHEV · G et H calculées ici")
V =lambda r,col: '=IFERROR(VLOOKUP($B{r},{z},{c},FALSE),0)'.format(r=r,z=ZR,c=col)
VT=lambda r,col: '=IFERROR(VLOOKUP($B{r},{z},{c},FALSE),"")'.format(r=r,z=ZR,c=col)
for i,code in enumerate(SEQUENCE):
    r=L0+i
    ws.cell(r,2,code)                       # LA CLE — elle fixe l'ordre
    ws.cell(r,3,VT(r,2)); ws.cell(r,4,VT(r,3))
    ws.cell(r,5,V(r,5));  ws.cell(r,6,V(r,6))
    ws.cell(r,7,"=F{0}-E{0}".format(r))
    ws.cell(r,8,'=IF($C{r}="Produits","",-F{r}/SUM(F{c1}:F{cn}))'.format(r=r,c1=CH0,cn=LN))
    ws.cell(r,10,VT(r,4))                   # Poste court, pour l'axe du graphe
    ws.cell(r,2).font=F(8.5,False,MUTED); ws.cell(r,2).alignment=Cn
    ws.cell(r,3).font=F(8.5,False,MUTED); ws.cell(r,3).alignment=ind(1)
    ws.cell(r,4).font=F(8.5);             ws.cell(r,4).alignment=ind(1)
    for c in (5,6):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format='#,##0" €"'
    x=ws.cell(r,7); x.font=F(8.5); x.alignment=R
    x.number_format='"▲ "#,##0;"▼ "#,##0;"—"'
    x=ws.cell(r,8); x.font=F(8.5); x.alignment=R; x.number_format='0.0%'
    ws.row_dimensions[r].height=15.5

# ---- sources du graphe : les treize postes de charge, en valeur absolue -----
for r in range(CH0,LN+1):
    ws.cell(r,11,"=-E%d"%r); ws.cell(r,12,"=-F%d"%r)
ws.cell(TAB0,11,"2025"); ws.cell(TAB0,12,"2026")

# ---- LES REGLES DE FOND, DANS L'ORDRE QUI COMPTE ---------------------------
# Excel retient la premiere regle qui pose une propriete donnee. Les deux
# regles SPECIFIQUES -- les produits et le siege -- passent donc AVANT la regle
# generique, sinon leur fond distinctif serait ecrase par le blanc.
for f_,fond in (('$C{0}="Produits"'.format(L0),PARENT),('$B{0}="SIEGE"'.format(L0),SOFT)):
    ws.conditional_formatting.add("B{0}:H{1}".format(L0,LN),Rule(type="expression",
        formula=[f_],dxf=DifferentialStyle(font=Font(bold=True),
        fill=PatternFill(bgColor=fond),border=Border(bottom=sd()))))
ws.conditional_formatting.add("B{0}:H{1}".format(L0,LN),Rule(type="expression",
    formula=['$B{0}<>""'.format(L0)],
    dxf=DifferentialStyle(fill=PatternFill(bgColor=PANEL),border=Border(bottom=sd()))))
ws.conditional_formatting.add("G{0}:G{1}".format(L0,LN),
    CellIsRule(operator="greaterThan",formula=["0"],font=Font(name=UI,size=8.5,color=GOOD)))
ws.conditional_formatting.add("G{0}:G{1}".format(L0,LN),
    CellIsRule(operator="lessThan",formula=["0"],font=Font(name=UI,size=8.5,color=CRIT)))
ws.conditional_formatting.add("H{0}:H{1}".format(L0,LN),
    DataBarRule(start_type="num",start_value=0,end_type="max",color="FF"+BLUE3,showValue=True))

# ============================================================================
# 4. LE CONTROLE
# ============================================================================
for c in range(2,9):
    x=ws.cell(CTRL,c); x.fill=fill(SOFT)
    x.border=Border(top=sd(SLATE,"medium"),bottom=sd(SLATE,"medium"))
ws.cell(CTRL,2,"Contrôle").font=F(8.5,True,MUTED); ws.cell(CTRL,2).alignment=ind(1)
ws.cell(CTRL,4,"la somme des seize lignes doit valoir l'EBITDA")
ws.cell(CTRL,4).font=F(8.5,True,MUTED); ws.cell(CTRL,4).alignment=ind(1)
for c in (5,6):
    x=ws.cell(CTRL,c,"=SUM({0}{1}:{0}{2})".format(GL(c),L0,LN))
    x.number_format='#,##0" €"'; x.alignment=R; x.font=F(11,True,BLUE)

# ============================================================================
# 4 bis. LE RAPPROCHEMENT DES DEUX CHAINES
# ============================================================================
REC=CTRL+3
ws.cell(REC-1,2,"RAPPROCHEMENT DU CHIFFRE D'AFFAIRES  ·  comptes de produit contre socle CRM")
ws.cell(REC-1,2).font=F(10,True,INK,f=DISPLAY); ws.cell(REC-1,2).alignment=ind(0)
ws.row_dimensions[REC-1].height=20
CRMS=lambda c: "=SUM(${0}${1}:${0}${2})".format(GL(ZC0+c),ZCRM0,ZCRM0+2)
for j,(lab,f25,f26) in enumerate((
        ("Comptes de produit  ·  706 + 7062 + 708, somme des trois lignes ci-dessus",
         "=SUM(E{0}:E{1})".format(L0,L0+NPROD-1),"=SUM(F{0}:F{1})".format(L0,L0+NPROD-1)),
        ("Socle CRM  ·  effectifs × droits de scolarité, restitution de Q_D3_CA_CRM",
         CRMS(6),CRMS(7)))):
    r=REC+j
    for c in range(2,9): ws.cell(r,c).fill=fill(PANEL); ws.cell(r,c).border=Border(bottom=sd())
    ws.cell(r,2,lab).font=F(8.5); ws.cell(r,2).alignment=ind(1)
    for c,v in ((5,f25),(6,f26)):
        x=ws.cell(r,c,v); x.number_format='#,##0" €"'; x.alignment=R; x.font=F(8.5)
r=REC+2
for c in range(2,9): ws.cell(r,c).fill=fill(SOFT); ws.cell(r,c).border=Border(bottom=sd(SLATE,"medium"))
ws.cell(r,2,"Écart").font=F(8.5,True); ws.cell(r,2).alignment=ind(1)
for c in (5,6):
    x=ws.cell(r,c,"={0}{1}-{0}{2}".format(GL(c),REC,REC+1))
    x.number_format='+#,##0" €";-#,##0" €";"0 €"'; x.alignment=R; x.font=F(9,True,BLUE)
for c in (7,8):
    x=ws.cell(r,c,"={0}{1}/{0}{2}".format(GL(c-2),r,REC+1))
    x.number_format='+0.00%;-0.00%;"0,00 %"'; x.alignment=R; x.font=F(8.5,False,MUTED)
for j,txt in enumerate((
   "Les deux chaînes disent le même montant depuis le réalignement du 06/09. Cet écart doit rester à zéro ; s'il reparaît, c'est que le socle CRM a bougé sans que les comptes de produit suivent — FIX_CA_COMPTA_2024_2025.sql les remet d'accord.",
   "C'est ce qui permet d'ouvrir le chiffre d'affaires en trois comptes ici : le tableau est un vrai compte d'exploitation, quinze lignes qui sont toutes de vraies écritures, plus le siège qui est une allocation et le dit.",
   "Le modèle continue de piloter par le CRM, et pour deux raisons qui ne tiennent pas à l'exactitude. Le GRAIN — 180 lignes campus × programme × année × modalité contre 105 au grain campus × compte, sans quoi aucune marge par programme n'est calculable.",
   "Et le PILOTAGE — le CRM donne le CA comme un produit d'inducteurs, effectifs × droits de scolarité, donc il se simule. Un montant déjà posé est un constat. DRILL3 ouvre cette chaîne-là.")):
    c=ws.cell(REC+4+j,2,txt); c.font=F(8,False,MUTED,i=True); c.alignment=ind(1)

# ============================================================================
# 2. LE GRAPHE
# ============================================================================
bc=BarChart(); bc.type="bar"; bc.grouping="clustered"; bc.gapWidth=45; bc.overlap=-15
for c in (11,12):
    bc.add_data(Reference(ws,min_col=c,max_col=c,min_row=CH0,max_row=LN),titles_from_data=False)
for s,coul,nom in zip(bc.series,(BLUE3,BLUE),("2025","2026")):
    s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
    s.tx=SeriesLabel(v=nom)
for s in bc.series:
    s.cat=AxDataSource(strRef=StrRef(f="'Drill par compte'!$J${0}:$J${1}".format(CH0,LN)))
bc.legend.position="b"; bc.x_axis.numFmt='#,##0," k€"'
bc.height=12.5; bc.width=21; bc.visible_cells_only=False
bc.x_axis.delete=False; bc.y_axis.delete=False
bc.x_axis.majorTickMark="none"; bc.y_axis.majorTickMark="none"
ws.add_chart(bc,"B%d"%GRAPH0)
for r in range(GRAPH0,TAB0-1): ws.row_dimensions[r].height=15
wb.save(OUT)
print("%s ecrit"%OUT)
print("  1 réponse       B5")
print("  2 graphe        B%d — treize postes de charge, 2025 contre 2026"%GRAPH0)
print("  3 tableau       B%d:H%d — %d lignes dont %d comptes de produit, zéro valeur en dur"
      %(TAB0,LN,len(SEQUENCE),NPROD))
print("  4 contrôle      E%d et F%d"%(CTRL,CTRL))
print("  5 rapprochement B%d:H%d"%(REC-1,REC+7))
print("  zone Q_D2_SOCLE   %s"%ZR.replace("$",""))
print("  zone Q_D3_CA_CRM  %s%d:%s%d"%(GL(ZC0),ZCRM0,GL(ZC0+7),ZCRM0+2))
