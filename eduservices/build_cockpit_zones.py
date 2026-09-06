#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_cockpit_zones.py — la variante qui s'appuie sur les ZONES NOMMEES.

Idee de Saad, et elle est meilleure que mes colonnes de relais : si Tagetik
nomme lui-meme la zone de restitution de chaque query, il la redimensionne a
chaque navigation. Les graphes n'ont plus rien a deviner.

TROIS ZONES a nommer cote Tagetik, sur les LIGNES DE DONNEES seules, en-tete
exclu :

    Z_PONT      le bloc du pont          AB..AG   6 colonnes
    Z_MARGE     le bloc marge par marque AI..AU  13 colonnes
    Z_TENSION   le bloc acquisition      AZ..BF   7 colonnes

Une seule zone par query suffit : chaque serie va chercher SA colonne avec
INDEX(zone, 0, rang). Le zero en deuxieme argument veut dire "toute la
colonne", donc la serie suit la hauteur de la zone sans qu'on s'en occupe.

    Z_PONT      1 RANG  2 ETAPE  3 SOCLE  4 ANCRE  5 HAUSSE  6 BAISSE
    Z_MARGE     1 LIBELLE  2 MARGE_2024  3 MARGE_2025  4 MARGE_2026
                5 ECART_PT  6 NIVEAU  7 CODE  8..13 CA et EBITDA par exercice
    Z_TENSION   1 EXERCICE  2 IND_DEPENSES  3 IND_INSCRITS
                4 CAC  5 ECART_PT  6 DEPENSES  7 INSCRITS

Les query ont ete reordonnees pour cela : categorie en premiere colonne utile,
puis les series, contigues. Plus aucune colonne de relais dans le classeur.

Les noms sont definis ici a l'etendue actuelle pour que le fichier s'ouvre
sans erreur. Des que Tagetik les maintient, ce sont les siens qui font foi.

LE PIEGE A CONNAITRE. Une reference de serie stocke le NOM DU CLASSEUR :
'COCKPIT.xlsm'!S_MARGE_CAT. C'est ce qui a fait disparaitre les series la
derniere fois, quand le fichier a change de nom. Excel remet ce prefixe a jour
sur un simple Enregistrer sous, mais pas quand les elements sont COPIES d'un
classeur vers un autre. Donc : ouvrir ce fichier, l'enregistrer sous le nom
voulu, et ne jamais recopier les graphes ailleurs.
"""
import openpyxl, shutil
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.marker import Marker
from openpyxl.chart.data_source import AxDataSource, StrRef, NumDataSource, NumRef
from openpyxl.chart.series import SeriesLabel, Series
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.styles import Font

SRC="COCKPIT_DESIGN.xlsm"; OUT="COCKPIT_ZONES.xlsm"
BLUE="2A78D6"; BLUE2="6FA5DC"; BLUE3="B8CFEC"
SLATE="526071"; GOOD="1E9E89"; CRIT="D64545"; ORANGE="F07B32"

wb=openpyxl.load_workbook(SRC, keep_vba=True); ws=wb["2"]

# les trois zones, a l'etendue du dernier rendu. Tagetik les redefinira.
ZONES={"Z_PONT":"'2'!$AB$7:$AG$11","Z_MARGE":"'2'!$AI$7:$AU$11","Z_TENSION":"'2'!$AZ$7:$BF$9"}
for k,v in ZONES.items(): wb.defined_names[k]=DefinedName(k,attr_text=v)

def serie(zone,rang,nom=None):
    """une colonne de la zone, quelle que soit sa hauteur"""
    cle="S_%s_%d"%(zone[2:],rang)
    wb.defined_names[cle]=DefinedName(cle,attr_text="INDEX(%s,0,%d)"%(zone,rang))
    return "'%s'!%s"%(OUT,cle)

def monte(ch,zone,cat_rang,val_rangs,noms=None):
    ch.series=[]
    for i,rg in enumerate(val_rangs):
        s=Series(idx=i, order=i, val=NumDataSource(NumRef(f=serie(zone,rg))))
        s.cat=AxDataSource(strRef=StrRef(f=serie(zone,cat_rang)))
        if noms: s.tx=SeriesLabel(v=noms[i])
        ch.series.append(s)
    ch.visible_cells_only=False
    ch.x_axis.delete=False; ch.y_axis.delete=False
    ch.x_axis.majorTickMark="none"; ch.y_axis.majorTickMark="none"
    return ch

# on reprend la geometrie et les cadres deja poses, on ne refait que les series
old=list(ws._charts); ws._charts=[]

br=BarChart(); br.type="col"; br.grouping="stacked"; br.overlap=100; br.gapWidth=55
monte(br,"Z_PONT",2,(3,4,5,6))
for s,coul in zip(br.series,(None,SLATE,GOOD,CRIT)):
    if coul is None: s.graphicalProperties.noFill=True
    else: s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
br.legend=None; br.y_axis.numFmt='0.0,," M€"'; br.height=9.0; br.width=8.1
ws.add_chart(br,"D13")

mg=BarChart(); mg.type="col"; mg.grouping="clustered"; mg.gapWidth=60; mg.overlap=-10
monte(mg,"Z_MARGE",1,(2,3,4),("2024","2025","2026"))
for s,coul in zip(mg.series,(BLUE3,BLUE2,BLUE)):
    s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
mg.legend.position="b"; mg.y_axis.numFmt='0%'; mg.height=9.0; mg.width=8.1
ws.add_chart(mg,"H13")

tn=LineChart()
monte(tn,"Z_TENSION",1,(2,3),("Dépenses","Inscrits"))
for s,coul in zip(tn.series,(ORANGE,BLUE)):
    s.graphicalProperties.line.solidFill=coul; s.graphicalProperties.line.width=25000
    s.marker=Marker(symbol="circle",size=6); s.smooth=False
    s.marker.graphicalProperties.solidFill=coul; s.marker.graphicalProperties.line.solidFill=coul
tn.legend.position="b"; tn.y_axis.numFmt='0'
tn.y_axis.scaling.min=95; tn.y_axis.scaling.max=125; tn.y_axis.majorUnit=10
tn.height=9.0; tn.width=8.1
ws.add_chart(tn,"L13")

wb.save(OUT)
print("%s ecrit — %d graphes sur zones nommees, %d noms definis"
      %(OUT,len(ws._charts),len(wb.defined_names)))
