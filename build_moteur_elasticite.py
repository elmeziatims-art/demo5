#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_moteur_elasticite.py — le moteur raconte en UNE relation, jusqu'a l'EBITDA.

CE QUI CHANGE PAR RAPPORT A MOTEUR_MASQUE. Le moteur de production garde ses
deux elasticites -- budget d'acquisition vers leads payants, budget de marque
vers leads organiques -- puis son entonnoir a quatre etages. C'est juste, c'est
verifie, et c'est illisible pour qui n'a pas trente minutes.

Ce classeur raconte la MEME projection avec une seule relation, celle qu'un
directeur financier peut verifier sur ses propres comptes :

    inscrits N = inscrits N-1 x ( budget marketing N / budget N-1 ) ^ epsilon

L'entonnoir n'a pas disparu, il est A L'INTERIEUR de l'elasticite -- raison
pour laquelle on ne remultiplie surtout pas par un taux de conversion, il
serait compte deux fois.

CE QUI JUSTIFIE LA SIMPLIFICATION EST UN CONSTAT, PAS UNE HYPOTHESE. Le taux
lead vers inscrit est passe de 7,135 % a 7,147 % en trois ans. Sur les 137
inscrits gagnes, 98,5 % viennent du volume et 1,5 % de la conversion.

=============================================================================
POURQUOI DESCENDRE JUSQU'A L'EBITDA CHANGE LA NATURE DE L'EXERCICE

Tant qu'on s'arrete aux inscrits, le budget marketing n'est qu'un levier. Des
qu'on descend a l'EBITDA, il est AUSSI une charge -- et l'arbitrage devient
reel : les 111 052 EUR qu'on ajoute rapportent-ils plus qu'ils ne coutent ?

    Delta EBITDA  =  Delta CA x 88,26 %  -  Delta budget marketing

Le taux de 88,26 % n'est pas une hypothese : seuls les comptes 621, 604 et 6063
suivent le chiffre d'affaires, soit 11,74 % de celui-ci. Meme regle que
V_BUDGET, meme regle que le masque de challenge.

ET UNE PRECISION QUI COMPTE. Le marketing de 2027 n'agit que sur les ENTRANTS.
Les autres annees viennent des cohortes deja inscrites, qui ne doivent rien au
budget de l'annee. Les entrants pesent 39,5 % de l'effectif : un moteur qui
ferait bouger 100 % de l'effectif avec le budget serait faux d'un facteur 2,5.

=============================================================================
UN VRAI MASQUE, PAS UN INSTANTANE. Un onglet Donnees porte la sortie de
requete ; tout le reste est en formules qui pointent dessus. Deux cellules
jaunes seulement -- le geste sur le budget, le geste sur le tarif -- et les
quatre-vingts nombres du classeur suivent.

Les elasticites sont calculees DANS le classeur par SLOPE sur les logarithmes,
pas recopiees. On change un chiffre dans Donnees, la pente se refait.

Fonctions volontairement anterieures a 2007 -- SLOPE, LN, SUMPRODUCT, INDEX,
MATCH -- parce que Tagetik prefixe les autres en _xlfn a chaque rafraichissement.

