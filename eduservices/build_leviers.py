#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_leviers.py — deux onglets, deux leviers, la meme chaine.

CE QUE C'EST, ET CE QUE CE N'EST PAS.

Ce n'est pas un moteur de plus. Le moteur est dans CAD_PIL et on n'y touche
pas. Ces deux feuilles sont la LECTURE de ce moteur : on deroule la chaine du
budget a l'EBITDA, une ligne par etape, et a cote de chaque taux on ecrit d'ou
il vient. C'est la piece qui manque pour qu'un CFO cesse de voir une boite
noire -- et c'est la seule chose qu'on montre.

LES DEUX ONGLETS SONT IDENTIQUES A UNE COLONNE PRES. C'est voulu : le CFO lit
le premier en trois minutes, le second en dix secondes, et la comparaison se
fait toute seule dans sa tete.

    payant      budget d'acquisition (6231)  ->  leads PAYANTS
    organique   budget de marque     (6236)  ->  leads ORGANIQUES

    puis le meme entonnoir, les memes taux, le meme CA par inscrit.

LES HUIT SEULES CONSTANTES DE CHAQUE FEUILLE, ET LEUR ORIGINE :

    budget 2026            comptabilite, compte 6231 / 6236
    elasticite             regression log-log sur trois exercices, calculee
                           campus par campus puis ramenee au reseau
    leads 2026             socle CRM
    lead -> candidature    constate 21,2 / 21,4 / 21,6 %   -- stable
    candidature -> admis   constate 70,7 / 70,6 / 70,5 %
    admis -> inscrit       constate 46,7 / 46,8 / 46,9 %
    CA par inscrit         scolarite + frais de dossier, constate
    cout variable / eleve  comptes 604 + 6063

Tout le reste est une formule qui part de LA SEULE CELLULE SAISIE.

DEUX HYPOTHESES, ECRITES SUR LA FEUILLE PARCE QU'ON NE LES CACHE PAS :

  1. L'elasticite du reseau est une elasticite EFFECTIVE, calee sur les
     quatorze elasticites campus. Verifie : l'ecart avec le calcul campus par
     campus reste sous 0,09 % de -10 % a +50 %.
  2. Les trois taux de l'entonnoir sont ceux du reseau, appliques a l'identique
     aux deux sources. Un lead organique convertit peut-etre mieux ; on ne le
     sait pas, donc on ne le suppose pas.

CE QUI N'EST PAS DANS CES FEUILLES, ET IL FAUT LE DIRE SOI-MEME : la CAPACITE.
Le reseau a 351 places libres dans ses cohortes d'entree, pas 974, et MBway
Paris Mastere M1 est plein. Au-dela d'un certain geste il faut ouvrir une
classe. C'est un raccourci de demo, assume.
"""
import csv, math, openpyxl
from collections import defaultdict
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.utils import get_column_letter as GL

OUT = "MOTEUR_LEVIERS.xlsx"
INK, AZUR, ROUGE, VERT = "262626", "007AC3", "E5202E", "85BC20"
PALE, GRIS = "A6D0EA", "E7E6E6"
VERT_T, ROUGE_T, OCRE = "5F8A17", "C41822", "B26B00"
FOND, PANEL, FILET, DOUX = "F5F6F7", "FFFFFF", "D5D7DA", "6B7075"
VUE, CALC, PARM = "E8F1F9", "FDF3E7", "F0EDE4"
UI = "Arial"
F = lambda sz=8, b=False, c=INK, i=False: Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd = lambda c=FILET: Side(style="thin", color=c)
R = Alignment("right", vertical="center"); Cn = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)
WRAP = Alignment("center", vertical="bottom", wrap_text=True)

# ---------------------------------------------------------------- la donnee
num = lambda v: float(v.replace(",", ".")) if v else 0.0
lire = lambda n: list(csv.DictReader(open("data/" + n, encoding="utf-8-sig"), delimiter=";"))
S, C = lire("socle_crm.csv"), lire("compta.csv")
Y = (2024, 2025, 2026)
v = defaultdict(lambda: defaultdict(float)); g = defaultdict(lambda: defaultdict(float))
for r in S:
    y = int(r["EXERCICE"]); d = v[(r["ENTITY"], y)]
    for a, b in (("pay", "VOL_LEAD_PAY"), ("org", "VOL_LEAD_ORG"), ("acq", "DEPENSE_ACQ"),
                 ("mrq", "DEPENSE_MARQUE")): d[a] += num(r[b])
    for k in ("VOL_LEAD_PAY", "VOL_LEAD_ORG", "VOL_CAND", "VOL_ADMIS", "VOL_NEW", "VOL_EFF"):
        g[y][k] += num(r[k])
    g[y]["CA"] += num(r["VOL_NEW"]) * (num(r["REV_STUD"]) + num(r["REV_FRAIS_INS"]))
ENTS = sorted({e for e, _ in v})
def pente(xs, ys):
    n = len(xs)
    return (n*sum(a*b for a, b in zip(xs, ys)) - sum(xs)*sum(ys)) / (n*sum(a*a for a in xs) - sum(xs)**2)
def elast(cle, bud):
    """L'elasticite EFFECTIVE du reseau : on calcule les quatorze, on applique
    un +8 % a chacune, et on cherche la pente unique qui redonne le meme total.
    Ce n'est pas une moyenne de pentes -- une pente ne se moyenne pas."""
    EL = {e: pente([math.log(v[(e, y)][bud]) for y in Y], [math.log(v[(e, y)][cle]) for y in Y])
          for e in ENTS}
    L0 = sum(v[(e, 2026)][cle] for e in ENTS)
    dl = sum(v[(e, 2026)][cle] * (1.08 ** EL[e] - 1) for e in ENTS)
    return math.log(1 + dl / L0) / math.log(1.08), min(EL.values()), max(EL.values())
