#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_drill1_excel.py — le drill 1, moitie requete moitie Excel.

Q_D1_SOCLE ne renvoie que de la matiere additive, une ligne par campus. Toutes
les divisions, tous les tests de signe et la cascade sont des FORMULES du
classeur. On peut donc auditer chaque effet en cliquant dessus.

  B7:L26    la sortie de Q_D1_SOCLE          (valeurs, ecrites par Tagetik)
  N7:R26    les cinq effets, ligne par ligne (formules)
  B29:E35   le tableau du drill              (formules)
  G29:K35   la cascade du graphe             (formules)
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.utils import get_column_letter as GL
from socle_reel import construire

OUT="DRILL1_EXCEL.xlsx"; N,P=2026,2025
NAVY="172033"; SLATE="526071"; INK="202733"; MUTED="69778B"; ONDARK="B8C6DA"
CANVAS="F3F6FA"; PANEL="FFFFFF"; SEP="E9EDF3"; SOFT="EAF2FC"; WARM="FFF1E8"
GOOD="1E9E89"; CRIT="D64545"; UI="Arial"; DISPLAY="Fira Sans Medium"
def F(sz=8.5,b=False,c=INK,i=False,f=None): return Font(name=f or UI,size=sz,bold=b,color=c,italic=i)
fill=lambda c: PatternFill("solid",fgColor=c); sd=lambda c=SEP: Side(style="thin",color=c)
R=Alignment("right",vertical="center"); Cn=Alignment("center",vertical="center")
ind=lambda n: Alignment("left",vertical="center",indent=n)
LIBC={"IPAC_MTP":"Ipac Montpellier","IPAC_NAN":"Ipac Nantes","IPAC_REN":"Ipac Rennes",
 "ISCOM_LIL":"ISCOM Lille","ISCOM_PAR":"ISCOM Paris","ISCOM_TLS":"ISCOM Toulouse",
 "MBWAY_BOR":"MBway Bordeaux","MBWAY_LYO":"MBway Lyon","MBWAY_NAN":"MBway Nantes",
 "MBWAY_PAR":"MBway Paris","PIGIER_BOR":"Pigier Bordeaux","PIGIER_LYO":"Pigier Lyon",
 "TUNON_LYO":"Tunon Lyon","TUNON_PAR":"Tunon Paris"}
C=sorted(construire(),key=lambda c:LIBC[c["ent"]])
R0=7; R1=R0+len(C)-1

wb=openpyxl.Workbook(); ws=wb.active; ws.title="Drill EBITDA"
ws.sheet_view.showGridLines=False
ws.column_dimensions["A"].width=2.5; ws.column_dimensions["B"].width=22
for c in range(3,17): ws.column_dimensions[GL(c)].width=13
for c in (6,7,8,9,10): ws.column_dimensions[GL(c)].width=15
ws.column_dimensions["R"].width=3
for c in range(19,24): ws.column_dimensions[GL(c)].width=15
for r in range(1,60):
    for c in range(1,25): ws.cell(r,c).fill=fill(CANVAS)
for r in (1,2,3):
    for c in range(1,25): ws.cell(r,c).fill=fill(NAVY)
ws.cell(2,2,"POURQUOI L'EBITDA A BOUGÉ").font=F(15,True,"FFFFFF",f=DISPLAY)
ws.cell(2,2).alignment=ind(0)
ws.cell(3,2,"drill sur EDUSERVICES · 2026 contre 2025 · la requête ne renvoie que des sommes, "
            "tout le reste est formule").font=F(8,False,ONDARK)
ws.cell(3,2).alignment=ind(0)
for r,h in ((1,8),(2,26),(3,15),(4,8),(5,17),(6,16)): ws.row_dimensions[r].height=h

def entete(row,c0,titres,titre,note=""):
    t=ws.cell(row-1,c0,titre); t.font=F(10,True,INK,f=DISPLAY); t.alignment=ind(0)
    if note:
        x=ws.cell(row-1,c0+len(titres)-1,note+"  "); x.font=F(7.5,False,MUTED,i=True); x.alignment=R
    for j,lab in enumerate(titres):
        c=ws.cell(row,c0+j,lab); c.fill=fill(SLATE); c.font=F(8,True,"FFFFFF",f=DISPLAY)
        c.alignment=Alignment("center",vertical="center",wrap_text=True) if j else ind(1)
        c.border=Border(*[sd(SLATE)]*4)
    ws.row_dimensions[row].height=30