Charte identique a MOTEUR_MASQUE : fond blanc, encre 262626, azur 007AC3.
"""
import math, warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
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

EUR  = '#,##0" €"'
EURS = '+#,##0" €";[Red]-#,##0" €";"—"'
PCT  = '+0.0%;[Red]-0.0%;"—"'
PC1  = '0.0%'
NB   = '#,##0'
NB1  = '#,##0.0'
NBS  = '+#,##0.0;[Red]-#,##0.0;"—"'
ELF  = '0.000'

exec(open("/tmp/claude-0/-home-user-demo5/b8c71a6a-b866-551a-b98b-eceadba2b120/scratchpad/snap_moteur.txt",
          encoding="utf-8").read())

MARQUES = []
for m in dict.fromkeys(c[1] for c in CAMPUS):
    MARQUES.append((m, [c for c in CAMPUS if c[1] == m]))

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
        ws.cell(1, c).fill = fill(AZUR)
    x = ws.cell(1, 2, titre); x.font = F(13, True, PANEL); x.alignment = ind(0); x.fill = fill(AZUR)
    x = ws.cell(2, 2, sous); x.font = F(8.5, False, DOUX); x.alignment = ind(0)

def titre(ws, r, txt, c1=2, c2=None):
    x = ws.cell(r, c1, txt); x.font = F(9, True, AZUR); x.alignment = ind(0)
    for c in range(c1, (c2 or c1) + 1):
        ws.cell(r, c).border = Border(bottom=sd(AZUR))

def entete(ws, r, cols, h=30, vides=()):
    ws.row_dimensions[r].height = h
    for c in vides:
        ws.cell(r, c).fill = fill(AZUR)
    for c, lab, al in cols:
        x = ws.cell(r, c, lab); x.font = F(8, True, PANEL); x.fill = fill(AZUR)
        x.alignment = al; x.border = Border(bottom=sd(INK))

def po(ws, r, c, v=None, f=None, nf=None, al=None, fl=None, bd=None):
    #  Un LIBELLE qui commence par « = » serait lu comme une formule et rendrait
    #  #NOM?. Les vraies formules ne commencent jamais par « = » suivi d'un
    #  espace : on ne desamorce que celles-la, avec une espace insecable.
    if isinstance(v, str) and v.startswith("= "):
        v = "\u00a0" + v
    x = ws.cell(r, c, v)
    x.font = f or F()
    if nf: x.number_format = nf
    if al: x.alignment = al
    if fl: x.fill = fill(fl)
    if bd: x.border = bd
    return x

# =============================================================================
#  5. DONNEES — la sortie de requete, et rien d'autre en dur dans le classeur
# =============================================================================
wd = feuille("Donnees", {})
D0 = 4                                   # premiere ligne de donnees
D1 = D0 + len(CAMPUS) - 1
COLS = ["CAMPUS", "MARQUE", "VILLE",
        "BUDGET 2024", "BUDGET 2025", "BUDGET 2026",
        "INSCRITS 2024", "INSCRITS 2025", "INSCRITS 2026",
        "EFFECTIF 2026", "DONT ENTRANTS", "CA 2026",
        "VARIABLES 2026", "STRUCTURE 2026"]
TECH = ["ln bud 24", "ln bud 25", "ln bud 26", "ln ins 24", "ln ins 25", "ln ins 26",
        "ELASTICITE 3 ANS", "ELASTICITE 24-25", "INSCRITS PREDITS 26", "ECART"]
po(wd, 1, 1, "Q_ELASTICITE  ·  sortie de requête — budget marketing et inscrits par campus",
   f=F(10, True, AZUR), al=ind(0))
po(wd, 2, 1, "Le budget marketing est la somme de l'acquisition (6231) et des frais de marque (6236), "
             "ramenés au campus qui en bénéficie. Le total groupe est inchangé.",
   f=F(8, False, DOUX, True), al=ind(0))
for j, t in enumerate(COLS, start=1):
    x = po(wd, 3, j, t, f=F(7.5, True, PANEL), al=WR, fl=AZUR, bd=Border(bottom=sd(INK)))
for j, t in enumerate(TECH, start=len(COLS) + 2):
    x = po(wd, 3, j, t, f=F(7.5, True, PANEL), al=WR, fl=DOUX, bd=Border(bottom=sd(INK)))
wd.row_dimensions[3].height = 30
for i, c in enumerate(CAMPUS):
    r = D0 + i
    for j, v in enumerate(c, start=1):
        x = po(wd, r, j, v, f=F(7.5), bd=Border(bottom=sd(GRIS)))
        x.alignment = ind(1) if j <= 3 else R_
        if j >= 4:
            x.number_format = NB1 if j in (10, 11) else NB
    for j, src in enumerate(("D", "E", "F", "G", "H", "I"), start=16):
        po(wd, r, j, "=LN(%s%d)" % (src, r), f=F(7.5), nf='0.0000', al=R_, bd=Border(bottom=sd(GRIS)))
    po(wd, r, 22, "=SLOPE(S%d:U%d,P%d:R%d)" % (r, r, r, r), f=F(7.5, True), nf=ELF, al=R_,
       bd=Border(bottom=sd(GRIS)))
    po(wd, r, 23, "=SLOPE(S%d:T%d,P%d:Q%d)" % (r, r, r, r), f=F(7.5), nf=ELF, al=R_,
       bd=Border(bottom=sd(GRIS)))
    po(wd, r, 24, "=H%d*POWER(F%d/E%d,W%d)" % (r, r, r, r), f=F(7.5), nf=NB1, al=R_,
       bd=Border(bottom=sd(GRIS)))
    po(wd, r, 25, "=X%d/I%d-1" % (r, r), f=F(7.5), nf='+0.00%;-0.00%', al=R_,
       bd=Border(bottom=sd(GRIS)))
RS = D1 + 2
po(wd, RS, 1, "SIÈGE 2026 (hors frais de marque)", f=F(9, True), al=ind(0))
po(wd, RS, 12, SIEGE_2026, f=F(9, True), nf=EUR, al=R_, bd=Border(*[sd(AZUR)] * 4))
for j, w in ((1, 13), (2, 22), (3, 13)):
    wd.column_dimensions[GL(j)].width = w
for j in range(4, 26):
    wd.column_dimensions[GL(j)].width = 11
DN = "Donnees!"
CD = lambda col: "%s$%s$%d:$%s$%d" % (DN, col, D0, col, D1)
SIEGE = "Donnees!$L$%d" % RS

#  aiguillage : une ligne du classeur porte soit un code campus, soit "MQ:<marque>"
def val(cle_cell, col):
    """Montant d'une ligne : somme de la marque, ou valeur du campus."""
    return ('IF(LEFT(%s,3)="MQ:",SUMPRODUCT((%s=MID(%s,4,99))*1,%s),'
            'INDEX(%s,MATCH(%s,%s,0)))'
            % (cle_cell, CD("B"), cle_cell, CD(col), CD(col), cle_cell, CD("A")))

#  la trame commune aux trois onglets de restitution : 5 marques, 14 campus
TRAME = []
for m, lst in MARQUES:
    TRAME.append(("MQ:" + m, m, True))
    for c in lst:
        TRAME.append((c[0], c[2], False))

def corps(ws, r0, colonnes, cle_col, nc):
    """Pose la trame et rend la ligne de chaque entree. colonnes = [(col, fabrique)]."""
    r = r0
    for cle, lib, gras in TRAME:
        po(ws, r, cle_col, cle, f=F(7, False, DOUX))          # clé technique
        x = po(ws, r, 2, lib, f=F(9.5, True, AZUR) if gras else F(),
               al=ind(0) if gras else ind(3))
        for c, fab in colonnes:
            po(ws, r, c, fab(r), f=F(9, True) if gras else F(), al=R_)
        for c in range(2, nc + 1):
            cc = ws.cell(r, c)
            if gras:
                cc.fill = fill(CIEL)
                cc.border = Border(top=sd(FILET), bottom=sd(FILET))
            else:
                cc.border = Border(bottom=sd(GRIS))
        r += 1
    return r

