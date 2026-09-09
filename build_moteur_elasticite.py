#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_moteur_elasticite.py — le moteur raconte, en une seule relation.

CE QUI CHANGE PAR RAPPORT A MOTEUR_MASQUE. Le moteur de production garde ses
deux elasticites -- budget d'acquisition vers leads payants, budget de marque
vers leads organiques -- puis son entonnoir. C'est juste, c'est verifie, et
c'est illisible pour qui n'a pas trente minutes.

Ce classeur-ci raconte la MEME projection avec UNE relation, celle que le
directeur financier peut verifier lui-meme sur ses propres comptes :

    inscrits N = inscrits N-1 x ( budget marketing N / budget N-1 ) ^ epsilon

L'entonnoir n'a pas disparu, il est A L'INTERIEUR de l'elasticite. C'est
d'ailleurs pour ca qu'on ne remultiplie surtout pas par un taux de conversion :
il serait compte deux fois.

POURQUOI ON PEUT SE PERMETTRE CETTE SIMPLIFICATION, ET C'EST UN CONSTAT, PAS
UNE HYPOTHESE. Sur les trois exercices, le taux lead vers inscrit est passe de
7,135 % a 7,147 %. Sur les 137 inscrits gagnes, 98,5 % viennent du VOLUME de
leads et 1,5 % de la conversion. Le funnel n'a pas bouge : le tenir constant
n'invente rien, ca decrit ce qui s'est passe.

CE QUE L'ELASTICITE SERT A PRODUIRE, et c'est la seule chose qui interesse un
CFO en seance budgetaire : la table qui relie un objectif d'inscrits a un
budget. +10 % d'inscrits demandent +23 % de budget marketing. Voila un
rendement de 0,46, dit dans la langue de celui qui signe.

LA PREUVE. On cale l'elasticite sur 2024-2025 SEULEMENT, on lui donne le budget
2026 et on regarde ce qu'elle rend : 1 232 inscrits contre 1 229 constates,
+0,25 %. Par campus, ecart moyen 1,06 %, maximum 2,28 %. Hors echantillon.

Grain : campus, regroupes par marque -- l'elasticite se mesure la ou le budget
se decide. La valeur groupe (0,460) n'est qu'un reperage.

