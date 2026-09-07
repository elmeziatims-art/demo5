#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_moteur_masque.py — le bloc (1) du moteur, restitue contre calcule.

DEUX ONGLETS.

  « Le moteur »        deux tableaux empiles sur les memes quatorze campus :
                       celui du haut est ce que V_MOTEUR_CAL RESTITUE, celui du
                       bas ce que le masque CALCULE. Chaque formule du bas
                       pointe une cellule du haut -- on clique, on voit d'ou
                       ca vient.

  « Le cout variable » la justification, parce que la question tombera : un
                       cout par eleve ne peut pas etre unique.

=============================================================================
POURQUOI LE COUT VARIABLE N'EST PAS UN NOMBRE, ET CE QU'IL EST VRAIMENT

La comptabilite ne connait pas le programme : AW_002_000004_000001 est au grain
CAMPUS x COMPTE. Un cout variable par programme ne peut donc PAS se lire, il
doit s'allouer -- et V_ALLOCATION le fait deja, avec deux cles differentes :

    621  vacataires      cle HEURES      les heures d'une classe dependent du
                                         programme et de la modalite
    604  achats d'etudes cle EFFECTIFS   uniforme dans un campus
    6063 fournitures     cle EFFECTIFS

D'ou deux comportements opposes, et c'est tout le sujet :

    consommables   varient d'un CAMPUS a l'autre (300 ou 372 EUR) mais sont
                   uniformes A L'INTERIEUR d'un campus, par construction de la
                   cle
    vacataires     varient par PROGRAMME et par MODALITE, de 454 a 607 EUR par
                   eleve, parce que les heures varient

Cout variable moyen constate en 2026, au grain cycle x modalite :

    MAS  alternance     801 EUR/eleve      18,0 h/eleve
    BAC  alternance     864 EUR/eleve      21,0 h/eleve
    BAC  initial        945 EUR/eleve      24,1 h/eleve
    BTS  alternance   1 123 EUR/eleve      34,6 h/eleve

Un facteur 1,40 entre les extremes. UNE MOYENNE UNIQUE N'EXISTE
NULLE PART dans le reseau -- c'est une moyenne, pas une realite.

=============================================================================
MAIS CE N'EST PAS CE COUT-LA QU'IL FAUT SOUSTRAIRE

Le geste ajoute des eleves dans des classes QUI EXISTENT DEJA. Le vacataire de
ces classes est deja paye : il ne coute pas un euro de plus. Le cout marginal
d'un eleve de plus n'est donc PAS le cout moyen.

    tant qu'il reste une place        les consommables seuls
                                      300 ou 372 EUR selon le campus

    quand la classe est pleine        + la quote-part du vacataire d'une
                                      classe neuve, et LA le programme compte :
                                        BAC alternance   357 EUR/place
                                        MAS alternance   385 EUR/place
                                        BAC initial      446 EUR/place
                                        BTS alternance   555 EUR/place

    ex. MBway Paris, BAC alternance   372 + 357 =   729 EUR
        Pigier Lyon, BTS alternance   300 + 555 =   855 EUR

Le masque bascule tout seul en comparant les inscrits gagnes aux places libres.
Au niveau campus il prend la quote-part MOYENNE du campus, COUT_VACAT_N /
PLACES_N, ce qui evite un lookup par programme sans rien perdre : c'est la
composition reelle du campus qui pondere.

Le compte 6231 n'est JAMAIS dans ce cout. C'est le budget d'acquisition, deja
soustrait comme Delta budget : l'y remettre le compterait deux fois.

=============================================================================
ET LES ENSEIGNANTS PERMANENTS ? LA QUESTION TOMBE TOUJOURS

Ils sont dans le modele -- compte 6411, 3 841 070 EUR en 2026, alloues a
l'HEURE exactement comme les vacataires -- et ils pesent meme 58,6 % du cout
d'enseignement du reseau. Ils ne sont pourtant pas dans le cout marginal, et
ce n'est pas un oubli :

    un poste permanent est un ENGAGEMENT DE CAPACITE. Il est paye pareil que
    la salle contienne 24 ou 32 etudiants. Il ne varie pas avec l'eleve, il
    varie avec le NOMBRE DE POSTES -- donc par palier, et le palier suivant
    n'est pas une classe, c'est un campus.

Le vacataire est la seule ressource enseignante qui s'achete a la classe.
Accessoirement le 621 est du personnel EXTERIEUR : une facture, donc sans
charges sociales 645 en plus, contrairement au 6411.

Sur 20,6 MEUR de charges, 1,13 MEUR seulement -- 5,5 % -- bougent quand un
eleve de plus s'assoit. Tout le reste est de la capacite deja engagee : c'est
exactement ce qui rend le geste d'acquisition aussi rentable tant qu'il reste
des places.

=============================================================================
CE QUI EST LIE, ET CE QUI NE DOIT SURTOUT PAS L'ETRE

Tout ce qui se deduit est lie : l'onglet du cout ne retape aucun euro, il
pointe le tableau (1) de l'onglet « Le moteur » ; les heures et les capacites
viennent des parametres de l'onglet 3 ; le tarif horaire est calcule une fois
et pointe partout.

Une chose reste DELIBEREMENT non liee : le tableau des comptes. Il vient de la
comptabilite, la ou le tableau (1) vient de la vue. Les lier ferait disparaitre
les quatre reconciliations de l'onglet 3 -- un controle qui compare une cellule
a un lien vers elle-meme ne controle rien.
"""
import csv, math, openpyxl
from collections import defaultdict
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, FormulaRule
from openpyxl.utils import get_column_letter as GL

OUT = "MOTEUR_MASQUE.xlsx"
INK, AZUR, ROUGE, VERT = "262626", "007AC3", "E5202E", "85BC20"
PALE, GRIS = "A6D0EA", "E7E6E6"
VERT_T, ROUGE_T, OCRE_ = "5F8A17", "C41822", "B26B00"
FOND, PANEL, FILET, DOUX = "F5F6F7", "FFFFFF", "D5D7DA", "6B7075"
HM_BAS, HM_MED, HM_HAUT = "F6C9CC", "F7F7F5", "DCEBC0"
VUE, CALC, PARM = "E8F1F9", "FDF3E7", "F0EDE4"   # les trois fonds qui disent l'origine
UI = "Arial"
def F(sz=8, b=False, c=INK, i=False): return Font(name=UI, size=sz, bold=b, color=c, italic=i)
fill = lambda c: PatternFill("solid", fgColor=c)
sd = lambda c=FILET, st="thin": Side(style=st, color=c)
R = Alignment("right", vertical="center"); Cn = Alignment("center", vertical="center")
ind = lambda n=0: Alignment("left", vertical="center", indent=n)
WRAP = Alignment("center", vertical="bottom", wrap_text=True)

# ---------------------------------------------------------------- la donnee
num = lambda v: float(v.replace(",", ".")) if v else 0.0
TX = {("BAC","INIT"):600, ("BAC","ALT"):480, ("MAS","INIT"):520,
      ("MAS","ALT"):420, ("BTS","INIT"):1000, ("BTS","ALT"):700}
CAPA = {"BAC":32, "MAS":26, "BTS":30}
lire = lambda n: list(csv.DictReader(open("data/"+n, encoding="utf-8-sig"), delimiter=";"))
S, C = lire("socle_crm.csv"), lire("compta.csv")
v = defaultdict(lambda: defaultdict(float)); k = defaultdict(lambda: defaultdict(float))
prog = defaultdict(lambda: defaultdict(float))
for r in S:
    ex = int(r["EXERCICE"])
    if ex not in (2024, 2025, 2026): continue
    cyc = r["PROGRAMME"].split("_")[0]
    d = v[(r["ENTITY"], ex)]
    for a, b in (("pay","VOL_LEAD_PAY"), ("org","VOL_LEAD_ORG"), ("acq","DEPENSE_ACQ"),
                 ("mrq","DEPENSE_MARQUE"), ("new","VOL_NEW"), ("eff","VOL_EFF"),
                 ("cls","VOL_CLASS")): d[a] += num(r[b])
    d["places"] += num(r["VOL_CLASS"]) * CAPA[cyc]
    d["hrs"]    += num(r["VOL_CLASS"]) * TX[(cyc, r["MODALITE"])]
    d["ca"]     += num(r["VOL_NEW"]) * num(r["REV_STUD"]) + num(r["VOL_NEW"]) * num(r["REV_FRAIS_INS"])
    if ex == 2026:
        p = prog[(cyc, r["MODALITE"])]
        p["eff"] += num(r["VOL_EFF"]); p["hrs"] += num(r["VOL_CLASS"]) * TX[(cyc, r["MODALITE"])]
        p["ent_" + r["ENTITY"]] = 1
for r in C:
    if r["EXERCICE"] != "2026" or r["ENTITY"] == "GRP": continue
    if r["ACCOUNT"] == "621":            k[r["ENTITY"]]["vac"]  += num(r["AMOUNT"])
    if r["ACCOUNT"] == "6411":           k[r["ENTITY"]]["perm"] += num(r["AMOUNT"])
    if r["ACCOUNT"] in ("604", "6063"):  k[r["ENTITY"]]["odir"] += num(r["AMOUNT"])
# la conso par programme s'alloue LIGNE A LIGNE avec la cle EFFECTIFS : chaque
# ligne du socle porte l'effectif du programme dans SON campus, donc la somme
# des poches par programme redonne exactement le total du reseau.
for r in S:
    if int(r["EXERCICE"]) != 2026: continue
    e, cyc = r["ENTITY"], r["PROGRAMME"].split("_")[0]
    prog[(cyc, r["MODALITE"])]["conso"] += num(r["VOL_EFF"]) * k[e]["odir"] / v[(e, 2026)]["eff"]
ENTS = sorted({e for e, _ in v})
MQ = {"IPAC":"Ipac Bachelor Factory", "ISCOM":"ISCOM", "MBWAY":"MBway",
      "PIGIER":"Pigier", "TUNON":"Tunon"}
LIBC = {"IPAC_MTP":"Montpellier","IPAC_NAN":"Nantes","IPAC_REN":"Rennes",
        "ISCOM_LIL":"Lille","ISCOM_PAR":"Paris","ISCOM_TLS":"Toulouse",
        "MBWAY_BOR":"Bordeaux","MBWAY_LYO":"Lyon","MBWAY_NAN":"Nantes","MBWAY_PAR":"Paris",
        "PIGIER_BOR":"Bordeaux","PIGIER_LYO":"Lyon","TUNON_LYO":"Lyon","TUNON_PAR":"Paris"}
CYC = {"BAC": "Bachelor", "MAS": "Mastère", "BTS": "BTS"}
MOD = {"INIT": "initial", "ALT": "alternance"}
def pente(xs, ys):
    n = len(xs)
    return (n*sum(a*b for a,b in zip(xs,ys)) - sum(xs)*sum(ys)) / (n*sum(a*a for a in xs) - sum(xs)**2)
EL = {e: pente([math.log(v[(e,y)]["acq"]) for y in (2024,2025,2026)],
               [math.log(v[(e,y)]["pay"]) for y in (2024,2025,2026)]) for e in ENTS}
#  La MEME pente, cote marque. Elle existe, elle se mesure, et elle est plus
#  plate : 0,280 a 0,358 contre 0,419 a 0,591 pour l'acquisition.
EL_ORG = {e: pente([math.log(v[(e,y)]["mrq"]) for y in (2024,2025,2026)],
                   [math.log(v[(e,y)]["org"]) for y in (2024,2025,2026)]) for e in ENTS}
TARIF = sum(k[e]["vac"] for e in ENTS) / sum(v[(e,2026)]["hrs"] for e in ENTS)

# ============================================================================
#  LES DOUZE LEVIERS, RESTITUES PAR Q_HYPOTHESES
#
#  Ils ne sont plus en dur nulle part. La requete tagetik/Q_HYPOTHESES.sql les
#  rend dans une zone masquee a droite du tableau (colonnes AD..AJ), une ligne
#  par levier et les trois scenarios en colonnes. Un selecteur en haut du
#  masque designe la colonne retenue, et chaque taux du classeur est un
#  INDEX/MATCH sur cette zone.
#
#  Consequence, et c'est tout l'interet : on bouge un taux dans Tagetik, on
#  rafraichit, et les quarante nombres du classeur suivent. On bascule de
#  scenario, pareil, d'un seul clic.
#
#  Les valeurs ci-dessous ne sont qu'une AMORCE pour que le classeur vive hors
#  connexion. Elles sont les memes que celles de SEED_HYPOTHESES.sql.
# ============================================================================
HYP = [(1,  "Croissance", "HYP_ACQ_BUD",      "Variation du budget acquisition",       0.0800,  0.1500, -0.0500),
       (2,  "Croissance", "HYP_BRAND_BUD",    "Variation du budget de marque",         0.1000,  0.1500, -0.0500),
       (3,  "Croissance", "HYP_PRICE",        "Hausse tarifaire",                      0.0029,  0.0350,  0.0200),
       (4,  "Croissance", "HYP_CONV_LEAD",    "Gain conversion Lead → Candidature",    0.0100,  0.0300, -0.0100),
       (5,  "Croissance", "HYP_CONV_ADM",     "Gain conversion Admis → Inscrit",       0.0100,  0.0250, -0.0100),
       (6,  "Croissance", "HYP_PASSAGE",      "Amélioration du taux de passage",       0.0050,  0.0150, -0.0100),
       (7,  "Coûts",      "HYP_INFL_EXT",     "Inflation des charges externes",        0.0200,  0.0150,  0.0300),
       (8,  "Coûts",      "HYP_SALARY",       "Politique salariale",                   0.0250,  0.0200,  0.0300),
       (9,  "Coûts",      "HYP_FTE_PERM",     "Variation des effectifs permanents",    0.0400,  0.0300,  0.0500),
       (10, "Coûts",      "HYP_PRODUCTIVITY", "Effort de productivité",                0.0185,  0.0300,  0.0000),
       (11, "Coûts",      "HYP_STRUCT_COST",  "Variation des coûts de structure",      0.0000, -0.0300,  0.0400),
       (12, "Constante",  "HYP_FEE",          "Frais de dossier par nouvel inscrit",  90.0000, 90.0000, 90.0000)]
ZC = 30                                   # AD : premiere colonne de la zone
ZH = 3                                    # la ligne d'en-tete de la zone
ZONE = "'Le moteur'!$%s$%d:$%s$%d" % (GL(ZC + 4), ZH + 1, GL(ZC + 6), ZH + len(HYP))
ZCODE = "'Le moteur'!$%s$%d:$%s$%d" % (GL(ZC + 2), ZH + 1, GL(ZC + 2), ZH + len(HYP))
ZTETE = "'Le moteur'!$%s$%d:$%s$%d" % (GL(ZC + 4), ZH, GL(ZC + 6), ZH)
VERS = "'Le moteur'!$N$4"                 # le selecteur de scenario
def hyp(code):
    """Le taux du levier <code>, dans le scenario choisi. Deux MATCH : la ligne
    par le code, la colonne par le selecteur. Rien n'est ecrit en dur."""
    return '=INDEX({0},MATCH("{1}",{2},0),MATCH({3},{4},0))'.format(ZONE, code, ZCODE, VERS, ZTETE)

