#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_drill3_excel.py — le drill 3, "d'ou vient ce chiffre d'affaires".

LE DERNIER DRILL, ET LE SEUL QUI FAIT TRAVAILLER DEUX REQUETES ENSEMBLE.

  Q_D3_CA_COMPTA   lit les comptes 706, 7062 et 708 tels qu'ils sont poses.
                   C'est la chaine du CONSTAT.
  Q_D3_CA_CRM      part des inducteurs : effectifs x droits de scolarite.
                   C'est la chaine du PILOTAGE.

Un chiffre qui arrive deux fois par deux chemins differents est un chiffre
verifie. La page les met face a face, puis ouvre la seconde chaine : combien
vient du VOLUME, combien vient du PRIX.

ORDRE DE LECTURE :
  1  la reponse en une phrase
  2  les deux chaines face a face, trois comptes et un total
  3  le graphe : la variation decomposee, volume contre prix
  4  le detail des inducteurs, volumes et prix moyens
  5  le controle : la somme des effets doit valoir la variation

AUCUNE DIVISION DANS LES REQUETES. Le prix moyen ne survivrait pas a une somme
-- additionner les prix moyens de quatorze campus ne donne pas le prix moyen du
groupe. Les requetes rendent le montant et le volume ; le classeur divise apres
avoir somme. Le resultat est alors juste a tous les niveaux de la hierarchie.

