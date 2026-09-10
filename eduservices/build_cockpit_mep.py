#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_cockpit_mep.py — mise en page du rapport Tagetik COCKPIT_nav541.

Relit l'export Tagetik et en produit une copie mise en forme, sans toucher a
une seule formule ni a une seule valeur. A relancer apres chaque rafraichi.

Le point dur : le nombre de lignes d'entites change avec le filtre. La mise en
forme de la hierarchie ne peut donc PAS etre posee ligne par ligne. Elle est
entierement conditionnelle, pilotee par la colonne C que Saad a ajoutee :

    C = 2  groupe    fond bleu-gris soutenu, gras
    C = 3  marque    fond bleu pale, gras, libelle decale de 2 espaces
    C = 4  campus    fond blanc, normal, libelle decale de 6 espaces

Le decalage passe par le FORMAT DE NOMBRE de la regle conditionnelle
('"      "@'), parce qu'Excel ne sait pas piloter l'indentation par une regle
mais sait piloter le format. Les plages vont jusqu'a la ligne 200 : la mise en
forme suit l'ouverture d'un noeud sans qu'on y retouche.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.styles.numbers import NumberFormat
from openpyxl.formatting.rule import Rule, CellIsRule, DataBarRule
from openpyxl.chart import BarChart, LineChart, Reference, Series
from openpyxl.chart.marker import Marker
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.chart.series import SeriesLabel
from openpyxl.utils import get_column_letter as gl

SRC="COCKPIT_nav541.xlsx"; OUT="COCKPIT_nav541_MEP.xlsx"
FIN=200   # derniere ligne couverte par la mise en forme dynamique

# palette : .claude/skills/cfo-executive-dataviz/assets/reference-cockpit.xlsx
NAVY="172033"; BLUE="2A78D6"; BLUE2="6FA5DC"; BLUE3="B8CFEC"
SLATE="526071"; INK="202733"; MUTED="69778B"; ONDARK="B8C6DA"
CANVAS="F3F6FA"; PANEL="FFFFFF"; SOFT="EAF2FC"; PARENT="D9E2EF"; SEP="E9EDF3"; WARM="FFF1E8"
GOOD="1E9E89"; WARN="B97800"; CRIT="D64545"; ORANGE="F07B32"
UI="Arial"; DISPLAY="Fira Sans Medium"
def F(sz=8.5,b=False,c=INK,i=False,f=None): return Font(name=f or UI,size=sz,bold=b,color=c,italic=i)
def fill(c): return PatternFill("solid",fgColor=c)
def sd(c=SEP,st="thin"): return Side(style=st,color=c)
L=Alignment("left",vertical="center"); R=Alignment("right",vertical="center")
Cn=Alignment("center",vertical="center")
def ind(n): return Alignment("left",vertical="center",indent=n)

wb=openpyxl.load_workbook(SRC); ws=wb["2"]
ws.sheet_view.showGridLines=False

# ---------------------------------------------------------------- la grille
# C etroit (le niveau), D large (les libelles, 33 caracteres au plus long),
# E..P uniformes : six cartes de KPI de deux colonnes, toutes de meme largeur.
ws.column_dimensions["A"].width=2.5; ws.column_dimensions["B"].width=2.5
ws.column_dimensions["C"].width=4.5; ws.column_dimensions["D"].width=34
for c in range(5,17): ws.column_dimensions[gl(c)].width=11.0
for c in range(17,59): ws.column_dimensions[gl(c)].hidden=True   # zone technique
for r in range(1,FIN+1):
    for c in range(1,17): ws.cell(r,c).fill=fill(CANVAS)

# ---------------------------------------------------------------- bandeau
for r in (1,2,3):
    for c in range(1,17): ws.cell(r,c).fill=fill(NAVY)