K = defaultdict(float)
for r in C:
    if r["EXERCICE"] == "2026": K[r["ACCOUNT"]] += num(r["AMOUNT"])
TOT = g[2026]["VOL_LEAD_PAY"] + g[2026]["VOL_LEAD_ORG"]
R_LC = g[2026]["VOL_CAND"] / TOT
R_CA = g[2026]["VOL_ADMIS"] / g[2026]["VOL_CAND"]
R_AI = g[2026]["VOL_NEW"] / g[2026]["VOL_ADMIS"]
CAI = g[2026]["CA"] / g[2026]["VOL_NEW"]
CONSO = (K["604"] + K["6063"]) / g[2026]["VOL_EFF"]
SUITE = lambda k: "  ·  ".join(("%.1f %%" % (100 * g[y][k] / (g[y]["VOL_LEAD_PAY"] + g[y]["VOL_LEAD_ORG"])))
                               .replace(".", ",") for y in Y)

# ============================================================================
#  UNE SEULE FONCTION POUR LES DEUX ONGLETS
#
#  Ils doivent etre identiques a la ligne pres : c'est ce qui rend la
#  comparaison immediate. Les ecrire deux fois, c'est se garantir qu'ils
#  finiront par diverger.
# ============================================================================
wb = openpyxl.Workbook(); wb.remove(wb.active)
NC = 7                                    # B..G