Charte identique a MOTEUR_MASQUE : fond blanc, encre 262626, azur 007AC3.
"""
import math, warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as GL

warnings.filterwarnings("ignore")
OUT = "/home/user/demo5/eduservices/MOTEUR_ELASTICITE.xlsx"

INK, AZUR, ROUGE, VERT = "262626", "007AC3", "E5202E", "85BC20"
GRIS, CIEL, JAUNE = "E7E6E6", "E8F1F9", "FFF2CC"
PANEL, FILET, DOUX, OCRE = "FFFFFF", "D5D7DA", "6B7075", "B26B00"
VERT_T, ROUGE_T = "5F8A17", "C41822"
UI = "Arial"
F = lambda sz=8.5, b=False, c=INK, i=False: Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd = lambda c=FILET, st="thin": Side(style=st, color=c)
R_ = Alignment("right", vertical="center")
C_ = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)
WR = Alignment("center", vertical="center", wrap_text=True)
WL = Alignment("left", vertical="top", wrap_text=True)

EUR = '#,##0" €"'
PCT = '+0.0%;-0.0%;"—"'
PC2 = '0.00%'
NB  = '#,##0'
NB1 = '#,##0.0'
EL  = '0.000'

exec(open("/tmp/claude-0/-home-user-demo5/b8c71a6a-b866-551a-b98b-eceadba2b120/scratchpad/snap_el.txt",
          encoding="utf-8").read())

# ---------------------------------------------------------------- la mesure
def pente(xs, ys):
    n = len(xs); mx, my = sum(xs)/n, sum(ys)/n
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)

def eps(bud, ins):
    return pente([math.log(b) for b in bud], [math.log(i) for i in ins])

LIG = []
for (code, marque, ville, b24, b25, b26, i24, i25, i26, ca) in CAMPUS:
    e3 = eps((b24, b25, b26), (i24, i25, i26))
    e2 = eps((b24, b25), (i24, i25))                 # cale hors 2026
    pred = i25 * (b26 / b25) ** e2
    LIG.append(dict(code=code, marque=marque, ville=ville, b=(b24, b25, b26),
                    i=(i24, i25, i26), ca=ca, e3=e3, e2=e2, pred=pred,
                    ecart=pred / i26 - 1))
MARQUES = []
for m in sorted({l["marque"] for l in LIG}, key=lambda x: [l["marque"] for l in LIG].index(x)):
    s = [l for l in LIG if l["marque"] == m]
    MARQUES.append(dict(nom=m, lignes=s,
                        b=tuple(sum(l["b"][k] for l in s) for k in range(3)),
                        i=tuple(sum(l["i"][k] for l in s) for k in range(3))))
for m in MARQUES:
    m["e3"] = eps(m["b"], m["i"])
BG = tuple(sum(l["b"][k] for l in LIG) for k in range(3))
IG = tuple(sum(l["i"][k] for l in LIG) for k in range(3))
EG = eps(BG, IG)
CAG = sum(l["ca"] for l in LIG)

wb = openpyxl.Workbook()

def feuille(nom, larg):
    ws = wb.create_sheet(nom)
    ws.sheet_view.showGridLines = False
    for c, w in larg.items():
        ws.column_dimensions[c].width = w
    return ws

def bandeau(ws, titre, sous, nc):
    ws.row_dimensions[1].height = 26
    for c in range(1, nc + 1):
        x = ws.cell(1, c); x.fill = fill(AZUR)
    x = ws.cell(1, 2, titre); x.font = F(13, True, PANEL); x.alignment = ind(0); x.fill = fill(AZUR)
    x = ws.cell(2, 2, sous); x.font = F(8.5, False, DOUX); x.alignment = ind(0)

def titre(ws, r, txt, c1=2, c2=None):
    x = ws.cell(r, c1, txt); x.font = F(9, True, AZUR); x.alignment = ind(0)
    for c in range(c1, (c2 or c1) + 1):
        ws.cell(r, c).border = Border(bottom=sd(AZUR))

def entete(ws, r, cols, h=28):
    ws.row_dimensions[r].height = h
    for c, lab, al in cols:
        x = ws.cell(r, c, lab); x.font = F(8, True, PANEL); x.fill = fill(AZUR)
        x.alignment = al; x.border = Border(bottom=sd(INK))

def po(ws, r, c, v=None, f=None, nf=None, al=None, fl=None, bd=None):
    x = ws.cell(r, c, v)
    x.font = f or F()
    if nf: x.number_format = nf
    if al: x.alignment = al
    if fl: x.fill = fill(fl)
    if bd: x.border = bd
    return x

# =============================================================================
#  1. LA METHODE — le recit, sans un seul tableau
# =============================================================================
w1 = feuille("La méthode", {"A": 1.8, "B": 4, "C": 26, "D": 96, "E": 2})
bandeau(w1, "COMMENT LA PROJECTION EST CONSTRUITE",
        "Une seule relation, mesurée sur trois exercices — et ce qu'elle permet de dire", 5)

TEMPS = [
 ("1", "On ne prévoit pas,\non construit",
  "Personne ne devine le nombre d'inscrits de 2027. On part de 2026, et on applique ce que "
  "l'historique a mesuré. Deux entrées seulement : le budget marketing, décidé au siège, et les "
  "effectifs déjà inscrits, qui poursuivent leur cursus."),
 ("2", "Ce que dit l'historique :\nune élasticité",
  "Sur 2024-2026, le budget marketing a crû de +13,7 % par an, les inscrits de +6,1 %. Le rapport "
  "de ces deux croissances, mesuré en logarithmes, vaut 0,46 au niveau du groupe. Autrement dit : "
  "+1 % de budget donne +0,46 % d'inscrits. Ce n'est pas une hypothèse posée, c'est une pente "
  "relevée sur les comptes."),
 ("3", "Pourquoi ce rendement\ndécroît",
  "Parce qu'on n'achète pas des inscrits : on achète de l'audience, sur un marché fini, par "
  "enchères. Les contacts les moins chers sont pris en premier ; l'euro suivant va chercher des "
  "audiences plus larges, moins qualifiées, et plus disputées. Le volume continue de monter, "
  "simplement moins vite que la dépense."),
 ("4", "Ce qu'on n'a PAS eu\nà supposer",
  "Le taux de transformation d'un contact en inscrit est passé de 7,135 % à 7,147 % en trois ans. "
  "Sur les 137 inscrits gagnés, 98,5 % viennent du volume de contacts et 1,5 % de la "
  "transformation. Le tenir constant ne relève d'aucune hypothèse : c'est ce que montre "
  "l'historique. Et c'est pour cela qu'il ne faut surtout pas le remultiplier — il est déjà "
  "contenu dans l'élasticité."),
 ("5", "Ce que ça permet\nde dire",
  "La relation se lit dans les deux sens. Du budget vers les inscrits pour construire le "
  "budget 2027 ; des inscrits vers le budget pour répondre à la seule question qui se pose en "
  "séance : « il faut combien pour tenir l'objectif ? »"),
 ("6", "Puis la mécanique,\nqui ne se discute pas",
  "Les inscrits entrent en première année. Les autres années viennent des cohortes déjà là, "
  "multipliées par le taux de passage. L'effectif total rencontre le tarif, et donne le chiffre "
  "d'affaires. Aucune élasticité là-dedans, que de l'arithmétique."),
 ("7", "Et la preuve",
  "On cale l'élasticité sur 2024 et 2025 uniquement. On lui donne le budget 2026, qu'elle n'a "
  "jamais vu. Elle rend 1 232 inscrits ; il y en a eu 1 229. Écart : +0,25 %. Par campus, écart "
  "moyen 1,06 %, maximum 2,28 %."),
]
r = 4
for num, tit, txt in TEMPS:
    x = po(w1, r, 2, num, f=F(14, True, AZUR), al=C_)
    po(w1, r, 3, tit, f=F(10, True, INK), al=WL)
    po(w1, r, 4, txt, f=F(9), al=WL)
    #  la hauteur suit la longueur : colonne D large de 96 caracteres, 9 pt
    w1.row_dimensions[r].height = max(46, math.ceil(len(txt) / 92) * 12 + 14)
    for c in range(2, 5):
        w1.cell(r, c).border = Border(bottom=sd(GRIS))
    r += 1

r += 1
titre(w1, r, "LA RELATION, ÉCRITE EN ENTIER", 2, 4)
r += 1
w1.row_dimensions[r].height = 22
po(w1, r, 3, "inscrits 2027", f=F(11, True, INK), al=R_)
po(w1, r, 4, "=  inscrits 2026  ×  ( budget marketing 2027 ÷ budget marketing 2026 ) ^ 0,46",
   f=F(11, True, AZUR), al=ind(1))
r += 1
po(w1, r, 4, "et rien d'autre : le taux de transformation est déjà dans l'exposant.",
   f=F(8.5, False, DOUX, True), al=ind(1))

# =============================================================================
#  2. CE QUE DIT L'HISTORIQUE — l'elasticite par campus, groupee par marque
# =============================================================================
w2 = feuille("Ce que dit l'historique",
             {"A": 1.8, "B": 22, "C": 14, "D": 12, "E": 12, "F": 12, "G": 3,
              "H": 10, "I": 10, "J": 10, "K": 3, "L": 12, "M": 12, "N": 13, "O": 2})
bandeau(w2, "CE QUE DIT L'HISTORIQUE",
        "Trois exercices, deux colonnes, une pente — mesurée là où le budget se décide", 15)
po(w2, 3, 2, "L'élasticité est la pente de ln(inscrits) sur ln(budget marketing). "
             "Elle se mesure par campus, parce que c'est là que le marché est.",
   f=F(8.5, False, DOUX, True), al=ind(0))

RH = 5
entete(w2, RH, [(2, "Marque · Campus", ind(1)), (3, "", C_),
                (4, "Budget 2024", WR), (5, "Budget 2025", WR), (6, "Budget 2026", WR),
                (8, "Inscrits\n2024", WR), (9, "Inscrits\n2025", WR), (10, "Inscrits\n2026", WR),
                (12, "Budget\npar an", WR), (13, "Inscrits\npar an", WR),
                (14, "ÉLASTICITÉ", WR)])
for c in (7, 11):
    w2.cell(RH, c).fill = fill(AZUR)

r = RH + 1
for m in MARQUES:
    po(w2, r, 2, m["nom"], f=F(9.5, True, AZUR), al=ind(0), fl=CIEL)
    for c in range(2, 15):
        w2.cell(r, c).fill = fill(CIEL)
        w2.cell(r, c).border = Border(top=sd(FILET), bottom=sd(FILET))
    for k, c in ((0, 4), (1, 5), (2, 6)):
        po(w2, r, c, m["b"][k], f=F(9, True), nf=EUR, al=R_, fl=CIEL)
    for k, c in ((0, 8), (1, 9), (2, 10)):
        po(w2, r, c, m["i"][k], f=F(9, True), nf=NB, al=R_, fl=CIEL)
    po(w2, r, 12, (m["b"][2]/m["b"][0])**.5 - 1, f=F(9, True), nf=PCT, al=R_, fl=CIEL)
    po(w2, r, 13, (m["i"][2]/m["i"][0])**.5 - 1, f=F(9, True), nf=PCT, al=R_, fl=CIEL)
    po(w2, r, 14, m["e3"], f=F(10, True, AZUR), nf=EL, al=C_, fl=CIEL)
    r += 1
    for l in m["lignes"]:
        po(w2, r, 2, l["ville"], al=ind(3))
        for k, c in ((0, 4), (1, 5), (2, 6)):
            po(w2, r, c, l["b"][k], nf=EUR, al=R_)
        for k, c in ((0, 8), (1, 9), (2, 10)):
            po(w2, r, c, l["i"][k], nf=NB, al=R_)
        po(w2, r, 12, (l["b"][2]/l["b"][0])**.5 - 1, nf=PCT, al=R_)
        po(w2, r, 13, (l["i"][2]/l["i"][0])**.5 - 1, nf=PCT, al=R_)
        po(w2, r, 14, l["e3"], f=F(9, True), nf=EL, al=C_)
        for c in range(2, 15):
            w2.cell(r, c).border = Border(bottom=sd(GRIS))
        r += 1

RT = r
po(w2, RT, 2, "GROUPE", f=F(10, True), al=ind(1))
for k, c in ((0, 4), (1, 5), (2, 6)):
    po(w2, RT, c, BG[k], f=F(10, True), nf=EUR, al=R_)
for k, c in ((0, 8), (1, 9), (2, 10)):
    po(w2, RT, c, IG[k], f=F(10, True), nf=NB, al=R_)
po(w2, RT, 12, (BG[2]/BG[0])**.5 - 1, f=F(10, True), nf=PCT, al=R_)
po(w2, RT, 13, (IG[2]/IG[0])**.5 - 1, f=F(10, True), nf=PCT, al=R_)
po(w2, RT, 14, EG, f=F(12, True, AZUR), nf=EL, al=C_)
for c in range(2, 15):
    w2.cell(RT, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))

r = RT + 2
po(w2, r, 2, "Comment la lire", f=F(9, True, AZUR), al=ind(0))
for c in range(2, 15):
    w2.cell(r, c).border = Border(bottom=sd(AZUR))
LECT = [
 "Une élasticité de %.2f veut dire : +1 %% de budget marketing donne +%.2f %% d'inscrits." % (EG, EG),
 "Elle est INFÉRIEURE À 1 partout : le volume monte toujours, mais moins vite que la dépense. "
 "C'est le rendement décroissant, et il se mesure.",
 "Elle varie de %.2f à %.2f selon le campus. Les marchés les plus disputés sont ceux où le "
 "prochain euro travaille le moins." % (min(l["e3"] for l in LIG), max(l["e3"] for l in LIG)),
 "La valeur groupe de %.2f n'est qu'un repère : un budget se décide campus par campus." % EG,
 "Une élasticité ne se moyenne pas. Celle d'une marque n'est pas la moyenne de ses campus : elle est "
 "recalculée sur le budget et les inscrits de la marque entière, exactement comme un indice base 100.",
]
for i, t in enumerate(LECT):
    po(w2, r + 1 + i, 2, t, f=F(8.5, False, DOUX), al=ind(0))

# =============================================================================
#  3. BUDGET <-> INSCRITS — la table que l'elasticite sert a produire
# =============================================================================
w3 = feuille("Budget ↔ inscrits",
             {"A": 1.8, "B": 24, "C": 15, "D": 15, "E": 13, "F": 3,
              "G": 24, "H": 15, "I": 15, "J": 13, "K": 2})
bandeau(w3, "COMBIEN DE BUDGET POUR COMBIEN D'INSCRITS",
        "La même relation, lue dans les deux sens — c'est la question qui se pose en séance", 11)

titre(w3, 4, "JE VEUX TANT D'INSCRITS — IL ME FAUT COMBIEN ?", 2, 5)
entete(w3, 5, [(2, "Objectif", ind(1)), (3, "Inscrits visés", WR),
               (4, "Budget marketing requis", WR), (5, "Soit", WR)], 26)
r = 6
for x in (0.03, 0.05, 0.10, 0.15, 0.20):
    ratio = (1 + x) ** (1 / EG)
    gras = abs(x - 0.10) < 1e-9
    po(w3, r, 2, "+%.0f %% d'inscrits" % (100*x), f=F(9, gras), al=ind(1))
    po(w3, r, 3, IG[2]*(1+x), f=F(9, gras), nf=NB, al=R_)
    po(w3, r, 4, BG[2]*ratio, f=F(9, gras), nf=EUR, al=R_)
    po(w3, r, 5, ratio-1, f=F(10, True, AZUR) if gras else F(9), nf=PCT, al=R_)
    for c in range(2, 6):
        w3.cell(r, c).border = Border(bottom=sd(GRIS))
        if gras: w3.cell(r, c).fill = fill(CIEL)
    r += 1
po(w3, r, 2, "budget 2026 de référence", f=F(8.5, False, DOUX, True), al=ind(1))
po(w3, r, 3, IG[2], f=F(8.5, False, DOUX), nf=NB, al=R_)
po(w3, r, 4, BG[2], f=F(8.5, False, DOUX), nf=EUR, al=R_)
for c in range(2, 6):
    w3.cell(r, c).border = Border(top=sd(INK))

titre(w3, 4, "JE METS TANT DE BUDGET — J'OBTIENS QUOI ?", 7, 10)
entete(w3, 5, [(7, "Budget en plus", ind(1)), (8, "Soit", WR),
               (9, "Inscrits gagnés", WR), (10, "Coût du\ndernier inscrit", WR)], 26)
r = 6
for x in (0.05, 0.10, 0.20, 0.30):
    gain = IG[2]*((1+x)**EG - 1)
    po(w3, r, 7, "+%.0f %% de budget" % (100*x), al=ind(1))
    po(w3, r, 8, BG[2]*x, nf=EUR, al=R_)
    po(w3, r, 9, gain, f=F(9, True), nf=NB1, al=R_)
    po(w3, r, 10, BG[2]*x/gain, nf=EUR, al=R_)
    for c in range(7, 11):
        w3.cell(r, c).border = Border(bottom=sd(GRIS))
    r += 1

RC = 14
titre(w3, RC, "CE QUE ÇA DIT DU PROCHAIN INSCRIT", 2, 10)
marg = BG[2] / (EG * IG[2])
CAS = [("Coût du prochain inscrit", marg, EUR, AZUR),
       ("Coût moyen d'un inscrit de 2026", BG[2]/IG[2], EUR, INK),
       ("Rapport", marg/(BG[2]/IG[2]), '0.0" ×"', INK)]
r = RC + 1
for lab, val, nf, col in CAS:
    po(w3, r, 2, lab, f=F(9, lab.startswith("Coût du")), al=ind(1))
    po(w3, r, 4, val, f=F(11, True, col) if lab.startswith("Coût du") else F(9), nf=nf, al=R_)
    for c in range(2, 6):
        w3.cell(r, c).border = Border(bottom=sd(GRIS))
    r += 1
r += 1
po(w3, r, 2, "Le coût moyen regarde en arrière : il divise la dépense de 2026 par tous les inscrits de 2026, "
             "y compris ceux venus sans qu'on les achète. Le coût du prochain regarde en avant, et c'est le "
             "seul qui engage un budget.", f=F(8.5, False, DOUX), al=ind(0))

# =============================================================================
#  4. PLAYBACK — la preuve, hors echantillon
# =============================================================================
w4 = feuille("Playback",
             {"A": 1.8, "B": 22, "C": 13, "D": 13, "E": 13, "F": 3,
              "G": 13, "H": 13, "I": 12, "J": 13, "K": 2})
bandeau(w4, "PLAYBACK — LA MÉTHODE MISE À L'ÉPREUVE",
        "On la cale sur 2024-2025 seulement, on lui donne le budget 2026 qu'elle n'a jamais vu", 11)
po(w4, 3, 2, "Une méthode calée sur trois points et jugée sur ces trois points ne prouve rien. "
             "Ici elle n'en voit que deux, et on la juge sur le troisième.",
   f=F(8.5, False, DOUX, True), al=ind(0))

RP = 5
entete(w4, RP, [(2, "Marque · Campus", ind(1)),
                (3, "Élasticité\ncalée 24-25", WR), (4, "Budget 2026", WR),
                (5, "Inscrits\nprédits", WR),
                (7, "Inscrits\nconstatés", WR), (8, "Écart", WR), (9, "en %", WR),
                (10, "Élasticité\nsur 3 ans", WR)])
w4.cell(RP, 6).fill = fill(AZUR)
r = RP + 1
for m in MARQUES:
    po(w4, r, 2, m["nom"], f=F(9.5, True, AZUR), al=ind(0), fl=CIEL)
    for c in range(2, 11):
        w4.cell(r, c).fill = fill(CIEL)
        w4.cell(r, c).border = Border(top=sd(FILET), bottom=sd(FILET))
    pm = sum(l["pred"] for l in m["lignes"]); im = m["i"][2]
    po(w4, r, 4, m["b"][2], f=F(9, True), nf=EUR, al=R_, fl=CIEL)
    po(w4, r, 5, pm, f=F(9, True), nf=NB1, al=R_, fl=CIEL)
    po(w4, r, 7, im, f=F(9, True), nf=NB, al=R_, fl=CIEL)
    po(w4, r, 8, pm-im, f=F(9, True), nf='+#,##0.0;-#,##0.0', al=R_, fl=CIEL)
    po(w4, r, 9, pm/im-1, f=F(9, True, VERT_T if abs(pm/im-1) < .03 else OCRE),
       nf='+0.00%;-0.00%', al=R_, fl=CIEL)
    po(w4, r, 10, m["e3"], f=F(9, True), nf=EL, al=C_, fl=CIEL)
    r += 1
    for l in m["lignes"]:
        po(w4, r, 2, l["ville"], al=ind(3))
        po(w4, r, 3, l["e2"], nf=EL, al=C_)
        po(w4, r, 4, l["b"][2], nf=EUR, al=R_)
        po(w4, r, 5, l["pred"], nf=NB1, al=R_)
        po(w4, r, 7, l["i"][2], nf=NB, al=R_)
        po(w4, r, 8, l["pred"]-l["i"][2], nf='+#,##0.0;-#,##0.0', al=R_)
        po(w4, r, 9, l["ecart"], f=F(9, True, VERT_T if abs(l["ecart"]) < .03 else OCRE),
           nf='+0.00%;-0.00%', al=R_)
        po(w4, r, 10, l["e3"], nf=EL, al=C_)
        for c in range(2, 11):
            w4.cell(r, c).border = Border(bottom=sd(GRIS))
        r += 1

EG2 = eps(BG[:2], IG[:2])
PG = IG[1] * (BG[2]/BG[1]) ** EG2
po(w4, r, 2, "GROUPE", f=F(10, True), al=ind(1))
po(w4, r, 3, EG2, f=F(10, True), nf=EL, al=C_)
po(w4, r, 4, BG[2], f=F(10, True), nf=EUR, al=R_)
po(w4, r, 5, PG, f=F(10, True), nf=NB1, al=R_)
po(w4, r, 7, IG[2], f=F(10, True), nf=NB, al=R_)
po(w4, r, 8, PG-IG[2], f=F(10, True), nf='+#,##0.0;-#,##0.0', al=R_)
po(w4, r, 9, PG/IG[2]-1, f=F(12, True, VERT_T), nf='+0.00%;-0.00%', al=R_)
po(w4, r, 10, EG, f=F(10, True), nf=EL, al=C_)
for c in range(2, 11):
    w4.cell(r, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))

r += 2
titre(w4, r, "CE QUE LE TEST ÉTABLIT", 2, 10)
mo = sum(abs(l["ecart"]) for l in LIG)/len(LIG)
mx = max(abs(l["ecart"]) for l in LIG)
CONC = [
 "Au niveau du groupe, la méthode rend %.0f inscrits pour %.0f constatés : %+.2f %%." % (PG, IG[2], 100*(PG/IG[2]-1)),
 "Sur les quatorze campus, écart moyen %.2f %%, maximum %.2f %%." % (100*mo, 100*mx),
 "L'élasticité calée sur deux points (%.3f) et celle calée sur trois (%.3f) ne diffèrent que de "
 "%.1f %% : la pente est stable, elle ne dépend pas de l'année qu'on lui donne." % (EG2, EG, 100*abs(EG2/EG-1)),
 "Ce n'est pas un ajustement rétrospectif : le budget 2026 n'entre nulle part dans le calage.",
]
for i, t in enumerate(CONC):
    po(w4, r+1+i, 2, t, f=F(8.5, False, DOUX), al=ind(0))

# =============================================================================
wb.remove(wb["Sheet"])
wb._sheets = [w1, w2, w3, w4]
for s in wb:
    s.sheet_properties.tabColor = AZUR
    s.freeze_panes = "B3"
wb.save(OUT)
print("écrit :", OUT)
print("  élasticité groupe %.4f  ·  calée 24-25 %.4f  ·  playback %+.3f %%" % (EG, EG2, 100*(PG/IG[2]-1)))
print("  par campus : de %.3f à %.3f" % (min(l["e3"] for l in LIG), max(l["e3"] for l in LIG)))