# ============================================================================
#  LE PLAN DES COMPTES : LEUR FAMILLE D'INDUCTEUR, ET LEUR PERIMETRE
#
#  Deux decoupages differents du meme P&L, et il faut les tenir tous les deux.
#
#  LA FAMILLE dit CE QUI FAIT BOUGER l'euro : l'eleve, la classe, les postes,
#  la masse, l'indexation, la decision. C'est la maille du budget.
#
#  LE PERIMETRE dit OU il est constate : campus ou siege. C'est la maille de
#  l'allocation, celle du rapport Q_RAPPORT_ALLOUE, et elle ne se superpose
#  PAS a la famille -- 6414 est une masse salariale mais il est au siege.
#
#  D'ou la regle de l'onglet 4 : les six familles ne portent que le CAMPUS, et
#  le siege sort en bloc a part. Le mettre dans une famille « indexe » ferait
#  croire qu'il s'indexe, alors qu'il se DECIDE puis se cascade (K1, K4). Et
#  c'est ce qui permet d'afficher les deux resultats que le comite attend :
#  l'EBITDA PROPRE, qui juge les campus, et l'EBITDA NET, qui est celui du
#  groupe.
# ============================================================================
CPT = [
    ("604",   "Achats d'études et supports pédagogiques",        "COST_ODIR",   "EFFECTIFS", "Variable",     "OUI", VERT_T),
    ("6063",  "Fournitures pédagogiques et administratives",     "COST_ODIR",   "EFFECTIFS", "Variable",     "OUI", VERT_T),
    ("621",   "Personnel extérieur — enseignants vacataires",    "COST_VAC",    "HEURES",    "Semi-variable","Seulement si une classe doit ouvrir", "B26B00"),
    ("6411",  "Salaires — enseignants permanents",               "COST_PERM",   "HEURES",    "Capacité",     "NON — le poste est engagé à l'année, pas à l'élève", ROUGE_T),
    ("6231",  "Annonces et insertions — budget d'acquisition",   "COST_ODIR",   "ENTRANTS",  "Levier",       "C'EST LA SAISIE — déjà soustrait comme Δ budget", AZUR),
    ("6413",  "Salaires — personnel administratif des campus",   "COST_STRUCT", "K3",        "Structure",    "NON", DOUX),
    ("645",   "Charges sociales sur les salaires",               "COST_STRUCT", "K3",        "Structure",    "NON — et 621 n'en porte pas : c'est une facture, pas une paie", DOUX),
    ("613",   "Locations immobilières des campus",               "COST_STRUCT", "K3",        "Structure",    "NON — c'est le mur qui coûte, pas l'élève", DOUX),
    ("615",   "Entretien et réparations",                        "COST_STRUCT", "K3",        "Structure",    "NON", DOUX),
    ("616",   "Primes d'assurance",                              "COST_STRUCT", "K3",        "Structure",    "NON", DOUX),
    ("625",   "Déplacements, missions et réceptions",            "COST_STRUCT", "K3",        "Structure",    "NON", DOUX),
    ("63511", "Contribution économique territoriale",            "COST_STRUCT", "K3",        "Structure",    "NON", DOUX),
    ("6236",  "Catalogues et imprimés — marketing de marque",    "COST_MARQUE", "K4",        "Siège",        "NON", DOUX),
    ("6414",  "Salaires du siège",                               "COST_HOLDING","K1",        "Siège",        "NON", DOUX),
    ("6226",  "Honoraires",                                      "COST_HOLDING","K1",        "Siège",        "NON", DOUX),
    ("626",   "Frais postaux et de télécommunications",          "COST_HOLDING","K1",        "Siège",        "NON", DOUX),
    ("6281",  "Cotisations et concours divers",                  "COST_HOLDING","K1",        "Siège",        "NON", DOUX),
    ("6331",  "Versement mobilité",                              "COST_HOLDING","K1",        "Siège",        "NON", DOUX),
    ("6333",  "Participation à la formation professionnelle",    "COST_HOLDING","K1",        "Siège",        "NON", DOUX),
    ("6811",  "Dotations aux amortissements",                    "hors modèle", "—",         "Hors EBITDA",  "NON — sous la ligne d'EBITDA", DOUX)]
MTT = defaultdict(float)
for r in C:
    if r["EXERCICE"] == "2026": MTT[r["ACCOUNT"]] += num(r["AMOUNT"])
MTT = defaultdict(float, {a: round(x, 2) for a, x in MTT.items()})
CA26 = round(sum(MTT[a] for a in ("706", "7062", "708")), 2)
LIBC_CPT = {c[0]: c[1] for c in CPT}
COUL_CPT = {c[0]: c[6] for c in CPT}
BOUGE = {c[0]: c[5] for c in CPT}

#  Les CINQ familles d'inducteur, PERIMETRE CAMPUS -- et elles suivent
#  desormais la regle de CAD_PIL, compte pour compte. C'etait la condition pour
#  tomber sur les memes chiffres que le scenario deploye. On y perd une finesse
#  (chez CAD_PIL le vacataire suit le CHIFFRE D'AFFAIRES, alors qu'il suit la
#  CLASSE dans la realite) ; on la garde en reserve, ecrite au bas de l'onglet.
FAM = [("①  Suit le CHIFFRE D'AFFAIRES", "604 + 6063 + 621",
        "le CA, moins l'effort de productivité", ["604", "6063", "621"], "VERT"),
       ("②  Suit la MASSE SALARIALE", "6411 + 6413 + 645",
        "politique salariale × effectifs permanents", ["6411", "6413", "645"], "ROUGE"),
       ("③  INDEXÉ  ·  structure de campus", "613 · 615 · 616 · 625",
        "inflation, moins l'effort, × variation de structure",
        ["613", "615", "616", "625"], "DOUX"),
       ("④  INDEXÉ  ·  impôts et taxes", "63511", "inflation, moins l'effort",
        ["63511"], "DOUX"),
       ("⑤  DÉCIDÉ", "6231", "le geste d'acquisition lui-même", ["6231"], "AZUR")]
SIEGE = ["6236", "6414", "6226", "626", "6281", "6331", "6333"]
DOTA  = "6811"
CAMPUS = [a for f in FAM for a in f[3]]

#  Le plan de lignes de l'onglet 4, calcule ici parce que les controles de
#  l'onglet 3 en ont besoin avant que l'onglet 4 ne soit ecrit.
TP = 67
PLANL = []; ROWP = {}; rr_ = TP
for lab, cl, regle, cpts, coul in FAM:
    PLANL.append(("fam", rr_, lab, cl, regle, cpts, coul)); rr_ += 1
    for a in cpts: ROWP[a] = rr_; PLANL.append(("cpt", rr_, a, coul)); rr_ += 1
R_CAMP, R_CA, R_PROPRE = rr_, rr_ + 1, rr_ + 2;  rr_ += 4
R_SIEGE_T = rr_; rr_ += 1                    # le siege, en bloc a part
for a in SIEGE: ROWP[a] = rr_; PLANL.append(("sie", rr_, a, "DOUX")); rr_ += 1
R_SIEGE, R_NET, R_MARGE = rr_, rr_ + 2, rr_ + 3; rr_ += 5
R_DOTA = rr_; ROWP[DOTA] = R_DOTA            # les dotations, sous la ligne
R_FIN = rr_ + 3

# ============================================================================
#  ONGLET 1 — LE MOTEUR
#
#  L'ORDRE DE LECTURE, ET C'EST LE SUJET.
#
#  L'instinct est de raconter CA, puis cout, puis EBITDA -- l'ordre causal.
#  C'est le mauvais ordre en comite, pour une raison precise : il fait du cout
#  une OBJECTION au lieu d'un ARGUMENT. On annonce 205 651 EUR de chiffre
#  d'affaires, la salle pense "oui mais ca coute combien", on repond, et on a
#  depense son credit a se defendre au lieu de convaincre.
#
#  L'ordre juste est LE COMPTE DE RESULTAT DU GESTE, quatre nombres sur une
#  ligne : je depense, j'encaisse, les servir coute, il me reste. Le cout est
#  DEDANS, pas en reponse.
#
#  Puis la question que le DAF pose ensuite -- jusqu'ou ? -- et la reponse
#  honnete n'est pas economique mais PHYSIQUE : 974 places libres.
# ============================================================================
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Le moteur"
NC = 27
ws.sheet_view.showGridLines = False
for r in range(1, 76):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(FOND)
for r in (1, 2):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(INK)
for c in range(1, NC + 1): ws.cell(3, c).fill = fill(AZUR)
ws.cell(1, 2, "EDUSERVICES · le moteur d'acquisition").font = F(7.5, False, PALE)
ws.cell(1, 2).alignment = ind(0)
ws.cell(2, 2, "LE MOTEUR D'ACQUISITION  —  l'effet d'un euro de plus, campus par campus").font = F(14, True, "FFFFFF")
ws.cell(2, 2).alignment = ind(0)
ws.column_dimensions["A"].width = 2.4
ws.column_dimensions["B"].width = 21; ws.column_dimensions["C"].width = 13
for c in range(4, NC + 1): ws.column_dimensions[GL(c)].width = 11.5
for r, h in ((1,14),(2,24),(3,3),(4,22),(5,8),(6,24),(7,8),(8,3),(9,12),(10,28),(11,14),
             (12,8),(13,20),(14,16),(15,8),(16,3),(17,12),(18,28),(19,14),
             (20,8),(21,20),(22,14)): ws.row_dimensions[r].height = h

T1, T2 = 24, 46                          # les deux lignes d'en-tete
NL = len(ENTS); RT1 = T1 + NL + 1; RT2 = T2 + NL + 1

# ---- LA ZONE D'HYPOTHESES, restituee et masquee ---------------------------
#  Colonnes AD..AJ, repliees. C'est la sortie de Q_HYPOTHESES.sql, collee telle
#  quelle. Personne ne la regarde ; tout le classeur la lit.
from openpyxl.worksheet.datavalidation import DataValidation
#  ELLE RESTE VISIBLE. On ne peut pas cabler une zone qu'on ne voit pas : elle
#  est groupee, pas masquee. Un clic sur le « − » de la marge la replie le jour
#  de la demo, un clic sur le « + » la rouvre.
ws.cell(1, ZC, "LA ZONE D'HYPOTHÈSES  ·  collez ici la sortie de Q_HYPOTHESES.sql").font = F(9, True, AZUR)
ws.cell(1, ZC).alignment = ind(0)
ws.cell(2, ZC, "Tout le classeur la lit. Repliez-la d'un clic sur le « − » de la marge quand vous présentez.")
ws.cell(2, ZC).font = F(7.5, False, DOUX, True); ws.cell(2, ZC).alignment = ind(0)
for i, h in enumerate(["Ordre", "Famille", "Code", "Libellé", "Cadrage", "Optimiste", "Prudent"]):
    x = ws.cell(ZH, ZC + i, h); x.font = F(8, True, INK); x.fill = fill(GRIS)
    x.border = Border(bottom=sd(INK))
for j, ligne_ in enumerate(HYP):
    for i, val in enumerate(ligne_):
        x = ws.cell(ZH + 1 + j, ZC + i, val); x.fill = fill(VUE); x.font = F(8, False, INK)
        x.alignment = ind(0) if i in (1, 2, 3) else R
        x.number_format = '0' if i == 0 else ('+0.00%;-0.00%' if i > 3 and ligne_[2] != "HYP_FEE"
                                              else ('#,##0" €"' if i > 3 else 'General'))
for c in range(ZC, ZC + 7):
    ws.column_dimensions[GL(c)].width = 22 if c == ZC + 3 else 13
    ws.column_dimensions[GL(c)].outlineLevel = 1

# ---- 4. LE GESTE : DEUX budgets, donc DEUX saisies ------------------------
#  Il n'y en avait qu'une, et c'etait un trou : on pilotait l'acquisition
#  (434 174 EUR) sans jamais toucher a la marque (676 344 EUR), soit 56 % de
#  plus. Les deux leviers sont maintenant a l'ecran, cote a cote.
for c in range(2, NC + 1):
    x = ws.cell(4, c); x.fill = fill(FOND); x.border = Border(bottom=sd(FILET))
ws.cell(4, 2, "LE GESTE  ·  dicté par le scénario").font = F(7.5, True, DOUX)
ws.cell(4, 2).alignment = ind(0)
#  Les deux Δ ne se saisissent plus : ils viennent de la zone d'hypotheses. Le
#  seul geste du classeur, c'est le SELECTEUR -- un clic qui deplace quarante
#  nombres, et qui reste coherent avec ce qui est dans Tagetik.
for col_, lab_, code_ in ((4, "Δ budget d'acquisition", "HYP_ACQ_BUD"),
                          (8, "Δ budget de marque", "HYP_BRAND_BUD")):
    ws.cell(4, col_, lab_).font = F(7.5, True, DOUX); ws.cell(4, col_).alignment = R
    g_ = ws.cell(4, col_ + 2, hyp(code_)); g_.fill = fill(PANEL); g_.font = F(11, True, AZUR)
    g_.alignment = Cn; g_.border = Border(*[sd(AZUR)] * 4)
    g_.number_format = '+0.0%;-0.0%;"—"'
ws.cell(4, 12, "SCÉNARIO").font = F(7.5, True, DOUX); ws.cell(4, 12).alignment = R
sel = ws.cell(4, 14, "Cadrage"); sel.fill = fill(PARM); sel.font = F(11, True, OCRE_)
sel.alignment = Cn; sel.border = Border(*[sd(OCRE_)] * 4)
dv = DataValidation(type="list", formula1='"Cadrage,Optimiste,Prudent"', allow_blank=False)
dv.prompt = "Il fixe les douze leviers d'un seul coup."; dv.promptTitle = "Scénario"
ws.add_data_validation(dv); dv.add(sel)
ws.cell(4, 16, "un clic ici déplace tout le classeur").font = F(7, False, DOUX, True)
ws.cell(4, 16).alignment = ind(0)

