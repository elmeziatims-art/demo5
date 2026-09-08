# -*- coding: utf-8 -*-
"""refaire_bande_kpi.py — la bande de cinq KPI de l'onglet Pilotage.

CE QU'ELLE AVAIT DE FAUX, ET PAS SEULEMENT DANS LES MOTS :
  H10  l'effectif portait un format en euros : 3 254 EUR d'etudiants.
  B11  TEXT(...,"#,##0 EUR") s'evalue dans une locale a points : le masque
       affichait "contre 23.098.985 EUR en 2026". On supprime le TEXT et on
       laisse le FORMAT DE NOMBRE faire le travail -- il suit la locale du
       poste, il ne peut pas se tromper de separateur.
  J11  "vs 2026" en dur, qui n'apprend rien.
  J9   la croissance du CA repetait la sous-ligne du premier KPI. La cinquieme
       case devient l'ecart a l'objectif : c'est la question du cockpit.

PATCH XML CHIRURGICAL. Le classeur porte un graphique qu'openpyxl ne sait pas
relire : un aller-retour le supprimerait. On ne touche que styles.xml et
sheet3.xml.
"""
import re, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]
FEUILLE = "xl/worksheets/sheet3.xml"

#  cellule -> (libelle ou formule, format de nombre ou None)
LABELS = {
    "B9": "Chiffre d'affaires",
    "D9": "EBITDA après siège",
    "F9": "Marge EBITDA",
    "H9": "Effectif moyen",
    "J9": "Écart à l'objectif",
}
FORMULES = {
    "J10": "H55-Cadrage!$B$8",
    "B11": "Cadrage!$C$12",
    "D11": "Cadrage!$C$13",
    "F11": "Cadrage!$C$14",
    "H11": "Cadrage!$C$15",
    "J11": "Cadrage!$B$8",
}
FORMATS = {
    "H10": '#,##0;\\-#,##0;"–"',
    "J10": '+#,##0" €";\\-#,##0" €";"–"',
    "B11": '"2026 : "#,##0" €"',
    "D11": '"2026 : "#,##0" €"',
    "F11": '"2026 : "0.0%',
    "H11": '"2026 : "#,##0',
    "J11": '"objectif "#,##0" €"',
}

# ------------------------------------------------------------------ styles --
def bloc(xml, conteneur):
    m = re.search(r"<%s\b[^>]*>.*?</%s>" % (conteneur, conteneur), xml, re.S)
    return (m.group(0), m.start(), m.end()) if m else (None, -1, -1)

def elements(b, enfant):
    return re.findall(r"<%s\b(?:[^>]*/>|[^>]*>.*?</%s>)" % (enfant, enfant), b, re.S)

def ajouter(xml, conteneur, enfant, neuf):
    b, d, f = bloc(xml, conteneur)
    liste = elements(b, enfant)
    if neuf in liste:
        return xml, liste.index(neuf)
    idx = len(liste)
    corps = b[: -len("</%s>" % conteneur)] + neuf + "</%s>" % conteneur
    corps = re.sub(r'count="\d+"', 'count="%d"' % (idx + 1), corps, count=1)
    return xml[:d] + corps + xml[f:], idx

def numfmt_id(xml, code):
    """Renvoie (xml, id) pour un format personnalise, en le creant au besoin."""
    esc = code.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
    b, d, f = bloc(xml, "numFmts")
    if b is None:                                    # aucun format perso encore
        m = re.search(r"<fonts\b", xml)
        xml = xml[:m.start()] + '<numFmts count="0"></numFmts>' + xml[m.start():]
        b, d, f = bloc(xml, "numFmts")
    for e in elements(b, "numFmt"):
        if 'formatCode="%s"' % esc in e:
            return xml, int(re.search(r'numFmtId="(\d+)"', e).group(1))
    ids = [int(i) for i in re.findall(r'numFmtId="(\d+)"', b)]
    neuf_id = max(ids + [163]) + 1
    corps = b[: -len("</numFmts>")] + \
        '<numFmt numFmtId="%d" formatCode="%s"/>' % (neuf_id, esc) + "</numFmts>"
    corps = re.sub(r'count="\d+"', 'count="%d"' % (len(elements(b, "numFmt")) + 1),
                   corps, count=1)
    return xml[:d] + corps + xml[f:], neuf_id

