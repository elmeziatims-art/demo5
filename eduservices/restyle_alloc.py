# -*- coding: utf-8 -*-
"""restyle_alloc.py — ALLOCATION mis a la charte du masque Cadrage.

LA CHARTE EST CELLE DU FICHIER, PAS UNE AUTRE : encre 262626, azur 007AC3,
gris d'en-tete E7E6E6, ciel E8F1F9, jaune de saisie FFF2CC, filets noirs fins.
Pas de bleu nuit : celui-la etait pour Pilotage.

CE QUE LE SCRIPT POSE :
  un filet azur sous le bandeau, comme sur Cadrage ;
  les titres de bloc en gras sur filet noir ;
  les quatre cles d'allocation et la version en jaune de saisie ;
  l'en-tete du grand tableau en gris, sauf les deux colonnes de rentabilite
    qui passent en azur : c'est le sujet de l'onglet ;
  la hierarchie coloree par niveau -- marque en ciel, campus en gris tres
    clair, classe en blanc -- pour qu'un tableau de 78 lignes se lise ;
  la ligne GROUPE en gris avec le double trait comptable.

PATCH CHIRURGICAL : le classeur porte deux images ancrees et une feuille
_TGK_HIDDEN ; un aller-retour openpyxl les mettrait en danger. On ne touche
qu'a styles.xml et a la feuille.
"""
import re, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]
FEUILLE = "xl/worksheets/sheet2.xml"          # Allocation
ENCRE, AZUR, GRIS = "FF262626", "FF007AC3", "FFE7E6E6"
CIEL, JAUNE, CAMPUS = "FFE8F1F9", "FFFFF2CC", "FFF7F7F9"
BLANC, FILET = "FFFFFFFF", "FFD5D7DA"
UI = "Arial"

def bloc(xml, c):
    m = re.search(r"<%s\b[^>]*>.*?</%s>" % (c, c), xml, re.S)
    return (m.group(0), m.start(), m.end()) if m else (None, -1, -1)

def elements(b, e):
    return re.findall(r"<%s\b(?:[^>]*/>|[^>]*>.*?</%s>)" % (e, e), b, re.S)

def ajouter(xml, cont, enf, neuf):
    b, d, f = bloc(xml, cont)
    liste = elements(b, enf)
    if neuf in liste:
        return xml, liste.index(neuf)
    idx = len(liste)
    corps = b[: -len("</%s>" % cont)] + neuf + "</%s>" % cont
    corps = re.sub(r'count="\d+"', 'count="%d"' % (idx + 1), corps, count=1)
    return xml[:d] + corps + xml[f:], idx

def lire(xml, cont, enf, i):
    return elements(bloc(xml, cont)[0], enf)[i]

def remplissage(c):
    return ('<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
            '<bgColor indexed="64"/></patternFill></fill>' % c)

def attribut(xf, nom, val):
    if re.search(r'\s%s="[^"]*"' % nom, xf):
        return re.sub(r'\s%s="[^"]*"' % nom, ' %s="%s"' % (nom, val), xf)
    return re.sub(r"^<xf", '<xf %s="%s"' % (nom, val), xf)

def police(styles, font_id, couleur=None, gras=None, taille=None):
    """Reconstruit la police au lieu de la rapiecer.

    Deux raisons. D'abord certaines portent <b val="0"/> et non <b/> : un
    simple ajout de <b/> se faisait annuler par le val="0" qui suivait.
    Ensuite l'ordre des enfants d'un <font> est une sequence dans le schema ;
    autant la reecrire dans le bon ordre que d'esperer qu'Excel pardonne.
    """
    src = lire(styles, "fonts", "font", font_id)
    def vrai(balise):
        m = re.search(r"<%s\b([^>]*)/>" % balise, src)
        if not m:
            return False
        v = re.search(r'val="([^"]*)"', m.group(1))
        return True if not v else v.group(1) not in ("0", "false")
    def attr(balise, nom="val"):
        m = re.search(r'<%s\b[^>]*%s="([^"]*)"' % (balise, nom), src)
        return m.group(1) if m else None
    b_    = vrai("b") if gras is None else bool(gras)
    i_    = vrai("i")
    u_    = re.search(r"<u\b", src) is not None
    sz    = taille if taille is not None else (attr("sz") or "11")
    if couleur is not None:
        coul = '<color rgb="%s"/>' % couleur
    else:
        m = re.search(r"<color\b[^>]*/>", src)
        coul = m.group(0) if m else ""
    fam   = attr("family")
    n = "<font>"
    if b_: n += "<b/>"
    if i_: n += "<i/>"
    if u_: n += "<u/>"
    n += '<sz val="%s"/>' % sz + coul + '<name val="%s"/>' % UI
    if fam: n += '<family val="%s"/>' % fam
    n += "</font>"
    return ajouter(styles, "fonts", "font", n)

