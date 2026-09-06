#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_drill2_excel.py — le drill 2, "de quoi cet EBITDA est-il fait".

Meme logique que le drill 1 : la requete somme, le classeur met en forme et
controle, et l'ordre de lecture repond avant de prouver.

  1  la reponse en une phrase
  2  le graphe : ou part l'argent, treize postes en barres horizontales
  3  le tableau : quatorze lignes, du chiffre d'affaires a l'EBITDA
  4  le controle

Le graphe est volontairement DIFFERENT de celui du drill 1. Une cascade y
disait une variation ; ici on montre une composition, et deux cascades de
suite dans une demo se ressemblent trop pour qu'on distingue les deux
questions.
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
from socle_reel import construire, CPT_VAR, CPT_DIRECT

OUT="DRILL2_EXCEL.xlsx"; N,P=2026,2025
NAVY="172033"; SLATE="526071"; INK="202733"; MUTED="69778B"; ONDARK="B8C6DA"
CANVAS="F3F6FA"; PANEL="FFFFFF"; SEP="E9EDF3"; SOFT="EAF2FC"; PARENT="D9E2EF"
GOOD="1E9E89"; CRIT="D64545"; BLUE="2A78D6"; BLUE3="B8CFEC"; ORANGE="F07B32"
UI="Arial"; DISPLAY="Fira Sans Medium"
def F(sz=8.5,b=False,c=INK,i=False,f=None): return Font(name=f or UI,size=sz,bold=b,color=c,italic=i)
fill=lambda c: PatternFill("solid",fgColor=c)
sd=lambda c=SEP,st="thin": Side(style=st,color=c)
R=Alignment("right",vertical="center"); Cn=Alignment("center",vertical="center")
WRAP=Alignment("center",vertical="center",wrap_text=True)
ind=lambda n: Alignment("left",vertical="center",indent=n)

# ---------------------------------------------- ce que Q_D2_SOCLE renverra
C=construire()
cpt=defaultdict(lambda: defaultdict(float))
for r in csv.DictReader(open("data/compta.csv",encoding="utf-8-sig"),delimiter=";"):
    ex=int(r["EXERCICE"])
    if ex in (P,N) and r["ENTITY"]!="GRP": cpt[r["ACCOUNT"]][ex]+=float(r["AMOUNT"])
POSTES=[(2,"Coût variable","621","Personnel extérieur (vacataires)","Vacataires"),
        (3,"Coût variable","604","Achats d'études","Achats d'études"),
        (4,"Coût variable","6063","Fournitures","Fournitures"),
        (5,"Coût variable","6231","Publicité et acquisition","Acquisition"),
        (6,"Coûts directs","6411","Salaires des permanents","Salaires"),
        (7,"Coûts directs","6413","Primes","Primes"),
        (8,"Coûts directs","645","Charges sociales","Charges sociales"),
        (9,"Coûts directs","613","Loyers","Loyers"),
        (10,"Coûts directs","615","Entretien","Entretien"),
        (11,"Coûts directs","616","Assurances","Assurances"),
        (12,"Coûts directs","625","Déplacements","Déplacements"),
        (13,"Coûts directs","63511","Taxes","Taxes")]
S=lambda a,e: sum(c[a][e] for c in C)
LIGNES=[(1,"Produits","","Chiffre d'affaires (socle CRM)","Chiffre d'affaires",S("ca",P),S("ca",N))]
LIGNES+=[(r,f,a,l,ct,-cpt[a][P],-cpt[a][N]) for r,f,a,l,ct in POSTES]
LIGNES+=[(14,"Siège","","Siège redescendu (allocation, pas une écriture)","Siège",
          -S("csiege",P),-S("csiege",N))]
CA_CPT={e:sum(v for a,d in cpt.items() if a.startswith("7") for x,v in d.items() if x==e)
        for e in (P,N)}

# ------------------------------------------------------------- l'ossature
GRAPH0, TAB0 = 8, 33
L0    = TAB0+1              # premiere ligne de donnees
LN    = L0+13               # QUATORZE lignes, ni plus ni moins : la liste des
                            # comptes est ecrite dans la query, pas decouverte
                            # dans la donnee, donc le compte est connu d'avance