# =============================================================================
#  2. LE MOTEUR — le masque : deux gestes, et la chaine jusqu'a l'EBITDA
# =============================================================================
w2 = feuille("Le moteur",
             {"A": 1.6, "B": 24, "C": 13, "D": 13, "E": 9, "F": 3, "G": 11, "H": 11, "I": 10,
              "J": 3, "K": 11, "L": 11, "M": 13, "N": 13, "O": 3,
              "P": 13, "Q": 13, "R": 13, "S": 1.6})
for c in ("T", "U", "V"):
    w2.column_dimensions[c].width = 12
    w2.column_dimensions[c].hidden = True
bandeau(w2, "LE MOTEUR — DU BUDGET MARKETING À L'EBITDA",
        "Deux gestes, une élasticité mesurée, et la chaîne complète", 19)

#  ---- les deux gestes ------------------------------------------------------
po(w2, 4, 2, "LE GESTE", f=F(9, True, AZUR), al=ind(0))
for c in range(2, 20):
    w2.cell(4, c).border = Border(bottom=sd(AZUR))
po(w2, 5, 2, "Δ budget marketing 2027", f=F(9, True), al=ind(1))
G_BUD = po(w2, 5, 4, 0.137, f=F(12, True, INK), nf=PCT, al=C_, fl=JAUNE,
           bd=Border(*[sd(AZUR)] * 4))
po(w2, 5, 5, "← la tendance des trois derniers exercices", f=F(8, False, DOUX, True), al=ind(1))
po(w2, 6, 2, "Δ tarif 2027", f=F(9, True), al=ind(1))
G_PRX = po(w2, 6, 4, 0.0029, f=F(12, True, INK), nf=PCT, al=C_, fl=JAUNE,
           bd=Border(*[sd(AZUR)] * 4))
po(w2, 6, 5, "← le levier prix du cadrage V01", f=F(8, False, DOUX, True), al=ind(1))
for dv, cel in ((DataValidation(type="decimal", operator="between", formula1=-0.5, formula2=1.0),
                 "$D$5"),
                (DataValidation(type="decimal", operator="between", formula1=-0.2, formula2=0.3),
                 "$D$6")):
    w2.add_data_validation(dv); dv.add(cel)

#  ---- groupes de colonnes --------------------------------------------------
RG, RH, RD = 8, 9, 10
for c, lab in ((3, "CE QUE VOUS DÉCIDEZ"), (7, "CE QUE ÇA DONNE"),
               (13, "LE CHIFFRE D'AFFAIRES"), (16, "L'EBITDA")):
    po(w2, RG, c, lab, f=F(8, True, AZUR), al=ind(0))
for c in range(3, 19):
    w2.cell(RG, c).border = Border(bottom=sd(AZUR))
entete(w2, RH, [(2, "Marque · Campus", ind(1)),
                (3, "Budget\nmarketing 2026", WR), (4, "Budget\nmarketing 2027", WR),
                (5, "Élasti-\ncité", WR),
                (7, "Inscrits\n2026", WR), (8, "Inscrits\n2027", WR), (9, "Δ", WR),
                (11, "Effectif\n2026", WR), (12, "Effectif\n2027", WR),
                (13, "CA 2026", WR), (14, "CA 2027", WR),
                (16, "EBITDA 2026", WR), (17, "EBITDA 2027", WR), (18, "Δ EBITDA", WR)],
       vides=(6, 10, 15))

K = lambda r: "$T%d" % r
FAB = [
 (3,  lambda r: "=" + val(K(r), "F")),
 (4,  lambda r: "=$C%d*(1+$D$5)" % r),
 (5,  lambda r: "=SLOPE(LN(INDEX(%s,MATCH(%s,%s,0))):LN(0),0)" % (CD("I"), K(r), CD("A"))),
 (7,  lambda r: "=" + val(K(r), "I")),
 (8,  lambda r: "=$G%d*POWER(1+$D$5,$E%d)" % (r, r)),
 (9,  lambda r: "=$H%d-$G%d" % (r, r)),
 (11, lambda r: "=" + val(K(r), "J")),
 (12, lambda r: "=$K%d+$I%d" % (r, r)),
 (13, lambda r: "=" + val(K(r), "L")),
 (14, lambda r: "=$L%d*($M%d/$K%d)*(1+$D$6)" % (r, r, r)),
 (16, lambda r: "=$M%d-$U%d-$C%d-%s" % (r, r, r, val(K(r), "N"))),
 (17, lambda r: "=$N%d-$V%d-$D%d-%s" % (r, r, r, val(K(r), "N"))),
 (18, lambda r: "=$Q%d-$P%d" % (r, r)),
 (21, lambda r: "=" + val(K(r), "M")),
 (22, lambda r: "=$U%d*($N%d/$M%d)" % (r, r, r)),
]
RF = corps(w2, RD, FAB, 20, 18)
#  l'elasticite ne se calcule pas ligne a ligne ici : on la prend a l'onglet dedie
for r in range(RD, RF):
    w2.cell(r, 5).value = ("=INDEX(Historique!$U$1:$U$200,"
                           "MATCH($T%d,Historique!$T$1:$T$200,0))" % r)
    w2.cell(r, 5).number_format = ELF
    w2.cell(r, 5).alignment = C_

