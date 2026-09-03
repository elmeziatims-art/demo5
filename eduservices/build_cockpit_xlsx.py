#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COCKPIT_EDUSERVICES.xlsx — le dashboard exécutif en Excel.
Onglet 1 « Données » : le SOCLE CAMPUS (seule saisie) + paramètres + zone technique des graphes.
Onglet 2 « Cockpit »  : 100% formules — tuiles KPI, 3 graphes, grille marque/campus repliable.
Aucune cellule fusionnée dans la grille de données (seulement bandeaux et notes)."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference, Series
from openpyxl.chart.marker import Marker
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import DataBarRule, CellIsRule
from openpyxl.utils import get_column_letter

# ---------- palette (identique au dashboard web, validée) ----------
BLUE="2A78D6"; BLUE2="7AABE6"; BLUE3="C3D9F4"; BLUESOFT="DCE9F9"
ORANGE="EB6834"; ORANGESOFT="FBE3D8"
GOOD="0CA30C"; WARN="FAB219"; CRIT="D03B3B"
INK="131922"; INK2="4D5866"; INK3="7C8798"
CANVAS="EEF1F6"; PANEL="FFFFFF"; PANEL2="F7F9FC"; LINE="DFE4EC"; LINE2="EAEEF4"
WHITE="FFFFFF"
UI="Segoe UI"; MONO="Consolas"

def F(sz=10,b=False,c=INK,f=UI): return Font(name=f,size=sz,bold=b,color=c)
def fill(c): return PatternFill("solid",fgColor=c)
def side(c=LINE): return Side(style="thin",color=c)
L=Alignment("left",vertical="center"); R=Alignment("right",vertical="center")
C=Alignment("center",vertical="center"); TOP=Alignment("left",vertical="top",wrap_text=True)
def indent(n): return Alignment("left",vertical="center",indent=n)

EUR='#,##0'; PCT='0.0%'; PCT0='0%'
DPCT='"▲ "0.0%;"▼ "0.0%'
DPT ='"↗ +"0.0" pt";"↘ −"0.0" pt";"→ "0.0" pt"'
MEUR='#,##0.00,," M€"'

def box(ws,r1,c1,r2,c2,bg=PANEL,bd=LINE):
    """Peint un panneau : fond + contour fin (sans fusionner)."""
    for r in range(r1,r2+1):
        for c in range(c1,c2+1):
            cell=ws.cell(r,c); cell.fill=fill(bg)
            t=side(bd) if r==r1 else None; b=side(bd) if r==r2 else None
            l=side(bd) if c==c1 else None; rr=side(bd) if c==c2 else None
            cell.border=Border(top=t,bottom=b,left=l,right=rr)

wb=openpyxl.Workbook()

# ==========================================================================================
# ONGLET 1 — DONNÉES
# ==========================================================================================
d=wb.active; d.title="Données"; d.sheet_view.showGridLines=False
for col,w in zip("ABCDEFGHIJK",[18,12,14,14,14,14,14,14,11,12,11]): d.column_dimensions[col].width=w
d.cell(1,1,"SOCLE DE DONNÉES — cockpit EDUSERVICES").font=F(12,True,WHITE)
for c in range(1,12): d.cell(1,c).fill=fill(BLUE)
d.row_dimensions[1].height=24

def h(ws,row,txt):
    ws.cell(row,1,txt).font=F(9.5,True,BLUE)

def hdr(ws,row,labels,start=1):
    for j,t in enumerate(labels,start):
        c=ws.cell(row,j,t); c.font=F(9,True,WHITE); c.fill=fill(INK2); c.alignment=C
        c.border=Border(top=side(INK2),bottom=side(INK2),left=side(INK2),right=side(INK2))

# ---- ① périmètre
h(d,3,"① PÉRIMÈTRE (les filtres du cockpit)")
hdr(d,4,["Filtre","Valeur"])
for i,(k,v) in enumerate([("Scénario","REEL"),("Version","V_FINAL"),("Exercice",2026),
                          ("Période","12 — Cumul"),("Marque","Toutes"),("Campus","Tous"),("Modalité","Toutes")]):
    d.cell(5+i,1,k).font=F(9.5); d.cell(5+i,2,v).font=F(9.5,True)
    d.cell(5+i,1).alignment=L; d.cell(5+i,2).alignment=L

