#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_cadpil.py — applique les dix-sept corrections DANS le fichier d'origine.

POURQUOI DE LA CHIRURGIE XML ET PAS OPENPYXL. Ce classeur ne contient pas que
des cellules : neuf customXml, deux webextensions (le volet Tagetik), quatre
images et trois miniatures, un lien externe, quarante plages nommees. Le faire
relire et reecrire par openpyxl en perdrait la moitie -- on rendrait un fichier
qui ne parle plus a Tagetik. On ouvre donc le .xlsx comme l'archive zip qu'il
est, on remplace les nœuds <c> des seules cellules concernees, et TOUT LE RESTE
est recopie octet pour octet.

DEUX PRECAUTIONS QUI EVITENT LE MESSAGE « CONTENU ILLISIBLE » :

  - on retire la valeur en cache <v> de chaque cellule qu'on modifie, et on
    pose fullCalcOnLoad sur le classeur : Excel recalcule tout a l'ouverture ;
  - on supprime xl/calcChain.xml, devenu faux, ainsi que sa declaration dans
    [Content_Types].xml et sa relation. Excel le reconstruit seul. Un calcChain
    perime est la premiere cause de fichier repare.
"""
import zipfile, re, shutil, sys

SRC = "/tmp/claude-0/-home-user-demo5/b8c71a6a-b866-551a-b98b-eceadba2b120/scratchpad/CAD_PIL_nav211.xlsx"
OUT = "CAD_PIL_nav211_CORRIGE.xlsx"
CAD, PIL, MOT = "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml", "xl/worksheets/sheet8.xml"
esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

#  ---- l'ordre affiche et la permutation, relus dans le fichier -------------
import openpyxl, warnings
warnings.filterwarnings("ignore")
sv = openpyxl.load_workbook(SRC, data_only=True)["Pilotage"]
LIB = [sv.cell(r, 1).value for r in range(19, 33)]
CLE = {sv.cell(r, 12).value: r for r in range(19, 33)}
assert set(LIB) == set(CLE), "colonne L incoherente"

FORMULES = {}
VALEURS = {}
VIDES = {}
TEXTES = {}

#  ① le coefficient de prix : la table est en K24:K28, pas K12:K16
for r in range(2, 191):
    FORMULES[(MOT, "AC%d" % r)] = (
        'IF($A{0}="","",IF($F{0}="MBWAY",Cadrage!$K$24,IF($F{0}="ISCOM",Cadrage!$K$25,'
        'IF($F{0}="IPAC",Cadrage!$K$26,IF($F{0}="PIGIER",Cadrage!$K$27,Cadrage!$K$28)))))'
    ).format(r)

#  ② le bloc de pilotage : D, K et L deviennent des formules, E..I sont remis
#     en face du bon campus
for j, lib in enumerate(LIB):
    r, s = 19 + j, CLE[lib]
    FORMULES[(PIL, "D%d" % r)] = "SUMIFS(Campagne!$N$2:$N$15,Campagne!$C$2:$C$15,$A%d)" % r
    FORMULES[(PIL, "K%d" % r)] = "SUMIFS(Campagne!$G$2:$G$15,Campagne!$C$2:$C$15,$A%d)" % r
    FORMULES[(PIL, "L%d" % r)] = "$A%d" % r
    for col in "EFGHI":
        VALEURS[(PIL, "%s%d" % (col, r))] = sv["%s%d" % (col, s)].value

#  ③ les cinq leviers de couts, decales d'une ligne
for r in range(34, 39):
    FORMULES[(CAD, "F%d" % r)] = "INDEX(C{0}:E{0},MATCH(Cadrage!$C$5,$C$22:$E$22,0))".format(r)
VIDES[(CAD, "F22")] = True
VIDES[(CAD, "J22")] = True

#  ④ les quatre libelles et ratios faux
FORMULES[(CAD, "D14")] = "IFERROR(D13/D12,0)"
FORMULES[(CAD, "D9")] = '"scénario « "&$C$5&" »   ·   marge "&TEXT(D14,"0.0%")'
FORMULES[(CAD, "B9")] = ('"+"&TEXT($F$5,"0.00%")&" sur "&TEXT(C13,"#,##0 €")&" en 2026, soit "'
                         '&TEXT($B$8-C13,"+#,##0 €")&" à trouver"')
FORMULES[(PIL, "J10")] = "IFERROR(E55/Cadrage!$C$12-1,0)"
TEXTES[(CAD, "B18")] = "②   LES DOUZE LEVIERS"

# ============================================================================
#  LE REMPLACEMENT D'UN NŒUD <c>
#
#  Une cellule Excel s'ecrit soit <c r="X" s="12"/> (vide), soit
#  <c r="X" s="12"><v>3</v></c>, soit <c r="X" s="12"><f>…</f><v>3</v></c>.
#  On garde l'attribut de STYLE -- c'est toute la mise en forme -- et on
#  remplace le contenu. La valeur en cache disparait : Excel la recalculera.
# ============================================================================
CELL = lambda ref: re.compile(r'<c r="%s"((?:\s+[a-zA-Z:]+="[^"]*")*)\s*(?:/>|>(.*?)</c>)' % ref, re.S)

def attrs_sans_type(a):
    """On retire t="s" ou t="str" : la cellule change de nature."""
    return re.sub(r'\s+t="[^"]*"', "", a)

def remplace(xml, ref, inner, garder_type=False):
    m = CELL(ref).search(xml)
    if not m:
        return xml, False
    a = m.group(1) if garder_type else attrs_sans_type(m.group(1))
    neuf = '<c r="%s"%s>%s</c>' % (ref, a, inner) if inner else '<c r="%s"%s/>' % (ref, a)
    return xml[:m.start()] + neuf + xml[m.end():], True

parts = {}
with zipfile.ZipFile(SRC) as z:
    noms = z.namelist()
    for n in noms: parts[n] = z.read(n)

compte = {"formule": 0, "valeur": 0, "vide": 0, "texte": 0, "manquant": []}
for feuille in (CAD, PIL, MOT):
    x = parts[feuille].decode("utf-8")
    for (f_, ref), fo in FORMULES.items():
        if f_ != feuille: continue
        x, ok = remplace(x, ref, "<f>%s</f>" % esc(fo))
        compte["formule" if ok else "manquant"] = (compte["formule"] + 1) if ok else compte["manquant"]
        if not ok: compte["manquant"].append((feuille, ref))
    for (f_, ref), v in VALEURS.items():
        if f_ != feuille: continue
        x, ok = remplace(x, ref, "<v>%r</v>" % float(v))
        if ok: compte["valeur"] += 1
        else: compte["manquant"].append((feuille, ref))
    for (f_, ref) in VIDES:
        if f_ != feuille: continue
        x, ok = remplace(x, ref, "")
        if ok: compte["vide"] += 1
    for (f_, ref), t in TEXTES.items():
        if f_ != feuille: continue
        x, ok = remplace(x, ref, "<is><t>%s</t></is>" % esc(t))
        if ok:
            x = re.sub(r'(<c r="%s")((?:\s+[a-zA-Z:]+="[^"]*")*)' % ref,
                       lambda m: m.group(1) + m.group(2) + ' t="inlineStr"', x, count=1)
            compte["texte"] += 1
    parts[feuille] = x.encode("utf-8")

#  ---- Excel doit tout recalculer a l'ouverture -----------------------------
wbx = parts["xl/workbook.xml"].decode("utf-8")
wbx = re.sub(r'<calcPr[^/]*/>', '<calcPr calcId="191029" fullCalcOnLoad="1"/>', wbx)
parts["xl/workbook.xml"] = wbx.encode("utf-8")

#  ---- le calcChain devenu faux : on le retire proprement -------------------
if "xl/calcChain.xml" in parts:
    del parts["xl/calcChain.xml"]
    ct = parts["[Content_Types].xml"].decode("utf-8")
    ct = ct.replace('<Override PartName="/xl/calcChain.xml" ContentType="application/vnd.'
                    'openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>', "")
    parts["[Content_Types].xml"] = ct.encode("utf-8")
    rl = parts["xl/_rels/workbook.xml.rels"].decode("utf-8")
    rl = re.sub(r'<Relationship[^>]*Target="calcChain\.xml"[^>]*/>', "", rl)
    parts["xl/_rels/workbook.xml.rels"] = rl.encode("utf-8")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for n in noms:
        if n in parts: z.writestr(n, parts[n])
print("écrit :", OUT)
print("  %d formules, %d valeurs, %d cellules vidées, %d libellés"
      % (compte["formule"], compte["valeur"], compte["vide"], compte["texte"]))
if compte["manquant"]: print("  INTROUVABLES :", compte["manquant"][:10])
print("  parties conservées : %d sur %d" % (len(parts), len(noms)))