# ---- 6. LA PHRASE ---------------------------------------------------------
ws.cell(6, 2, '="Je dépense "&TEXT(H{0},"#,##0 €")&".   J\'encaisse "&TEXT(J{0},"#,##0 €")'
              '&".   Les servir coûte "&TEXT(I{0}*K{0},"#,##0 €")&".   Il me reste "'
              '&TEXT(L{0},"#,##0 €")&"."'.format(RT2)).font = F(13, True, INK)
ws.cell(6, 2).alignment = ind(0)

# ---- 16-19. LE FACE-A-FACE : deux leviers, deux rendements ----------------
#  C'est la ligne que le comite retient. Le meme modele, applique aux deux
#  budgets, et le verdict par euro depense. La reserve est ecrite dessous,
#  parce qu'elle doit venir de nous et pas de la salle.
DUEL = [(2,  "L'EURO D'ACQUISITION", '=IFERROR(J{0}/H{0},0)'.format(RT2), '0.00" €"', VERT_T,
         "de chiffre d'affaires pour un euro dépensé"),
        (8,  "L'EURO DE MARQUE",     '=IFERROR(P{0}/N{0},0)'.format(RT2), '0.00" €"', ROUGE_T,
         "de chiffre d'affaires pour un euro dépensé"),
        (14, "LE RAPPORT",           '=IFERROR(R{0},0)'.format(RT2), '0.0"×"', AZUR,
         "et pourtant le budget de marque est 56 % plus gros")]