CTRL  = LN+2
wb=openpyxl.Workbook(); ws=wb.active; ws.title="Drill par compte"
ws.sheet_view.showGridLines=False
for col,w in (("A",2.5),("B",5),("C",16),("D",9),("E",34),("F",15),("G",15),("H",14),("I",14)):
    ws.column_dimensions[col].width=w
for c in (11,12,13): ws.column_dimensions[GL(c)].hidden=True    # sources du graphe
for r in range(1,CTRL+16):
    for c in range(1,11): ws.cell(r,c).fill=fill(CANVAS)
for r in (1,2,3):
    for c in range(1,11): ws.cell(r,c).fill=fill(NAVY)
ws.cell(2,2,"DE QUOI CET EBITDA EST-IL FAIT").font=F(15,True,"FFFFFF",f=DISPLAY)
ws.cell(2,2).alignment=ind(0)
ws.cell(3,2,"drill sur la cellule cliquée · 2026 contre 2025 · comptes lus dans "
            "AW_002_000004_000001, CA reconstruit dans le socle CRM").font=F(8,False,ONDARK)
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

# ---------------------------------------- 1. la reponse, en une phrase
ws.cell(5,2,'="Sur "&TEXT(G{0},"#,##0 €")&" de chiffre d\'affaires, "'
            '&TEXT(-SUM(G{1}:G{2}),"#,##0 €")&" partent en charges. '
            'Il reste "&TEXT(SUM(G{0}:G{2}),"#,##0 €")&" d\'EBITDA, soit "'
            '&TEXT(SUM(G{0}:G{2})/G{0},"0.0%")&" du chiffre d\'affaires."'
            .format(L0,L0+1,LN)).font=F(13,True,INK,f=DISPLAY)
ws.cell(5,2).alignment=ind(0)
ws.cell(6,2,"les charges ci-dessous sont signées en négatif : leur somme avec le CA donne l'EBITDA")
ws.cell(6,2).font=F(8.5,False,MUTED,i=True); ws.cell(6,2).alignment=ind(0)

# ---------------------------------------- 3. le tableau, quatorze lignes
entete(TAB0,2,("Rang","Famille","Compte","Poste","Montant 2025","Montant 2026",
               "Variation","Part des charges"),
       "LE COMPTE D'EXPLOITATION, POSTE PAR POSTE",
       "ce que la requête renvoie · les deux dernières colonnes sont calculées")
for i,(rg,fam,cp,lab,court,m25,m26) in enumerate(LIGNES):
    r=L0+i
    for col,v in zip(range(2,8),(rg,fam,cp,lab,m25,m26)): ws.cell(r,col,v)
    ws.cell(r,11,court)                      # le libelle court, pour l'axe
for r in range(L0,LN+1):
    ws.cell(r,2).font=F(7.5,False,MUTED); ws.cell(r,2).alignment=Cn
    ws.cell(r,3).font=F(8.5,False,MUTED); ws.cell(r,3).alignment=ind(1)
    ws.cell(r,4).font=F(8.5,False,MUTED); ws.cell(r,4).alignment=Cn
    ws.cell(r,5).font=F(8.5); ws.cell(r,5).alignment=ind(1)
    for c in (6,7):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format='#,##0" €"'
    x=ws.cell(r,8,"=IF(F{0}=0,\"\",G{0}-F{0})".format(r) if ws.cell(r,2).value else None)
    x.font=F(8.5); x.alignment=R; x.number_format='"▲ "#,##0;"▼ "#,##0;"—"'
    x=ws.cell(r,9,"=IF(OR(B{0}=\"\",B{0}=1),\"\",-G{0}/SUM(G{1}:G{2}))".format(r,L0+1,LN)
                  if ws.cell(r,2).value else None)
    x.font=F(8.5); x.alignment=R; x.number_format='0.0%'
    ws.row_dimensions[r].height=15.5
    # sources du graphe : le poste et les deux montants en valeur absolue
    if ws.cell(r,2).value and rg not in (1,):
        pass