#  ---- les lignes de synthese : des sommes, pas des recalculs ----------------
#  Le grain de calcul est le CAMPUS : c'est la qu'une elasticite se mesure. Une
#  ligne marque est la somme de ses campus, sinon le masque ne s'additionne pas
#  sous les yeux du lecteur -- et un masque qui ne s'additionne pas est mort.
#  Son elasticite affichee est alors celle qui RESSORT de l'agregation.
ENFANTS = {}
_mq = None
for i, (cle, _lib, gras) in enumerate(TRAME):
    if gras:
        _mq = RD + i
        ENFANTS[_mq] = []
    else:
        ENFANTS[_mq].append(RD + i)
COLS_SOM = (3, 4, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 21, 22)
for rm, fils in ENFANTS.items():
    for c in COLS_SOM:
        w2.cell(rm, c).value = "=" + "+".join("$%s%d" % (GL(c), rr) for rr in fils)
    #  L'elasticite d'une ligne de synthese est la moyenne de ses campus, ponderee
    #  par les inscrits. Elle reste definie meme quand le geste est nul, ce qu'une
    #  lecture LN(H/G)/LN(1+geste) ne ferait pas.
    w2.cell(rm, 5).value = "=SUMPRODUCT($E$%d:$E$%d,$G$%d:$G$%d)/SUM($G$%d:$G$%d)" % (
        fils[0], fils[-1], fils[0], fils[-1], fils[0], fils[-1])
for r in range(RD, RF):
    for c, nf in ((3, EUR), (4, EUR), (7, NB), (8, NB1), (9, NBS), (11, NB), (12, NB1),
                  (13, EUR), (14, EUR), (16, EUR), (17, EUR), (18, EURS)):
        w2.cell(r, c).number_format = nf

#  ---- le total groupe, puis la cascade EBITDA ------------------------------
RT = RF
MQ_ROWS = [RD + i for i, (cle, _, g) in enumerate(TRAME) if g]
SOM = lambda col: "=" + "+".join("$%s%d" % (col, r) for r in MQ_ROWS)
po(w2, RT, 2, "GROUPE  ·  avant siège", f=F(10, True), al=ind(1))
for c, nf in ((3, EUR), (4, EUR), (7, NB), (8, NB1), (9, NBS), (11, NB), (12, NB1),
              (13, EUR), (14, EUR), (16, EUR), (17, EUR), (18, EURS)):
    po(w2, RT, c, SOM(GL(c)), f=F(10, True), nf=nf, al=R_)
for c in (21, 22):
    w2.cell(RT, c).value = SOM(GL(c))
po(w2, RT, 5, "=(" + "+".join("$E%d*$G%d" % (r, r) for r in MQ_ROWS) + ")/("
              + "+".join("$G%d" % r for r in MQ_ROWS) + ")", f=F(10, True), nf=ELF, al=C_)
for c in range(2, 19):
    w2.cell(RT, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))

RC = RT + 2
titre(w2, RC, "D'OÙ VIENT L'EFFET SUR L'EBITDA", 2, 9)
CASC = [
 ("Chiffre d'affaires supplémentaire", "=$N%d-$M%d" % (RT, RT), EURS, False),
 ("dont les charges variables consomment", "=-($V%d-$U%d)" % (RT, RT), EURS, False),
 ("Budget marketing supplémentaire", "=-($D%d-$C%d)" % (RT, RT), EURS, False),
 ("= EFFET SUR L'EBITDA", "=$R%d" % RT, EURS, True),
]
r = RC + 1
for lab, fm, nf, gras in CASC:
    po(w2, r, 2, lab, f=F(10, True) if gras else F(9), al=ind(1))
    po(w2, r, 8, fm, f=F(11, True) if gras else F(9), nf=nf, al=R_)
    for c in range(2, 10):
        w2.cell(r, c).border = Border(top=sd(INK) if gras else None,
                                      bottom=sd(INK, "double") if gras else sd(GRIS))
    r += 1

RE = RC + 1
titre(w2, RC, "L'EBITDA DU RÉSEAU", 11, 18)
BIL = [("EBITDA avant siège, 2026", "=$P%d" % RT, EUR, False),
       ("Siège", "=-%s" % SIEGE, EURS, False),
       ("= EBITDA réseau 2026", "=$R%d-%s" % (RC + 1, SIEGE), EUR, True),
       ("EBITDA réseau 2027", "=$Q%d-%s" % (RT, SIEGE), EUR, True),
       ("écart", "=$R%d-$R%d" % (RE + 3, RE + 2), EURS, False)]
r = RE
for i, (lab, fm, nf, gras) in enumerate(BIL):
    po(w2, r, 11, lab, f=F(10, True) if gras else F(9), al=ind(1))
    po(w2, r, 18, fm, f=F(11, True) if gras else F(9), nf=nf, al=R_)
    for c in range(11, 19):
        w2.cell(r, c).border = Border(bottom=sd(INK, "double") if gras else sd(GRIS))
    r += 1
w2.cell(RE + 2, 18).value = "=$R%d-%s" % (RE, SIEGE)
w2.cell(RE + 3, 18).value = "=$Q%d-%s" % (RT, SIEGE)
w2.cell(RE + 4, 18).value = "=$R%d-$R%d" % (RE + 3, RE + 2)