def bordure(styles, border_id, bas=None, haut=None):
    src = lire(styles, "borders", "border", border_id)
    n = re.sub(r"<bottom\b(?:[^>]*/>|[^>]*>.*?</bottom>)", "", src, flags=re.S)
    n = re.sub(r"<top\b(?:[^>]*/>|[^>]*>.*?</top>)", "", n, flags=re.S)
    morceaux = ""
    if haut: morceaux += '<top style="%s"><color rgb="%s"/></top>' % haut
    if bas:  morceaux += '<bottom style="%s"><color rgb="%s"/></bottom>' % bas
    n = re.sub(r"^(<border[^>]*>)", lambda m: m.group(1) + morceaux, n)
    return ajouter(styles, "borders", "border", n)

def num_col(ref):
    n = 0
    for ch in re.match(r"([A-Z]+)", ref).group(1):
        n = n * 26 + ord(ch) - 64
    return n

def col(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def trouver(feuille, ref):
    return re.search(r'<c r="%s"((?:\s+[a-zA-Z:]+="[^"]*")*)\s*(?:/>|>(.*?)</c>)' % ref,
                     feuille, re.S)

def style_de(feuille, ref):
    m = trouver(feuille, ref)
    if not m:
        return None
    s = re.search(r'\ss="(\d+)"', m.group(1) or "")
    return int(s.group(1)) if s else 0

def poser(feuille, ref, sid):
    m = trouver(feuille, ref)
    a = m.group(1) or ""
    a = re.sub(r'\ss="\d+"', ' s="%d"' % sid, a) if re.search(r'\ss="\d+"', a) \
        else a + ' s="%d"' % sid
    corps = ('<c r="%s"%s>%s</c>' % (ref, a, m.group(2))) if m.group(2) is not None \
        else ('<c r="%s"%s/>' % (ref, a))
    return feuille[:m.start()] + corps + feuille[m.end():]

def assurer(feuille, refs):
    """Cree les <c> absentes : une case vide n'existe pas, donc ne se style pas."""
    par_ligne = {}
    for ref in refs:
        par_ligne.setdefault(int(re.search(r"\d+", ref).group(0)), []).append(ref)
    for ligne, voulues in sorted(par_ligne.items()):
        m = re.search(r'<row r="%d"(?![0-9])[^>]*>.*?</row>|<row r="%d"(?![0-9])[^>]*/>'
                      % (ligne, ligne), feuille, re.S)
        if m:
            contenu = m.group(0)
            attrs = re.match(r"<row([^>]*?)/?>", contenu).group(1)
            cellules = re.findall(r'<c r="[A-Z]+\d+"(?:[^>]*/>|[^>]*>.*?</c>)', contenu, re.S)
            debut, fin = m.start(), m.end()
        else:
            attrs, cellules = ' r="%d"' % ligne, []
            suivant = None
            for autre in re.finditer(r'<row r="(\d+)"', feuille):
                if int(autre.group(1)) > ligne:
                    suivant = autre.start(); break
            debut = fin = suivant if suivant is not None else feuille.index("</sheetData>")
        presentes = {re.search(r'r="([A-Z]+\d+)"', c).group(1) for c in cellules}
        for ref in voulues:
            if ref not in presentes:
                cellules.append('<c r="%s"/>' % ref)
        cellules.sort(key=lambda c: num_col(re.search(r'r="([A-Z]+\d+)"', c).group(1)))
        attrs = re.sub(r'\sspans="[^"]*"', "", attrs)
        feuille = feuille[:debut] + "<row%s>%s</row>" % (attrs, "".join(cellules)) + feuille[fin:]
    return feuille

zin = zipfile.ZipFile(SRC)
styles = zin.read("xl/styles.xml").decode("utf8")
feuille = zin.read(FEUILLE).decode("utf8")
journal = {}

def peindre(refs, fond=None, couleur=None, gras=None, taille=None, bas=None, haut=None):
    global styles, feuille
    feuille = assurer(feuille, refs)
    cache, n = {}, 0
    fid = None
    if fond:
        styles, fid = ajouter(styles, "fills", "fill", remplissage(fond))
    for ref in refs:
        sid = style_de(feuille, ref)
        if sid is None:
            continue
        cle = (sid, fond, couleur, gras, taille, bas, haut)
        if cle not in cache:
            xf = lire(styles, "cellXfs", "xf", sid)
            if fid is not None:
                xf = attribut(attribut(xf, "fillId", fid), "applyFill", "1")
            if couleur is not None or gras is not None or taille is not None:
                m = re.search(r'fontId="(\d+)"', xf)
                styles, pid = police(styles, int(m.group(1)) if m else 0, couleur, gras, taille)
                xf = attribut(attribut(xf, "fontId", pid), "applyFont", "1")
            if bas or haut:
                m = re.search(r'borderId="(\d+)"', xf)
                styles, bid = bordure(styles, int(m.group(1)) if m else 0, bas, haut)
                xf = attribut(attribut(xf, "borderId", bid), "applyBorder", "1")
            styles, cache[cle] = ajouter(styles, "cellXfs", "xf", xf)
        feuille = poser(feuille, ref, cache[cle])
        n += 1
    return n

BAND = lambda r, c1=2, c2=13: ["%s%d" % (col(c), r) for c in range(c1, c2 + 1)]

# 1. le filet azur sous le bandeau, comme sur Cadrage
journal["filet azur"] = peindre(["%s3" % col(c) for c in range(1, 14)], fond=AZUR)
# 2. le titre : Calibri 16 -> Arial 14 gras encre
journal["titre"] = peindre(["D2"], couleur=ENCRE, gras=True, taille="14")
# 3. les titres de bloc, sur filet noir
for r in (5, 12, 14):
    journal["bloc %d" % r] = peindre(BAND(r), couleur=ENCRE, gras=True, taille="10.5",
                                     bas=("thin", ENCRE))
# 4. les saisies
journal["saisies"] = peindre(["C6", "C7", "C8", "C9", "C12"], fond=JAUNE,
                             couleur=ENCRE, gras=True,
                             bas=("thin", ENCRE), haut=("thin", ENCRE))
# 5. l'en-tete du tableau ; la rentabilite en azur, c'est le sujet de l'onglet
journal["entete"] = peindre(BAND(17, 2, 11), fond=GRIS, couleur=ENCRE, gras=True,
                            taille="8.5", haut=("thin", ENCRE), bas=("thin", ENCRE))
journal["entete azur"] = peindre(BAND(17, 12, 13), fond=AZUR, couleur=BLANC, gras=True,
                                 taille="8.5", haut=("thin", ENCRE), bas=("thin", ENCRE))

# 6. la hierarchie, lue dans l'indentation de la colonne B
def texte(ref):
    m = trouver(feuille, ref)
    if not m or m.group(2) is None:
        return None
    t = re.search(r"<is><t[^>]*>(.*?)</t></is>", m.group(2), re.S)
    if t:
        return t.group(1)
    v = re.search(r"<v>([^<]*)</v>", m.group(2))
    return v.group(1) if v else None

sst = None
if "xl/sharedStrings.xml" in zin.namelist():
    x = zin.read("xl/sharedStrings.xml").decode("utf8")
    sst = ["".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))
           for si in re.findall(r"<si>.*?</si>", x, re.S)]