for col, lab, formule, nf_, coul, note in DUEL:
    for c in range(col, col + 6):
        ws.cell(16, c).fill = fill(AZUR if col == 14 else GRIS)
        ws.cell(17, c).fill = fill(PANEL); ws.cell(18, c).fill = fill(PANEL)
        x = ws.cell(19, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    a = ws.cell(17, col, lab); a.font = F(7, True, INK); a.alignment = ind(1)
    x = ws.cell(18, col, formule); x.font = F(18, False, coul); x.alignment = ind(1)
    x.number_format = nf_
    n = ws.cell(19, col, note); n.font = F(6.5, False, DOUX, True); n.alignment = ind(1)
ws.cell(20, 2, "À horizon un an, et à effort relatif égal. La marque se juge sur trois ans : une "
               "régression sur trois exercices ne capte que l'effet de l'année. La conclusion "
               "défendable n'est pas « coupez la marque », c'est « si elle rapporte à trois ans, "
               "il faut le mesurer, pas le supposer ».")
ws.cell(20, 2).font = F(7.5, False, DOUX, True); ws.cell(20, 2).alignment = ind(0)

# ---- 9-11. LE COMPTE DE RESULTAT DU GESTE, quatre blocs -------------------
BLOCS = [(2,  "JE DÉPENSE",       "=H%d" % RT2, '#,##0" €"', ROUGE_T, "le Δ appliqué au budget 2026"),
         (5,  "J'ENCAISSE",       "=J%d" % RT2, '#,##0" €"', INK,     "les inscrits gagnés × le CA par inscrit"),
         (8,  "LES SERVIR COÛTE", '=I{0}*K{0}'.format(RT2), '#,##0" €"', ROUGE_T,
              "consommables, et vacataire si une classe doit ouvrir"),
         (11, "IL ME RESTE",      "=L%d" % RT2, '#,##0" €"', VERT_T,  "d'EBITDA en plus, première année"),
         (14, "PAR EURO INVESTI", '=IFERROR(L{0}/H{0},0)'.format(RT2), '0.00" €"', AZUR,
              "d'EBITDA pour un euro d'acquisition")]
for col, lab, formule, coul, note in [(b[0], b[1], b[2], b[4], b[5]) for b in BLOCS]:
    for c in (col, col + 1, col + 2):
        ws.cell(8, c).fill = fill(AZUR if lab == "IL ME RESTE" else GRIS)
        ws.cell(9, c).fill = fill(PANEL); ws.cell(10, c).fill = fill(PANEL)
        x = ws.cell(11, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    a = ws.cell(9, col, lab)
    a.font = F(7, True, "262626" if lab != "IL ME RESTE" else INK); a.alignment = ind(1)
    x = ws.cell(10, col, formule); x.font = F(18, False, coul); x.alignment = ind(1)
    x.number_format = [b[3] for b in BLOCS if b[1] == lab][0]
    n = ws.cell(11, col, note); n.font = F(6.5, False, DOUX, True); n.alignment = ind(1)

# ---- 13-14. JUSQU'OU : la borne est physique, pas economique --------------
for c in range(2, NC + 1):
    x = ws.cell(13, c); x.fill = fill(PANEL); x.border = Border(top=sd(FILET))
    ws.cell(14, c).fill = fill(PANEL); ws.cell(14, c).border = Border(bottom=sd(FILET))
ws.cell(13, 2, '="JUSQU\'OÙ ?   Le geste gagne "&TEXT(I{0},"#,##0")&" inscrits pour "'
               '&TEXT(G{0},"#,##0")&" places libres dans le réseau, soit "'
               '&TEXT(I{0}/G{0},"0.0%")&" de la capacité disponible."'.format(RT2))
ws.cell(13, 2).font = F(10, True, INK); ws.cell(13, 2).alignment = ind(1)
ws.cell(14, 2, "La limite n'est pas économique — l'euro d'acquisition reste rentable très loin — "
               "elle est PHYSIQUE. Le modèle ne compte que le vacataire d'une classe qui ouvre ; "
               "il ne dit rien du jour où il faudrait un campus de plus.")
ws.cell(14, 2).font = F(7.5, False, DOUX, True); ws.cell(14, 2).alignment = ind(1)

# ---- 17-34. TABLEAU (1) : CE QUE LA VUE RESTITUE --------------------------
# Aucune formule ici. Ce sont les colonnes de V_MOTEUR_CAL, telles quelles.
ws.cell(21, 2, "①  CE QUI VIENT DE LA BASE  ·  une ligne par campus, aucun calcul")
ws.cell(21, 2).font = F(10, True, AZUR); ws.cell(21, 2).alignment = ind(0)
ws.cell(22, 2, "Ces vingt-six colonnes sortent de la base. Elles sont additives : on peut les sommer, "
               "les filtrer, les remonter à la marque — rien n'y est un ratio.")
ws.cell(22, 2).font = F(7.5, False, DOUX, True); ws.cell(22, 2).alignment = ind(0)

#  L'ordre des colonnes n'est pas decoratif : les deux leviers sont poses en
#  miroir -- trois annees de leads, trois annees de budget, une pente -- pour
#  qu'on voie du premier coup d'oeil que la MEME mesure a ete faite des deux
#  cotes. Les millesimes 2024 et 2025 sont groupes et replies : ils prouvent
#  la pente, ils n'ont pas a encombrer l'ecran.
H1 = ["Marque", "Campus",
      "Leads payants 2024", "Leads payants 2025", "Leads payants 2026",
      "Budget acq. 2024", "Budget acq. 2025", "Budget acq. 2026", "Élasticité payante",
      "Leads organiques 2024", "Leads organiques 2025", "Leads organiques 2026",
      "Budget marque 2024", "Budget marque 2025", "Budget marque 2026", "Élasticité organique",
      "Leads totaux 2026", "Inscrits 2026", "CA nouveaux 2026", "Effectifs 2026",
      "Places 2026", "Classes 2026", "Heures d'enseignement 2026", "Consommables 604+6063",
      "Vacataires 621", "Enseignants permanents 6411"]
NB1 = ['General', 'General', '#,##0', '#,##0', '#,##0',
       '#,##0" €"', '#,##0" €"', '#,##0" €"', '0.000',
       '#,##0', '#,##0', '#,##0',
       '#,##0" €"', '#,##0" €"', '#,##0" €"', '0.000',
       '#,##0', '#,##0', '#,##0" €"', '#,##0', '#,##0', '#,##0', '#,##0" h"', '#,##0" €"',
       '#,##0" €"', '#,##0" €"']
HIST = [2, 3, 5, 6, 9, 10, 12, 13]     # les millesimes 2024/2025 : D E G H K L N O
#  (indices dans H1 ; la colonne du classeur vaut 2 + indice)
for i, h in enumerate(H1):
    x = ws.cell(T1, 2 + i, h); x.font = F(8, True, INK)
    x.alignment = ind(0) if i < 2 else WRAP
    x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
ws.row_dimensions[T1].height = 34


#  L'elasticite n'est plus un nombre pose : c'est LA REGRESSION, ecrite dans la
#  cellule. Meme formule que la vue -- pente des moindres carres en log-log sur
#  les trois millesimes -- mais en Excel, sans plage matricielle, donc lisible
#  et cliquable. LN et non LOG : le LOG() de T-SQL est le neperien.
def regression(r, cx, cy):
    """pente = ( n·Sxy − Sx·Sy ) / ( n·Sx² − (Sx)² ),  x = LN(budget), y = LN(leads)"""
    X = ["LN(%s%d)" % (c, r) for c in cx]; Yy = ["LN(%s%d)" % (c, r) for c in cy]
    sxy = "+".join("%s*%s" % (a, b) for a, b in zip(X, Yy))
    sx, sy = "+".join(X), "+".join(Yy)
    sx2 = "+".join("%s^2" % a for a in X)
    return "=(3*({0})-({1})*({2}))/(3*({3})-({1})^2)".format(sxy, sx, sy, sx2)

marque_vue = None
for j, e in enumerate(ENTS):
    r = T1 + 1 + j; d24, d25, d26 = (v[(e, y)] for y in (2024, 2025, 2026))
    mq = e.split("_")[0]
    vals = [MQ[mq] if mq != marque_vue else "", LIBC[e],
            d24["pay"], d25["pay"], d26["pay"], d24["acq"], d25["acq"], d26["acq"],
            regression(r, "GHI", "DEF"),
            d24["org"], d25["org"], d26["org"], d24["mrq"], d25["mrq"], d26["mrq"],
            regression(r, "NOP", "KLM"),
            d26["pay"] + d26["org"], d26["new"], d26["ca"], d26["eff"],
            d26["places"], d26["cls"], d26["hrs"], k[e]["odir"], k[e]["vac"], k[e]["perm"]]
    marque_vue = mq
    for i, val in enumerate(vals):
        x = ws.cell(r, 2 + i, val); x.fill = fill(VUE); x.number_format = NB1[i]
        x.font = F(8, i == 0, INK if i else AZUR); x.alignment = ind(0) if i < 2 else R
        if i in (8, 15): x.font = F(8, True, "B26B00")
        x.border = Border(bottom=sd("EAF0F6"))

for i in range(26):
    c = 2 + i; x = ws.cell(RT1, c)
    x.fill = fill(GRIS); x.font = F(8, True, INK); x.number_format = NB1[i]
    x.border = Border(top=sd(INK), bottom=sd(INK))
    x.alignment = ind(0) if i < 2 else R
    if i == 0: x.value = "GROUPE"
    elif i == 1: x.value = "14 campus"
    elif i in (8, 15): x.value = "—"; x.alignment = R   # une élasticité ne se somme pas
    else: x.value = "=SUM({0}{1}:{0}{2})".format(GL(c), T1 + 1, RT1 - 1)

# ---- 41-58. TABLEAU (2) : CE QUE LE MASQUE CALCULE -------------------------
# Chaque cellule pointe le tableau du dessus. On clique, on remonte à la vue.
ws.cell(43, 2, "②  CE QUE LE MOTEUR CALCULE  ·  chaque formule pointe une cellule du tableau ①")
ws.cell(43, 2).font = F(10, True, "B26B00"); ws.cell(43, 2).alignment = ind(0)
ws.cell(44, 2, "Rien n'est stocké ici. Cliquez une cellule : la formule remonte au tableau du dessus, "
               "et les deux seules saisies sont F4 et J4 — les deux Δ budget.")
ws.cell(44, 2).font = F(7.5, False, DOUX, True); ws.cell(44, 2).alignment = ind(0)

H2 = ["Marque", "Campus", "Conversion lead → inscrit", "CA par inscrit",
      "Consommables / élève", "Places libres",
      "Δ budget acquisition", "Inscrits gagnés · acquisition", "CA gagné · acquisition",
      "Coût marginal / élève", "EBITDA gagné · acquisition", "CAC marginal · acquisition",
      "Δ budget marque", "Inscrits gagnés · marque", "CA gagné · marque",
      "CAC marginal · marque", "L'euro d'acquisition vaut"]
NB2 = ['General', 'General', '0.0%', '#,##0" €"', '#,##0" €"', '#,##0',
       '#,##0" €"', '#,##0.0', '#,##0" €"', '#,##0" €"', '#,##0" €"', '#,##0" €"',
       '#,##0" €"', '#,##0.0', '#,##0" €"', '#,##0" €"', '0.0"× l\'euro de marque"']
for i, h in enumerate(H2):
    x = ws.cell(T2, 2 + i, h); x.font = F(8, True, INK)
    x.alignment = ind(0) if i < 2 else WRAP
    x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
ws.row_dimensions[T2].height = 34
for r_, h_ in ((21,20),(22,14),(43,20),(44,14)): ws.row_dimensions[r_].height = h_

def ligne2(r2, r1):
    """Les quinze formules du masque -- six communes, cinq par levier.

    Les deux leviers sont ecrits EXACTEMENT de la meme facon : budget x Delta,
    leads x l'effet d'elasticite, converti au taux du campus, valorise au CA
    par inscrit. C'est ce qui rend la comparaison honnete : ce n'est pas deux
    modeles qu'on compare, c'est le meme, applique a deux budgets.
    """
    return {
        4:  "=IFERROR(S{0}/R{0},0)".format(r1),                          # conversion
        5:  "=IFERROR(T{0}/S{0},0)".format(r1),                          # CA par inscrit
        6:  "=IFERROR(Y{0}/U{0},0)".format(r1),                          # consommables/eleve
        7:  "=V{0}-U{0}".format(r1),                                     # places libres
        8:  "=I{0}*$F$4".format(r1),                                     # Delta budget acquisition
        9:  "=F{0}*((1+$F$4)^J{0}-1)*D{1}".format(r1, r2),               # inscrits gagnes acq
        10: "=I{0}*E{0}".format(r2),                                     # CA gagne acq
        11: "=IF(I{0}<=G{0},F{0},F{0}+Z{1}/V{1})".format(r2, r1),        # cout marginal
        12: "=J{0}-H{0}-I{0}*K{0}".format(r2),                           # EBITDA gagne acq
        13: "=IFERROR(H{0}/I{0},0)".format(r2),                          # CAC marginal acq
        14: "=P{0}*$J$4".format(r1),                                     # Delta budget marque
        15: "=M{0}*((1+$J$4)^Q{0}-1)*D{1}".format(r1, r2),               # inscrits gagnes marque
        16: "=O{0}*E{0}".format(r2),                                     # CA gagne marque
        17: "=IFERROR(N{0}/O{0},0)".format(r2),                          # CAC marginal marque
        18: "=IFERROR((J{0}/H{0})/(P{0}/N{0}),0)".format(r2)}            # le rapport

marque_calc = None
for j, e in enumerate(ENTS):
    r2, r1 = T2 + 1 + j, T1 + 1 + j; mq = e.split("_")[0]
    ws.cell(r2, 2, MQ[mq] if mq != marque_calc else ""); marque_calc = mq
    ws.cell(r2, 3, "=C%d" % r1)
    for c, f in ligne2(r2, r1).items(): ws.cell(r2, c, f)
    for i in range(17):
        x = ws.cell(r2, 2 + i); x.fill = fill(CALC); x.number_format = NB2[i]
        x.font = F(8, i == 0, INK); x.alignment = ind(0) if i < 2 else R
        x.border = Border(bottom=sd("F5E6D2"))
    ws.cell(r2, 18).font = F(8, True, AZUR)

for c, f in ligne2(RT2, RT1).items(): ws.cell(RT2, c, f)
# Au groupe, ce qui est un VOLUME ou un EURO se somme ; ce qui est un RAPPORT
# se refait sur les sommes, jamais en moyennant les taux des campus.
ws.cell(RT2, 2, "GROUPE"); ws.cell(RT2, 3, "14 campus")
for c in (7, 8, 9, 10, 12, 14, 15, 16):
    ws.cell(RT2, c, "=SUM({0}{1}:{0}{2})".format(GL(c), T2 + 1, RT2 - 1))
ws.cell(RT2, 11, "=IFERROR(SUMPRODUCT(I{1}:I{2},K{1}:K{2})/I{0},0)".format(RT2, T2 + 1, RT2 - 1))
for i in range(17):
    x = ws.cell(RT2, 2 + i); x.fill = fill(GRIS); x.font = F(8, True, INK)
    x.number_format = NB2[i]; x.alignment = ind(0) if i < 2 else R
    x.border = Border(top=sd(INK), bottom=sd(INK))

# heatmap sur le CAC marginal : le vert va au CAC BAS, un CAC eleve n'est pas une performance
ws.conditional_formatting.add("M{0}:M{1}".format(T2 + 1, RT2 - 1),
    ColorScaleRule(start_type="min", start_color=HM_HAUT,
                   mid_type="percentile", mid_value=50, mid_color=HM_MED,
                   end_type="max", end_color=HM_BAS))
# la classe qui doit ouvrir : le cout marginal decroche des consommables seuls
ws.conditional_formatting.add("K{0}:K{1}".format(T2 + 1, RT2 - 1),
    CellIsRule(operator="greaterThan", formula=["F%d" % (T2 + 1)],
               font=Font(name=UI, size=8, bold=True, color=ROUGE_T)))
# le CAC marginal cote marque : meme echelle de lecture, le vert au CAC bas
ws.conditional_formatting.add("Q{0}:Q{1}".format(T2 + 1, RT2 - 1),
    ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                   mid_color=HM_MED, end_type="max", end_color=HM_BAS))

# ---- les millesimes 2024/2025 : groupes et replies -----------------------
#  Ils PROUVENT la pente, ils n'ont pas a encombrer l'ecran. Un « + » en haut
#  de la feuille les rouvre.
ws.sheet_properties.outlinePr.summaryRight = True
for i in HIST:
    d_ = ws.column_dimensions[GL(2 + i)]; d_.outlineLevel = 1; d_.hidden = True

ws.cell(RT2 + 2, 2, "Lecture des fonds :  bleu = restitué par la vue,  ocre = calculé par le masque,  sable = paramètre du modèle.  Un coût marginal en rouge signale un campus où la classe doit ouvrir.")
ws.cell(RT2 + 2, 2).font = F(7.5, False, DOUX, True); ws.cell(RT2 + 2, 2).alignment = ind(0)
# on fige les deux colonnes d'identite, pas les lignes : les deux tableaux ont chacun son en-tete
ws.freeze_panes = "D1"


# ============================================================================
#  LES DEUX AUTRES ONGLETS
#
#  Ils sont crees maintenant, dans l'ordre d'affichage, mais ecrits dans un
#  autre ordre : l'onglet 3 porte les PARAMETRES du modele (heures par classe,
#  capacite), et l'onglet 2 les pointe. On remplit donc les parametres d'abord.
# ============================================================================
w2 = wb.create_sheet("Le coût variable")
w3 = wb.create_sheet("Intégration & contrôles")

def bandeau(w, nc, titre_, nlig=82):
    w.sheet_view.showGridLines = False
    for r in range(1, nlig):
        for c in range(1, nc + 1): w.cell(r, c).fill = fill(FOND)
    for r in (1, 2):
        for c in range(1, nc + 1): w.cell(r, c).fill = fill(INK)
    for c in range(1, nc + 1): w.cell(3, c).fill = fill(AZUR)
    w.cell(1, 2, "EDUSERVICES · le moteur d'acquisition").font = F(7.5, False, PALE)
    w.cell(1, 2).alignment = ind(0)
    w.cell(2, 2, titre_).font = F(14, True, "FFFFFF"); w.cell(2, 2).alignment = ind(0)
    for r, h in ((1, 14), (2, 24), (3, 3)): w.row_dimensions[r].height = h

def titre(w, r, txt, sous, coul=AZUR):
    w.cell(r, 2, txt).font = F(10, True, coul); w.cell(r, 2).alignment = ind(0)
    w.cell(r + 1, 2, sous).font = F(7.5, False, DOUX, True); w.cell(r + 1, 2).alignment = ind(0)
    w.row_dimensions[r].height = 20; w.row_dimensions[r + 1].height = 14

def entete(w, r, libelles, haut=30, col0=2):
    for i, h in enumerate(libelles):
        x = w.cell(r, col0 + i, h); x.font = F(8, True, INK)
        x.alignment = ind(0) if i == 0 else WRAP
        x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
    w.row_dimensions[r].height = haut

def ligne(w, r, vals, nb, fond=PANEL, gras=False, trait="EDEEF0", col0=2, gauche=()):
    for i, val in enumerate(vals):
        x = w.cell(r, col0 + i, val); x.fill = fill(fond); x.number_format = nb[i]
        x.font = F(8, gras or i == 0, INK)
        x.alignment = ind(0) if (i == 0 or i in gauche) else R
        x.border = Border(bottom=sd(trait))

# ============================================================================
#  ONGLET 3 (a) — LES PARAMETRES DU MODELE
#
#  Ce sont les SEULES hypotheses du classeur. Elles ne sortent d'aucune vue :
#  elles decrivent la maquette pedagogique. On les isole, on les colore, et
#  l'onglet 2 les pointe -- de sorte qu'un CFO qui conteste « 480 heures pour
#  un Bachelor en alternance » n'a qu'une cellule a changer.
# ============================================================================
NC3 = 12
bandeau(w3, NC3, "INTÉGRATION TAGETIK  &  CONTRÔLES", 80)
w3.column_dimensions["A"].width = 2.4; w3.column_dimensions["B"].width = 34
for c, wd in ((3, 14), (4, 14), (5, 18), (6, 16), (7, 16), (8, 16), (9, 16),
              (10, 16), (11, 16), (12, 16)):
    w3.column_dimensions[GL(c)].width = wd

titre(w3, 5, "ⓐ  Les paramètres du modèle  ·  les seules hypothèses du classeur",
      "Elles ne sortent d'aucune vue : elles décrivent la maquette pédagogique. Fond sable = "
      "hypothèse. Changer une cellule ici change tout l'onglet « Le coût variable ».")
entete(w3, 8, ["Programme", "Heures / classe", "Capacité de la classe", "Origine"], 28)
NBQ = ['General', '#,##0" h"', '#,##0', 'General']
PARAM_ROW = {}
for j, key in enumerate(sorted(TX, key=lambda t: (t[0], t[1]))):
    r = 9 + j; PARAM_ROW[key] = r
    ligne(w3, r, ["%s · %s" % (CYC[key[0]], MOD[key[1]]), TX[key], CAPA[key[0]],
                  "maquette pédagogique" + ("" if key in prog else "  (programme absent du réseau en 2026)")],
          NBQ, fond=PARM, gauche=(3,))
    if key not in prog:
        for c in range(2, 6): w3.cell(r, c).font = F(8, c == 2, DOUX, True)
PR_FIN = 9 + len(TX)
w3.cell(PR_FIN + 1, 2, "Le tarif horaire, lui, n'est PAS un paramètre : il se déduit du réel, "
                       "compte 621 ÷ heures d'enseignement. Il vit dans l'onglet « Le coût variable ».")
w3.cell(PR_FIN + 1, 2).font = F(7.5, False, DOUX, True); w3.cell(PR_FIN + 1, 2).alignment = ind(0)

# ============================================================================
#  ONGLET 2 — LE COUT VARIABLE
#
#  Tout ce qui peut etre lie l'est. Aucun montant n'est retape : les euros
#  viennent du tableau (1) de l'onglet « Le moteur », les heures et capacites
#  des parametres de l'onglet 3. On clique n'importe quelle cellule chiffree,
#  on remonte a sa source.
#
#  L'onglet repond a trois questions, dans cet ordre :
#     (1) pourquoi un cout par eleve ne peut pas etre unique
#     (2) combien il vaut en moyenne -- et pourquoi la moyenne ne sert a rien
#     (3) ce que le masque soustrait vraiment, et pourquoi les permanents
#         n'y sont pas
# ============================================================================
NC2 = 14
bandeau(w2, NC2, "LE COÛT VARIABLE  —  pourquoi il ne peut pas être un nombre", 102)
w2.column_dimensions["A"].width = 2.4; w2.column_dimensions["B"].width = 34
for c, wd in ((3, 14), (4, 15), (5, 14), (6, 15), (7, 14), (8, 22), (9, 14), (10, 15), (11, 14),
              (12, 14), (13, 14), (14, 14)):
    w2.column_dimensions[GL(c)].width = wd
M, T = "'Le moteur'!", "'Intégration & contrôles'!"      # les deux sources

w2.cell(5, 2, "La comptabilité ne connaît pas le programme.").font = F(12, True, INK)
w2.cell(5, 2).alignment = ind(0); w2.row_dimensions[5].height = 22
w2.cell(6, 2, "La comptabilité est tenue au grain CAMPUS × COMPTE. Un coût par élève et par programme "
              "ne se lit donc pas : il s'alloue. V_ALLOCATION le fait déjà, avec des clés différentes "
              "selon la nature de la charge — et c'est de là que vient tout le reste.")
w2.cell(6, 2).font = F(8, False, DOUX, True); w2.cell(6, 2).alignment = ind(0)
w2.row_dimensions[6].height = 16

# ---- (1) TROIS POCHES, TROIS COMPORTEMENTS --------------------------------
titre(w2, 8, "①  Trois poches d'enseignement, trois comportements",
      "Le même euro de charge ne se répartit pas de la même façon, et surtout ne réagit pas de la "
      "même façon quand un élève de plus arrive.")
entete(w2, 11, ["Poche", "Comptes", "Montant 2026", "Clé d'allocation", "Varie avec",
                "Comportement", "Bouge si un élève de plus arrive ?"], 30)
NBP = ['General', 'General', '#,##0" €"', 'General', 'General', 'General', 'General']
POCHES = [("Consommables", "604 + 6063", "=%sR34" % M, "EFFECTIFS", "le campus",
           "VARIABLE", "OUI — c'est le seul euro qui suit vraiment l'élève", VERT_T),
          ("Vacataires", "621", "=%sS34" % M, "HEURES", "le programme",
           "SEMI-VARIABLE", "Seulement si la classe doit ouvrir", "B26B00"),
          ("Enseignants permanents", "6411", "=%sT34" % M, "HEURES", "le nombre de postes",
           "CAPACITÉ", "NON — payé pareil pour 24 ou 32 élèves dans la salle", ROUGE_T)]
for i, p in enumerate(POCHES):
    ligne(w2, 12 + i, list(p[:7]), NBP, gauche=(3, 4, 5, 6))
    w2.cell(12 + i, 7).font = F(8, True, p[7]); w2.cell(12 + i, 8).font = F(8, False, p[7])
w2.cell(15, 2, "Les heures d'une classe dépendent du programme : un BTS en initial pèse 1 000 heures, "
               "un Mastère en alternance 420. La clé EFFECTIFS, elle, ne distingue rien à l'intérieur "
               "d'un campus — par construction.")
w2.cell(15, 2).font = F(7.5, False, DOUX, True); w2.cell(15, 2).alignment = ind(0)

# ---- (2) LE COUT MOYEN, par cycle x modalite ------------------------------
titre(w2, 18, "②  Le coût variable MOYEN, au grain cycle × modalité",
      "Ce que coûte un élève déjà inscrit, vacataire et consommables. Chaque ligne est une réalité du "
      "réseau ; la moyenne, elle, n'est nulle part. Le tarif horaire est déduit du réel : 621 ÷ heures.")
entete(w2, 21, ["Cycle · modalité", "Effectifs 2026", "Heures / élève", "Tarif horaire",
                "Vacataires / élève", "Consommables / élève", "Coût moyen / élève", "Écart à la moyenne"])
NB3 = ['General', '#,##0', '0.0" h"', '0.00" €"', '#,##0" €"', '#,##0" €"', '#,##0" €"', '+0.0%;-0.0%']
lignes_b = []
for key, p in sorted(prog.items(), key=lambda x: x[1]["hrs"] / x[1]["eff"]):
    lignes_b.append((key, p, p["conso"] / p["eff"]))
RB0, RBN = 22, 22 + len(lignes_b)
TARIF_CELL = "$E$%d" % RBN                       # le tarif, calcule une fois, pointe partout
for j, (key, p, conso) in enumerate(lignes_b):
    r = RB0 + j
    ligne(w2, r, ["%s · %s" % (CYC[key[0]], MOD[key[1]]), p["eff"], p["hrs"] / p["eff"],
                  "=%s" % TARIF_CELL, "=D%d*E%d" % (r, r), conso, "=F%d+G%d" % (r, r),
                  "=IFERROR(H{0}/$H${1}-1,0)".format(r, RBN)], NB3)
    for c in (6, 8): w2.cell(r, c).font = F(8, True, INK)
ligne(w2, RBN, ["MOYENNE PONDÉRÉE", "=SUM(C{0}:C{1})".format(RB0, RBN - 1),
                "=IFERROR({0}X{2}/C{1},0)".format(M, RBN, RT1), "=IFERROR({0}Z{1}/{0}X{1},0)".format(M, RT1),
                "=D%d*E%d" % (RBN, RBN),
                "=IFERROR(SUMPRODUCT(C{0}:C{1},G{0}:G{1})/C{2},0)".format(RB0, RBN - 1, RBN),
                "=F%d+G%d" % (RBN, RBN), "—"], NB3, fond=GRIS, gras=True, trait=INK)
w2.cell(RBN, 9).alignment = R
for c in (4, 5): w2.cell(RBN, c).fill = fill(GRIS)
w2.conditional_formatting.add("H{0}:H{1}".format(RB0, RBN - 1),
    ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                   mid_color=HM_MED, end_type="max", end_color=HM_BAS))