# ---- ② socle campus : LA SEULE SAISIE
h(d,13,"② SOCLE CAMPUS — la seule saisie  (source : V_COCKPIT / V_ALLOCATION, grain campus × exercice)")
hdr(d,14,["Entity","Marque","CA 2024","CA 2025","CA 2026","EBITDA 2024","EBITDA 2025","EBITDA 2026",
          "Inscrits 26","Rempl. 26","Mix alt. 26"])
SOCLE=[
 ("MBWAY_PAR","MBway",3640000,3920664,4250000, 596000, 678784, 812000, 224,.94,.81),
 ("MBWAY_LYO","MBway",2790000,2974742,3180000, 427000, 479129, 528000, 168,.86,.77),
 ("MBWAY_BOR","MBway",2040000,2149621,2270000, 298000, 325885, 350000, 120,.81,.74),
 ("ISCOM_PAR","Iscom",3590000,3783019,4010000, 560000, 645000, 690000, 205,.88,.67),
 ("ISCOM_LIL","Iscom",2420000,2498727,2591085, 342000, 363500, 391990, 136,.81,.62),
 ("PIGIER_BOR","Pigier",2310000,2462687,2640000, 430000, 488000, 545000, 143,.85,.83),
 ("PIGIER_LYO","Pigier",2050000,2173095,2310000, 384652, 410500, 454900, 125,.81,.81),
 ("TUNON_PAR","Tunon",1030000,1069253,1102400, 105000, 106800,  96300,  64,.79,.72),
 ("TUNON_LYO","Tunon", 682827, 744012, 745500,  -6000, -12780, -22400,  44,.67,.66),
]
for i,row in enumerate(SOCLE):
    r=15+i
    for j,v in enumerate(row,1):
        c=d.cell(r,j,v); c.font=F(9.5); c.border=Border(bottom=side(LINE))
        c.alignment=L if j<=2 else R
        if 3<=j<=8: c.number_format=EUR
        if j==9: c.number_format='#,##0'
        if j in (10,11): c.number_format=PCT0
d.cell(24,1,"TOTAL GROUPE").font=F(9.5,True)
for j in range(3,10):
    c=d.cell(24,j,"=SUM(%s15:%s23)"%(get_column_letter(j),get_column_letter(j)))
    c.font=F(9.5,True); c.number_format=EUR if j<9 else '#,##0'; c.alignment=R
    c.border=Border(top=side(INK3))

# ---- ③ acquisition
h(d,26,"③ ACQUISITION & CAPACITÉ (groupe)")
hdr(d,27,["Mesure","2024","2025","2026"])
ACQ=[("Dépenses d'acquisition (€)",358170,394702,434174,EUR),
     ("Inscrits (nouveaux)",1092,1159,1229,'#,##0'),
     ("Remplissage moyen",.87,.86,.85,PCT0)]
for i,(lab,a,b,c_,fmt) in enumerate(ACQ):
    r=28+i
    d.cell(r,1,lab).font=F(9.5); d.cell(r,1).alignment=L
    for j,v in enumerate((a,b,c_),2):
        x=d.cell(r,j,v); x.number_format=fmt; x.font=F(9.5); x.alignment=R; x.border=Border(bottom=side(LINE))

# ---- ④ bridge
h(d,32,"④ BRIDGE EBITDA 2025 → 2026  (l'effet coûts est le résidu : le pont boucle toujours)")
hdr(d,33,["Étape","Montant (€)"])
d.cell(34,1,"EBITDA 2025").font=F(9.5);        d.cell(34,2,"=SUM(G15:G23)")
d.cell(35,1,"Effet activité").font=F(9.5);      d.cell(35,2,211706)
d.cell(36,1,"Effet prix / mix").font=F(9.5);    d.cell(36,2,289000)
d.cell(37,1,"Effet coûts (résidu)").font=F(9.5);d.cell(37,2,"=B38-B34-B35-B36")
d.cell(38,1,"EBITDA 2026").font=F(9.5,True);    d.cell(38,2,"=SUM(H15:H23)")
for r in range(34,39):
    d.cell(r,1).alignment=L; d.cell(r,2).number_format=EUR; d.cell(r,2).alignment=R
    d.cell(r,2).font=F(9.5,r==38); d.cell(r,2).border=Border(bottom=side(LINE))

