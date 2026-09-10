#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_nav_tagetik.py — la navigation reelle, remise en forme au standard Tagetik.

ENTREE  NAV_SOURCE_ok.xlsx   la navigation du 07/09 sortie de Tagetik
SORTIE  COCKPIT_TAGETIK.xlsx la meme, restylee, corrigee, graphes reconstruits

LA REFERENCE : les trois rapports de demo Tagetik (E150, E221, E223). Ce qu'ils
disent, et qu'on suit ici :

  POLICE      Arial, et rien d'autre. 8 pt pour le corps, 8 pt gras pour les
              entetes et les totaux, 18 a 20 pt pour les grands nombres.
              Aucune police d'affichage -- Fira Sans est abandonnee.

  FONDS       quasi aucun. Le seul remplissage de leurs trois rapports est le
              blanc. Toute la structure est portee par des FILETS HORIZONTAUX :
              un trait fin sous chaque ligne, un trait medium sous les totaux.
              Aucun trait vertical, aucun aplat de couleur.

  PALETTE     celle de leur theme :
                262626  encre        007AC3  azur Tagetik (accent1)
                E5202E  rouge        85BC20  vert
                A6D0EA  bleu pale    E7E6E6  gris clair

  GRILLE      colonne A en gouttiere a 2,4 -- deja le cas ici.

CE QU'ON GARDE DE NOTRE COTE : un fond de page qui n'est pas blanc. C'est ce
qui fait disparaitre les lignes non servies au lieu de les montrer comme un
tableau vide, et c'est le seul point ou l'on s'ecarte de la reference.

=============================================================================
LES CINQ CORRECTIONS DE FOND, TOUTES VERIFIEES SUR LE FICHIER SOURCE

1. DRILL 2, B5 : quatre plages fausses dans une seule formule. Elle etait
   restee sur le tableau a QUATORZE lignes alors qu'il en porte SEIZE depuis
   que le chiffre d'affaires est ouvert en trois comptes.
       lu  : TEXT(F34)  -SUM(F35:F47)  SUM(F34:F47)  /F34
       juste: SUM(F34:F36)  -SUM(F37:F49)  SUM(F34:F49)  /SUM(F34:F36)
   Consequence : le CA affiche etait celui du seul compte 706, les charges
   amputees de deux lignes, et le taux de marge divise par le mauvais total.

2. COCKPIT, D38:E57 : les colonnes Programme et Modalite portent le mot
   "Programme" et le mot "Modalite" sur LES VINGT LIGNES. L'axe de lignes
   s'arrete au campus, ces deux dimensions n'ont donc pas de membre a ce
   niveau et Tagetik y a recopie l'intitule. On les vide.

3. LES ACCENTS DES LIBELLES DE GRAPHE : la zone du pont porte "Activite" et
   "Couts". Ce n'est pas un defaut d'encodage a corriger, c'est une contrainte
   du canal du loader -- un litteral SQL accentue en ressort casse. La bonne
   reponse est de CHOISIR DES MOTS SANS ACCENT : Volume et Charges. Meme sens,
   francais correct, zero accent. A repercuter dans Q_G1_PONT.

4. DRILL 1, ligne 43 : le TOTAL porte un tiret sous "CA par eleve 2025" et
   rien sous les quatre autres colonnes unitaires. Une valeur unitaire ne se
   somme pas : les cinq doivent porter le meme tiret.

5. _xlfn.IFERROR : Tagetik ecrit ses IFERROR prefixes _xlfn. Ce prefixe est
   reserve aux fonctions inconnues du format ; IFERROR est standard depuis
   2007. A verifier a l'ouverture -- si les cellules affichent #NOM?, c'est
   cela. Le fichier de sortie les ecrit sans prefixe.

=============================================================================
CE QUE SAAD A DEMANDE POUR LE DRILL 2

  - une echelle de couleur sur la VARIATION, et le signe qui la double ;
  - la colonne NATURE tout a droite : produit, charge, allocation.

LE POINT QUI COMPTE, ET QUI EST CONTRE-INTUITIF : une seule echelle suffit
pour les seize lignes, produits ET charges. Parce que les montants sont
SIGNES, une variation positive veut toujours dire "cette ligne apporte plus a
l'EBITDA" -- que ce soit un produit qui monte ou une charge qui baisse. Vert
au positif, rouge au negatif, sans exception et sans cas particulier.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import CellIsRule, Rule, ColorScaleRule, DataBarRule
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.marker import Marker
from openpyxl.chart.data_source import AxDataSource, StrRef
from openpyxl.chart.series import SeriesLabel
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter as GL

SRC, OUT = "NAV_SOURCE_ok.xlsx", "COCKPIT_TAGETIK.xlsx"