RN = r + 1
NOTES = [
 "Le marketing de 2027 n'agit que sur les ENTRANTS : les autres années viennent de cohortes déjà "
 "inscrites, qui ne doivent rien au budget de l'année. Les entrants pèsent 39,5 % de l'effectif.",
 "Les charges variables (621 vacataires, 604 achats d'études, 6063 fournitures) suivent le chiffre "
 "d'affaires — 11,74 % de celui-ci. Tout le reste est tenu constant : ce moteur porte sur le "
 "marketing et le tarif, pas sur les coûts.",
 "Le budget marketing est à la fois le levier et une charge. C'est pour cela que l'effet sur "
 "l'EBITDA n'est pas la marge sur le chiffre d'affaires supplémentaire, mais cette marge MOINS le "
 "budget engagé.",
 "L'élasticité vient de l'onglet « Historique », où elle est calculée par régression "
 "sur les trois exercices. Elle n'est recopiée nulle part.",
 "Le calcul se fait CAMPUS PAR CAMPUS : c'est là qu'une élasticité se mesure, et là que le "
 "budget se dépense. Les lignes marque et la ligne groupe sont des sommes — le masque "
 "s'additionne. L'élasticité qu'elles affichent n'est donc pas une pente mesurée : c'est la "
 "moyenne de leurs campus, pondérée par les inscrits.",
]
for i, t in enumerate(NOTES):
    po(w2, RN + i, 2, t, f=F(8, False, DOUX), al=ind(0))

# =============================================================================
#  3. CE QUE DIT L'HISTORIQUE — l'elasticite, calculee ici et nulle part ailleurs
# =============================================================================
w3 = feuille("Historique",
             {"A": 1.6, "B": 22, "C": 13, "D": 13, "E": 13, "F": 3,
              "G": 11, "H": 11, "I": 11, "J": 3, "K": 12, "L": 12, "M": 13, "N": 1.6})
for c in ("T", "U", "V", "W", "X", "Y", "Z", "AA", "AB"):
    w3.column_dimensions[c].width = 11
    w3.column_dimensions[c].hidden = True
bandeau(w3, "CE QUE DIT L'HISTORIQUE",
        "Trois exercices, deux colonnes, une pente — mesurée là où le budget se décide", 13)
po(w3, 3, 2, "L'élasticité est la pente de ln(inscrits) sur ln(budget marketing), calculée par "
             "SLOPE sur les colonnes masquées V à AA. Rien n'est recopié.",
   f=F(8.5, False, DOUX, True), al=ind(0))
RH3, RD3 = 5, 6
entete(w3, RH3, [(2, "Marque · Campus", ind(1)),
                 (3, "Budget 2024", WR), (4, "Budget 2025", WR), (5, "Budget 2026", WR),
                 (7, "Inscrits\n2024", WR), (8, "Inscrits\n2025", WR), (9, "Inscrits\n2026", WR),
                 (11, "Budget\npar an", WR), (12, "Inscrits\npar an", WR),
                 (13, "ÉLASTICITÉ", WR)], vides=(6, 10))
FAB3 = [(3, lambda r: "=" + val("$T%d" % r, "D")),
        (4, lambda r: "=" + val("$T%d" % r, "E")),
        (5, lambda r: "=" + val("$T%d" % r, "F")),
        (7, lambda r: "=" + val("$T%d" % r, "G")),
        (8, lambda r: "=" + val("$T%d" % r, "H")),
        (9, lambda r: "=" + val("$T%d" % r, "I")),
        (11, lambda r: "=POWER($E%d/$C%d,0.5)-1" % (r, r)),
        (12, lambda r: "=POWER($I%d/$G%d,0.5)-1" % (r, r)),
        (13, lambda r: "=$U%d" % r)]
RF3 = corps(w3, RD3, FAB3, 20, 13)
for r in range(RD3, RF3):
    for j, src in enumerate(("C", "D", "E", "G", "H", "I"), start=21):
        po(w3, r, j, "=LN($%s%d)" % (src, r), f=F(7), nf='0.0000')
    po(w3, r, 21 + 6, "=SLOPE($X%d:$Z%d,$U%d:$W%d)" % (r, r, r, r), f=F(7), nf=ELF)
    for c, nf in ((3, EUR), (4, EUR), (5, EUR), (7, NB), (8, NB), (9, NB),
                  (11, PCT), (12, PCT)):
        w3.cell(r, c).number_format = nf
    w3.cell(r, 13).number_format = ELF
    w3.cell(r, 13).alignment = C_
#  U = elasticite, lue par les autres onglets ; V..AA = les logarithmes
for r in range(RD3, RF3):
    w3.cell(r, 21).value = "=SLOPE($X%d:$Z%d,$U%d:$W%d)" % (r, r, r, r)
for r in range(RD3, RF3):
    for j, src in enumerate(("C", "D", "E", "G", "H", "I"), start=22):
        w3.cell(r, j).value = "=LN($%s%d)" % (src, r)
    w3.cell(r, 21).value = "=SLOPE($Y%d:$AA%d,$V%d:$X%d)" % (r, r, r, r)
    #  temoin : l'elasticite des seules lignes CAMPUS. MIN et MAX ignorent le
    #  texte, donc les lignes marque -- qui sont des agregats -- sortent du calcul.
    w3.cell(r, 28).value = '=IF(LEFT($T%d,3)="MQ:","",$U%d)' % (r, r)