# ---- ⑤ agrégats marque (calculés)
h(d,40,"⑤ AGRÉGATS PAR MARQUE — 100% calculés depuis ②")
hdr(d,41,["Marque","CA 2024","CA 2025","CA 2026","EBITDA 2024","EBITDA 2025","EBITDA 2026",
          "Marge 2024","Marge 2025","Marge 2026"])
MARQUES=["MBway","Iscom","Pigier","Tunon"]
for i,m in enumerate(MARQUES):
    r=42+i
    d.cell(r,1,m).font=F(9.5); d.cell(r,1).alignment=L
    for j,src in zip(range(2,8),"CDEFGH"):
        c=d.cell(r,j,'=SUMIF($B$15:$B$23,$A%d,%s$15:%s$23)'%(r,src,src))
        c.number_format=EUR; c.font=F(9.5); c.alignment=R
    for j,(num,den) in zip(range(8,11),[(5,2),(6,3),(7,4)]):
        c=d.cell(r,j,"=%s%d/%s%d"%(get_column_letter(num),r,get_column_letter(den),r))
        c.number_format=PCT; c.font=F(9.5,True); c.alignment=R
    for j in range(1,11): d.cell(r,j).border=Border(bottom=side(LINE))

# ---- ⑥ zone technique des graphes
h(d,47,"⑥ ZONE TECHNIQUE — séries des graphes (ne pas saisir)")
# waterfall : Étape | Socle | Ancre | Hausse | Baisse
hdr(d,48,["Étape (waterfall)","Socle","Ancre","Hausse","Baisse"])
WF=[("EBITDA 2025","0","=B34","0","0"),
    ("Activité","=B34","0","=B35","0"),
    ("Prix / mix","=B34+B35","0","=B36","0"),
    ("Coûts","=B38","0","0","=B34+B35+B36-B38"),
    ("EBITDA 2026","0","=B38","0","0")]
for i,(cat,so,an,ha,ba) in enumerate(WF):
    r=49+i
    d.cell(r,1,cat).font=F(9,c=INK3); d.cell(r,1).alignment=L
    for j,v in enumerate((so,an,ha,ba),2):
        c=d.cell(r,j,v); c.number_format=EUR; c.font=F(9,c=INK3); c.alignment=R
# tension base 100
hdr(d,56,["Exercice","Dépenses (base 100)","Inscrits (base 100)"])
for i,(ex,col) in enumerate([(2024,"B"),(2025,"C"),(2026,"D")]):
    r=57+i
    d.cell(r,1,ex).font=F(9,c=INK3); d.cell(r,1).alignment=C; d.cell(r,1).number_format='0'
    d.cell(r,2,"=%s28/$B$28*100"%col).number_format='0.0'
    d.cell(r,3,"=%s29/$B$29*100"%col).number_format='0.0'
    for j in (2,3): d.cell(r,j).font=F(9,c=INK3); d.cell(r,j).alignment=R

d.cell(62,1,"Règle de lecture : la variation d'une MARGE se lit en POINTS (différence), jamais en % relatif.").font=F(9,True,ORANGE)

# ==========================================================================================
# ONGLET 2 — COCKPIT
# ==========================================================================================
w=wb.create_sheet("Cockpit"); w.sheet_view.showGridLines=False
w.column_dimensions["A"].width=2
for col in "CDEFGHIJKLM": w.column_dimensions[col].width=12
w.column_dimensions["B"].width=22
w.column_dimensions["N"].width=2
HEIGHTS={1:6,2:30,3:16,4:6,5:20,6:6,7:15,8:28,9:16,10:8,11:20,32:8,33:20,34:18,49:8,53:6}
for r,hh in HEIGHTS.items(): w.row_dimensions[r].height=hh
for r in range(12,32): w.row_dimensions[r].height=16
for r in range(35,49): w.row_dimensions[r].height=17
for r in (50,51,52): w.row_dimensions[r].height=15