# ---- sources du graphe : les treize postes de charge, en valeur absolue ----
# Plus aucun NA() ni emplacement vide : la structure comptable est stable, donc
# la plage du graphe l'est aussi. C'est ce qui creait les trous a l'ecran.
for i in range(1,len(LIGNES)):
    r=L0+i
    ws.cell(r,12,"=-F%d"%r); ws.cell(r,13,"=-G%d"%r)
ws.cell(TAB0,12,"2025"); ws.cell(TAB0,13,"2026")

# ---- LES REGLES DE FOND, DANS L'ORDRE QUI COMPTE ----------------------------
# Excel retient la premiere regle qui pose une propriete donnee. Les deux
# regles SPECIFIQUES -- le chiffre d'affaires et le siege, qui sont des lignes
# calculees et non des ecritures -- passent donc AVANT la regle generique,
# sinon leur fond distinctif serait ecrase par le blanc.
for f_,fond in (('$B{0}=1'.format(L0),PARENT),('$B{0}=14'.format(L0),SOFT)):
    ws.conditional_formatting.add("B{0}:I{1}".format(L0,LN),Rule(type="expression",
        formula=[f_],dxf=DifferentialStyle(font=Font(bold=True),
        fill=PatternFill(bgColor=fond),border=Border(bottom=sd()))))
# puis la generique : une ligne servie prend fond blanc et filet, une ligne
# vide ne prend rien et se confond avec le fond de page
ws.conditional_formatting.add("B{0}:I{1}".format(L0,LN),Rule(type="expression",
    formula=['$B{0}<>""'.format(L0)],
    dxf=DifferentialStyle(fill=PatternFill(bgColor=PANEL),border=Border(bottom=sd()))))
ws.conditional_formatting.add("H{0}:H{1}".format(L0,LN),
    CellIsRule(operator="greaterThan",formula=["0"],font=Font(name=UI,size=8.5,color=GOOD)))
ws.conditional_formatting.add("H{0}:H{1}".format(L0,LN),
    CellIsRule(operator="lessThan",formula=["0"],font=Font(name=UI,size=8.5,color=CRIT)))
ws.conditional_formatting.add("I{0}:I{1}".format(L0,LN),
    DataBarRule(start_type="num",start_value=0,end_type="num",end_value=0.30,
                color="FF"+BLUE3,showValue=True))

# ---------------------------------------- 4. le controle
for c in range(2,10):
    x=ws.cell(CTRL,c); x.fill=fill(SOFT)
    x.border=Border(top=sd(SLATE,"medium"),bottom=sd(SLATE,"medium"))
ws.cell(CTRL,2,"Contrôle").font=F(8.5,True,MUTED); ws.cell(CTRL,2).alignment=ind(1)
ws.cell(CTRL,5,"la somme des quatorze lignes doit valoir l'EBITDA")
ws.cell(CTRL,5).font=F(8.5,True,MUTED); ws.cell(CTRL,5).alignment=ind(1)
for c,ex in ((6,P),(7,N)):
    x=ws.cell(CTRL,c,"=SUM({0}{1}:{0}{2})".format(GL(c),L0,LN))
    x.number_format='#,##0" €"'; x.alignment=R; x.font=F(11,True,BLUE)

# ------------------------------ 4 bis. le rapprochement du chiffre d'affaires
# La question tombe toujours : pourquoi le CA vient-il du CRM et non de la
# compta ? On met les deux cote a cote, l'ecart se voit et la reponse se donne
# toute seule.
REC=CTRL+3
ws.cell(REC-1,2,"POURQUOI LE CHIFFRE D'AFFAIRES VIENT DU SOCLE CRM")
ws.cell(REC-1,2).font=F(10,True,INK,f=DISPLAY); ws.cell(REC-1,2).alignment=ind(0)
ws.row_dimensions[REC-1].height=20
for j,(lab,v25,v26) in enumerate((
        ("Chiffre d'affaires en comptabilité  ·  706 + 7062 + 708",CA_CPT[P],CA_CPT[N]),
        ("Chiffre d'affaires du socle CRM  ·  effectifs × droits de scolarité",
         S("ca",P),S("ca",N)))):
    r=REC+j
    for c in range(2,10): ws.cell(r,c).fill=fill(PANEL); ws.cell(r,c).border=Border(bottom=sd())
    ws.cell(r,2,lab).font=F(8.5); ws.cell(r,2).alignment=ind(1)
    for c,v in ((6,v25),(7,v26)):
        x=ws.cell(r,c,v); x.number_format='#,##0" €"'; x.alignment=R; x.font=F(8.5)