w2.cell(RBN + 2, 2, '="Un facteur "&TEXT(MAX(H{0}:H{1})/MIN(H{0}:H{1}),"0.00")&" entre les extrêmes. '
                    'Le coût variable « moyen » du réseau — "&TEXT(H{2},"#,##0 €")&" — ne décrit aucun '
                    'élève réel : il cadre, il ne décide pas."'.format(RB0, RBN - 1, RBN))
w2.cell(RBN + 2, 2).font = F(8, True, INK); w2.cell(RBN + 2, 2).alignment = ind(0)

# ---- (3) CAMPUS PAR CAMPUS, tout lie a l'onglet « Le moteur » -------------
titre(w2, 30, "③  Le coût d'enseignement campus par campus  ·  ce qui suit l'élève, ce qui suit la "
              "classe, ce qui ne bouge pas",
      "Aucun montant n'est saisi ici : chaque euro pointe le tableau ① de l'onglet « Le moteur ». "
      "La colonne « quote-part vacataire / place » est exactement le terme que le masque ajoute "
      "quand une classe doit ouvrir.")
entete(w2, 33, ["Campus", "Effectifs 2026", "Places libres", "Consommables 604+6063",
                "Consommables / élève", "Heures d'enseignement", "Vacataires 621",
                "Quote-part vacataire / place", "Permanents 6411", "Permanents / élève",
                "Croissance possible avant saturation"], 34)
NB4 = ['General', '#,##0', '#,##0', '#,##0" €"', '#,##0" €"', '#,##0" h"', '#,##0" €"',
       '#,##0" €"', '#,##0" €"', '#,##0" €"', '0.0%']
RC0 = 34
for j, e in enumerate(ENTS):
    r, r1, r2 = RC0 + j, T1 + 1 + j, T2 + 1 + j
    ligne(w2, r, ["%s %s" % (MQ[e.split("_")[0]], LIBC[e]),
                  "={0}U{1}".format(M, r1), "={0}G{1}".format(M, r2), "={0}Y{1}".format(M, r1),
                  "=IFERROR(E%d/C%d,0)" % (r, r), "={0}X{1}".format(M, r1),
                  "={0}Z{1}".format(M, r1), "=IFERROR(H{0}/{1}V{2},0)".format(r, M, r1),
                  "={0}AA{1}".format(M, r1), "=IFERROR(J%d/C%d,0)" % (r, r),
                  "=IFERROR(D%d/C%d,0)" % (r, r)], NB4)
RCN = RC0 + len(ENTS)
ligne(w2, RCN, ["GROUPE · 14 campus"] +
      ["=SUM({0}{1}:{0}{2})".format(GL(c), RC0, RCN - 1) for c in (3, 4, 5)] +
      ["=IFERROR(E{0}/C{0},0)".format(RCN)] +
      ["=SUM({0}{1}:{0}{2})".format(GL(c), RC0, RCN - 1) for c in (7, 8)] +
      ["=IFERROR(H{0}/{1}V{2},0)".format(RCN, M, RT1), "=SUM(J{0}:J{1})".format(RC0, RCN - 1),
       "=IFERROR(J{0}/C{0},0)".format(RCN),
       # la croissance possible ne se somme pas : au groupe, c'est celle du
       # PREMIER campus qui sature, pas la moyenne du reseau.
       "=MIN(L{0}:L{1})".format(RC0, RCN - 1)], NB4, fond=GRIS, gras=True, trait=INK)
for col in ("F", "I", "K"):
    w2.conditional_formatting.add("{0}{1}:{0}{2}".format(col, RC0, RCN - 1),
        ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                       mid_color=HM_MED, end_type="max", end_color=HM_BAS))
w2.cell(RCN + 1, 2, "La dernière colonne ne se somme pas : au groupe, la croissance possible est "
                    "celle du PREMIER campus qui sature, pas la moyenne du réseau.")
w2.cell(RCN + 1, 2).font = F(7.5, False, DOUX, True); w2.cell(RCN + 1, 2).alignment = ind(0)
w2.cell(RCN + 2, 2, '="Les permanents pèsent "&TEXT(J{0}/(E{0}+H{0}+J{0}),"0 %")&" du coût '
                    'd\'enseignement du réseau, et pas un euro d\'entre eux ne bouge quand un élève '
                    'de plus s\'assoit."'.format(RCN))
w2.cell(RCN + 2, 2).font = F(8, True, INK); w2.cell(RCN + 2, 2).alignment = ind(0)

# ---- (4) LE COUT MARGINAL, celui que le masque soustrait ------------------
RD = RCN + 4
titre(w2, RD, "④  Mais ce n'est pas ce coût-là que le masque soustrait",
      "Le geste ajoute des élèves dans des classes qui existent déjà. Leur vacataire est déjà payé, "
      "leur professeur permanent aussi : ils ne coûtent pas un euro de plus. Le coût MARGINAL n'est "
      "donc pas le coût moyen.", "B26B00")
for c in range(2, NC2 + 1):
    w2.cell(RD + 3, c).fill = fill(PANEL); w2.cell(RD + 3, c).border = Border(top=sd(FILET))
    w2.cell(RD + 4, c).fill = fill(PANEL)
    w2.cell(RD + 5, c).fill = fill(PANEL); w2.cell(RD + 5, c).border = Border(bottom=sd(FILET))
w2.cell(RD + 3, 2, "TANT QU'IL RESTE UNE PLACE").font = F(8, True, VERT_T)
w2.cell(RD + 3, 2).alignment = ind(0)
w2.cell(RD + 3, 4, '="les consommables seuls  —  de "&TEXT(MIN(F{0}:F{1}),"#,##0 €")&" à "'
                   '&TEXT(MAX(F{0}:F{1}),"#,##0 €")&" selon le campus"'.format(RC0, RCN - 1))
w2.cell(RD + 3, 4).font = F(8, False, INK); w2.cell(RD + 3, 4).alignment = ind(0)
w2.cell(RD + 4, 2, "QUAND LA CLASSE EST PLEINE").font = F(8, True, ROUGE_T)
w2.cell(RD + 4, 2).alignment = ind(0)
w2.cell(RD + 4, 4, "+ la quote-part du vacataire d'une classe neuve  —  et là, le programme compte")
w2.cell(RD + 4, 4).font = F(8, False, INK); w2.cell(RD + 4, 4).alignment = ind(0)
w2.cell(RD + 5, 4, "Le masque bascule seul : IF(inscrits gagnés <= places libres ; consommables ; "
                   "consommables + vacataires du campus ÷ places du campus).")
w2.cell(RD + 5, 4).font = F(7.5, False, DOUX, True); w2.cell(RD + 5, 4).alignment = ind(0)

RE = RD + 8
entete(w2, RE, ["Programme qui ouvre", "Heures / classe", "Tarif horaire", "Coût du vacataire",
                "Capacité de la classe", "Coût d'ouverture / place",
                "+ consommables ⇒ coût marginal"], 30)
NB5 = ['General', '#,##0" h"', '0.00" €"', '#,##0" €"', '#,##0', '#,##0" €"', 'General']
ouvre = sorted(lignes_b, key=lambda t: TX[t[0]] / CAPA[t[0][0]])
for j, (key, p, conso) in enumerate(ouvre):
    r, pr = RE + 1 + j, PARAM_ROW[key]
    ligne(w2, r, ["%s · %s" % (CYC[key[0]], MOD[key[1]]),
                  "={0}C{1}".format(T, pr), "=%s" % TARIF_CELL, "=C%d*D%d" % (r, r),
                  "={0}D{1}".format(T, pr), "=E%d/F%d" % (r, r),
                  '="de "&TEXT(G{0}+MIN($F${1}:$F${2}),"#,##0 €")&" à "'
                  '&TEXT(G{0}+MAX($F${1}:$F${2}),"#,##0 €")&" selon le campus"'.format(r, RC0, RCN - 1)],
          NB5, gauche=(6,))
    w2.cell(r, 7).font = F(8, True, INK); w2.cell(r, 8).font = F(8, False, DOUX, True)
REN = RE + 1 + len(ouvre)
w2.cell(REN + 1, 2, "Heures et capacités viennent de l'onglet « Intégration & contrôles » ; le tarif "
                    "horaire de la ligne MOYENNE PONDÉRÉE ci-dessus. Rien n'est saisi dans ce tableau.")
w2.cell(REN + 1, 2).font = F(7.5, False, DOUX, True); w2.cell(REN + 1, 2).alignment = ind(0)

# ---- (5) ET LES ENSEIGNANTS PERMANENTS ? ---------------------------------
#  La question qui vient toujours. La reponse tient en un paragraphe -- le
#  tableau des vingt comptes, lui, vit dans l'onglet « Budget 2027 », ou il
#  porte 2026 ET 2027 au lieu de 2026 seul. Le dupliquer ici serait entretenir
#  deux verites.
RF = REN + 3
titre(w2, RF, "⑤  Et les enseignants permanents, ils sont où ?",
      "Dans le modèle, et alloués à l'heure comme les vacataires — mais jamais dans le coût "
      "marginal.", ROUGE_T)
for c in range(2, NC2 + 1):
    w2.cell(RF + 2, c).fill = fill(PANEL); w2.cell(RF + 2, c).border = Border(top=sd(FILET))
    w2.cell(RF + 3, c).fill = fill(PANEL)
    w2.cell(RF + 4, c).fill = fill(PANEL); w2.cell(RF + 4, c).border = Border(bottom=sd(FILET))
w2.cell(RF + 2, 2, "Un professeur permanent est un ENGAGEMENT DE CAPACITÉ, pas un coût à l'élève : "
                   "il est payé pareil que la salle contienne 24 ou 32 étudiants. Il varie avec le "
                   "nombre de POSTES — donc par palier, et le palier suivant n'est pas une classe, "
                   "c'est un campus.")
w2.cell(RF + 2, 2).font = F(8, False, INK); w2.cell(RF + 2, 2).alignment = ind(0)
w2.cell(RF + 3, 2, "Le vacataire est la seule ressource enseignante qui s'achète à la classe. Et le "
                   "621 est du personnel EXTÉRIEUR : une facture, donc sans charges sociales 645 en "
                   "plus, contrairement au 6411.")
w2.cell(RF + 3, 2).font = F(8, False, INK); w2.cell(RF + 3, 2).alignment = ind(0)
w2.cell(RF + 4, 2, '="Sur "&TEXT(\'Budget 2027\'!D{0}+\'Budget 2027\'!D{1}+\'Budget 2027\'!D{2},"#,##0 €")'
                   '&" de charges, "&TEXT(\'Budget 2027\'!D{3},"#,##0 €")&" seulement bougent quand un '
                   'élève de plus s\'assoit — soit "'
                   '&TEXT(\'Budget 2027\'!D{3}/(\'Budget 2027\'!D{0}+\'Budget 2027\'!D{1}'
                   '+\'Budget 2027\'!D{2}),"0.0 %")&". Tout le reste est de la capacité déjà engagée : '
                   'c\'est ce qui rend le geste aussi rentable tant qu\'il reste des places."'
                   .format(R_CAMP, R_SIEGE, R_DOTA, TP))
w2.cell(RF + 4, 2).font = F(9, True, INK); w2.cell(RF + 4, 2).alignment = ind(0)
w2.cell(RF + 6, 2, "Le détail des vingt comptes — chacun avec son comportement et son inducteur — "
                   "est dans l'onglet « Budget 2027 ». Il n'est pas dupliqué ici.")
w2.cell(RF + 6, 2).font = F(7.5, False, DOUX, True); w2.cell(RF + 6, 2).alignment = ind(0)
CV_FIN = RF + 6


# ============================================================================
#  ONGLET 3 (b) — LE MAPPING : colonne du classeur <-> colonne de la vue
#
#  C'est la piece que reclame l'integrateur. Deux colonnes n'existent pas
#  encore dans V_MOTEUR_CAL et sont marquees comme telles : HEURES_N et
#  COUT_PERM_N. Le fichier tagetik/V_MOTEUR_CAL.sql les ajoute.
# ============================================================================
MAP = [
    ("B", "Marque",                       "MARQUE",         "dimension", "regroupement d'affichage"),
    ("C", "Campus",                       "CAMPUS",         "dimension", "libellé azienda"),
    ("D", "Leads payants 2024",           "LEAD_PAY_2024",  "mesure",    ""),
    ("E", "Leads payants 2025",           "LEAD_PAY_2025",  "mesure",    ""),
    ("F", "Leads payants 2026",           "LEAD_PAY_2026",  "mesure",    "base du geste d'acquisition"),
    ("G", "Budget acq. 2024",             "SPEND_ACQ_2024", "mesure",    ""),
    ("H", "Budget acq. 2025",             "SPEND_ACQ_2025", "mesure",    ""),
    ("I", "Budget acq. 2026",             "SPEND_ACQ_2026", "mesure",    "= compte 6231"),
    ("J", "Élasticité payante",           "ELASTICITE",     "NON additive", "régression log-log, reste au campus"),
    ("K", "Leads organiques 2024",        "LEAD_ORG_2024",  "mesure",    "À AJOUTER À LA VUE"),
    ("L", "Leads organiques 2025",        "LEAD_ORG_2025",  "mesure",    "À AJOUTER À LA VUE"),
    ("M", "Leads organiques 2026",        "LEAD_ORG_2026",  "mesure",    "À AJOUTER À LA VUE"),
    ("N", "Budget marque 2024",           "SPEND_MRQ_2024", "mesure",    "À AJOUTER À LA VUE"),
    ("O", "Budget marque 2025",           "SPEND_MRQ_2025", "mesure",    "À AJOUTER À LA VUE"),
    ("P", "Budget marque 2026",           "SPEND_MRQ_2026", "mesure",    "À AJOUTER · = compte 6236"),
    ("Q", "Élasticité organique",         "ELASTICITE_ORG", "NON additive", "À AJOUTER · même régression, côté marque"),
    ("R", "Leads totaux 2026",            "LEAD_TOT_N",     "mesure",    "dénominateur de la conversion"),
    ("S", "Inscrits 2026",                "INSCRITS_N",     "mesure",    "numérateur de la conversion"),
    ("T", "CA nouveaux 2026",             "CA_NEW_N",       "mesure",    ""),
    ("U", "Effectifs 2026",               "EFFECTIFS_N",    "mesure",    ""),
    ("V", "Places 2026",                  "PLACES_N",       "mesure",    "classes × capacité"),
    ("W", "Classes 2026",                 "CLASSES_N",      "mesure",    ""),
    ("X", "Heures d'enseignement 2026",   "HEURES_N",       "mesure",    "À AJOUTER À LA VUE"),
    ("Y", "Consommables 604+6063",        "COUT_CONSO_N",   "mesure",    ""),
    ("Z", "Vacataires 621",               "COUT_VACAT_N",   "mesure",    ""),
    ("AA", "Enseignants permanents 6411", "COUT_PERM_N",    "mesure",    "À AJOUTER À LA VUE")]