# fond canvas
for r in range(1,58):
    for c in range(1,16): w.cell(r,c).fill=fill(CANVAS)

# ---- bandeau
box(w,2,2,3,13)
w.cell(2,2,"  Cockpit de performance — EDUSERVICES GROUP").font=F(14,True,INK)
w.cell(3,2,"  Constat 2024 → 2026 · socle CRM & comptabilité rapprochés · base du cadrage 2027").font=F(9.5,c=INK3)
w.cell(2,2).alignment=L; w.cell(3,2).alignment=L
w.cell(2,13,"RÉEL · CLÔTURE 2026  ").font=F(9,True,BLUE); w.cell(2,13).alignment=R

# ---- filtres (6 pastilles de 2 colonnes, sans fusion : libellé + valeur côte à côte)
FILT=[("Scénario","=Données!B5"),("Version","=Données!B6"),("Exercice","=Données!B7"),
      ("Période","=Données!B8"),("Marque","=Données!B9"),("Campus","=Données!B10")]
for i,(lab,ref) in enumerate(FILT):
    c1=2+i*2
    box(w,5,c1,5,c1+1,bg=(BLUESOFT if lab=="Exercice" else PANEL),bd=(BLUE if lab=="Exercice" else LINE))
    a=w.cell(5,c1,"  "+lab); a.font=F(9,c=INK3); a.alignment=L
    b=w.cell(5,c1+1,ref); b.font=F(9.5,True,BLUE if lab=="Exercice" else INK); b.alignment=L

# ---- tuiles KPI (6 × 2 colonnes)
KPI=[("Chiffre d'affaires","=C35",MEUR,"=D35",DPCT,False),
     ("EBITDA","=E35",MEUR,"=F35",DPCT,False),
     ("Marge EBITDA","=H35",PCT,"=I35",DPT,False),
     ("Inscrits (nouveaux)","=J35",'#,##0',"=J35/Données!C29-1",DPCT,False),
     ("Coût d'acquisition","=Données!D28/Données!D29",'#,##0" €"',
      "=(Données!D28/Données!D29)/(Données!C28/Données!C29)-1",DPCT,True),
     ("Remplissage moyen","=K35",PCT0,"=(K35-Données!C30)*100",DPT,False)]
for i,(lab,val,fmt,dv,dfmt,alert) in enumerate(KPI):
    c1=2+i*2
    box(w,7,c1,9,c1+1,bd=(WARN if alert else LINE))
    a=w.cell(7,c1,"  "+lab.upper()); a.font=F(8.5,True,INK3); a.alignment=L
    v=w.cell(8,c1,val); v.font=F(20,True,INK,MONO); v.number_format=fmt; v.alignment=indent(1)
    x=w.cell(9,c1,dv); x.font=F(9.5,True); x.number_format=dfmt; x.alignment=indent(1)
    w.conditional_formatting.add("%s9"%get_column_letter(c1),
        CellIsRule(operator="greaterThan",formula=["0"],font=Font(name=UI,size=9.5,bold=True,color=GOOD)))
    w.conditional_formatting.add("%s9"%get_column_letter(c1),
        CellIsRule(operator="lessThan",formula=["0"],font=Font(name=UI,size=9.5,bold=True,color=CRIT)))
# le CAC qui monte est une MAUVAISE nouvelle : on inverse son code couleur
w.conditional_formatting.add("J9",CellIsRule(operator="greaterThan",formula=["0"],
    font=Font(name=UI,size=9.5,bold=True,color=CRIT)))

# ---- 3 panneaux graphiques
PANELS=[(2,5,"Bridge EBITDA 2025 → 2026","M€ · axe tronqué à 3,2"),
        (6,9,"Marge EBITDA par marque","2024 · 2025 · 2026"),
        (10,13,"Tension acquisition","base 100 = 2024")]
