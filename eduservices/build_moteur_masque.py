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
"""
import csv, math, openpyxl
from collections import defaultdict
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.utils import get_column_letter as GL

OUT = "MOTEUR_MASQUE.xlsx"
INK, AZUR, ROUGE, VERT = "262626", "007AC3", "E5202E", "85BC20"
PALE, GRIS = "A6D0EA", "E7E6E6"
VERT_T, ROUGE_T = "5F8A17", "C41822"
FOND, PANEL, FILET, DOUX = "F5F6F7", "FFFFFF", "D5D7DA", "6B7075"
HM_BAS, HM_MED, HM_HAUT = "F6C9CC", "F7F7F5", "DCEBC0"
VUE, CALC = "E8F1F9", "FDF3E7"          # les deux fonds qui disent l'origine
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
    if r["ACCOUNT"] in ("604", "6063"):  k[r["ENTITY"]]["odir"] += num(r["AMOUNT"])
ENTS = sorted({e for e, _ in v})
MQ = {"IPAC":"Ipac Bachelor Factory", "ISCOM":"ISCOM", "MBWAY":"MBway",
      "PIGIER":"Pigier", "TUNON":"Tunon"}
LIBC = {"IPAC_MTP":"Montpellier","IPAC_NAN":"Nantes","IPAC_REN":"Rennes",
        "ISCOM_LIL":"Lille","ISCOM_PAR":"Paris","ISCOM_TLS":"Toulouse",
        "MBWAY_BOR":"Bordeaux","MBWAY_LYO":"Lyon","MBWAY_NAN":"Nantes","MBWAY_PAR":"Paris",
        "PIGIER_BOR":"Bordeaux","PIGIER_LYO":"Lyon","TUNON_LYO":"Lyon","TUNON_PAR":"Paris"}
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
NC = 18
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
ws.cell(18, 2, "Ces dix-sept colonnes sortent de la base. Elles sont additives : on peut les sommer, "
               "les filtrer, les remonter à la marque — rien n'y est un ratio.")
ws.cell(18, 2).font = F(7.5, False, DOUX, True); ws.cell(18, 2).alignment = ind(0)

H1 = ["Marque", "Campus", "Leads payants 2024", "Leads payants 2025", "Leads payants 2026",
      "Budget acq. 2024", "Budget acq. 2025", "Budget acq. 2026", "Élasticité",
      "Leads totaux 2026", "Inscrits 2026", "CA nouveaux 2026", "Effectifs 2026",
      "Places 2026", "Classes 2026", "Consommables 604+6063", "Vacataires 621"]
NB1 = ['General', 'General', '#,##0', '#,##0', '#,##0', '#,##0" €"', '#,##0" €"', '#,##0" €"', '0.000',
       '#,##0', '#,##0', '#,##0" €"', '#,##0', '#,##0', '#,##0', '#,##0" €"', '#,##0" €"']
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
            d26["places"], d26["cls"], k[e]["odir"], k[e]["vac"]]
    marque_vue = mq
    for i, val in enumerate(vals):
        x = ws.cell(r, 2 + i, val); x.fill = fill(VUE); x.number_format = NB1[i]
        x.font = F(8, i == 0, INK if i else AZUR); x.alignment = ind(0) if i < 2 else R
        x.border = Border(bottom=sd("EAF0F6"))

for i in range(17):
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
        6:  "=IFERROR(Q{0}/N{0},0)".format(r1),                          # consommables/eleve
        7:  "=O{0}-N{0}".format(r1),                                     # places libres
        8:  "=I{0}*$F$4".format(r1),                                     # Delta budget
        9:  "=F{0}*((1+$F$4)^J{0}-1)*D{1}".format(r1, r2),               # inscrits gagnes
        10: "=I{0}*E{0}".format(r2),                                     # CA gagne
        11: "=IF(I{0}<=G{0},F{0},F{0}+R{1}/O{1})".format(r2, r1),        # cout marginal
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

ws.cell(RT2 + 2, 2, "Lecture des fonds :  bleu = restitué par la vue,  ocre = calculé par le masque.  "
                    "Un coût marginal en rouge signale un campus où la classe doit ouvrir.")
ws.cell(RT2 + 2, 2).font = F(7.5, False, DOUX, True); ws.cell(RT2 + 2, 2).alignment = ind(0)
# on fige les deux colonnes d'identite, pas les lignes : les deux tableaux ont chacun son en-tete
ws.freeze_panes = "D1"

# ============================================================================
#  ONGLET 2 — LE COUT VARIABLE
#
#  La question tombera : « un cout par eleve, c'est combien ? ». Il n'y a pas
#  de reponse en un nombre, et l'onglet le montre en trois temps :
#     deux poches, deux cles     -- pourquoi le cout ne peut pas etre unique
#     le cout MOYEN              -- ce qu'il vaut, par cycle et par modalite
#     le cout MARGINAL           -- ce que le masque soustrait vraiment
# ============================================================================
w2 = wb.create_sheet("Le coût variable")
NC2 = 9
w2.sheet_view.showGridLines = False
for r in range(1, 82):
    for c in range(1, NC2 + 1): w2.cell(r, c).fill = fill(FOND)
for r in (1, 2):
    for c in range(1, NC2 + 1): w2.cell(r, c).fill = fill(INK)
for c in range(1, NC2 + 1): w2.cell(3, c).fill = fill(AZUR)
w2.cell(1, 2, "EDUSERVICES · le moteur d'acquisition").font = F(7.5, False, PALE)
w2.cell(1, 2).alignment = ind(0)
w2.cell(2, 2, "LE COÛT VARIABLE  —  pourquoi il ne peut pas être un nombre").font = F(14, True, "FFFFFF")
w2.cell(2, 2).alignment = ind(0)
w2.column_dimensions["A"].width = 2.4; w2.column_dimensions["B"].width = 26
for c in range(3, NC2 + 1): w2.column_dimensions[GL(c)].width = 14
for r, h in ((1,14),(2,24),(3,3),(5,22),(6,16)): w2.row_dimensions[r].height = h

w2.cell(5, 2, "La comptabilité ne connaît pas le programme.").font = F(12, True, INK)
w2.cell(5, 2).alignment = ind(0)
w2.cell(6, 2, "AW_002_000004_000001 est au grain CAMPUS × COMPTE. Un coût par élève et par programme "
              "ne se lit donc pas : il s'alloue. V_ALLOCATION le fait déjà, avec deux clés différentes — "
              "et c'est de là que vient toute la suite.")
w2.cell(6, 2).font = F(8, False, DOUX, True); w2.cell(6, 2).alignment = ind(0)

def titre(w, r, txt, sous, coul=AZUR):
    w.cell(r, 2, txt).font = F(10, True, coul); w.cell(r, 2).alignment = ind(0)
    w.cell(r + 1, 2, sous).font = F(7.5, False, DOUX, True); w.cell(r + 1, 2).alignment = ind(0)
    w.row_dimensions[r].height = 20; w.row_dimensions[r + 1].height = 14

def entete(w, r, libelles, largeur=None):
    for i, h in enumerate(libelles):
        x = w.cell(r, 2 + i, h); x.font = F(8, True, INK)
        x.alignment = ind(0) if i == 0 else WRAP
        x.fill = fill(FOND); x.border = Border(bottom=sd(INK), top=sd(FILET))
    w.row_dimensions[r].height = largeur or 30

def ligne(w, r, vals, nb, fond=PANEL, gras=False, trait="EDEEF0"):
    for i, val in enumerate(vals):
        x = w.cell(r, 2 + i, val); x.fill = fill(fond); x.number_format = nb[i]
        x.font = F(8, gras or i == 0, INK); x.alignment = ind(0) if i == 0 else R
        x.border = Border(bottom=sd(trait))

# ---- A. DEUX POCHES, DEUX CLES --------------------------------------------
titre(w2, 8, "①  Deux poches, deux clés",
      "Le même euro de charge variable ne se répartit pas de la même façon selon ce qu'il paie.")
entete(w2, 11, ["Poche", "Comptes", "Clé d'allocation", "Varie avec", "Uniforme à l'intérieur d'un campus ?"])
w2.column_dimensions["F"].width = 22
POCHES = [("Vacataires", "621", "HEURES", "le programme et la modalité", "NON"),
          ("Consommables", "604 + 6063", "EFFECTIFS", "le campus seulement", "OUI")]
NBP = ['General', 'General', 'General', 'General', 'General']
for i, p in enumerate(POCHES):
    ligne(w2, 12 + i, list(p), NBP)
    w2.cell(12 + i, 6).font = F(8, True, ROUGE_T if p[4] == "NON" else VERT_T)
w2.cell(15, 2, "Les heures d'une classe dépendent du programme : un BTS en initial pèse 1 000 heures, "
               "un Mastère en alternance 420. La clé EFFECTIFS, elle, ne distingue rien à l'intérieur "
               "d'un campus — par construction.")
w2.cell(15, 2).font = F(7.5, False, DOUX, True); w2.cell(15, 2).alignment = ind(0)

# ---- B. LE COUT MOYEN, par cycle x modalite -------------------------------
titre(w2, 18, "②  Le coût variable MOYEN, au grain cycle × modalité",
      "Ce que coûte un élève déjà inscrit, tous frais variables confondus. Chaque ligne est une réalité "
      "du réseau ; la moyenne, elle, n'est nulle part.")
entete(w2, 21, ["Cycle · modalité", "Effectifs 2026", "Heures / élève", "Tarif horaire",
                "Vacataires / élève", "Consommables / élève", "Coût moyen / élève", "Écart à la moyenne"])
CYC = {"BAC": "Bachelor", "MAS": "Mastère", "BTS": "BTS"}
MOD = {"INIT": "initial", "ALT": "alternance"}
NB3 = ['General', '#,##0', '0.0" h"', '0.00" €"', '#,##0" €"', '#,##0" €"', '#,##0" €"', '+0.0%;-0.0%']
lignes_b = []
for key, p in sorted(prog.items(), key=lambda x: x[1]["hrs"] / x[1]["eff"]):
    ents = [a[4:] for a in p if a.startswith("ent_")]
    conso = sum(k[e]["odir"] for e in ents) / sum(v[(e, 2026)]["eff"] for e in ents)
    lignes_b.append((key, p, conso))
RB0, RBN = 22, 22 + len(lignes_b)
for j, (key, p, conso) in enumerate(lignes_b):
    r = RB0 + j
    ligne(w2, r, ["%s · %s" % (CYC[key[0]], MOD[key[1]]), p["eff"], p["hrs"] / p["eff"], TARIF,
                  "=D%d*E%d" % (r, r), conso, "=F%d+G%d" % (r, r),
                  "=IFERROR(H{0}/$H${1}-1,0)".format(r, RBN)], NB3)
    for c in (6, 8): w2.cell(r, c).font = F(8, True, INK)
ligne(w2, RBN, ["MOYENNE PONDÉRÉE",
                "=SUM(C{0}:C{1})".format(RB0, RBN - 1), "=IFERROR(SUMPRODUCT(C{0}:C{1},D{0}:D{1})/C{2},0)".format(RB0, RBN - 1, RBN),
                TARIF, "=D%d*E%d" % (RBN, RBN),
                "=IFERROR(SUMPRODUCT(C{0}:C{1},G{0}:G{1})/C{2},0)".format(RB0, RBN - 1, RBN),
                "=F%d+G%d" % (RBN, RBN), "—"], NB3, fond=GRIS, gras=True, trait=INK)
w2.cell(RBN, 9).alignment = R
w2.conditional_formatting.add("H{0}:H{1}".format(RB0, RBN - 1),
    ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                   mid_color=HM_MED, end_type="max", end_color=HM_BAS))
w2.cell(RBN + 2, 2, "Un facteur 1,40 entre les extrêmes. Le coût variable « moyen » du réseau ne décrit "
                    "aucun élève réel — il ne sert qu'à cadrer, jamais à décider.")
w2.cell(RBN + 2, 2).font = F(8, True, INK); w2.cell(RBN + 2, 2).alignment = ind(0)

# ---- C. LES CONSOMMABLES, uniformes dans un campus, pas entre campus ------
titre(w2, 30, "③  La poche uniforme : les consommables, campus par campus",
      "Clé EFFECTIFS. À l'intérieur d'un campus, tous les élèves portent le même montant — "
      "mais d'un campus à l'autre l'écart est de 24 %.")
entete(w2, 33, ["Campus", "Effectifs 2026", "Consommables 604+6063", "Consommables / élève",
                "Places libres"], 24)
NB4 = ['General', '#,##0', '#,##0" €"', '#,##0" €"', '#,##0']
RC0 = 34
for j, e in enumerate(ENTS):
    r = RC0 + j; d = v[(e, 2026)]; r1 = T1 + 1 + j
    ligne(w2, r, ["%s %s" % (MQ[e.split("_")[0]], LIBC[e]),
                  "='Le moteur'!N%d" % r1, "='Le moteur'!Q%d" % r1,
                  "=IFERROR(D%d/C%d,0)" % (r, r), "='Le moteur'!G%d" % (T2 + 1 + j)], NB4)
RCN = RC0 + len(ENTS)
ligne(w2, RCN, ["GROUPE", "=SUM(C{0}:C{1})".format(RC0, RCN - 1), "=SUM(D{0}:D{1})".format(RC0, RCN - 1),
                "=IFERROR(D{0}/C{0},0)".format(RCN), "=SUM(F{0}:F{1})".format(RC0, RCN - 1)],
      NB4, fond=GRIS, gras=True, trait=INK)
w2.conditional_formatting.add("E{0}:E{1}".format(RC0, RCN - 1),
    ColorScaleRule(start_type="min", start_color=HM_HAUT, mid_type="percentile", mid_value=50,
                   mid_color=HM_MED, end_type="max", end_color=HM_BAS))

# ---- D. LE COUT MARGINAL, celui que le masque soustrait vraiment ----------
RD = RCN + 3
titre(w2, RD, "④  Mais ce n'est pas ce coût-là que le masque soustrait", 
      "Le geste ajoute des élèves dans des classes qui existent déjà. Leur vacataire est déjà payé : "
      "il ne coûte pas un euro de plus. Le coût MARGINAL n'est donc pas le coût moyen.", "B26B00")
for c in range(2, NC2 + 1):
    w2.cell(RD + 3, c).fill = fill(PANEL); w2.cell(RD + 3, c).border = Border(top=sd(FILET))
    w2.cell(RD + 4, c).fill = fill(PANEL)
    w2.cell(RD + 5, c).fill = fill(PANEL); w2.cell(RD + 5, c).border = Border(bottom=sd(FILET))
w2.cell(RD + 3, 2, "TANT QU'IL RESTE UNE PLACE").font = F(8, True, VERT_T)
w2.cell(RD + 3, 2).alignment = ind(0)
w2.cell(RD + 3, 5, "les consommables seuls  —  300 ou 372 € selon le campus").font = F(8, False, INK)
w2.cell(RD + 3, 5).alignment = ind(0)
w2.cell(RD + 4, 2, "QUAND LA CLASSE EST PLEINE").font = F(8, True, ROUGE_T)
w2.cell(RD + 4, 2).alignment = ind(0)
w2.cell(RD + 4, 5, "+ la quote-part du vacataire d'une classe neuve  —  et là, le programme compte")
w2.cell(RD + 4, 5).font = F(8, False, INK); w2.cell(RD + 4, 5).alignment = ind(0)
w2.cell(RD + 5, 5, "Le masque bascule seul : IF(inscrits gagnés <= places libres ; conso ; conso + "
                   "vacataires du campus / places du campus).")
w2.cell(RD + 5, 5).font = F(7.5, False, DOUX, True); w2.cell(RD + 5, 5).alignment = ind(0)

RE = RD + 8
entete(w2, RE, ["Programme qui ouvre", "Heures / classe", "Tarif horaire", "Coût du vacataire",
                "Capacité de la classe", "Coût d'ouverture / place", "+ consommables ⇒ coût marginal"], 30)
NB5 = ['General', '#,##0" h"', '0.00" €"', '#,##0" €"', '#,##0', '#,##0" €"', 'General']
for j, (key, p, conso) in enumerate(sorted(lignes_b, key=lambda t: TX[t[0]] / CAPA[t[0][0]])):
    r = RE + 1 + j
    ligne(w2, r, ["%s · %s" % (CYC[key[0]], MOD[key[1]]), TX[key], TARIF,
                  "=C%d*D%d" % (r, r), CAPA[key[0]], "=E%d/F%d" % (r, r),
                  "de %d à %d € selon le campus" % (300 + TX[key] * TARIF / CAPA[key[0]],
                                                    372 + TX[key] * TARIF / CAPA[key[0]])], NB5)
    w2.cell(r, 7).font = F(8, True, INK); w2.cell(r, 8).font = F(8, False, DOUX, True)
    w2.cell(r, 8).alignment = ind(0)
REN = RE + 1 + len(lignes_b)

for c in range(2, NC2 + 1):
    w2.cell(REN + 2, c).fill = fill(PANEL); w2.cell(REN + 2, c).border = Border(top=sd(AZUR))
    w2.cell(REN + 3, c).fill = fill(PANEL); w2.cell(REN + 3, c).border = Border(bottom=sd(AZUR))
w2.cell(REN + 2, 2, "Et le compte 6231 n'est jamais là-dedans.").font = F(9, True, AZUR)
w2.cell(REN + 2, 2).alignment = ind(0)
w2.cell(REN + 3, 2, "6231 est le budget d'acquisition lui-même. Il est déjà soustrait comme Δ budget "
                    "dans le compte de résultat du geste : le remettre dans le coût variable le compterait "
                    "deux fois.")
w2.cell(REN + 3, 2).font = F(7.5, False, DOUX, True); w2.cell(REN + 3, 2).alignment = ind(0)
w2.row_dimensions[REN + 2].height = 18

wb.save(OUT)
print("écrit :", OUT, "· tableau ① lignes %d-%d · tableau ② lignes %d-%d" % (T1, RT1, T2, RT2))