t=ws.cell(2,3,"COCKPIT EDUSERVICES — PILOTAGE DE LA MARGE"); t.font=F(15,True,"FFFFFF",f=DISPLAY); t.alignment=ind(0)
u=ws.cell(3,3,"Exercice 2026 · variation contre 2025 · source V_ALLOCATION et socle CRM"); u.font=F(8,False,ONDARK); u.alignment=ind(0)
for r,h in ((1,8),(2,26),(3,15),(4,6),(5,20),(6,6),(7,10),(8,13),(9,26),(10,14),(11,10),(31,20),(32,17)):
    ws.row_dimensions[r].height=h
for r in range(12,31): ws.row_dimensions[r].height=17.5
for r in range(33,FIN+1): ws.row_dimensions[r].height=15.5

# ---------------------------------------------------------------- filtres
for c in range(3,17):
    x=ws.cell(5,c); x.fill=fill(SOFT)
    x.border=Border(top=sd(BLUE3),bottom=sd(BLUE3))
for col,lab in ((3,"SCÉNARIO"),(6,"VERSION"),(9,"MARQUE"),(12,"CAMPUS")):
    a=ws.cell(5,col); a.value=lab; a.font=F(7.5,True,SLATE); a.alignment=ind(1)
    b=ws.cell(5,col+1); b.font=F(9,True,INK); b.alignment=L

# ---------------------------------------------------------------- les six KPI
# On deplace les cartes sur la grille reguliere E..P sans changer une formule :
# chacune garde exactement le calcul qu'elle avait, seule son adresse bouge.
KPI=[(5,"CHIFFRE D'AFFAIRES","=E33",'0.0,," M€"',        "=F33",'"+"0.0%;"-"0.0%;"—"',        "bon"),
     (7,"EBITDA",            "=G33",'0.0,," M€"',        "=H33",'"+"0.0%;"-"0.0%;"—"',        "bon"),
     (9,"MARGE EBITDA",      "=J33",'0.0%',              "=K33",'"+"0.00" pt";"-"0.00" pt";"—"',"bon"),
     (11,"INSCRITS (NOUVEAUX)","=L33",'#,##0',           "=Z33",'"+"0.0%;"-"0.0%;"—"',        "bon"),
     (13,"COÛT D'ACQUISITION","=T33/L33",'#,##0" €"',
         '=IFERROR(M9/(U33/X33)-1,"")','"+"0.0%;"-"0.0%;"—"',                                  "mauvais"),
     (15,"REMPLISSAGE MOYEN", "=M33",'0.0%',             "=P33-O33",'#,##0" places libres"',   "neutre")]
for r in (8,9,10):
    for c in range(3,17): ws.cell(r,c).value=None
for col,lab,val,fmt,var,vfmt,sens in KPI:
    for c in (col,col+1):
        for r in (8,9,10):
            x=ws.cell(r,c); x.fill=fill(PANEL)
            x.border=Border(top=sd(SEP) if r==8 else None,bottom=sd(SEP) if r==10 else None,
                            left=sd(SEP) if c==col else None,right=sd(SEP) if c==col+1 else None)
    a=ws.cell(8,col,lab); a.font=F(7.5,True,SLATE); a.alignment=ind(1)
    v=ws.cell(9,col,val); v.font=F(18,True,INK,f=DISPLAY); v.number_format=fmt; v.alignment=ind(1)
    d=ws.cell(10,col,var); d.font=F(8.5,True,MUTED); d.number_format=vfmt; d.alignment=ind(1)
    ws.cell(10,col).comment=None

# ---------------------------------------------------------------- libelles fautifs
# La query renvoyait ses libelles en litteraux prefixes N, prefixe que le canal
# du loader ne conserve pas : "Activit?" et "Co?ts" sont arrives ainsi dans la
# zone technique. On les retablit ici, la correction cote SQL est deja faite.
for r in range(6,14):
    v=ws.cell(r,29).value
    if isinstance(v,str):
        ws.cell(r,29).value=v.replace("Activit?","Activité").replace("Co?ts","Coûts")

# ---------------------------------------------------------------- le tableau
ENTETES={5:"CA",6:"Δ CA",7:"EBITDA",8:"Δ EBITDA",9:"Part EBITDA",10:"Marge EBITDA",
         11:"Δ Marge (pt)",12:"Inscrits",13:"Remplissage",14:"Mix alternance",
         15:"Effectifs",16:"Places"}
