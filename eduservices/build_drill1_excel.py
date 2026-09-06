#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_drill1_excel.py — le drill 1, pense pour la demo.

ORDRE DE LECTURE, et c'est le sujet. Un drill-through s'ouvre devant un
public : il doit repondre AVANT de prouver. D'ou l'implantation :

  1  la reponse en une phrase       l'EBITDA passe de X a Y, soit Z
  2  la cascade                     le message, en grand
  3  le pont chiffre, sept lignes   la legende du graphe
  4  le controle                    la preuve que ca boucle
  5  le detail par campus           l'audit, pour qui veut creuser

Le detail vient EN DERNIER. C'est le materiau, pas le message : personne dans
un comite ne commence par lire quatorze lignes de couts unitaires.

MISE EN FORME CONDITIONNELLE. Le nombre de campus depend de la cellule
cliquee : quatorze a la racine, deux sur Tunon. Les lignes non servies ne
portent donc ni fond ni bordure en dur -- elles les recoivent d'une regle
conditionnelle qui ne se declenche que si le campus est renseigne. Une ligne
vide se confond avec le fond de page. Le TOTAL, lui, est pose en dur : il
s'affiche toujours.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import CellIsRule, Rule
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.utils import get_column_letter as GL
from socle_reel import construire

OUT="DRILL1_EXCEL.xlsx"; N,P=2026,2025
NAVY="172033"; SLATE="526071"; INK="202733"; MUTED="69778B"; ONDARK="B8C6DA"
CANVAS="F3F6FA"; PANEL="FFFFFF"; SEP="E9EDF3"; SOFT="EAF2FC"; PARENT="D9E2EF"; WARM="FFF1E8"
GOOD="1E9E89"; CRIT="D64545"; UI="Arial"; DISPLAY="Fira Sans Medium"
def F(sz=8.5,b=False,c=INK,i=False,f=None): return Font(name=f or UI,size=sz,bold=b,color=c,italic=i)
fill=lambda c: PatternFill("solid",fgColor=c)
sd=lambda c=SEP,st="thin": Side(style=st,color=c)
R=Alignment("right",vertical="center"); Cn=Alignment("center",vertical="center")
WRAP=Alignment("center",vertical="center",wrap_text=True)
ind=lambda n: Alignment("left",vertical="center",indent=n)
LIBC={"IPAC_MTP":"Ipac Montpellier","IPAC_NAN":"Ipac Nantes","IPAC_REN":"Ipac Rennes",
 "ISCOM_LIL":"ISCOM Lille","ISCOM_PAR":"ISCOM Paris","ISCOM_TLS":"ISCOM Toulouse",
 "MBWAY_BOR":"MBway Bordeaux","MBWAY_LYO":"MBway Lyon","MBWAY_NAN":"MBway Nantes",
 "MBWAY_PAR":"MBway Paris","PIGIER_BOR":"Pigier Bordeaux","PIGIER_LYO":"Pigier Lyon",
 "TUNON_LYO":"Tunon Lyon","TUNON_PAR":"Tunon Paris"}
C=sorted(construire(),key=lambda c:LIBC[c["ent"]])

# --------------------------------------------------------------- l'ossature
GRAPH0, TAB0, CTRL, DET0 = 8, 28, 38, 41
DR0   = DET0+2          # ligne du TOTAL
CAMP0 = DR0+1           # premiere ligne de campus
CAMPN = CAMP0+29        # trente emplacements : de quoi absorber tout noeud
wb=openpyxl.Workbook(); ws=wb.active; ws.title="Drill EBITDA"
ws.sheet_view.showGridLines=False
ws.column_dimensions["A"].width=2.5; ws.column_dimensions["B"].width=26
LARG={3:11,4:11,5:12,6:13,7:13,8:15,9:15,10:19,11:14,12:14,13:12,14:12,15:13,16:13}
for c,w in LARG.items(): ws.column_dimensions[GL(c)].width=w
ws.column_dimensions["R"].width=3
for c in range(19,24): ws.column_dimensions[GL(c)].width=15
for c in range(25,31): ws.column_dimensions[GL(c)].hidden=True   # la cascade, plomberie
for r in range(1,CAMPN+4):
    for c in range(1,24): ws.cell(r,c).fill=fill(CANVAS)