def libelle(r):
    m = trouver(feuille, "B%d" % r)
    if not m or m.group(2) is None:
        return None
    if 't="s"' in (m.group(1) or ""):
        v = re.search(r"<v>(\d+)</v>", m.group(2))
        return sst[int(v.group(1))] if v and sst else None
    return texte("B%d" % r)

niveaux = {1: [], 2: [], 3: [], 0: []}
for r in range(18, 96):
    lib = libelle(r)
    if not lib:
        continue
    lib = lib.replace("&#160;", " ")
    if lib.strip() == "GROUPE":       niveaux[0] += BAND(r)
    elif lib.startswith("      "):    niveaux[3] += BAND(r)
    elif lib.startswith("   "):       niveaux[2] += BAND(r)
    else:                             niveaux[1] += BAND(r)
journal["marques"] = peindre(niveaux[1], fond=CIEL, gras=True, bas=("thin", FILET))
journal["campus"]  = peindre(niveaux[2], fond=CAMPUS, gras=True, bas=("thin", FILET))
journal["classes"] = peindre(niveaux[3], fond=BLANC, bas=("thin", FILET))
journal["GROUPE"]  = peindre(niveaux[0], fond=GRIS, couleur=ENCRE, gras=True,
                             haut=("thin", ENCRE), bas=("double", ENCRE))

# 7. la colonne M, seule sans largeur, un peu trop juste pour un pourcentage
b, d, f = bloc(feuille, "cols")
if '<col min="13"' not in b:
    b = b.replace("</cols>", '<col min="13" max="13" width="11" customWidth="1"/></cols>')
    feuille = feuille[:d] + b + feuille[f:]
    journal["largeur colonne M"] = 1

for cont, enf in (("cellXfs", "xf"), ("fills", "fill"), ("fonts", "font"), ("borders", "border")):
    decl = int(re.search(r'<%s count="(\d+)"' % cont, styles).group(1))
    reel = len(elements(bloc(styles, cont)[0], enf))
    assert decl == reel, "%s : %d declares, %d reels" % (cont, decl, reel)

zout = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for n in zin.namelist():
    d = zin.read(n)
    if n == "xl/styles.xml":  d = styles.encode("utf8")
    elif n == FEUILLE:        d = feuille.encode("utf8")
    zout.writestr(n, d)
zout.close()
for k, v in journal.items():
    print("  %-20s %d" % (k, v))