RM = PR_FIN + 3
titre(w3, RM, "ⓑ  Le mapping  ·  colonne du classeur ↔ colonne de V_MOTEUR_CAL",
      "Le tableau ① de l'onglet « Le moteur » est la vue, colonne pour colonne. Neuf colonnes sont "
      "à ajouter — les sept du levier marque, les heures et les permanents. Elles sont signalées en "
      "rouge, et tagetik/V_MOTEUR_CAL.sql les porte déjà.")
entete(w3, RM + 3, ["Colonne du classeur", "Colonne de la vue", "Nature", "Commentaire"], 26)
NBM = ['General'] * 4
RM0 = RM + 4
for j, (col, lib, vue, nat, com) in enumerate(MAP):
    r = RM0 + j
    ligne(w3, r, ["%s  ·  %s" % (col, lib), vue, nat, com], NBM, fond=VUE, gauche=(1, 2, 3))
    if com.startswith("À AJOUTER"):
        for c in range(2, 6): w3.cell(r, c).font = F(8, c == 2, ROUGE_T)
    if nat.startswith("NON"): w3.cell(r, 4).font = F(8, True, "B26B00")
RMN = RM0 + len(MAP)

# ============================================================================
#  ONGLET 3 (c) — LES FORMULES DU MASQUE, dans l'ordre du tableau (2)
# ============================================================================
#  La doc ne peut pas deriver du classeur : les formules ne sont pas retapees
#  ici, elles sont LUES dans ligne2(), la fonction qui les ecrit. Si le masque
#  change, cette page change avec lui, sans rien faire.
FML = ligne2(T2 + 1, T1 + 1)
FORM = [("F4", "Δ budget d'acquisition", "SAISIE", "la première des deux cellules modifiables"),
        ("J4", "Δ budget de marque",     "SAISIE", "la seconde — le levier qu'on ne pilotait pas")] + [
    (GL(c), lab, FML[c], dit) for c, lab, dit in [
        (4,  "Conversion lead → inscrit",
             "INSCRITS ÷ LEADS TOTAUX — jamais pré-calculée, sinon la ligne groupe se trompe"),
        (5,  "CA par inscrit", "CA des nouveaux ÷ inscrits"),
        (6,  "Consommables / élève", "604 + 6063 ÷ effectifs"),
        (7,  "Places libres", "places − effectifs : la borne physique du geste"),
        (8,  "Δ budget acquisition", "le geste, appliqué au budget 2026"),
        (9,  "Inscrits gagnés · acquisition",
             "leads payants × l'effet d'élasticité, converti au taux du campus"),
        (10, "CA gagné · acquisition", "inscrits gagnés × CA par inscrit"),
        (11, "Coût marginal / élève",
             "consommables seuls, + quote-part vacataire si la classe doit ouvrir"),
        (12, "EBITDA gagné · acquisition", "CA gagné − Δ budget − coût de service"),
        (13, "CAC marginal · acquisition", "Δ budget ÷ inscrits gagnés"),
        (14, "Δ budget marque", "le second levier, appliqué au budget de marque 2026"),
        (15, "Inscrits gagnés · marque",
             "leads ORGANIQUES × l'effet d'élasticité organique — la même formule"),
        (16, "CA gagné · marque", "inscrits gagnés × le même CA par inscrit"),
        (17, "CAC marginal · marque", "Δ budget de marque ÷ inscrits gagnés"),
        (18, "Le rapport",
             "ce que vaut l'euro d'acquisition rapporté à l'euro de marque")]]
RN = RMN + 2
titre(w3, RN, "ⓒ  Les formules du masque  ·  la ligne %d, campus Ipac Montpellier" % (T2 + 1),
      "Toutes les autres lignes sont la même formule, décalée. Aucune n'utilise de constante : "
      "chacune pointe le tableau ① ou l'une des deux saisies.", "B26B00")
entete(w3, RN + 3, ["Mesure", "Col.", "Formule du classeur", None, "Ce qu'elle dit"], 26)
NBF = ['General'] * 5
RN0 = RN + 4
for j, (col, lib, f, dit) in enumerate(FORM):
    r = RN0 + j
    ligne(w3, r, [lib, col, f, None, dit], NBF, fond=CALC if j > 1 else PANEL, gauche=(1, 2, 3, 4))
    w3.cell(r, 4).data_type = "s"          # une formule MONTREE, pas evaluee
    w3.cell(r, 4).font = Font(name="Consolas", size=7.5, color=INK if j > 1 else AZUR, bold=j < 2)
    if j < 2:
        for c in range(2, 7): w3.cell(r, c).font = F(8, True, AZUR)
        w3.cell(r, 4).font = Font(name="Consolas", size=7.5, color=AZUR, bold=True)
        w3.cell(r, 4).data_type = "s"
RNN = RN0 + len(FORM)

# ============================================================================
#  ONGLET 3 (d) — LES CONTROLES
#
#  Six d'entre eux confrontent DEUX SOURCES REELLEMENT INDEPENDANTES -- le CRM
#  d'un cote, la comptabilite de l'autre, ou le grain programme contre le grain
#  campus. Un controle qui compare une cellule a un lien vers elle-meme ne
#  controle rien ; il n'y en a pas ici.
# ============================================================================
CV, BU = "'Le coût variable'!", "'Budget 2027'!"
CTRL = [
    ("Budget d'acquisition : dépense CRM 2026 = compte 6231",
     "={0}I{1}".format(M, RT1), "={0}D{1}".format(BU, ROWP["6231"]), '#,##0" €"',
     "socle CRM contre comptabilité"),
    ("Consommables : comptes 604 + 6063 = COUT_CONSO_N",
     "={0}D{1}+{0}D{2}".format(BU, ROWP["604"], ROWP["6063"]), "={0}Y{1}".format(M, RT1), '#,##0" €"',
     "comptes contre agrégat de la vue"),
    ("Vacataires : compte 621 = COUT_VACAT_N",
     "={0}D{1}".format(BU, ROWP["621"]), "={0}Z{1}".format(M, RT1), '#,##0" €"',
     "comptes contre agrégat de la vue"),
    ("Permanents : compte 6411 = COUT_PERM_N",
     "={0}D{1}".format(BU, ROWP["6411"]), "={0}AA{1}".format(M, RT1), '#,##0" €"',
     "comptes contre agrégat de la vue"),
    ("Effectifs : grain programme = grain campus",
     "={0}C{1}".format(CV, RBN), "={0}U{1}".format(M, RT1), '#,##0',
     "cycle × modalité contre campus"),
    ("Allocation : consommables alloués aux programmes = total réseau",
     "=SUMPRODUCT({0}C{1}:C{2},{0}G{1}:G{2})".format(CV, RB0, RBN - 1), "={0}Y{1}".format(M, RT1),
     '#,##0" €"', "la clé EFFECTIFS ne perd rien"),
    ("EBITDA gagné : CA gagné − Δ budget − coût de service",
     "={0}J{1}-{0}H{1}-{0}I{1}*{0}K{1}".format(M, RT2), "={0}L{1}".format(M, RT2), '#,##0" €"',
     "additivité de la ligne groupe"),
    ("Régime du coût marginal : inscrits gagnés ≤ places libres",
     "={0}I{1}".format(M, RT2), "={0}G{1}".format(M, RT2), '#,##0',
     "si dépassé, une classe ouvre")]
RK = RNN + 2
titre(w3, RK, "ⓓ  Les contrôles  ·  ils doivent tous valoir zéro",
      "Chacun confronte deux sources indépendantes. Le dernier n'est pas un écart mais une marge : "
      "il dit combien de sièges restent avant que le coût marginal ne bascule.")
entete(w3, RK + 3, ["Contrôle", None, "Source A", "Source B", "Écart", "Statut", "Ce qui est comparé"], 26)
RK0 = RK + 4
for j, (lib, a, b, nf, com) in enumerate(CTRL):
    r = RK0 + j; dernier = (j == len(CTRL) - 1)
    ligne(w3, r, [lib, None, a, b, "=E{0}-D{0}".format(r) if dernier else "=D{0}-E{0}".format(r),
                  '=IF(ABS(F{0})<1,"OK","À VÉRIFIER")'.format(r) if not dernier
                  else '=IF(F{0}>0,"OK · marge","BASCULE")'.format(r), com],
          ['General', 'General', nf, nf, nf, 'General', 'General'], gauche=(1, 6))
    w3.cell(r, 8).font = F(8, False, DOUX, True); w3.cell(r, 8).alignment = ind(0)
RKN = RK0 + len(CTRL)
w3.conditional_formatting.add("G{0}:G{1}".format(RK0, RKN - 1),
    FormulaRule(formula=['ISNUMBER(SEARCH("OK",$G%d))' % RK0],
                font=Font(name=UI, size=8, bold=True, color=VERT_T)))
w3.conditional_formatting.add("G{0}:G{1}".format(RK0, RKN - 1),
    FormulaRule(formula=['NOT(ISNUMBER(SEARCH("OK",$G%d)))' % RK0],
                font=Font(name=UI, size=8, bold=True, color=ROUGE_T), fill=fill(HM_BAS)))

for c in range(2, NC3 + 1):
    w3.cell(RKN + 2, c).fill = fill(PANEL); w3.cell(RKN + 2, c).border = Border(top=sd(AZUR))
    w3.cell(RKN + 3, c).fill = fill(PANEL); w3.cell(RKN + 3, c).border = Border(bottom=sd(AZUR))
w3.cell(RKN + 2, 2, "Ce qu'il reste à faire côté Tagetik").font = F(9, True, AZUR)
w3.cell(RKN + 2, 2).alignment = ind(0); w3.row_dimensions[RKN + 2].height = 18
w3.cell(RKN + 3, 2, "① rejouer V_MOTEUR_CAL : elle porte maintenant le levier marque (LEAD_ORG, "
                    "SPEND_MRQ, ELASTICITE_ORG), les heures et les permanents.  "
                    "② brancher le tableau ① sur la vue, une ligne par campus, hiérarchie MARQUE ▸ CAMPUS.  "
                    "③ le tableau ② est un masque de saisie : seule F4 est ouverte.  "
                    "④ l'onglet « Le coût variable » ne lit que le tableau ① et les paramètres ci-dessus.")
w3.cell(RKN + 3, 2).font = F(7.5, False, DOUX, True); w3.cell(RKN + 3, 2).alignment = ind(0)

# ============================================================================
#  ONGLET 4 — LE BUDGET 2027
#
#  CET ONGLET SE PROJETTE DEVANT UN CFO. Il est ecrit pour lui, pas pour
#  l'integrateur, et cela change trois choses concretes :
#
#  1. LE RESULTAT EN HAUT. Quatre nombres des la premiere vue -- CA, EBITDA
#     propre, quote-part du siege, EBITDA net -- avant meme les hypotheses.
#     On ne fait pas descendre un DAF sur quatre-vingts lignes pour lui donner
#     le chiffre qu'il est venu chercher.
#
#  2. DES POURCENTAGES, PAS DES COEFFICIENTS. La version precedente affichait
#     « 1,062 » et « 1,020 ». Personne ne lit un coefficient. Les colonnes
#     portent maintenant des ecarts -- « +6,9 % » et « +2,0 % » -- et le calcul
#     s'ecrit D x (1+F) x (1+G). Un zero s'affiche « — » au lieu de « 1,000 ».
#
#  3. LE DETAIL REPLIE. Les vingt comptes sont groupes sous leur famille et
#     FERMES par defaut. Le CFO voit six familles et trois resultats ; il
#     ouvre un « + » s'il veut le compte. Le detail n'a pas disparu, il attend.
#
#  Le siege reste en bloc a part : il ne suit aucun inducteur d'activite, il se
#  decide puis se cascade. Le ranger dans une famille « indexe » ferait croire
#  qu'il s'indexe.
# ============================================================================
w4 = wb.create_sheet("Budget 2027")
NC4 = 13
bandeau(w4, NC4, "BUDGET 2027  —  le chiffre d'affaires en cinq lignes, les coûts en cinq familles",
        R_FIN + 12)
w4.column_dimensions["A"].width = 2.4; w4.column_dimensions["B"].width = 36
for c, wd in ((3, 11), (4, 15), (5, 24), (6, 12), (7, 12), (8, 15), (9, 12), (10, 22),
              (11, 14), (12, 14), (13, 14)): w4.column_dimensions[GL(c)].width = wd
MO, CO = "'Le moteur'!", "'Le coût variable'!"
CL = {"VERT": VERT_T, "OCRE": "B26B00", "ROUGE": ROUGE_T, "DOUX": DOUX, "AZUR": AZUR}

w4.cell(5, 2, "La croissance se défait en deux, et la seconde moitié, c'est le moteur.").font = F(12, True, INK)
w4.cell(5, 2).alignment = ind(0); w4.row_dimensions[5].height = 22
w4.cell(6, 2, "On sait séparer ce que porte le socle de ce qu'ajoute le budget d'acquisition : "
              "+181 élèves en 2026, dont 31,8 dus au +10 % d'acquisition et 149,2 au socle. Le socle "
              "se saisit ; le geste, lui, ne se saisit pas — il vient de l'onglet précédent.")
w4.cell(6, 2).font = F(8, False, DOUX, True); w4.cell(6, 2).alignment = ind(0)
w4.row_dimensions[6].height = 16

