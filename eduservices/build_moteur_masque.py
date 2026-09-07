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
VERT_T, ROUGE_T = "5F8A17", "C41822"
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
                 ("new","VOL_NEW"), ("eff","VOL_EFF"), ("cls","VOL_CLASS")): d[a] += num(r[b])
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
TARIF = sum(k[e]["vac"] for e in ENTS) / sum(v[(e,2026)]["hrs"] for e in ENTS)

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
NC = 20
ws.sheet_view.showGridLines = False
for r in range(1, 70):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(FOND)
for r in (1, 2):
    for c in range(1, NC + 1): ws.cell(r, c).fill = fill(INK)
for c in range(1, NC + 1): ws.cell(3, c).fill = fill(AZUR)
ws.cell(1, 2, "EDUSERVICES · le moteur d'acquisition").font = F(7.5, False, PALE)
ws.cell(1, 2).alignment = ind(0)
ws.cell(2, 2, "CALIBRATION & EFFET D'UN +Δ%  —  campus groupé par marque").font = F(14, True, "FFFFFF")
ws.cell(2, 2).alignment = ind(0)
ws.column_dimensions["A"].width = 2.4
ws.column_dimensions["B"].width = 21; ws.column_dimensions["C"].width = 13
for c in range(4, NC + 1): ws.column_dimensions[GL(c)].width = 11.5
for r, h in ((1,14),(2,24),(3,3),(4,22),(5,8),(6,24),(7,8),(8,3),(9,12),(10,28),(11,14),
             (12,8),(13,20),(14,16),(15,10)): ws.row_dimensions[r].height = h

T1, T2 = 19, 43                          # les deux lignes d'en-tete
NL = len(ENTS); RT1 = T1 + NL + 1; RT2 = T2 + NL + 1

# ---- 4. LE GESTE, la seule saisie -----------------------------------------
for c in range(2, NC + 1):
    x = ws.cell(4, c); x.fill = fill(FOND); x.border = Border(bottom=sd(FILET))
ws.cell(4, 2, "LE GESTE  ·  la seule cellule à saisir").font = F(7.5, True, DOUX)
ws.cell(4, 2).alignment = ind(0)
ws.cell(4, 4, "Δ budget d'acquisition").font = F(7.5, True, DOUX); ws.cell(4, 4).alignment = R
g_ = ws.cell(4, 6, 0.08); g_.fill = fill(PANEL); g_.font = F(11, True, AZUR); g_.alignment = Cn
g_.border = Border(*[sd(AZUR)]*4); g_.number_format = '+0.0%;-0.0%;"—"'

# ---- 6. LA PHRASE ---------------------------------------------------------
ws.cell(6, 2, '="Je dépense "&TEXT(H{0},"#,##0 €")&".   J\'encaisse "&TEXT(J{0},"#,##0 €")'
              '&".   Les servir coûte "&TEXT(I{0}*K{0},"#,##0 €")&".   Il me reste "'
              '&TEXT(L{0},"#,##0 €")&"."'.format(RT2)).font = F(13, True, INK)
ws.cell(6, 2).alignment = ind(0)

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
ws.cell(17, 2, "①  CE QUE LA VUE RESTITUE  ·  V_MOTEUR_CAL, une ligne par campus, aucun calcul")
ws.cell(17, 2).font = F(10, True, AZUR); ws.cell(17, 2).alignment = ind(0)
ws.cell(18, 2, "Ces dix-neuf colonnes sortent de la base. Elles sont additives : on peut les sommer, "
               "les filtrer, les remonter à la marque — rien n'y est un ratio.")
ws.cell(18, 2).font = F(7.5, False, DOUX, True); ws.cell(18, 2).alignment = ind(0)

H1 = ["Marque", "Campus", "Leads payants 2024", "Leads payants 2025", "Leads payants 2026",
      "Budget acq. 2024", "Budget acq. 2025", "Budget acq. 2026", "Élasticité",
      "Leads totaux 2026", "Inscrits 2026", "CA nouveaux 2026", "Effectifs 2026",
      "Places 2026", "Classes 2026", "Heures d'enseignement 2026", "Consommables 604+6063",
      "Vacataires 621", "Enseignants permanents 6411"]
NB1 = ['General', 'General', '#,##0', '#,##0', '#,##0', '#,##0" €"', '#,##0" €"', '#,##0" €"', '0.000',
       '#,##0', '#,##0', '#,##0" €"', '#,##0', '#,##0', '#,##0', '#,##0" h"', '#,##0" €"',
       '#,##0" €"', '#,##0" €"']
for i, h in enumerate(H1):
    x = ws.cell(T1, 2 + i, h); x.font = F(8, True, INK)
    x.alignment = ind(0) if i < 2 else WRAP
    x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
ws.row_dimensions[T1].height = 34
ws.row_dimensions[17].height = 20; ws.row_dimensions[18].height = 14

