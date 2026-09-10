#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_patch_cadpil.py — le classeur de patch de CAD_PIL.

POURQUOI UN PATCH ET PAS UN FICHIER CORRIGE. Faire relire CAD_PIL par openpyxl
et le reecrire lui couterait ses valeurs en cache et son extension Tagetik. On
ne rend pas a quelqu'un une copie degradee de son propre fichier. Ce classeur
ne contient donc que ce qui doit changer : douze formules a coller, et un bloc
de valeurs a remettre dans le bon ordre.

LES TROIS DEFAUTS SERIEUX ONT LA MEME CAUSE : la remise en page a deplace des
blocs, et les formules qui les visaient n'ont pas suivi.

  _CALC_MOTEUR!AC pointe Cadrage!K12:K16, la table des coefficients de prix est
  passee en K24:K28  ->  coefficient nul, la hausse tarifaire n'est jamais
  appliquee, 77 403 EUR de chiffre d'affaires manquants.

  Cadrage!F34:F38 pointent une ligne trop haut  ->  chaque levier de cout
  affiche le levier precedent, et l'inflation affiche zero. Le calcul, lui, est
  juste : _CALC_PNL lit les colonnes C/D/E, pas F.

  Pilotage!D19:L32 : les colonnes A/B/C ont ete retriees par marque, les
  colonnes de mesure sont restees en ordre alphabetique. Chaque ligne porte les
  chiffres d'un autre campus.

