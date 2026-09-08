# -*- coding: utf-8 -*-
"""restyle_cadpil.py — sortir CAD_PIL de la nappe grise.

LE DIAGNOSTIC. Le fond de page etait F5F6F7 : 910 cellules sur Cadrage, 311 sur
Pilotage. Par-dessus, les en-tetes et les totaux etaient en E7E6E6. Deux gris a
quatre pour cent d'ecart : rien ne peut ressortir, tout se lit gris.

CE QUE FAIT LE SCRIPT :
  1  le fond de page passe au blanc, sur les deux onglets, d'un seul geste --
     on repeint la DEFINITION du remplissage dans styles.xml, pas les cellules ;
  2  les en-tetes de colonnes passent en bleu nuit, texte blanc ;
  3  la bande de KPI de Pilotage quitte le gris pour le ciel E8F1F9, deja dans
     la palette : elle se lit comme un resume, pas comme un en-tete ;
  4  la ligne GROUPE passe en bleu clair ;
  5  le sous-total garde son gris -- devenu le SEUL gris de la page, il redevient
     un signal ;
  6  la bande de KPI est refaite : libelles, formats, et deux defauts reels
     (l'effectif en euros, les separateurs a points venus de TEXT()).

PATCH XML CHIRURGICAL. Le classeur porte un graphique qu'openpyxl ne sait pas
relire : un aller-retour le supprimerait.
"""
import re, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]
VARIANTE = sys.argv[3] if len(sys.argv) > 3 else "encre"
CADRAGE, PILOTAGE = "xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml"

FOND_PAGE = "FFF5F6F7"          # la nappe grise a supprimer
GRIS      = "FFE7E6E6"          # en-tetes ET totaux, indistinctement
ENCRE, BLANC, CIEL, BLEU = "FF1F3B57", "FFFFFFFF", "FFE8F1F9", "FFDDEBF7"

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

def lire(xml, conteneur, enfant, idx):
    return elements(bloc(xml, conteneur)[0], enfant)[idx]

def remplissage(couleur):
    return ('<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
            '<bgColor indexed="64"/></patternFill></fill>' % couleur)

def couleur_du_fill(e):
    m = re.search(r'<fgColor rgb="([0-9A-Fa-f]{8})"', e)
    return m.group(1).upper() if m else None

def table_fills(styles):
    return [couleur_du_fill(e) for e in elements(bloc(styles, "fills")[0], "fill")]

def fill_de_xf(styles, xf_id):
    m = re.search(r'fillId="(\d+)"', lire(styles, "cellXfs", "xf", xf_id))
    return int(m.group(1)) if m else 0

def font_de_xf(styles, xf_id):
    m = re.search(r'fontId="(\d+)"', lire(styles, "cellXfs", "xf", xf_id))
    return int(m.group(1)) if m else 0

def attribut(xf, nom, valeur):
    if re.search(r'\s%s="[^"]*"' % nom, xf):
        return re.sub(r'\s%s="[^"]*"' % nom, ' %s="%s"' % (nom, valeur), xf)
    return re.sub(r"^<xf", '<xf %s="%s"' % (nom, valeur), xf)

def police_coloree(styles, font_id, couleur):
    src = lire(styles, "fonts", "font", font_id)
    neuf = re.sub(r"<color\b[^>]*/>", "", src)
    neuf = re.sub(r"<b\s*/>", "", neuf)
    neuf = re.sub(r"^(<font[^>]*>)", r'\1<b/><color rgb="%s"/>' % couleur, neuf)
    return ajouter(styles, "fonts", "font", neuf)

def xf_variante(styles, xf_id, fill_id=None, font_id=None, fmt_id=None):
    neuf = lire(styles, "cellXfs", "xf", xf_id)
    if fill_id is not None:
        neuf = attribut(attribut(neuf, "fillId", fill_id), "applyFill", "1")
    if font_id is not None:
        neuf = attribut(attribut(neuf, "fontId", font_id), "applyFont", "1")
    if fmt_id is not None:
        neuf = attribut(attribut(neuf, "numFmtId", fmt_id), "applyNumberFormat", "1")
    return ajouter(styles, "cellXfs", "xf", neuf)

def numfmt_id(styles, code):
    esc = code.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
    b, d, f = bloc(styles, "numFmts")
    if b is None:
        m = re.search(r"<fonts\b", styles)
        styles = styles[:m.start()] + '<numFmts count="0"></numFmts>' + styles[m.start():]
        b, d, f = bloc(styles, "numFmts")
    for e in elements(b, "numFmt"):
        if 'formatCode="%s"' % esc in e:
            return styles, int(re.search(r'numFmtId="(\d+)"', e).group(1))
    neuf_id = max([int(i) for i in re.findall(r'numFmtId="(\d+)"', b)] + [163]) + 1
    corps = b[: -len("</numFmts>")] + \
        '<numFmt numFmtId="%d" formatCode="%s"/>' % (neuf_id, esc) + "</numFmts>"
    corps = re.sub(r'count="\d+"', 'count="%d"' % (len(elements(b, "numFmt")) + 1),
                   corps, count=1)
    return styles[:d] + corps + styles[f:], neuf_id