def attribut(xf, nom, valeur):
    if re.search(r'\s%s="[^"]*"' % nom, xf):
        return re.sub(r'\s%s="[^"]*"' % nom, ' %s="%s"' % (nom, valeur), xf)
    return re.sub(r"^<xf", '<xf %s="%s"' % (nom, valeur), xf)

def xf_avec_format(xml, xf_id, fmt_id):
    b, _, _ = bloc(xml, "cellXfs")
    neuf = elements(b, "xf")[xf_id]
    neuf = attribut(neuf, "numFmtId", fmt_id)
    neuf = attribut(neuf, "applyNumberFormat", "1")
    return ajouter(xml, "cellXfs", "xf", neuf)

# ----------------------------------------------------------------- feuille --
CELL = re.compile
def trouver(feuille, ref):
    return re.search(r'<c r="%s"((?:\s+[a-zA-Z:]+="[^"]*")*)\s*(?:/>|>(.*?)</c>)' % ref,
                     feuille, re.S)

def style_de(feuille, ref):
    m = trouver(feuille, ref)
    s = re.search(r'\ss="(\d+)"', m.group(1) or "")
    return int(s.group(1)) if s else 0

def ecrire(feuille, ref, attrs, interieur):
    m = trouver(feuille, ref)
    neuf = '<c r="%s"%s>%s</c>' % (ref, attrs, interieur)
    return feuille[:m.start()] + neuf + feuille[m.end():]

def sans_type(attrs):
    return re.sub(r'\st="[^"]*"', "", attrs)

def echapper(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

zin = zipfile.ZipFile(SRC)
styles = zin.read("xl/styles.xml").decode("utf8")
feuille = zin.read(FEUILLE).decode("utf8")

#  1. les formats de nombre, avant tout : ils changent le s= des cellules
for ref, code in FORMATS.items():
    styles, fid = numfmt_id(styles, code)
    styles, nid = xf_avec_format(styles, style_de(feuille, ref), fid)
    m = trouver(feuille, ref)
    a = re.sub(r'\ss="\d+"', ' s="%d"' % nid, m.group(1)) if re.search(r'\ss="\d+"', m.group(1)) \
        else m.group(1) + ' s="%d"' % nid
    feuille = feuille[:m.start()] + \
        ('<c r="%s"%s>%s</c>' % (ref, a, m.group(2)) if m.group(2) is not None
         else '<c r="%s"%s/>' % (ref, a)) + feuille[m.end():]

#  2. les libelles, en chaines internes : pas de sharedStrings a recompter
for ref, texte in LABELS.items():
    m = trouver(feuille, ref)
    a = sans_type(m.group(1)) + ' t="inlineStr"'
    feuille = ecrire(feuille, ref, a, "<is><t>%s</t></is>" % echapper(texte))

#  3. les formules ; la valeur en cache est retiree, Excel recalcule a l'ouverture
for ref, f in FORMULES.items():
    m = trouver(feuille, ref)
    feuille = ecrire(feuille, ref, sans_type(m.group(1)), "<f>%s</f>" % echapper(f))

#  4. le cache de calcul devient faux : on le supprime et on force le recalcul
parties = [n for n in zin.namelist() if n != "xl/calcChain.xml"]
types = zin.read("[Content_Types].xml").decode("utf8")
types = types.replace('<Override PartName="/xl/calcChain.xml" ContentType="application/'
                      'vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>', "")
rels = zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
rels = re.sub(r'<Relationship[^>]*Target="calcChain\.xml"[^>]*/>', "", rels)
wbx = zin.read("xl/workbook.xml").decode("utf8")
if "<calcPr" in wbx:
    wbx = re.sub(r"<calcPr\b[^>]*/>", '<calcPr calcId="191029" fullCalcOnLoad="1"/>', wbx)
else:
    wbx = wbx.replace("</workbook>", '<calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')

zout = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for n in parties:
    d = zin.read(n)
    if n == "xl/styles.xml":            d = styles.encode("utf8")
    elif n == FEUILLE:                  d = feuille.encode("utf8")
    elif n == "[Content_Types].xml":    d = types.encode("utf8")
    elif n == "xl/_rels/workbook.xml.rels": d = rels.encode("utf8")
    elif n == "xl/workbook.xml":        d = wbx.encode("utf8")
    zout.writestr(n, d)
zout.close()
print("libelles :", len(LABELS), "| formules :", len(FORMULES),
      "| formats :", len(FORMATS), "| calcChain supprimee :",
      "xl/calcChain.xml" in zin.namelist())