for r in (1,2,3):
    for c in range(1,24): ws.cell(r,c).fill=fill(NAVY)
ws.cell(2,2,"POURQUOI L'EBITDA A BOUGÉ").font=F(15,True,"FFFFFF",f=DISPLAY)
ws.cell(2,2).alignment=ind(0)
ws.cell(3,2,"drill sur la cellule cliquée · 2026 contre 2025 · V_ALLOCATION").font=F(8,False,ONDARK)
ws.cell(3,2).alignment=ind(0)
for r,h in ((1,8),(2,26),(3,15),(4,10),(5,24),(6,14),(7,8)): ws.row_dimensions[r].height=h

def entete(row,c0,titres,titre,note=""):
    t=ws.cell(row-1,c0,titre); t.font=F(10,True,INK,f=DISPLAY); t.alignment=ind(0)
    if note:
        x=ws.cell(row-1,c0+len(titres)-1,note+"  "); x.font=F(7.5,False,MUTED,i=True); x.alignment=R
    for j,lab in enumerate(titres):
        c=ws.cell(row,c0+j,lab); c.fill=fill(SLATE); c.font=F(8,True,"FFFFFF",f=DISPLAY)
        c.alignment=WRAP if j else ind(1); c.border=Border(*[sd(SLATE)]*4)
    ws.row_dimensions[row].height=42 if len(titres)>6 else 20

# ------------------------------------------- 1. la reponse, en une phrase
ebp=sum(c["eb"][P] for c in C); ebn=sum(c["eb"][N] for c in C)
# La phrase lit le PONT, pas la ligne de total : en C{depart} et C{arrivee} se
# trouvent les deux EBITDA, alors que C et D de la ligne de total portent les
# effectifs. Formats en notation canonique -- virgule pour les milliers, point
# pour les decimales -- qu'Excel traduit ensuite dans la langue du poste.
ws.cell(5,2,'="L\'EBITDA passe de "&TEXT(C{0},"#,##0 €")&" à "&TEXT(C{1},"#,##0 €")'
            '&", soit "&TEXT(C{1}-C{0},"+#,##0 €;-#,##0 €")&"  ("'
            '&TEXT(C{1}/C{0}-1,"+0.0%;-0.0%")&")"'.format(TAB0+1,TAB0+7)).font=F(14,True,INK,f=DISPLAY)
ws.cell(5,2).alignment=ind(0)
ws.cell(6,2,"le pont ci-dessous décompose cette variation en cinq causes, sans reste")
ws.cell(6,2).font=F(8.5,False,MUTED,i=True); ws.cell(6,2).alignment=ind(0)

# ------------------------------------------- 3. le pont, sept lignes
LIB=["EBITDA %d"%P,"Effet effectifs","Effet prix et mix","Effet coût var. unitaire",
     "Effet coûts directs","Effet siège","EBITDA %d"%N]
COLEF={2:"S",3:"T",4:"U",5:"V",6:"W"}
entete(TAB0,2,("Effet","Montant","Part de la variation"),
       "LE PONT, CHIFFRE PAR CHIFFRE","la légende du graphe")
