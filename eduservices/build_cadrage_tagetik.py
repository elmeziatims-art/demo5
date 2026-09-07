#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_cadrage_tagetik.py — Cadrage & Pilotage, refonte complete.

ENTREE  CAD_PIL_EBITDA_DRIVEN.xlsx     le classeur du 01/09
SORTIE  CAD_PIL_TAGETIK.xlsx

=============================================================================
CE QUE LA RELECTURE A TROUVE, ET QUI ALLAIT AU-DELA DES EN-TETES

  - DEUX TITRES SUPERPOSES en ligne 2 : le nouveau en B, l'ancien toujours
    en C.
  - LES EN-TETES NE SE VOYAIENT PAS. Je les avais posees sans aplat, avec un
    simple filet azur -- la grammaire des rapports de reference. Mais leurs
    rapports sont sur fond BLANC : un entete sans aplat s'y detache. Ici la
    page est grise et les lignes sont blanches, donc un entete gris se fond
    dans la page au lieu de coiffer le tableau. Il prend donc un aplat.
  - PILOTAGE N'ETAIT PAS MISE EN FORME sous la ligne 12. Les deux blocs de
    quatorze campus sortaient bruts.
  - DES LIBELLES DE CHANTIER RESTAIENT A L'ECRAN : "COLumn to hide" en A15,
    "a masquer" en U17:W17.
  - LA COLONNE A DE PILOTAGE PORTE LES CODES CAMPUS sur une largeur de 3,3 :
    illisible. Elle est masquee -- Marque et Ville identifient le campus mieux
    qu'un code, et les 406 formules qui la lisent continuent de le faire, une
    colonne masquee se calcule normalement.
  - LES LEVIERS AVAIENT DEUX LIGNES D'ENTETE, la 20 qui affiche =C21 et la 21
    qui porte les noms. La 21 est masquee : elle nourrit la 20 et le MATCH du
    scenario, elle n'a rien a montrer.
  - AUCUN ENCODAGE VISUEL sur les deux tableaux de Pilotage, alors que c'est
    exactement la ou il sert : le CAC marginal va de 890 a 2 193 EUR selon le
    campus, et c'est LA question de la page -- ou mettre l'euro suivant.

=============================================================================
LES ANCRES GELEES -- 47 noms definis et pres de 15 000 renvois

    Cadrage    C4 SCENARIO_ACTIF · F4 TEC_PL · F5 TEC_EBITDA · P1 SCENARIO_CODE
               C11 reference de CA
               C22:E27 C31:E35 C39   les onze leviers, HYP_*
               K11:K15               les coefficients de prix
    Pilotage   J19:J32 HYP_CAP_RETENU · K19:K32 BUD_REF_CAP

L'objectif d'EBITDA en euros vit en O4, derriere le rideau, et non plus au
milieu du tableau. Une seule formule le lisait, Pilotage!B12, repointee.
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import CellIsRule, Rule, ColorScaleRule, DataBarRule
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.utils import get_column_letter as GL

SRC, OUT = "CAD_PIL_EBITDA_DRIVEN.xlsx", "CAD_PIL_TAGETIK.xlsx"

INK, AZUR, ROUGE, VERT = "262626", "007AC3", "E5202E", "85BC20"
PALE, GRIS = "A6D0EA", "E7E6E6"
VERT_T, ROUGE_T = "5F8A17", "C41822"
FOND, PANEL, FILET, DOUX = "F5F6F7", "FFFFFF", "D5D7DA", "6B7075"
HM_BAS, HM_MED, HM_HAUT = "F6C9CC", "F7F7F5", "DCEBC0"
UI = "Arial"
def F(sz=8, b=False, c=INK, i=False): return Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd   = lambda c=FILET, st="thin": Side(style=st, color=c)
R  = Alignment("right", vertical="center")
Cn = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)
WRAP = Alignment("center", vertical="bottom", wrap_text=True)

wb = openpyxl.load_workbook(SRC)

