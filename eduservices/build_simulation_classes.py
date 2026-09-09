#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_simulation_classes.py — le masque d'OUVERTURE et de FERMETURE de classe.

CE QU'IL DEMONTRE. Le cadrage top-down projette un effectif SANS PLAFOND DE
CAPACITE. Il peut donc sortir 86,7 etudiants dans un cursus qui n'a que 78
places -- et personne ne le voit, parce que le budget est un montant, pas une
salle. Symetriquement il maintient des groupes a 53 % de remplissage.

Ce masque confronte, classe par classe, l'effectif construit aux places
reellement ouvertes, et chiffre le seul geste que l'operationnel maitrise :
ouvrir un groupe, en fermer un, recruter quelques etudiants de plus.

CE QUI PART, CE QUI RESTE -- tout le masque tient dans cette distinction.

    621   vacataires          PART avec le groupe. Un groupe de moins, c'est un
                              paquet d'heures de moins ; un groupe de plus, un
                              paquet de plus. C'est le seul cout qui suit la
                              STRUCTURE.
    604   achats d'etudes     SUIVENT L'ELEVE, environ 367 EUR (294 chez Pigier).
    6063  fournitures
    6411  permanents          RESTENT. Le professeur permanent n'est pas licencie
                              parce qu'un groupe ferme -- sauf decision RH, et
                              c'est pour ca qu'il y a un curseur.
    613 615 616 625 645 6413 63511   structure du campus : RESTE.
    6236  frais de marque     RESTE, et se REALLOUE sur les classes survivantes.
    siege 6414 6226 626 6281 6331 6333    idem.

    6231  recrutement         volontairement EXCLU du cout marginal : le cout du
                              prochain inscrit est deja porte par le CAC
                              MARGINAL (CPL / (rendement x conversion)), 890 a
                              2 193 EUR selon le campus. L'y remettre compterait
                              l'acquisition deux fois -- c'est la meme regle que
                              dans le masque « Le moteur ».

D'OU LE PIEGE, qui est le vrai sujet de la demo. Au cout complet, le BTS 2e
annee de Pigier Bordeaux affiche 3 971 EUR de marge : il a l'air de ne rien
valoir. Sa CONTRIBUTION reelle est de 170 410 EUR -- un facteur 43. Fermer la
filiere BTS de ce campus ne fait pas gagner d'argent : elle en fait perdre
359 774 EUR, parce que les permanents, les murs, la marque et le siege restent
et se reallouent simplement sur les classes qui restent.

LA SAISIE. Les deux curseurs par ligne (delta groupes, etudiants recrutes) se
stockent dans le cube d'hypotheses AW_002_000001_000001, au grain CAMPUS, avec
la classe portee par KEY_ALLOC :

    PARAMETRE = SIM_DGROUPES   ENTITY = MBWAY_PAR   KEY_ALLOC = MAS_MGT|M1|ALT
    PARAMETRE = SIM_DELEVES    idem
    PARAMETRE = SIM_ECO_PERM / SIM_ECO_STRUCT   grain campus, KEY_ALLOC vide

Ces lignes sont PUREMENT ADDITIVES : les cinq lecteurs du cube filtrent deja
(V_CADRAGE_LEVIERS sur ENTITY='GRP', Q_HYPOTHESES idem, V_MOTEUR sur
HYP_PRICE_COEF, V_ALLOCATION et DIAG_COCKPIT_VIDE sur PARAMETRE LIKE 'ALLOC_').
Rien de ce qui existe ne les voit. Le cadrage n'est pas touche.

LES TROIS FICHIERS SQL QUI VONT AVEC

    V_SIMULATION_CLASSES  la base : effectif construit, capacite ouverte, cout
                          poste par poste, couts UNITAIRES (vacataires par
                          groupe, consommables par eleve, permanents par groupe)
                          et CAC marginal du campus.
    Q_SIMULATION_CLASSES  la requete du masque, sans CTE ni ORDER BY ni ';',
                          alias entre guillemets doubles et sans accent.
    V_SIMULATION_SAISIE   la meme arithmetique cote serveur, a partir de ce qui
                          a ete saisi. Verifie identique au masque sur les trois
                          gestes de la demo (+1 groupe M1 MBway Paris +60 063,
                          +12 inscrits +72 303, -1 groupe Pigier Bordeaux
                          -12 308).
    Q_SIMULATION_EFFET    sa restitution.