RT3 = RF3
MQ3 = [RD3 + i for i, (cle, _, g) in enumerate(TRAME) if g]
po(w3, RT3, 20, "GROUPE", f=F(7, False, DOUX))
po(w3, RT3, 2, "GROUPE", f=F(10, True), al=ind(1))
for c, nf in ((3, EUR), (4, EUR), (5, EUR), (7, NB), (8, NB), (9, NB)):
    po(w3, RT3, c, "=" + "+".join("$%s%d" % (GL(c), r) for r in MQ3), f=F(10, True), nf=nf, al=R_)
po(w3, RT3, 11, "=POWER($E%d/$C%d,0.5)-1" % (RT3, RT3), f=F(10, True), nf=PCT, al=R_)
po(w3, RT3, 12, "=POWER($I%d/$G%d,0.5)-1" % (RT3, RT3), f=F(10, True), nf=PCT, al=R_)
for j, src in enumerate(("C", "D", "E", "G", "H", "I"), start=22):
    po(w3, RT3, j, "=LN($%s%d)" % (src, RT3), f=F(7), nf='0.0000')
po(w3, RT3, 21, "=SLOPE($Y%d:$AA%d,$V%d:$X%d)" % (RT3, RT3, RT3, RT3), f=F(7), nf=ELF)
po(w3, RT3, 13, "=$U%d" % RT3, f=F(12, True, AZUR), nf=ELF, al=C_)
for c in range(2, 14):
    w3.cell(RT3, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))

r = RT3 + 2
titre(w3, r, "COMMENT LA LIRE", 2, 13)
LECT = [
 '="Une élasticité de "&TEXT($M%d,"0.00")&" veut dire : +1 %% de budget marketing donne +"'
 '&TEXT($M%d,"0.00")&" %% d\'inscrits."' % (RT3, RT3),
 "Elle est inférieure à 1 partout : le volume monte toujours, mais moins vite que la dépense. "
 "C'est le rendement décroissant, et il se mesure au lieu de se supposer.",
 '="Elle varie de "&TEXT(MIN($AB$%d:$AB$%d),"0.00")&" à "&TEXT(MAX($AB$%d:$AB$%d),"0.00")'
 '&" selon le campus : les marchés les plus disputés sont ceux où le prochain euro travaille le moins."'
 % (RD3, RF3 - 1, RD3, RF3 - 1),
 "Une élasticité ne se moyenne pas. Celle d'une marque, ici, est recalculée sur le budget et les "
 "inscrits de la marque entière, comme un indice base 100 — ce n'est pas la moyenne de ses campus.",
 '="Deux mesures, deux niveaux : sur les totaux consolidés du groupe la pente vaut "'
 '&TEXT($M%d,"0.00")&" ; le moteur, lui, calcule campus par campus et fait la somme, ce qui '
 'donne "&TEXT(\'Le moteur\'!$E$%d,"0.00")&". L\'écart est un effet de composition : les campus '
 'les plus réactifs ne sont pas les plus gros. C\'est le second chiffre qui pilote le masque, '
 'parce que c\'est au campus que le budget se dépense."' % (RT3, RT),
]
for i, t in enumerate(LECT):
    po(w3, r + 1 + i, 2, t, f=F(8.5, False, DOUX), al=ind(0))

# =============================================================================
#  4. PLAYBACK — la preuve, hors echantillon, en formules
# =============================================================================
w4 = feuille("Playback",
             {"A": 1.6, "B": 22, "C": 13, "D": 13, "E": 13, "F": 3,
              "G": 13, "H": 11, "I": 11, "J": 13, "K": 1.6})
for c in ("T", "U"):
    w4.column_dimensions[c].width = 11
    w4.column_dimensions[c].hidden = True
bandeau(w4, "PLAYBACK — LA MÉTHODE MISE À L'ÉPREUVE",
        "Calée sur 2024-2025 seulement, à qui l'on donne le budget 2026 qu'elle n'a jamais vu", 10)
po(w4, 3, 2, "Une méthode calée sur trois points et jugée sur ces trois points ne prouve rien. "
             "Ici elle n'en voit que deux, et on la juge sur le troisième.",
   f=F(8.5, False, DOUX, True), al=ind(0))
RH4, RD4 = 5, 6
entete(w4, RH4, [(2, "Marque · Campus", ind(1)),
                 (3, "Élasticité\ncalée 24-25", WR), (4, "Budget 2026", WR),
                 (5, "Inscrits\nprédits", WR),
                 (7, "Inscrits\nconstatés", WR), (8, "Écart", WR), (9, "en %", WR),
                 (10, "Élasticité\nsur 3 ans", WR)], vides=(6,))