s=ws.cell(31,3,"PORTEFEUILLE — MARQUE ET CAMPUS"); s.font=F(10,True,INK,f=DISPLAY); s.alignment=ind(0)
h=ws.cell(31,5,"le retrait du libellé donne le niveau : groupe, marque, campus"); h.font=F(7.5,False,MUTED,i=True); h.alignment=L
for c in range(3,17):
    x=ws.cell(32,c); x.fill=fill(SLATE)
    x.font=F(8,True,"FFFFFF",f=DISPLAY)
    x.alignment=Cn if c>=5 else ind(1)
    x.border=Border(top=sd(SLATE),bottom=sd(SLATE),left=sd(SLATE),right=sd(SLATE))
ws.cell(32,3).value="Niv."; ws.cell(32,3).alignment=Cn
ws.cell(32,4).value="Entité"
for c,lab in ENTETES.items(): ws.cell(32,c).value=lab

FMT={5:'#,##0',6:'"+"0.0%;"-"0.0%;""',7:'#,##0',8:'"+"0.0%;"-"0.0%;""',9:'0.0%',
     10:'0.0%',11:'"+"0.00;"-"0.00;""',12:'#,##0',13:'0.0%',14:'0.0%',15:'#,##0',16:'#,##0'}
for r in range(33,FIN+1):
    ws.cell(r,3).font=F(7.5,False,MUTED); ws.cell(r,3).alignment=Cn
    ws.cell(r,4).font=F(8.5); ws.cell(r,4).alignment=L
    for c in range(5,17):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format=FMT[c]
    for c in range(3,17):
        ws.cell(r,c).fill=fill(PANEL)
        ws.cell(r,c).border=Border(bottom=sd(SEP))

# ------------------------------------------------- la mise en forme dynamique
ws.conditional_formatting=openpyxl.formatting.formatting.ConditionalFormattingList()
def dxf(**k): return DifferentialStyle(**k)
def regle(plage,formule,**k):
    ws.conditional_formatting.add(plage,Rule(type="expression",formula=[formule],dxf=dxf(**k)))

# 1. les variations, d'abord : elles ne posent qu'une couleur de police, donc
#    elles se composent avec les fonds de niveau poses ensuite.
for plage,bon in (("F33:F%d"%FIN,True),("H33:H%d"%FIN,True),("K33:K%d"%FIN,True)):
    ws.conditional_formatting.add(plage,CellIsRule(operator="greaterThan",formula=["0"],
        font=Font(name=UI,size=8.5,color=GOOD if bon else CRIT)))
    ws.conditional_formatting.add(plage,CellIsRule(operator="lessThan",formula=["0"],
        font=Font(name=UI,size=8.5,color=CRIT if bon else GOOD)))
ws.conditional_formatting.add("J33:J%d"%FIN,
    DataBarRule(start_type="num",start_value=0,end_type="num",end_value=0.25,color="FF"+BLUE3,showValue=True))
ws.conditional_formatting.add("M33:M%d"%FIN,CellIsRule(operator="lessThan",formula=["0.7"],
    font=Font(name=UI,size=8.5,bold=True,color=WARN)))

# 2. les trois niveaux de hierarchie. Le decalage du libelle passe par le
#    format de nombre, seul levier d'indentation qu'une regle sache poser.
regle("C33:P%d"%FIN,"$C33=2",font=Font(bold=True,color=INK),fill=PatternFill(bgColor=PARENT))
regle("C33:P%d"%FIN,"$C33=3",font=Font(bold=True,color=INK),fill=PatternFill(bgColor=SOFT))
regle("C33:P%d"%FIN,"$C33=4",font=Font(bold=False,color=INK),fill=PatternFill(bgColor=PANEL))
regle("D33:D%d"%FIN,"$C33=3",numFmt=NumberFormat(numFmtId=171,formatCode='"  "@'))
regle("D33:D%d"%FIN,"$C33=4",numFmt=NumberFormat(numFmtId=172,formatCode='"      "@'))
# le trait qui ferme chaque bloc de marque
regle("C33:P%d"%FIN,"$C33=2",border=Border(top=Side(style="medium",color=SLATE)))