for c1,c2,title,hint in PANELS:
    box(w,11,c1,31,c2)
    t=w.cell(11,c1,"  "+title); t.font=F(10.5,True,INK); t.alignment=L
    hn=w.cell(11,c2,hint+"  "); hn.font=F(8.5,c=INK3); hn.alignment=R

# --- graphe 1 : waterfall
wf=BarChart(); wf.type="col"; wf.grouping="stacked"; wf.overlap=100; wf.gapWidth=45
wf.height=7.9; wf.width=10.2; wf.legend=None; wf.y_axis.numFmt='#,##0,," M€"'
wf.y_axis.scaling.min=3200000; wf.y_axis.scaling.max=4000000; wf.y_axis.majorUnit=200000
wf.x_axis.delete=False; wf.y_axis.delete=False
for col in (2,3,4,5):
    wf.add_data(Reference(d,min_col=col,max_col=col,min_row=49,max_row=53),titles_from_data=False)
s_so,s_an,s_ha,s_ba=wf.series
s_so.graphicalProperties.noFill=True; s_so.graphicalProperties.line.noFill=True
for s,col in ((s_an,BLUE),(s_ha,GOOD),(s_ba,CRIT)):
    s.graphicalProperties.solidFill=col; s.graphicalProperties.line.solidFill=col
for s,fmt in ((s_an,'#,##0,,.000" M€"'),(s_ha,'"+ "#,##0" €"'),(s_ba,'"− "#,##0" €"')):
    s.dLbls=DataLabelList(); s.dLbls.showVal=True; s.dLbls.numFmt=fmt; s.dLbls.dLblPos="ctr"
    s.dLbls.showSerName=False; s.dLbls.showCatName=False; s.dLbls.showLegendKey=False
wf.set_categories(Reference(d,min_col=1,max_col=1,min_row=49,max_row=53))
w.add_chart(wf,"B12")

# --- graphe 2 : marge EBITDA par marque, 3 ans (rampe séquentielle, pas 3 teintes)
mg=BarChart(); mg.type="col"; mg.grouping="clustered"; mg.gapWidth=60; mg.overlap=-10
mg.height=7.9; mg.width=8.4; mg.y_axis.numFmt='0%'
mg.y_axis.scaling.min=0; mg.y_axis.scaling.max=0.22; mg.y_axis.majorUnit=0.05
mg.x_axis.delete=False; mg.y_axis.delete=False
for col,cc in ((8,BLUE3),(9,BLUE2),(10,BLUE)):
    ref=Reference(d,min_col=col,max_col=col,min_row=41,max_row=45)
    mg.add_data(ref,titles_from_data=True)
for s,cc in zip(mg.series,(BLUE3,BLUE2,BLUE)):
    s.graphicalProperties.solidFill=cc; s.graphicalProperties.line.solidFill=cc
mg.series[2].dLbls=DataLabelList(); mg.series[2].dLbls.showVal=True
mg.series[2].dLbls.numFmt='0.0%'; mg.series[2].dLbls.dLblPos="outEnd"
mg.series[2].dLbls.showSerName=False; mg.series[2].dLbls.showCatName=False; mg.series[2].dLbls.showLegendKey=False
mg.set_categories(Reference(d,min_col=1,max_col=1,min_row=42,max_row=45))
mg.legend.position="b"
w.add_chart(mg,"F12")

# --- graphe 3 : tension (2 séries indexées base 100 — un seul axe)
tn=LineChart(); tn.height=7.9; tn.width=8.4
tn.y_axis.numFmt='0'; tn.y_axis.scaling.min=95; tn.y_axis.scaling.max=125; tn.y_axis.majorUnit=10
tn.x_axis.delete=False; tn.y_axis.delete=False
for col,cc,name in ((2,ORANGE,"Dépenses d'acquisition"),(3,BLUE,"Inscrits")):
    ref=Reference(d,min_col=col,max_col=col,min_row=56,max_row=59)
    tn.add_data(ref,titles_from_data=True)