H = "Historique"
FAB4 = [
 (3, lambda r: "=SLOPE(LN(INDEX(%s!$H$1:$H$200,MATCH($T%d,%s!$T$1:$T$200,0))):"
               "LN(1),LN(1):LN(1))" % (H, r, H)),
 (4, lambda r: "=INDEX(%s!$E$1:$E$200,MATCH($T%d,%s!$T$1:$T$200,0))" % (H, r, H)),
 (5, lambda r: "=INDEX(%s!$H$1:$H$200,MATCH($T%d,%s!$T$1:$T$200,0))*POWER($D%d/"
               "INDEX(%s!$D$1:$D$200,MATCH($T%d,%s!$T$1:$T$200,0)),$C%d)" % (H, r, H, r, H, r, H, r)),
 (7, lambda r: "=INDEX(%s!$I$1:$I$200,MATCH($T%d,%s!$T$1:$T$200,0))" % (H, r, H)),
 (8, lambda r: "=$E%d-$G%d" % (r, r)),
 (9, lambda r: "=$E%d/$G%d-1" % (r, r)),
 (10, lambda r: "=INDEX(%s!$M$1:$M$200,MATCH($T%d,%s!$T$1:$T$200,0))" % (H, r, H)),
]
RF4 = corps(w4, RD4, FAB4, 20, 10)
#  l'elasticite 24-25 : pente sur deux points = ln(i25/i24) / ln(b25/b24)
for r in range(RD4, RF4):
    m = lambda col: "INDEX(%s!$%s$1:$%s$200,MATCH($T%d,%s!$T$1:$T$200,0))" % (H, col, col, r, H)
    w4.cell(r, 3).value = "=LN(%s/%s)/LN(%s/%s)" % (m("H"), m("G"), m("D"), m("C"))
    w4.cell(r, 5).value = "=%s*POWER($D%d/%s,$C%d)" % (m("H"), r, m("D"), r)
    for c, nf in ((3, ELF), (4, EUR), (5, NB1), (7, NB), (8, NBS), (9, '+0.00%;-0.00%'), (10, ELF)):
        w4.cell(r, c).number_format = nf
    w4.cell(r, 3).alignment = C_; w4.cell(r, 10).alignment = C_
    #  temoin : l'ecart absolu des seules lignes CAMPUS. MOYENNE et MAX ignorent
    #  le texte, les lignes marque sont donc hors du calcul.
    w4.cell(r, 21).value = '=IF(LEFT($T%d,3)="MQ:","",ABS($I%d))' % (r, r)
RT4 = RF4
po(w4, RT4, 20, "GROUPE", f=F(7, False, DOUX))
po(w4, RT4, 2, "GROUPE", f=F(10, True), al=ind(1))
mg = lambda col: "INDEX(%s!$%s$1:$%s$200,MATCH(\"GROUPE\",%s!$T$1:$T$200,0))" % (H, col, col, H)
po(w4, RT4, 3, "=LN(%s/%s)/LN(%s/%s)" % (mg("H"), mg("G"), mg("D"), mg("C")),
   f=F(10, True), nf=ELF, al=C_)
po(w4, RT4, 4, "=" + mg("E"), f=F(10, True), nf=EUR, al=R_)
po(w4, RT4, 5, "=%s*POWER($D%d/%s,$C%d)" % (mg("H"), RT4, mg("D"), RT4),
   f=F(10, True), nf=NB1, al=R_)
po(w4, RT4, 7, "=" + mg("I"), f=F(10, True), nf=NB, al=R_)
po(w4, RT4, 8, "=$E%d-$G%d" % (RT4, RT4), f=F(10, True), nf=NBS, al=R_)
po(w4, RT4, 9, "=$E%d/$G%d-1" % (RT4, RT4), f=F(12, True, VERT_T), nf='+0.00%;-0.00%', al=R_)
po(w4, RT4, 10, "=" + mg("M"), f=F(10, True), nf=ELF, al=C_)
for c in range(2, 11):
    w4.cell(RT4, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))
r = RT4 + 2
titre(w4, r, "CE QUE LE TEST ÉTABLIT", 2, 10)
CONC = [
 '="Au niveau du groupe, la méthode rend "&TEXT($E%d,"#,##0")&" inscrits pour "'
 '&TEXT($G%d,"#,##0")&" constatés, soit "&TEXT($I%d,"+0.00%%;-0.00%%")&"."' % (RT4, RT4, RT4),
 '="Sur les "&TEXT(COUNT($U$%d:$U$%d),"0")&" campus, écart moyen "'
 '&TEXT(AVERAGE($U$%d:$U$%d),"0.00%%")&", maximum "&TEXT(MAX($U$%d:$U$%d),"0.00%%")&"."'
 % (RD4, RF4 - 1, RD4, RF4 - 1, RD4, RF4 - 1),
  ("=\"L'élasticité calée sur deux points (\"&TEXT($C%d,\"0.000\")"
   "&\") et celle calée sur trois (\"&TEXT($J%d,\"0.000\")"
   "&\") ne diffèrent que de \"&TEXT(ABS($C%d/$J%d-1),\"0.0%%\")"
   "&\" : la pente ne dépend pas de l'année qu'on lui donne.\"") % (RT4, RT4, RT4, RT4),
 "Ce n'est pas un ajustement rétrospectif : le budget 2026 n'entre nulle part dans le calage.",
]
for i, t in enumerate(CONC):
    po(w4, r + 1 + i, 2, t, f=F(8.5, False, DOUX), al=ind(0))

# =============================================================================
#  1. LA METHODE — le recit, aucun tableau
# =============================================================================
w1 = feuille("La méthode", {"A": 1.6, "B": 4, "C": 26, "D": 94, "E": 2})
bandeau(w1, "COMMENT LA PROJECTION EST CONSTRUITE",
        "Une seule relation, mesurée sur trois exercices — et ce qu'elle permet de dire", 5)