# ============================================================================
#  LE SYSTEME, partage par les deux onglets
# ============================================================================
def page(ws, nc, nr):
    ws.sheet_view.showGridLines = False
    for r in range(1, nr + 1):
        for c in range(1, nc + 1): ws.cell(r, c).fill = fill(FOND)

def bandeau(ws, nc, sur, titre):
    for r in (1, 2):
        for c in range(1, nc + 1): ws.cell(r, c).fill = fill(INK)
    for c in range(1, nc + 1): ws.cell(3, c).fill = fill(AZUR)
    a = ws.cell(1, 2, sur);   a.font = F(7.5, False, PALE);    a.alignment = ind(0)
    t = ws.cell(2, 2, titre); t.font = F(14, True, "FFFFFF");  t.alignment = ind(0)
    for r, h in ((1, 14), (2, 24), (3, 3)): ws.row_dimensions[r].height = h

def titre_bloc(ws, row, c1, c2, num, titre, note=""):
    """Un numero azur, un titre encre, un filet sous toute la largeur du bloc."""
    for c in range(c1, c2 + 1):
        x = ws.cell(row, c); x.fill = fill(FOND); x.border = Border(bottom=sd(INK))
    t = ws.cell(row, c1, "%s   %s" % (num, titre)); t.font = F(10, True, INK); t.alignment = ind(0)
    if note:
        n = ws.cell(row, c2, note + " "); n.font = F(7, False, DOUX, True); n.alignment = R
    ws.row_dimensions[row].height = 20

def entete(ws, row, c1, c2, gauche=(), h=24):
    """UN APLAT. Sur une page grise a lignes blanches, un entete sans aplat
    disparait dans le fond -- c'etait le defaut signale."""
    for c in range(c1, c2 + 1):
        x = ws.cell(row, c); x.fill = fill(GRIS); x.font = F(7.5, True, INK)
        x.border = Border(top=sd(FILET), bottom=sd(INK, "medium"))
        x.alignment = ind(1) if c in gauche else WRAP
    ws.row_dimensions[row].height = h

def ligne(ws, row, c1, c2, total=False, h=15):
    for c in range(c1, c2 + 1):
        x = ws.cell(row, c); x.fill = fill(GRIS if total else PANEL)
        x.border = Border(top=sd(INK, "medium") if total else None,
                          bottom=sd(INK, "medium") if total else sd(FILET))
    ws.row_dimensions[row].height = h

def saisie(cell, sz=10):
    cell.fill = fill(PANEL); cell.font = F(sz, True, AZUR); cell.alignment = Cn
    cell.border = Border(*[sd(AZUR)] * 4)

def signe(ws, plage, sz=8):
    for op, coul in (("greaterThan", VERT_T), ("lessThan", ROUGE_T)):
        ws.conditional_formatting.add(plage, CellIsRule(operator=op, formula=["0"],
            font=Font(name=UI, size=sz, color=coul)))

def echelle(ws, plage, lo, mid, hi, inverse=False):
    a, b = (HM_HAUT, HM_BAS) if inverse else (HM_BAS, HM_HAUT)
    ws.conditional_formatting.add(plage, ColorScaleRule(
        start_type="num", start_value=lo, start_color="FF" + a,
        mid_type="num",   mid_value=mid,  mid_color="FF" + HM_MED,
        end_type="num",   end_value=hi,   end_color="FF" + b))

# ============================================================================
#  ONGLET 1 — CADRAGE
# ============================================================================
ws = wb["Cadrage"]
NC = 11
page(ws, NC, 70)
bandeau(ws, NC, "EDUSERVICES · budget 2027 piloté par l'EBITDA",
        "CADRAGE 2027  —  LE POSTE DE COMMANDE")
ws["C2"].value = None                    # l'ancien titre, qui doublait le neuf

# LA CAUSE DU "PAS D'ENTETE" : les lignes 10, 21, 59 et 66 sont MASQUEES dans
# le classeur d'origine. La 10 est justement la ligne d'entetes du tableau de
# reconciliation -- je l'ai stylee pendant des heures sans jamais la voir.
# On les rouvre toutes, sauf la 21 qui est bel et bien technique.
for r in (10, 59, 66): ws.row_dimensions[r].hidden = False
ws.column_dimensions["A"].width = 2.6
for L_, w_ in (("B", 46), ("C", 15.5), ("D", 17), ("E", 14), ("F", 14),
               ("G", 2.6), ("H", 2.0), ("I", 2.0), ("J", 20), ("K", 12)):
    ws.column_dimensions[L_].width = w_
