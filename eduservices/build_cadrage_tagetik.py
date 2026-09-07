#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_cadrage_tagetik.py — la feuille Cadrage, remise au standard Tagetik.

ENTREE  CAD_PIL_EBITDA_DRIVEN.xlsx     le classeur Cadrage & Pilotage du 01/09
SORTIE  CAD_PIL_TAGETIK.xlsx           la meme mecanique, une autre lecture

=============================================================================
CE QUI CHANGE, ET POURQUOI

1. L'OBJECTIF SORT DU TABLEAU. La colonne "Objectif" portait UNE valeur sur
   cinq lignes -- un tiret pour le CA, un tiret pour la marge, rien pour
   l'effectif. Une colonne qui ne sert qu'une fois n'est pas une colonne.

   Plus profondement : le tableau reconcilie TROIS choses -- d'ou l'on part,
   ce que les leviers produisent, ce qui manque. L'objectif n'est pas un
   quatrieme indicateur, c'est le chiffre que toute la page sert. Il monte
   donc dans un bandeau de cadrage, en trois blocs qui se lisent de gauche a
   droite : point de depart, objectif, ecart a fermer.

2. LE VERDICT EXISTE. "Objectif atteint, +6 534 EUR" ou "il manque 12 300
   EUR", en une ligne, avec sa couleur. C'est ce qu'un DAF regarde en premier
   et il n'existait nulle part -- il fallait lire F12 et comprendre le signe.

3. L'OBJECTIF S'AFFICHE EN EUROS. On lisait "+6,5 %" et on calculait de tete.
   4 095 766 EUR est un chiffre qu'on retient et qu'on repete en comite.

4. LA SAISIE SE VOIT. Deux cellules sur toute la page : le scenario et
   l'objectif. Elles sont les seules a avoir l'air cliquables -- fond blanc,
   filet azur, police azur. Tout le reste est du calcul.

=============================================================================
CE QU'ON NE POUVAIT PAS DEPLACER, ET QUI A DICTE LE PLAN

Quarante-sept noms definis pointent dans cette feuille, et d'autres feuilles
la lisent des milliers de fois. Toutes ces adresses sont GELEES :

    C4   SCENARIO_ACTIF     lu 12 fois          P1   SCENARIO_CODE
    F4   TEC_PL             l'objectif saisi    F5   TEC_EBITDA
    C11  la reference de CA                     D12  l'objectif d'EBITDA
    C22:E27 C31:E35 C39     les onze leviers, HYP_* -- pres de 15 000 renvois
    K11:K15                 les coefficients de prix par marque

D12 EST DONC RESTE OU IL EST. Trois formules d'autres feuilles le lisent : le
vider aurait casse le classeur. Il garde sa formule, il devient une ANCRE
TECHNIQUE, et son format de nombre ";;;" le rend invisible. Le bandeau lit
cette meme cellule -- un seul endroit ou l'objectif se calcule, deux endroits
ou il se lit.

=============================================================================
F5 / TEC_EBITDA : UN POINT A TRANCHER, PAS UN BUG A CORRIGER

La cellule F5 portait 15,0 % sous le libelle "(marge : constat -- plus une
saisie)". AUCUNE formule du classeur ne la lit : c'est un vestige de la
version ou le DAF saisissait une marge cible.

Elle contredisait meme le tableau -- 15,0 % affiche a cote d'une marge 2026
constatee a 16,65 %.

MAIS ELLE PORTE LE NOM TAGETIK TEC_EBITDA. On ne supprime donc ni la cellule
ni le nom : la definition du rapport peut s'y lier. On vide sa valeur, on la
rend invisible, et on laisse a Saad le soin de verifier la liaison cote
Tagetik avant de retirer le nom.

A noter au passage : les deux noms sont INVERSES par rapport a leur contenu --
TEC_PL designe l'objectif d'EBITDA et TEC_EBITDA une marge. A corriger cote
Tagetik, pas ici.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import CellIsRule, Rule
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.utils import get_column_letter as GL

SRC, OUT = "CAD_PIL_EBITDA_DRIVEN.xlsx", "CAD_PIL_TAGETIK.xlsx"