TEMPS = [
 ("1", "On ne prévoit pas,\non construit",
  "Personne ne devine le nombre d'inscrits de 2027. On part de 2026 et on applique ce que "
  "l'historique a mesuré. Deux entrées seulement : le budget marketing, décidé au siège, et les "
  "effectifs déjà inscrits, qui poursuivent leur cursus."),
 ("2", "Ce que dit l'historique :\nune élasticité",
  "Sur 2024-2026, le budget marketing a crû de +13,7 % par an, les inscrits de +6,1 %. Le rapport "
  "de ces deux croissances, mesuré en logarithmes, vaut 0,46 sur les totaux du groupe. Autrement "
  "dit : +1 % de budget donne +0,46 % d'inscrits. Ce n'est pas une hypothèse posée, c'est une "
  "pente relevée sur les comptes — et elle est relevée séparément pour chacun des 14 campus, "
  "parce que c'est au campus que le budget se dépense."),
 ("3", "Pourquoi ce rendement\ndécroît",
  "Parce qu'on n'achète pas des inscrits : on achète de l'audience, sur un marché fini, par "
  "enchères. Les contacts les moins chers sont pris en premier ; l'euro suivant va chercher des "
  "audiences plus larges et plus disputées. Le volume continue de monter, moins vite que la dépense."),
 ("4", "Ce qu'on n'a PAS eu\nà supposer",
  "Le taux de transformation d'un contact en inscrit est passé de 7,135 % à 7,147 % en trois ans. "
  "Sur les 137 inscrits gagnés, 98,5 % viennent du volume de contacts et 1,5 % de la "
  "transformation. Le tenir constant ne relève d'aucune hypothèse. Et c'est pour cela qu'il ne faut "
  "surtout pas le remultiplier : il est déjà contenu dans l'élasticité."),
 ("5", "Le marketing n'agit que\nsur les entrants",
  "Les inscrits entrent en première année. Les autres années viennent des cohortes déjà là, qui ne "
  "doivent rien au budget de l'exercice. Les entrants pèsent 39,5 % de l'effectif : un moteur qui "
  "ferait bouger tout l'effectif avec le budget se tromperait d'un facteur deux et demi."),
 ("6", "Puis le compte\nd'exploitation",
  "L'effectif rencontre le tarif et donne le chiffre d'affaires. Les charges variables — vacataires, "
  "achats d'études, fournitures — le suivent, à 11,74 %. Le reste est tenu constant. Et le budget "
  "marketing se retranche : c'est un levier, mais c'est aussi une charge."),
 ("7", "Et la preuve",
  "On cale l'élasticité sur 2024 et 2025 uniquement. On lui donne le budget 2026, qu'elle n'a "
  "jamais vu. Elle rend 1 232 inscrits ; il y en a eu 1 229. Écart : +0,25 %. Par campus, écart "
  "moyen 1,06 %, maximum 2,28 %."),
]
r = 4
for num, tit, txt in TEMPS:
    po(w1, r, 2, num, f=F(14, True, AZUR), al=C_)
    po(w1, r, 3, tit, f=F(10, True, INK), al=WL)
    po(w1, r, 4, txt, f=F(9), al=WL)
    w1.row_dimensions[r].height = max(46, math.ceil(len(txt) / 90) * 12 + 16)
    for c in range(2, 5):
        w1.cell(r, c).border = Border(bottom=sd(GRIS))
    r += 1
r += 1
titre(w1, r, "LA RELATION, ÉCRITE EN ENTIER", 2, 4)
r += 1
w1.row_dimensions[r].height = 22
po(w1, r, 3, "inscrits 2027", f=F(11, True, INK), al=R_)
#  espace initial volontaire : une chaine qui commence par « = » serait lue
#  comme une formule par Excel, et rendrait #NOM?.
po(w1, r, 4, "  =  inscrits 2026  ×  ( budget marketing 2027 ÷ budget marketing 2026 ) ^ élasticité",
   f=F(11, True, AZUR), al=ind(1))
r += 1
TXT_REL = ('="et rien d\'autre : le taux de transformation est deja dans l\'exposant. '
           'L\'elasticite est propre a chaque campus, de "&TEXT(MIN(Historique!$AB$%d:$AB$%d),"0.00")'
           '&" a "&TEXT(MAX(Historique!$AB$%d:$AB$%d),"0.00")&" ; elle vaut "'
           '&TEXT(Historique!$M$%d,"0.00")&" sur les totaux du groupe."') % (
    RD3, RF3 - 1, RD3, RF3 - 1, RT3)
TXT_REL = TXT_REL.replace("deja", "d\u00e9j\u00e0").replace("L'elasticite", "L'\u00e9lasticit\u00e9")
TXT_REL = TXT_REL.replace("propre a chaque", "propre \u00e0 chaque").replace('&" a "&', '&" \u00e0 "&')
po(w1, r, 4, TXT_REL,
   f=F(8.5, False, DOUX, True), al=ind(1))
r += 2
titre(w1, r, "PUIS, JUSQU'À L'EBITDA", 2, 4)
for i, t in enumerate([
  "chiffre d'affaires  =  effectif  ×  tarif",
  "charges variables   =  chiffre d'affaires  ×  11,74 %",
  "EBITDA              =  chiffre d'affaires  −  variables  −  budget marketing  −  structure",
]):
    po(w1, r + 1 + i, 4, t, f=F(10, i == 2, AZUR if i == 2 else INK), al=ind(1))

# =============================================================================
wb.remove(wb["Sheet"])
wb._sheets = [w1, w2, w3, w4, wd]
for s in wb:
    s.sheet_properties.tabColor = AZUR
w2.freeze_panes = "B%d" % RD
w3.freeze_panes = "B%d" % RD3
w4.freeze_panes = "B%d" % RD4
wd.freeze_panes = "A4"
wb.save(OUT)
print("écrit :", OUT)
print("  onglets :", wb.sheetnames)
print("  trame : %d lignes (%d marques + %d campus)" % (len(TRAME), len(MARQUES), len(CAMPUS)))