r=REC+2
for c in range(2,10): ws.cell(r,c).fill=fill(SOFT); ws.cell(r,c).border=Border(bottom=sd(SLATE,"medium"))
ws.cell(r,2,"Écart").font=F(8.5,True); ws.cell(r,2).alignment=ind(1)
for c in (6,7):
    x=ws.cell(r,c,"={0}{1}-{0}{2}".format(GL(c),REC,REC+1))
    x.number_format='+#,##0" €";-#,##0" €";"0 €"'; x.alignment=R; x.font=F(9,True,BLUE)
ws.cell(r,8,"={0}{1}/{0}{2}".format("F",r,REC+1)).number_format='+0.00%;-0.00%;"0,00 %"'
ws.cell(r,8).alignment=R; ws.cell(r,8).font=F(8.5,False,MUTED)
ws.cell(r,9,"={0}{1}/{0}{2}".format("G",r,REC+1)).number_format='+0.00%;-0.00%;"0,00 %"'
ws.cell(r,9).alignment=R; ws.cell(r,9).font=F(8.5,False,MUTED)
for j,txt in enumerate((
   "Les deux disent la même chose. Le modèle prend le CRM pour deux raisons qui ne tiennent pas à l'exactitude :",
   "le GRAIN — 180 lignes campus × programme × année × modalité contre 105 au grain campus × compte, sans quoi aucune marge par programme n'est calculable ;",
   "le PILOTAGE — le CRM donne le CA comme un produit d'inducteurs, effectifs × droits de scolarité, donc il se simule. Un montant comptable est un constat.")):
    c=ws.cell(REC+4+j,2,txt); c.font=F(8,False,MUTED,i=True); c.alignment=ind(1)

# ---------------------------------------- 2. le graphe
bc=BarChart(); bc.type="bar"; bc.grouping="clustered"; bc.gapWidth=45; bc.overlap=-15
for c in (12,13):
    bc.add_data(Reference(ws,min_col=c,max_col=c,min_row=L0+1,max_row=LN),titles_from_data=False)
for s,coul,nom in zip(bc.series,(BLUE3,BLUE),("2025","2026")):
    s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
    s.tx=SeriesLabel(v=nom)
for s in bc.series:
    s.cat=AxDataSource(strRef=StrRef(f="'Drill par compte'!$K${0}:$K${1}".format(L0+1,LN)))
bc.legend.position="b"; bc.x_axis.numFmt='#,##0," k€"'
bc.height=12.5; bc.width=21; bc.visible_cells_only=False
bc.x_axis.delete=False; bc.y_axis.delete=False
bc.x_axis.majorTickMark="none"; bc.y_axis.majorTickMark="none"
ws.add_chart(bc,"B%d"%GRAPH0)
for r in range(GRAPH0,TAB0-1): ws.row_dimensions[r].height=15
wb.save(OUT)
print("%s ecrit"%OUT)
print("  1 réponse   B5")
print("  2 graphe    B%d — treize postes, barres horizontales, 2025 contre 2026"%GRAPH0)
print("  3 tableau   B%d:I%d, %d lignes servies sur %d emplacements"%(TAB0,LN,len(LIGNES),LN-L0+1))
print("  4 contrôle  F%d et G%d"%(CTRL,CTRL))
print("  5 rapprochement du CA  B%d:I%d"%(REC-1,REC+6))
print("  sources du graphe : K, L, M masquées")