# ---------------------------------------------------------------- la palette
INK   = "262626"   # dk1     encre
AZUR  = "007AC3"   # accent1 azur Tagetik
ROUGE = "E5202E"   # accent2
VERT  = "85BC20"   # accent3
PALE  = "A6D0EA"   # accent5
GRIS  = "E7E6E6"   # lt2
# Deux variantes assombries : E5202E et 85BC20 passent en aplat et en barre,
# pas en texte de 8 pt sur fond clair, ou ils manquent de contraste.
VERT_T  = "5F8A17"
ROUGE_T = "C41822"
# Notre seul ecart a la reference : un fond de page qui n'est pas blanc.
FOND  = "F5F6F7"
PANEL = "FFFFFF"
FILET = "D5D7DA"
DOUX  = "6B7075"
# Teintes de l'echelle de couleur, derivees des deux accents.
HM_BAS, HM_MED, HM_HAUT = "F6C9CC", "F4F4F2", "DCEBC0"
UI = "Arial"

def F(sz=8, b=False, c=INK, i=False): return Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd   = lambda c=FILET, st="thin": Side(style=st, color=c)
R    = Alignment("right",  vertical="center")
Cn   = Alignment("center", vertical="center")
L    = Alignment("left",   vertical="center")
ind  = lambda n: Alignment("left", vertical="center", indent=n)
WRAP = Alignment("center", vertical="center", wrap_text=True)

wb = openpyxl.load_workbook(SRC)

def bandeau(ws, ncol, titre, sous):
    """Le bandeau de tete : encre pleine, puis le filet azur qui le signe."""
    for r in (1, 2, 3):
        for c in range(1, ncol + 1): ws.cell(r, c).fill = fill(INK)
    for c in range(1, ncol + 1): ws.cell(4, c).fill = fill(AZUR)
    t = ws.cell(2, 3, titre); t.font = F(14, True, "FFFFFF"); t.alignment = ind(0)
    u = ws.cell(3, 3, sous);  u.font = F(8, False, PALE);     u.alignment = ind(0)
    for r, h in ((1, 6), (2, 22), (3, 13), (4, 3)): ws.row_dimensions[r].height = h

def page(ws, ncol, nrow):
    ws.sheet_view.showGridLines = False
    for r in range(1, nrow + 1):
        for c in range(1, ncol + 1): ws.cell(r, c).fill = fill(FOND)

def entete(ws, row, c1, c2):
    """La ligne d'entete : pas d'aplat, du gras, et un filet azur dessous."""
    for c in range(c1, c2 + 1):
        x = ws.cell(row, c); x.fill = fill(FOND); x.font = F(8, True, INK)
        x.border = Border(top=sd(FILET), bottom=sd(AZUR, "medium"))
        if x.alignment.horizontal != "left": x.alignment = WRAP
    ws.row_dimensions[row].height = 26

def titre_bloc(ws, row, col, txt, note="", cnote=None):
    t = ws.cell(row, col, txt); t.font = F(9.5, True, INK); t.alignment = ind(0)
    if note:
        n = ws.cell(row, cnote, note + "  "); n.font = F(7, False, DOUX, True); n.alignment = R
    ws.row_dimensions[row].height = 18

# ============================================================================
#  COCKPIT
# ============================================================================
ws = wb["Cockpit"]
NC, R0, RN, RCF = 17, 38, 57, 120
page(ws, NC, RCF + 4)
bandeau(ws, NC, "COCKPIT EDUSERVICES — PILOTAGE DE LA MARGE",
        "Exercice 2026 · variation contre 2025 · V_ALLOCATION et socle CRM")

ws.column_dimensions["A"].width = 2.4
ws.column_dimensions["B"].width = 4.5; ws.column_dimensions["B"].hidden = True
ws.column_dimensions["C"].width = 30
ws.column_dimensions["D"].width = 13
ws.column_dimensions["E"].width = 11
for c in range(6, 18): ws.column_dimensions[GL(c)].width = 10.7
for c in range(18, 70): ws.column_dimensions[GL(c)].hidden = True

# ---- ligne de filtres : pas d'aplat, un simple filet dessous ---------------
for c in range(3, NC + 1):
    x = ws.cell(5, c); x.fill = fill(FOND); x.border = Border(bottom=sd(FILET))
ws.row_dimensions[5].height = 18
for r in (5,):
    for c in range(2, NC + 1): ws.cell(r, c).value = None
for col, lab, val in ((3, "SCÉNARIO", "Forecast 2026"), (7, "VERSION", "V_FINAL"),
                      (11, "ENTITÉ", "EDUSERVICES")):
    a = ws.cell(5, col, lab); a.font = F(7, True, AZUR); a.alignment = ind(0)
    v = ws.cell(5, col + 1, val); v.font = F(9, True, INK); v.alignment = ind(0)