# En-tetes en clair, identiques a ceux de la requete. Le drill-through affiche
# sa sortie telle quelle : autant que l'utilisateur lise "CA par eleve 2025"
# plutot que CAE_P.
COLS=("Campus","Effectifs 2025","Effectifs 2026","Élèves gagnés",
      "CA par élève 2025","CA par élève 2026",
      "Coût var. par élève 2025","Coût var. par élève 2026",
      "Marge sur coût var. par élève 2025",
      "Coûts directs 2025","Coûts directs 2026","Siège 2025","Siège 2026",
      "EBITDA 2025","EBITDA 2026")
entete(6,2,COLS,"CE QUE LA REQUÊTE RENVOIE  ·  Q_D1_SOCLE","une ligne par campus")
entete(6,19,("Effet effectifs","Effet prix et mix","Effet coût var. unitaire",
             "Effet coûts directs","Effet siège"),
       "CE QUE LE CLASSEUR CALCULE","une multiplication par effet, aucune division")
for i,c in enumerate(C):
    r=R0+i
    ep,en=c["eff"][P],c["eff"][N]
    vals=(LIBC[c["ent"]],ep,en,en-ep,
          round(c["ca"][P]/ep,6),round(c["ca"][N]/en,6),
          round(c["cvar"][P]/ep,6),round(c["cvar"][N]/en,6),
          round(c["ca"][P]/ep-c["cvar"][P]/ep,6),
          c["cdir"][P],c["cdir"][N],c["csiege"][P],c["csiege"][N],
          c["eb"][P],c["eb"][N])
    for col,v in zip(range(2,17),vals):
        x=ws.cell(r,col,v); x.fill=fill(PANEL); x.border=Border(bottom=sd())
        x.font=F(8.5); x.alignment=ind(1) if col==2 else R
        x.number_format='#,##0.00' if col in (6,7,8,9,10) else '#,##0'
    # les cinq effets : une multiplication chacun, plus aucune division
    for col,f_ in zip(range(19,24),(
        '=E{0}*J{0}'.format(r),
        '=(G{0}-F{0})*D{0}'.format(r),
        '=-(I{0}-H{0})*D{0}'.format(r),
        '=-(L{0}-K{0})'.format(r),
        '=-(N{0}-M{0})'.format(r))):
        x=ws.cell(r,col,f_); x.fill=fill(WARM); x.border=Border(bottom=sd())
        x.font=F(8.5); x.alignment=R; x.number_format='#,##0'
TOT=R1+1
ws.cell(TOT,2,"TOTAL du périmètre").font=F(8.5,True); ws.cell(TOT,2).alignment=ind(1)
for col in [3,4,5]+list(range(11,17))+list(range(19,24)):
    x=ws.cell(TOT,col,"=SUM({0}{1}:{0}{2})".format(GL(col),R0,R1))
    x.font=F(8.5,True); x.alignment=R; x.number_format='#,##0'
    x.fill=fill(SOFT); x.border=Border(top=Side(style="medium",color=SLATE))
ws.cell(TOT,2).fill=fill(SOFT); ws.cell(TOT,2).border=Border(top=Side(style="medium",color=SLATE))

# ------------------------------------------------------ le tableau du drill
D0=TOT+3
entete(D0,2,("Ordre","Effet","Montant","Part de la variation"),
       "LE TABLEAU DU DRILL","formules")
entete(D0,7,("Étape","Socle invisible","Ancre","Hausse","Baisse"),
       "LA CASCADE DU GRAPHE","formules")
EBP="=SUM(O{0}:O{1})".format(R0,R1)     # EBITDA_P vient de la query
EBN="=SUM(P{0}:P{1})".format(R0,R1)     # EBITDA_N aussi
LIB=["EBITDA %d"%P,"Effet effectifs","Effet prix et mix","Effet coût var. unitaire",
     "Effet coûts directs","Effet siège","EBITDA %d"%N]