CE QUE LE PATCH CHANGE EN PLUS, ET C'EST DELIBERE : D, K et L de Pilotage
deviennent des FORMULES qui vont chercher la valeur par le nom du campus. Un
retri ne pourra plus les desaligner. Les colonnes E a I restent des valeurs --
je ne connais pas leur regle de calcul -- mais elles sont livrees dans le bon
ordre, pretes a coller.
"""
import openpyxl, warnings
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.utils import get_column_letter as GL
warnings.filterwarnings("ignore")

SRC = "/tmp/claude-0/-home-user-demo5/b8c71a6a-b866-551a-b98b-eceadba2b120/scratchpad/CAD_PIL_nav211.xlsx"
OUT = "CAD_PIL_PATCH.xlsx"
INK, AZUR, ROUGE, PALE, GRIS = "262626", "007AC3", "E5202E", "A6D0EA", "E7E6E6"
VERT_T, ROUGE_T, OCRE = "5F8A17", "C41822", "B26B00"
FOND, PANEL, FILET, DOUX = "F5F6F7", "FFFFFF", "D5D7DA", "6B7075"
CALC, VUE = "FDF3E7", "E8F1F9"
UI = "Arial"
F = lambda sz=8, b=False, c=INK, i=False: Font(name=UI, size=sz, bold=b, color=c, italic=i)
MONO = lambda sz=7.5, c=INK: Font(name="Consolas", size=sz, color=c)
fill = lambda c: PatternFill("solid", fgColor=c)
sd = lambda c=FILET: Side(style="thin", color=c)
R = Alignment("right", vertical="center"); Cn = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)
WRAP = Alignment("center", vertical="bottom", wrap_text=True)

#  ---- les douze corrections -------------------------------------------------
#  (gravite, onglet, cellule, recopier jusqu'a, contenu, ce que ca corrige)
P = [
 ("1 · FAUSSE UN CHIFFRE", "_CALC_MOTEUR", "AC2", "AC190",
  '=IF($A2="","",IF($F2="MBWAY",Cadrage!$K$24,IF($F2="ISCOM",Cadrage!$K$25,'
  'IF($F2="IPAC",Cadrage!$K$26,IF($F2="PIGIER",Cadrage!$K$27,Cadrage!$K$28)))))',
  "La table des coefficients de prix est en K24:K28, la formule visait K12:K16. "
  "Coefficient nul ⇒ hausse tarifaire jamais appliquée : +77 403 € de CA, et l'objectif "
  "d'EBITDA passe de « il manque 52 748 € » à « dépassé de 15 737 € »."),
 ("2 · FAUSSE LE PILOTAGE", "Pilotage", "D19", "D32",
  '=SUMIFS(Campagne!$N$2:$N$15,Campagne!$C$2:$C$15,$A19)',
  "Le CAC marginal était collé en dur dans l'ordre alphabétique, alors que la colonne A "
  "a été retriée par marque. MBway Paris affichait 1 034 € — le CAC d'Ipac Montpellier — "
  "au lieu de 1 475 €. En formule, un retri ne peut plus le désaligner."),
 ("2 · FAUSSE LE PILOTAGE", "Pilotage", "K19", "K32",
  '=SUMIFS(Campagne!$G$2:$G$15,Campagne!$C$2:$C$15,$A19)',
  "Même cause, et c'est le plus grave : MBway Paris portait un budget d'acquisition de "
  "15 178 € au lieu de 68 291 €. Cette colonne alimente le budget rejoué du moteur."),
 ("2 · FAUSSE LE PILOTAGE", "Pilotage", "L19", "L32",
  '=$A19',
  "La colonne Entity doublonnait la colonne A dans un autre ordre. En formule, elle ne "
  "peut plus mentir — et elle sert de contrôle visuel."),
 ("2 · FAUSSE LE PILOTAGE", "Pilotage", "E19:I32", "—",
  "→ voir l'onglet « Bloc Pilotage »",
  "Croiss. leads, Intensité mkt et les trois Cap étaient dans le même désordre. Le bloc "
  "réordonné est prêt à coller dans la feuille suivante."),
 ("3 · PIÈGE EN SÉANCE", "—", "—", "—", "aucune correction : c'est une conséquence",
  "Tant que tous les « Cap retenu » valent 1, le décalage de la colonne K s'annule dans "
  "le moteur. Le jour où vous bougez un cap en démo, la réallocation part sur les mauvais "
  "campus. Les trois corrections ci-dessus le désamorcent."),
 ("4 · AFFICHAGE", "Cadrage", "F34", "—",
  '=INDEX(C34:E34,MATCH(Cadrage!$C$5,$C$22:$E$22,0))',
  "Les cinq leviers de coûts pointaient une ligne trop haut : chacun affichait le levier "
  "précédent, et l'inflation affichait 0,00 % au lieu de 2,00 %. Le calcul était juste "
  "(_CALC_PNL lit C/D/E), mais la colonne RETENU est celle que le CFO lit."),
 ("4 · AFFICHAGE", "Cadrage", "F35", "—",
  '=INDEX(C35:E35,MATCH(Cadrage!$C$5,$C$22:$E$22,0))', "idem — politique salariale"),
 ("4 · AFFICHAGE", "Cadrage", "F36", "—",
  '=INDEX(C36:E36,MATCH(Cadrage!$C$5,$C$22:$E$22,0))', "idem — effectifs permanents"),
 ("4 · AFFICHAGE", "Cadrage", "F37", "—",
  '=INDEX(C37:E37,MATCH(Cadrage!$C$5,$C$22:$E$22,0))', "idem — effort de productivité"),
 ("4 · AFFICHAGE", "Cadrage", "F38", "—",
  '=INDEX(C38:E38,MATCH(Cadrage!$C$5,$C$22:$E$22,0))', "idem — coûts de structure"),
 ("4 · AFFICHAGE", "Cadrage", "F22", "—", "(vider la cellule)",
  "Formule parasite sur la ligne d'en-tête : elle affiche 0,08 dans la ligne "
  "« Cadrage · Optimiste · Prudent »."),
 ("4 · AFFICHAGE", "Cadrage", "D14", "—", '=IFERROR(D13/D12,0)',
  "La marge d'EBITDA construite divisait par D11, qui est l'en-tête texte « Construit "
  "2027 » : elle affichait 0 %, et l'écart −16,6 points."),
 ("4 · AFFICHAGE", "Cadrage", "D9", "—",
  '="scénario « "&$C$5&" »   ·   marge "&TEXT(D14,"0.0%")',
  "Pointait $C$4 (vide — le scénario est en C5) et D13, l'EBITDA en euros affiché en "
  "pourcentage : « scénario «  » · marge 40 430 182,3 % »."),
 ("4 · AFFICHAGE", "Cadrage", "B9", "—",
  '="+"&TEXT($F$5,"0.00%")&" sur "&TEXT(C13,"#,##0 €")&" en 2026, soit "'
  '&TEXT($B$8-C13,"+#,##0 €")&" à trouver"',
  "Pointait $F$4 (vide) et C12, le chiffre d'affaires, alors que l'objectif B8 se calcule "
  "sur C13, l'EBITDA. La queue de la formule visait $O$4, vide elle aussi."),
 ("4 · AFFICHAGE", "Pilotage", "J10", "—", '=IFERROR(E55/Cadrage!$C$12-1,0)',
  "« Croissance CA vs 2026 » divisait le CA 2027 par l'EBITDA 2026 : 528 % au lieu "
  "de 4,6 %."),
 ("5 · COSMÉTIQUE", "Cadrage", "B18", "—", "②   LES DOUZE LEVIERS",
  "Le titre annonce onze leviers ; il y en a douze — six de croissance, cinq de coûts, "
  "une constante."),
 ("5 · COSMÉTIQUE", "Cadrage", "J21 / J22", "—", "(supprimer le doublon)",
  "Le titre « ② COEFFICIENTS DE PRIX » figure deux fois, et le numéro ② est déjà pris "
  "par le bloc des leviers."),
]

# ============================================================================
#  ONGLET 1 — LES CORRECTIONS
# ============================================================================
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Les corrections"
NC = 8
ws.sheet_view.showGridLines = False
for r in range(1, 46):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(FOND)
for r in (1, 2):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(INK)
for c in range(1, NC + 1): ws.cell(3, c).fill = fill(AZUR)
ws.cell(1, 2, "EDUSERVICES · CAD_PIL").font = F(7.5, False, PALE); ws.cell(1, 2).alignment = ind(0)
ws.cell(2, 2, "LES CORRECTIONS  —  douze formules à coller, un bloc à réordonner").font = F(14, True, "FFFFFF")
ws.cell(2, 2).alignment = ind(0)
ws.column_dimensions["A"].width = 2.4
for c, w in ((2, 20), (3, 15), (4, 13), (5, 13), (6, 74), (7, 62), (8, 14)):
    ws.column_dimensions[GL(c)].width = w
for r, h in ((1, 14), (2, 24), (3, 3), (5, 22), (6, 16)): ws.row_dimensions[r].height = h

ws.cell(5, 2, "Trois défauts sérieux, et ils ont la même cause.").font = F(12, True, INK)
ws.cell(5, 2).alignment = ind(0)
ws.cell(6, 2, "La remise en page a déplacé des blocs, et les formules qui les visaient ne les ont pas "
              "suivis. Rien n'est cassé dans le modèle : ce sont des adresses à corriger.")
ws.cell(6, 2).font = F(8, False, DOUX, True); ws.cell(6, 2).alignment = ind(0)

for i, h in enumerate(["Gravité", "Onglet", "Cellule", "Recopier\njusqu'à",
                       "Ce qu'il faut mettre", "Ce que ça corrige"]):
    x = ws.cell(8, 2 + i, h); x.font = F(8, True, INK)
    x.alignment = ind(0) if i in (0, 1, 4, 5) else WRAP
    x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
ws.row_dimensions[8].height = 28

COUL = {"1": ROUGE_T, "2": ROUGE_T, "3": OCRE, "4": AZUR, "5": DOUX}
grav = None
for j, (g, onglet, cell, jusqua, contenu, pourquoi) in enumerate(P):
    r = 9 + j
    neuf = g != grav; grav = g
    for c in range(2, NC + 1):
        x = ws.cell(r, c); x.fill = fill(CALC if g[0] in "12" else PANEL)
        x.border = Border(bottom=sd("EDEEF0"), top=sd(FILET) if neuf else None)
    ws.cell(r, 2, g if neuf else "").font = F(7.5, True, COUL[g[0]])
    ws.cell(r, 2).alignment = ind(0)
    for c, v in ((3, onglet), (4, cell), (5, jusqua)):
        x = ws.cell(r, c, v); x.font = F(8, c == 4, INK); x.alignment = ind(0) if c == 3 else Cn
    x = ws.cell(r, 6, contenu); x.data_type = "s"      # une formule MONTREE, pas evaluee
    x.font = MONO(7, INK if contenu.startswith("=") else DOUX); x.alignment = ind(0)
    ws.cell(r, 7, pourquoi).font = F(7.5, False, DOUX, True); ws.cell(r, 7).alignment = ind(0)
    ws.row_dimensions[r].height = 26 if len(pourquoi) > 110 else 15
FIN = 9 + len(P)
for c in range(2, NC + 1):
    ws.cell(FIN + 1, c).fill = fill(PANEL); ws.cell(FIN + 1, c).border = Border(top=sd(AZUR))
    ws.cell(FIN + 2, c).fill = fill(PANEL); ws.cell(FIN + 2, c).border = Border(bottom=sd(AZUR))
ws.cell(FIN + 1, 2, "Après les corrections 1 à 3, le chiffre qui change à l'écran :")
ws.cell(FIN + 1, 2).font = F(9, True, INK); ws.cell(FIN + 1, 2).alignment = ind(0)
ws.cell(FIN + 2, 2, "CA construit 24 154 301 € → 24 231 704 €   ·   EBITDA 4 043 018 € → 4 111 503 €   "
                    "·   objectif 4 095 766 € : « il manque 52 748 € » devient « dépassé de 15 737 € ».")
ws.cell(FIN + 2, 2).font = F(8, False, DOUX, True); ws.cell(FIN + 2, 2).alignment = ind(0)
ws.row_dimensions[FIN + 1].height = 18

# ============================================================================
#  ONGLET 2 — LE BLOC PILOTAGE, REMIS DANS L'ORDRE
#
#  Les colonnes E a I de Pilotage!19:32 sont des valeurs collees, et je ne
#  connais pas leur regle de calcul -- je ne peux donc pas les transformer en
#  formules comme D, K et L. Mais je peux les remettre en face du bon campus :
#  la colonne L, qui portait la vraie cle de chaque ligne, donne la permutation.
# ============================================================================
src = openpyxl.load_workbook(SRC, data_only=True)["Pilotage"]
LIB = [src.cell(r, 1).value for r in range(19, 33)]                  # l'ordre affiche
CLE = {src.cell(r, 12).value: r for r in range(19, 33)}              # la vraie cle -> sa ligne
assert set(LIB) == set(CLE), "la colonne L ne couvre pas les memes campus que la colonne A"

w2 = wb.create_sheet("Bloc Pilotage")
NC2 = 9
w2.sheet_view.showGridLines = False
for r in range(1, 30):
    for c in range(1, NC2 + 1): w2.cell(r, c).fill = fill(FOND)
for r in (1, 2):
    for c in range(1, NC2 + 1): w2.cell(r, c).fill = fill(INK)
for c in range(1, NC2 + 1): w2.cell(3, c).fill = fill(AZUR)
w2.cell(1, 2, "EDUSERVICES · CAD_PIL").font = F(7.5, False, PALE); w2.cell(1, 2).alignment = ind(0)
w2.cell(2, 2, "LE BLOC E19:I32 DE PILOTAGE, REMIS EN FACE DU BON CAMPUS").font = F(14, True, "FFFFFF")
w2.cell(2, 2).alignment = ind(0)
w2.column_dimensions["A"].width = 2.4; w2.column_dimensions["B"].width = 15
for c in range(3, NC2 + 1): w2.column_dimensions[GL(c)].width = 15
for r, h in ((1, 14), (2, 24), (3, 3), (5, 22), (6, 16), (7, 16)): w2.row_dimensions[r].height = h

w2.cell(5, 2, "Sélectionnez D9:H22 ci-dessous, copiez, et collez en Pilotage!E19.").font = F(12, True, INK)
w2.cell(5, 2).alignment = ind(0)
w2.cell(6, 2, "La colonne « Campus » est là pour vérifier, PAS pour être collée : l'ordre est déjà "
              "celui de votre colonne A. Les colonnes D, K et L, elles, deviennent des formules — "
              "voir l'onglet précédent — donc il n'y a que ces cinq colonnes à coller.")
w2.cell(6, 2).font = F(8, False, DOUX, True); w2.cell(6, 2).alignment = ind(0)
w2.cell(7, 2, "Contrôle : la colonne « vient de la ligne » dit d'où chaque valeur a été reprise. "
              "Si elle donne 19 partout, c'est que le fichier était déjà dans l'ordre.")
w2.cell(7, 2).font = F(7.5, False, DOUX, True); w2.cell(7, 2).alignment = ind(0)

TET = ["Campus", "à ne pas coller", "Croiss. leads", "Intensité mkt", "Cap Eff", "Cap mom.",
       "Cap pot.", "vient de\nla ligne"]
for i, h in enumerate(TET):
    x = w2.cell(8, 2 + i, h); x.font = F(8, True, INK if i not in (0, 1, 7) else DOUX)
    x.alignment = WRAP if i else ind(0)
    x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
w2.row_dimensions[8].height = 28
for j, lib in enumerate(LIB):
    r = 9 + j; s = CLE[lib]
    w2.cell(r, 2, lib).font = F(8, True, DOUX); w2.cell(r, 2).alignment = ind(0)
    w2.cell(r, 3, "→").font = F(8, False, DOUX); w2.cell(r, 3).alignment = Cn
    for i, col in enumerate(range(5, 10)):                # E..I de la source
        x = w2.cell(r, 4 + i, src.cell(s, col).value)
        x.fill = fill(VUE); x.font = F(8, False, INK); x.alignment = R
        x.number_format = '0.000000'
        x.border = Border(bottom=sd("EAF0F6"))
    x = w2.cell(r, 9, s); x.font = F(7.5, False, DOUX, True); x.alignment = Cn
    for c in (2, 3, 9): w2.cell(r, c).border = Border(bottom=sd("EDEEF0"))

for w_, coul in ((ws, AZUR), (w2, GRIS)):
    w_.sheet_properties.tabColor = coul
    w_.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    w_.page_setup.orientation = "landscape"; w_.page_setup.paperSize = w_.PAPERSIZE_A4
    w_.page_setup.fitToWidth = 1; w_.page_setup.fitToHeight = 0
    w_.page_margins.left = w_.page_margins.right = 0.4
    w_.oddFooter.left.text = "EDUSERVICES · CAD_PIL · " + w_.title
    w_.oddFooter.left.size = 8; w_.oddFooter.left.font = "Arial"
wb.save(OUT)
print("écrit :", OUT)
print("  %d corrections, dont %d qui faussent un chiffre"
      % (len([x for x in P if x[1] != "—"]), len([x for x in P if x[0][0] in "12"])))
print("  permutation du bloc Pilotage :")
for lib in LIB: print("     %-11s  ←  ligne %d" % (lib, CLE[lib]))