# ---- les six cartes : un filet azur en tete, rien d'autre ------------------
HB   = '"▲ "0.0%;"▼ "0.0%;"—"'
HBPT = '"▲ "0.00" pt";"▼ "0.00" pt";"—"'
KPI = [(6,  "CHIFFRE D'AFFAIRES", "=F38", '0.0,," M€"', "=G38", HB,   True),
       (8,  "EBITDA",             "=H38", '0.0,," M€"', "=I38", HB,   True),
       (10, "MARGE EBITDA",       "=K38", '0.0%',       "=L38", HBPT, True),
       (12, "INSCRITS (NOUVEAUX)","=M38", '#,##0',      "=AA38",HB,   True),
       (14, "COÛT D'ACQUISITION", "=U38/M38", '#,##0" €"',
            '=IFERROR(N9/(V38/Y38)-1,"")',                      HB,   False),
       (16, "REMPLISSAGE MOYEN",  "=N38", '0.0%',       "=Q38-P38",
            '#,##0" places libres";-#,##0" places libres";"—"', None)]
for r in (7, 8, 9, 10, 11):
    for c in range(2, NC + 1): ws.cell(r, c).value = None
for r, h in ((6, 6), (7, 3), (8, 12), (9, 24), (10, 13), (11, 8), (12, 18)):
    ws.row_dimensions[r].height = h
for col, lab, val, fmt, var, vfmt, sens in KPI:
    for c in (col, col + 1):
        ws.cell(7, c).fill = fill(AZUR)                 # le filet de tete
        for r in (8, 9, 10):
            x = ws.cell(r, c); x.fill = fill(PANEL)
            x.border = Border(bottom=sd(FILET) if r == 10 else None)
    a = ws.cell(8, col, lab);  a.font = F(7, True, DOUX);  a.alignment = ind(1)
    v = ws.cell(9, col, val);  v.font = F(20, False, INK); v.number_format = fmt; v.alignment = ind(1)
    d = ws.cell(10, col, var); d.font = F(8, True, DOUX);  d.number_format = vfmt; d.alignment = ind(1)

# ---- le tableau -----------------------------------------------------------
titre_bloc(ws, 36, 3, "PORTEFEUILLE — MARQUE ET CAMPUS",
           "graisse et filet donnent le niveau · échelle de couleur = performance", 17)
ENT = {6:"CA", 7:"Δ CA", 8:"EBITDA", 9:"Δ EBITDA", 10:"Part EBITDA", 11:"Marge EBITDA",
       12:"Δ Marge (pt)", 13:"Inscrits", 14:"Remplissage", 15:"Mix alternance",
       16:"Effectifs", 17:"Places"}
ws.cell(37, 3, "Entité"); ws.cell(37, 3).alignment = ind(0)
ws.cell(37, 4, "Programme"); ws.cell(37, 5, "Modalité")
for c, lab in ENT.items(): ws.cell(37, c, lab)
entete(ws, 37, 2, NC)
for c in (3, 4, 5): ws.cell(37, c).alignment = ind(0)

FMT = {6:'#,##0', 7:'"▲ "0.0%;"▼ "0.0%;""', 8:'#,##0', 9:'"▲ "0.0%;"▼ "0.0%;""',
       10:'0.0%', 11:'0.0%', 12:'"▲ "0.00;"▼ "0.00;""', 13:'#,##0', 14:'0.0%',
       15:'0.0%', 16:'#,##0', 17:'#,##0'}
# CORRECTION 2 : Programme et Modalite portaient leur intitule sur les vingt
# lignes. L'axe s'arrete au campus, ces colonnes n'ont pas de membre ici.
for r in range(R0, RCF + 1):
    for c in (4, 5):
        if ws.cell(r, c).value in ("Programme", "Modalité"): ws.cell(r, c).value = None
    for c in range(2, NC + 1):
        x = ws.cell(r, c); x.border = Border(); x.fill = fill(FOND)
    ws.cell(r, 3).font = F(8); ws.cell(r, 3).alignment = ind(0)
    for c in (4, 5): ws.cell(r, c).font = F(7.5, False, DOUX); ws.cell(r, c).alignment = ind(0)
    for c in range(6, NC + 1):
        x = ws.cell(r, c); x.font = F(8); x.alignment = R; x.number_format = FMT[c]
    ws.row_dimensions[r].height = 14.25

# ---- les regles, dans l'ordre qui compte ----------------------------------
ws.conditional_formatting = ConditionalFormattingList()
rg = lambda c1, c2=None: "%s%d:%s%d" % (GL(c1), R0, GL(c2 or c1), RCF)
for c1, lo, mid, hi in ((11, 0.02, 0.12, 0.22), (14, 0.55, 0.75, 0.95)):
    ws.conditional_formatting.add(rg(c1), ColorScaleRule(
        start_type="num", start_value=lo, start_color="FF" + HM_BAS,
        mid_type="num",   mid_value=mid,  mid_color="FF" + HM_MED,
        end_type="num",   end_value=hi,   end_color="FF" + HM_HAUT))