# ---- LE RESULTAT, AVANT LES HYPOTHESES ------------------------------------
KP = [(2,  "CHIFFRE D'AFFAIRES", "=H%d" % R_CA,     '#,##0" €"', INK,
       '="contre "&TEXT(D{0},"#,##0 €")&" en 2026"'.format(R_CA)),
      (5,  "EBITDA PROPRE",      "=H%d" % R_PROPRE, '#,##0" €"', VERT_T,
       '="ce que les campus produisent  ·  marge "&TEXT(H{0}/H{1},"0.0 %")'.format(R_PROPRE, R_CA)),
      (8,  "QUOTE-PART DU SIÈGE", "=H%d" % R_SIEGE, '#,##0" €"', ROUGE_T,
       '="soit "&TEXT(H{0}/H{1},"0.0 %")&" du chiffre d\'affaires"'.format(R_SIEGE, R_CA)),
      (11, "EBITDA NET",         "=H%d" % R_NET,    '#,##0" €"', VERT_T,
       '="marge "&TEXT(D{0}/D{1},"0.0 %")&" → "&TEXT(H{0}/H{1},"0.0 %")'.format(R_NET, R_CA))]
for col, lab, f, nf, coul, note in KP:
    for c in (col, col + 1, col + 2):
        w4.cell(8, c).fill = fill(AZUR if lab == "EBITDA NET" else GRIS)
        w4.cell(9, c).fill = fill(PANEL); w4.cell(10, c).fill = fill(PANEL)
        x = w4.cell(11, c); x.fill = fill(PANEL); x.border = Border(bottom=sd(FILET))
    a = w4.cell(9, col, lab); a.font = F(7, True, INK); a.alignment = ind(1)
    x = w4.cell(10, col, f); x.font = F(16, False, coul); x.alignment = ind(1); x.number_format = nf
    n = w4.cell(11, col, note); n.font = F(6.5, False, DOUX, True); n.alignment = ind(1)
for r, h in ((8, 3), (9, 12), (10, 26), (11, 14)): w4.row_dimensions[r].height = h

# ---- (a) LES SAISIES ------------------------------------------------------
titre(w4, 14, "ⓐ  Les hypothèses  ·  huit viennent de Tagetik, une seule est un calage",
      "Une seule est saisie ici — le calage du socle. Toutes les autres viennent de la ZONE "
      "D'HYPOTHÈSES restituée par Tagetik : changez le scénario en haut de l'onglet précédent, "
      "et ces neuf lignes changent ensemble.")
entete(w4, 17, ["Hypothèse", None, None, "Valeur retenue", None, "D'où elle vient"], 24)
SAIS = [(None, "CE QUI FAIT LE CHIFFRE D'AFFAIRES", None, None),
        (0, "Croissance du socle", 0.031505,
         "CALAGE sur le scénario Cadrage de CAD_PIL — absorbe conversion et passage"),
        (0, "Hausse tarifaire", hyp("HYP_PRICE"), "zone d'hypothèses · HYP_PRICE"),
        (0, "Δ budget d'acquisition", "='Le moteur'!F4", "onglet précédent · HYP_ACQ_BUD"),
        (0, "Δ budget de marque", "='Le moteur'!J4", "onglet précédent · HYP_BRAND_BUD"),
        (None, "CE QUI FAIT LES COÛTS", None, None),
        (0, "Inflation des charges externes", hyp("HYP_INFL_EXT"), "zone d'hypothèses · HYP_INFL_EXT"),
        (0, "Effort de productivité", hyp("HYP_PRODUCTIVITY"), "zone d'hypothèses · HYP_PRODUCTIVITY"),
        (0, "Politique salariale", hyp("HYP_SALARY"), "zone d'hypothèses · HYP_SALARY"),
        (0, "Variation des effectifs permanents", hyp("HYP_FTE_PERM"), "zone d'hypothèses · HYP_FTE_PERM"),
        (0, "Variation des coûts de structure", hyp("HYP_STRUCT_COST"), "zone d'hypothèses · HYP_STRUCT_COST")]
SA0, REFS = 18, {}
for j, (kind, lab, val, src) in enumerate(SAIS):
    r = SA0 + j
    if kind is None:
        for c in range(2, NC4 + 1): w4.cell(r, c).fill = fill(FOND)
        w4.cell(r, 2, lab).font = F(8, True, AZUR); w4.cell(r, 2).alignment = ind(0)
        w4.row_dimensions[r].height = 18
        continue
    for c in range(2, NC4 + 1):
        x = w4.cell(r, c); x.fill = fill(PARM); x.border = Border(bottom=sd("E6E2D6"))
    w4.cell(r, 2, lab).font = F(8, True, INK); w4.cell(r, 2).alignment = ind(1)
    lie = isinstance(val, str)
    x = w4.cell(r, 5, val); x.number_format = '+0.00%;-0.00%;"—"'
    x.font = F(9, True, AZUR if lie else INK); x.alignment = R
    x.fill = fill(PANEL); x.border = Border(*[sd(AZUR if lie else "C9C3B0")] * 4)
    w4.cell(r, 7, src).font = F(7.5, False, DOUX, lie); w4.cell(r, 7).alignment = ind(0)
    REFS[lab.split("  (")[0]] = "$E$%d" % r
SOC, TAR = REFS["Croissance du socle"], REFS["Hausse tarifaire"]
ACQ, MRQ = REFS["Δ budget d'acquisition"], REFS["Δ budget de marque"]
INF, PRD = REFS["Inflation des charges externes"], REFS["Effort de productivité"]
SAL, POS = REFS["Politique salariale"], REFS["Variation des effectifs permanents"]
STR = REFS["Variation des coûts de structure"]

def bloc_lignes(w, r0, lignes_, nc):
    """Un bloc « libelle · valeur · lecture ». La valeur est en E, la lecture en G."""
    for j, (lab, f, nf, lec, fort) in enumerate(lignes_):
        r = r0 + j
        for c in range(2, nc + 1):
            w.cell(r, c).fill = fill(PANEL); w.cell(r, c).border = Border(bottom=sd("EDEEF0"))
        w.cell(r, 2, lab).font = F(8, fort, INK); w.cell(r, 2).alignment = ind(0 if fort else 1)
        x = w.cell(r, 5, f); x.number_format = nf; x.alignment = R; x.font = F(9 if fort else 8, fort, INK)
        w.cell(r, 7, lec).font = F(7.5, False, DOUX, True); w.cell(r, 7).alignment = ind(0)

# ---- (b) LE VOLUME 2027 ---------------------------------------------------
V0 = 34
titre(w4, 30, "ⓑ  Combien d'élèves en 2027  ·  ce que porte le socle, ce qu'ajoute le geste",
      "La ligne « ce que le geste ajoute » n'est pas calculée ici : elle vient du moteur "
      "d'acquisition. Bouger le Δ budget là-bas bouge ce budget-ci.")
entete(w4, 33, ["Grandeur", None, None, "2027", None, "Lecture"], 24)
bloc_lignes(w4, V0, [
    ("Élèves 2026",                          "={0}U{1}".format(MO, RT1), '#,##0', "constaté", False),
    ("+ ce que porte le socle",              "=E{0}*{1}".format(V0, SOC), '#,##0.0',
     "rétention, passage, notoriété", False),
    ("+ ce que le geste d'acquisition ajoute", "={0}I{1}".format(MO, RT2), '#,##0.0',
     "LIÉ au moteur — les inscrits gagnés par l'acquisition", False),
    ("+ ce que le geste de marque ajoute",   "={0}O{1}".format(MO, RT2), '#,##0.0',
     "LIÉ au moteur — les inscrits gagnés par la marque", False),
    ("= Élèves 2027",                        "=E{0}+E{1}+E{2}+E{3}".format(V0, V0 + 1, V0 + 2, V0 + 3),
     '#,##0', "", True),
    ("Croissance totale",                    "=IFERROR(E{0}/E{1}-1,0)".format(V0 + 4, V0), '+0.00%',
     "elle ne se saisit pas : elle se déduit", False),
    ("Places du réseau",                     "={0}V{1}".format(MO, RT1), '#,##0',
     "135 classes, inchangées depuis 2024", False),
    ("Classes 2026",                         "={0}W{1}".format(MO, RT1), '#,##0', "", False),
    ("Capacité moyenne d'une classe",        "=IFERROR(E{0}/E{1},0)".format(V0 + 6, V0 + 7), '#,##0.0', "", False),
    ("Croissance possible avant saturation", "={0}L{1}".format(CO, RCN), '0.0%',
     "le premier campus qui sature : MBway Paris", False),
    ("Classes à ouvrir en 2027",             "=MAX(0,ROUNDUP((E{0}-E{1})/E{2},0))".format(V0 + 4, V0 + 6, V0 + 8),
     '#,##0', "aucune — et c'est toute la démonstration", True),
    ("Classes 2027",                         "=E{0}+E{1}".format(V0 + 7, V0 + 10), '#,##0', "", False),
    ("Effet volume du compte 621",           "=IFERROR(E{0}/E{1}-1,0)".format(V0 + 11, V0 + 7), '+0.0%;-0.0%;"—"',
     "il suit les CLASSES, jamais les élèves", False)], NC4)
w4.cell(V0 + 4, 5).font = F(10, True, AZUR); w4.cell(V0 + 10, 5).font = F(10, True, VERT_T)
w4.cell(48, 2, "À +6 % l'an, MBway Paris tient jusqu'en 2029 — c'est le premier campus qui butera "
               "sur ses murs, et le classeur dit lequel et quand.")
w4.cell(48, 2).font = F(7.5, False, DOUX, True); w4.cell(48, 2).alignment = ind(0)

# ---- (c) LE CHIFFRE D'AFFAIRES 2027 --------------------------------------
CA0 = 54
titre(w4, 50, "ⓒ  Le chiffre d'affaires 2027  ·  quatre lignes, et une seule est une décision",
      "Le socle est déjà inscrit, le geste vient du moteur, le prix est un arbitrage. "
      "Rien d'autre n'entre dans le chiffre d'affaires.")
entete(w4, 53, ["Ligne", None, None, "Montant", None, "Lecture"], 24)
bloc_lignes(w4, CA0, [
    ("Chiffre d'affaires 2026",   CA26, '#,##0" €"', "constaté · 706 + 7062 + 708", False),
    ("+ ce que porte le socle",   "=E{0}*{1}".format(CA0, SOC), '#,##0" €"', "la rentrée déjà engagée", False),
    ("+ ce que le geste d'acquisition ajoute", "={0}J{1}".format(MO, RT2), '#,##0" €"',
     "LIÉ au moteur — le CA gagné par le Δ acquisition", False),
    ("+ ce que le geste de marque ajoute", "={0}P{1}".format(MO, RT2), '#,##0" €"',
     "LIÉ au moteur — le CA gagné par le Δ marque", False),
    ("+ effet prix",              "=(E{0}+E{1}+E{2}+E{3})*{4}".format(CA0, CA0 + 1, CA0 + 2, CA0 + 3, TAR),
     '#,##0" €"', "la hausse tarifaire", False),
    ("= Chiffre d'affaires 2027", "=SUM(E{0}:E{1})".format(CA0, CA0 + 4), '#,##0" €"', "", True)], NC4)
w4.cell(CA0 + 5, 5).font = F(11, True, AZUR)
w4.cell(61, 2, '="Sur "&TEXT(E{5}-E{0},"#,##0 €")&" de croissance, "&TEXT(E{1}/(E{5}-E{0}),"0 %")'
               '&" viennent du socle déjà inscrit, "&TEXT((E{2}+E{3})/(E{5}-E{0}),"0 %")&" des deux '
               'gestes d\'acquisition et de marque, et "&TEXT(E{4}/(E{5}-E{0}),"0 %")&" du prix. '
               'Le chiffre d\'affaires ne se décrète pas."'.format(CA0, CA0 + 1, CA0 + 2, CA0 + 3, CA0 + 4, CA0 + 5))
w4.cell(61, 2).font = F(9, True, INK); w4.cell(61, 2).alignment = ind(0)

# ---- (d) LES COUTS DE CAMPUS : six familles, six regles ------------------
titre(w4, 63, "ⓓ  Les coûts de CAMPUS  ·  cinq familles, cinq règles",
      "Un budget qui indexe tout au même taux ne dit rien. Celui-ci donne à chaque euro l'inducteur "
      "de son comportement — c'est ce qui fait apparaître où est le levier, et surtout où il n'est pas. "
      "Le détail des comptes est replié : cliquez le « + » dans la marge.", "B26B00")
entete(w4, 66, ["Famille · compte", None, "Montant 2026", "Ce qui la fait bouger", "Effet volume",
                "Effet prix", "Montant 2027", "Variation", "Bouge si un élève de plus arrive ?"], 30)
PC = '+0.0%;-0.0%;"—"'
NB7 = ['General', 'General', '#,##0" €"', 'General', PC, PC, '#,##0" €"', '+0.0%;-0.0%', 'General']
FAM_BOUGE = ["OUI — ils suivent le chiffre d'affaires",
             "NON — la masse est engagée à l'année",
             "NON — c'est le mur qui coûte, pas l'élève",
             "NON — assis sur la base fiscale",
             "c'est la décision elle-même"]
#  LA REGLE DE CAD_PIL, COMPTE POUR COMPTE. On l'a décodée dans son onglet
#  _CALC_PNL et reproduite ici à six euros près sur vingt millions. C'est ce
#  qui fait que le Budget 2027 tombe sur le scénario déployé, et non à côté.
#
#      604 6063 621          CA × (1 − productivité)
#      6411 6413 6414 645    (1 + salaire) × (1 + postes)
#      613 615 616 625       (1 + inflation) × (1 − productivité) × (1 + structure)
#      6226 626 6281         idem — la structure du siège suit la même règle
#      6331 6333 63511       (1 + inflation) × (1 − productivité)
#      6231                  1 + Δ acquisition
#      6236                  1 + Δ marque
#      6811                  1 + inflation
CAF = "($E${0}/$E${1}-1)".format(CA0 + 5, CA0)      # la croissance du CA, moteur du variable
IDX = "=(1+{0})*(1-{1})-1".format(INF, PRD)         # indexé, moins l'effort
IDS = "=(1+{0})*(1-{1})*(1+{2})-1".format(INF, PRD, STR)   # idem, plus la structure
REGLE = {"604": ("=" + CAF, "=-%s" % PRD, "le chiffre d'affaires"),
         "6063": ("=" + CAF, "=-%s" % PRD, "le chiffre d'affaires"),
         "621": ("=" + CAF, "=-%s" % PRD, "le chiffre d'affaires"),
         "6411": ("=%s" % POS, "=%s" % SAL, "les postes"),
         "6413": ("=%s" % POS, "=%s" % SAL, "les postes"),
         "645": ("=%s" % POS, "=%s" % SAL, "les postes"),
         "6414": ("=%s" % POS, "=%s" % SAL, "les postes"),
         "6231": (0, "=%s" % ACQ, "le geste"),
         "6236": (0, "=%s" % MRQ, "le budget de marque"),
         "6811": (0, "=%s" % INF, "l'indexation")}