def feuille(titre_, sous_, budget, elas, leads, lab_bud, lab_lead, cpte, src_el, couleur):
    w = wb.create_sheet(titre_)
    w.sheet_view.showGridLines = False
    for r in range(1, 44):
        for c in range(1, NC + 1): w.cell(r, c).fill = fill(FOND)
    for r in (1, 2):
        for c in range(1, NC + 1): w.cell(r, c).fill = fill(INK)
    for c in range(1, NC + 1): w.cell(3, c).fill = fill(AZUR)
    w.cell(1, 2, "EDUSERVICES · comment le budget marketing devient de l'EBITDA").font = F(7.5, False, PALE)
    w.cell(1, 2).alignment = ind(0)
    w.cell(2, 2, titre_.upper() + "  —  du budget à l'EBITDA, étape par étape").font = F(14, True, "FFFFFF")
    w.cell(2, 2).alignment = ind(0)
    w.column_dimensions["A"].width = 2.4; w.column_dimensions["B"].width = 38
    for c, wd in ((3, 16), (4, 14), (5, 16), (6, 15), (7, 52)): w.column_dimensions[GL(c)].width = wd
    for r, h in ((1, 14), (2, 24), (3, 3), (5, 22), (6, 16), (8, 3), (9, 30), (10, 14)):
        w.row_dimensions[r].height = h

    w.cell(5, 2, sous_).font = F(12, True, INK); w.cell(5, 2).alignment = ind(0)
    w.cell(6, 2, "Chaque ligne dit d'où elle vient. Rien n'est posé : les huit chiffres en bleu sont "
                 "constatés dans la base, tout le reste est une formule qui part de la seule cellule "
                 "que vous changez.")
    w.cell(6, 2).font = F(8, False, DOUX, True); w.cell(6, 2).alignment = ind(0)

    # ---- la saisie, seule et grande ---------------------------------------
    for c in range(2, NC + 1):
        w.cell(8, c).fill = fill(couleur)
        w.cell(9, c).fill = fill(PANEL)
        x = w.cell(10, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    w.cell(9, 2, lab_bud.upper()).font = F(9, True, INK); w.cell(9, 2).alignment = ind(1)
    s_ = w.cell(9, 3, 0.08); s_.fill = fill(PARM); s_.font = F(18, True, couleur); s_.alignment = Cn
    s_.border = Border(*[sd(couleur)] * 4); s_.number_format = '+0.0%;-0.0%;"—"'
    w.cell(9, 5, "la seule cellule à saisir").font = F(8, False, DOUX, True)
    w.cell(9, 5).alignment = ind(0)
    w.cell(10, 2, "Tournez ce curseur et regardez les quinze lignes du dessous bouger ensemble.")
    w.cell(10, 2).font = F(7.5, False, DOUX, True); w.cell(10, 2).alignment = ind(0)

    # ---- la chaine ---------------------------------------------------------
    w.cell(12, 2, "LA CHAÎNE, ÉTAPE PAR ÉTAPE").font = F(10, True, AZUR)
    w.cell(12, 2).alignment = ind(0); w.row_dimensions[12].height = 20
    w.cell(13, 2, "Un étage sur deux est un TAUX : c'est là que le modèle fait une hypothèse, et "
                  "c'est là qu'on peut le contredire. Les étages entre les deux ne sont que des "
                  "multiplications.")
    w.cell(13, 2).font = F(7.5, False, DOUX, True); w.cell(13, 2).alignment = ind(0)
    w.row_dimensions[13].height = 14
    for i, h in enumerate(["Étape", "2026 constaté", "Taux appliqué", "2027 simulé", "Écart",
                           "D'où vient ce chiffre"]):
        x = w.cell(15, 2 + i, h); x.font = F(8, True, INK)
        x.alignment = ind(0) if i in (0, 5) else WRAP
        x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
    w.row_dimensions[15].height = 28

    #  (libelle, 2026, taux, 2027, format, source, gras)
    CH = [
      (lab_bud, budget, "=$C$9", "=C16*(1+D16)", '#,##0" €"',
       "comptabilité, compte %s  ·  votre décision, c'est le taux" % cpte, True),
      ("      × élasticité", None, elas, None, '0.000',
       src_el, False),
      (lab_lead, leads, None, "=C18*(1+D16)^D17", '#,##0',
       "socle CRM  ·  ce que le budget achète", True),
      ("      × taux lead → candidature", None, R_LC, None, '0.0%',
       "constaté  " + SUITE("VOL_CAND") + "  ·  stable", False),
      ("Candidatures", "=C18*D19", None, "=E18*D19", '#,##0', "", False),
      ("      × taux candidature → admis", None, R_CA, None, '0.0%',
       "constaté  70,7 %  ·  70,6 %  ·  70,5 %  ·  la sélection ne bouge pas", False),
      ("Admis", "=C20*D21", None, "=E20*D21", '#,##0', "", False),
      ("      × taux admis → inscrit", None, R_AI, None, '0.0%',
       "constaté  46,7 %  ·  46,8 %  ·  46,9 %  ·  le levier le plus contestable", False),
      ("Nouveaux inscrits", "=C22*D23", None, "=E22*D23", '#,##0.0', "", True),
      ("      × chiffre d'affaires par inscrit", None, CAI, None, '#,##0" €"',
       "scolarité + frais de dossier, constaté 2026", False),
      ("Chiffre d'affaires", "=C24*D25", None, "=E24*D25", '#,##0" €"', "", True),
    ]
    #  Trois natures de ligne, et le fond le dit :
    #     un TAUX seul            fond blanc, la valeur encadrée en ocre
    #     un VOLUME calculé       fond ocre  -- il sort d'une multiplication
    #     un VOLUME constaté      fond bleu  -- il vient de la base
    for j, (lab, c26, tx, c27, nf, src, gras) in enumerate(CH):
        r = 16 + j; stock = c26 is not None or c27 is not None
        for c in range(2, NC + 1):
            x = w.cell(r, c); x.fill = fill(VUE if gras else (CALC if stock else PANEL))
            x.border = Border(bottom=sd("EDEEF0"))
        w.cell(r, 2, lab).font = F(8.5 if gras else 8, gras, INK if stock else DOUX)
        w.cell(r, 2).alignment = ind(0)
        if tx is not None:
            x = w.cell(r, 4, tx); x.number_format = nf if not stock else '+0.0%;-0.0%;"—"'
            x.alignment = Cn; x.font = F(9, True, OCRE)
            x.fill = fill(PARM); x.border = Border(*[sd("D8D2C0")] * 4)
        if stock:
            for col, val in ((3, c26), (5, c27)):
                x = w.cell(r, col, val); x.number_format = nf; x.alignment = R
                x.font = F(9 if gras else 8, gras, INK)
            x = w.cell(r, 6, "=E{0}-C{0}".format(r)); x.number_format = "+" + nf + ";-" + nf
            x.alignment = R; x.font = F(9 if gras else 8, True, couleur)
        w.cell(r, 7, src).font = F(7.5, False, DOUX, True); w.cell(r, 7).alignment = ind(0)
    return w, 16 + len(CH) - 1          # la derniere ligne : le chiffre d'affaires

def resultat(w, rca, couleur, reserve, cpte):
    """Le compte de resultat du geste : quatre nombres, et le rendement.
    On ne remonte pas au CA total -- ce qui interesse un DAF, c'est ce que le
    geste AJOUTE, et ce qu'il faut mettre en face pour le servir."""
    r0 = rca + 2
    w.cell(r0, 2, "CE QUE LE GESTE RAPPORTE, UNE FOIS TOUT PAYÉ").font = F(10, True, couleur)
    w.cell(r0, 2).alignment = ind(0); w.row_dimensions[r0].height = 20
    #  Le coût variable par élève est le seul chiffre neuf de ce bloc : on le
    #  POSE dans la colonne des taux, visible, plutôt que de l'enterrer dans
    #  une formule.
    LIG = [("Chiffre d'affaires gagné", None, "=F%d" % rca, '#,##0" €"', INK,
            "les inscrits gagnés × le CA par inscrit", False),
           ("−  coût variable de les servir", CONSO, "=-F{0}*D{1}".format(rca - 2, r0 + 2),
            '#,##0" €"', ROUGE_T,
            "comptes 604 + 6063 : licences, fournitures, supports — par élève", False),
           ("−  budget supplémentaire", None, "=-F16", '#,##0" €"', ROUGE_T,
            "le compte %s, augmenté du taux saisi" % cpte, False),
           ("=  EBITDA GAGNÉ", None, "=SUM(F{0}:F{1})".format(r0 + 1, r0 + 3), '#,##0" €"', VERT_T,
            "première année, à capacité constante", True),
           ("PAR EURO INVESTI", None, "=IFERROR(F{0}/-F{1},0)".format(r0 + 4, r0 + 3), '0.00" €"',
            couleur, "d'EBITDA pour un euro mis dans ce levier", True)]
    for j, (lab, tx, f_, nf, coul, src, gras) in enumerate(LIG):
        r = r0 + 1 + j
        for c in range(2, NC + 1):
            x = w.cell(r, c); x.fill = fill(GRIS if gras else PANEL)
            x.border = Border(bottom=sd(INK if gras else "EDEEF0"))
        w.cell(r, 2, lab).font = F(10 if gras else 8.5, gras, INK); w.cell(r, 2).alignment = ind(0)
        if tx is not None:
            x = w.cell(r, 4, tx); x.number_format = '#,##0" €"'; x.alignment = Cn
            x.font = F(9, True, OCRE); x.fill = fill(PARM); x.border = Border(*[sd("D8D2C0")] * 4)
        x = w.cell(r, 6, f_); x.number_format = nf; x.alignment = R
        x.font = F(13 if gras else 9, gras, coul)
        w.cell(r, 7, src).font = F(7.5, False, DOUX, True); w.cell(r, 7).alignment = ind(0)
    #  Les deux notes tiennent sur des lignes SEPAREES : un paragraphe de trois
    #  cents signes dans une seule cellule deborde hors du panneau.
    rf = r0 + 6
    NOTE = [(reserve, F(8.5, True, INK)),
            ("Ce qui n'est pas dans cette feuille, et il faut le dire soi-même : la CAPACITÉ.",
             F(7.5, True, DOUX)),
            ("Le réseau a 351 places libres dans ses cohortes d'entrée — pas 974 — et MBway Paris "
             "Mastère M1 est déjà plein. Au-delà d'un certain geste il faut ouvrir une classe, et un "
             "vacataire avec. Raccourci de démonstration, assumé.", F(7.5, False, DOUX, True))]
    for j, (txt, ft) in enumerate(NOTE):
        r = rf + j
        for c in range(2, NC + 1):
            x = w.cell(r, c); x.fill = fill(PANEL)
            if j == 0: x.border = Border(top=sd(AZUR))
            if j == len(NOTE) - 1: x.border = Border(bottom=sd(AZUR))
        w.cell(r, 2, txt).font = ft; w.cell(r, 2).alignment = ind(0)
    w.row_dimensions[rf].height = 18
    # la finition : ces feuilles se projettent et s'impriment
    w.sheet_properties.tabColor = couleur
    w.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    w.page_setup.orientation = "landscape"; w.page_setup.paperSize = w.PAPERSIZE_A4
    w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 0
    w.print_options.horizontalCentered = True
    w.page_margins.left = w.page_margins.right = 0.4
    w.oddFooter.left.text = "EDUSERVICES · " + w.title; w.oddFooter.left.size = 8
    w.oddFooter.left.font = "Arial"
    w.oddFooter.right.text = "page &P / &N"; w.oddFooter.right.size = 8
    w.oddFooter.right.font = "Arial"

EP, epmin, epmax = elast("pay", "acq")
EO, eomin, eomax = elast("org", "mrq")
w1, r1 = feuille(
    "Le levier payant",
    "Je mets un euro de plus en acquisition. Qu'est-ce qu'il devient ?",
    K["6231"], EP, g[2026]["VOL_LEAD_PAY"], "Budget d'acquisition", "Leads payants", "6231",
    "régression log-log sur trois exercices, faite campus par campus (%.2f à %.2f) "
    "puis ramenée au réseau" % (epmin, epmax), AZUR)
resultat(w1, r1, AZUR,
         "L'euro d'acquisition est le levier COURT : il achète un lead aujourd'hui, "
         "qui devient un inscrit cette année.", "6231")
w2, r2 = feuille(
    "Le levier organique",
    "Je mets un euro de plus en marque. Qu'est-ce qu'il devient ?",
    K["6236"], EO, g[2026]["VOL_LEAD_ORG"], "Budget de marque", "Leads organiques", "6236",
    "même régression, côté marque, campus par campus (%.2f à %.2f) "
    "puis ramenée au réseau" % (eomin, eomax), OCRE)
resultat(w2, r2, OCRE,
         "ATTENTION : ce chiffre dit ce que l'euro de marque rapporte EN 2027. "
         "Une régression sur trois ans ne capte que l'effet de l'année.", "6236")
wb.save(OUT)
print("écrit :", OUT)
print("  entonnoir  lead→cand %.2f%%  cand→admis %.2f%%  admis→inscrit %.2f%%" % (100*R_LC, 100*R_CA, 100*R_AI))
print("  élasticité payante %.4f (%.3f–%.3f)  ·  organique %.4f (%.3f–%.3f)"
      % (EP, epmin, epmax, EO, eomin, eomax))
print("  CA par inscrit %.0f €  ·  coût variable %.0f €/élève" % (CAI, CONSO))