ws.conditional_formatting.add(rg(10), DataBarRule(
    start_type="num", start_value=0, end_type="num", end_value=1.0,
    color="FF" + PALE, showValue=True))
for c1 in (7, 9, 12):
    ws.conditional_formatting.add(rg(c1), CellIsRule(operator="greaterThan",
        formula=["0"], font=Font(name=UI, size=8, color=VERT_T)))
    ws.conditional_formatting.add(rg(c1), CellIsRule(operator="lessThan",
        formula=["0"], font=Font(name=UI, size=8, color=ROUGE_T)))
def niveau(f_, **k):
    ws.conditional_formatting.add("B%d:%s%d" % (R0, GL(NC), RCF),
        Rule(type="expression", formula=[f_], dxf=DifferentialStyle(**k)))
# LA GRAMMAIRE DE LA REFERENCE : un seul aplat, celui du total. Les deux
# autres niveaux se distinguent par la GRAISSE et le FILET, pas par la couleur.
niveau('$B%d=2' % R0, font=Font(bold=True, color=INK), fill=PatternFill(bgColor=GRIS),
       border=Border(top=Side(style="medium", color=INK), bottom=Side(style="medium", color=INK)))
niveau('$B%d=3' % R0, font=Font(bold=True, color=INK), fill=PatternFill(bgColor=PANEL),
       border=Border(bottom=Side(style="thin", color=INK)))
niveau('$B%d=4' % R0, font=Font(color=INK), fill=PatternFill(bgColor=PANEL),
       border=Border(bottom=Side(style="thin", color=FILET)))
niveau('$B%d=5' % R0, font=Font(color=DOUX), fill=PatternFill(bgColor=PANEL),
       border=Border(bottom=Side(style="hair", color=FILET)))
for col in (6, 8):
    ws.conditional_formatting.add("%s9" % GL(col), Rule(type="cellIs", operator="lessThan",
        formula=["1000000"], dxf=DifferentialStyle(numFmt=openpyxl.styles.numbers
        .NumberFormat(numFmtId=180 + col, formatCode='#,##0" €"'))))
for col, bon in ((6, True), (8, True), (10, True), (12, True), (14, False)):
    cell = "%s10" % GL(col)
    ws.conditional_formatting.add(cell, CellIsRule(operator="greaterThan", formula=["0"],
        font=Font(name=UI, size=8, bold=True, color=VERT_T if bon else ROUGE_T)))
    ws.conditional_formatting.add(cell, CellIsRule(operator="lessThan", formula=["0"],
        font=Font(name=UI, size=8, bold=True, color=ROUGE_T if bon else VERT_T)))

# CORRECTION 3 : des mots sans accent plutot qu'un accent qui ne passe pas.
for r in range(7, 12):
    v = ws.cell(r, 30).value
    if v == "Activite": ws.cell(r, 30).value = "Volume"
    if v == "Couts":    ws.cell(r, 30).value = "Charges"
ws.cell(RN + 3, 3, "Source : V_ALLOCATION et AW_002_000002_000001. Marges, remplissage et coût "
                   "d'acquisition sont divisés après somme, jamais moyennés.")
ws.cell(RN + 3, 3).font = F(7, False, DOUX, True); ws.cell(RN + 3, 3).alignment = ind(0)

# ============================================================================
#  DRILL EBITDA 1 — pourquoi l'EBITDA a bouge
# ============================================================================
d1 = wb["Drill EBITDA 1"]
page(d1, 24, 80)
bandeau(d1, 24, "POURQUOI L'EBITDA A BOUGÉ",
        "drill sur la cellule cliquée · 2026 contre 2025 · cinq effets, sans reste")
d1.column_dimensions["A"].width = 2.4
for L_, w_ in (("B", 26), ("C", 13), ("D", 15), ("E", 12), ("F", 13), ("G", 13),
               ("H", 15), ("I", 15), ("J", 19), ("K", 14), ("L", 14), ("M", 12),
               ("N", 12), ("O", 13), ("P", 13), ("R", 2.4), ("S", 14), ("T", 14),
               ("U", 15), ("V", 14), ("W", 13)):
    d1.column_dimensions[L_].width = w_
for c in range(25, 32): d1.column_dimensions[GL(c)].hidden = True

d1.cell(6, 2).font = F(12.5, True, INK); d1.cell(6, 2).alignment = ind(0)
d1.row_dimensions[6].height = 20
d1.cell(7, 2).font = F(8, False, DOUX, True); d1.cell(7, 2).alignment = ind(0)

titre_bloc(d1, 10, 2, "LE PONT, CHIFFRE PAR CHIFFRE",
           "chaque effet rapporté à sa masse : ce qui pousse, ou ce qui freine", 4)
