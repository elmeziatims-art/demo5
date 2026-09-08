# -*- coding: utf-8 -*-
"""restyle_pilotage.py — differencie les trois roles de l'onglet Pilotage.

POURQUOI UN PATCH XML ET PAS OPENPYXL. Ce classeur porte un graphique
qu'openpyxl ne sait pas relire (Series seriesType) : un aller-retour le
supprimerait. On n'ouvre donc que styles.xml et sheet3.xml, on ajoute les
formats manquants et on rebranche l'attribut s= des cellules visees.

CE QUI CHANGE, ET RIEN D'AUTRE :
  lignes 18 et 38  en-tetes de colonnes  gris E7E6E6 -> encre 1F3B57, texte blanc
  ligne  55        ligne GROUPE          gris E7E6E6 -> bleu clair DDEBF7
Le sous-total (53) et le siege (54) gardent leur gris : c'est ce contraste qui
rend les trois roles lisibles.

Chaque cellule garde SON style d'origine, cloné : bordures, alignement et
format de nombre sont preserves cellule par cellule, seuls le fond et, pour les
en-tetes, la couleur de police changent.
"""
import re, shutil, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]
#  "encre" : bandeau bleu nuit, texte blanc.  "filet" : fond blanc, texte bleu
#  nuit en gras, le filet noir deja present sous la ligne fait la separation.
VARIANTE = sys.argv[3] if len(sys.argv) > 3 else "encre"
FEUILLE = "xl/worksheets/sheet3.xml"
ENCRE, BLEU, BLANC = "FF1F3B57", "FFDDEBF7", "FFFFFFFF"

def bloc(xml, conteneur):
    m = re.search(r"<%s\b[^>]*>.*?</%s>" % (conteneur, conteneur), xml, re.S)
    return m.group(0), m.start(), m.end()

def elements(b, enfant):
    return re.findall(r"<%s\b(?:[^>]*/>|[^>]*>.*?</%s>)" % (enfant, enfant), b, re.S)

def ajouter(xml, conteneur, enfant, neuf):
    """Ajoute l'element s'il n'existe pas deja. Renvoie (xml, index)."""
    b, d, f = bloc(xml, conteneur)
    liste = elements(b, enfant)
    if neuf in liste:
        return xml, liste.index(neuf)
    idx = len(liste)
    corps = b[: -len("</%s>" % conteneur)] + neuf + "</%s>" % conteneur
    corps = re.sub(r'count="\d+"', 'count="%d"' % (idx + 1), corps, count=1)
    return xml[:d] + corps + xml[f:], idx

def lire(xml, conteneur, enfant, idx):
    b, _, _ = bloc(xml, conteneur)
    return elements(b, enfant)[idx]

def police_entete(xml, font_id, couleur):
    """La police d'origine, en gras, dans la couleur voulue."""
    src = lire(xml, "fonts", "font", font_id)
    neuf = re.sub(r"<color\b[^>]*/>", "", src)
    neuf = re.sub(r"<b\s*/>", "", neuf)
    neuf = re.sub(r"^(<font[^>]*>)", r'\1<b/><color rgb="%s"/>' % couleur, neuf)
    return ajouter(xml, "fonts", "font", neuf)

def attribut(xf, nom, valeur):
    if re.search(r'\s%s="[^"]*"' % nom, xf):
        return re.sub(r'\s%s="[^"]*"' % nom, ' %s="%s"' % (nom, valeur), xf)
    return re.sub(r"^<xf", '<xf %s="%s"' % (nom, valeur), xf)

def xf_variante(xml, xf_id, fill_id, font_id=None):
    neuf = lire(xml, "cellXfs", "xf", xf_id)
    neuf = attribut(neuf, "fillId", fill_id)
    neuf = attribut(neuf, "applyFill", "1")
    if font_id is not None:
        neuf = attribut(neuf, "fontId", font_id)
        neuf = attribut(neuf, "applyFont", "1")
    return ajouter(xml, "cellXfs", "xf", neuf)

def font_de(xml, xf_id):
    m = re.search(r'fontId="(\d+)"', lire(xml, "cellXfs", "xf", xf_id))
    return int(m.group(1)) if m else 0

CELL = lambda ref: re.compile(r'<c r="%s"(\s[^>]*?)?(/>|>)' % ref)

def style_de(feuille, ref):
    m = CELL(ref).search(feuille)
    if not m:
        return None
    s = re.search(r'\ss="(\d+)"', m.group(1) or "")
    return int(s.group(1)) if s else 0

def poser_style(feuille, ref, sid):
    m = CELL(ref).search(feuille)
    a = m.group(1) or ""
    a = re.sub(r'\ss="\d+"', ' s="%d"' % sid, a) if re.search(r'\ss="\d+"', a) \
        else a + ' s="%d"' % sid
    return feuille[:m.start()] + '<c r="%s"%s%s' % (ref, a, m.group(2)) + feuille[m.end():]

COLS = [chr(ord("A") + i) for i in range(12)]                       # A a L
zin = zipfile.ZipFile(SRC)
styles = zin.read("xl/styles.xml").decode("utf8")
feuille = zin.read(FEUILLE).decode("utf8")

avant = len(elements(bloc(styles, "cellXfs")[0], "xf"))
FOND_ENTETE, TEXTE_ENTETE = (ENCRE, BLANC) if VARIANTE == "encre" else (BLANC, ENCRE)
styles, f_entete = ajouter(styles, "fills", "fill",
    '<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
    '<bgColor indexed="64"/></patternFill></fill>' % FOND_ENTETE)
styles, f_bleu = ajouter(styles, "fills", "fill",
    '<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
    '<bgColor indexed="64"/></patternFill></fill>' % BLEU)

faits, cache = {"entete": 0, "groupe": 0}, {}
for ref in ["%s%d" % (c, r) for r in (18, 38) for c in COLS]:
    sid = style_de(feuille, ref)
    if sid is None:
        continue
    if ("e", sid) not in cache:
        styles, fid = police_entete(styles, font_de(styles, sid), TEXTE_ENTETE)
        styles, cache[("e", sid)] = xf_variante(styles, sid, f_entete, fid)
    feuille = poser_style(feuille, ref, cache[("e", sid)])
    faits["entete"] += 1
for ref in ["%s55" % c for c in COLS]:
    sid = style_de(feuille, ref)
    if sid is None:
        continue
    if ("g", sid) not in cache:
        styles, cache[("g", sid)] = xf_variante(styles, sid, f_bleu)
    feuille = poser_style(feuille, ref, cache[("g", sid)])
    faits["groupe"] += 1

apres = len(elements(bloc(styles, "cellXfs")[0], "xf"))
declare = int(re.search(r'<cellXfs count="(\d+)"', styles).group(1))
assert apres == declare, "compteur cellXfs incoherent : %d vs %d" % (apres, declare)

zout = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    d = zin.read(it.filename)
    if it.filename == "xl/styles.xml":
        d = styles.encode("utf8")
    elif it.filename == FEUILLE:
        d = feuille.encode("utf8")
    zout.writestr(it, d)
zout.close()
print("variante :", VARIANTE, "| en-tetes repeints :", faits["entete"],
      "| ligne GROUPE :", faits["groupe"])
print("cellXfs : %d -> %d (declare %d)" % (avant, apres, declare))