# ----------------------------------------------------------------- feuille --
def trouver(feuille, ref):
    return re.search(r'<c r="%s"((?:\s+[a-zA-Z:]+="[^"]*")*)\s*(?:/>|>(.*?)</c>)' % ref,
                     feuille, re.S)

def style_de(feuille, ref):
    m = trouver(feuille, ref)
    if not m:
        return None
    s = re.search(r'\ss="(\d+)"', m.group(1) or "")
    return int(s.group(1)) if s else 0

def poser_style(feuille, ref, sid):
    m = trouver(feuille, ref)
    a = m.group(1) or ""
    a = re.sub(r'\ss="\d+"', ' s="%d"' % sid, a) if re.search(r'\ss="\d+"', a) \
        else a + ' s="%d"' % sid
    corps = ('<c r="%s"%s>%s</c>' % (ref, a, m.group(2))) if m.group(2) is not None \
        else ('<c r="%s"%s/>' % (ref, a))
    return feuille[:m.start()] + corps + feuille[m.end():]

def cellules(feuille, lignes=None):
    for m in re.finditer(r'<c r="([A-Z]+)(\d+)"', feuille):
        if lignes is None or int(m.group(2)) in lignes:
            yield m.group(1) + m.group(2), int(m.group(2))

zin = zipfile.ZipFile(SRC)
styles = zin.read("xl/styles.xml").decode("utf8")
feuilles = {n: zin.read(n).decode("utf8") for n in (CADRAGE, PILOTAGE)}
journal = {}

# ---- 1. la nappe grise devient blanche, partout, en une seule reecriture ----
b, d, f = bloc(styles, "fills")
liste = elements(b, "fill")
vises = [i for i, e in enumerate(liste) if couleur_du_fill(e) == FOND_PAGE]
for i in vises:
    b = b.replace(liste[i], remplissage(BLANC), 1)
styles = styles[:d] + b + styles[f:]
journal["remplissages de fond repeints"] = len(vises)

# ---- 2 a 5. les cellules encore grises, par role -----------------------------
def repeindre(nom_feuille, lignes, fond, couleur_police=None):
    """Repeint les cellules grises des lignes visees, style par style."""
    global styles
    feuille = feuilles[nom_feuille]
    fills = table_fills(styles)
    cache, n = {}, 0
    styles, fid = ajouter(styles, "fills", "fill", remplissage(fond))
    for ref, ligne in list(cellules(feuille, lignes)):
        sid = style_de(feuille, ref)
        if sid is None or fills[fill_de_xf(styles, sid)] != GRIS.lstrip("F")[:0] + GRIS:
            continue
        if sid not in cache:
            pid = None
            if couleur_police:
                styles, pid = police_coloree(styles, font_de_xf(styles, sid),
                                             couleur_police)
            styles, cache[sid] = xf_variante(styles, sid, fill_id=fid, font_id=pid)
        feuille = poser_style(feuille, ref, cache[sid])
        n += 1
    feuilles[nom_feuille] = feuille
    return n

FOND_ENTETE, TEXTE_ENTETE = (ENCRE, BLANC) if VARIANTE == "encre" else (BLANC, ENCRE)
journal["en-tetes Pilotage"] = repeindre(PILOTAGE, {18, 38}, FOND_ENTETE, TEXTE_ENTETE)
journal["en-tetes Cadrage"] = repeindre(CADRAGE, {11, 19}, FOND_ENTETE, TEXTE_ENTETE)
journal["bande KPI Pilotage"] = repeindre(PILOTAGE, {8, 9}, CIEL)
journal["ligne GROUPE"] = repeindre(PILOTAGE, {55}, BLEU)
#  les trois bandeaux de cartes de Cadrage : D7 etait deja azur, B7 et F7 gris.
journal["cartes Cadrage"] = repeindre(CADRAGE, {7}, "FF007AC3", BLANC)