Donnees : V_SIMULATION_CLASSES (2027, version V01), instantane au 09/09/2026.
CA campus cale a 1 centime sur la table du masque de challenge.
"""
import warnings
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.utils import get_column_letter as GL

warnings.filterwarnings("ignore")
OUT = "/home/user/demo5/eduservices/SIMULATION_CLASSES.xlsx"

#  la charte du masque Cadrage, pas une autre
INK, AZUR, GRIS = "262626", "007AC3", "E7E6E6"
CIEL, JAUNE, DOUX = "E8F1F9", "FFF2CC", "6B7075"
PANEL, FILET, ROUGE, VERT = "FFFFFF", "D5D7DA", "C41822", "2E7D4F"
UI = "Arial"
F = lambda sz=8.5, b=False, c=INK, i=False: Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd = lambda c=FILET, st="thin": Side(style=st, color=c)
D_ = Alignment("right", vertical="center")
C_ = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)
WR = Alignment("center", vertical="center", wrap_text=True)

EUR   = '#,##0" €";[Red]-#,##0" €";"–"'
EURS  = '+#,##0" €";[Red]-#,##0" €";"–"'
PCT   = '0.0%;[Red]-0.0%;"–"'
PCT0  = '0%'
NB1   = '#,##0.0;[Red]-#,##0.0;"–"'
NB1S  = '+#,##0.0;[Red]-#,##0.0;"–"'
ENT   = '#,##0;[Red]-#,##0;"–"'
DGRP  = '+0;[Red]-0;0'

exec(open("/tmp/claude-0/-home-user-demo5/b8c71a6a-b866-551a-b98b-eceadba2b120/scratchpad/snapshot.txt", encoding="utf-8").read())

MQ = {"IPAC": "Ipac", "ISCOM": "ISCOM", "MBWAY": "MBway", "PIGIER": "Pigier", "TUNON": "Tunon"}
VILLE = {"MTP": "Montpellier", "NAN": "Nantes", "REN": "Rennes", "LIL": "Lille",
         "PAR": "Paris", "TLS": "Toulouse", "BOR": "Bordeaux", "LYO": "Lyon"}
LIB_PROG = [("BAC_CCE", "Bachelor Commerce"), ("BAC_COM", "Bachelor Communication"),
            ("BAC_MGT", "Bachelor Management"), ("BAC_RH", "Bachelor Ressources humaines"),
            ("BAC_TOU", "Bachelor Tourisme"), ("BTS_GES", "BTS Gestion"),
            ("MAS_COM", "Mastère Communication"), ("MAS_MGT", "Mastère Management")]
LIB_AN = [("B1", "1re année"), ("B2", "2e année"), ("B3", "3e année"),
          ("BTS1", "1re année"), ("BTS2", "2e année"), ("M1", "M1"), ("M2", "M2")]
LIB_MOD = [("ALT", "alternance"), ("INIT", "initial")]
CAMPUS = sorted({r[0] for r in SNAPSHOT})
LIB_CAMP = [(c, MQ[c.split("_")[0]] + " " + VILLE[c.split("_")[1]]) for c in CAMPUS]
DEFAUT = "MBway Paris"

wb = openpyxl.Workbook()

# =============================================================================
#  4. LIBELLES — la table de correspondance, codes a gauche, libelles a droite
# =============================================================================
wl = wb.active
wl.title = "Libelles"
wl.sheet_view.showGridLines = False
for c, w in (("A", 2.0), ("B", 14), ("C", 22), ("D", 3), ("E", 12), ("F", 28),
             ("G", 3), ("H", 10), ("I", 14), ("J", 3), ("K", 10), ("L", 14)):
    wl.column_dimensions[c].width = w
wl["B1"] = "TABLE DE CORRESPONDANCE"
wl["B1"].font = F(11, True, AZUR)
wl["B2"] = "Le code est la clé technique lue par le masque ; le libellé est ce que voit le lecteur."
wl["B2"].font = F(8, False, DOUX, True)
for col, titre, table in (("B", "Campus", LIB_CAMP), ("E", "Programme", LIB_PROG),
                          ("H", "Année", LIB_AN), ("K", "Modalité", LIB_MOD)):
    c2 = GL(openpyxl.utils.column_index_from_string(col) + 1)
    wl[col + "4"] = "code"
    wl[c2 + "4"] = titre
    for cc in (col, c2):
        wl[cc + "4"].font = F(8, True, PANEL)
        wl[cc + "4"].fill = fill(AZUR)
        wl[cc + "4"].alignment = ind(1) if cc == col else ind(1)
    for i, (k, v) in enumerate(table):
        wl[col + str(5 + i)] = k
        wl[c2 + str(5 + i)] = v
        for cc in (col, c2):
            wl[cc + str(5 + i)].font = F(8.5)
            wl[cc + str(5 + i)].alignment = ind(1)
            wl[cc + str(5 + i)].border = Border(bottom=sd(GRIS))
        wl[col + str(5 + i)].font = F(8, False, DOUX)

# =============================================================================
#  3. DONNEES — le retour de Q_SIMULATION_CLASSES, plus les colonnes techniques
# =============================================================================
wd = wb.create_sheet("Donnees")
wd.sheet_view.showGridLines = False
COLS = ["CAMPUS", "MARQUE", "PROGRAMME", "ANNEE", "MODALITE", "ENTREE", "GROUPES",
        "CAPACITE", "PLACES", "EFFECTIF", "CA", "VACATAIRES", "CONSOMMABLES",
        "RECRUTEMENT", "PERMANENTS", "STRUCTURE", "FRAIS DE MARQUE", "SIEGE",
        "COUT DU PROCHAIN INSCRIT", "COUT COMPLET", "MARGE COMPLETE", "CONTRIBUTION",
        "VACATAIRES PAR GROUPE", "PERMANENTS PAR GROUPE", "CONSOMMABLES PAR ELEVE",
        "REMPLISSAGE", "RANG", "CLE", "EFFECTIF PAR GROUPE", "POINT MORT"]
wd["A1"] = "Q_SIMULATION_CLASSES · scénario 2027BUD_V1 · version V01"
wd["A1"].font = F(10, True, AZUR)
HD = 3                                    # ligne des en-tetes
D0 = HD + 1                               # premiere ligne de donnees
D1 = D0 + len(SNAPSHOT) - 1
for j, t in enumerate(COLS, start=1):
    x = wd.cell(HD, j, t)
    x.font = F(7.5, True, PANEL)
    x.fill = fill(AZUR if j <= 21 else DOUX)
    x.alignment = WR
    x.border = Border(bottom=sd(INK))
wd.row_dimensions[HD].height = 30
for i, r in enumerate(SNAPSHOT):
    y = D0 + i
    ent, ncl, cap, eff, ca, vac, cons, recr, perm, st, mq, sg, cac = r[4:]
    vals = [r[0], r[0].split("_")[0], r[1], r[2], r[3], ent, ncl, cap, ncl * cap,
            eff, ca, vac, cons, recr, perm, st, mq, sg, cac]
    for j, v in enumerate(vals, start=1):
        wd.cell(y, j, v)
    wd.cell(y, 20, "=SUM(L%d:R%d)" % (y, y))                     # cout complet
    wd.cell(y, 21, "=K%d-T%d" % (y, y))                          # marge complete
    wd.cell(y, 22, "=K%d-(L%d+M%d+N%d)" % (y, y, y, y))          # contribution
    wd.cell(y, 23, "=L%d/G%d" % (y, y))                          # vacataires / groupe
    wd.cell(y, 24, "=O%d/G%d" % (y, y))                          # permanents / groupe
    wd.cell(y, 25, "=M%d/J%d" % (y, y))                          # consommables / eleve
    wd.cell(y, 26, "=J%d/I%d" % (y, y))                          # remplissage
    wd.cell(y, 27, "=COUNTIFS($A$%d:$A%d,$A%d)" % (D0, y, y))    # rang dans le campus
    wd.cell(y, 28, '=$A%d&"#"&$AA%d' % (y, y))                   # cle campus#rang
    wd.cell(y, 29, "=J%d/G%d" % (y, y))                          # effectif par groupe
    #  point mort = cout complet d'UN groupe / marge de contribution par eleve
    #  (la formule de V_CAMPUS_CLASSE, a l'identique)
    wd.cell(y, 30, "=(T%d/G%d)/(V%d/J%d)" % (y, y, y, y))
    for j in range(1, 31):
        x = wd.cell(y, j)
        x.font = F(7.5)
        x.border = Border(bottom=sd(GRIS))
        if j <= 6:
            x.alignment = ind(1)
        elif j in (7, 8, 9):
            x.number_format = ENT; x.alignment = D_
        elif j == 10:
            x.number_format = NB1; x.alignment = D_
        elif j == 26:
            x.number_format = PCT; x.alignment = D_
        elif j == 27:
            x.number_format = ENT; x.alignment = D_
        elif j == 28:
            x.alignment = ind(1)
        elif j in (29, 30):
            x.number_format = NB1; x.alignment = D_
        else:
            x.number_format = EUR; x.alignment = D_
for j in range(1, 31):
    wd.column_dimensions[GL(j)].width = 11 if j > 6 else 13
wd.column_dimensions["A"].width = 13
DN = "Donnees!"

LIM = 400                       # marge large : la requete peut grossir sans retoucher le masque
RG = lambda col: "%s$%s$%d:$%s$%d" % (DN, col, D0, col, LIM)
CL = lambda col: "%s$%s$1:$%s$%d" % (DN, col, col, LIM)
IX = lambda col, r: "INDEX(%s,$U%d)" % (CL(col), r)

# =============================================================================
#  1. SIMULATION — le masque
# =============================================================================
ws = wb.create_sheet("Simulation", 0)
ws.sheet_view.showGridLines = False
LARG = {"A": 1.8, "B": 26, "C": 11, "D": 11, "E": 8.5, "F": 8.5, "G": 11, "H": 11,
        "I": 11.5, "J": 13, "K": 13, "L": 13, "M": 9.5, "N": 11.5, "O": 10, "P": 11,
        "Q": 12.5, "R": 12.5, "S": 13.5, "T": 1.8}
for c, w in LARG.items():
    ws.column_dimensions[c].width = w
for c in ("U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC", "AD", "AE"):
    ws.column_dimensions[c].width = 11
    ws.column_dimensions[c].hidden = True

R_BAN, R_SUB, R_PAR, R_P2, R_P3, R_CONS = 1, 2, 4, 5, 6, 8
R_GRP, R_HDR, R_D0, NLIG = 10, 11, 12, 5
R_TOT = R_D0 + NLIG
R_B, R_BH, R_L0 = 19, 20, 21
R_LTOT, R_LFIG = R_L0 + 7, R_L0 + 8
R_R0, R_REFF = 21, 27
R_C0 = 29                       # la cascade EBITDA, cinq lignes
R_N0 = 36
CODE = "$AC$4"                  # le code campus, en technique

def po(r, c, v=None, f=None, nf=None, al=None, fl=None, bd=None):
    x = ws.cell(r, c, v)
    x.font = f or F()
    if nf: x.number_format = nf
    if al: x.alignment = al
    if fl: x.fill = fill(fl)
    if bd: x.border = bd
    return x

#  ---- bandeau -------------------------------------------------------------
ws.row_dimensions[R_BAN].height = 26
for c in range(1, 21):
    po(R_BAN, c, None, fl=AZUR)
po(R_BAN, 2, "SIMULATION D'OUVERTURE ET DE FERMETURE DE CLASSE",
   f=F(13, True, PANEL), al=ind(0), fl=AZUR)
po(R_SUB, 2, "Budget 2027 construit par le cadrage · version V01 — ce que valent vraiment "
             "un groupe de plus et un groupe de moins", f=F(8.5, False, DOUX), al=ind(0))

#  ---- selecteur et hypotheses ---------------------------------------------
po(R_PAR, 2, "Campus", f=F(9, True), al=ind(0))
sel = po(R_PAR, 3, DEFAUT, f=F(10, True, INK), al=C_, fl=JAUNE, bd=Border(*[sd(AZUR)] * 4))
po(R_PAR, 4, None, fl=JAUNE, bd=Border(top=sd(AZUR), bottom=sd(AZUR), right=sd(AZUR)))
dv = DataValidation(type="list", formula1="=Libelles!$C$5:$C$%d" % (4 + len(LIB_CAMP)),
                    allow_blank=False)
ws.add_data_validation(dv); dv.add(sel)
po(R_PAR, 6, "capacité par groupe : Bachelor 32 · Mastère 26 · BTS 30",
   f=F(8, False, DOUX, True), al=ind(0))
po(R_PAR, 12, "SI UN GROUPE FERME, QU'EST-CE QU'ON SUPPRIME VRAIMENT ?",
   f=F(8.5, True, AZUR), al=ind(0))
for r, lib in ((R_P2, "Part des enseignants permanents effectivement supprimée"),
               (R_P3, "Part de la structure du campus effectivement supprimée")):
    po(r, 12, lib, f=F(8.5), al=ind(0))
    po(r, 19, 0.0, f=F(9, True), nf=PCT0, al=C_, fl=JAUNE, bd=Border(*[sd(AZUR)] * 4))
dvp = DataValidation(type="decimal", operator="between", formula1=0, formula2=1,
                     allow_blank=False, error="Une part entre 0 % et 100 %.",
                     errorTitle="Hors bornes")
ws.add_data_validation(dvp); dvp.add("S%d:S%d" % (R_P2, R_P3))

po(R_PAR, 29, '=INDEX(Libelles!$B$1:$B$40,MATCH($C$4,Libelles!$C$1:$C$40,0))')
po(R_CONS, 29, "=SUMPRODUCT((%s=%s)*(%s>%s)*(%s-%s))"
   % (RG("A"), CODE, RG("J"), RG("I"), RG("J"), RG("I")))
po(R_CONS, 30, "=SUMPRODUCT((%s=%s)*(%s>%s)*(%s-%s))"
   % (RG("A"), CODE, RG("I"), RG("J"), RG("I"), RG("J")))

po(R_CONS, 2,
   '="Le cadrage a construit "&TEXT(SUMIFS(%s,%s,%s),"#,##0")&" étudiants pour "'
   '&TEXT(SUMIFS(%s,%s,%s),"#,##0")&" places ouvertes : "'
   '&IF($AC$8<0.5,"aucun sans place",TEXT($AC$8,"#,##0")&" sans place")'
   '&", et "&TEXT($AD$8,"#,##0")&" places vides."'
   % (RG("J"), RG("A"), CODE, RG("I"), RG("A"), CODE),
   f=F(9.5, True, INK), al=ind(0))
ws.row_dimensions[R_CONS].height = 16

#  ---- titres de groupes de colonnes ---------------------------------------
po(R_GRP, 5, "CE QUE LE CADRAGE A CONSTRUIT", f=F(8, True, AZUR), al=ind(0))
po(R_GRP, 13, "VOTRE DÉCISION", f=F(8, True, AZUR), al=ind(0))
po(R_GRP, 15, "CE QUE ÇA DONNE", f=F(8, True, AZUR), al=ind(0))
po(R_GRP, 17, "L'EFFET", f=F(8, True, AZUR), al=ind(0))
for c in range(5, 20):
    x = ws.cell(R_GRP, c)
    if x.value is None:
        x.font = F(8, True, AZUR); x.alignment = ind(0)
    x.border = Border(bottom=sd(AZUR))
    if 13 <= c <= 14:
        x.fill = fill(JAUNE)

#  ---- en-tetes ------------------------------------------------------------
ENTETES = [(2, "Programme", ind(0)), (3, "Année", C_), (4, "Modalité", C_),
           (5, "Groupes", WR), (6, "Places", WR), (7, "Effectif construit", WR),
           (8, "Effectif plaçable", WR), (9, "Remplissage", WR),
           (10, "Chiffre d'affaires", WR), (11, "Contribution", WR),
           (12, "Marge complète", WR), (13, "Groupes\n+ / −", WR),
           (14, "Étudiants recrutés", WR), (15, "Places après", WR),
           (16, "Effectif retenu", WR), (17, "Δ chiffre d'affaires", WR),
           (18, "Δ coûts", WR), (19, "Δ EBITDA", WR)]
ws.row_dimensions[R_HDR].height = 30
for c, t, al in ENTETES:
    po(R_HDR, c, t, f=F(8, True, PANEL), al=al, fl=AZUR, bd=Border(bottom=sd(INK)))

#  ---- les lignes de classes ------------------------------------------------
for i in range(NLIG):
    r = R_D0 + i
    ws.row_dimensions[r].height = 15
    g = "$U%d=0" % r
    po(r, 21, '=IF(ISERROR(MATCH(%s&"#"&%d,Donnees!$AB$1:$AB$400,0)),0,'
              'MATCH(%s&"#"&%d,Donnees!$AB$1:$AB$400,0))' % (CODE, i + 1, CODE, i + 1))
    po(r, 2, '=IF(%s,"",INDEX(Libelles!$F$1:$F$40,MATCH(%s,Libelles!$E$1:$E$40,0)))'
       % (g, IX("C", r)), al=ind(1))
    po(r, 3, '=IF(%s,"",INDEX(Libelles!$I$1:$I$40,MATCH(%s,Libelles!$H$1:$H$40,0)))'
       % (g, IX("D", r)), al=C_)
    po(r, 4, '=IF(%s,"",INDEX(Libelles!$L$1:$L$40,MATCH(%s,Libelles!$K$1:$K$40,0)))'
       % (g, IX("E", r)), al=C_)
    po(r, 5, '=IF(%s,"",%s)' % (g, IX("G", r)), nf=ENT, al=D_)
    po(r, 6, '=IF(%s,"",%s)' % (g, IX("I", r)), nf=ENT, al=D_)
    po(r, 7, '=IF(%s,"",%s)' % (g, IX("J", r)), nf=NB1, al=D_)
    po(r, 8, '=IF(%s,"",MIN($G%d,$F%d))' % (g, r, r), nf=NB1, al=D_)
    po(r, 9, '=IF(%s,"",$G%d/$F%d)' % (g, r, r), nf=PCT, al=D_)
    po(r, 10, '=IF(%s,"",%s)' % (g, IX("K", r)), nf=EUR, al=D_)
    po(r, 11, '=IF(%s,"",%s)' % (g, IX("V", r)), nf=EUR, al=D_)
    po(r, 12, '=IF(%s,"",%s)' % (g, IX("U", r)), nf=EUR, al=D_)
    po(r, 13, 0, f=F(9, True), nf=DGRP, al=C_, fl=JAUNE,
       bd=Border(left=sd(AZUR), right=sd(GRIS), top=sd(GRIS), bottom=sd(GRIS)))
    po(r, 14, 0, f=F(9, True), nf=NB1, al=C_, fl=JAUNE,
       bd=Border(left=sd(GRIS), right=sd(AZUR), top=sd(GRIS), bottom=sd(GRIS)))
    po(r, 15, '=IF(%s,"",($E%d+$M%d)*%s)' % (g, r, r, IX("H", r)), nf=ENT, al=D_)
    po(r, 16, '=IF(%s,"",MIN($G%d+$N%d,$O%d))' % (g, r, r, r), nf=NB1, al=D_)
    po(r, 17, '=IF(%s,"",($P%d-$H%d)*$J%d/$G%d)' % (g, r, r, r, r), nf=EURS, al=D_)
    #  les composantes du cout, en technique
    po(r, 22, '=IF(%s,0,$M%d*%s)' % (g, r, IX("W", r)))                       # vacataires
    po(r, 23, '=IF(%s,0,($P%d-$H%d)*%s)' % (g, r, r, IX("Y", r)))             # consommables
    po(r, 24, '=IF(%s,0,MAX(0,$P%d-MIN($G%d,$O%d))*%s)' % (g, r, r, r, IX("S", r)))
    po(r, 25, '=IF(%s,0,MAX(0,-$M%d)*%s*$S$5)' % (g, r, IX("X", r)))          # permanents
    po(r, 26, '=IF(%s,0,MAX(0,-$M%d)*%s/MAX($E%d,1)*$S$6)' % (g, r, IX("P", r), r))
    #  ce que les places d'aujourd'hui ne permettent pas de livrer, decision a zero
    po(r, 27, '=IF(%s,0,($H%d-$G%d)*$J%d/$G%d)' % (g, r, r, r, r))
    po(r, 28, '=IF(%s,0,($H%d-$G%d)*%s)' % (g, r, r, IX("Y", r)))
    po(r, 18, '=IF(%s,"",$V%d+$W%d+$X%d-$Y%d-$Z%d)' % (g, r, r, r, r, r), nf=EURS, al=D_)
    po(r, 19, '=IF(%s,"",$Q%d-$R%d)' % (g, r, r), f=F(9, True), nf=EURS, al=D_)
    for c in range(2, 20):
        x = ws.cell(r, c)
        if c not in (13, 14):
            x.border = Border(bottom=sd(GRIS))
        if c == 12:
            x.border = Border(bottom=sd(GRIS), right=sd(GRIS))

#  ---- total campus ---------------------------------------------------------
ws.row_dimensions[R_TOT].height = 17
S_ = lambda col: "=SUM(%s%d:%s%d)" % (col, R_D0, col, R_TOT - 1)
po(R_TOT, 2, "Total du campus", f=F(9, True), al=ind(1))
for c, nf in ((5, ENT), (6, ENT), (7, NB1), (8, NB1), (10, EUR), (11, EUR), (12, EUR),
              (15, ENT), (16, NB1), (17, EURS), (18, EURS)):
    po(R_TOT, c, S_(GL(c)), f=F(9, True), nf=nf, al=D_)
po(R_TOT, 9, "=$G%d/$F%d" % (R_TOT, R_TOT), f=F(9, True), nf=PCT, al=D_)
po(R_TOT, 19, "=$Q%d-$R%d" % (R_TOT, R_TOT), f=F(10, True), nf=EURS, al=D_)
for c in range(2, 20):
    ws.cell(R_TOT, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))

#  ---- bloc gauche : ce qui part, ce qui reste ------------------------------
po(R_B, 2, "CE QUI PART AVEC LE GROUPE, CE QUI RESTE SUR LE CAMPUS",
   f=F(9, True, AZUR), al=ind(0))
for c in range(2, 11):
    ws.cell(R_B, c).border = Border(bottom=sd(AZUR))
po(R_BH, 2, "Poste", f=F(8, True, PANEL), al=ind(1), fl=DOUX)
for c in (3, 4, 5, 6, 7, 8):
    po(R_BH, c, None, fl=DOUX)
po(R_BH, 9, "Montant 2027", f=F(8, True, PANEL), al=D_, fl=DOUX)
po(R_BH, 10, "Comportement", f=F(8, True, PANEL), al=ind(1), fl=DOUX)
POSTES = [("Vacataires (621)", "L", "part avec le groupe", AZUR),
          ("Achats d'études et fournitures (604 · 6063)", "M", "suivent l'élève", AZUR),
          ("Recrutement (6231)", "N", "suit l'entrant", AZUR),
          ("Enseignants permanents (6411)", "O", "restent, sauf décision RH", DOUX),
          ("Structure du campus (613 · 615 · 616 · 625 · 645 · 6413 · 63511)", "P",
           "reste", DOUX),
          ("Frais de marque (6236)", "Q", "reste, se réalloue", DOUX),
          ("Siège (6414 · 6226 · 626 · 6281 · 6331 · 6333)", "R", "reste, se réalloue", DOUX)]
for i, (lib, col, comp, coul) in enumerate(POSTES):
    r = R_L0 + i
    po(r, 2, lib, al=ind(1))
    po(r, 9, "=SUMIFS(%s,%s,%s)" % (RG(col), RG("A"), CODE), nf=EUR, al=D_)
    po(r, 10, comp, f=F(8, False, coul, True), al=ind(1))
    for c in range(2, 11):
        ws.cell(r, c).border = Border(bottom=sd(GRIS))
po(R_LTOT, 2, "Coût complet du campus", f=F(9, True), al=ind(1))
po(R_LTOT, 9, "=SUM(I%d:I%d)" % (R_L0, R_L0 + 6), f=F(9, True), nf=EUR, al=D_)
for c in range(2, 11):
    ws.cell(R_LTOT, c).border = Border(top=sd(INK), bottom=sd(INK))
po(R_LFIG, 2, "dont ne bouge pas si un groupe ferme", f=F(8.5, True, DOUX), al=ind(1))
po(R_LFIG, 9, "=SUM(I%d:I%d)" % (R_L0 + 3, R_L0 + 6), f=F(8.5, True, DOUX), nf=EUR, al=D_)
po(R_LFIG, 10, '=TEXT(I%d/I%d,"0 %%")&" du coût complet"' % (R_LFIG, R_LTOT),
   f=F(8, False, DOUX, True), al=ind(1))

#  ---- bloc droit : l'effet de la decision ---------------------------------
po(R_B, 12, "L'EFFET DE VOTRE DÉCISION", f=F(9, True, AZUR), al=ind(0))
for c in range(12, 20):
    ws.cell(R_B, c).border = Border(bottom=sd(AZUR))
for c in range(12, 19):
    po(R_BH, c, None, fl=DOUX)
po(R_BH, 12, "", f=F(8, True, PANEL), al=ind(1), fl=DOUX)
po(R_BH, 19, "Montant", f=F(8, True, PANEL), al=D_, fl=DOUX)
SU = lambda col: "SUM(%s%d:%s%d)" % (col, R_D0, col, R_TOT - 1)
EFFETS = [("Chiffre d'affaires", "=$Q%d" % R_TOT),
          ("Vacataires (621)", "=-%s" % SU("V")),
          ("Achats d'études et fournitures (604 · 6063)", "=-%s" % SU("W")),
          ("Acquisition des étudiants recrutés en plus", "=-%s" % SU("X")),
          ("Permanents et structure effectivement supprimés", "=%s+%s" % (SU("Y"), SU("Z")))]
for i, (lib, fm) in enumerate(EFFETS):
    r = R_R0 + i
    po(r, 12, lib, al=ind(1))
    po(r, 19, fm, nf=EURS, al=D_)
    for c in range(12, 20):
        ws.cell(r, c).border = Border(bottom=sd(GRIS))
po(R_REFF, 12, "EFFET SUR L'EBITDA DU CAMPUS", f=F(10, True), al=ind(1))
po(R_REFF, 19, "=SUM(S%d:S%d)" % (R_R0, R_R0 + 4), f=F(11, True), nf=EURS, al=D_)
for c in range(12, 20):
    ws.cell(R_REFF, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))

#  ---- la cascade : du budget construit a l'EBITDA reellement livrable ------
NL = "=%s-%s" % (SU("AA"), SU("AB"))
CASC = [("EBITDA du campus construit par le cadrage", "=%s" % SU("L"), EUR, False),
        ("ce que les places d'aujourd'hui ne permettent pas de livrer", NL, EURS, False),
        ("EBITDA livrable sans rien changer", "=$S%d+$S%d" % (R_C0, R_C0 + 1), EUR, True),
        ("effet de votre décision", "=$S%d" % R_REFF, EURS, False),
        ("EBITDA du campus après décision", "=$S%d+$S%d" % (R_C0 + 2, R_C0 + 3), EUR, True)]
for i, (lib, fm, nf, gras) in enumerate(CASC):
    r = R_C0 + i
    po(r, 12, lib, f=F(9.5, True) if gras else F(9), al=ind(1))
    po(r, 19, fm, f=F(10, True) if gras else F(9), nf=nf, al=D_)
    for c in range(12, 20):
        ws.cell(r, c).border = Border(
            top=sd(GRIS) if i == 0 else None,
            bottom=sd(INK, "double") if i == 4 else sd(INK if gras else GRIS))

#  ---- les notes -----------------------------------------------------------
NOTES = [
    "Effectif plaçable = MIN(effectif construit ; places ouvertes). Le cadrage, lui, ne plafonne pas : c'est de cet écart "
    "que vient la ligne « ce que les places d'aujourd'hui ne permettent pas de livrer ».",
    "Effectif retenu = MIN(effectif construit + étudiants recrutés ; places après décision). Les colonnes Δ mesurent l'écart "
    "à l'effectif plaçable, c'est-à-dire ce que votre décision change vraiment.",
    "Un groupe qui s'ouvre ou qui se ferme emporte UN paquet d'heures de vacataires — c'est le seul coût qui suit la structure. "
    "Les achats et fournitures suivent l'élève.",
    "Les étudiants recrutés en plus sont valorisés au CAC marginal du campus, CPL ÷ (rendement × conversion), de 890 € à 2 193 € "
    "selon le campus. Le compte 6231 en est exclu pour ne pas compter l'acquisition deux fois.",
    "Les permanents et la structure ne sortent de l'EBITDA que dans la proportion saisie en haut à droite. À 0 %, ils restent "
    "et se réallouent sur les classes qui survivent.",
]
for i, t in enumerate(NOTES):
    po(R_N0 + i, 2, t, f=F(8, False, DOUX), al=ind(0))

ws.conditional_formatting.add(
    "I%d:I%d" % (R_D0, R_TOT - 1),
    CellIsRule(operator="greaterThan", formula=["1"],
               font=Font(name=UI, size=8.5, bold=True, color=ROUGE)))
ws.conditional_formatting.add(
    "I%d:I%d" % (R_D0, R_TOT - 1),
    CellIsRule(operator="lessThan", formula=["0.7"],
               font=Font(name=UI, size=8.5, bold=True, color="B26B00")))
dvg = DataValidation(type="whole", operator="between", formula1=-3, formula2=3,
                     allow_blank=False, error="Entre −3 et +3 groupes.", errorTitle="Hors bornes")
ws.add_data_validation(dvg); dvg.add("M%d:M%d" % (R_D0, R_TOT - 1))
dve = DataValidation(type="decimal", operator="between", formula1=-200, formula2=200,
                     allow_blank=False, error="Un nombre d'étudiants.", errorTitle="Hors bornes")
ws.add_data_validation(dve); dve.add("N%d:N%d" % (R_D0, R_TOT - 1))
ws.freeze_panes = "B%d" % R_D0

# =============================================================================
#  2. LE PIEGE DU COUT COMPLET — pourquoi fermer coute de l'argent
# =============================================================================
wp = wb.create_sheet("Le piège du coût complet", 1)
wp.sheet_view.showGridLines = False
for c, w in (("A", 1.8), ("B", 30), ("C", 12), ("D", 13), ("E", 14), ("F", 14),
             ("G", 15), ("H", 14), ("I", 14), ("J", 15), ("K", 13)):
    wp.column_dimensions[c].width = w
wp.column_dimensions["L"].width = 10
wp.column_dimensions["L"].hidden = True

def pp(r, c, v=None, f=None, nf=None, al=None, fl=None, bd=None):
    x = wp.cell(r, c, v)
    x.font = f or F()
    if nf: x.number_format = nf
    if al: x.alignment = al
    if fl: x.fill = fill(fl)
    if bd: x.border = bd
    return x

wp.row_dimensions[1].height = 26
for c in range(1, 12):
    pp(1, c, None, fl=AZUR)
pp(1, 2, "LE PIÈGE DU COÛT COMPLET", f=F(13, True, PANEL), al=ind(0), fl=AZUR)
pp(2, 2, "Pourquoi une classe qui ne rapporte rien au coût complet coûte cher à fermer",
   f=F(8.5, False, DOUX), al=ind(0))
pp(4, 2, "Campus", f=F(9, True), al=ind(0))
pp(4, 3, "=Simulation!$C$4", f=F(10, True, AZUR), al=ind(0))
TEXTES = [
    "L'allocation répartit sur chaque classe la totalité des charges du campus, de la marque et du siège. C'est juste pour mesurer une rentabilité, "
    "et faux pour décider d'une fermeture : la classe qui part n'emmène avec elle que ses vacataires et ses consommables.",
    "Tout le reste — les enseignants permanents, les murs, la marque, le siège — reste à payer, et se réalloue simplement sur les classes qui survivent. "
    "La marge complète de la classe fermée disparaît donc du rapport, mais ses coûts, eux, réapparaissent ailleurs.",
]
for i, t in enumerate(TEXTES):
    pp(6 + i, 2, t, f=F(8.5, False, DOUX), al=ind(0))

R1T, R1H, R1D, R1TOT = 9, 10, 11, 16
pp(R1T, 2, "CE QUE DIT LE COÛT COMPLET, ET CE QUE DIT LA CONTRIBUTION",
   f=F(9, True, AZUR), al=ind(0))
for c in range(2, 12):
    wp.cell(R1T, c).border = Border(bottom=sd(AZUR))
E1 = [(2, "Programme", ind(1)), (3, "Année", C_), (4, "Chiffre d'affaires", WR),
      (5, "Coûts qui partent\navec la classe", WR), (6, "Contribution", WR),
      (7, "Coûts qui restent\nsur le campus", WR), (8, "Marge complète", WR),
      (9, "Contribution\n÷ marge complète", WR),
      (10, "Effectif\npar groupe", WR), (11, "Point mort\nen élèves", WR)]
wp.row_dimensions[R1H].height = 30
for c, t, al in E1:
    pp(R1H, c, t, f=F(8, True, PANEL), al=al, fl=AZUR, bd=Border(bottom=sd(INK)))
IP = lambda col, r: "INDEX(%s,$L%d)" % (CL(col), r)
for i in range(5):
    r = R1D + i
    g = "$L%d=0" % r
    pp(r, 12, '=IF(ISERROR(MATCH(Simulation!$AC$4&"#"&%d,Donnees!$AB$1:$AB$400,0)),0,'
              'MATCH(Simulation!$AC$4&"#"&%d,Donnees!$AB$1:$AB$400,0))' % (i + 1, i + 1))
    pp(r, 2, '=IF(%s,"",INDEX(Libelles!$F$1:$F$40,MATCH(%s,Libelles!$E$1:$E$40,0)))' % (g, IP("C", r)),
       al=ind(1))
    pp(r, 3, '=IF(%s,"",INDEX(Libelles!$I$1:$I$40,MATCH(%s,Libelles!$H$1:$H$40,0)))' % (g, IP("D", r)),
       al=C_)
    pp(r, 4, '=IF(%s,"",%s)' % (g, IP("K", r)), nf=EUR, al=D_)
    pp(r, 5, '=IF(%s,"",%s+%s+%s)' % (g, IP("L", r), IP("M", r), IP("N", r)), nf=EUR, al=D_)
    pp(r, 6, '=IF(%s,"",$D%d-$E%d)' % (g, r, r), f=F(8.5, True), nf=EUR, al=D_)
    pp(r, 7, '=IF(%s,"",%s+%s+%s+%s)' % (g, IP("O", r), IP("P", r), IP("Q", r), IP("R", r)),
       nf=EUR, al=D_)
    pp(r, 8, '=IF(%s,"",$F%d-$G%d)' % (g, r, r), nf=EUR, al=D_)
    pp(r, 9, '=IF(%s,"",IF($H%d<=0,"—",$F%d/$H%d))' % (g, r, r, r), nf='#,##0.0" ×"', al=D_)
    #  la lecture du cockpit directeur, reprise telle quelle : un groupe est sous
    #  l'eau quand son effectif ne couvre pas le cout complet d'un groupe.
    pp(r, 10, '=IF(%s,"",%s)' % (g, IP("AC", r)), nf=NB1, al=D_)
    pp(r, 11, '=IF(%s,"",%s)' % (g, IP("AD", r)), nf=NB1, al=D_)
    for c in range(2, 12):
        wp.cell(r, c).border = Border(bottom=sd(GRIS))
pp(R1TOT, 2, "Total du campus", f=F(9, True), al=ind(1))
for c in (4, 5, 6, 7, 8):
    pp(R1TOT, c, "=SUM(%s%d:%s%d)" % (GL(c), R1D, GL(c), R1D + 4),
       f=F(9, True), nf=EUR, al=D_)
pp(R1TOT, 9, "=IF($H%d<=0,\"—\",$F%d/$H%d)" % (R1TOT, R1TOT, R1TOT),
   f=F(9, True), nf='#,##0.0" ×"', al=D_)
for c in range(2, 12):
    wp.cell(R1TOT, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))
#  le groupe sous son point mort passe en rouge -- meme signal que le cockpit
wp.conditional_formatting.add(
    "K%d:K%d" % (R1D, R1D + 4),
    FormulaRule(formula=["AND($K%d<>\"\",$K%d>$J%d)" % (R1D, R1D, R1D)],
                font=Font(name=UI, size=8.5, bold=True, color=ROUGE)))

#  ---- bloc 2 : fermer une filiere entiere ---------------------------------
R2T, R2N, R2H, R2D = 18, 19, 20, 21
R2MC, R2SEM, R2EF, R2EC = R2D + 7, R2D + 8, R2D + 9, R2D + 10
pp(R2T, 2, "ET SI ON FERMAIT UNE FILIÈRE ENTIÈRE ?", f=F(9, True, AZUR), al=ind(0))
for c in range(2, 11):
    wp.cell(R2T, c).border = Border(bottom=sd(AZUR))
#  les deux filieres du campus, en technique : la premiere, puis la premiere qui differe
pp(4, 12, '=IF($L%d=0,"",INDEX(%s,$L%d))' % (R1D, CL("C"), R1D))
#  la seconde filiere est celle de la DERNIERE ligne du campus : les lignes sont
#  groupees par programme, donc si elle differe de la premiere, il y en a deux.
pp(6, 12, "=COUNTIFS(%s,Simulation!$AC$4)" % RG("A"))
pp(7, 12, '=IF($L$6=0,0,MATCH(Simulation!$AC$4&"#"&$L$6,Donnees!$AB$1:$AB$400,0))')
pp(5, 12, '=IF($L$7=0,"",IF(INDEX(%s,$L$7)=$L$4,"",INDEX(%s,$L$7)))' % (CL("C"), CL("C")))
for k, (colM, colE, cle) in enumerate((("F", "G", "$L$4"), ("I", "J", "$L$5"))):
    pp(R2N, openpyxl.utils.column_index_from_string(colM),
       '=IF(%s="","—",INDEX(Libelles!$F$1:$F$40,MATCH(%s,Libelles!$E$1:$E$40,0)))' % (cle, cle),
       f=F(9.5, True, AZUR), al=ind(0))
    for c in (colM, colE):
        wp[c + str(R2N)].border = Border(bottom=sd(AZUR))
    pp(R2H, openpyxl.utils.column_index_from_string(colM), "Montant 2027",
       f=F(8, True, PANEL), al=D_, fl=DOUX)
    pp(R2H, openpyxl.utils.column_index_from_string(colE), "Effet si on ferme",
       f=F(8, True, PANEL), al=D_, fl=DOUX)
pp(R2H, 2, "Poste", f=F(8, True, PANEL), al=ind(1), fl=DOUX)
for c in (3, 4, 5, 8):
    pp(R2H, c, None, fl=DOUX)
LIGNES2 = [("Chiffre d'affaires", "K", -1),
           ("Vacataires (621)", "L", +1),
           ("Achats d'études et fournitures (604 · 6063)", "M", +1),
           ("Recrutement (6231)", "N", +1),
           ("Enseignants permanents (6411) — restent", "O", 0),
           ("Structure du campus (613 · 615 · 616 · 625 · 645 · 6413 · 63511) — reste", "P", 0),
           ("Frais de marque et siège (6236 · holding) — restent", "Q", 0)]
for i, (lib, col, sgn) in enumerate(LIGNES2):
    r = R2D + i
    pp(r, 2, lib, f=F(8.5) if sgn else F(8.5, False, DOUX), al=ind(1))
    for colM, colE, cle in (("F", "G", "$L$4"), ("I", "J", "$L$5")):
        base = ('SUMIFS(%s,%s,Simulation!$AC$4,%s,%s)' % (RG(col), RG("A"), RG("C"), cle)) \
            if col != "Q" else \
            ('SUMIFS(%s,%s,Simulation!$AC$4,%s,%s)+SUMIFS(%s,%s,Simulation!$AC$4,%s,%s)'
             % (RG("Q"), RG("A"), RG("C"), cle, RG("R"), RG("A"), RG("C"), cle))
        pp(r, openpyxl.utils.column_index_from_string(colM),
           '=IF(%s="","",%s)' % (cle, base), nf=EUR, al=D_)
        pp(r, openpyxl.utils.column_index_from_string(colE),
           '=IF(%s="","",%s%s)' % (cle, "" if sgn >= 0 else "-", base) if sgn
           else '=IF(%s="","",0)' % cle,
           f=F(8.5) if sgn else F(8.5, False, DOUX), nf=EURS, al=D_)
    for c in range(2, 11):
        wp.cell(r, c).border = Border(bottom=sd(GRIS))
pp(R2MC, 2, "Marge complète affichée par le rapport", f=F(8.5, True), al=ind(1))
pp(R2SEM, 2, "la fermeture semble donc rapporter cela en moins", f=F(8.5), al=ind(1))
pp(R2EF, 2, "EFFET RÉEL SUR L'EBITDA DU CAMPUS", f=F(10, True), al=ind(1))
pp(R2EC, 2, "écart : les coûts qui restent et se réallouent sur les classes survivantes",
   f=F(8.5, False, DOUX, True), al=ind(1))
for colM, colE in (("F", "G"), ("I", "J")):
    cM = openpyxl.utils.column_index_from_string(colM)
    cE = openpyxl.utils.column_index_from_string(colE)
    pp(R2MC, cM, "=%s%d-SUM(%s%d:%s%d)" % (colM, R2D, colM, R2D + 1, colM, R2D + 6),
       f=F(8.5, True), nf=EUR, al=D_)
    pp(R2SEM, cE, "=-%s%d" % (colM, R2MC), nf=EURS, al=D_)
    pp(R2EF, cE, "=SUM(%s%d:%s%d)" % (colE, R2D, colE, R2D + 6),
       f=F(11, True), nf=EURS, al=D_)
    pp(R2EC, cE, "=%s%d-%s%d" % (colE, R2EF, colE, R2SEM), f=F(8.5, False, DOUX), nf=EURS, al=D_)
for c in range(2, 11):
    wp.cell(R2MC, c).border = Border(top=sd(GRIS), bottom=sd(GRIS))
    wp.cell(R2SEM, c).border = Border(bottom=sd(GRIS))
    wp.cell(R2EF, c).border = Border(top=sd(INK), bottom=sd(INK, "double"))
pp(R2EC + 2, 2, "Le rapport au coût complet annonce une marge quasi nulle sur ces filières. "
                "La fermer ne fait pourtant pas gagner cette marge : elle fait perdre sa contribution, "
                "parce que les permanents, les murs, la marque et le siège restent — et se réallouent sur les classes qui restent.",
   f=F(8.5, False, DOUX), al=ind(0))

# =============================================================================
wb._sheets = [wb["Simulation"], wb["Le piège du coût complet"], wd, wl]
for s in wb:
    s.sheet_properties.tabColor = AZUR
wb.save(OUT)
print("écrit :", OUT)
