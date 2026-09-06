#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_drill1.py — simulation du DRILL 1, "pourquoi l'EBITDA a bouge".

Rejoue Q_D1_TABLEAU et Q_D1_GRAPHE sur la cellule cliquee, pose les deux
resultats la ou Tagetik les posera, et branche la cascade dessus.

  Q_D1_TABLEAU  ->  B7:E13    RANG, EFFET, MONTANT, PART_VAR
  Q_D1_GRAPHE   ->  G7:K13    ETAPE, SOCLE, ANCRE, HAUSSE, BAISSE

Le graphe ne lit PAS le tableau : les deux query sont independantes et
renvoient chacune ses sept lignes. C'est ce que fera Tagetik.
"""
import sys, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.utils import get_column_letter as GL
from socle_reel import construire

CIBLE = sys.argv[1] if len(sys.argv)>1 else "EDUSERVICES"
EX    = int(sys.argv[2]) if len(sys.argv)>2 else 2026
OUT   = "DRILL1_POURQUOI.xlsm"
NAVY="172033"; SLATE="526071"; INK="202733"; MUTED="69778B"; ONDARK="B8C6DA"
CANVAS="F3F6FA"; PANEL="FFFFFF"; SEP="E9EDF3"; SOFT="EAF2FC"
GOOD="1E9E89"; CRIT="D64545"; UI="Arial"; DISPLAY="Fira Sans Medium"
def F(sz=8.5,b=False,c=INK,i=False,f=None): return Font(name=f or UI,size=sz,bold=b,color=c,italic=i)
fill=lambda c: PatternFill("solid",fgColor=c); sd=lambda c=SEP: Side(style="thin",color=c)
R=Alignment("right",vertical="center"); Cn=Alignment("center",vertical="center")
ind=lambda n: Alignment("left",vertical="center",indent=n)

TOUS=construire()
CODE={"Ipac Bachelor Factory":"IPAC","ISCOM":"ISCOM","MBway":"MBWAY","Pigier":"PIGIER","Tunon":"TUNON"}
C = TOUS if CIBLE=="EDUSERVICES" else \
    [c for c in TOUS if CODE[c["marque"]]==CIBLE] or [c for c in TOUS if c["ent"]==CIBLE]
P=EX-1
p_=sum(c["eb"][P] for c in C); n_=sum(c["eb"][EX] for c in C)
vol=pri=cva=cdi=sie=0.0
for c in C:
    ep,en=c["eff"][P],c["eff"][EX]
    cap,can=c["ca"][P]/ep,c["ca"][EX]/en
    cvp,cvn=c["cvar"][P]/ep,c["cvar"][EX]/en
    vol+=(en-ep)*(cap-cvp); pri+=(can-cap)*en; cva+=-(cvn-cvp)*en
    cdi+=-(c["cdir"][EX]-c["cdir"][P]); sie+=-(c["csiege"][EX]-c["csiege"][P])
EFFETS=[vol,pri,cva,cdi,sie]
LIB=["EBITDA %d"%P,"Effet effectifs","Effet prix et mix","Effet cout variable unitaire",
     "Effet couts directs","Effet siege","EBITDA %d"%EX]
dv=n_-p_
T=[];G=[];cum=p_
for r in range(1,8):
    if r==1:   m,so,an,ha,ba,pa = p_,0,p_,0,0,None
    elif r==7: m,so,an,ha,ba,pa = n_,0,n_,0,0,None
    else:
        m=EFFETS[r-2]; av=cum; cum=av+m
        so,an,ha,ba = min(av,cum),0,max(m,0),max(-m,0); pa=m/dv if dv else None
    T.append((r,LIB[r-1],round(m),pa)); G.append((LIB[r-1],round(so),round(an),round(ha),round(ba)))

wb=openpyxl.Workbook(); ws=wb.active; ws.title="Drill EBITDA"
ws.sheet_view.showGridLines=False
ws.column_dimensions["A"].width=2.5; ws.column_dimensions["B"].width=5
ws.column_dimensions["C"].width=30
for col in "DE": ws.column_dimensions[col].width=13
ws.column_dimensions["F"].width=3
ws.column_dimensions["G"].width=26
for col in "HIJK": ws.column_dimensions[col].width=12
for r in range(1,40):
    for c in range(1,14): ws.cell(r,c).fill=fill(CANVAS)
for r in (1,2,3):
    for c in range(1,14): ws.cell(r,c).fill=fill(NAVY)
t=ws.cell(2,3,"POURQUOI L'EBITDA A BOUGÉ"); t.font=F(15,True,"FFFFFF",f=DISPLAY); t.alignment=ind(0)
u=ws.cell(3,3,"drill sur %s · exercice %d contre %d · V_ALLOCATION"%(CIBLE,EX,P))
u.font=F(8,False,ONDARK); u.alignment=ind(0)
for r,h in ((1,8),(2,26),(3,15),(4,8),(5,18),(6,16)): ws.row_dimensions[r].height=h
for r in range(7,14): ws.row_dimensions[r].height=16

s=ws.cell(5,3,"Q_D1_TABLEAU"); s.font=F(10,True,INK,f=DISPLAY); s.alignment=ind(0)
s=ws.cell(5,7,"Q_D1_GRAPHE"); s.font=F(10,True,INK,f=DISPLAY); s.alignment=ind(0)
for c0,titres in ((2,("RANG","EFFET","MONTANT","PART_VAR")),
                  (7,("ETAPE","SOCLE","ANCRE","HAUSSE","BAISSE"))):
    for j,x in enumerate(titres):
        cc=ws.cell(6,c0+j,x); cc.fill=fill(SLATE); cc.font=F(8,True,"FFFFFF",f=DISPLAY)
        cc.alignment=Cn if j else ind(1)
        cc.border=Border(*[sd(SLATE)]*4)
for i,(rg,lab,mt,pa) in enumerate(T,7):
    niveau = rg in (1,7)
    for c in range(2,6):
        x=ws.cell(i,c); x.fill=fill(SOFT if niveau else PANEL); x.border=Border(bottom=sd())
    a=ws.cell(i,2,rg); a.font=F(7.5,False,MUTED); a.alignment=Cn
    b=ws.cell(i,3,lab); b.font=F(8.5,niveau); b.alignment=ind(1)
    m=ws.cell(i,4,mt); m.number_format='#,##0" €"'; m.alignment=R; m.font=F(8.5,niveau)
    if pa is not None:
        q=ws.cell(i,5,round(pa,4)); q.number_format='0.0%'; q.alignment=R; q.font=F(8.5,False,MUTED)
for i,(et,so,an,ha,ba) in enumerate(G,7):
    for j,v in enumerate((et,so,an,ha,ba)):
        x=ws.cell(i,7+j,v); x.fill=fill(PANEL); x.border=Border(bottom=sd())
        if j: x.number_format='#,##0'; x.alignment=R
        else: x.alignment=ind(1)
        x.font=F(8.5)
ws.conditional_formatting.add("D8:D12",CellIsRule(operator="greaterThan",formula=["0"],
    font=Font(name=UI,size=8.5,color=GOOD)))
ws.conditional_formatting.add("D8:D12",CellIsRule(operator="lessThan",formula=["0"],
    font=Font(name=UI,size=8.5,color=CRIT)))
ws.cell(15,3,"Contrôle · les cinq effets redonnent l'EBITDA d'arrivée")
ws.cell(15,3).font=F(8,True,MUTED)
k=ws.cell(15,4,"=D8+D9+D10+D11+D12+D13-D14"); k.number_format='0.00" €"'; k.alignment=R
k.font=F(9,True,GOOD)

br=BarChart(); br.type="col"; br.grouping="stacked"; br.overlap=100; br.gapWidth=45
for c in range(8,12):
    br.add_data(Reference(ws,min_col=c,max_col=c,min_row=7,max_row=13),titles_from_data=False)
for x,coul in zip(br.series,(None,SLATE,GOOD,CRIT)):
    if coul is None: x.graphicalProperties.noFill=True
    else: x.graphicalProperties.solidFill=coul; x.graphicalProperties.line.noFill=True
for x in br.series: x.cat=AxDataSource(strRef=StrRef(f="'Drill EBITDA'!$G$7:$G$13"))
br.legend=None; br.y_axis.numFmt='#,##0'; br.height=9.5; br.width=21
br.visible_cells_only=False; br.x_axis.delete=False; br.y_axis.delete=False
br.x_axis.majorTickMark="none"; br.y_axis.majorTickMark="none"
ws.add_chart(br,"C18")
wb.save(OUT)

import zipfile,re
z=zipfile.ZipFile(OUT); c=z.read("xl/charts/chart1.xml").decode()
print("%s — cellule %s, exercice %d"%(OUT,CIBLE,EX))
print("  tableau B7:E13, graphe G7:K13")
print("  cascade : %d series | refs %s"%(c.count("<ser>"),sorted(set(re.findall(r"<f>([^<]+)</f>",c)))))
print("  reference hors classeur :",any(".xls" in r for r in re.findall(r"<f>([^<]+)</f>",c)))
print("  noms definis :",re.findall(r'<definedName name="([^"]+)"',z.read("xl/workbook.xml").decode()) or "aucun")
print("  controle du pont : %.6f EUR"%(p_+sum(EFFETS)-n_))