#  ---- 7. les colonnes de Pilotage ------------------------------------------
#  B a K etaient toutes a 19,6 : dix colonnes identiques, une table qui s'etale
#  sur 1 400 px et ou aucun groupe ne se lit. M faisait 255,6 -- une colonne
#  vide de 1 800 px collee au tableau. On demasque L au passage : elle porte le
#  CAC marginal du second tableau, qui etait invisible.
#  Les formes ancrees de Pilotage ne couvrent que B:C sur la ligne de titre :
#  retailler ces colonnes ne deforme pas le classeur.
COLS = ('<cols>'
        '<col min="1" max="1" style="146" width="3.42" customWidth="1"/>'
        '<col min="2" max="2" width="17" customWidth="1"/>'
        '<col min="3" max="3" width="14" customWidth="1"/>'
        '<col min="4" max="4" width="13" customWidth="1"/>'
        '<col min="5" max="5" width="13.5" customWidth="1"/>'
        '<col min="6" max="6" width="12.5" customWidth="1"/>'
        '<col min="7" max="9" width="11.5" customWidth="1"/>'
        '<col min="10" max="10" width="12" customWidth="1"/>'
        '<col min="11" max="11" width="14" customWidth="1"/>'
        '<col min="12" max="12" width="13" customWidth="1"/>'
        '<col min="13" max="13" width="2.5" customWidth="1"/>'
        '<col min="14" max="16" width="13" hidden="1" customWidth="1"/>'
        '<col min="21" max="23" width="13" hidden="1" customWidth="1"/>'
        '</cols>')
import re as _re
feuilles[PILOTAGE], n = _re.subn(r"<cols>.*?</cols>", COLS, feuilles[PILOTAGE], flags=_re.S)
assert n == 1, "bloc <cols> de Pilotage introuvable"
journal["colonnes Pilotage retaillees"] = 12
#  le sous-total (53) n'est pas touche : il devient le seul gris de la page.

# ---- 6. la bande de KPI : libelles, formules, formats ------------------------
LABELS = {"B9": "Chiffre d'affaires", "D9": "EBITDA après siège",
          "F9": "Marge EBITDA", "H9": "Effectif moyen", "J9": "Écart à l'objectif"}
FORMULES = {"J10": "H55-Cadrage!$B$8", "B11": "Cadrage!$C$12", "D11": "Cadrage!$C$13",
            "F11": "Cadrage!$C$14", "H11": "Cadrage!$C$15", "J11": "Cadrage!$B$8"}
FORMATS = {"H10": '#,##0;\\-#,##0;"–"', "J10": '+#,##0" €";\\-#,##0" €";"–"',
           "B11": '"2026 : "#,##0" €"', "D11": '"2026 : "#,##0" €"',
           "F11": '"2026 : "0.0%', "H11": '"2026 : "#,##0',
           "J11": '"objectif "#,##0" €"'}
feuille = feuilles[PILOTAGE]
for ref, code in FORMATS.items():
    styles, fmt = numfmt_id(styles, code)
    styles, nid = xf_variante(styles, style_de(feuille, ref), fmt_id=fmt)
    feuille = poser_style(feuille, ref, nid)
ech = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
for ref, texte in LABELS.items():
    m = trouver(feuille, ref)
    a = re.sub(r'\st="[^"]*"', "", m.group(1)) + ' t="inlineStr"'
    feuille = feuille[:m.start()] + \
        '<c r="%s"%s><is><t>%s</t></is></c>' % (ref, a, ech(texte)) + feuille[m.end():]
for ref, fx in FORMULES.items():
    m = trouver(feuille, ref)
    a = re.sub(r'\st="[^"]*"', "", m.group(1))
    feuille = feuille[:m.start()] + \
        '<c r="%s"%s><f>%s</f></c>' % (ref, a, ech(fx)) + feuille[m.end():]
feuilles[PILOTAGE] = feuille

# ---- controle et ecriture ---------------------------------------------------
declare = int(re.search(r'<cellXfs count="(\d+)"', styles).group(1))
reel = len(elements(bloc(styles, "cellXfs")[0], "xf"))
assert declare == reel, "cellXfs : %d declares, %d reels" % (declare, reel)
declare = int(re.search(r'<fills count="(\d+)"', styles).group(1))
reel = len(elements(bloc(styles, "fills")[0], "fill"))
assert declare == reel, "fills : %d declares, %d reels" % (declare, reel)

wbx = zin.read("xl/workbook.xml").decode("utf8")
wbx = re.sub(r"<calcPr\b[^>]*/>", '<calcPr calcId="191029" fullCalcOnLoad="1"/>', wbx) \
    if "<calcPr" in wbx else \
    wbx.replace("</workbook>", '<calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')

zout = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for n in zin.namelist():
    if n == "xl/calcChain.xml":
        continue
    d = zin.read(n)
    if n == "xl/styles.xml":       d = styles.encode("utf8")
    elif n in feuilles:            d = feuilles[n].encode("utf8")
    elif n == "xl/workbook.xml":   d = wbx.encode("utf8")
    zout.writestr(n, d)
zout.close()
print("variante :", VARIANTE)
for k, v in journal.items():
    print("  %-28s %d" % (k, v))
