#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_pilotage_mep.py — l'onglet Pilotage, habille a la charte du Cadrage.

LA GEOMETRIE NE BOUGE PAS. Chaque contenu reste a l'adresse ou il est deja :
le bandeau lignes 1-3, le selecteur ligne 6, la bande de KPI 9-11, le premier
bloc 16-32, le second 36-55. C'est la condition pour qu'un collage special
« formats » tombe juste -- si je reflowais la page, il n'y aurait plus rien a
coller.

LA CHARTE EST RELEVEE SUR LE CADRAGE, pas inventee :

    police        Arial, et rien d'autre  (le Pilotage etait en Aptos Narrow)
    encre         262626      azur  007AC3      gris de note  6B7075
    fonds         feuille F5F6F7   panneau FFFFFF   en-tete et total E7E6E6
    bandeau       deux lignes encre, puis un filet azur de 11,2 points
    titre         Arial 14 gras blanc            KPI  Arial 20
    section       Arial 10 gras                  en-tete de tableau  Arial 7,5 gras
    donnee        Arial 8,5                      total  Arial 9 gras sur gris
    formats       #,##0" €"   ·   0,0%   ·   +0,00%;-0,00%;"—"   ·   0,00

TROIS CHOSES QUE JE CHANGE AU-DELA DE LA FORME, ET JE LES SIGNALE :

  1. le titre passe de G2 a B2, parce que c'est la que le Cadrage le met et
     que la reference, c'est lui ;
  2. les formules corrigees par le patch sont deja en place (J10, D/K/L du
     premier bloc) -- livrer une feuille propre avec des formules fausses
     n'aurait pas de sens ;
  3. les colonnes E a I du premier bloc sont reordonnees, comme dans le patch.