for a in ("613", "615", "616", "625", "6226", "626", "6281"):
    REGLE[a] = (0, IDS, "l'indexation et la structure")
for a in ("63511", "6331", "6333"):
    REGLE[a] = (0, IDX, "l'indexation, moins l'effort")

def ligne_compte(r, a, fond=CALC):
    vol, prix, dit = REGLE[a]
    ligne(w4, r, ["      %s · %s" % (a, LIBC_CPT[a]), None, MTT[a], dit, vol, prix,
                  "=D{0}*(1+F{0})*(1+G{0})".format(r), "=IFERROR(H{0}/D{0}-1,0)".format(r), ""],
          NB7, fond=fond, gauche=(1, 3, 8))
    w4.cell(r, 2).font = F(8, False, DOUX)
    w4.cell(r, 5).font = F(7.5, False, DOUX, True)

nf = 0
for item in PLANL:
    if item[0] == "fam":
        _, rr, lab, cl, regle, cpts, coul = item
        a, b = ROWP[cpts[0]], ROWP[cpts[-1]]
        ligne(w4, rr, [lab, None, "=SUM(D{0}:D{1})".format(a, b), regle, "", "",
                       "=SUM(H{0}:H{1})".format(a, b), "=IFERROR(H{0}/D{0}-1,0)".format(rr),
                       FAM_BOUGE[nf]], NB7, fond=GRIS, gras=True, trait=INK, gauche=(1, 3, 8))
        w4.cell(rr, 5).font = F(8, True, CL[coul]); w4.cell(rr, 9).font = F(9, True, CL[coul])
        w4.cell(rr, 10).font = F(7.5, False, CL[coul], True)
        nf += 1
    elif item[0] == "cpt":
        ligne_compte(item[1], item[2])
CPT_R = [it[1] for it in PLANL if it[0] == "cpt"]
FAM_R = [it[1] for it in PLANL if it[0] == "fam"]
w4.conditional_formatting.add(" ".join("I%d" % x for x in CPT_R),
    ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                   mid_color=HM_MED, end_type="max", end_color=HM_BAS))
SOM = lambda col, rows: "=" + "+".join("%s%d" % (col, x) for x in rows)
ligne(w4, R_CAMP, ["TOTAL DES CHARGES DE CAMPUS", None, SOM("D", FAM_R), "", "", "",
                   SOM("H", FAM_R), "=IFERROR(H{0}/D{0}-1,0)".format(R_CAMP), ""],
      NB7, fond=GRIS, gras=True, trait=INK, gauche=(1, 3, 8))
ligne(w4, R_CA, ["Chiffre d'affaires", None, CA26, "", "", "", "=E%d" % (CA0 + 5),
                 "=IFERROR(H{0}/D{0}-1,0)".format(R_CA), "bloc ⓒ ci-dessus"],
      NB7, fond=VUE, gras=True, gauche=(1, 3, 8))
ligne(w4, R_PROPRE, ["EBITDA PROPRE  ·  avant quote-part du siège", None,
                     "=D{0}-D{1}".format(R_CA, R_CAMP), "", "", "",
                     "=H{0}-H{1}".format(R_CA, R_CAMP),
                     "=IFERROR(H{0}/D{0}-1,0)".format(R_PROPRE), "ce que les campus produisent"],
      NB7, fond=GRIS, gras=True, trait=INK, gauche=(1, 3, 8))
for c in (4, 8): w4.cell(R_PROPRE, c).font = F(10, True, VERT_T)

# ---- le siege, en bloc a part --------------------------------------------
for c in range(2, NC4 + 1): w4.cell(R_SIEGE_T, c).fill = fill(FOND)
w4.cell(R_SIEGE_T, 2, "LE SIÈGE  ·  mêmes règles, périmètre à part — c'est lui qui sépare l'EBITDA propre de l'EBITDA net")
w4.cell(R_SIEGE_T, 2).font = F(9, True, AZUR); w4.cell(R_SIEGE_T, 2).alignment = ind(0)
w4.row_dimensions[R_SIEGE_T].height = 20
for a in SIEGE: ligne_compte(ROWP[a], a, fond=PANEL)
ligne(w4, R_SIEGE, ["QUOTE-PART DU SIÈGE", None, SOM("D", [ROWP[a] for a in SIEGE]), "", "", "",
                    SOM("H", [ROWP[a] for a in SIEGE]),
                    "=IFERROR(H{0}/D{0}-1,0)".format(R_SIEGE), "marque, holding — cascades K1 et K4"],
      NB7, fond=GRIS, gras=True, trait=INK, gauche=(1, 3, 8))
ligne(w4, R_NET, ["EBITDA NET  ·  celui du groupe", None, "=D{0}-D{1}".format(R_PROPRE, R_SIEGE),
                  "", "", "", "=H{0}-H{1}".format(R_PROPRE, R_SIEGE),
                  "=IFERROR(H{0}/D{0}-1,0)".format(R_NET), "dotations exclues"],
      NB7, fond=GRIS, gras=True, trait=INK, gauche=(1, 3, 8))
for c in (4, 8): w4.cell(R_NET, c).font = F(11, True, VERT_T)
ligne(w4, R_MARGE, ["Marge d'EBITDA  —  propre", None, "=IFERROR(D{0}/D{1},0)".format(R_PROPRE, R_CA),
                    "", "", "", "=IFERROR(H{0}/H{1},0)".format(R_PROPRE, R_CA), "", ""],
      NB7, fond=PANEL, gras=True, gauche=(1, 3, 8))
w4.cell(R_MARGE, 10, '="et nette : "&TEXT(D{0}/D{1},"0.0 %")&"  →  "&TEXT(H{0}/H{1},"0.0 %")'
                     .format(R_NET, R_CA))
w4.cell(R_MARGE, 10).font = F(8, True, INK); w4.cell(R_MARGE, 10).alignment = ind(0)
for c in (4, 8): w4.cell(R_MARGE, c).number_format = '0.00%'
ligne(w4, R_DOTA, ["      6811 · Dotations aux amortissements  ·  sous la ligne d'EBITDA", None,
                   MTT["6811"], "l'indexation", 0, "=%s" % INF,
                   "=D{0}*(1+F{0})*(1+G{0})".format(R_DOTA),
                   "=IFERROR(H{0}/D{0}-1,0)".format(R_DOTA), ""],
      NB7, fond=PANEL, gauche=(1, 3, 8))
w4.cell(R_DOTA, 2).font = F(8, False, DOUX); w4.cell(R_DOTA, 5).font = F(7.5, False, DOUX, True)

# ---- le detail des comptes, groupe et FERME par defaut -------------------
#  Le CFO voit six familles et trois resultats. Le detail attend derriere un
#  « + » dans la marge -- il n'a pas disparu, il ne s'impose pas.
w4.sheet_properties.outlinePr.summaryBelow = False
for r in CPT_R + [ROWP[a] for a in SIEGE]:
    w4.row_dimensions[r].outlineLevel = 1
    w4.row_dimensions[r].hidden = True

# ---- (e) LA RECONCILIATION AVEC LE SIMULATEUR ----------------------------
RR = R_FIN
titre(w4, RR, "ⓔ  Est-ce que ce budget dit la même chose que le moteur ?",
      "Le CA gagné est le même nombre — c'est la même cellule. Le coût de service, lui, obéit à deux "
      "doctrines : le budget applique la règle de CAD_PIL, où le vacataire suit le chiffre d'affaires ; "
      "le moteur le fait suivre la CLASSE, ce qui est plus juste. L'écart est affiché, pas gommé.")
entete(w4, RR + 3, ["Ce que le geste rapporte", None, "Le moteur", None, "Le budget 2027", None,
                    "Écart", None, "Pourquoi"], 26)
L1, L2, L3 = RR + 4, RR + 5, RR + 6
REC = [("CA gagné par le geste d'acquisition", "={0}J{1}".format(MO, RT2), "=E%d" % (CA0 + 2),
        "la même cellule — zéro par construction"),
       ("Coût de servir ces élèves", "={0}I{1}*{0}K{1}".format(MO, RT2),
        "=D{0}*{1}J{2}/D{3}*(1-{4})".format(TP, MO, RT2, R_CA, PRD),
        "le moteur suit la CLASSE, le budget suit le CA — c'est là qu'ils divergent"),
       ("EBITDA gagné", "={0}L{1}".format(MO, RT2),
        "=F{0}-(H{1}-D{1})-F{2}".format(L1, ROWP["6231"], L2),
        "CA gagné − Δ budget d'acquisition − coût de service")]
for j, (lab, mot, bud, pq) in enumerate(REC):
    r = L1 + j
    for c in range(2, NC4 + 1):
        w4.cell(r, c).fill = fill(PANEL); w4.cell(r, c).border = Border(bottom=sd("EDEEF0"))
    w4.cell(r, 2, lab).font = F(8, j == 2, INK); w4.cell(r, 2).alignment = ind(0)
    for col, val in ((4, mot), (6, bud), (8, "=F{0}-D{0}".format(r))):
        x = w4.cell(r, col, val); x.number_format = '#,##0" €"'; x.alignment = R
        x.font = F(9 if j == 2 else 8, j == 2, INK)
    w4.cell(r, 8).font = F(9 if j == 2 else 8, True, VERT_T)
    w4.cell(r, 10, pq).font = F(7.5, False, DOUX, True); w4.cell(r, 10).alignment = ind(0)
for c in range(2, NC4 + 1):
    w4.cell(L3 + 2, c).fill = fill(PANEL); w4.cell(L3 + 2, c).border = Border(top=sd(AZUR))
    w4.cell(L3 + 3, c).fill = fill(PANEL)
    w4.cell(L3 + 4, c).fill = fill(PANEL); w4.cell(L3 + 4, c).border = Border(bottom=sd(AZUR))
w4.cell(L3 + 2, 2, '="Ce budget reproduit le scénario Cadrage de CAD_PIL à l\'euro : "'
                   '&TEXT(H{0},"#,##0 €")&" de chiffre d\'affaires, "&TEXT(H{1},"#,##0 €")'
                   '&" d\'EBITDA net. L\'écart de "&TEXT(ABS(H{2}),"#,##0 €")&" ci-dessus est le prix '
                   'de sa doctrine : chez lui le vacataire suit le CA, chez nous il suit la classe."'
                   .format(R_CA, R_NET, L3))
w4.cell(L3 + 2, 2).font = F(9, True, INK); w4.cell(L3 + 2, 2).alignment = ind(0)
w4.row_dimensions[L3 + 2].height = 18
w4.cell(L3 + 3, 2, '="La marge nette gagne "&TEXT((H{2}/H{1}-D{2}/D{1})*100,"0.0")&" pt quand la '
                   'marge propre n\'en gagne que "&TEXT((H{0}/H{1}-D{0}/D{1})*100,"0.0")&" : la '
                   'différence ne vient pas des campus, elle vient du siège qui se dilue — il croît '
                   'de "&TEXT(H{3}/D{3}-1,"0.0 %")&" quand le chiffre d\'affaires croît de "'
                   '&TEXT(H{1}/D{1}-1,"0.0 %")&"."'.format(R_PROPRE, R_CA, R_NET, R_SIEGE))
w4.cell(L3 + 3, 2).font = F(9, True, INK); w4.cell(L3 + 3, 2).alignment = ind(0)
w4.row_dimensions[L3 + 3].height = 18
w4.cell(L3 + 4, 2, '="Et le gain ne vient d\'aucune économie : il vient de "&TEXT(E{0}-E{1},"#,##0")'
                   '&" élèves de plus dans des classes déjà ouvertes — dont "&TEXT(E{2}+E{3},"#,##0")'
                   '&" que les deux gestes ont payés."'.format(V0 + 4, V0, V0 + 2, V0 + 3))
w4.cell(L3 + 4, 2).font = F(7.5, False, DOUX, True); w4.cell(L3 + 4, 2).alignment = ind(0)

# ============================================================================
#  LA FINITION — parce que le classeur se projette et s'imprime
#
#  Un onglet qui sort en paysage sur une page large, avec un pied de page qui
#  le nomme, ne ressemble pas a un fichier de travail. C'est la difference
#  entre « voici mon Excel » et « voici le budget ».
# ============================================================================
from openpyxl.worksheet.properties import PageSetupProperties
def finition(w, couleur, gel="D1"):
    w.sheet_properties.tabColor = couleur
    w.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    w.page_setup.orientation = "landscape"
    w.page_setup.paperSize = w.PAPERSIZE_A4
    w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 0
    w.print_options.horizontalCentered = True
    w.page_margins.left = w.page_margins.right = 0.4
    w.page_margins.top = 0.5; w.page_margins.bottom = 0.5
    w.oddFooter.left.text = "EDUSERVICES · " + w.title
    w.oddFooter.left.size = 8; w.oddFooter.left.font = "Arial"
    w.oddFooter.right.text = "page &P / &N"
    w.oddFooter.right.size = 8; w.oddFooter.right.font = "Arial"
    w.sheet_view.zoomScale = 100
    if gel: w.freeze_panes = gel
for w_, c_, g_ in ((ws, AZUR, "D1"), (w4, AZUR, "D1"), (w2, GRIS, "D1"), (w3, GRIS, "D1")):
    finition(w_, c_, g_)

# ---- l'ordre des onglets : par AUDIENCE, pas par sujet --------------------
#  Deux onglets se montrent en comite -- le geste, puis le budget. Les deux
#  autres sont des reserves : on ne les ouvre que si la question tombe.
wb._sheets = [ws, w4, w2, w3]

wb.save(OUT)
print("écrit :", OUT)
print("  onglet 1 : tableau ① lignes %d-%d, tableau ② lignes %d-%d" % (T1, RT1, T2, RT2))
print("  onglet 2 : poches 12, moyen %d-%d, campus %d-%d, marginal %d, permanents %d"
      % (RB0, RBN, RC0, RCN, RE, RF))
print("  onglet 3 : paramètres %d-%d, mapping %d-%d, formules %d-%d, contrôles %d-%d"
      % (9, PR_FIN - 1, RM0, RMN - 1, RN0, RNN - 1, RK0, RKN - 1))
print("  onglet 4 : résultat 9-11, hypothèses %d-%d, volume %d-%d, CA %d-%d, coûts %d-%d, siège %d-%d, réconciliation %d-%d"
      % (SA0, SA0 + 10, V0, V0 + 12, CA0, CA0 + 5, TP, R_PROPRE, R_SIEGE_T, R_SIEGE, L1, L3))