for s,cc in zip(tn.series,(ORANGE,BLUE)):
    s.graphicalProperties.line.solidFill=cc; s.graphicalProperties.line.width=25000
    s.marker=Marker(symbol="circle",size=6); s.smooth=False
    s.marker.graphicalProperties.solidFill=cc; s.marker.graphicalProperties.line.solidFill=cc
tn.set_categories(Reference(d,min_col=1,max_col=1,min_row=57,max_row=59))
tn.legend.position="b"
w.add_chart(tn,"J12")

# ---- grille marque / campus
box(w,33,2,48,13)
w.cell(33,2,"  Portefeuille — marque & campus").font=F(10.5,True,INK); w.cell(33,2).alignment=L
w.cell(33,13,"exercice 2026 · variation vs 2025  ").font=F(8.5,c=INK3); w.cell(33,13).alignment=R
COLS=["Marque / campus","CA 2026","Δ CA","EBITDA","Δ EBITDA","Part EBITDA","Marge EBITDA",
      "Δ marge","Inscrits","Rempl.","Mix alt.","Alerte"]
for j,t in enumerate(COLS,2):
    c=w.cell(34,j,t); c.font=F(8.5,True,INK3); c.fill=fill(PANEL2); c.alignment=L if j==2 else R
    c.border=Border(bottom=side(LINE),top=side(LINE))

SRC="Données!$A$15:$K$23"; MK="Données!$B$15:$B$23"
ROWS=[("GROUPE",0),("MBway",1),("MBWAY_PAR",2),("MBWAY_LYO",2),("MBWAY_BOR",2),
      ("Iscom",1),("ISCOM_PAR",2),("ISCOM_LIL",2),
      ("Pigier",1),("PIGIER_BOR",2),("PIGIER_LYO",2),
      ("Tunon",1),("TUNON_PAR",2),("TUNON_LYO",2)]
for i,(name,lvl) in enumerate(ROWS):
    r=35+i
    w.cell(r,2,name).alignment=indent(lvl)
    w.cell(r,2).font=F(10 if lvl==0 else 9.5, lvl<=1, INK if lvl<2 else INK2)
    if lvl==0:      # groupe : sommes directes
        f={ "C":"=SUM(Données!$E$15:$E$23)","D":"=C35/SUM(Données!$D$15:$D$23)-1",
            "E":"=SUM(Données!$H$15:$H$23)","F":"=E35/SUM(Données!$G$15:$G$23)-1",
            "G":"=E35/$E$35","H":"=E35/C35",
            "I":"=(H35-SUM(Données!$G$15:$G$23)/SUM(Données!$D$15:$D$23))*100",
            "J":"=SUM(Données!$I$15:$I$23)",
            "K":"=SUMPRODUCT(Données!$I$15:$I$23,Données!$J$15:$J$23)/J35",
            "L":"=SUMPRODUCT(Données!$I$15:$I$23,Données!$K$15:$K$23)/J35","M":'=IF(H35<0.08,"FRAGILE","")'}
    elif lvl==1:    # marque : SUMIF
        S=lambda col: 'SUMIF(%s,$B%d,Données!$%s$15:$%s$23)'%(MK,r,col,col)
        f={ "C":"="+S("E"),"D":"=C%d/%s-1"%(r,S("D")),"E":"="+S("H"),"F":"=E%d/%s-1"%(r,S("G")),
            "G":"=E%d/$E$35"%r,"H":"=E%d/C%d"%(r,r),
            "I":"=(H%d-%s/%s)*100"%(r,S("G"),S("D")),"J":"="+S("I"),
            "K":"=SUMPRODUCT((%s=$B%d)*Données!$I$15:$I$23*Données!$J$15:$J$23)/J%d"%(MK,r,r),
            "L":"=SUMPRODUCT((%s=$B%d)*Données!$I$15:$I$23*Données!$K$15:$K$23)/J%d"%(MK,r,r),
            "M":'=IF(H%d<0.08,"FRAGILE","")'%r}
    else:           # campus : VLOOKUP
        V=lambda n: 'VLOOKUP($B%d,%s,%d,0)'%(r,SRC,n)
        f={ "C":"="+V(5),"D":"=C%d/%s-1"%(r,V(4)),"E":"="+V(8),
            "F":'=IF(%s<=0,"n/s",E%d/%s-1)'%(V(7),r,V(7)),
            "G":"=E%d/$E$35"%r,"H":"=E%d/C%d"%(r,r),
            "I":"=(H%d-%s/%s)*100"%(r,V(7),V(4)),"J":"="+V(9),"K":"="+V(10),"L":"="+V(11),
            "M":'=IF(H%d<0.08,"FRAGILE","")'%r}
    fmts={"C":EUR,"D":DPCT,"E":EUR,"F":DPCT,"G":'0.0%;-0.0%',"H":'0.0%;-0.0%',"I":DPT,
          "J":'#,##0',"K":PCT0,"L":PCT0,"M":"General"}
    for col,formula in f.items():
        c=w.cell(r,openpyxl.utils.column_index_from_string(col),formula)
        c.number_format=fmts[col]; c.alignment=R if col!="M" else C
        c.font=F(9.5,lvl<=1,INK if lvl<2 else INK2,MONO if col!="M" else UI)
    if col=="M": pass
    w.cell(r,13).font=F(8,True,ORANGE)
    for j in range(2,14):
        w.cell(r,j).border=Border(bottom=side(LINE2))
        if lvl==0: w.cell(r,j).fill=fill(PANEL2)
    if lvl==2:
        w.row_dimensions[r].outlineLevel=2; w.row_dimensions[r].hidden=False
    elif lvl==1:
        w.row_dimensions[r].outlineLevel=1