COLEF={2:"S",3:"T",4:"U",5:"V",6:"W"}          # l'effet de chaque rang
for i,lab in enumerate(LIB,1):
    r=D0+i
    for c in list(range(2,6))+list(range(7,12)):
        x=ws.cell(r,c); x.fill=fill(SOFT if i in (1,7) else PANEL); x.border=Border(bottom=sd())
    ws.cell(r,2,i).font=F(7.5,False,MUTED); ws.cell(r,2).alignment=Cn
    ws.cell(r,3,lab).font=F(8.5,i in (1,7)); ws.cell(r,3).alignment=ind(1)
    m = EBP if i==1 else EBN if i==7 else "={0}{1}".format(COLEF[i],TOT)
    x=ws.cell(r,4,m); x.number_format='#,##0" €"'; x.alignment=R; x.font=F(8.5,i in (1,7))
    if i not in (1,7):
        x=ws.cell(r,5,"=IFERROR(D{0}/(D{1}-D{2}),\"\")".format(r,D0+7,D0+1))
        x.number_format='0.0%'; x.alignment=R; x.font=F(8.5,False,MUTED)
    # la cascade : le cumul avant, le cumul apres, et le plus bas des deux
    ws.cell(r,7,lab).font=F(8.5); ws.cell(r,7).alignment=ind(1)
    if i in (1,7):
        ws.cell(r,8,0); ws.cell(r,9,"=D%d"%r); ws.cell(r,10,0); ws.cell(r,11,0)
    else:
        av="D{0}+SUM(D{1}:D{2})".format(D0+1,D0+2,r-1) if i>2 else "D{0}".format(D0+1)
        ap="D{0}+SUM(D{1}:D{2})".format(D0+1,D0+2,r)
        ws.cell(r,8,"=MIN({0},{1})".format(av,ap))
        ws.cell(r,9,0)
        ws.cell(r,10,"=MAX(D%d,0)"%r)
        ws.cell(r,11,"=MAX(-D%d,0)"%r)
    for c in range(8,12):
        ws.cell(r,c).number_format='#,##0'; ws.cell(r,c).alignment=R; ws.cell(r,c).font=F(8.5)
ws.conditional_formatting.add("D{0}:D{1}".format(D0+2,D0+6),
    CellIsRule(operator="greaterThan",formula=["0"],font=Font(name=UI,size=8.5,color=GOOD)))
ws.conditional_formatting.add("D{0}:D{1}".format(D0+2,D0+6),
    CellIsRule(operator="lessThan",formula=["0"],font=Font(name=UI,size=8.5,color=CRIT)))
CTRL=D0+9
ws.cell(CTRL,3,"Contrôle · les cinq effets moins la variation d’EBITDA").font=F(8,True,MUTED)
ws.cell(CTRL,3).alignment=ind(1)
k=ws.cell(CTRL,4,"=SUM(D{0}:D{1})-(D{2}-D{3})".format(D0+2,D0+6,D0+7,D0+1))
k.number_format='0.00" €"'; k.alignment=R; k.font=F(10,True,GOOD)
ws.cell(CTRL,5,"doit valoir 0,00 €").font=F(7.5,False,MUTED,i=True); ws.cell(CTRL,5).alignment=ind(1)

br=BarChart(); br.type="col"; br.grouping="stacked"; br.overlap=100; br.gapWidth=45
for c in range(8,12):
    br.add_data(Reference(ws,min_col=c,max_col=c,min_row=D0+1,max_row=D0+7),titles_from_data=False)
for x,coul in zip(br.series,(None,SLATE,GOOD,CRIT)):
    if coul is None: x.graphicalProperties.noFill=True
    else: x.graphicalProperties.solidFill=coul; x.graphicalProperties.line.noFill=True
for x in br.series:
    x.cat=AxDataSource(strRef=StrRef(f="'Drill EBITDA'!$G${0}:$G${1}".format(D0+1,D0+7)))
br.legend=None; br.y_axis.numFmt='#,##0'; br.height=9.5; br.width=22
br.visible_cells_only=False; br.x_axis.delete=False; br.y_axis.delete=False
br.x_axis.majorTickMark="none"; br.y_axis.majorTickMark="none"
ws.add_chart(br,"C%d"%(CTRL+2))
wb.save(OUT)
print("%s ecrit"%OUT)
print("  Q_D1_SOCLE      B%d:P%d   %d campus, valeurs"%(R0,R1,len(C)))
print("  effets/campus   S%d:W%d   formules"%(R0,R1))
print("  tableau drill   B%d:E%d   formules"%(D0+1,D0+7))
print("  cascade         G%d:K%d   formules"%(D0+1,D0+7))
print("  controle        D%d"%CTRL)