INK, AZUR, ROUGE, VERT = "262626", "007AC3", "E5202E", "85BC20"
PALE, GRIS = "A6D0EA", "E7E6E6"
VERT_T, ROUGE_T = "5F8A17", "C41822"
FOND, PANEL, FILET, DOUX = "F5F6F7", "FFFFFF", "D5D7DA", "6B7075"
UI = "Arial"
def F(sz=8, b=False, c=INK, i=False): return Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd   = lambda c=FILET, st="thin": Side(style=st, color=c)
R  = Alignment("right", vertical="center")
Cn = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)

wb = openpyxl.load_workbook(SRC)
ws = wb["Cadrage"]
NC = 12                                   # A..L, la largeur utile de la feuille

ws.sheet_view.showGridLines = False
for r in range(1, 70):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(FOND)

# ---- le bandeau de tete ---------------------------------------------------
ws.cell(1, 15).value = None                       # "code scénario ->", technique
for r in (1, 2):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(INK)
for c in range(1, NC + 1): ws.cell(3, c).fill = fill(AZUR)
t = ws.cell(2, 2, "CADRAGE 2027  —  LE POSTE DE COMMANDE")
t.font = F(14, True, "FFFFFF"); t.alignment = ind(0)
ws.cell(1, 2, "EDUSERVICES · piloté par l'EBITDA").font = F(8, False, PALE)
ws.cell(1, 2).alignment = ind(0)
for r, h in ((1, 16), (2, 24), (3, 3)): ws.row_dimensions[r].height = h

# ---- LA ZONE TECHNIQUE, hors du champ de lecture -------------------------
# L'objectif d'EBITDA en euros vivait en D12, AU MILIEU DU TABLEAU, avec un
# format ";;;" pour le taire. Une cellule muette au milieu d'une grille reste
# une cellule au milieu d'une grille : elle occupe une colonne, elle interdit
# de s'en servir, et elle finit par ressortir le jour ou quelqu'un change un
# format. Elle part donc en O4, derriere le rideau.
#
# UNE SEULE formule du classeur la lisait -- Pilotage!B12, trois fois dans la
# meme chaine. Elle est repointee plus bas. C'etait le seul cout du
# deplacement, et il valait la peine : la colonne D redevient une VRAIE
# colonne du tableau.
for c in range(13, 19): ws.column_dimensions[GL(c)].hidden = True
ws.cell(3, 14, "ZONE TECHNIQUE — ne rien afficher a partir d'ici").font = F(7, False, DOUX, True)
ws.cell(4, 14, "Objectif EBITDA 2027 (€)").font = F(7.5, False, DOUX)
o = ws.cell(4, 15, "=C12*(1+$F$4)"); o.number_format = '#,##0" €"'; o.font = F(9, True, AZUR)

# ---- ligne 4 : LA COMMANDE. Les deux seules cellules saisissables. --------
for c in range(2, NC + 1):
    x = ws.cell(4, c); x.fill = fill(FOND); x.border = Border(bottom=sd(FILET))
ws.row_dimensions[4].height = 22
a = ws.cell(4, 2, "SCÉNARIO ACTIF"); a.font = F(7, True, DOUX); a.alignment = ind(0)
b = ws.cell(4, 5, "OBJECTIF D'EBITDA 2027  ·  amélioration vs 2026")
b.font = F(7, True, DOUX); b.alignment = R
def saisie(cell):
    cell.fill = fill(PANEL); cell.font = F(10, True, AZUR); cell.alignment = Cn
    cell.border = Border(*[sd(AZUR)] * 4)
saisie(ws["C4"]); saisie(ws["F4"])
ws["F4"].number_format = '+0.0%;-0.0%;"—"'

# ---- ligne 5 : LE VERDICT -------------------------------------------------
# F5 porte TEC_EBITDA : la cellule et son nom restent, la valeur part et le
# format ";;;" la rend muette. Le texte du verdict deborde librement dessus.
ws["F5"].value = None; ws["F5"].number_format = ";;;"
ws["E5"].value = None
for c in range(2, NC + 1):
    x = ws.cell(5, c); x.fill = fill(PANEL)
    x.border = Border(top=sd(FILET), bottom=sd(FILET))
ws.row_dimensions[5].height = 24
v = ws.cell(5, 2, '=IF(D12>=$O$4,"✓   Objectif atteint   ·   "&TEXT(D12-$O$4,"+#,##0 €")'
                  '&" au-dessus de la cible   ·   marge construite "&TEXT(D13,"0.0%")'
                  '&" contre "&TEXT(C13,"0.0%")&" en 2026",'
                  '"✗   Objectif non atteint   ·   il manque "&TEXT($O$4-D12,"#,##0 €")'
                  '&"   ·   marge construite "&TEXT(D13,"0.0%")&" contre "'
                  '&TEXT(C13,"0.0%")&" en 2026")')