marque_vue = None
for j, e in enumerate(ENTS):
    r = T1 + 1 + j; d24, d25, d26 = (v[(e, y)] for y in (2024, 2025, 2026))
    mq = e.split("_")[0]
    vals = [MQ[mq] if mq != marque_vue else "", LIBC[e],
            d24["pay"], d25["pay"], d26["pay"], d24["acq"], d25["acq"], d26["acq"],
            EL[e], d26["pay"] + d26["org"], d26["new"], d26["ca"], d26["eff"],
            d26["places"], d26["cls"], d26["hrs"], k[e]["odir"], k[e]["vac"], k[e]["perm"]]
    marque_vue = mq
    for i, val in enumerate(vals):
        x = ws.cell(r, 2 + i, val); x.fill = fill(VUE); x.number_format = NB1[i]
        x.font = F(8, i == 0, INK if i else AZUR); x.alignment = ind(0) if i < 2 else R
        x.border = Border(bottom=sd("EAF0F6"))

for i in range(19):
    c = 2 + i; x = ws.cell(RT1, c)
    x.fill = fill(GRIS); x.font = F(8, True, INK); x.number_format = NB1[i]
    x.border = Border(top=sd(INK), bottom=sd(INK))
    x.alignment = ind(0) if i < 2 else R
    if i == 0: x.value = "GROUPE"
    elif i == 1: x.value = "14 campus"
    elif i == 8: x.value = "—"; x.alignment = R      # une élasticité ne se somme pas
    else: x.value = "=SUM({0}{1}:{0}{2})".format(GL(c), T1 + 1, RT1 - 1)

# ---- 41-58. TABLEAU (2) : CE QUE LE MASQUE CALCULE -------------------------
# Chaque cellule pointe le tableau du dessus. On clique, on remonte à la vue.
ws.cell(41, 2, "②  CE QUE LE MASQUE CALCULE  ·  chaque formule pointe une cellule du tableau ①")
ws.cell(41, 2).font = F(10, True, "B26B00"); ws.cell(41, 2).alignment = ind(0)
ws.cell(42, 2, "Rien n'est stocké ici. Cliquez une cellule : la formule remonte au tableau du dessus, "
               "et la seule saisie du classeur est F4.")
ws.cell(42, 2).font = F(7.5, False, DOUX, True); ws.cell(42, 2).alignment = ind(0)

H2 = ["Marque", "Campus", "Conversion lead → inscrit", "CA par inscrit",
      "Consommables / élève", "Places libres", "Δ budget", "Inscrits gagnés",
      "CA gagné", "Coût marginal / élève", "EBITDA gagné", "CAC marginal"]
NB2 = ['General', 'General', '0.0%', '#,##0" €"', '#,##0" €"', '#,##0', '#,##0" €"', '#,##0.0',
       '#,##0" €"', '#,##0" €"', '#,##0" €"', '#,##0" €"']
for i, h in enumerate(H2):
    x = ws.cell(T2, 2 + i, h); x.font = F(8, True, INK)
    x.alignment = ind(0) if i < 2 else WRAP
    x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
ws.row_dimensions[T2].height = 34
ws.row_dimensions[41].height = 20; ws.row_dimensions[42].height = 14

def ligne2(r2, r1):
    """Les dix formules du masque, ecrites une seule fois pour les 14 campus et le groupe."""
    return {
        4:  "=IFERROR(L{0}/K{0},0)".format(r1),                          # conversion
        5:  "=IFERROR(M{0}/L{0},0)".format(r1),                          # CA par inscrit
        6:  "=IFERROR(R{0}/N{0},0)".format(r1),                          # consommables/eleve
        7:  "=O{0}-N{0}".format(r1),                                     # places libres
        8:  "=I{0}*$F$4".format(r1),                                     # Delta budget
        9:  "=F{0}*((1+$F$4)^J{0}-1)*D{1}".format(r1, r2),               # inscrits gagnes
        10: "=I{0}*E{0}".format(r2),                                     # CA gagne
        11: "=IF(I{0}<=G{0},F{0},F{0}+S{1}/O{1})".format(r2, r1),        # cout marginal
        12: "=J{0}-H{0}-I{0}*K{0}".format(r2),                           # EBITDA gagne
        13: "=IFERROR(H{0}/I{0},0)".format(r2)}                          # CAC marginal

marque_calc = None
for j, e in enumerate(ENTS):
    r2, r1 = T2 + 1 + j, T1 + 1 + j; mq = e.split("_")[0]
    ws.cell(r2, 2, MQ[mq] if mq != marque_calc else ""); marque_calc = mq
    ws.cell(r2, 3, "=C%d" % r1)
    for c, f in ligne2(r2, r1).items(): ws.cell(r2, c, f)
    for i in range(12):
        x = ws.cell(r2, 2 + i); x.fill = fill(CALC); x.number_format = NB2[i]
        x.font = F(8, i == 0, INK); x.alignment = ind(0) if i < 2 else R
        x.border = Border(bottom=sd("F5E6D2"))

for c, f in ligne2(RT2, RT1).items(): ws.cell(RT2, c, f)
# au groupe, quatre colonnes se somment et le cout marginal se pondere par les inscrits
ws.cell(RT2, 2, "GROUPE"); ws.cell(RT2, 3, "14 campus")
for c in (7, 8, 9, 10, 12):
    ws.cell(RT2, c, "=SUM({0}{1}:{0}{2})".format(GL(c), T2 + 1, RT2 - 1))