# 3. les variations du bandeau de KPI, avec le bon sens pour chacune
for col,bon in ((5,True),(7,True),(9,True),(11,True),(13,False)):
    cell="%s10"%gl(col)
    ws.conditional_formatting.add(cell,CellIsRule(operator="greaterThan",formula=["0"],
        font=Font(name=UI,size=8.5,bold=True,color=GOOD if bon else CRIT)))
    ws.conditional_formatting.add(cell,CellIsRule(operator="lessThan",formula=["0"],
        font=Font(name=UI,size=8.5,bold=True,color=CRIT if bon else GOOD)))

# ---------------------------------------------------------------- les graphes
# Ils lisent la zone technique, qui est masquee : sans visible_cells_only a
# False, Excel n'en trace aucune serie.
def cadre(r1,c1,r2,c2,titre):
    for r in range(r1,r2+1):
        for c in range(c1,c2+1):
            x=ws.cell(r,c); x.fill=fill(PANEL)
            x.border=Border(top=sd(SEP) if r==r1 else None,bottom=sd(SEP) if r==r2 else None,
                            left=sd(SEP) if c==c1 else None,right=sd(SEP) if c==c2 else None)
    t=ws.cell(r1,c1,"  "+titre); t.font=F(9,True,INK,f=DISPLAY); t.alignment=ind(0)

# ------------------------------------------------- dimensionnement des series
# Les blocs techniques n'ont pas un nombre de lignes fixe : le bloc de marge
# suit le noeud choisi, cinq marques a la racine mais quatre campus sur MBway
# et deux sur Tunon. Une reference cablee sur cinq lignes tracerait des barres
# vides, et tronquerait un noeud a plus de cinq enfants.
#
# Premiere tentative : des noms definis en OFFSET + COUNTA, qui se
# redimensionnent a l'ouverture. Excel n'en a pas voulu dans les references de
# serie. On dimensionne donc a la CONSTRUCTION, en comptant les lignes
# remplies, et le script se relance apres chaque rafraichi Tagetik -- ce qu'il
# faut faire de toute facon pour remettre la mise en page.
def compte(col,r0=7,rmax=80):
    n=0
    for r in range(r0,rmax+1):
        if ws.cell(r,col).value in (None,""): break
        n+=1
    return max(n,1)
def plage(col,n,r0=7):
    return "'2'!$%s$%d:$%s$%d"%(gl(col),r0,gl(col),r0+n-1)

def categories_texte(ch,plage):
    """Les libelles d'axe sont du TEXTE. openpyxl les declare en numRef, et
    Excel affiche alors 1, 2, 3 a la place. On force strRef sur chaque serie."""
    for s in ch.series: s.cat=AxDataSource(strRef=StrRef(f=plage))

def noms_series(ch,noms):
    """Sans cela la legende reprend les en-tetes techniques : MARGE_2024,
    IND_DEPENSES. On pose des libelles lisibles."""
    for s,n in zip(ch.series,noms): s.tx=SeriesLabel(v=n)

def habille(ch,h=8.2,w=8.0):
    ch.height=h; ch.width=w; ch.visible_cells_only=False
    ch.x_axis.delete=False; ch.y_axis.delete=False
    ch.x_axis.majorTickMark="none"; ch.y_axis.majorTickMark="none"
    return ch

N_PONT=compte(29); N_MARGE=compte(37); N_TENSION=compte(52)
# la tension s'arrete aux exercices reellement documentes des deux cotes
while N_TENSION>1 and not ws.cell(6+N_TENSION,55).value: N_TENSION-=1