v.font = F(11, True, INK); v.alignment = ind(1)

# ---- lignes 6-8 : LE BANDEAU DE CADRAGE, trois blocs ----------------------
BLOCS = [(2, "OBJECTIF 2027",                 "=$O$4",
             '="+"&TEXT($F$4,"0.0%")&" sur "&TEXT(C12,"#,##0 €")&" en 2026, '
             'soit "&TEXT($O$4-C12,"+#,##0 €")&" à trouver"'),
         (4, "CE QUE LES LEVIERS PRODUISENT", "=D12",
             '="scénario « "&$C$4&" »  ·  marge "&TEXT(D13,"0.0%")'),
         (6, "RESTE À TROUVER",              "=$O$4-D12",
             "objectif moins construit  ·  se ferme à chaque levier tiré")]
for r, h in ((6, 12), (7, 26), (8, 14), (9, 22)): ws.row_dimensions[r].height = h
for col, lab, formule, note in BLOCS:
    for c in (col, col + 1):
        ws.cell(6, c).fill = fill(PANEL)
        ws.cell(7, c).fill = fill(PANEL)
        x = ws.cell(8, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    a = ws.cell(6, col, lab); a.font = F(7, True, DOUX); a.alignment = ind(1)
    x = ws.cell(7, col, formule); x.alignment = ind(1)
    x.font = F(20, False, AZUR if col == 4 else INK)
    x.number_format = '#,##0" €"' if col != 6 else '+#,##0" €";-#,##0" €";"0 €"'
    n = ws.cell(8, col, note); n.font = F(7, False, DOUX, True); n.alignment = ind(1)
    if col == 6:
        # Positif : il reste a trouver. Negatif : on est au-dela de la cible.
        x.number_format = '#,##0" €";#,##0" € d\'avance";"0 €"'
    if col == 4: x.font = F(20, False, AZUR)

# ---- le tableau de reconciliation : quatre colonnes, toutes remplies ------
# L'ancienne ligne d'entetes etait en 9 ; la nouvelle est en 10. On efface
# la 9 AVANT d'y poser le titre, sinon "Reference", "Objectif", "Construit"
# survivent dessous et se lisent en transparence a l'impression.
for c in range(3, 12): ws.cell(9, c).value = None
ws.cell(9, 2, "RÉCONCILIATION  —  référence · construit · écart")
ws.cell(9, 2).font = F(9.5, True, INK); ws.cell(9, 2).alignment = ind(0)
ws.cell(9, 10, "COEFFICIENTS DE PRIX PAR MARQUE")
ws.cell(9, 10).font = F(9.5, True, INK); ws.cell(9, 10).alignment = ind(0)
for r in (7, 8):
    for c in (10, 11): ws.cell(r, c).value = None
ENT = {2: "Indicateur", 3: "Référence 2026", 4: "Construit 2027  ·  scénario actif",
       5: "Écart", 6: "Écart %"}
for c, lab in ENT.items(): ws.cell(10, c).value = lab
ws.cell(10, 7).value = None
ws.cell(10, 10, "Marque"); ws.cell(10, 11, "Coeff prix")
for c in list(range(2, 8)) + [10, 11]:
    x = ws.cell(10, c); x.fill = fill(FOND); x.font = F(8, True, INK)
    x.border = Border(top=sd(FILET), bottom=sd(AZUR, "medium"))
    x.alignment = ind(0) if c in (2, 10) else Cn
ws.row_dimensions[10].height = 24

# Les quatre lignes sont reecrites en entier : le CONSTRUIT descend de E en D,
# et les deux colonnes d'ecart se recalent derriere.
CONSTRUIT = {11: ws.cell(11, 5).value, 12: ws.cell(12, 5).value, 14: ws.cell(14, 5).value}
for r, f_ in CONSTRUIT.items(): ws.cell(r, 4).value = f_
ws.cell(13, 4).value = "=IFERROR(D12/D11,0)"
for r in (11, 12, 13, 14):
    ws.cell(r, 5).value = "=D{0}-C{0}".format(r)
    ws.cell(r, 6).value = ("=IFERROR(D{0}/C{0}-1,0)".format(r) if r != 13 else None)
    ws.cell(r, 7).value = None
FMT = {11: '#,##0" €"', 12: '#,##0" €"', 13: '0.0%', 14: '#,##0'}
ECART = {11: '+#,##0" €";-#,##0" €";"—"', 12: '+#,##0" €";-#,##0" €";"—"',
         13: '+0.00" pt";-0.00" pt";"—"', 14: '+#,##0;-#,##0;"—"'}
for r in range(11, 15):
    eb = r == 12
    for c in range(2, 8):
        x = ws.cell(r, c); x.fill = fill(GRIS if eb else PANEL)
        x.border = Border(bottom=sd(INK, "medium") if eb else sd(FILET))
    ws.cell(r, 2).font = F(8.5, eb); ws.cell(r, 2).alignment = ind(1)
    for c in (3, 4):
        x = ws.cell(r, c); x.font = F(9.5 if eb else 8.5, eb, AZUR if (eb and c == 4) else INK)
        x.alignment = R; x.number_format = FMT[r]
    x = ws.cell(r, 5); x.font = F(9 if eb else 8.5, eb); x.alignment = R
    x.number_format = ECART[r]
    x = ws.cell(r, 6); x.font = F(8, False, DOUX); x.alignment = R
    x.number_format = '+0.0%;-0.0%;"—"'
    ws.row_dimensions[r].height = 16

for r in range(11, 16):
    for c in (10, 11):
        x = ws.cell(r, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    ws.cell(r, 10).font = F(8); ws.cell(r, 10).alignment = ind(1)
    x = ws.cell(r, 11); x.font = F(9, True, AZUR); x.alignment = Cn
    x.number_format = '0.00'; x.border = Border(*[sd(AZUR)] * 4); x.fill = fill(PANEL)

# ---- les onze leviers -----------------------------------------------------
# Trois jeux de valeurs, un INDEX/MATCH qui bascule sur le scenario. Les trois
# colonnes sont saisissables : c'est la que se parametrent les scenarios.
for r, txt in ((18, "LEVIERS DE CROISSANCE  ·  ce qui fait le chiffre d'affaires"),
               (29, "LEVIERS DE COÛTS  ·  ce qui fait la marge"),
               (37, "CONSTANTE  ·  hors scénario")):
    x = ws.cell(r, 2, txt); x.font = F(9.5, True, INK); x.alignment = ind(0)
    ws.row_dimensions[r].height = 20
for c in range(2, 8):
    x = ws.cell(20, c); x.fill = fill(FOND); x.font = F(8, True, INK)
    x.border = Border(top=sd(FILET), bottom=sd(AZUR, "medium"))
    x.alignment = ind(0) if c == 2 else Cn
ws.cell(20, 2, "Paramètre"); ws.cell(20, 6, "ACTIF  ·  scénario retenu")
ws.row_dimensions[20].height = 24
ws.cell(21, 2).value = None
for c in (3, 4, 5):
    x = ws.cell(21, c); x.font = F(7.5, True, DOUX); x.alignment = Cn
    x.fill = fill(FOND); x.border = Border(bottom=sd(FILET))
LIGNES = list(range(22, 28)) + list(range(31, 36)) + [39]
for r in LIGNES:
    for c in range(2, 8):
        x = ws.cell(r, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    ws.cell(r, 2).font = F(8.5); ws.cell(r, 2).alignment = ind(1)
    pct = r != 39
    for c in (3, 4, 5):
        x = ws.cell(r, c); x.font = F(8.5, False, AZUR); x.alignment = Cn
        x.number_format = '+0.00%;-0.00%;"—"' if pct else '#,##0" €"'
        x.border = Border(bottom=sd(FILET), left=sd(PALE), right=sd(PALE))
    x = ws.cell(r, 6); x.font = F(9, True, INK); x.alignment = Cn
    x.number_format = '+0.00%;-0.00%;"—"' if pct else '#,##0" €"'
    x.fill = fill(GRIS); x.border = Border(bottom=sd(FILET))
    ws.cell(r, 7).value = None
    ws.row_dimensions[r].height = 15.5
for r in (16, 17, 19, 28, 30, 36, 38): ws.row_dimensions[r].height = 8

# ---- les regles conditionnelles ------------------------------------------
ws.conditional_formatting = ConditionalFormattingList()
# Le verdict : vert s'il est atteint, rouge sinon. Une seule regle porte le
# jugement, le texte porte le fait.
for f_, coul in (('$D$12>=$O$4', VERT_T), ('$D$12<$O$4', ROUGE_T)):
    ws.conditional_formatting.add("B5:L5", Rule(type="expression", formula=[f_],
        dxf=DifferentialStyle(font=Font(bold=True, color=coul))))
# L'ecart a aller chercher : il est positif tant qu'on n'y est pas.
for op, coul in (("greaterThan", ROUGE_T), ("lessThanOrEqual", VERT_T)):
    ws.conditional_formatting.add("F7:G7", CellIsRule(operator=op, formula=["0"],
        font=Font(name=UI, size=20, color=coul)))
for c1 in (5, 6):
    for op, coul in (("greaterThan", VERT_T), ("lessThan", ROUGE_T)):
        ws.conditional_formatting.add("%s11:%s14" % (GL(c1), GL(c1)),
            CellIsRule(operator=op, formula=["0"], font=Font(name=UI, size=8.5, color=coul)))
ws.cell(41, 2, "Le chiffre d'affaires n'est pas une saisie : il vient du socle CRM, la rentrée est "
               "déjà engagée. Seul l'objectif d'EBITDA se décide, et les onze leviers ferment l'écart.")
ws.cell(41, 2).font = F(7.5, False, DOUX, True); ws.cell(41, 2).alignment = ind(0)

# ---- la feuille Pilotage : meme charte, sans toucher a la mecanique -------
pl = wb["Pilotage"]
# D12 ne porte plus l'objectif -- il porte le construit. La chaine de verdict
# du Pilotage le lisait trois fois : on la repointe sur la zone technique.
if isinstance(pl["B12"].value, str):
    pl["B12"] = pl["B12"].value.replace("Cadrage!$D$12", "Cadrage!$O$4")
pl.sheet_view.showGridLines = False
for r in range(1, 14):
    for c in range(1, 24): pl.cell(r, c).fill = fill(FOND)
for r in (1, 2):
    for c in range(1, 24): pl.cell(r, c).fill = fill(INK)
for c in range(1, 24): pl.cell(3, c).fill = fill(AZUR)
pl.cell(2, 2).value = None
t = pl.cell(2, 2, "PILOTAGE 2027  —  COCKPIT DE DÉCISION")
t.font = F(14, True, "FFFFFF"); t.alignment = ind(0)
pl.cell(1, 2, "EDUSERVICES · où mettre l'euro suivant").font = F(8, False, PALE)
pl.cell(1, 2).alignment = ind(0)
pl.cell(2, 7).value = None
for r, h in ((1, 16), (2, 24), (3, 3), (9, 12), (10, 26), (12, 22)): pl.row_dimensions[r].height = h
for col in (2, 4, 6, 8, 10):
    for c in (col, col + 1):
        pl.cell(8, c).fill = fill(AZUR)
        for r in (9, 10):
            x = pl.cell(r, c); x.fill = fill(PANEL)
            x.border = Border(bottom=sd(FILET) if r == 10 else None)
    pl.cell(9, col).font = F(7, True, DOUX); pl.cell(9, col).alignment = ind(1)
    x = pl.cell(10, col); x.font = F(18, False, INK); x.alignment = ind(1)
pl.row_dimensions[8].height = 3
for col, fmt in ((2, '0.0,," M€"'), (4, '0.0,," M€"'), (6, '0.0%'), (8, '#,##0'), (10, '+0.0%;-0.0%;"—"')):
    pl.cell(10, col).number_format = fmt
for c in range(2, 24):
    x = pl.cell(12, c); x.fill = fill(PANEL); x.border = Border(top=sd(FILET), bottom=sd(FILET))
pl.cell(12, 2).font = F(11, True, INK); pl.cell(12, 2).alignment = ind(1)

wb.save(OUT)
print("%s ecrit" % OUT)
print("  bandeau 1-3 · commande 4 · verdict 5 · cadrage 6-8 · réconciliation 9-14")
print("  leviers 18-39 · note 41")
print("  ancres gelées : C4 F4 F5 P1 C11 D12 · C22:E27 C31:E35 C39 · K11:K15")