ws.cell(RT2, 11, "=IFERROR(SUMPRODUCT(I{1}:I{2},K{1}:K{2})/I{0},0)".format(RT2, T2 + 1, RT2 - 1))
for i in range(12):
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
w2.cell(6, 2, "AW_002_000004_000001 est au grain CAMPUS × COMPTE. Un coût par élève et par programme "
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
                "=IFERROR({0}Q34/C{1},0)".format(M, RBN), "=IFERROR({0}S34/{0}Q34,0)".format(M),
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
                  "={0}N{1}".format(M, r1), "={0}G{1}".format(M, r2), "={0}R{1}".format(M, r1),
                  "=IFERROR(E%d/C%d,0)" % (r, r), "={0}Q{1}".format(M, r1),
                  "={0}S{1}".format(M, r1), "=IFERROR(H{0}/{1}O{2},0)".format(r, M, r1),
                  "={0}T{1}".format(M, r1), "=IFERROR(J%d/C%d,0)" % (r, r),
                  "=IFERROR(D%d/C%d,0)" % (r, r)], NB4)
RCN = RC0 + len(ENTS)
ligne(w2, RCN, ["GROUPE · 14 campus"] +
      ["=SUM({0}{1}:{0}{2})".format(GL(c), RC0, RCN - 1) for c in (3, 4, 5)] +
      ["=IFERROR(E{0}/C{0},0)".format(RCN)] +
      ["=SUM({0}{1}:{0}{2})".format(GL(c), RC0, RCN - 1) for c in (7, 8)] +
      ["=IFERROR(H{0}/{1}O{2},0)".format(RCN, M, RT1), "=SUM(J{0}:J{1})".format(RC0, RCN - 1),
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

# ---- (5) ET LES ENSEIGNANTS PERMANENTS ? ----------------------------------
#  La question qui vient toujours. Reponse : ils sont dans le modele, alloues
#  a l'heure comme les vacataires -- mais ils ne sont pas VARIABLES. Un poste
#  est engage a l'annee ; il est paye pareil pour 24 ou 32 eleves dans la
#  salle. Le tableau montre les DIX-NEUF comptes de charges et, pour chacun,
#  la seule question qui compte : bouge-t-il quand un eleve de plus arrive ?
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
# Volontairement AUCUN lien ici. Ces montants viennent de la comptabilite ;
# le tableau (1) porte les memes grandeurs vues par la vue. Les lier ferait
# disparaitre les quatre reconciliations de l'onglet 3 -- un controle qui
# compare une cellule a un lien vers elle-meme ne controle rien.
LIEN = {}

RF = REN + 3
titre(w2, RF, "⑤  Et les enseignants permanents, ils sont où ?",
      "Dans le modèle, et alloués à l'heure comme les vacataires — mais pas dans le coût variable. "
      "Voici les vingt comptes de charges du P&L et, pour chacun, la seule question qui compte.",
      ROUGE_T)
w2.cell(RF + 2, 2, "Un professeur permanent est un ENGAGEMENT DE CAPACITÉ, pas un coût à l'élève : "
                   "il est payé pareil que la salle contienne 24 ou 32 étudiants. C'est pour cela "
                   "qu'il pèse le plus lourd du coût d'enseignement et qu'il ne figure quand même pas "
                   "dans le coût marginal. Le vacataire, lui, est la seule ressource enseignante que "
                   "l'on achète à la classe — et le 621 est du personnel EXTÉRIEUR : une facture, "
                   "donc sans charges sociales 645 en plus.")
w2.cell(RF + 2, 2).font = F(8, False, INK); w2.cell(RF + 2, 2).alignment = ind(0)
w2.row_dimensions[RF + 2].height = 16

RG = RF + 5
w2.cell(RG - 1, 2, "Ces montants sont restitués par la COMPTABILITÉ (AW_002_000004_000001), et non "
                   "repris du tableau ① : c'est ce qui permet de les réconcilier avec la vue — "
                   "quatre contrôles, onglet « Intégration & contrôles ».")
w2.cell(RG - 1, 2).font = F(7.5, False, DOUX, True); w2.cell(RG - 1, 2).alignment = ind(0)
entete(w2, RG, ["Compte et libellé", None, "Montant 2026", "Part des charges", "Poche du modèle",
                "Clé d'allocation", "Comportement", "Bouge si un élève de plus arrive ?"], 30)
NB6 = ['General', 'General', '#,##0" €"', '0.0%', 'General', 'General', 'General', 'General']
RG0 = RG + 1
for j, (cpt, lib, poche, cle, comp, bouge, coul) in enumerate(CPT):
    r = RG0 + j
    ligne(w2, r, ["%s · %s" % (cpt, lib), None, LIEN.get(cpt, MTT[cpt]), "=IFERROR(D{0}/$D${1},0)".format(r, RG0 + len(CPT)),
                  poche, cle, comp, bouge], NB6, gauche=(1, 4, 5, 6, 7),
          fond=VUE if cpt in LIEN else PANEL)
    w2.cell(r, 8).font = F(8, True, coul); w2.cell(r, 9).font = F(8, False, coul)
RGN = RG0 + len(CPT)
ligne(w2, RGN, ["TOTAL DES CHARGES 2026  ·  dotations incluses", None,
                "=SUM(D{0}:D{1})".format(RG0, RGN - 1), 1.0, "", "", "", ""],
      NB6, fond=GRIS, gras=True, trait=INK, gauche=(1, 4, 5, 6, 7))
CA26 = sum(MTT[a] for a in ("706", "7062", "708"))
ligne(w2, RGN + 1, ["Chiffre d'affaires 2026  ·  706 + 7062 + 708", None,
                    CA26, "", "", "", "", ""],
      NB6, fond=VUE, gras=True, gauche=(1, 4, 5, 6, 7))
ligne(w2, RGN + 2, ["EBITDA 2026  =  CA − charges hors dotations", None,
                    "=D{0}-D{1}+D{2}".format(RGN + 1, RGN, RG0 + len(CPT) - 1),
                    "", "", "", "", ""],
      NB6, fond=GRIS, gras=True, trait=INK, gauche=(1, 4, 5, 6, 7))
w2.cell(RGN + 2, 4).font = F(9, True, VERT_T)
w2.cell(RGN + 4, 2, '="Sur "&TEXT(D{0},"#,##0 €")&" de charges, "&TEXT(D{1}+D{2},"#,##0 €")&" seulement '
                    'bougent quand un élève de plus s\'assoit — soit "&TEXT((D{1}+D{2})/D{0},"0.0 %")'
                    '&". Tout le reste est de la capacité déjà engagée : c\'est précisément ce qui rend '
                    'le geste d\'acquisition aussi rentable tant qu\'il reste des places."'
                    .format(RGN, RG0, RG0 + 1))
w2.cell(RGN + 4, 2).font = F(9, True, INK); w2.cell(RGN + 4, 2).alignment = ind(0)
w2.row_dimensions[RGN + 4].height = 18
for c in range(2, NC2 + 1):
    w2.cell(RGN + 4, c).fill = fill(PANEL)
    w2.cell(RGN + 4, c).border = Border(top=sd(AZUR), bottom=sd(AZUR))
CV_FIN = RGN + 4

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
    ("F", "Leads payants 2026",           "LEAD_PAY_2026",  "mesure",    "base du geste"),
    ("G", "Budget acq. 2024",             "SPEND_ACQ_2024", "mesure",    ""),
    ("H", "Budget acq. 2025",             "SPEND_ACQ_2025", "mesure",    ""),
    ("I", "Budget acq. 2026",             "SPEND_ACQ_2026", "mesure",    "= compte 6231"),
    ("J", "Élasticité",                   "ELASTICITE",     "NON additive", "régression log-log, reste au campus"),
    ("K", "Leads totaux 2026",            "LEAD_TOT_N",     "mesure",    "dénominateur de la conversion"),
    ("L", "Inscrits 2026",                "INSCRITS_N",     "mesure",    "numérateur de la conversion"),
    ("M", "CA nouveaux 2026",             "CA_NEW_N",       "mesure",    ""),
    ("N", "Effectifs 2026",               "EFFECTIFS_N",    "mesure",    ""),
    ("O", "Places 2026",                  "PLACES_N",       "mesure",    "classes × capacité"),
    ("P", "Classes 2026",                 "CLASSES_N",      "mesure",    ""),
    ("Q", "Heures d'enseignement 2026",   "HEURES_N",       "mesure",    "À AJOUTER À LA VUE"),
    ("R", "Consommables 604+6063",        "COUT_CONSO_N",   "mesure",    ""),
    ("S", "Vacataires 621",               "COUT_VACAT_N",   "mesure",    ""),
    ("T", "Enseignants permanents 6411",  "COUT_PERM_N",    "mesure",    "À AJOUTER À LA VUE")]
RM = PR_FIN + 3
titre(w3, RM, "ⓑ  Le mapping  ·  colonne du classeur ↔ colonne de V_MOTEUR_CAL",
      "Le tableau ① de l'onglet « Le moteur » est la vue, colonne pour colonne. Deux colonnes sont "
      "à ajouter à la vue — elles sont signalées en rouge, et tagetik/V_MOTEUR_CAL.sql les porte déjà.")
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
FORM = [
    ("F4",  "Δ budget d'acquisition", "SAISIE", "la seule cellule modifiable du classeur"),
    ("D", "Conversion lead → inscrit", "=IFERROR(L20/K20,0)",
     "INSCRITS_N ÷ LEAD_TOT_N — jamais pré-calculée, sinon la ligne groupe se trompe"),
    ("E", "CA par inscrit", "=IFERROR(M20/L20,0)", "CA_NEW_N ÷ INSCRITS_N"),
    ("F", "Consommables / élève", "=IFERROR(R20/N20,0)", "COUT_CONSO_N ÷ EFFECTIFS_N"),
    ("G", "Places libres", "=O20-N20", "PLACES_N − EFFECTIFS_N : la borne physique du geste"),
    ("H", "Δ budget", "=I20*$F$4", "le geste, appliqué au budget 2026"),
    ("I", "Inscrits gagnés", "=F20*((1+$F$4)^J20-1)*D44",
     "leads payants × l'effet d'élasticité, converti au taux du campus"),
    ("J", "CA gagné", "=I44*E44", "inscrits gagnés × CA par inscrit"),
    ("K", "Coût marginal / élève", "=IF(I44<=G44,F44,F44+S20/O20)",
     "consommables seuls, + quote-part vacataire si la classe doit ouvrir"),
    ("L", "EBITDA gagné", "=J44-H44-I44*K44", "CA gagné − Δ budget − coût de service"),
    ("M", "CAC marginal", "=IFERROR(H44/I44,0)", "Δ budget ÷ inscrits gagnés")]
RN = RMN + 2
titre(w3, RN, "ⓒ  Les formules du masque  ·  la ligne 44, campus Ipac Montpellier",
      "Toutes les autres lignes sont la même formule, décalée. Aucune n'utilise de constante : "
      "chacune pointe le tableau ① ou la saisie F4.", "B26B00")
entete(w3, RN + 3, ["Mesure", "Col.", "Formule du classeur", None, "Ce qu'elle dit"], 26)
NBF = ['General'] * 5
RN0 = RN + 4
for j, (col, lib, f, dit) in enumerate(FORM):
    r = RN0 + j
    # garde-fou : la doc ne peut pas deriver du classeur. Si la formule ecrite
    # ici ne correspond plus a celle du masque, la generation s'arrete.
    if j: assert ws["%s44" % col].value == f, "doc desynchronisee : %s44" % col
    ligne(w3, r, [lib, col, f, None, dit], NBF, fond=CALC if j else PANEL, gauche=(1, 2, 3, 4))
    w3.cell(r, 4).data_type = "s"          # une formule MONTREE, pas evaluee
    w3.cell(r, 4).font = Font(name="Consolas", size=7.5, color=INK if j else AZUR, bold=not j)
    if not j:
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
CV = "'Le coût variable'!"
R6231, R604, R6063, R621, R6411 = RG0 + 4, RG0, RG0 + 1, RG0 + 2, RG0 + 3
CTRL = [
    ("Budget d'acquisition : dépense CRM 2026 = compte 6231",
     "={0}I34".format(M), "={0}D{1}".format(CV, R6231), '#,##0" €"',
     "socle CRM contre comptabilité"),
    ("Consommables : comptes 604 + 6063 = COUT_CONSO_N",
     "={0}D{1}+{0}D{2}".format(CV, R604, R6063), "={0}R34".format(M), '#,##0" €"',
     "comptes contre agrégat de la vue"),
    ("Vacataires : compte 621 = COUT_VACAT_N",
     "={0}D{1}".format(CV, R621), "={0}S34".format(M), '#,##0" €"',
     "comptes contre agrégat de la vue"),
    ("Permanents : compte 6411 = COUT_PERM_N",
     "={0}D{1}".format(CV, R6411), "={0}T34".format(M), '#,##0" €"',
     "comptes contre agrégat de la vue"),
    ("Effectifs : grain programme = grain campus",
     "={0}C{1}".format(CV, RBN), "={0}N34".format(M), '#,##0',
     "cycle × modalité contre campus"),
    ("Allocation : consommables alloués aux programmes = total réseau",
     "=SUMPRODUCT({0}C{1}:C{2},{0}G{1}:G{2})".format(CV, RB0, RBN - 1), "={0}R34".format(M),
     '#,##0" €"', "la clé EFFECTIFS ne perd rien"),
    ("EBITDA gagné : CA gagné − Δ budget − coût de service",
     "={0}J58-{0}H58-{0}I58*{0}K58".format(M), "={0}L58".format(M), '#,##0" €"',
     "additivité de la ligne groupe"),
    ("Régime du coût marginal : inscrits gagnés ≤ places libres",
     "={0}I58".format(M), "={0}G58".format(M), '#,##0',
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
w3.cell(RKN + 3, 2, "① ajouter HEURES_N et COUT_PERM_N à V_MOTEUR_CAL (le .sql du dépôt les porte).  "
                    "② brancher le tableau ① sur la vue, une ligne par campus, hiérarchie MARQUE ▸ CAMPUS.  "
                    "③ le tableau ② est un masque de saisie : seule F4 est ouverte.  "
                    "④ l'onglet « Le coût variable » ne lit que le tableau ① et les paramètres ci-dessus.")
w3.cell(RKN + 3, 2).font = F(7.5, False, DOUX, True); w3.cell(RKN + 3, 2).alignment = ind(0)

# ============================================================================
#  ONGLET 4 — PROJETER LES COUTS 2027
#
#  LA QUESTION EST JUSTE, ET LA REPONSE HONNETE COMMENCE PAR UN AVEU.
#
#  Le moteur ne projette RIEN. C'est un modele MARGINAL : il applique des couts
#  unitaires 2026 a un volume marginal, et repond a « si je bouge le budget
#  d'acquisition, qu'est-ce que ca change ». Cette reponse ne depend pas de
#  l'inflation 2027 -- elle depend du cout du siege suivant. Valide pour un
#  delta ; ce n'est pas un budget.
#
#  Et il n'y a rien a restituer : la comptabilite ne contient AUCUN cout 2027.
#  Les deux seules lignes 2027 sont techniques (TEC_PL, TEC_EBITDA) et on ne
#  les utilise pas. Le 2027 se CONSTRUIT.
#
#  Il se construit avec UN INDUCTEUR PAR COMPORTEMENT -- et le comportement,
#  c'est exactement la colonne du tableau (5). D'ou cet onglet : la colonne
#  « comportement » devient une regle de projection.
#
#      Variable      604 6063     effectifs x inflation
#      Semi-variable 621          CLASSES x inflation -- et non pas effectifs :
#                                 tant qu'aucune classe n'ouvre, le vacataire
#                                 ne prend que son prix
#      Capacite      6411         postes x politique salariale
#      Assis         645 6331     la masse salariale, au prorata
#                    6333
#      Structure     613 615 616  inflation moins l'effort de productivite
#                    625 63511
#                    6413 6226
#                    626 6281
#      Siege         6414         politique salariale
#                    6236         le budget de marque, qui est une decision
#      Levier        6231         LE GESTE lui-meme, lie a la saisie F4 du
#                                 premier onglet
#      Hors EBITDA   6811         le plan d'amortissement
#
#  CE QUE LES TROIS EXERCICES REELS DISENT, ET QUI CADRE LES SAISIES :
#  tous les comptes de charges progressent au MEME rythme, +4,58 % puis
#  +4,77 %, pendant que les effectifs montent de +5,8 % puis +6,2 % et que le
#  nombre de classes ne bouge pas -- 135, trois ans de suite. C'est du levier
#  operationnel pur : la charge par eleve tombe de 6 281 a 6 183 EUR et la
#  marge passe de 15,3 % a 16,7 %.
#
#  ET LA MARCHE NE TOMBE PAS EN 2027. Le premier campus a saturer est MBway
#  Paris, a +16,2 % d'effectifs. A +6,2 % l'an, il tient jusqu'en 2029. C'est
#  pour cela que 621 ne prend que l'inflation en 2027, et c'est verifiable
#  dans le classeur, pas affirme.
# ============================================================================
w4 = wb.create_sheet("Projection 2027")
NC4 = 12
bandeau(w4, NC4, "PROJETER LES COÛTS 2027  —  un inducteur par comportement", 76)
w4.column_dimensions["A"].width = 2.4; w4.column_dimensions["B"].width = 34
for c, wd in ((3, 14), (4, 15), (5, 24), (6, 13), (7, 13), (8, 15), (9, 13), (10, 26),
              (11, 14), (12, 14)): w4.column_dimensions[GL(c)].width = wd

w4.cell(5, 2, "La base 2027 n'existe pas. Il n'y a rien à restituer.").font = F(12, True, INK)
w4.cell(5, 2).alignment = ind(0); w4.row_dimensions[5].height = 22
w4.cell(6, 2, "Les deux seules lignes 2027 de la comptabilité sont techniques. Le 2027 se construit — "
              "et le moteur, lui, ne le construit pas : c'est un modèle MARGINAL, qui applique des coûts "
              "unitaires 2026 à un volume marginal. Ici on fait l'autre travail : une règle de projection "
              "par comportement, et le comportement est la colonne du tableau ⑤.")
w4.cell(6, 2).font = F(8, False, DOUX, True); w4.cell(6, 2).alignment = ind(0)
w4.row_dimensions[6].height = 16

# ---- (a) LES NEUF SAISIES -------------------------------------------------
titre(w4, 8, "ⓐ  Les neuf saisies  ·  chacune est une décision, et chacune a un propriétaire",
      "Six d'entre elles sont les leviers de l'onglet Cadrage, reprises telles quelles. La septième "
      "n'est pas saisie ici : elle est LIÉE au geste du premier onglet.")
entete(w4, 11, ["Saisie", None, None, "Valeur retenue", None, "D'où elle vient"], 24)
SAIS = [("Croissance des effectifs 2027",                    0.062,  "constatée 2026 : +6,2 %"),
        ("Hausse tarifaire",                                 0.0029, "levier Cadrage · croissance"),
        ("Inflation des charges externes",                   0.020,  "levier Cadrage · coûts"),
        ("Effort de productivité achats & structure",        0.0185, "levier Cadrage · coûts"),
        ("Politique salariale sur la masse permanente",      0.025,  "levier Cadrage · coûts"),
        ("Variation des effectifs permanents",               0.040,  "levier Cadrage · coûts"),
        ("Δ budget d'acquisition  (6231)",     "='Le moteur'!F4", "LIÉ au geste, onglet « Le moteur »"),
        ("Δ budget de marque  (6236)",                       0.100,  "levier Cadrage · croissance"),
        ("Dotations aux amortissements",                     0.020,  "plan d'amortissement")]
SA0 = 12
for j, (lab, val, src) in enumerate(SAIS):
    r = SA0 + j
    for c in range(2, NC4 + 1):
        x = w4.cell(r, c); x.fill = fill(PARM); x.border = Border(bottom=sd("E6E2D6"))
    w4.cell(r, 2, lab).font = F(8, True, INK); w4.cell(r, 2).alignment = ind(0)
    x = w4.cell(r, 5, val); x.number_format = '+0.00%;-0.00%;"—"'
    x.font = F(9, True, AZUR if isinstance(val, str) else INK); x.alignment = R
    x.fill = fill(PANEL); x.border = Border(*[sd(AZUR if isinstance(val, str) else "C9C3B0")] * 4)
    w4.cell(r, 7, src).font = F(7.5, False, DOUX, True); w4.cell(r, 7).alignment = ind(0)
EFF, TAR, INF, PRD, SAL, POS, ACQ, MRQ, DOT = ["$E$%d" % (SA0 + i) for i in range(9)]

# ---- (b) LE VOLUME 2027, et la marche qui ne tombe pas --------------------
titre(w4, 22, "ⓑ  Le volume 2027  ·  et la seule question qui fasse bouger le 621",
      "Un vacataire de plus ne se paie pas parce qu'il y a des élèves de plus : il se paie parce "
      "qu'une CLASSE ouvre. Tant qu'aucune n'ouvre, le 621 ne prend que son prix.")
entete(w4, 25, ["Grandeur", None, None, "2027", None, "Lecture"], 24)
VOL = [("Effectifs 2026",                        "='Le moteur'!N%d" % RT1,     '#,##0',  ""),
       ("Effectifs 2027",                        "=E26*(1+%s)" % EFF,          '#,##0',  "la croissance saisie"),
       ("Places du réseau",                      "='Le moteur'!O%d" % RT1,     '#,##0',  "135 classes, inchangées depuis 2024"),
       ("Classes 2026",                          "='Le moteur'!P%d" % RT1,     '#,##0',  ""),
       ("Capacité moyenne d'une classe",         "=IFERROR(E28/E29,0)",        '#,##0.0', ""),
       ("Croissance possible avant saturation",  "='Le coût variable'!L%d" % RCN, '0.0%',
        "le premier campus qui sature : MBway Paris"),
       ("Classes à ouvrir en 2027",              "=MAX(0,ROUNDUP((E27-E28)/E30,0))", '#,##0',
        "aucune : la marche ne tombe pas en 2027"),
       ("Classes 2027",                          "=E29+E32",                   '#,##0',  ""),
       ("Inducteur du compte 621",               "=IFERROR(E33/E29,0)",        '0.000',
        "le ratio de CLASSES, pas d'effectifs")]
for j, (lab, f, nf, lec) in enumerate(VOL):
    r = 26 + j
    for c in range(2, NC4 + 1):
        w4.cell(r, c).fill = fill(PANEL); w4.cell(r, c).border = Border(bottom=sd("EDEEF0"))
    w4.cell(r, 2, lab).font = F(8, j in (1, 5, 6, 8), INK); w4.cell(r, 2).alignment = ind(0)
    x = w4.cell(r, 5, f); x.number_format = nf; x.alignment = R
    x.font = F(8, j in (1, 5, 6, 8), ROUGE_T if j == 5 else INK)
    w4.cell(r, 7, lec).font = F(7.5, False, DOUX, True); w4.cell(r, 7).alignment = ind(0)
w4.cell(35, 2, "À +6,2 % l'an, MBway Paris tient jusqu'en 2029. C'est vérifiable ligne à ligne dans "
               "l'onglet « Le coût variable », dernière colonne — ce n'est pas une affirmation.")
w4.cell(35, 2).font = F(7.5, False, DOUX, True); w4.cell(35, 2).alignment = ind(0)

# ---- (c) LA PROJECTION, COMPTE PAR COMPTE --------------------------------
titre(w4, 38, "ⓒ  La projection, compte par compte", 
      "Montant 2026 lié au tableau ⑤. Chaque compte reçoit un effet volume et un effet prix — "
      "jamais les deux au hasard : c'est son comportement qui les désigne.", "B26B00")
entete(w4, 41, ["Compte et libellé", None, "Montant 2026", "Inducteur de volume", "Effet volume",
                "Effet prix", "Montant 2027", "Variation", "Ce qui décide"], 30)
RP0 = 42
LIG = {c[0]: RP0 + i for i, c in enumerate(CPT)}
MASSE = "=({0}+{1}+{2})/({3}+{4}+{5})".format(*["H%d" % LIG[a] for a in ("6411", "6413", "6414")]
                                              + ["D%d" % LIG[a] for a in ("6411", "6413", "6414")])
IDX = "=1+%s-%s" % (INF, PRD)
PROJ = {
 "604":  ("=1+%s" % EFF, "=1+%s" % INF, "effectifs", "le remplissage"),
 "6063": ("=1+%s" % EFF, "=1+%s" % INF, "effectifs", "le remplissage"),
 "621":  ("=$E$34",      "=1+%s" % INF, "CLASSES, pas effectifs", "l'ouverture d'une classe"),
 "6411": ("=1+%s" % POS, "=1+%s" % SAL, "postes permanents", "le recrutement"),
 "6231": (1,             "=1+%s" % ACQ, "—", "LE GESTE — onglet « Le moteur »"),
 "6413": (1,             "=1+%s" % SAL, "—", "la politique salariale"),
 "645":  (MASSE,         1,             "la masse salariale", "assis sur la masse"),
 "613":  (1, IDX, "—", "l'indexation, moins l'effort"),
 "615":  (1, IDX, "—", "l'indexation, moins l'effort"),
 "616":  (1, IDX, "—", "l'indexation, moins l'effort"),
 "625":  (1, IDX, "—", "l'indexation, moins l'effort"),
 "63511":(1, IDX, "—", "la fiscalité locale"),
 "6236": (1,             "=1+%s" % MRQ, "—", "le budget de marque"),
 "6414": (1,             "=1+%s" % SAL, "—", "la politique salariale"),
 "6226": (1, IDX, "—", "l'indexation, moins l'effort"),
 "626":  (1, IDX, "—", "l'indexation, moins l'effort"),
 "6281": (1, IDX, "—", "l'indexation, moins l'effort"),
 "6331": (MASSE, 1, "la masse salariale", "assis sur la masse"),
 "6333": (MASSE, 1, "la masse salariale", "assis sur la masse"),
 "6811": (1,             "=1+%s" % DOT, "—", "le plan d'amortissement")}
NB7 = ['General', 'General', '#,##0" €"', 'General', '0.000', '0.000', '#,##0" €"', '+0.0%;-0.0%', 'General']
for j, (cpt, lib, poche, cle, comp, bouge, coul) in enumerate(CPT):
    r = RP0 + j; vol, prix, ind_, dec = PROJ[cpt]
    ligne(w4, r, ["%s · %s" % (cpt, lib), None, "='Le coût variable'!D%d" % (RG0 + j),
                  ind_, vol, prix, "=D{0}*F{0}*G{0}".format(r), "=IFERROR(H{0}/D{0}-1,0)".format(r),
                  dec], NB7, gauche=(1, 3, 8), fond=CALC)
    w4.cell(r, 5).font = F(8, False, DOUX); w4.cell(r, 10).font = F(8, False, coul)
    w4.cell(r, 8).font = F(8, True, INK)
RPN = RP0 + len(CPT)
ligne(w4, RPN, ["TOTAL DES CHARGES  ·  dotations incluses", None,
                "=SUM(D{0}:D{1})".format(RP0, RPN - 1), "", "", "",
                "=SUM(H{0}:H{1})".format(RP0, RPN - 1),
                "=IFERROR(H{0}/D{0}-1,0)".format(RPN), ""],
      NB7, fond=GRIS, gras=True, trait=INK, gauche=(1, 3, 8))
ligne(w4, RPN + 1, ["Chiffre d'affaires", None, "='Le coût variable'!D%d" % (RGN + 1), "volume × prix",
                    "=1+%s" % EFF, "=1+%s" % TAR, "=D{0}*F{0}*G{0}".format(RPN + 1),
                    "=IFERROR(H{0}/D{0}-1,0)".format(RPN + 1), "le socle CRM et le tarif"],
      NB7, fond=VUE, gras=True, gauche=(1, 3, 8))
ligne(w4, RPN + 2, ["EBITDA  ·  hors dotations", None,
                    "=D{0}-D{1}+D{2}".format(RPN + 1, RPN, RP0 + len(CPT) - 1), "", "", "",
                    "=H{0}-H{1}+H{2}".format(RPN + 1, RPN, RP0 + len(CPT) - 1),
                    "=IFERROR(H{0}/D{0}-1,0)".format(RPN + 2), ""],
      NB7, fond=GRIS, gras=True, trait=INK, gauche=(1, 3, 8))
ligne(w4, RPN + 3, ["Marge d'EBITDA", None, "=IFERROR(D{0}/D{1},0)".format(RPN + 2, RPN + 1), "", "", "",
                    "=IFERROR(H{0}/H{1},0)".format(RPN + 2, RPN + 1),
                    "=H{0}-D{0}".format(RPN + 3), ""],
      NB7, fond=PANEL, gras=True, gauche=(1, 3, 8))
for c in (4, 8): w4.cell(RPN + 3, c).number_format = '0.00%'
w4.cell(RPN + 3, 9).number_format = '+0.00" pt";-0.00" pt"'
for c in (4, 8): w4.cell(RPN + 2, c).font = F(10, True, VERT_T)
w4.conditional_formatting.add("I{0}:I{1}".format(RP0, RPN - 1),
    ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                   mid_color=HM_MED, end_type="max", end_color=HM_BAS))

for c in range(2, NC4 + 1):
    w4.cell(RPN + 5, c).fill = fill(PANEL); w4.cell(RPN + 5, c).border = Border(top=sd(AZUR))
    w4.cell(RPN + 6, c).fill = fill(PANEL); w4.cell(RPN + 6, c).border = Border(bottom=sd(AZUR))
w4.cell(RPN + 5, 2, '="2027 : "&TEXT(H{0},"#,##0 €")&" d\'EBITDA, marge "&TEXT(H{1},"0.0 %")'
                    '&"  —  contre "&TEXT(D{1},"0.0 %")&" en 2026. Le gain ne vient pas d\'une '
                    'économie : il vient de "&TEXT(E27-E26,"#,##0")&" élèves de plus dans des '
                    'classes déjà ouvertes."'.format(RPN + 2, RPN + 3))
w4.cell(RPN + 5, 2).font = F(9, True, INK); w4.cell(RPN + 5, 2).alignment = ind(0)
w4.row_dimensions[RPN + 5].height = 18
w4.cell(RPN + 6, 2, "Le jour où une classe doit ouvrir, la ligne 621 change d'inducteur toute seule — "
                    "et c'est là que la marge s'arrête de monter. Le classeur dit quand : "
                    "onglet « Le coût variable », dernière colonne.")
w4.cell(RPN + 6, 2).font = F(7.5, False, DOUX, True); w4.cell(RPN + 6, 2).alignment = ind(0)


wb.save(OUT)
print("écrit :", OUT)
print("  onglet 1 : tableau ① lignes %d-%d, tableau ② lignes %d-%d" % (T1, RT1, T2, RT2))
print("  onglet 2 : poches %d, moyen %d-%d, campus %d-%d, marginal %d, comptes %d-%d"
      % (12, RB0, RBN, RC0, RCN, RE, RG0, RGN))
print("  onglet 3 : paramètres %d-%d, mapping %d-%d, formules %d-%d, contrôles %d-%d"
      % (9, PR_FIN - 1, RM0, RMN - 1, RN0, RNN - 1, RK0, RKN - 1))