for i,lab in enumerate(LIB,1):
    r=TAB0+i; niv = i in (1,7)
    for c in range(2,5):
        x=ws.cell(r,c); x.fill=fill(PARENT if niv else PANEL); x.border=Border(bottom=sd())
    ws.cell(r,2,lab).font=F(9,niv); ws.cell(r,2).alignment=ind(1)
    m = "=SUM(O{0}:O{1})".format(CAMP0,CAMPN) if i==1 else \
        "=SUM(P{0}:P{1})".format(CAMP0,CAMPN) if i==7 else "={0}{1}".format(COLEF[i],DR0)
    x=ws.cell(r,3,m); x.number_format='#,##0" €"'; x.alignment=R; x.font=F(9,niv)
    if not niv:
        x=ws.cell(r,4,'=IFERROR(C{0}/(C{1}-C{2}),"")'.format(r,TAB0+7,TAB0+1))
        x.number_format='0.0%'; x.alignment=R; x.font=F(8.5,False,MUTED)
    # la plomberie de la cascade, en colonnes masquees
    ws.cell(r,25,lab)
    if niv:
        ws.cell(r,26,0); ws.cell(r,27,"=C%d"%r); ws.cell(r,28,0); ws.cell(r,29,0)
    else:
        av="C{0}+SUM(C{1}:C{2})".format(TAB0+1,TAB0+2,r-1) if i>2 else "C{0}".format(TAB0+1)
        ap="C{0}+SUM(C{1}:C{2})".format(TAB0+1,TAB0+2,r)
        ws.cell(r,26,"=MIN({0},{1})".format(av,ap)); ws.cell(r,27,0)
        ws.cell(r,28,"=MAX(C%d,0)"%r); ws.cell(r,29,"=MAX(-C%d,0)"%r)
ws.conditional_formatting.add("C{0}:C{1}".format(TAB0+2,TAB0+6),
    CellIsRule(operator="greaterThan",formula=["0"],font=Font(name=UI,size=9,color=GOOD)))
ws.conditional_formatting.add("C{0}:C{1}".format(TAB0+2,TAB0+6),
    CellIsRule(operator="lessThan",formula=["0"],font=Font(name=UI,size=9,color=CRIT)))

# ------------------------------------------- 4. le controle
for c in range(2,5):
    x=ws.cell(CTRL,c); x.fill=fill(SOFT); x.border=Border(top=sd(SLATE,"medium"),bottom=sd(SLATE,"medium"))
ws.cell(CTRL,2,"Contrôle · les cinq effets moins la variation").font=F(8.5,True,MUTED)
ws.cell(CTRL,2).alignment=ind(1)
k=ws.cell(CTRL,3,"=SUM(C{0}:C{1})-(C{2}-C{3})".format(TAB0+2,TAB0+6,TAB0+7,TAB0+1))
k.number_format='0.00" €"'; k.alignment=R; k.font=F(11,True,GOOD)
ws.cell(CTRL,4,"doit valoir 0,00 €").font=F(7.5,False,MUTED,i=True); ws.cell(CTRL,4).alignment=Cn

# ------------------------------------------- 5. le detail par campus
COLS=("Campus","Effectifs 2025","Effectifs 2026","Élèves gagnés",
      "CA par élève 2025","CA par élève 2026",
      "Coût var. par élève 2025","Coût var. par élève 2026",
      "Marge sur coût var. par élève 2025",
      "Coûts directs 2025","Coûts directs 2026","Siège 2025","Siège 2026",
      "EBITDA 2025","EBITDA 2026")
entete(DET0+1,2,COLS,"LE DÉTAIL PAR CAMPUS  ·  ce que la requête renvoie",
       "une ligne par campus")
entete(DET0+1,19,("Effet effectifs","Effet prix et mix","Effet coût var. unitaire",
                  "Effet coûts directs","Effet siège"),
       "CE QUE LE CLASSEUR CALCULE","une multiplication par effet")
FMT={3:'#,##0',4:'#,##0',5:'#,##0',6:'#,##0.00',7:'#,##0.00',8:'#,##0.00',9:'#,##0.00',
     10:'#,##0.00',11:'#,##0',12:'#,##0',13:'#,##0',14:'#,##0',15:'#,##0',16:'#,##0'}
# le TOTAL, pose en dur : il s'affiche toujours, meme si un seul campus repond
for c in list(range(2,17))+list(range(19,24)):
    x=ws.cell(DR0,c); x.fill=fill(PARENT); x.border=Border(top=sd(SLATE,"medium"),bottom=sd(SLATE))
    x.font=F(8.5,True); x.alignment=R
    if c!=2: x.value="=SUM({0}{1}:{0}{2})".format(GL(c),CAMP0,CAMPN); x.number_format=FMT.get(c,'#,##0')