for c in range(12, 20): ws.column_dimensions[GL(c)].hidden = True

# ---- la zone technique, derriere le rideau -------------------------------
ws.cell(3, 13, "ZONE TECHNIQUE — rien de ceci ne s'affiche").font = F(7, False, DOUX, True)
ws.cell(4, 13, "Objectif EBITDA 2027 (€)").font = F(7.5, False, DOUX)
o = ws.cell(4, 14, "=C12*(1+$F$4)"); o.number_format = '#,##0" €"'; o.font = F(9, True, AZUR)

# ---- ligne 4 : LA COMMANDE ------------------------------------------------
for c in range(2, NC + 1):
    x = ws.cell(4, c); x.fill = fill(FOND); x.border = Border(bottom=sd(FILET))
ws.row_dimensions[4].height = 24
ws.cell(4, 2, "LA COMMANDE  ·  les deux seules cellules à saisir").font = F(7.5, True, DOUX)
ws.cell(4, 2).alignment = ind(0)
# ATTENTION : C4 et F4 SONT les deux saisies. Les libelles vont a leur gauche.
ws.cell(4, 4, "Objectif d'EBITDA  ·  amélioration vs 2026")
ws.cell(4, 4).font = F(7.5, True, DOUX); ws.cell(4, 4).alignment = R
ws.cell(4, 5).value = None
saisie(ws["C4"]); saisie(ws["F4"])
ws["F4"].number_format = '+0.0%;-0.0%;"—"'

# ---- ligne 5 : LE VERDICT -------------------------------------------------
ws["F5"].value = None; ws["F5"].number_format = ";;;"    # TEC_EBITDA, nom conserve
ws["E5"].value = None
for c in range(2, NC + 1):
    x = ws.cell(5, c); x.fill = fill(PANEL); x.border = Border(top=sd(FILET), bottom=sd(FILET))
ws.row_dimensions[5].height = 26
v = ws.cell(5, 2, '=IF(D12>=$N$4,"✓   OBJECTIF ATTEINT   ·   "&TEXT(D12-$N$4,"+#,##0 €")'
                  '&" au-dessus de la cible   ·   marge construite "&TEXT(D13,"0.0%")'
                  '&" contre "&TEXT(C13,"0.0%")&" en 2026",'
                  '"✗   OBJECTIF NON ATTEINT   ·   il manque "&TEXT($N$4-D12,"#,##0 €")'
                  '&"   ·   marge construite "&TEXT(D13,"0.0%")&" contre "'
                  '&TEXT(C13,"0.0%")&" en 2026")')
v.font = F(11, True, INK); v.alignment = ind(1)

# ---- lignes 6-8 : les trois blocs ----------------------------------------
BLOCS = [(2, "OBJECTIF 2027", "=$N$4", '#,##0" €"', INK,
          '="+"&TEXT($F$4,"0.0%")&" sur "&TEXT(C12,"#,##0 €")&" en 2026, soit "'
          '&TEXT($N$4-C12,"+#,##0 €")&" à trouver"'),
         (4, "CE QUE LES LEVIERS PRODUISENT", "=D12", '#,##0" €"', AZUR,
          '="scénario « "&$C$4&" »   ·   marge "&TEXT(D13,"0.0%")'),
         (6, "RESTE À TROUVER", "=$N$4-D12",
          '#,##0" €";#,##0" € d\'avance";"0 €  ✓"', INK,
          '"objectif moins construit  ·  se ferme à chaque levier"')]
