#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_cockpit_design.py — mise au point du template Tagetik COCKPIT.xlsm.

Travaille sur LE TEMPLATE, pas sur un resultat : la ligne 38 ne contient que
des valeurs de maquette et la zone technique n'a que ses en-tetes. Tout ce qui
est pose ici doit donc rester juste quand Tagetik remplira, a la navigation,
un nombre de lignes qu'on ne connait pas a la conception.

Trois choses demandees :
  1. des fleches de tendance sur les six evolutions du bandeau
  2. une heatmap reellement lisible sur le tableau de portefeuille
  3. des graphes dont les sources tiennent au lancement

Le retrait du libelle par niveau a ete retire : il est gere dans Tagetik.

CARTOGRAPHIE (celle du design, decalee d'une colonne par rapport a la mienne)
  B  niveau hierarchique   C  libelle
  D  CA        E  D CA     F  EBITDA   G  D EBITDA  H  Part EBITDA
  I  Marge     J  D Marge  K  Inscrits L  Rempl.    M  Mix alt.
  N  EFFECTIFS O  PLACES   P..Y mesures techniques
  AB..AG pont   AI..AU marge par marque   AZ..BF tension
  Tableau : entete ligne 37, donnees a partir de la ligne 38.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.styles.numbers import NumberFormat
from openpyxl.formatting.rule import Rule, CellIsRule, ColorScaleRule, DataBarRule
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.marker import Marker
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.chart.series import SeriesLabel
from openpyxl.utils import get_column_letter as gl

SRC="COCKPIT.xlsm"; OUT="COCKPIT_DESIGN.xlsm"
R0=38          # premiere ligne de donnees
RSTAT=90       # derniere ligne mise en forme en dur : 50 lignes servies au grain
               # programme x modalite, plus de la marge
RCF=120        # les regles vont plus loin : un noeud plus large passe sans retouche

NAVY="172033"; BLUE="2A78D6"; BLUE2="6FA5DC"; BLUE3="B8CFEC"
SLATE="526071"; INK="202733"; MUTED="69778B"; ONDARK="B8C6DA"
CANVAS="F3F6FA"; PANEL="FFFFFF"; SOFT="EAF2FC"; PARENT="D9E2EF"; SEP="E9EDF3"
GOOD="1E9E89"; WARN="B97800"; CRIT="D64545"; ORANGE="F07B32"
# teintes pales de la heatmap : lisibles sous du texte dense
HM_BAS="F7CFCF"; HM_MED="FDF0CE"; HM_HAUT="CDE9DF"
UI="Arial"; DISPLAY="Fira Sans Medium"
def F(sz=8.5,b=False,c=INK,i=False,f=None): return Font(name=f or UI,size=sz,bold=b,color=c,italic=i)
def fill(c): return PatternFill("solid",fgColor=c)
def sd(c=SEP,st="thin"): return Side(style=st,color=c)
L=Alignment("left",vertical="center"); R=Alignment("right",vertical="center")
Cn=Alignment("center",vertical="center")
def ind(n): return Alignment("left",vertical="center",indent=n)

wb=openpyxl.load_workbook(SRC, keep_vba=True); ws=wb["2"]
ws.sheet_view.showGridLines=False

# Un lien externe traine dans le classeur : il pointe vers mon fichier
# precedent, reste dans le dossier Downloads. Excel l'a cree quand les
# elements y ont ete copies, et c'est le meme mecanisme qui a fait disparaitre
# les series des graphes -- une reference vers un classeur introuvable.
# Aucune formule n'en depend. On le retire : sans quoi chaque lancement de la
# navigation demanderait s'il faut mettre a jour les liaisons.
wb._external_links=[]

# ---------------------------------------------------------------- la grille
ws.column_dimensions["A"].width=2.5
ws.column_dimensions["B"].width=4.5
ws.column_dimensions["B"].hidden=True     # LE NIVEAU EST TECHNIQUE : il pilote
                                          # les quatre regles de hierarchie et
                                          # ne se lit jamais. Une regle
                                          # conditionnelle evalue $B meme quand
                                          # la colonne est masquee.
ws.column_dimensions["C"].width=33       # "      Ipac Bachelor Factory Montpellier" fait
                                         # 39 signes avec son retrait : 30 etait juste
ws.column_dimensions["D"].width=13       # Programme, sur les lignes de niveau 5
ws.column_dimensions["E"].width=11       # Modalite, idem
for c in range(6,18): ws.column_dimensions[gl(c)].width=11.0   # F..Q, les douze mesures
for c in range(18,59): ws.column_dimensions[gl(c)].hidden=True # R..BF : technique
for r in range(1,RCF+4):
    for c in range(1,18): ws.cell(r,c).fill=fill(CANVAS)

# ---------------------------------------------------------------- bandeau
for r in (1,2,3):
    for c in range(1,18): ws.cell(r,c).fill=fill(NAVY)
t=ws.cell(2,3,"COCKPIT EDUSERVICES — PILOTAGE DE LA MARGE"); t.font=F(15,True,"FFFFFF",f=DISPLAY); t.alignment=ind(0)
u=ws.cell(3,3,"Exercice 2026 · variation contre 2025 · V_ALLOCATION et socle CRM"); u.font=F(8,False,ONDARK); u.alignment=ind(0)
for r,h in ((1,8),(2,26),(3,15),(4,6),(5,20),(6,6),(7,10),(8,13),(9,26),(10,14),(11,10),(36,20),(37,17)):
    ws.row_dimensions[r].height=h
for r in range(12,36): ws.row_dimensions[r].height=15.5
for r in range(R0,RSTAT+1): ws.row_dimensions[r].height=15.5

# ---------------------------------------------------------------- filtres
for c in range(3,18):
    x=ws.cell(5,c); x.fill=fill(SOFT); x.border=Border(top=sd(BLUE3),bottom=sd(BLUE3))
for col,lab in ((3,"SCÉNARIO"),(10,"VERSION"),(14,"ENTITÉ")):
    a=ws.cell(5,col,lab); a.font=F(7.5,True,SLATE); a.alignment=ind(1)
    ws.cell(5,col+1).font=F(9,True,INK); ws.cell(5,col+1).alignment=L

# --------------------------------------------------- les six cartes de KPI
# Elles etaient en C, E, G, I, K, M : la premiere tombait sur la colonne des
# libelles, large de 30, contre 22 pour les cinq autres. On les decale d'une
# colonne, sur D..O : six cartes de deux colonnes, strictement egales.
#
# LES FLECHES. Elles sont dans le FORMAT DE NOMBRE, pas dans le texte : la
# section positive porte le triangle haut, la section negative le triangle bas,
# la troisieme le tiret quand la variation est nulle ou vide. La fleche dit
# donc le SENS, et la couleur conditionnelle dit si c'est une bonne nouvelle.
# Les deux ne se confondent pas, et c'est voulu : sur le cout d'acquisition,
# une fleche vers le haut est rouge.
HAUT_BAS  = '"▲ "0.0%;"▼ "0.0%;"—"'
HAUT_BAS_PT='"▲ "0.00" pt";"▼ "0.00" pt";"—"'
KPI=[(6, "CHIFFRE D'AFFAIRES",  "=F38",       '0.0,," M€"', "=G38",       HAUT_BAS,   True),
     (8, "EBITDA",              "=H38",       '0.0,," M€"', "=I38",       HAUT_BAS,   True),
     (10,"MARGE EBITDA",        "=K38",       '0.0%',       "=L38",       HAUT_BAS_PT,True),
     (12,"INSCRITS (NOUVEAUX)", "=M38",       '#,##0',      "=AA38",      HAUT_BAS,   True),
     (14,"COÛT D'ACQUISITION",  "=U38/M38",   '#,##0" €"',
         '=IFERROR(N9/(V38/Y38)-1,"")',                                   HAUT_BAS,   False),
     (16,"REMPLISSAGE MOYEN",   "=N38",       '0.0%',       "=Q38-P38",
         '#,##0" places libres";-#,##0" places libres";"—"',              None)]
for r in (8,9,10):
    for c in range(2,18): ws.cell(r,c).value=None
for col,lab,val,fmt,var,vfmt,sens in KPI:
    for c in (col,col+1):
        for r in (8,9,10):
            x=ws.cell(r,c); x.fill=fill(PANEL)
            x.border=Border(top=sd(SEP) if r==8 else None,bottom=sd(SEP) if r==10 else None,
                            left=sd(SEP) if c==col else None,right=sd(SEP) if c==col+1 else None)
    a=ws.cell(8,col,lab);  a.font=F(7.5,True,SLATE); a.alignment=ind(1)
    v=ws.cell(9,col,val);  v.font=F(18,True,INK,f=DISPLAY); v.number_format=fmt; v.alignment=ind(1)
    d=ws.cell(10,col,var); d.font=F(9,True,MUTED); d.number_format=vfmt; d.alignment=ind(1)

# ---------------------------------------------------------------- le tableau
ENTETES={6:"CA",7:"Δ CA",8:"EBITDA",9:"Δ EBITDA",10:"Part EBITDA",11:"Marge EBITDA",
         12:"Δ Marge (pt)",13:"Inscrits",14:"Remplissage",15:"Mix alternance",
         16:"Effectifs",17:"Places"}
s=ws.cell(36,3,"PORTEFEUILLE — MARQUE, CAMPUS, PROGRAMME ET MODALITÉ"); s.font=F(10,True,INK,f=DISPLAY); s.alignment=ind(0)
h=ws.cell(36,8,"graisse et fond donnent le niveau · échelle de couleur = performance relative")
h.font=F(7.5,False,MUTED,i=True); h.alignment=L
for c in range(2,18):
    x=ws.cell(37,c); x.fill=fill(SLATE); x.font=F(8,True,"FFFFFF",f=DISPLAY)
    x.alignment=Cn if c>=6 else ind(1)
    x.border=Border(top=sd(SLATE),bottom=sd(SLATE),left=sd(SLATE),right=sd(SLATE))
ws.cell(37,2,"Niv."); ws.cell(37,2).alignment=Cn
ws.cell(37,3,"Entité")
ws.cell(37,4,"Programme"); ws.cell(37,5,"Modalité")
for c,lab in ENTETES.items(): ws.cell(37,c).value=lab
# Le bloc technique, R..AA : masque, mais correctement nomme. Il l'etait resté
# au nom de l'ancienne colonne apres le decalage de deux crans.
for j,lab in enumerate(("EFFECTIFS_ALT","EBITDA_N1","CA_N1","SPEND_ACQ","SPEND_ACQ_N1",
                        "MARGE_EBITDA_N1","PLACES_N1","INSCRITS_N1","EFFECTIFS_N1",
                        "PCT_NOUVEAUX_INSCRITS")):
    x=ws.cell(37,18+j,lab); x.font=F(7,False,MUTED); x.alignment=Cn
for c in range(28,40): ws.cell(37,c).value=None
FMT={6:'#,##0',7:'"▲ "0.0%;"▼ "0.0%;""',8:'#,##0',9:'"▲ "0.0%;"▼ "0.0%;""',10:'0.0%',
     11:'0.0%',12:'"▲ "0.00;"▼ "0.00;""',13:'#,##0',14:'0.0%',15:'0.0%',16:'#,##0',17:'#,##0'}
# Police, alignement et formats sont poses en dur jusqu'a RCF : ils
# n'apparaissent pas sur une cellule vide. Le FOND et les BORDURES, eux,
# viennent des regles de niveau uniquement -- sinon une navigation sur Tunon,
# qui ne sert que quatre lignes, laisserait seize lignes blanches bordees en
# dessous, qui se lisent comme un tableau vide.
for r in range(R0,RCF+1):
    # on efface le fond et les bordures heritees du fichier d'origine : c'est
    # aux regles de niveau de les poser, et a elles seules
    for c in range(2,18):
        ws.cell(r,c).border=Border(); ws.cell(r,c).fill=fill(CANVAS)
    ws.cell(r,2).font=F(7.5,False,MUTED); ws.cell(r,2).alignment=Cn
    ws.cell(r,3).font=F(8.5); ws.cell(r,3).alignment=L
    for c in (4,5):
        x=ws.cell(r,c); x.font=F(8,False,MUTED); x.alignment=L
    for c in range(6,18):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format=FMT[c]

# ------------------------------------------- mise en forme conditionnelle
# L'ORDRE COMPTE. Excel applique la premiere regle qui pose une propriete
# donnee. On met donc la heatmap AVANT les fonds de niveau, sans quoi le fond
# de la marque ecraserait l'echelle de couleur. Les regles qui ne posent qu'une
# couleur de police, elles, se composent avec tout le reste.
ws.conditional_formatting=openpyxl.formatting.formatting.ConditionalFormattingList()
def rg(c1,c2=None): return "%s%d:%s%d"%(gl(c1),R0,gl(c2 or c1),RCF)

# 1. LA HEATMAP. Bornes fixes et non des percentiles : un campus doit garder sa
#    couleur quand on change de perimetre, sinon la lecture n'est plus
#    comparable d'un lancement a l'autre. Marge de 2 a 22 %, remplissage de
#    55 a 95 %, ce qui couvre l'amplitude reelle du reseau.
ws.conditional_formatting.add(rg(11), ColorScaleRule(
    start_type="num", start_value=0.02, start_color="FF"+HM_BAS,
    mid_type="num",   mid_value=0.12,   mid_color="FF"+HM_MED,
    end_type="num",   end_value=0.22,   end_color="FF"+HM_HAUT))
ws.conditional_formatting.add(rg(14), ColorScaleRule(
    start_type="num", start_value=0.55, start_color="FF"+HM_BAS,
    mid_type="num",   mid_value=0.75,   mid_color="FF"+HM_MED,
    end_type="num",   end_value=0.95,   end_color="FF"+HM_HAUT))

# 1 bis. LA BARRE DE DONNEES sur la part d'EBITDA. Barre et echelle de couleur
#    ne disent pas la meme chose : la barre montre une MAGNITUDE, l'echelle une
#    PERFORMANCE RELATIVE. Les melanger sur la meme colonne brouille les deux.
#    Part d'EBITDA est une magnitude, marge et remplissage sont des
#    performances : chacune a l'encodage qui lui revient.
# Bornee a 100 % et non a 30 % : la colonne melange les trois niveaux, le
# groupe y vaut 100 %, une marque jusqu'a 45 % et un campus 1 a 16 %. A 30 %
# tout ce qui depasse une marque saturait et la barre ne disait plus rien.
ws.conditional_formatting.add(rg(10), DataBarRule(
    start_type="num", start_value=0, end_type="num", end_value=1.0,
    color="FF"+BLUE3, showValue=True))

# 2. les variations : couleur de police seule, donc elles survivent par-dessus
#    la heatmap comme par-dessus les fonds de niveau
for c1 in (7,9,12):
    ws.conditional_formatting.add(rg(c1),CellIsRule(operator="greaterThan",formula=["0"],
        font=Font(name=UI,size=8.5,color=GOOD)))
    ws.conditional_formatting.add(rg(c1),CellIsRule(operator="lessThan",formula=["0"],
        font=Font(name=UI,size=8.5,color=CRIT)))

# 3. les trois niveaux de hierarchie, pilotes par la colonne B : gras, fond et
#    filet. Le retrait du libelle est gere cote Tagetik, pas ici.
def niveau(plage,formule,**k):
    ws.conditional_formatting.add(plage,Rule(type="expression",formula=[formule],
                                             dxf=DifferentialStyle(**k)))
niveau("B%d:Q%d"%(R0,RCF),"$B%d=2"%R0,font=Font(bold=True,color=INK),
       fill=PatternFill(bgColor=PARENT),
       border=Border(top=Side(style="medium",color=SLATE),bottom=sd(SEP)))
niveau("B%d:Q%d"%(R0,RCF),"$B%d=3"%R0,font=Font(bold=True,color=INK),
       fill=PatternFill(bgColor=SOFT),  border=Border(bottom=sd(SEP)))
niveau("B%d:Q%d"%(R0,RCF),"$B%d=4"%R0,font=Font(bold=True,color=INK),
       fill=PatternFill(bgColor=PANEL), border=Border(bottom=sd(SEP)))
# NIVEAU 5 : programme x modalite. Le campus prend le gras -- il est devenu un
# parent -- et la feuille passe en fond tres clair, sans gras, en encre douce.
# Quatre fonds et deux graisses pour quatre niveaux : la hierarchie se lit sans
# retrait, ce que Saad gere de son cote dans Tagetik.
niveau("B%d:Q%d"%(R0,RCF),"$B%d=5"%R0,font=Font(bold=False,color=MUTED),
       fill=PatternFill(bgColor="FBFCFE"), border=Border(bottom=sd(SEP)))
# Le RETRAIT du libelle par niveau a ete retire a la demande de Saad, qui le
# gere directement dans Tagetik. Il passait par le format de nombre de la
# regle ('"      "@'), seul levier d'indentation qu'une regle conditionnelle
# sache poser. Les niveaux restent lisibles par le gras, le fond et le filet.

# 3 bis. LE FORMAT DES MONTANTS S'ADAPTE A L'ORDRE DE GRANDEUR. En M€, un
#    EBITDA de 81 725 EUR s'affiche 0,1 M€ : toute la precision est perdue, et
#    c'est ce qui arriverait des qu'on descend sur Ipac, Pigier ou Tunon. Sous
#    le million, la carte bascule en euros. Excel ne sait pas conditionner un
#    format dans un format, mais une regle sait poser un format.
for col in (6,8):
    ws.conditional_formatting.add("%s9"%gl(col),Rule(type="cellIs",operator="lessThan",
        formula=["1000000"],dxf=DifferentialStyle(numFmt=NumberFormat(numFmtId=180+col,
        formatCode='#,##0" €"'))))

# 4. les evolutions du bandeau. La fleche dit le sens, la couleur dit si c'est
#    une bonne nouvelle : sur le cout d'acquisition les deux sont inverses.
for col,bon in ((6,True),(8,True),(10,True),(12,True),(14,False)):
    cell="%s10"%gl(col)
    ws.conditional_formatting.add(cell,CellIsRule(operator="greaterThan",formula=["0"],
        font=Font(name=UI,size=9,bold=True,color=GOOD if bon else CRIT)))
    ws.conditional_formatting.add(cell,CellIsRule(operator="lessThan",formula=["0"],
        font=Font(name=UI,size=9,bold=True,color=CRIT if bon else GOOD)))

# --------------------------------------------------- ou tombent les query
# Les trois query sortent desormais DANS L'ORDRE DU GRAPHE : la categorie en
# premiere colonne utile, puis les series, contigues. Il n'y a donc plus de
# colonnes de relais dans le classeur -- les graphes lisent la zone de
# restitution telle quelle.
#
#   Z_PONT     AB..AG   1 RANG  2 ETAPE  3 SOCLE  4 ANCRE  5 HAUSSE  6 BAISSE
#   Z_MARGE    AI..AU   1 LIBELLE  2 MARGE_2024  3 MARGE_2025  4 MARGE_2026
#                       5 ECART_PT  puis niveau, code, CA et EBITDA par exercice
#   Z_TENSION  AZ..BF   1 EXERCICE  2 IND_DEPENSES  3 IND_INSCRITS
#                       4 CAC  5 ECART_PT  6 DEPENSES  7 INSCRITS
#
# Ici les plages sont figees a la hauteur maximale connue -- cinq pas pour le
# pont, cinq marques, trois exercices. C'est le repli quand les zones ne sont
# pas nommees. Des qu'elles le sont, build_cockpit_zones.py rebranche les
# series dessus et la hauteur suit toute seule.
PONT_C, PONT_N = 28, 5      # AB
MARGE_C, MARGE_N = 35, 5    # AI
TENS_C, TENS_N = 52, 3      # AZ
for c in range(18,81): ws.column_dimensions[gl(c)].hidden=True

def cadre(r1,c1,r2,c2,titre,note=""):
    for r in range(r1,r2+1):
        for c in range(c1,c2+1):
            x=ws.cell(r,c); x.fill=fill(PANEL)
            x.border=Border(top=sd(SEP) if r==r1 else None,bottom=sd(SEP) if r==r2 else None,
                            left=sd(SEP) if c==c1 else None,right=sd(SEP) if c==c2 else None)
    t=ws.cell(r1,c1,"  "+titre); t.font=F(9,True,INK,f=DISPLAY); t.alignment=ind(0)
    if note:
        n=ws.cell(r1,c2,note+"  "); n.font=F(7.5,False,MUTED,i=True); n.alignment=R

def habille(ch,h=9.0,w=8.1):
    ch.height=h; ch.width=w; ch.visible_cells_only=False
    ch.x_axis.delete=False; ch.y_axis.delete=False
    ch.x_axis.majorTickMark="none"; ch.y_axis.majorTickMark="none"
    return ch
def cats(ch,c0,r1,r2):
    p="'2'!$%s$%d:$%s$%d"%(gl(c0),r1,gl(c0),r2)
    for s in ch.series: s.cat=AxDataSource(strRef=StrRef(f=p))
def noms(ch,libelles):
    for s,n in zip(ch.series,libelles): s.tx=SeriesLabel(v=n)

ws._charts=[]      # on repart des cadres vides laisses par Excel

# 1 — le pont d'EBITDA
cadre(12,4,35,8,"Pont d'EBITDA 2025 → 2026")
br=BarChart(); br.type="col"; br.grouping="stacked"; br.overlap=100; br.gapWidth=55
for j in range(2,6):   # SOCLE, ANCRE, HAUSSE, BAISSE
    br.add_data(Reference(ws,min_col=PONT_C+j,max_col=PONT_C+j,min_row=7,max_row=6+PONT_N),
                titles_from_data=False)
for s,coul in zip(br.series,(None,SLATE,GOOD,CRIT)):
    if coul is None: s.graphicalProperties.noFill=True
    else: s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
cats(br,PONT_C+1,7,6+PONT_N); br.legend=None; br.y_axis.numFmt='0.0,," M€"'
# AXE LIBRE, et c'est un correctif. Il etait fige entre 3 et 5 M€, ce qui
# convenait au groupe mais laissait le graphe COMPLETEMENT VIDE sur les cinq
# marques : ISCOM culmine a 1,3 M€, Tunon a 0,2 M€. Un cadrage qui ne marche
# que sur un noeud sur six n'est pas un cadrage. Excel echelonne donc lui-meme,
# et l'effet activite reste largement lisible, autour du quart de la hauteur.
habille(br); ws.add_chart(br,"D13")

# 2 — la marge par marque, ou par campus si l'on est descendu sur une marque
cadre(12,9,35,13,"Marge EBITDA — 3 exercices")
mg=BarChart(); mg.type="col"; mg.grouping="clustered"; mg.gapWidth=60; mg.overlap=-10
for j in range(1,4):   # MARGE_2024, MARGE_2025, MARGE_2026
    mg.add_data(Reference(ws,min_col=MARGE_C+j,max_col=MARGE_C+j,min_row=7,max_row=6+MARGE_N),
                titles_from_data=False)
for s,coul in zip(mg.series,(BLUE3,BLUE2,BLUE)):
    s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
cats(mg,MARGE_C,7,6+MARGE_N); noms(mg,("2024","2025","2026"))
mg.legend.position="b"; mg.y_axis.numFmt='0%'
habille(mg); ws.add_chart(mg,"I13")

# 3 — la tension d'acquisition
cadre(12,14,35,17,"Acquisition — dépenses vs inscrits","base 100")
tn=LineChart()
for j in range(1,3):   # IND_DEPENSES, IND_INSCRITS
    tn.add_data(Reference(ws,min_col=TENS_C+j,max_col=TENS_C+j,min_row=7,max_row=6+TENS_N),
                titles_from_data=False)
for s,coul in zip(tn.series,(ORANGE,BLUE)):
    s.graphicalProperties.line.solidFill=coul; s.graphicalProperties.line.width=25000
    s.marker=Marker(symbol="circle",size=6); s.smooth=False
    s.marker.graphicalProperties.solidFill=coul; s.marker.graphicalProperties.line.solidFill=coul
cats(tn,TENS_C,7,6+TENS_N); noms(tn,("Dépenses","Inscrits"))
tn.legend.position="b"; tn.y_axis.numFmt='0'
tn.y_axis.scaling.min=95; tn.y_axis.scaling.max=125; tn.y_axis.majorUnit=10
habille(tn); ws.add_chart(tn,"N13")

p=ws.cell(RSTAT+2,3,"Source : V_ALLOCATION et AW_002_000002_000001. Marges et indices divisés après somme, jamais moyennés.")
p.font=F(7.5,False,MUTED,i=True); p.alignment=ind(0)
wb.save(OUT)
print("%s ecrit — %d graphes branches direct sur %s / %s / %s, regles jusqu'a la ligne %d"
      %(OUT,len(ws._charts),gl(PONT_C),gl(MARGE_C),gl(TENS_C),RCF))