w.sheet_properties.outlinePr.summaryBelow=False

# barre de données sur la marge (la colonne EST la viz)
w.conditional_formatting.add("H35:H48",
    DataBarRule(start_type="num",start_value=0,end_type="num",end_value=0.22,
                color="FF"+BLUE,showValue=True,minLength=None,maxLength=None))
# couleur des variations
for rng in ("D35:D48","F35:F48","I35:I48"):
    w.conditional_formatting.add(rng,CellIsRule(operator="greaterThan",formula=["0"],
        font=Font(name=MONO,size=9.5,color=GOOD)))
    w.conditional_formatting.add(rng,CellIsRule(operator="lessThan",formula=["0"],
        font=Font(name=MONO,size=9.5,color=CRIT)))
# remplissage sous 75% = alerte
w.conditional_formatting.add("K35:K48",CellIsRule(operator="lessThan",formula=["0.75"],
    font=Font(name=MONO,size=9.5,bold=True,color=WARN)))

# ---- callout
box(w,50,2,52,13,bg=PANEL2)
w.merge_cells(start_row=50,start_column=2,end_row=52,end_column=13)
w.cell(50,2,"  Le signal du cockpit.  Tunon pèse 8,0 % du CA mais 1,9 % de l'EBITDA — et son campus de Lyon est en marge "
            "négative à 67 % de remplissage. À l'inverse, Pigier est la plus petite des trois autres marques et la plus rentable (20,2 %). "
            "Le cadrage 2027 ne peut pas être un « + x % » uniforme : c'est là que s'ouvre la discussion EBITDA par marque.").font=F(9.5,c=INK2)
w.cell(50,2).alignment=TOP
for r in range(50,53): w.cell(r,2).border=Border(left=Side(style="thick",color=ORANGE))

w.cell(54,2,"Source : socle CRM et comptabilité rapprochés (écart 0) · vues V_COCKPIT, V_MOTEUR_CAL, V_ALLOCATION · "
            "les marges se lisent en POINTS. Tout le cockpit est en formules : seul l'onglet Données se saisit.").font=F(8.5,c=INK3)
w.cell(54,2).alignment=L

w.sheet_view.zoomScale=90
wb.active=1
out="/home/user/demo5/eduservices/COCKPIT_EDUSERVICES.xlsx"
wb.save(out); print("SAVED",out)