for r, h in ((6, 12), (7, 28), (8, 15), (9, 8)): ws.row_dimensions[r].height = h
for col, lab, formule, fmt, coul, note in BLOCS:
    for c in (col, col + 1):
        ws.cell(6, c).fill = fill(AZUR if col == 4 else GRIS)
        ws.cell(7, c).fill = fill(PANEL)
        x = ws.cell(8, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    a = ws.cell(6, col, lab)
    a.font = F(7, True, "FFFFFF" if col == 4 else DOUX); a.alignment = ind(1)
    x = ws.cell(7, col, formule); x.alignment = ind(1)
    x.font = F(20, False, coul); x.number_format = fmt
    n = ws.cell(8, col, note if note.startswith("=") else note.strip('"'))
    n.font = F(7, False, DOUX, True); n.alignment = ind(1)

# ---- 10-14 : la reconciliation, et le panneau des coefficients -----------
# LES LIGNES 11 A 14 NE BOUGENT PAS : C11 porte la reference de CA, lue par
# Pilotage. L'entete reste donc en 10, et le titre du bloc remonte en 9.
# Les entetes d'origine etaient en 9, les miennes en 10 : on efface la 9 avant
# d'y poser le titre, sinon "Reference", "Objectif", "Construit" survivent.
for c in range(3, 8): ws.cell(9, c).value = None
ws.cell(7, 10).value = None                      # "Coeff prix par marque (decision)"
for c in (10, 11): ws.cell(9, c).value = None     # ses anciens entetes
titre_bloc(ws, 9, 2, 6, "①", "RÉCONCILIATION", "de 2026 au scénario construit ")
titre_bloc(ws, 9, 10, 11, "②", "COEFFICIENTS DE PRIX")
for c, lab in {2: "Indicateur", 3: "Référence 2026", 4: "Construit 2027",
               5: "Écart", 6: "Écart %"}.items(): ws.cell(10, c).value = lab
ws.cell(10, 7).value = None
ws.cell(10, 10, "Marque"); ws.cell(10, 11, "Coeff")
entete(ws, 10, 2, 6, gauche=(2,)); entete(ws, 10, 10, 11, gauche=(10,))

# Le CONSTRUIT descend de E en D, les deux ecarts se recalent derriere.
for r, f_ in ((11, ws.cell(11, 5).value), (12, ws.cell(12, 5).value), (14, ws.cell(14, 5).value)):
    ws.cell(r, 4).value = f_
ws.cell(13, 4).value = "=IFERROR(D12/D11,0)"
for r in (11, 12, 13, 14):
    ws.cell(r, 5).value = "=D{0}-C{0}".format(r)
    ws.cell(r, 6).value = "=IFERROR(D{0}/C{0}-1,0)".format(r) if r != 13 else None
    ws.cell(r, 7).value = None
FMT   = {11: '#,##0" €"', 12: '#,##0" €"', 13: '0.0%', 14: '#,##0'}
ECART = {11: '+#,##0" €";-#,##0" €";"—"', 12: '+#,##0" €";-#,##0" €";"—"',
         13: '+0.00" pt";-0.00" pt";"—"', 14: '+#,##0;-#,##0;"—"'}
for r in range(11, 15):
    eb = r == 12
    ligne(ws, r, 2, 6, total=eb, h=16)
    ws.cell(r, 2).font = F(9 if eb else 8.5, eb); ws.cell(r, 2).alignment = ind(1)
    for c in (3, 4):
        x = ws.cell(r, c); x.alignment = R; x.number_format = FMT[r]
        x.font = F(10 if eb else 8.5, eb, AZUR if (eb and c == 4) else INK)
    x = ws.cell(r, 5); x.font = F(9 if eb else 8.5, eb); x.alignment = R
    x.number_format = ECART[r]
    x = ws.cell(r, 6); x.font = F(8, False, DOUX); x.alignment = R
    x.number_format = '+0.0%;-0.0%;"—"'
for r in range(11, 16):
    ligne(ws, r, 10, 11, h=16)
    ws.cell(r, 10).font = F(8.5); ws.cell(r, 10).alignment = ind(1)
    saisie(ws.cell(r, 11), 9); ws.cell(r, 11).number_format = '0.00'

# ---- 17-39 : les onze leviers --------------------------------------------
titre_bloc(ws, 17, 2, 6, "③", "LES ONZE LEVIERS",
           "trois jeux de valeurs · le scénario actif désigne la colonne retenue ")
ws.row_dimensions[16].height = 10
# Il y avait DEUX lignes d'entete, la 19 et la 20, l'une affichant le contenu
# de l'autre. On garde la 18, on vide la 20, et la 21 reste masquee : elle
# nourrit le MATCH du scenario, elle n'a rien a montrer.
ws.cell(18, 2).value = None
for c in range(2, 8): ws.cell(20, c).value = None
for c, lab in {2: "Levier", 3: "Cadrage", 4: "Optimiste", 5: "Prudent",
               6: "RETENU"}.items(): ws.cell(18, c).value = lab
ws.cell(18, 7).value = None
entete(ws, 18, 2, 6, gauche=(2,), h=20)
ws.cell(18, 6).fill = fill(AZUR); ws.cell(18, 6).font = F(7.5, True, "FFFFFF")
ws.row_dimensions[19].height = 5
ws.row_dimensions[21].hidden = True
GROUPES = [(20, 22, 27, "CROISSANCE", "ce qui fait le chiffre d'affaires"),
           (29, 31, 35, "COÛTS",      "ce qui fait la marge"),
           (37, 39, 39, "CONSTANTE",  "hors scénario, saisie directe")]
for rt, r0, r1, fam, note in GROUPES:
    for c in range(2, 7): ws.cell(rt, c).fill = fill(FOND); ws.cell(rt, c).value = None
    t = ws.cell(rt, 2, "%s   ·   %s" % (fam, note))
    t.font = F(8, True, AZUR); t.alignment = ind(0)
    ws.row_dimensions[rt].height = 18
    for r in range(r0, r1 + 1):
        ligne(ws, r, 2, 6, h=15.5)
        ws.cell(r, 2).font = F(8.5); ws.cell(r, 2).alignment = ind(1)
        pct = r != 39
        for c in (3, 4, 5):
            saisie(ws.cell(r, c), 8.5)
            ws.cell(r, c).number_format = '+0.00%;-0.00%;"—"' if pct else '#,##0" €"'
        x = ws.cell(r, 6); x.font = F(9, True, INK); x.alignment = Cn
        x.number_format = '+0.00%;-0.00%;"—"' if pct else '#,##0" €"'
        x.fill = fill(GRIS); x.border = Border(bottom=sd(FILET))
        ws.cell(r, 7).value = None
for r in (28, 30, 36, 38, 40): ws.row_dimensions[r].height = 6

# ---- les regles ----------------------------------------------------------
ws.conditional_formatting = ConditionalFormattingList()
for f_, coul in (('$D$12>=$N$4', VERT_T), ('$D$12<$N$4', ROUGE_T)):
    ws.conditional_formatting.add("B5:K5", Rule(type="expression", formula=[f_],
        dxf=DifferentialStyle(font=Font(bold=True, color=coul))))
for op, coul in (("greaterThan", ROUGE_T), ("lessThanOrEqual", VERT_T)):
    ws.conditional_formatting.add("F7:G7", CellIsRule(operator=op, formula=["0"],
        font=Font(name=UI, size=20, color=coul)))
signe(ws, "E11:E14", 8.5); signe(ws, "F11:F14", 8)
signe(ws, "F22:F27", 9); signe(ws, "F31:F35", 9)
ws.cell(42, 2, "Le chiffre d'affaires n'est pas une saisie : il vient du socle CRM, la rentrée est "
               "déjà engagée. Seul l'objectif d'EBITDA se décide, et les onze leviers ferment l'écart.")
ws.cell(42, 2).font = F(7.5, False, DOUX, True); ws.cell(42, 2).alignment = ind(0)

# ============================================================================
#  ONGLET 2 — PILOTAGE
#  Elle n'etait pas mise en forme sous la ligne 12. Deux tableaux de quatorze
#  campus sortaient bruts, avec les codes campus ecrases dans une colonne A de
#  3,3 de large et des libelles de chantier restes a l'ecran.
# ============================================================================
pl = wb["Pilotage"]
NP = 11
page(pl, NP, 58)
bandeau(pl, NP, "EDUSERVICES · budget 2027", "PILOTAGE 2027  —  OÙ METTRE L'EURO SUIVANT")
pl.cell(2, 7).value = None
pl.cell(1, 15).value = None                     # "code scénario ->"
pl.cell(15, 1).value = None                     # "COLumn to hide"
for c in (21, 22, 23): pl.cell(17, c).value = None   # "à masquer"

# La colonne A porte les codes campus sur 3,3 de large : illisible. On la
# masque -- Marque et Ville identifient un campus mieux qu'un code, et les 406
# formules qui la lisent continuent de tourner, une colonne masquee se calcule.
pl.column_dimensions["A"].hidden = True
for L_, w_ in (("B", 13), ("C", 14), ("D", 13), ("E", 14), ("F", 12.5), ("G", 12.5),
               ("H", 13.5), ("I", 12), ("J", 12.5), ("K", 14), ("L", 12.5)):
    pl.column_dimensions[L_].width = w_
for c in range(12, 26): pl.column_dimensions[GL(c)].hidden = True

# ---- le rappel du scenario ------------------------------------------------
for r in (4, 5, 6, 7):
    for c in range(1, NP + 1): pl.cell(r, c).value = None if r != 6 else pl.cell(r, c).value
for c in range(2, NP + 1):
    x = pl.cell(6, c); x.fill = fill(FOND); x.border = Border(bottom=sd(FILET))
pl.row_dimensions[6].height = 22
pl.cell(6, 2, "SCÉNARIO ACTIF").font = F(7.5, True, DOUX); pl.cell(6, 2).alignment = ind(0)
saisie(pl["E6"])
for r, h in ((4, 6), (5, 6), (7, 8), (11, 8), (13, 10)): pl.row_dimensions[r].height = h

# ---- les cinq cartes ------------------------------------------------------
CARTES = [(2, "CA 2027", '0.0,," M€"'), (4, "EBITDA après siège", '0.0,," M€"'),
          (6, "MARGE EBITDA", '0.0%'), (8, "EFFECTIF", '#,##0'),
          (10, "CROISSANCE CA vs 2026", '+0.0%;-0.0%;"—"')]
for r, h in ((8, 3), (9, 12), (10, 28), (12, 26)): pl.row_dimensions[r].height = h
for col, lab, fmt in CARTES:
    for c in (col, col + 1):
        pl.cell(8, c).fill = fill(AZUR)
        pl.cell(9, c).fill = fill(PANEL)
        x = pl.cell(10, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    a = pl.cell(9, col, lab); a.font = F(7, True, DOUX); a.alignment = ind(1)
    x = pl.cell(10, col); x.font = F(19, False, INK); x.alignment = ind(1); x.number_format = fmt
for c in range(2, NP + 1):
    x = pl.cell(12, c); x.fill = fill(PANEL); x.border = Border(top=sd(FILET), bottom=sd(FILET))
pl.cell(12, 2).font = F(11, True, INK); pl.cell(12, 2).alignment = ind(1)
if isinstance(pl["B12"].value, str):
    pl["B12"] = pl["B12"].value.replace("Cadrage!$D$12", "Cadrage!$N$4")

# ---- bloc 1 : le cap strategique -----------------------------------------
titre_bloc(pl, 16, 2, 11, "①", "CAP STRATÉGIQUE PAR CAMPUS",
           "le CAC marginal dit où l'euro suivant rapporte le plus ")
for r in (14, 15, 17): pl.row_dimensions[r].height = 6
CAP = {2: "Marque", 3: "Ville", 4: "CAC marginal", 5: "Croiss. leads", 6: "Intensité mkt",
       7: "Cap efficience", 8: "Cap momentum", 9: "Cap potentiel", 10: "CAP RETENU",
       11: "Budget acq. réf."}
for c, lab in CAP.items(): pl.cell(18, c).value = lab
pl.cell(18, 12).value = None
entete(pl, 18, 2, 11, gauche=(2, 3), h=28)
pl.cell(18, 10).fill = fill(AZUR); pl.cell(18, 10).font = F(7.5, True, "FFFFFF")
FCAP = {4: '#,##0" €"', 5: '+0.0%;-0.0%;"—"', 6: '0.00%', 7: '0.00', 8: '0.00',
        9: '0.00', 10: '0.00', 11: '#,##0" €"'}
for r in range(19, 33):
    ligne(pl, r, 2, 11, h=15)
    for c in (2, 3): pl.cell(r, c).font = F(8.5, c == 3); pl.cell(r, c).alignment = ind(1)
    for c, fmt in FCAP.items():
        x = pl.cell(r, c); x.font = F(9 if c == 10 else 8.5, c == 10,
                                      AZUR if c == 10 else INK)
        x.alignment = R if c in (4, 11) else Cn; x.number_format = fmt

# ---- bloc 2 : la synthese -------------------------------------------------
titre_bloc(pl, 36, 2, 11, "②", "SYNTHÈSE PAR CAMPUS",
           "ce que le scénario actif produit, campus par campus ")
for r in (33, 34, 35, 37): pl.row_dimensions[r].height = 6
SYN = {2: "Marque", 3: "Ville", 4: "Effectif", 5: "CA 2027", 6: "Prix moyen",
       7: "Part du CA", 8: "EBITDA campus", 9: "Marge EBITDA", 10: "EBITDA / étudiant",
       11: "Budget rejoué"}
for c, lab in SYN.items(): pl.cell(38, c).value = lab
entete(pl, 38, 2, 11, gauche=(2, 3), h=28)
FSYN = {4: '#,##0', 5: '#,##0" €"', 6: '#,##0" €"', 7: '0.0%', 8: '#,##0" €"',
        9: '0.0%', 10: '#,##0" €"', 11: '#,##0" €"'}
for r in range(39, 56):
    tot = r >= 53
    ligne(pl, r, 2, 11, total=tot, h=15)
    for c in (2, 3):
        pl.cell(r, c).font = F(8.5, tot or c == 3); pl.cell(r, c).alignment = ind(1)
    for c, fmt in FSYN.items():
        x = pl.cell(r, c); x.font = F(9 if tot else 8.5, tot); x.alignment = R
        x.number_format = fmt
    if tot: pl.cell(r, 2).value = pl.cell(r, 1).value; pl.cell(r, 3).value = None

# ---- l'encodage visuel, la ou il sert ------------------------------------
pl.conditional_formatting = ConditionalFormattingList()
# LE CAC MARGINAL EST LA QUESTION DE LA PAGE : de 890 EUR a Bordeaux a 2 193 EUR
# a Tunon Paris. Bas = bon, donc l'echelle est INVERSEE : le vert va au CAC bas.
echelle(pl, "D19:D32", 800, 1300, 2300, inverse=True)
pl.conditional_formatting.add("J19:J32", DataBarRule(start_type="num", start_value=0,
    end_type="num", end_value=1.5, color="FF" + PALE, showValue=True))
# La marge par campus : bornes absolues, pour que Tunon reste rouge d'un
# lancement a l'autre.
echelle(pl, "I39:I52", 0.02, 0.12, 0.22)
pl.conditional_formatting.add("G39:G52", DataBarRule(start_type="num", start_value=0,
    end_type="num", end_value=0.20, color="FF" + PALE, showValue=True))
signe(pl, "E19:E32", 8.5)
pl.cell(57, 2, "Le CAC marginal est le coût du prochain inscrit, pas la moyenne des inscrits déjà "
               "acquis : c'est lui qui dit où le budget suivant rapporte le plus.")
pl.cell(57, 2).font = F(7.5, False, DOUX, True); pl.cell(57, 2).alignment = ind(0)

wb.save(OUT)
print("%s ecrit" % OUT)
print("  CADRAGE   bandeau 1-3 · commande 4 · verdict 5 · blocs 6-8")
print("            ① réconciliation 9-14   ② coefficients 9-15   ③ leviers 17-39")
print("  PILOTAGE  bandeau 1-3 · scénario 6 · cartes 8-10 · verdict 12")
print("            ① cap stratégique 16-32   ② synthèse 36-55")