entete(d1, 11, 2, 4)
d1.cell(11, 2).alignment = ind(0)
for r in range(12, 19):
    tete = r in (12, 18)
    for c in range(2, 5):
        x = d1.cell(r, c); x.fill = fill(GRIS if tete else PANEL)
        x.border = Border(bottom=sd(INK, "medium") if tete else sd(FILET))
    d1.cell(r, 2).font = F(9, tete); d1.cell(r, 2).alignment = ind(0)
    x = d1.cell(r, 3); x.font = F(9, tete); x.alignment = R; x.number_format = '#,##0" €"'
    x = d1.cell(r, 4); x.font = F(8, False, DOUX); x.alignment = R; x.number_format = '0.0%'
    d1.row_dimensions[r].height = 15
for c in range(2, 5):
    x = d1.cell(19, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
d1.cell(19, 2).font = F(8, True, DOUX); d1.cell(19, 2).alignment = ind(0)
x = d1.cell(19, 3); x.font = F(9, True, VERT_T);  x.alignment = R; x.number_format = '+#,##0" €"'
x = d1.cell(19, 4); x.font = F(9, True, ROUGE_T); x.alignment = R; x.number_format = '-#,##0" €"'
d1.cell(20, 2, "la variation nette est le SOLDE de ces deux masses, pas un mouvement : "
               "c'est pourquoi chaque effet est rapporté à la sienne")
d1.cell(20, 2).font = F(7, False, DOUX, True); d1.cell(20, 2).alignment = ind(0)
for c in range(2, 5):
    x = d1.cell(21, c); x.fill = fill(PANEL); x.border = Border(top=sd(AZUR, "medium"), bottom=sd(AZUR, "medium"))
d1.cell(21, 2).font = F(8, True, DOUX); d1.cell(21, 2).alignment = ind(0)
x = d1.cell(21, 3); x.font = F(10, True, AZUR); x.alignment = R; x.number_format = '0.00" €"'
d1.cell(21, 4).font = F(7, False, DOUX, True); d1.cell(21, 4).alignment = Cn
d1.conditional_formatting = ConditionalFormattingList()
for op, coul in (("greaterThan", VERT_T), ("lessThan", ROUGE_T)):
    d1.conditional_formatting.add("C13:C17", CellIsRule(operator=op, formula=["0"],
        font=Font(name=UI, size=9, color=coul)))

# ---- le detail par campus + le bloc des effets ----------------------------
titre_bloc(d1, 41, 2, "LE DÉTAIL PAR CAMPUS  ·  ce que la requête renvoie", "une ligne par campus  ", 16)
titre_bloc(d1, 41, 19, "CE QUE LE CLASSEUR CALCULE", "une multiplication par effet  ", 23)
entete(d1, 42, 2, 16); entete(d1, 42, 19, 23)
d1.cell(42, 2).alignment = ind(0)
FMT1 = {3:'#,##0', 4:'#,##0', 5:'#,##0', 6:'#,##0.00" €"', 7:'#,##0.00" €"',
        8:'#,##0.00" €"', 9:'#,##0.00" €"', 10:'#,##0.00" €"', 11:'#,##0" €"',
        12:'#,##0" €"', 13:'#,##0" €"', 14:'#,##0" €"', 15:'#,##0" €"', 16:'#,##0" €"'}
for r in range(43, 74):
    tot = r == 43
    for c in list(range(2, 17)) + list(range(19, 24)):
        x = d1.cell(r, c)
        x.fill = fill(GRIS if tot else FOND)
        x.border = Border(top=sd(INK, "medium") if tot else None,
                          bottom=sd(INK, "medium") if tot else None)
    d1.cell(r, 2).font = F(8, tot); d1.cell(r, 2).alignment = ind(0)
    for c in range(3, 17):
        x = d1.cell(r, c); x.font = F(8, tot); x.alignment = R; x.number_format = FMT1[c]
    for c in range(19, 24):
        x = d1.cell(r, c); x.font = F(8, tot); x.alignment = R
        x.number_format = '+#,##0" €";-#,##0" €";"—"'
    d1.row_dimensions[r].height = 14.25
# CORRECTION 4 : une valeur unitaire ne se somme pas -- les cinq colonnes
# unitaires portent le meme tiret, pas seulement la premiere.
for c in range(6, 11): d1.cell(43, c).value = "—"; d1.cell(43, c).alignment = Cn
# Les lignes non servies ne prennent ni fond ni filet : elles se confondent
# avec la page au lieu de se lire comme un tableau vide.
for plage in ("B44:P73", "S44:W73"):
    d1.conditional_formatting.add(plage, Rule(type="expression", formula=['$B44<>""'],
        dxf=DifferentialStyle(fill=PatternFill(bgColor=PANEL),
                              border=Border(bottom=Side(style="thin", color=FILET)))))
for c1 in range(19, 24):
    for op, coul in (("greaterThan", VERT_T), ("lessThan", ROUGE_T)):
        d1.conditional_formatting.add("%s44:%s73" % (GL(c1), GL(c1)),
            CellIsRule(operator=op, formula=["0"], font=Font(name=UI, size=8, color=coul)))

# ============================================================================
#  DRILL EBITDA 2 — de quoi cet EBITDA est fait
# ============================================================================
d2 = wb["Drill EBITDA 2"]
page(d2, 9, 62)
bandeau(d2, 9, "DE QUOI CET EBITDA EST-IL FAIT",
        "drill sur la cellule cliquée · quinze comptes lus en compta, plus le siège redescendu")
d2.column_dimensions["A"].width = 2.4
for L_, w_ in (("B", 9), ("C", 15), ("D", 34), ("E", 14), ("F", 14), ("G", 15),
               ("H", 15), ("I", 11)):
    d2.column_dimensions[L_].width = w_
for c in range(10, 26): d2.column_dimensions[GL(c)].hidden = True

# CORRECTION 1 : quatre plages fausses dans la phrase de synthese.
d2["B5"] = ('="Sur "&TEXT(SUM(F34:F36),"#,##0 €")&" de chiffre d\'affaires, "'
            '&TEXT(-SUM(F37:F49),"#,##0 €")&" partent en charges. Il reste "'
            '&TEXT(SUM(F34:F49),"#,##0 €")&" d\'EBITDA, soit "'
            '&TEXT(SUM(F34:F49)/SUM(F34:F36),"0.0%")&" du chiffre d\'affaires."')
d2.cell(5, 2).font = F(12.5, True, INK); d2.cell(5, 2).alignment = ind(0)
d2.row_dimensions[5].height = 20
d2.cell(6, 2, "les montants sont signés : une variation positive veut toujours dire "
              "« cette ligne apporte plus à l'EBITDA »")
d2.cell(6, 2).font = F(8, False, DOUX, True); d2.cell(6, 2).alignment = ind(0)

titre_bloc(d2, 32, 2, "LE COMPTE D'EXPLOITATION, POSTE PAR POSTE",
           "colonnes C à F lues dans la restitution par RECHERCHEV", 9)
for j, lab in enumerate(("Compte", "Famille", "Poste", "Montant 2025", "Montant 2026",
                         "Variation", "Part des charges", "Nature")):
    d2.cell(33, 2 + j, lab)
entete(d2, 33, 2, 9)
for c in (2, 3, 4): d2.cell(33, c).alignment = ind(0)
for r in range(34, 50):
    prod = r <= 36; siege = r == 49
    for c in range(2, 10):
        x = d2.cell(r, c); x.fill = fill(GRIS if prod else PANEL)
        x.border = Border(bottom=sd(INK, "medium") if r == 36 else sd(FILET))
    d2.cell(r, 2).font = F(8, prod, DOUX); d2.cell(r, 2).alignment = Cn
    d2.cell(r, 3).font = F(8, prod, DOUX); d2.cell(r, 3).alignment = ind(0)
    d2.cell(r, 4).font = F(8, prod);       d2.cell(r, 4).alignment = ind(0)
    for c in (5, 6):
        x = d2.cell(r, c); x.font = F(8, prod); x.alignment = R; x.number_format = '#,##0" €"'
    x = d2.cell(r, 7); x.font = F(8, True); x.alignment = R
    x.number_format = '"▲ "#,##0;"▼ "#,##0;"—"'
    x = d2.cell(r, 8); x.font = F(8); x.alignment = R; x.number_format = '0.0%'
    # LA COLONNE NATURE, demandee : elle traduit la famille, elle ne l'invente pas.
    d2.cell(r, 9, '=IF($C{0}="","",IF($C{0}="Produits","produit",'
                  'IF($C{0}="Siège","allocation","charge")))'.format(r))
    x = d2.cell(r, 9); x.font = F(7.5, False, DOUX); x.alignment = Cn
    d2.row_dimensions[r].height = 14.25
d2.conditional_formatting = ConditionalFormattingList()
# L'ECHELLE SUR LA VARIATION. Une seule suffit pour les seize lignes : les
# montants etant signes, positif veut toujours dire "apporte plus a l'EBITDA".
d2.conditional_formatting.add("G37:G49", ColorScaleRule(
    start_type="min", start_color="FF" + HM_BAS,
    mid_type="num", mid_value=0, mid_color="FF" + HM_MED,
    end_type="max", end_color="FF" + HM_HAUT))
# Le signe DOUBLE l'echelle : la fleche du format donne le sens, la couleur de
# police donne le jugement. Deux encodages pour deux lectures, pas un seul.
for op, coul in (("greaterThan", VERT_T), ("lessThan", ROUGE_T)):
    d2.conditional_formatting.add("G34:G49", CellIsRule(operator=op, formula=["0"],
        font=Font(name=UI, size=8, bold=True, color=coul)))
d2.conditional_formatting.add("H34:H49", DataBarRule(start_type="num", start_value=0,
    end_type="max", color="FF" + PALE, showValue=True))
d2.conditional_formatting.add("I34:I49", Rule(type="expression", formula=['$I34="produit"'],
    dxf=DifferentialStyle(font=Font(color=VERT_T))))
d2.conditional_formatting.add("I34:I49", Rule(type="expression", formula=['$I34="allocation"'],
    dxf=DifferentialStyle(font=Font(color=AZUR))))

for c in range(2, 10):
    x = d2.cell(51, c); x.fill = fill(PANEL)
    x.border = Border(top=sd(AZUR, "medium"), bottom=sd(AZUR, "medium"))
d2.cell(51, 2).font = F(8, True, DOUX); d2.cell(51, 2).alignment = ind(0)
d2.cell(51, 4).font = F(8, True, DOUX); d2.cell(51, 4).alignment = ind(0)
for c in (5, 6):
    x = d2.cell(51, c); x.font = F(10.5, True, AZUR); x.alignment = R; x.number_format = '#,##0" €"'
titre_bloc(d2, 53, 2, "RAPPROCHEMENT DU CHIFFRE D'AFFAIRES  ·  comptes de produit contre socle CRM")
for r in (54, 55, 56):
    for c in range(2, 10):
        x = d2.cell(r, c); x.fill = fill(GRIS if r == 56 else PANEL)
        x.border = Border(bottom=sd(INK, "medium") if r == 56 else sd(FILET))
    d2.cell(r, 2).font = F(8, r == 56); d2.cell(r, 2).alignment = ind(0)
    for c in (5, 6):
        x = d2.cell(r, c); x.font = F(8.5 if r == 56 else 8, r == 56, AZUR if r == 56 else INK)
        x.alignment = R
        x.number_format = '+#,##0" €";-#,##0" €";"0 €"' if r == 56 else '#,##0" €"'
    d2.row_dimensions[r].height = 14.25
for c in (7, 8):
    x = d2.cell(56, c); x.font = F(7.5, False, DOUX); x.alignment = R
    x.number_format = '+0.00%;-0.00%;"0,00 %"'

# ============================================================================
#  LES GRAPHES
#  openpyxl ne sait pas relire les graphes natifs Tagetik (attribut seriesType)
#  et les perdrait a l'enregistrement. On les reconstruit donc a l'identique,
#  en references INTERNES et sans aucun nom defini -- c'est ce qui faisait
#  disparaitre les series des qu'un fichier changeait de nom.
# ============================================================================
def fini(ch, h=8.6, w=8.3):
    ch.height = h; ch.width = w; ch.visible_cells_only = False
    ch.x_axis.delete = False; ch.y_axis.delete = False
    ch.x_axis.majorTickMark = "none"; ch.y_axis.majorTickMark = "none"
    ch.x_axis.majorGridlines = None
    return ch
def cats(ch, feuille, col, r1, r2):
    p = "'%s'!$%s$%d:$%s$%d" % (feuille, GL(col), r1, GL(col), r2)
    for s in ch.series: s.cat = AxDataSource(strRef=StrRef(f=p))
def noms(ch, libs):
    for s, n in zip(ch.series, libs): s.tx = SeriesLabel(v=n)

ws._charts = []; d1._charts = []; d2._charts = []
PONT, MARGE, TENS = 30, 37, 54          # AD, AK, BB dans la navigation reelle

titre_bloc(ws, 12, 3,  "01 · LES MOTEURS DE LA VARIATION",  "pont d'EBITDA 2025 → 2026  ", 7)
titre_bloc(ws, 12, 9,  "02 · PERFORMANCE PAR ENTITÉ",       "marge EBITDA, trois exercices  ", 12)
titre_bloc(ws, 12, 14, "03 · ACQUISITION & INSCRIPTIONS",   "base 2024 = 100  ", 17)
for r in range(13, 34): ws.row_dimensions[r].height = 14

br = BarChart(); br.type = "col"; br.grouping = "stacked"; br.overlap = 100; br.gapWidth = 60
for j in range(1, 5):
    br.add_data(Reference(ws, min_col=PONT + j, max_col=PONT + j, min_row=7, max_row=11),
                titles_from_data=False)
for s, coul in zip(br.series, (None, INK, VERT, ROUGE)):
    if coul is None: s.graphicalProperties.noFill = True
    else: s.graphicalProperties.solidFill = coul; s.graphicalProperties.line.noFill = True
cats(br, "Cockpit", PONT, 7, 11); br.legend = None; br.y_axis.numFmt = '0.0,," M€"'
fini(br); ws.add_chart(br, "C13")

mg = BarChart(); mg.type = "bar"; mg.grouping = "clustered"; mg.gapWidth = 60; mg.overlap = -10
for j in range(1, 4):
    mg.add_data(Reference(ws, min_col=MARGE + j, max_col=MARGE + j, min_row=7, max_row=11),
                titles_from_data=False)
for s, coul in zip(mg.series, (PALE, "4FA3D9", AZUR)):
    s.graphicalProperties.solidFill = coul; s.graphicalProperties.line.noFill = True
cats(mg, "Cockpit", MARGE, 7, 11); noms(mg, ("2024", "2025", "2026"))
mg.legend.position = "b"; mg.x_axis.numFmt = '0%'
fini(mg, 8.6, 8.6); ws.add_chart(mg, "I13")

tn = LineChart()
for j in range(1, 3):
    tn.add_data(Reference(ws, min_col=TENS + j, max_col=TENS + j, min_row=7, max_row=9),
                titles_from_data=False)
for s, coul in zip(tn.series, (ROUGE, AZUR)):
    s.graphicalProperties.line.solidFill = coul; s.graphicalProperties.line.width = 22000
    s.marker = Marker(symbol="circle", size=6); s.smooth = False
    s.marker.graphicalProperties.solidFill = coul
    s.marker.graphicalProperties.line.solidFill = coul
cats(tn, "Cockpit", TENS, 7, 9); noms(tn, ("Dépenses", "Inscrits"))
tn.legend.position = "b"; tn.y_axis.numFmt = '0'
tn.y_axis.scaling.min = 95; tn.y_axis.scaling.max = 125; tn.y_axis.majorUnit = 10
fini(tn, 8.6, 8.6); ws.add_chart(tn, "N13")

# ---- drill 1 : la cascade -------------------------------------------------
titre_bloc(d1, 23, 2, "LA CASCADE", "socle invisible, ancres, hausses et baisses  ", 8)
ca = BarChart(); ca.type = "col"; ca.grouping = "stacked"; ca.overlap = 100; ca.gapWidth = 55
for j in range(1, 5):
    ca.add_data(Reference(d1, min_col=25 + j, max_col=25 + j, min_row=30, max_row=36),
                titles_from_data=False)
for s, coul in zip(ca.series, (None, INK, VERT, ROUGE)):
    if coul is None: s.graphicalProperties.noFill = True
    else: s.graphicalProperties.solidFill = coul; s.graphicalProperties.line.noFill = True
cats(ca, "Drill EBITDA 1", 25, 30, 36); ca.legend = None; ca.y_axis.numFmt = '0.0,," M€"'
fini(ca, 10.5, 22.0); d1.add_chart(ca, "B24")

# ---- drill 2 : les treize postes de charge --------------------------------
titre_bloc(d2, 8, 2, "OÙ PART L'ARGENT", "treize postes de charge · 2025 contre 2026  ", 9)
bc = BarChart(); bc.type = "bar"; bc.grouping = "clustered"; bc.gapWidth = 45; bc.overlap = -15
for c in (11, 12):
    bc.add_data(Reference(d2, min_col=c, max_col=c, min_row=37, max_row=49), titles_from_data=False)
for s, coul, nom in zip(bc.series, (PALE, AZUR), ("2025", "2026")):
    s.graphicalProperties.solidFill = coul; s.graphicalProperties.line.noFill = True
    s.tx = SeriesLabel(v=nom)
for s in bc.series:
    s.cat = AxDataSource(strRef=StrRef(f="'Drill EBITDA 2'!$J$37:$J$49"))
bc.legend.position = "b"; bc.y_axis.numFmt = '#,##0," k€"'
fini(bc, 11.5, 20.0); d2.add_chart(bc, "B9")
for r in range(9, 31): d2.row_dimensions[r].height = 14

wb.save(OUT)

# ---- CORRECTION 5 : les IFERROR prefixes _xlfn. ---------------------------
import zipfile, re
tmp = OUT + ".tmp"
zin = zipfile.ZipFile(OUT); zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
n = 0
for it in zin.infolist():
    d = zin.read(it.filename)
    if it.filename.startswith("xl/worksheets/sheet"):
        t = d.decode("utf-8"); n += len(re.findall(r"_xlfn\.IFERROR", t))
        d = t.replace("_xlfn.IFERROR", "IFERROR").encode("utf-8")
    zout.writestr(it, d)
zout.close(); zin.close()
import os; os.replace(tmp, OUT)

print("%s ecrit" % OUT)
print("  prefixes _xlfn.IFERROR retires : %d" % n)
print("  Cockpit         bandeau 1-4 · filtres 5 · cartes 7-10 · graphes 12-33 · tableau 37-57")
print("  Drill EBITDA 1  pont 10-21 · cascade 23 · detail 41-73")
print("  Drill EBITDA 2  reponse 5 · graphe 8 · compte d'exploitation 32-49 · rapprochement 53-56")
