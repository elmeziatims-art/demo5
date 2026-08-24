#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cockpit dataviz natif Excel (expert) sur cad : 4 graphes soignes +
donnees sources en formules live. openpyxl preserve graphes/images existants."""
import warnings;warnings.filterwarnings("ignore")
import openpyxl
from openpyxl.chart import LineChart,BarChart,Reference,Series
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.axis import ChartLines
from openpyxl.drawing.line import LineProperties
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.marker import Marker
from openpyxl.styles import Font,PatternFill,Alignment
wb=openpyxl.load_workbook("MOTEUR_adapte.xlsx")
cad=wb["cad"]
NAVY="1F3864";BLUE="2E86DE";GREEN="27AE60";GOLD="C9971B";ORANGE="E8743B";PURPLE="8E44AD";GREY="9AA5B1"
MARQ=[("MBWAY",BLUE),("ISCOM",GREEN),("IPAC",GOLD),("PIGIER",ORANGE),("TUNON",PURPLE)]

def hdr(ref,txt): cad[ref]=txt; cad[ref].font=Font(size=9,bold=True,color=NAVY)
# ================= DONNEES SOURCES (formules live) =================
# --- Poids des marques (CA & marge 2026) en N40:P45 ---
hdr("N40","Poids des marques"); 
cad["N41"]="Marque"; cad["O41"]="CA"; cad["P41"]="Marge"
for c in ("N41","O41","P41"): cad[c].font=Font(size=8,bold=True,color=GREY)
for i,(m,_) in enumerate(MARQ):
    r=42+i
    cad["N%d"%r]=m
    cad["O%d"%r]='=SUMIFS(Allocation!$K:$K,Allocation!$E:$E,"%s",Allocation!$C:$C,"2026")'%m
    cad["P%d"%r]='=SUMIFS(Allocation!$T:$T,Allocation!$E:$E,"%s",Allocation!$C:$C,"2026")'%m
    cad["O%d"%r].number_format='# ##0'; cad["P%d"%r].number_format='# ##0'
# --- Waterfall EBITDA cible -> construit en N48:Q51 ---
hdr("N47","Waterfall EBITDA (cible -> construit)")
cad["N48"]="Etape";cad["O48"]="Base";cad["P48"]="Valeur"
for c in ("N48","O48","P48"): cad[c].font=Font(size=8,bold=True,color=GREY)
# cible=D11, construit=E11, ecart=E11-D11
cad["N49"]="Cible";      cad["O49"]=0;               cad["P49"]="=D11"
cad["N50"]="Ecart";      cad["O50"]="=MIN(D11,E11)"; cad["P50"]="=ABS(E11-D11)"
cad["N51"]="Construit";  cad["O51"]=0;               cad["P51"]="=E11"
for r in (49,50,51):
    cad["O%d"%r].number_format='# ##0';cad["P%d"%r].number_format='# ##0'

def style_axes(ch):
    ch.x_axis.delete=False; ch.y_axis.delete=False
    ch.x_axis.majorGridlines=None
    ch.y_axis.majorGridlines=ChartLines(spPr=GraphicalProperties(ln=LineProperties(solidFill="EEEEEE")))
    ch.x_axis.spPr=GraphicalProperties(ln=LineProperties(solidFill="CCCCCC"))
    for a in (ch.x_axis,ch.y_axis): a.txPr=None

# ================= 1) TRAJECTOIRE (colonnes CA/EBITDA + ligne Effectif) =================
bar=BarChart(); bar.type="col"; bar.grouping="clustered"; bar.title="Trajectoire 2024 -> 2027"
bar.height=7.2; bar.width=13; bar.style=None
data=Reference(cad,min_col=3,max_col=4,min_row=41,max_row=45)  # CA, EBITDA (M EUR)
bar.add_data(data,titles_from_data=True)
bar.set_categories(Reference(cad,min_col=2,min_row=42,max_row=45))
bar.series[0].graphicalProperties=GraphicalProperties(solidFill=BLUE)
bar.series[1].graphicalProperties=GraphicalProperties(solidFill=GREEN)
bar.y_axis.numFmt='0.0'; bar.y_axis.title="M EUR"
line=LineChart()
line.add_data(Reference(cad,min_col=5,min_row=41,max_row=45),titles_from_data=True)  # Effectif
line.series[0].graphicalProperties=GraphicalProperties(ln=LineProperties(solidFill=GOLD,w=28000))
line.series[0].marker=Marker(symbol="circle",size=6)
line.y_axis.axId=200; line.y_axis.title="Effectif"; bar.y_axis.crosses="autoZero"; line.y_axis.crosses="max"
bar+=line
bar.legend.position='b'; style_axes(bar)
cad.add_chart(bar,"B47")

# ================= 2) POIDS DES MARQUES (barres CA par marque, couleurs marque) =================
pm=BarChart(); pm.type="bar"; pm.title="Poids des marques - CA 2026"; pm.height=7.2; pm.width=9; pm.legend=None
pm.add_data(Reference(cad,min_col=15,min_row=41,max_row=46),titles_from_data=True)  # O = CA
pm.set_categories(Reference(cad,min_col=14,min_row=42,max_row=46))
from openpyxl.chart.series import DataPoint
pm.series[0].data_points=[DataPoint(idx=i,spPr=GraphicalProperties(solidFill=MARQ[i][1])) for i in range(5)]
pm.dataLabels=DataLabelList(); pm.dataLabels.showVal=True; pm.dataLabels.numFmt='# ##0'
pm.x_axis.numFmt='# ##0'; style_axes(pm)
cad.add_chart(pm,"H47")

# ================= 3) WATERFALL EBITDA (barres empilees base+valeur) =================
wf=BarChart(); wf.type="col"; wf.grouping="stacked"; wf.overlap=100; wf.title="Waterfall EBITDA : cible -> construit"
wf.height=7.2; wf.width=9; wf.gapWidth=40
base=Reference(cad,min_col=15,min_row=48,max_row=51)  # O Base
val=Reference(cad,min_col=16,min_row=48,max_row=51)   # P Valeur
wf.add_data(base,titles_from_data=True); wf.add_data(val,titles_from_data=True)
wf.set_categories(Reference(cad,min_col=14,min_row=49,max_row=51))
wf.series[0].graphicalProperties=GraphicalProperties(noFill=True)  # base invisible
# valeur : cible bleu, ecart or, construit vert
wf.series[1].data_points=[DataPoint(idx=0,spPr=GraphicalProperties(solidFill=BLUE)),
                          DataPoint(idx=1,spPr=GraphicalProperties(solidFill=GOLD)),
                          DataPoint(idx=2,spPr=GraphicalProperties(solidFill=GREEN))]
wf.legend=None; wf.y_axis.numFmt='# ##0'; style_axes(wf)
cad.add_chart(wf,"B62")

# ================= 4) CAP STRATEGIQUE par campus (barres) =================
pil=wb["Pilotage"]
cap=BarChart(); cap.type="bar"; cap.title="Cap strategique par campus - Cap retenu"; cap.height=9; cap.width=9; cap.legend=None
# Pilotage cap: entites en col C (Ville) rows 13-26, cap retenu en col M
cap.add_data(Reference(pil,min_col=13,min_row=12,max_row=26),titles_from_data=True)  # M cap retenu
cap.set_categories(Reference(pil,min_col=3,min_row=13,max_row=26))
cap.series[0].graphicalProperties=GraphicalProperties(solidFill=NAVY)
cap.dataLabels=DataLabelList(); cap.dataLabels.showVal=True; cap.dataLabels.numFmt='0.00'
style_axes(cap)
cad.add_chart(cap,"H62")

wb.save("MOTEUR_adapte.xlsx")
print("OK 4 graphes dataviz ajoutes sur cad (trajectoire, poids marques, waterfall, cap).")
