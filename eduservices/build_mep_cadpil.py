#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_mep_cadpil.py — le modele de mise en page de CAD_PIL (Cadrage + Pilotage).

CE QUE C'EST. Un jumeau visuel des deux onglets, a geometrie constante : memes
lignes, memes colonnes, memes emplacements. Les chiffres sont figes (ce sont les
valeurs en cache du fichier reel) : ce classeur n'est pas un moteur, c'est une
maquette de mise en forme dont on colle les formats.

CE QU'IL CORRIGE AU PASSAGE, ET C'EST DELIBERE :
  - le bloc campus est presente ALIGNE (colonne A = colonne L). C'est l'etat
    cible apres le geste 1. Chaque ligne porte enfin ses propres chiffres.
  - les colonnes C a F retrouvent une largeur ou un montant tient. En 8,43 de
    large, 26 814 169 EUR s'affiche #####.
  - la colonne L de Pilotage est demasquee : elle porte le CAC marginal dans le
    bloc 2, qui etait invisible.

REGLES TAGETIK RESPECTEES : zero cellule fusionnee (une grille Tagetik ne le
supporte pas), Arial uniquement, aucun format de nombre vide.
"""
import warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as GL
warnings.filterwarnings("ignore")

OUT = "/home/user/demo5/eduservices/CAD_PIL_MEP.xlsx"

# ---------------------------------------------------------------- la charte --
INK, AZUR, AZUR2 = "14293A", "007AC3", "5AA9DA"
PALE, CIEL, TETE = "BFDCEF", "E8F1F9", "E7EBEF"
VERT, VERTF = "2E7D4F", "E8F3EC"
ROUGE, ROUGEF = "B3261E", "FBEBEA"
AMBRE, AMBREF = "B26B00", "FFF6E5"
FOND, PANEL, ZEBRA = "F4F6F8", "FFFFFF", "F8FAFC"
LIGNE, NOTE = "DCE2E8", "6B7075"
UI = "Arial"

def F(sz=8.5, b=False, c=INK, i=False):
    return Font(name=UI, size=sz, bold=b, color=c, italic=i)
def fill(c):
    return PatternFill("solid", fgColor=c)
def sd(c=LIGNE, st="thin"):
    return Side(style=st, color=c)

G = Alignment("left", vertical="center")
D = Alignment("right", vertical="center")
C_ = Alignment("center", vertical="center")
def ind(n):
    return Alignment("left", vertical="center", indent=n)

EUR   = '#,##0" €"'
EURS  = '+#,##0" €";-#,##0" €";"—"'
EUR2  = '#,##0" €"'
PCT   = '0.0%'
PCTS  = '+0.0%;-0.0%;"—"'
TAUX  = '+0.00%;-0.00%;"—"'
COEF  = '0.00'
NB    = '#,##0'
NBD   = '#,##0.0'
NBS   = '+#,##0;-#,##0;"—"'
FLECHE= '"▲ "0.0%;"▼ "0.0%;"–"'

def peindre(ws, r1, c1, r2, c2, couleur):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(r, c).fill = fill(couleur)

def mettre(ws, r, c, v, font=None, al=None, fmt=None, fl=None, bd=None):
    x = ws.cell(r, c, v)
    x.font = font or F()
    x.alignment = al or G
    x.number_format = fmt or "General"
    if fl: x.fill = fill(fl)
    if bd: x.border = bd
    return x

def bandeau(ws, ncol, eyebrow, titre, sous_titre, droite, cdroite):
    """Deux lignes d'encre, un filet azur qui s'eclaircit vers la droite."""
    peindre(ws, 1, 1, 2, ncol, INK)
    mettre(ws, 1, 2, eyebrow, F(7, True, PALE), ind(0))
    mettre(ws, 1, cdroite, droite, F(7, False, "7E93A6"), D)
    mettre(ws, 2, 2, titre, F(16, True, "FFFFFF"), ind(0))
    mettre(ws, 2, 3, sous_titre, F(9.5, False, PALE), ind(0))
    coupe = max(3, ncol // 3)
    peindre(ws, 3, 1, 3, coupe, AZUR)
    peindre(ws, 3, coupe + 1, 3, ncol, AZUR2)
    ws.row_dimensions[1].height = 15.0
    ws.row_dimensions[2].height = 46.5
    ws.row_dimensions[3].height = 5.25

def section(ws, r, c1, c2, num, titre, note=""):
    """Un marqueur azur, un titre encre, un filet fin dessous."""
    peindre(ws, r, c1, r, c2, FOND)
    mettre(ws, r, c1, num, F(10.5, True, AZUR), ind(0))
    mettre(ws, r, c1 + 0, num + "   " + titre, F(10.5, True, INK), ind(0))
    if note:
        mettre(ws, r, c2, note, F(7.5, False, NOTE, True), D)
    for c in range(c1, c2 + 1):
        ws.cell(r, c).border = Border(bottom=sd(AZUR, "medium"))

def entete(ws, r, c1, c2, libelles, alignements):
    peindre(ws, r, c1, r, c2, INK)
    for i, lib in enumerate(libelles):
        x = mettre(ws, r, c1 + i, lib, F(7.5, True, "FFFFFF"),
                   {"g": ind(0), "d": D, "c": C_}[alignements[i]])
        x.border = Border(bottom=sd(AZUR, "medium"))

def carte(ws, r1, r2, c1, c2, accent):
    """Un panneau blanc, un liseré de couleur en haut, un filet clair autour."""
    peindre(ws, r1, c1, r2, c2, PANEL)
    for c in range(c1, c2 + 1):
        ws.cell(r1, c).border = Border(top=sd(accent, "medium"),
                                       left=sd(LIGNE) if c == c1 else None,
                                       right=sd(LIGNE) if c == c2 else None)
        ws.cell(r2, c).border = Border(bottom=sd(LIGNE),
                                       left=sd(LIGNE) if c == c1 else None,
                                       right=sd(LIGNE) if c == c2 else None)
        for r in range(r1 + 1, r2):
            ws.cell(r, c).border = Border(left=sd(LIGNE) if c == c1 else None,
                                          right=sd(LIGNE) if c == c2 else None)

def saisie(ws, r, c):
    """La marque visuelle d'une cellule qu'on tape en seance."""
    x = ws.cell(r, c)
    x.fill = fill(AMBREF)
    x.border = Border(left=sd(AMBRE), right=sd(AMBRE), top=sd(AMBRE), bottom=sd(AMBRE))
    return x

wb = openpyxl.Workbook()

# ============================================================================
#  ONGLET 1 — CADRAGE
#
#  LA CARTE DES LIGNES EST CELLE DU FICHIER REEL, AU NUMERO PRES :
#    1-3 bandeau · 5 scenario · 7-9 cartes KPI · 10 section (1) · 11 entete
#    12-15 reconciliation · 18 section (2) · 19 entete · 21 sous-titre CROISSANCE
#    22 ligne technique du MATCH · 23-28 leviers de croissance · 32 sous-titre COUTS
#    34-38 leviers de couts · 40 sous-titre CONSTANTE · 42 frais de dossier
#  Le panneau des coefficients de prix occupe J21:K28.
# ============================================================================
ws = wb.active
ws.title = "Cadrage"
ws.sheet_view.showGridLines = False
ws.sheet_properties.tabColor = AZUR
NCOL = 19
peindre(ws, 1, 1, 48, NCOL, FOND)

for c, w in ((1, 2.4), (2, 46.0), (3, 15.4), (4, 15.4), (5, 15.4), (6, 15.4),
             (7, 2.4), (8, 2.0), (9, 2.0), (10, 26.0), (11, 10.5), (12, 2.0), (13, 13.0)):
    ws.column_dimensions[GL(c)].width = w
H = {1: 14.25, 2: 46.5, 3: 11.25, 4: 20.25, 5: 24.0, 6: 26.25, 7: 24.0, 8: 28.5, 9: 24.0,
     10: 33.75, 11: 24.75, 12: 24.75, 13: 24.75, 14: 24.75, 15: 24.75, 16: 16.5, 17: 3.75,
     18: 30.0, 19: 20.25, 20: 5.25, 21: 21.0, 22: 9.0, 23: 22.5, 24: 22.5, 25: 22.5,
     26: 22.5, 27: 22.5, 28: 22.5, 29: 6.0, 30: 6.0, 31: 6.0, 32: 18.0, 33: 6.0,
     34: 21.75, 35: 21.75, 36: 21.75, 37: 21.75, 38: 21.75, 39: 6.0, 40: 18.0, 41: 6.0,
     42: 21.75, 43: 9.0, 44: 16.5, 45: 6.0, 46: 14.25}
for r, h in H.items():
    ws.row_dimensions[r].height = h

bandeau(ws, NCOL, "EDUSERVICES GROUP   ·   14 CAMPUS   ·   5 MARQUES",
        "CADRAGE", "Hypothèses & scénarios · Budget 2027",
        "TGK_MSSQL_07 · 2027BUD_V1", 11)

# --- ligne 5 : les deux seules cellules de saisie --------------------------
mettre(ws, 5, 2, "SCÉNARIO ACTIF", F(7.5, True, AZUR), ind(0))
mettre(ws, 5, 3, "Optimiste", F(10.5, True, INK), C_)
saisie(ws, 5, 3)
mettre(ws, 5, 5, "OBJECTIF D'EBITDA", F(7.5, True, AZUR), D)
mettre(ws, 5, 6, 0.065, F(10.5, True, INK), C_, PCT)
saisie(ws, 5, 6)
dv = DataValidation(type="list", formula1='"Cadrage,Optimiste,Prudent"', allow_blank=False)
ws.add_data_validation(dv); dv.add(ws["C5"])
mettre(ws, 6, 2, "les deux cellules ambre sont les seules à saisir : tout le reste se recalcule",
       F(7.5, False, NOTE, True), ind(0))

# --- lignes 7 a 9 : les trois cartes KPI -----------------------------------
KPI = [(2, 2, "OBJECTIF 2027", 4095766.36, EUR,
        "+6,50 % sur 3 845 790 € en 2026, soit +249 976 € à trouver", AZUR, INK),
       (3, 4, "CE QUE LES LEVIERS PRODUISENT", 6744302.91, EUR,
        "scénario « Optimiste »   ·   marge 25,2 %", VERT, INK),
       (5, 6, "RESTE À TROUVER", -2648536.55, EURS,
        "objectif moins construit  ·  se ferme à chaque levier", VERT, VERT)]
for c1, c2, lib, val, fmt, note, accent, coul in KPI:
    carte(ws, 7, 9, c1, c2, accent)
    mettre(ws, 7, c1, lib, F(7.5, True, accent), ind(1))
    mettre(ws, 8, c1, val, F(20, True, coul), ind(1), fmt)
    mettre(ws, 9, c1, note, F(7.5, False, NOTE, True), ind(1))

# --- lignes 10 a 15 : reconciliation ---------------------------------------
section(ws, 10, 2, 6, "①", "RÉCONCILIATION", "de 2026 au scénario construit")
entete(ws, 11, 2, 6, ["Indicateur", "Référence 2026", "Construit 2027", "Écart", "Écart %"],
       ["g", "d", "d", "d", "d"])
REC = [("Chiffre d'affaires", 23098985, 26814168.68, 3715183.68, 0.1608, EUR, EURS),
       ("EBITDA", 3845790.01, 6744302.91, 2898512.90, 0.7537, EUR, EURS),
       ("Marge EBITDA", 0.1665, 0.2515, 0.0850, None, PCT, PCTS),
       ("Effectif", 3114, 3473.67, 359.67, 0.1155, NB, NBS)]
for i, (lib, a, b, e, pc, f1, f2) in enumerate(REC):
    r = 12 + i
    peindre(ws, r, 2, r, 6, PANEL if i % 2 == 0 else ZEBRA)
    for c in range(2, 7):
        ws.cell(r, c).border = Border(bottom=sd("EDEFF2"))
    mettre(ws, r, 2, lib, F(8.5, i == 1, INK), ind(1))
    mettre(ws, r, 3, a, F(8.5), D, f1)
    mettre(ws, r, 4, b, F(8.5, True, INK), D, f1)
    mettre(ws, r, 5, e, F(8.5, False, VERT), D, f2)
    if pc is not None:
        mettre(ws, r, 6, pc, F(8.5, False, VERT), D, FLECHE)
for c in range(2, 7):                                   # l'EBITDA est la ligne qui compte
    ws.cell(13, c).fill = fill(CIEL)
    ws.cell(13, c).border = Border(top=sd(AZUR), bottom=sd(AZUR))

# --- lignes 18 a 42 : les douze leviers ------------------------------------
section(ws, 18, 2, 6, "②", "LES DOUZE LEVIERS",
        "six de croissance · cinq de coûts · une constante")
entete(ws, 19, 2, 6, ["Levier", "Cadrage", "Optimiste", "Prudent", "RETENU"],
       ["g", "c", "c", "c", "c"])
for c, col in ((3, "8A949E"), (4, VERT), (5, AMBRE)):
    ws.cell(19, c).border = Border(bottom=Side(style="medium", color=col))
ws.cell(19, 6).fill = fill(AZUR)
ws.cell(19, 6).border = Border(bottom=Side(style="medium", color="FFFFFF"))

def sous_titre(r, titre):
    peindre(ws, r, 2, r, 6, FOND)
    mettre(ws, r, 2, titre, F(8, True, AZUR), ind(0))
    for c in range(2, 7):
        ws.cell(r, c).border = Border(bottom=sd(PALE))

def leviers(r0, lignes, fmt):
    for i, (lib, cadr, opti, prud, ret) in enumerate(lignes):
        r = r0 + i
        peindre(ws, r, 2, r, 6, PANEL if i % 2 == 0 else ZEBRA)
        for c in range(2, 7):
            ws.cell(r, c).border = Border(bottom=sd("EDEFF2"))
        mettre(ws, r, 2, lib, F(8.5), ind(1))
        for j, v in enumerate((cadr, opti, prud)):
            if v is None:
                x = mettre(ws, r, 3 + j, "—", F(8.5, True, ROUGE), C_)
                x.fill = fill(ROUGEF)
            else:
                mettre(ws, r, 3 + j, v, F(8.5, False, NOTE), C_, fmt)
        x = mettre(ws, r, 6, ret, F(9, True, INK), C_, fmt)
        x.fill = fill(CIEL)
        x.border = Border(left=sd(AZUR), right=sd(AZUR), bottom=sd("C9DFEF"))

sous_titre(21, "CROISSANCE   ·   ce qui fait le chiffre d'affaires")
#  ligne 22 : elle porte les trois libelles que cherche le MATCH de la colonne
#  RETENU. On la garde, on la rend invisible : 9 pixels, texte couleur du fond.
for j, lib in enumerate(("Cadrage", "Optimiste", "Prudent")):
    mettre(ws, 22, 3 + j, lib, F(6, False, FOND), C_)
leviers(23, [("Variation du budget d'acquisition  →  leads payants", .08, .15, -.05, .15),
             ("Variation du budget de marque  →  socle organique", .10, .15, -.05, .15),
             ("Hausse tarifaire (prix)", .0029, .035, .02, .035),
             ("Gain du taux de conversion  Lead → Candidature", .01, .03, -.01, .03),
             ("Gain du taux de conversion  Admis → Inscrit", .01, .025, -.01, .025),
             ("Amélioration du taux de passage", .005, .015, -.01, .015)], TAUX)

sous_titre(32, "COÛTS   ·   ce qui fait la marge")
leviers(34, [("Inflation des charges externes", .02, .015, .03, .015),
             ("Politique salariale sur la masse permanente", .025, .02, .03, .02),
             ("Variation des effectifs permanents", .04, .03, .05, .03),
             ("Effort de productivité sur les achats et la structure", .0185, .03, None, .03),
             ("Variation des coûts de structure (loyers, IT, siège…)", None, -.03, .04, -.03)], TAUX)

sous_titre(40, "CONSTANTE   ·   hors scénario, saisie directe")
leviers(42, [("Frais de dossier par nouvel inscrit", 90, 90, 90, 90)], EUR)

mettre(ws, 44, 2,
       "⚠   deux cases sont vides dans la grille des scénarios : « Prudent » sur l'effort de "
       "productivité, « Cadrage » sur les coûts de structure. Sur ces scénarios, le levier "
       "tombe à zéro sans le dire.", F(7.5, False, ROUGE, True), ind(0))
mettre(ws, 46, 2,
       "Source : AW_002_000001_000001 (cube d'hypothèses)  ·  scénario 2027BUD_V1  ·  "
       "les versions V01 / V02 / V03 sont les colonnes Cadrage / Optimiste / Prudent.",
       F(7, False, NOTE, True), ind(0))

# --- J21:K28 : le panneau des coefficients de prix -------------------------
peindre(ws, 21, 10, 21, 11, FOND)
mettre(ws, 21, 10, "③   COEFFICIENTS DE PRIX", F(10.5, True, INK), ind(0))
for c in (10, 11):
    ws.cell(21, c).border = Border(bottom=sd(AZUR, "medium"))
entete(ws, 23, 10, 11, ["Marque", "Coeff."], ["g", "c"])
for i, (m, k) in enumerate([("MBway", 1.20), ("ISCOM", 1.15),
                            ("Ipac Bachelor Factory", 0.95), ("Pigier", 0.90),
                            ("Tunon", 1.05)]):
    r = 24 + i
    peindre(ws, r, 10, r, 11, PANEL if i % 2 == 0 else ZEBRA)
    for c in (10, 11):
        ws.cell(r, c).border = Border(bottom=sd("EDEFF2"))
    mettre(ws, r, 10, m, F(8.5), ind(1))
    mettre(ws, r, 11, k, F(9, True, INK), C_, COEF)
mettre(ws, 30, 10, "appliqué au prix moyen de chaque marque, avant hausse tarifaire",
       F(7.5, False, NOTE, True), ind(0))

for zone in ("C23:E28", "C34:E38"):
    ws.conditional_formatting.add(zone, CellIsRule(
        operator="lessThan", formula=["0"], font=Font(name=UI, size=8.5, color=ROUGE)))
ws.conditional_formatting.add("F23:F38", CellIsRule(
    operator="lessThan", formula=["0"], font=Font(name=UI, size=9, bold=True, color=ROUGE)))
ws.freeze_panes = "B10"

# ============================================================================
#  ONGLET 2 — PILOTAGE
# ============================================================================
p = wb.create_sheet("Pilotage")
p.sheet_view.showGridLines = False
p.sheet_properties.tabColor = INK
NC2 = 23
peindre(p, 1, 1, 58, NC2, FOND)
for c, w in ((1, 3.2), (2, 17.5), (3, 14.0), (4, 13.0), (5, 13.5), (6, 12.5),
             (7, 11.5), (8, 13.5), (9, 11.5), (10, 12.5), (11, 13.5), (12, 13.0),
             (13, 2.4), (14, 8.5)):
    p.column_dimensions[GL(c)].width = w
for lettre in ("N", "U", "V", "W"):
    p.column_dimensions[lettre].hidden = True

bandeau(p, NC2, "EDUSERVICES GROUP   ·   COCKPIT DE DÉCISION",
        "PILOTAGE", "Où se gagne le budget 2027, campus par campus",
        "TGK_MSSQL_07 · 2027BUD_V1", 12)
p.row_dimensions[3].height = 11.25

p.row_dimensions[4].height = 12.0
p.row_dimensions[5].height = 6.0
p.row_dimensions[6].height = 26.25
mettre(p, 6, 2, "SCÉNARIO ACTIF", F(7.5, True, AZUR), ind(0))
mettre(p, 6, 5, "Cadrage", F(10.5, True, INK), C_)
saisie(p, 6, 5)
dv2 = DataValidation(type="list", formula1='"Cadrage,Optimiste,Prudent"', allow_blank=False)
p.add_data_validation(dv2); dv2.add(p["E6"])
mettre(p, 6, 6, "← doit suivre Cadrage!C5, sinon les deux onglets racontent deux budgets",
       F(7.5, False, ROUGE, True), ind(1))

# --- la barre de cinq KPI --------------------------------------------------
for r, h in ((7, 8.25), (8, 3.75), (9, 24.0), (10, 33.75), (11, 20.25), (12, 8.25)):
    p.row_dimensions[r].height = h
KPI2 = [(2, 2, "CA 2027", 24231703.55, EUR, "contre 23 098 985 € en 2026", AZUR),
        (3, 4, "EBITDA (après siège)", 4111503.64, EUR, "contre 3 845 790 € en 2026", VERT),
        (5, 6, "MARGE EBITDA", 0.1697, PCT, "contre 16,6 % en 2026", VERT),
        (7, 8, "EFFECTIF", 3253.62, NBD, "contre 3 114 en 2026", AZUR),
        (9, 11, "CROISSANCE CA vs 2026", 0.0490, PCTS, "à scénario Cadrage", AZUR2)]
for c1, c2, lib, val, fmt, note, accent in KPI2:
    carte(p, 9, 11, c1, c2, accent)
    mettre(p, 9, c1, lib, F(7.5, True, accent), ind(1))
    mettre(p, 10, c1, val, F(20, True, INK), ind(1), fmt)
    mettre(p, 11, c1, note, F(7.5, False, NOTE, True), ind(1))

# --- les donnees campus, ALIGNEES (colonne A = colonne L) ------------------
#  entity, marque, ville | CAC, croiss, intensite, capEff, capMom, capPot, capRet, budget
CAP = [("IPAC_MTP", "Ipac", "Montpellier", 1033.98, .1448, .0194, 1.1626, 1.3855, .9443, 1, 15178),
       ("IPAC_NAN", "Ipac", "Nantes", 1216.29, .1379, .0213, .9883, 1.3195, .8591, 1, 21760),
       ("IPAC_REN", "Ipac", "Rennes", 1040.56, .1448, .0191, 1.1553, 1.3855, .9598, 1, 14933),
       ("ISCOM_LIL", "ISCOM", "Lille", 978.58, .0815, .0144, 1.2284, .7804, 1.2767, 1, 25220),
       ("ISCOM_PAR", "ISCOM", "Paris", 1540.33, .0777, .0209, .7804, .7440, .8773, 1, 60800),
       ("ISCOM_TLS", "ISCOM", "Toulouse", 919.03, .0821, .0136, 1.3080, .7858, 1.3518, 1, 22083),
       ("MBWAY_BOR", "MBway", "Bordeaux", 889.59, .1261, .0141, 1.3513, 1.2067, 1.3049, 1, 24923),
       ("MBWAY_LYO", "MBway", "Lyon", 1101.60, .1189, .0167, 1.0912, 1.1376, 1.0957, 1, 41783),
       ("MBWAY_NAN", "MBway", "Nantes", 963.58, .1238, .0146, 1.2476, 1.1847, 1.2551, 1, 31533),
       ("MBWAY_PAR", "MBway", "Paris", 1475.02, .1107, .0218, .8150, 1.0597, .8428, 1, 68291),
       ("PIGIER_BOR", "Pigier", "Bordeaux", 1368.09, .0875, .0194, .8787, .8377, .9454, 1, 21968),
       ("PIGIER_LYO", "Pigier", "Lyon", 1704.98, .0850, .0233, .7051, .8135, .7883, 1, 36612),
       ("TUNON_LYO", "Tunon", "Lyon", 1624.68, .0726, .0218, .7399, .6943, .8401, 1, 18850),
       ("TUNON_PAR", "Tunon", "Paris", 2192.89, .0695, .0278, .5482, .6653, .6586, 1, 30240)]
#  entity | effectif, CA, prix, part, EBITDA, marge, EBITDA/etudiant
SYN = {"MBWAY_PAR": (398.78, 3292150.80, 8255.51, .1359, 1096393.82, .3330, 2749.35),
       "MBWAY_LYO": (338.50, 2620797.34, 7742.43, .1082, 876442.71, .3344, 2589.21),
       "MBWAY_NAN": (307.34, 2267018.63, 7376.18, .0936, 763702.73, .3369, 2484.86),
       "MBWAY_BOR": (260.41, 1863775.69, 7157.03, .0769, 625402.30, .3356, 2401.59),
       "ISCOM_PAR": (369.35, 3048653.48, 8254.05, .1258, 985765.87, .3233, 2668.90),
       "ISCOM_LIL": (255.09, 1844124.54, 7229.40, .0761, 602778.74, .3269, 2363.04),
       "ISCOM_TLS": (241.48, 1709754.85, 7080.28, .0706, 560009.03, .3275, 2319.06),
       "IPAC_NAN": (151.32, 1067200.79, 7052.49, .0440, 331184.51, .3103, 2188.60),
       "IPAC_REN": (122.12, 818371.29, 6701.28, .0338, 254316.41, .3108, 2082.49),
       "IPAC_MTP": (122.13, 818445.73, 6701.29, .0338, 254308.30, .3107, 2082.23),
       "PIGIER_LYO": (236.95, 1653869.91, 6979.90, .0683, 626670.52, .3789, 2644.77),
       "PIGIER_BOR": (184.72, 1191512.54, 6450.49, .0492, 455099.20, .3820, 2463.77),
       "TUNON_PAR": (143.56, 1133628.58, 7896.53, .0468, 220510.28, .1945, 1536.01),
       "TUNON_LYO": (121.86, 902399.37, 7405.22, .0372, 178759.19, .1981, 1466.92)}

for r in (13, 14, 15):
    p.row_dimensions[r].height = 6.0
p.row_dimensions[16].height = 26.25
section(p, 16, 2, 12, "①", "CAP STRATÉGIQUE PAR CAMPUS",
        "marque × ville  ·  la colonne « Cap retenu » est le levier de séance")
p.row_dimensions[17].height = 6.0
p.row_dimensions[18].height = 24.0
entete(p, 18, 1, 12,
       ["", "Marque", "Ville", "CAC marginal", "Croiss. leads", "Intensité mkt",
        "Cap Eff", "Cap mom.", "Cap pot.", "Cap retenu", "Budget acq. réf.", "Entity"],
       ["c", "g", "g", "d", "d", "d", "c", "c", "c", "c", "d", "g"])
p.cell(18, 10).fill = fill(AMBRE)
p.cell(18, 12).font = F(7.5, True, "8FA3B4")

for i, ligne in enumerate(CAP):
    r = 19 + i
    p.row_dimensions[r].height = 18.0
    ent, mq, vl = ligne[0], ligne[1], ligne[2]
    peindre(p, r, 1, r, 12, PANEL if i % 2 == 0 else ZEBRA)
    for c in range(1, 13):
        p.cell(r, c).border = Border(bottom=sd("EDEFF2"))
    mettre(p, r, 1, ent, F(6, False, PANEL if i % 2 == 0 else ZEBRA), C_)   # cle, discrete
    mettre(p, r, 2, mq, F(8.5, True, INK), ind(1))
    mettre(p, r, 3, vl, F(8.5), ind(0))
    mettre(p, r, 4, ligne[3], F(8.5), D, EUR)
    mettre(p, r, 5, ligne[4], F(8.5), D, PCT)
    mettre(p, r, 6, ligne[5], F(8.5), D, PCT)
    for j in (6, 7, 8):
        mettre(p, r, j - 6 + 7, ligne[j], F(8.5), C_, COEF)
    x = mettre(p, r, 10, ligne[9], F(9, True, INK), C_, COEF)
    x.fill = fill(AMBREF)
    x.border = Border(left=sd(AMBRE), right=sd(AMBRE), bottom=sd("F0DFC0"))
    mettre(p, r, 11, ligne[10], F(8.5), D, EUR)
    mettre(p, r, 12, ent, F(7.5, False, "9AA7B2"), ind(0))

p.conditional_formatting.add("D19:D32", ColorScaleRule(
    start_type="min", start_color="D6ECD9", end_type="max", end_color="F5C9C5"))
p.conditional_formatting.add("K19:K32", DataBarRule(
    start_type="num", start_value=0, end_type="max", color=AZUR2, showValue=True))
for zone in ("G19:G32", "H19:H32", "I19:I32"):
    p.conditional_formatting.add(zone, ColorScaleRule(
        start_type="min", start_color="FFFFFF", end_type="max", end_color="BFDCEF"))

# --- (2) la synthese -------------------------------------------------------
for r in (33, 34, 35):
    p.row_dimensions[r].height = 8.25
p.row_dimensions[36].height = 26.25
section(p, 36, 2, 12, "②", "SYNTHÈSE PAR CAMPUS",
        "résultats du budget construit  ·  du chiffre d'affaires à l'EBITDA")
p.row_dimensions[37].height = 6.0
p.row_dimensions[38].height = 24.0
entete(p, 38, 1, 12,
       ["", "Marque", "Ville", "Effectif", "CA 2027", "Prix moyen", "Part CA",
        "EBITDA campus", "Marge", "EBITDA / étud.", "Budget rejoué", "CAC marginal"],
       ["c", "g", "g", "d", "d", "d", "d", "d", "c", "d", "d", "d"])

for i, ligne in enumerate(CAP):
    r = 39 + i
    ent, mq, vl = ligne[0], ligne[1], ligne[2]
    eff, ca, prix, part, ebitda, marge, epe = SYN[ent]
    p.row_dimensions[r].height = 18.0
    peindre(p, r, 1, r, 12, PANEL if i % 2 == 0 else ZEBRA)
    for c in range(1, 13):
        p.cell(r, c).border = Border(bottom=sd("EDEFF2"))
    mettre(p, r, 1, ent, F(6, False, PANEL if i % 2 == 0 else ZEBRA), C_)
    mettre(p, r, 2, mq, F(8.5, True, INK), ind(1))
    mettre(p, r, 3, vl, F(8.5), ind(0))
    mettre(p, r, 4, eff, F(8.5), D, NBD)
    mettre(p, r, 5, ca, F(8.5, True, INK), D, EUR)
    mettre(p, r, 6, prix, F(8.5), D, EUR)
    mettre(p, r, 7, part, F(8.5), D, PCT)
    mettre(p, r, 8, ebitda, F(8.5), D, EUR)
    mettre(p, r, 9, marge, F(8.5), C_, PCT)
    mettre(p, r, 10, epe, F(8.5), D, EUR)
    mettre(p, r, 11, ligne[10], F(8.5, False, NOTE), D, EUR)
    mettre(p, r, 12, ligne[3], F(8.5, False, NOTE), D, EUR)

p.conditional_formatting.add("G39:G52", DataBarRule(
    start_type="num", start_value=0, end_type="max", color=AZUR2, showValue=True))
p.conditional_formatting.add("I39:I52", ColorScaleRule(
    start_type="min", start_color="F5C9C5", mid_type="percentile", mid_value=50,
    mid_color="FFFFFF", end_type="max", end_color="CBE6D2"))
p.conditional_formatting.add("J39:J52", ColorScaleRule(
    start_type="min", start_color="FFFFFF", end_type="max", end_color="BFDCEF"))

# --- les trois lignes de total --------------------------------------------
TOT = [(53, "Sous-total campus", "14 campus", 3253.62, 24231703.55, 7447.62, 1.0,
        7831343.62, .3232, 2406.97, 434174, None, TETE, INK, 20.25),
       (54, "Siège / holding", "GRP", None, None, None, None,
        -3719839.98, None, None, None, None, ROUGEF, ROUGE, 18.0),
       (55, "GROUPE 2027", "consolidé", 3253.62, 24231703.55, 7447.62, 1.0,
        4111503.64, .1697, 1263.67, 434174, None, INK, "FFFFFF", 26.25)]
for (r, lib, sub, eff, ca, prix, part, ebitda, marge, epe, bud, _, bg, fg, h) in TOT:
    p.row_dimensions[r].height = h
    peindre(p, r, 1, r, 12, bg)
    gras = 9.5 if r == 55 else 9
    for c in range(1, 13):
        p.cell(r, c).border = Border(top=sd(AZUR if r != 54 else LIGNE,
                                            "medium" if r == 53 else "thin"))
    mettre(p, r, 2, lib, F(gras, True, fg), ind(1))
    mettre(p, r, 3, sub, F(7.5, False, fg if r == 55 else NOTE, True), ind(0))
    for c, v, fmt in ((4, eff, NBD), (5, ca, EUR), (6, prix, EUR), (7, part, PCT),
                      (8, ebitda, EUR), (9, marge, PCT), (10, epe, EUR), (11, bud, EUR)):
        if v is not None:
            mettre(p, r, c, v, F(gras, True, fg), C_ if c == 9 else D, fmt)

p.row_dimensions[56].height = 8.25
mettre(p, 57, 2,
       "Lecture  ·  la colonne ambre « Cap retenu » est le seul point de saisie : "
       "la porter à 1,15 sur un campus rouvre une classe et réalloue le budget d'acquisition. "
       "Colonne A = clé campus (identique à Entity) : c'est elle qui joint les deux blocs.",
       F(7, False, NOTE, True), ind(0))
p.row_dimensions[57].height = 24.0
p.freeze_panes = "B19"

# ============================================================================
#  NORMALISATION  —  aucune cellule ne doit rester en police par defaut
# ============================================================================
for feuille, nl, nc in ((ws, 48, NCOL), (p, 58, NC2)):
    for r in range(1, nl + 1):
        for c in range(1, nc + 1):
            x = feuille.cell(r, c)
            if x.font is None or x.font.name != UI:
                x.font = F(8.5, False, INK)
            if not x.number_format:
                x.number_format = "General"

# ============================================================================
#  CONTROLES
# ============================================================================
wb.save(OUT)
v = openpyxl.load_workbook(OUT)
pb = []
for s in v.worksheets:
    if s.merged_cells.ranges:
        pb.append("%s : %d fusion(s)" % (s.title, len(s.merged_cells.ranges)))
    for row in s.iter_rows():
        for c in row:
            if c.number_format == "":
                pb.append("%s!%s : format vide" % (s.title, c.coordinate))
            if c.font and c.font.name not in (None, UI):
                pb.append("%s!%s : police %s" % (s.title, c.coordinate, c.font.name))
print("onglets  :", v.sheetnames)
print("fusions  :", sum(len(s.merged_cells.ranges) for s in v.worksheets))
print("controle :", "PASS" if not pb else pb[:6])