La colonne A reste VISIBLE. Son commentaire disait « COLumn to hide », mais
c'est la cle sur laquelle les deux blocs font leurs SUMIFS : la montrer, c'est
rendre la feuille verifiable. C'est la colonne L, redondante, qui reste masquee.
"""
import openpyxl, warnings
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.utils import get_column_letter as GL
warnings.filterwarnings("ignore")

SRC = "/tmp/claude-0/-home-user-demo5/b8c71a6a-b866-551a-b98b-eceadba2b120/scratchpad/CAD_PIL_nav211.xlsx"
OUT = "PILOTAGE_MEP.xlsx"
#  ---- la charte, relevee cellule par cellule sur l'onglet Cadrage ----------
INK, AZUR, PALE, GRIS = "262626", "007AC3", "A6D0EA", "E7E6E6"
FOND, PANEL, FILET, DOUX = "F5F6F7", "FFFFFF", "D5D7DA", "6B7075"
VERT_T, ROUGE_T = "5F8A17", "C41822"
HM_BAS, HM_MED, HM_HAUT = "F6C9CC", "F7F7F5", "DCEBC0"
UI = "Arial"
F = lambda sz=8.5, b=False, c=INK, i=False: Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd = lambda c=FILET: Side(style="thin", color=c)
R = Alignment("right", vertical="center"); Cn = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)
WRAP = Alignment("center", vertical="bottom", wrap_text=True)
EUR = '#,##0" €";\\-#,##0" €";"–"'
NBR = '#,##0;\\-#,##0;"–"'
PCT = '0.0%;\\-0.0%;"–"'
DEC = '0.00'
FLE = '"▲ "0.0%;"▼ "0.0%;"–"'

src  = openpyxl.load_workbook(SRC)["Pilotage"]
srcv = openpyxl.load_workbook(SRC, data_only=True)["Pilotage"]
LIB = [srcv.cell(r, 1).value for r in range(19, 33)]          # l'ordre affiche, par marque
CLE = {srcv.cell(r, 12).value: r for r in range(19, 33)}      # la vraie cle -> sa ligne source

wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Pilotage"
NC = 12
ws.sheet_view.showGridLines = False
for r in range(1, 60):
    for c in range(1, NC + 2): ws.cell(r, c).fill = fill(FOND)

# ---- 1-3. LE BANDEAU ------------------------------------------------------
for r in (1, 2):
    for c in range(1, NC + 2): ws.cell(r, c).fill = fill(INK)
for c in range(1, NC + 2): ws.cell(3, c).fill = fill(AZUR)
ws.cell(1, 2, "EDUSERVICES · budget 2027 piloté par l'EBITDA").font = F(7.5, False, PALE)
ws.cell(1, 2).alignment = ind(0)
ws.cell(2, 2, "PILOTAGE  ·  le cockpit, campus par campus").font = F(14, True, "FFFFFF")
ws.cell(2, 2).alignment = ind(0)

# ---- 6. LE SCENARIO ACTIF -------------------------------------------------
ws.cell(6, 2, "Scénario actif :").font = F(12, True, INK); ws.cell(6, 2).alignment = ind(0)
s_ = ws.cell(6, 5, "Cadrage"); s_.font = F(10, True, AZUR); s_.fill = fill(PANEL)
s_.alignment = Cn; s_.border = Border(*[sd(AZUR)] * 4)
ws.cell(6, 7, "il commande les deux tableaux ci-dessous").font = F(8, False, DOUX, True)
ws.cell(6, 7).alignment = ind(0)
ws.cell(1, 15, "code scénario ->").font = F(7.5, False, DOUX)
ws.cell(1, 16, '=IF($E$6="Cadrage","V01",IF($E$6="Optimiste","V02","V03"))').font = F(7.5, False, DOUX)

# ---- 8-11. LA BANDE DE KPI ------------------------------------------------
#  Meme motif que le Cadrage : une etiquette sur gris, le nombre en 20 points
#  sur blanc, une note en italique dessous.
KPI = [(2, "CHIFFRE D'AFFAIRES 2027", "=E55", EUR,
        '="contre "&TEXT(Cadrage!$C$12,"#,##0 €")&" en 2026"'),
       (4, "EBITDA APRÈS SIÈGE", "=H55", EUR,
        '="contre "&TEXT(Cadrage!$C$13,"#,##0 €")&" en 2026"'),
       (6, "MARGE D'EBITDA", "=I55", PCT,
        '="contre "&TEXT(Cadrage!$C$14,"0.0%")&" en 2026"'),
       (8, "EFFECTIF", "=D55", NBR,
        '="contre "&TEXT(Cadrage!$C$15,"#,##0")&" en 2026"'),
       (10, "CROISSANCE DU CA", "=IFERROR(E55/Cadrage!$C$12-1,0)", FLE,
        "vs 2026 — la correction du patch")]
for col, lab, f_, nf, note in KPI:
    for c in (col, col + 1):
        ws.cell(8, c).fill = fill(GRIS)
        ws.cell(9, c).fill = fill(GRIS); ws.cell(10, c).fill = fill(PANEL)
        x = ws.cell(11, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    a = ws.cell(9, col, lab); a.font = F(7.5, True, INK); a.alignment = ind(1)
    a.border = Border(bottom=sd(FILET))
    x = ws.cell(10, col, f_); x.font = F(20, False, INK); x.alignment = ind(1); x.number_format = nf
    n = ws.cell(11, col, note); n.font = F(9, False, DOUX, True); n.alignment = ind(1)
ws.cell(10, 10).font = F(20, False, AZUR)

def titre_section(r, num, txt, sous):
    for c in range(1, NC + 2): ws.cell(r, c).fill = fill(FOND)
    ws.cell(r, 2, "%s   %s" % (num, txt)).font = F(10, True, INK)
    ws.cell(r, 2).alignment = ind(0)
    ws.cell(r + 1, 2, sous).font = F(8, False, DOUX, True); ws.cell(r + 1, 2).alignment = ind(0)

def entete(r, libelles):
    for i, h in enumerate(libelles):
        x = ws.cell(r, 1 + i, h); x.font = F(7.5, True, INK); x.fill = fill(GRIS)
        x.alignment = ind(0) if i < 3 else WRAP
        x.border = Border(bottom=sd(INK), top=sd(FILET))

def ligne(r, vals, nfs, fond=PANEL, gras=False, trait="EDEEF0", haut=None):
    for i, (v, nf) in enumerate(zip(vals, nfs)):
        x = ws.cell(r, 1 + i, v); x.fill = fill(fond); x.number_format = nf
        x.font = F(9 if gras else 8.5, gras or i == 0, INK)
        x.alignment = ind(0) if i < 3 else R
        x.border = Border(bottom=sd(trait), top=sd(INK) if haut else None)

# ---- 16-32. BLOC 1 : LE CAP STRATEGIQUE -----------------------------------
titre_section(16, "①", "CAP STRATÉGIQUE PAR CAMPUS",
              "Le cap retenu redistribue le budget d'acquisition entre campus, à enveloppe "
              "constante. Colonnes bleutées : elles viennent de l'onglet Campagne et se "
              "réalignent toutes seules sur le campus.")
ws.cell(15, 1, None)                                   # « COLumn to hide » : vestige, on vide
entete(18, ["Campus", "Marque", "Ville", "CAC marginal", "Croiss. leads", "Intensité mkt",
            "Cap effectif", "Cap moment", "Cap potentiel", "CAP RETENU", "Budget acq. réf.", ""])
NB1 = ['General', 'General', 'General', EUR, PCT, PCT, DEC, DEC, DEC, NBR, EUR, 'General']
for j, lib in enumerate(LIB):
    r, s = 19 + j, CLE[lib]
    #  D, K et L deviennent des formules : un retri ne pourra plus les desaligner.
    #  A, B et C viennent de la ligne d'ETIQUETTE ; seules les mesures D a K
    #  viennent de la ligne source, via la permutation que donne la colonne L.
    ligne(r, [lib, srcv.cell(r, 2).value, srcv.cell(r, 3).value,
              "=SUMIFS(Campagne!$N$2:$N$15,Campagne!$C$2:$C$15,$A%d)" % r,
              srcv.cell(s, 5).value, srcv.cell(s, 6).value,
              srcv.cell(s, 7).value, srcv.cell(s, 8).value, srcv.cell(s, 9).value,
              srcv.cell(s, 10).value,
              "=SUMIFS(Campagne!$G$2:$G$15,Campagne!$C$2:$C$15,$A%d)" % r,
              "=$A%d" % r], NB1)
    for c in (4, 5, 6, 7, 8, 9, 11): ws.cell(r, c).fill = fill("E8F1F9")
    x = ws.cell(r, 10); x.fill = fill("F0EDE4"); x.font = F(9, True, AZUR); x.alignment = Cn
    x.border = Border(*[sd("D8D2C0")] * 4)
ws.cell(33, 2, "La colonne CAP RETENU est la seule saisie de cette feuille. À 1 partout, la "
               "répartition d'origine est conservée.")
ws.cell(33, 2).font = F(8, False, DOUX, True); ws.cell(33, 2).alignment = ind(0)
#  le CAC marginal : le vert va au CAC BAS -- un CAC eleve n'est pas une performance
ws.conditional_formatting.add("D19:D32",
    ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                   mid_color=HM_MED, end_type="max", end_color=HM_BAS))

# ---- 36-55. BLOC 2 : LA SYNTHESE ------------------------------------------
titre_section(36, "②", "SYNTHÈSE PAR CAMPUS  ·  du chiffre d'affaires à l'EBITDA",
              "Tout est calculé : chaque ligne interroge le moteur et le P&L par le nom du "
              "campus. Le sous-total campus, la quote-part du siège, puis le groupe.")
entete(38, ["Campus", "Marque", "Ville", "Effectif", "CA 2027", "Prix moyen", "Part du CA",
            "EBITDA campus", "Marge EBITDA", "EBITDA / étudiant", "Budget rejoué", "CAC marginal"])
NB2 = ['General', 'General', 'General', NBR, EUR, EUR, PCT, EUR, PCT, EUR, EUR, EUR]
for j, lib in enumerate(LIB):
    r = 39 + j
    ligne(r, [lib, srcv.cell(r - 20, 2).value, srcv.cell(r - 20, 3).value,
              "=SUMIFS(Moteur!$P$1:$P$200,Moteur!$D$1:$D$200,$A{0},Moteur!$B$1:$B$200,$P$1)".format(r),
              "=SUMIFS(Moteur!$R$1:$R$200,Moteur!$D$1:$D$200,$A{0},Moteur!$B$1:$B$200,$P$1)".format(r),
              "=IFERROR(E{0}/D{0},0)".format(r), "=IFERROR(E{0}/SUM($E$39:$E$52),0)".format(r),
              "=SUMIFS(_CALC_PNL!$T$1:$T$1347,_CALC_PNL!$A$1:$A$1347,$A{0},"
              "_CALC_PNL!$D$1:$D$1347,$P$1,_CALC_PNL!$C$1:$C$1347,\"2027\")".format(r),
              "=IFERROR(H{0}/E{0},0)".format(r), "=IFERROR(H{0}/D{0},0)".format(r),
              "=SUMIFS(Pilotage!$K$19:$K$32,Pilotage!$A$19:$A$32,$A{0})"
              "*SUMIFS(Pilotage!$J$19:$J$32,Pilotage!$A$19:$A$32,$A{0})"
              "*(SUM(Pilotage!$K$19:$K$32)/SUMPRODUCT(Pilotage!$K$19:$K$32,Pilotage!$J$19:$J$32))".format(r),
              "=SUMIFS(Pilotage!$D$19:$D$32,Pilotage!$A$19:$A$32,$A{0})".format(r)], NB2)
for col, rng in (("I", "I39:I52"), ("J", "J39:J52")):
    ws.conditional_formatting.add(rng,
        ColorScaleRule(start_type="min", start_color=HM_BAS, mid_type="percentile", mid_value=50,
                       mid_color=HM_MED, end_type="max", end_color=HM_HAUT))
TOT = [(53, "Sous-total campus", GRIS, True),
       (54, "Siège / holding (GRP)", PANEL, False),
       (55, "GROUPE 2027", GRIS, True)]
ligne(53, ["Sous-total campus", "", "", "=SUM(D39:D52)", "=SUM(E39:E52)",
           "=IFERROR(E53/D53,0)", "=SUM(G39:G52)", "=SUM(H39:H52)", "=IFERROR(H53/E53,0)",
           "=IFERROR(H53/D53,0)", "=SUM(K39:K52)", ""], NB2, fond=GRIS, gras=True,
      trait=INK, haut=True)
ligne(54, ["Siège / holding (GRP)", "", "", "", "", "", "",
           '=SUMIFS(_CALC_PNL!$T$1:$T$1347,_CALC_PNL!$A$1:$A$1347,"GRP",'
           '_CALC_PNL!$D$1:$D$1347,$P$1,_CALC_PNL!$C$1:$C$1347,"2027")', "", "", "", ""],
      NB2, fond=PANEL, trait="EDEEF0")
ligne(55, ["GROUPE 2027", "", "", "=D53", "=E53", "=IFERROR(E55/D55,0)", "=SUM(G39:G52)",
           "=H53+H54", "=IFERROR(H55/E55,0)", "=IFERROR(H55/D55,0)", "=SUM(K39:K52)", ""],
      NB2, fond=GRIS, gras=True, trait=INK, haut=True)
for c in range(1, NC + 1):
    ws.cell(55, c).font = F(10, True, INK)
ws.cell(55, 8).font = F(10, True, VERT_T)
ws.cell(57, 2, "Lecture : le sous-total campus est l'EBITDA propre, avant que le siège ne soit "
               "réparti. La ligne GRP porte ce que le siège coûte, en négatif. Leur somme est "
               "l'EBITDA du groupe.")
ws.cell(57, 2).font = F(8, False, DOUX, True); ws.cell(57, 2).alignment = ind(0)

# ---- LA GEOMETRIE : largeurs, hauteurs, colonnes techniques ---------------
#  Les hauteurs reprennent celles du Cadrage la ou le motif est le meme :
#  bandeau 14,1 / 46,5 / 11,2 ; bloc de KPI 24 / 33,8 / 16 ; titre 30.
#  Les lignes de donnees passent a 18 -- le Cadrage tient a 22,5 parce qu'il
#  n'a que six leviers ; ici il y en a quatorze, deux fois.
for c, w in ((1, 13), (2, 13.5), (3, 13.5), (4, 13.5), (5, 13.5), (6, 13.5), (7, 12),
             (8, 12), (9, 12), (10, 12), (11, 14), (12, 13.5), (13, 2.6)):
    ws.column_dimensions[GL(c)].width = w
ws.column_dimensions["L"].hidden = True        # redondante avec la colonne A
for c in ("N", "O", "P", "U", "V", "W"):
    ws.column_dimensions[c].hidden = True      # la zone technique
for r, h in ((1, 14.1), (2, 46.5), (3, 11.2), (4, 8), (6, 24), (7, 8),
             (8, 4), (9, 24), (10, 33.8), (11, 16), (12, 8),
             (16, 30), (17, 14), (18, 30), (33, 16),
             (36, 30), (37, 14), (38, 30), (53, 20), (54, 18), (55, 24), (57, 16)):
    ws.row_dimensions[r].height = h
for r in list(range(19, 33)) + list(range(39, 53)): ws.row_dimensions[r].height = 18

ws.freeze_panes = "D19"                        # les trois colonnes d'identite restent a l'ecran
ws.sheet_properties.tabColor = AZUR
ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
ws.page_setup.orientation = "landscape"; ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
ws.print_options.horizontalCentered = True
ws.page_margins.left = ws.page_margins.right = 0.4
ws.oddFooter.left.text = "EDUSERVICES · Pilotage"; ws.oddFooter.left.size = 8
ws.oddFooter.left.font = "Arial"
ws.oddFooter.right.text = "page &P / &N"; ws.oddFooter.right.size = 8
ws.oddFooter.right.font = "Arial"
#  Aucun Calibri ne doit trainer : les cellules de fond que personne n'a
#  touchees portent la police par defaut du classeur.
for row in ws.iter_rows(min_row=1, max_row=60, max_col=14):
    for x in row:
        if x.font.name != UI: x.font = F(8.5, False, INK)
wb.save(OUT)
print("écrit :", OUT)
print("  bandeau 1-3 · scénario 6 · KPI 9-11 · bloc ① 16-32 · bloc ② 36-55")
print("  ordre des campus conservé :", ", ".join(LIB[:4]), "…")