# 1 — le pont d'EBITDA. Empilement SOCLE invisible + ANCRE + HAUSSE + BAISSE.
cadre(12,5,30,8,"Pont d'EBITDA 2025 → 2026")
ws.cell(12,7,"axe tronqué à 3,0 M€  ").font=F(7.5,False,MUTED,i=True); ws.cell(12,7).alignment=R
br=BarChart(); br.type="col"; br.grouping="stacked"; br.overlap=100; br.gapWidth=55
for col,coul in ((30,None),(31,SLATE),(32,GOOD),(33,CRIT)):
    br.add_data(Reference(ws,min_col=col,max_col=col,min_row=7,max_row=6+N_PONT),titles_from_data=False)
br.set_categories(Reference(ws,min_col=29,max_col=29,min_row=7,max_row=11))
for s,coul in zip(br.series,(None,SLATE,GOOD,CRIT)):
    if coul is None: s.graphicalProperties.noFill=True
    else:
        s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
categories_texte(br,plage(29,N_PONT))
br.legend=None; br.y_axis.numFmt='0.0,," M€"'
# axe tronque, et c'est assume : un pont de 3,47 a 3,85 M€ sur un axe partant
# de zero rendrait les effets invisibles. La troncature est dite dans le titre.
br.y_axis.scaling.min=3000000; br.y_axis.scaling.max=5000000; br.y_axis.majorUnit=500000
habille(br); ws.add_chart(br,"E13")

# 2 — la marge par marque, trois exercices. Rampe sequentielle, pas des teintes
#     categorielles : l'axe est le temps.
cadre(12,9,30,12,"Marge EBITDA par marque")
mg=BarChart(); mg.type="col"; mg.grouping="clustered"; mg.gapWidth=60; mg.overlap=-10
for col in (40,43,46):
    mg.add_data(Reference(ws,min_col=col,max_col=col,min_row=6,max_row=6+N_MARGE),titles_from_data=True)
mg.set_categories(Reference(ws,min_col=37,max_col=37,min_row=7,max_row=11))
for s,coul in zip(mg.series,(BLUE3,BLUE2,BLUE)):
    s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
categories_texte(mg,plage(37,N_MARGE)); noms_series(mg,("2024","2025","2026"))
mg.legend.position="b"; mg.y_axis.numFmt='0%'
habille(mg); ws.add_chart(mg,"I13")

# 3 — la tension d'acquisition. On s'arrete a la ligne 9 : la ligne 10 porte
#     un exercice 2027 sans depense en face, indice inscrits a 370, qui
#     ecraserait l'echelle. Le correctif est pose dans Q_TENSION_ACQUISITION.
cadre(12,13,30,16,"Acquisition — dépenses contre inscrits, base 100")
tn=LineChart()
for col in (55,56):
    tn.add_data(Reference(ws,min_col=col,max_col=col,min_row=6,max_row=6+N_TENSION),titles_from_data=True)
tn.set_categories(Reference(ws,min_col=52,max_col=52,min_row=7,max_row=9))
for s,coul in zip(tn.series,(ORANGE,BLUE)):
    s.graphicalProperties.line.solidFill=coul; s.graphicalProperties.line.width=25000
    s.marker=Marker(symbol="circle",size=6); s.smooth=False
    s.marker.graphicalProperties.solidFill=coul; s.marker.graphicalProperties.line.solidFill=coul
categories_texte(tn,plage(52,N_TENSION)); noms_series(tn,("Dépenses","Inscrits"))
tn.legend.position="b"; tn.y_axis.numFmt='0'
tn.y_axis.scaling.min=95; tn.y_axis.scaling.max=125; tn.y_axis.majorUnit=10
habille(tn); ws.add_chart(tn,"M13")

# ---------------------------------------------------------------- pied
p=ws.cell(FIN+2,3,"Source : V_ALLOCATION et AW_002_000002_000001, scénario et version repris du bandeau de filtres. "
                  "Marges et indices divisés après somme, jamais moyennés.")
p.font=F(7.5,False,MUTED,i=True); p.alignment=ind(0)
ws.sheet_view.zoomScale=100
wb.save(OUT)
print("  series dimensionnees : pont %d, marge %d, tension %d"%(N_PONT,N_MARGE,N_TENSION))
print("%s ecrit — %d graphes, mise en forme dynamique jusqu'a la ligne %d"%(OUT,len(ws._charts),FIN))