openpyxl ecrit les noms de fonctions en ANGLAIS : c'est ce que stocke le format
OOXML. Excel affiche RECHERCHEV et SIERREUR a l'ouverture.
"""
import csv, openpyxl
from collections import defaultdict
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import CellIsRule, Rule
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.chart.series import SeriesLabel
from openpyxl.utils import get_column_letter as GL

OUT="DRILL3_EXCEL.xlsx"; N,P=2026,2025
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
# CE QUE LES DEUX REQUETES RENVERRONT — simule pour que le classeur livre soit
# deja rempli. En production, Tagetik ecrase les deux zones.
# ============================================================================
num=lambda v: float(v.replace(",",".")) if v else 0.0
lire=lambda n: list(csv.DictReader(open("data/"+n,encoding="utf-8-sig"),delimiter=";"))
crm=defaultdict(lambda: defaultdict(float))
for r in lire("socle_crm.csv"):
    ex=int(r["EXERCICE"])
    if ex not in (P,N): continue
    a="7062" if r["MODALITE"]=="ALT" else "706"
    crm[a]["v%d"%ex]+=num(r["VOL_EFF"]); crm[a]["m%d"%ex]+=num(r["VOL_EFF"])*num(r["REV_STUD"])
    crm["708"]["v%d"%ex]+=num(r["VOL_NEW"]); crm["708"]["m%d"%ex]+=num(r["VOL_NEW"])*num(r["REV_FRAIS_INS"])
cpt=defaultdict(lambda: defaultdict(float))
for r in lire("compta.csv"):
    ex=int(r["EXERCICE"])
    if ex in (P,N) and r["ENTITY"]!="GRP": cpt[r["ACCOUNT"]][ex]+=num(r["AMOUNT"])

PLAN=(("706", "Scolarité des étudiants en initial","Scolarité initial",   "Effectifs"),
      ("7062","Scolarité des alternants",          "Scolarité alternance","Effectifs"),
      ("708", "Frais d'inscription",               "Frais d'inscription", "Nouveaux inscrits"))
Z_CRM=[(a,l,ct,u,crm[a]["v%d"%P],crm[a]["v%d"%N],crm[a]["m%d"%P],crm[a]["m%d"%N]) for a,l,ct,u in PLAN]
Z_CPT=[(a,l,cpt[a][P],cpt[a][N]) for a,l,_,_ in PLAN]
SEQ=[a for a,_,_,_ in PLAN]

# ============================================================================
# L'OSSATURE
# ============================================================================
ZC0        = 14                 # zones de restitution, colonnes N.. masquees
ZCRM0      = 7                  # Q_D3_CA_CRM     : N7:U12   (8 colonnes)
ZCPT0      = 15                 # Q_D3_CA_COMPTA  : N15:Q20  (4 colonnes)
GC0        = 27                 # sources du graphe : AA, AB, AC
T1, T2     = 9, 37              # lignes d'entete des deux tableaux
T1D, T2D   = T1+1, T2+1         # premieres lignes de donnees
T1T, T2T   = T1D+3, T2D+3       # lignes de total
GRAPH0     = 16
CTRL       = T2T+2
ZR_CRM="$%s$%d:$%s$%d"%(GL(ZC0),ZCRM0,GL(ZC0+7),ZCRM0+5)
ZR_CPT="$%s$%d:$%s$%d"%(GL(ZC0),ZCPT0,GL(ZC0+3),ZCPT0+5)

wb=openpyxl.Workbook(); ws=wb.active; ws.title="Drill chiffre d'affaires"
ws.sheet_view.showGridLines=False
ws.column_dimensions["A"].width=2.5
ws.column_dimensions["B"].width=9
ws.column_dimensions["C"].width=32
for c in range(4,13): ws.column_dimensions[GL(c)].width=13
for c in list(range(ZC0,ZC0+8))+list(range(GC0,GC0+3)):
    ws.column_dimensions[GL(c)].hidden=True
for r in range(1,CTRL+12):
    for c in range(1,13): ws.cell(r,c).fill=fill(CANVAS)
for r in (1,2,3):
    for c in range(1,13): ws.cell(r,c).fill=fill(NAVY)
ws.cell(2,2,"D'OÙ VIENT CE CHIFFRE D'AFFAIRES").font=F(15,True,"FFFFFF",f=DISPLAY)
ws.cell(2,2).alignment=ind(0)
ws.cell(3,2,"drill sur la cellule cliquée · 2026 contre 2025 · deux chaînes confrontées, "
            "les comptes de produit et le socle CRM").font=F(8,False,ONDARK)
ws.cell(3,2).alignment=ind(0)
for r,h in ((1,8),(2,26),(3,15),(4,10),(5,24),(6,14),(7,8)): ws.row_dimensions[r].height=h

def entete(row,titres,titre,note="",c0=2):
    t=ws.cell(row-1,c0,titre); t.font=F(10,True,INK,f=DISPLAY); t.alignment=ind(0)
    ws.row_dimensions[row-1].height=20
    if note:
        x=ws.cell(row-1,c0+len(titres)-1,note+"  "); x.font=F(7.5,False,MUTED,i=True); x.alignment=R
    for j,lab in enumerate(titres):
        c=ws.cell(row,c0+j,lab); c.fill=fill(SLATE); c.font=F(8,True,"FFFFFF",f=DISPLAY)
        c.alignment=WRAP if j>1 else ind(1); c.border=Border(*[sd(SLATE)]*4)
    ws.row_dimensions[row].height=28

def ligne_fond(r,c1,c2,fond=PANEL,bas=None):
    for c in range(c1,c2+1):
        ws.cell(r,c).fill=fill(fond); ws.cell(r,c).border=Border(bottom=bas or sd())

# ============================================================================
# LES DEUX ZONES DE RESTITUTION
# ============================================================================
for j,lab in enumerate(("Compte","Poste","Poste court","Unite comptee","Volume 2025",
                        "Volume 2026","Montant 2025","Montant 2026")):
    ws.cell(ZCRM0-1,ZC0+j,lab).font=F(8,True,MUTED)
for i,l in enumerate(Z_CRM):
    for j,v in enumerate(l): ws.cell(ZCRM0+i,ZC0+j,v)
for j,lab in enumerate(("Compte","Poste","Montant 2025","Montant 2026")):
    ws.cell(ZCPT0-1,ZC0+j,lab).font=F(8,True,MUTED)
for i,l in enumerate(Z_CPT):
    for j,v in enumerate(l): ws.cell(ZCPT0+i,ZC0+j,v)

VC =lambda r,c: '=IFERROR(VLOOKUP($B{r},{z},{c},FALSE),0)'.format(r=r,z=ZR_CRM,c=c)
VCT=lambda r,c: '=IFERROR(VLOOKUP($B{r},{z},{c},FALSE),"")'.format(r=r,z=ZR_CRM,c=c)
VP =lambda r,c: '=IFERROR(VLOOKUP($B{r},{z},{c},FALSE),0)'.format(r=r,z=ZR_CPT,c=c)

# ============================================================================
# 1. LA REPONSE, EN UNE PHRASE
# ============================================================================
ws.cell(5,2,'="Les deux chaînes disent "&TEXT(H{t1},"#,##0 €")&" en 2026, à "'
            '&TEXT(ABS(I{t1}),"#,##0 €")&" près. Le chiffre d\'affaires progresse de "'
            '&TEXT(L{t2},"+#,##0 €")&", dont "&TEXT(J{t2},"#,##0 €")&" de volume et "'
            '&TEXT(K{t2},"#,##0 €")&" de prix."'.format(t1=T1T,t2=T2T)).font=F(13,True,INK,f=DISPLAY)
ws.cell(5,2).alignment=ind(0)
ws.cell(6,2,"le constat comptable et le modèle piloté par les inducteurs, confrontés compte par compte")
ws.cell(6,2).font=F(8.5,False,MUTED,i=True); ws.cell(6,2).alignment=ind(0)

# ============================================================================
# 2. LES DEUX CHAINES FACE A FACE
# ============================================================================
entete(T1,("Compte","Poste","Comptes 2025","Socle CRM 2025","Écart 2025",
           "Comptes 2026","Socle CRM 2026","Écart 2026"),
       "LES DEUX CHAÎNES, FACE À FACE",
       "colonnes D et G · Q_D3_CA_COMPTA   colonnes E et H · Q_D3_CA_CRM")
for i,code in enumerate(SEQ):
    r=T1D+i
    ws.cell(r,2,code); ws.cell(r,3,VCT(r,2))
    ws.cell(r,4,VP(r,3)); ws.cell(r,5,VC(r,7)); ws.cell(r,6,"=D{0}-E{0}".format(r))
    ws.cell(r,7,VP(r,4)); ws.cell(r,8,VC(r,8)); ws.cell(r,9,"=G{0}-H{0}".format(r))
    ws.cell(r,2).font=F(8.5,False,MUTED); ws.cell(r,2).alignment=Cn
    ws.cell(r,3).font=F(8.5); ws.cell(r,3).alignment=ind(1)
    for c in (4,5,7,8):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format='#,##0" €"'
    for c in (6,9):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R
        x.number_format='+#,##0" €";-#,##0" €";"—"'
    ws.row_dimensions[r].height=15.5
ligne_fond(T1T,2,9,SOFT,sd(SLATE,"medium"))
ws.cell(T1T,2,"Total").font=F(9,True); ws.cell(T1T,2).alignment=ind(1)
ws.cell(T1T,3,"chiffre d'affaires du périmètre").font=F(8.5,True,MUTED)
ws.cell(T1T,3).alignment=ind(1)
for c in (4,5,7,8):
    x=ws.cell(T1T,c,"=SUM({0}{1}:{0}{2})".format(GL(c),T1D,T1D+2))
    x.number_format='#,##0" €"'; x.alignment=R; x.font=F(9.5,True,BLUE)
for c in (6,9):
    x=ws.cell(T1T,c,"=SUM({0}{1}:{0}{2})".format(GL(c),T1D,T1D+2))
    x.number_format='+#,##0" €";-#,##0" €";"0 €"'; x.alignment=R; x.font=F(9.5,True,GOOD)
ws.cell(T1T+1,3,"un chiffre qui arrive deux fois par deux chemins différents est un chiffre vérifié. "
                "L'écart doit rester à zéro.")
ws.cell(T1T+1,3).font=F(8,False,MUTED,i=True); ws.cell(T1T+1,3).alignment=ind(0)
for f_,coul in (("OR($F{0}<>0,$I{0}<>0)".format(T1D),CRIT),):
    ws.conditional_formatting.add("B{0}:I{1}".format(T1D,T1D+2),Rule(type="expression",
        formula=[f_],dxf=DifferentialStyle(font=Font(color=coul))))
ws.conditional_formatting.add("B{0}:I{1}".format(T1D,T1D+2),Rule(type="expression",
    formula=['$B{0}<>""'.format(T1D)],
    dxf=DifferentialStyle(fill=PatternFill(bgColor=PANEL),border=Border(bottom=sd()))))

# ============================================================================
# 4. LE DETAIL DES INDUCTEURS
# ============================================================================
entete(T2,("Compte","Unité comptée","Volume 2025","Volume 2026","Δ volume",
           "Prix moyen 2025","Prix moyen 2026","Δ prix","Effet volume","Effet prix","Δ CA"),
       "CE QUI FAIT BOUGER LE CHIFFRE D'AFFAIRES  ·  chaîne CRM",
       "colonnes C à E · Q_D3_CA_CRM   les six dernières sont calculées ici")
for i,code in enumerate(SEQ):
    r=T2D+i
    ws.cell(r,2,code); ws.cell(r,3,VCT(r,4))
    ws.cell(r,4,VC(r,5)); ws.cell(r,5,VC(r,6)); ws.cell(r,6,"=E{0}-D{0}".format(r))
    # le prix moyen se calcule ICI, apres la somme : montant / volume
    ws.cell(r,7,'=IFERROR(VLOOKUP($B{r},{z},7,FALSE)/D{r},0)'.format(r=r,z=ZR_CRM))
    ws.cell(r,8,'=IFERROR(VLOOKUP($B{r},{z},8,FALSE)/E{r},0)'.format(r=r,z=ZR_CRM))
    ws.cell(r,9,"=H{0}-G{0}".format(r))
    ws.cell(r,10,"=F{0}*G{0}".format(r))        # volume valorisé au prix de N-1
    ws.cell(r,11,"=I{0}*E{0}".format(r))        # prix appliqué au volume de N
    ws.cell(r,12,"=J{0}+K{0}".format(r))
    ws.cell(r,2).font=F(8.5,False,MUTED); ws.cell(r,2).alignment=Cn
    ws.cell(r,3).font=F(8.5); ws.cell(r,3).alignment=ind(1)
    for c in (4,5): x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format='#,##0'
    x=ws.cell(r,6); x.font=F(8.5); x.alignment=R; x.number_format='"▲ "#,##0;"▼ "#,##0;"—"'
    for c in (7,8): x=ws.cell(r,c); x.font=F(8.5); x.alignment=R; x.number_format='#,##0.0" €"'
    x=ws.cell(r,9); x.font=F(8.5); x.alignment=R
    x.number_format='+#,##0.0" €";-#,##0.0" €";"—"'
    for c in (10,11,12):
        x=ws.cell(r,c); x.font=F(8.5); x.alignment=R
        x.number_format='+#,##0" €";-#,##0" €";"—"'
    ws.row_dimensions[r].height=15.5
    ws.cell(r,GC0,VCT(r,3))                     # poste court, axe du graphe
    ws.cell(r,GC0+1,"=J%d"%r); ws.cell(r,GC0+2,"=K%d"%r)
ligne_fond(T2T,2,12,SOFT,sd(SLATE,"medium"))
ws.cell(T2T,2,"Total").font=F(9,True); ws.cell(T2T,2).alignment=ind(1)
ws.cell(T2T,3,"les volumes ne s'additionnent pas d'une ligne à l'autre").font=F(8,False,MUTED,i=True)
ws.cell(T2T,3).alignment=ind(1)
for c in (10,11,12):
    x=ws.cell(T2T,c,"=SUM({0}{1}:{0}{2})".format(GL(c),T2D,T2D+2))
    x.number_format='+#,##0" €";-#,##0" €";"0 €"'; x.alignment=R; x.font=F(9.5,True,BLUE)
ws.conditional_formatting.add("B{0}:L{1}".format(T2D,T2D+2),Rule(type="expression",
    formula=['$B{0}<>""'.format(T2D)],
    dxf=DifferentialStyle(fill=PatternFill(bgColor=PANEL),border=Border(bottom=sd()))))
for c,coul in ((6,None),(9,None),(10,None),(11,None),(12,None)):
    L=GL(c)
    ws.conditional_formatting.add("{0}{1}:{0}{2}".format(L,T2D,T2D+2),
        CellIsRule(operator="greaterThan",formula=["0"],font=Font(name=UI,size=8.5,color=GOOD)))
    ws.conditional_formatting.add("{0}{1}:{0}{2}".format(L,T2D,T2D+2),
        CellIsRule(operator="lessThan",formula=["0"],font=Font(name=UI,size=8.5,color=CRIT)))

# ============================================================================
# 5. LE CONTROLE
# ============================================================================
for c in range(2,13):
    x=ws.cell(CTRL,c); x.fill=fill(SOFT)
    x.border=Border(top=sd(SLATE,"medium"),bottom=sd(SLATE,"medium"))
ws.cell(CTRL,2,"Contrôle").font=F(8.5,True,MUTED); ws.cell(CTRL,2).alignment=ind(1)
ws.cell(CTRL,3,"effet volume + effet prix doit valoir la variation du chiffre d'affaires, "
               "sans résidu").font=F(8.5,True,MUTED)
ws.cell(CTRL,3).alignment=ind(1)
# chaque nombre porte son libelle DANS son format : la ligne de controle se lit
# sans dependre des entetes du tableau du dessus, qui disent autre chose.
x=ws.cell(CTRL,10,"=H{0}-E{0}".format(T1T))
x.number_format='"variation "+#,##0;"variation "-#,##0'; x.alignment=R; x.font=F(8.5,False,MUTED)
x=ws.cell(CTRL,11,"=L%d"%T2T)
x.number_format='"effets "+#,##0;"effets "-#,##0'; x.alignment=R; x.font=F(8.5,False,MUTED)
x=ws.cell(CTRL,12,"=K{0}-J{0}".format(CTRL))
x.number_format='"écart "+#,##0" €";"écart "-#,##0" €";"écart 0 €"'
x.alignment=R; x.font=F(10.5,True,BLUE)
for j,txt in enumerate((
   "Pas de terme croisé, pas de résidu : le volume est valorisé au prix de l'an dernier, le prix appliqué au volume de cette année. Les deux effets se somment exactement à la variation.",
   "L'effet prix porte aussi le MIX. Un campus qui bascule des initiaux vers des alternants voit son prix moyen bouger sans qu'aucun tarif ait changé. Pour séparer les deux il faudrait descendre au grain programme × année d'étude ; à ce stade du drill, ce n'est pas la question posée.",
   "Aucune division dans les requêtes. Le prix moyen ne survivrait pas à une somme — additionner les prix moyens de quatorze campus ne donne pas le prix moyen du groupe. Les requêtes rendent le montant et le volume, le classeur divise après avoir sommé.",
   "C'est ce qui rend la page juste à tous les niveaux de la hiérarchie, du campus au groupe, sans que les requêtes aient à savoir à quel niveau elles tournent.")):
    c=ws.cell(CTRL+2+j,2,txt); c.font=F(8,False,MUTED,i=True); c.alignment=ind(1)

# ============================================================================
# 3. LE GRAPHE — la variation decomposee, volume contre prix
# ============================================================================
bc=BarChart(); bc.type="col"; bc.grouping="stacked"; bc.overlap=100; bc.gapWidth=90
for c in (GC0+1,GC0+2):
    bc.add_data(Reference(ws,min_col=c,max_col=c,min_row=T2D,max_row=T2D+2),titles_from_data=False)
for s,coul,nom in zip(bc.series,(BLUE,BLUE3),("Effet volume","Effet prix")):
    s.graphicalProperties.solidFill=coul; s.graphicalProperties.line.noFill=True
    s.tx=SeriesLabel(v=nom)
for s in bc.series:
    s.cat=AxDataSource(strRef=StrRef(f="'Drill chiffre d''affaires'!${0}${1}:${0}${2}"
                                       .format(GL(GC0),T2D,T2D+2)))
bc.legend.position="b"; bc.y_axis.numFmt='#,##0," k€"'
bc.height=9.5; bc.width=20; bc.visible_cells_only=False
bc.x_axis.delete=False; bc.y_axis.delete=False
bc.x_axis.majorTickMark="none"; bc.y_axis.majorTickMark="none"
bc.title=None
ws.add_chart(bc,"B%d"%GRAPH0)
ws.cell(GRAPH0-1,2,"LA VARIATION, DÉCOMPOSÉE  ·  ce que le volume apporte, ce que le prix apporte")
ws.cell(GRAPH0-1,2).font=F(10,True,INK,f=DISPLAY); ws.cell(GRAPH0-1,2).alignment=ind(0)
ws.row_dimensions[GRAPH0-1].height=20
for r in range(GRAPH0,T2-2): ws.row_dimensions[r].height=15
wb.save(OUT)
print("%s ecrit"%OUT)
print("  1 réponse        B5")
print("  2 face à face    B%d:I%d  (3 comptes + total)"%(T1,T1T))
print("  3 graphe         B%d — colonnes empilées, volume contre prix"%GRAPH0)
print("  4 inducteurs     B%d:L%d"%(T2,T2T))
print("  5 contrôle       ligne %d"%CTRL)
print("  zone Q_D3_CA_CRM     %s"%ZR_CRM.replace("$",""))
print("  zone Q_D3_CA_COMPTA  %s"%ZR_CPT.replace("$",""))
print("  sources du graphe    %s à %s masquées"%(GL(GC0),GL(GC0+2)))