ws.cell(DR0,2,"TOTAL du périmètre"); ws.cell(DR0,2).alignment=ind(1); ws.cell(DR0,2).font=F(8.5,True)
for c in (6,7,8,9,10): ws.cell(DR0,c).value=None      # une moyenne d'unitaires n'a pas de sens
ws.cell(DR0,6,"—").alignment=Cn; ws.cell(DR0,6).font=F(8.5,False,MUTED)

# les campus : AUCUN fond ni bordure en dur, tout vient de la regle conditionnelle
for i,c in enumerate(C):
    r=CAMP0+i; ep,en=c["eff"][P],c["eff"][N]
    for col,v in zip(range(2,17),(LIBC[c["ent"]],ep,en,en-ep,
            round(c["ca"][P]/ep,6),round(c["ca"][N]/en,6),
            round(c["cvar"][P]/ep,6),round(c["cvar"][N]/en,6),
            round(c["ca"][P]/ep-c["cvar"][P]/ep,6),
            c["cdir"][P],c["cdir"][N],c["csiege"][P],c["csiege"][N],c["eb"][P],c["eb"][N])):
        ws.cell(r,col,v)
for r in range(CAMP0,CAMPN+1):
    ws.cell(r,2).font=F(8.5); ws.cell(r,2).alignment=ind(1)
    for c in range(3,17):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format=FMT[c]
    for col,f_ in zip(range(19,24),('=E{0}*J{0}','=(G{0}-F{0})*D{0}','=-(I{0}-H{0})*D{0}',
                                    '=-(L{0}-K{0})','=-(N{0}-M{0})')):
        x=ws.cell(r,col,f_.format(r) if ws.cell(r,2).value else None)
        x.font=F(8.5); x.alignment=R; x.number_format='#,##0'
    ws.row_dimensions[r].height=15.5

# LA REGLE : une ligne ne prend fond et bordure que si le campus est renseigne
def visible(plage,fond):
    ws.conditional_formatting.add(plage,Rule(type="expression",
        formula=['$B{0}<>""'.format(CAMP0)],
        dxf=DifferentialStyle(fill=PatternFill(bgColor=fond),border=Border(bottom=sd()))))
visible("B{0}:P{1}".format(CAMP0,CAMPN),PANEL)
visible("S{0}:W{1}".format(CAMP0,CAMPN),WARM)

# ------------------------------------------- 2. la cascade
br=BarChart(); br.type="col"; br.grouping="stacked"; br.overlap=100; br.gapWidth=45
for c in range(26,30):
    br.add_data(Reference(ws,min_col=c,max_col=c,min_row=TAB0+1,max_row=TAB0+7),titles_from_data=False)
for x,coul in zip(br.series,(None,SLATE,GOOD,CRIT)):
    if coul is None: x.graphicalProperties.noFill=True
    else: x.graphicalProperties.solidFill=coul; x.graphicalProperties.line.noFill=True
for x in br.series:
    x.cat=AxDataSource(strRef=StrRef(f="'Drill EBITDA'!$Y${0}:$Y${1}".format(TAB0+1,TAB0+7)))
br.legend=None; br.y_axis.numFmt='#,##0'; br.height=10.5; br.width=24
br.visible_cells_only=False; br.x_axis.delete=False; br.y_axis.delete=False
br.x_axis.majorTickMark="none"; br.y_axis.majorTickMark="none"
ws.add_chart(br,"B%d"%GRAPH0)
for r in range(GRAPH0,TAB0-1): ws.row_dimensions[r].height=15
wb.save(OUT)
print("%s ecrit"%OUT)
print("  1 réponse      B5")
print("  2 cascade      B%d, 24 x 10,5 cm"%GRAPH0)
print("  3 le pont      B%d:D%d"%(TAB0,TAB0+7))
print("  4 contrôle     C%d"%CTRL)
print("  5 détail       B%d:P%d, total en ligne %d, campus %d à %d"%(DET0+1,CAMPN,DR0,CAMP0,CAMPN))
print("  cascade source Y:AC, masquée")
