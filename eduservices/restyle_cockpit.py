# -*- coding: utf-8 -*-
"""restyle_cockpit.py — aligner COCKPIT sur la charte de CAD_PIL.

LE DIAGNOSTIC EST LE MEME QUE SUR CAD_PIL. Le fond de page est une nappe --
F3F6FA sur 1 012 cellules du Cockpit, 1 750 du premier drill, 579 du second --
et par-dessus, deux bleus sombres proches (172033 pour les bandeaux, 526071
pour les en-tetes de tableau) que rien ne distingue vraiment.

CE QUE FAIT LE SCRIPT :
  1  le fond passe au blanc sur les trois onglets ;
  2  les deux bleus sombres convergent vers l'encre 1F3B57 de CAD_PIL ;
  3  D9E2EF devient le bleu clair DDEBF7 des lignes de niveau ;
  4  le Cockpit recoit le bandeau encre qu'il n'avait pas -- les deux drills en
     ont un, lui pas : c'etait le seul onglet dont le titre flottait sur la
     nappe. Le logo est deja ancre en C2:D3, comme sur les drills ou il repose
     deja sur du sombre ;
  5  la bande d'en-tete du tableau detaille s'arretait en R alors que les
     en-tetes vont jusqu'a AB : elle est prolongee ;
  6  le tableau hierarchique est colore par NIVEAU, lu dans la colonne B --
     groupe en bleu clair, marques en gris, campus en blanc. Vingt lignes
     plates deviennent une arborescence ;
  7  les trois cellules de POV passent en jaune de saisie.

Les points 1 a 3 se font en repeignant les DEFINITIONS de remplissage, pas les
cellules : quatre lignes de XML pour 3 300 cases.

PATCH CHIRURGICAL. Le classeur porte cinq graphiques et trois images ;
openpyxl n'en relit pas la totalite, un aller-retour les perdrait.
"""
import re, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]
FEUILLES = {1: "xl/worksheets/sheet1.xml",      # Cockpit
            2: "xl/worksheets/sheet2.xml",      # Drill EBITDA 1
            3: "xl/worksheets/sheet3.xml"}      # Drill EBITDA 2

#  ancien -> nouveau, applique sur la DEFINITION du remplissage
REMAP = {"FFF3F6FA": "FFFFFFFF",       # la nappe de fond
         "FF172033": "FF1F3B57",       # bandeaux de titre
         "FF526071": "FF1F3B57",       # en-tetes de tableau
         "FFD9E2EF": "FFDDEBF7"}       # lignes de niveau du pont
ENCRE, BLANC, JAUNE = "FF1F3B57", "FFFFFFFF", "FFFFF2CC"
BLEU, GRIS_LIGNE = "FFDDEBF7", "FFF2F2F2"

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

def attribut(xf, nom, valeur):
    if re.search(r'\s%s="[^"]*"' % nom, xf):
        return re.sub(r'\s%s="[^"]*"' % nom, ' %s="%s"' % (nom, valeur), xf)
    return re.sub(r"^<xf", '<xf %s="%s"' % (nom, valeur), xf)

def police_coloree(styles, font_id, couleur, gras=True):
    src = lire(styles, "fonts", "font", font_id)
    neuf = re.sub(r"<color\b[^>]*/>", "", src)
    if gras:
        neuf = re.sub(r"<b\s*/>", "", neuf)
        neuf = re.sub(r"^(<font[^>]*>)", r'\1<b/><color rgb="%s"/>' % couleur, neuf)
    else:
        neuf = re.sub(r"^(<font[^>]*>)", r'\1<color rgb="%s"/>' % couleur, neuf)
    return ajouter(styles, "fonts", "font", neuf)

def xf_variante(styles, xf_id, fill_id=None, font_id=None):
    neuf = lire(styles, "cellXfs", "xf", xf_id)
    if fill_id is not None:
        neuf = attribut(attribut(neuf, "fillId", fill_id), "applyFill", "1")
    if font_id is not None:
        neuf = attribut(attribut(neuf, "fontId", font_id), "applyFont", "1")
    return ajouter(styles, "cellXfs", "xf", neuf)

def fill_de_xf(styles, xf_id):
    m = re.search(r'fillId="(\d+)"', lire(styles, "cellXfs", "xf", xf_id))
    return int(m.group(1)) if m else 0

def font_de_xf(styles, xf_id):
    m = re.search(r'fontId="(\d+)"', lire(styles, "cellXfs", "xf", xf_id))
    return int(m.group(1)) if m else 0

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
    if not m:
        return feuille, False
    a = m.group(1) or ""
    a = re.sub(r'\ss="\d+"', ' s="%d"' % sid, a) if re.search(r'\ss="\d+"', a) \
        else a + ' s="%d"' % sid
    corps = ('<c r="%s"%s>%s</c>' % (ref, a, m.group(2))) if m.group(2) is not None \
        else ('<c r="%s"%s/>' % (ref, a))
    return feuille[:m.start()] + corps + feuille[m.end():], True

def num_col(ref):
    lettres = re.match(r"([A-Z]+)", ref).group(1)
    n = 0
    for ch in lettres:
        n = n * 26 + ord(ch) - 64
    return n

def assurer_cellules(feuille, refs):
    """Cree les <c> absentes du XML : une case vide n'existe pas, donc ne peut
    pas etre stylee. On les insere dans l'ordre des colonnes, en creant la
    <row> si elle manque -- Excel exige les deux ordres."""
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
                    suivant = autre.start()
                    break
            debut = fin = suivant if suivant is not None else feuille.index("</sheetData>")
        presentes = {re.search(r'r="([A-Z]+\d+)"', c).group(1) for c in cellules}
        for ref in voulues:
            if ref not in presentes:
                cellules.append('<c r="%s"/>' % ref)
        cellules.sort(key=lambda c: num_col(re.search(r'r="([A-Z]+\d+)"', c).group(1)))
        attrs = re.sub(r'\sspans="[^"]*"', "", attrs)
        feuille = feuille[:debut] + "<row%s>%s</row>" % (attrs, "".join(cellules)) + feuille[fin:]
    return feuille

def col(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

zin = zipfile.ZipFile(SRC)
styles = zin.read("xl/styles.xml").decode("utf8")
feuilles = {k: zin.read(v).decode("utf8") for k, v in FEUILLES.items()}
journal = {}

# ---- on releve AVANT de repeindre : les en-tetes doivent passer en blanc ----
fills = [couleur_du_fill(e) for e in elements(bloc(styles, "fills")[0], "fill")]
entetes = {}
for k, f in feuilles.items():
    entetes[k] = [m.group(1) for m in re.finditer(r'<c r="([A-Z]+\d+)"', f)
                  if (lambda s: s is not None and fills[fill_de_xf(styles, s)] == "FF526071")
                     (style_de(f, m.group(1)))]

# ---- 1 a 3 : les definitions de remplissage --------------------------------
b, d, f = bloc(styles, "fills")
liste = elements(b, "fill")
n = 0
for i, e in enumerate(liste):
    c = couleur_du_fill(e)
    if c in REMAP:
        b = b.replace(liste[i], remplissage(REMAP[c]), 1)
        n += 1
styles = styles[:d] + b + styles[f:]
journal["remplissages repeints"] = n

# ---- les en-tetes de tableau en blanc gras ---------------------------------
cache, n = {}, 0
for k, refs in entetes.items():
    for ref in refs:
        sid = style_de(feuilles[k], ref)
        if sid not in cache:
            styles, pid = police_coloree(styles, font_de_xf(styles, sid), BLANC)
            styles, cache[sid] = xf_variante(styles, sid, font_id=pid)
        feuilles[k], ok = poser_style(feuilles[k], ref, cache[sid])
        n += ok
journal["en-tetes en blanc"] = n

# ---- 4 et 5 : le bandeau du Cockpit, et l'en-tete prolonge -----------------
def peindre(k, refs, fond, police=None, gras=True):
    global styles
    cache, n = {}, 0
    styles, fid = ajouter(styles, "fills", "fill", remplissage(fond))
    for ref in refs:
        sid = style_de(feuilles[k], ref)
        if sid is None:
            continue
        cle = (sid, fond, police)
        if cle not in cache:
            pid = None
            if police:
                styles, pid = police_coloree(styles, font_de_xf(styles, sid), police, gras)
            styles, cache[cle] = xf_variante(styles, sid, fill_id=fid, font_id=pid)
        feuilles[k], ok = poser_style(feuilles[k], ref, cache[cle])
        n += ok
    return n

BANDEAU = ["%s%d" % (col(c), r) for r in (1, 2, 3, 4) for c in range(1, 40)]
feuilles[1] = assurer_cellules(feuilles[1], BANDEAU)
journal["bandeau Cockpit"] = peindre(1, BANDEAU, ENCRE)
journal["titre en blanc"] = peindre(1, ["G2", "G3"], ENCRE, BLANC)
ENTETE37 = ["%s37" % col(c) for c in range(2, 29)]
feuilles[1] = assurer_cellules(feuilles[1], ENTETE37)
journal["en-tete prolonge"] = peindre(1, ENTETE37, ENCRE, BLANC)
journal["cellules de POV"] = peindre(1, ["F5", "K5", "N5"], JAUNE)

# ---- 6 : le tableau hierarchique, colore par niveau ------------------------
def valeur(feuille, ref):
    m = trouver(feuille, ref)
    if not m or m.group(2) is None:
        return None
    v = re.search(r"<v>([^<]*)</v>", m.group(2))
    return v.group(1) if v else None

par_niveau = {2: [], 3: []}
for r in range(38, 58):
    niv = valeur(feuilles[1], "B%d" % r)
    if niv in ("2", "3"):
        par_niveau[int(niv)] += ["%s%d" % (col(c), r) for c in range(2, 29)]
feuilles[1] = assurer_cellules(feuilles[1], par_niveau[2] + par_niveau[3])
journal["lignes groupe"] = peindre(1, par_niveau[2], BLEU)
journal["lignes marque"] = peindre(1, par_niveau[3], GRIS_LIGNE)

# ---- 7 : deux defauts d'affichage du tableau detaille ----------------------
#  AA porte "% nouveaux inscrits" avec un format entier : la colonne affiche 0
#  sur les vingt lignes. AB n'a pas d'en-tete et vaut (SPEND_ACQ - CA_N1)/CA_N1,
#  ce qui ne veut rien dire -- elle affiche -1 partout. On la masque plutot que
#  de la vider : rien n'est detruit, et aucun graphe ne la lit (verifie).
def numfmt_id(styles, code):
    esc = code.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
    b_, d_, f_ = bloc(styles, "numFmts")
    if b_ is None:
        m = re.search(r"<fonts\b", styles)
        styles = styles[:m.start()] + '<numFmts count="0"></numFmts>' + styles[m.start():]
        b_, d_, f_ = bloc(styles, "numFmts")
    for e in elements(b_, "numFmt"):
        if 'formatCode="%s"' % esc in e:
            return styles, int(re.search(r'numFmtId="(\d+)"', e).group(1))
    neuf = max([int(i) for i in re.findall(r'numFmtId="(\d+)"', b_)] + [163]) + 1
    corps = b_[: -len("</numFmts>")] + \
        '<numFmt numFmtId="%d" formatCode="%s"/>' % (neuf, esc) + "</numFmts>"
    corps = re.sub(r'count="\d+"', 'count="%d"' % (len(elements(b_, "numFmt")) + 1),
                   corps, count=1)
    return styles[:d_] + corps + styles[f_:], neuf

styles, fmt_pct = numfmt_id(styles, "0.0%")
cache, n = {}, 0
for r in range(38, 58):
    ref = "AA%d" % r
    sid = style_de(feuilles[1], ref)
    if sid is None:
        continue
    if sid not in cache:
        neuf = lire(styles, "cellXfs", "xf", sid)
        neuf = attribut(attribut(neuf, "numFmtId", fmt_pct), "applyNumberFormat", "1")
        styles, cache[sid] = ajouter(styles, "cellXfs", "xf", neuf)
    feuilles[1], ok = poser_style(feuilles[1], ref, cache[sid])
    n += ok
journal["colonne AA en pourcent"] = n

def masquer_colonne(feuille, num):
    """Marque hidden la definition de colonne qui couvre num, en la scindant
    si elle couvre une plage."""
    b_, d_, f_ = bloc(feuille, "cols")
    if b_ is None:
        return feuille, 0
    sortie, fait = [], 0
    for e in elements(b_, "col"):
        mn = int(re.search(r'min="(\d+)"', e).group(1))
        mx = int(re.search(r'max="(\d+)"', e).group(1))
        if not (mn <= num <= mx) or "hidden=" in e:
            sortie.append(e)
            continue
        gabarit = re.sub(r'\smin="\d+"', "", re.sub(r'\smax="\d+"', "", e))
        def morceau(a, b, cache=False):
            x = gabarit.replace("<col", '<col min="%d" max="%d"' % (a, b), 1)
            return x.replace("<col", "<col hidden=\"1\"", 1) if cache else x
        if mn < num:
            sortie.append(morceau(mn, num - 1))
        sortie.append(morceau(num, num, True))
        if mx > num:
            sortie.append(morceau(num + 1, mx))
        fait = 1
    return feuille[:d_] + "<cols>" + "".join(sortie) + "</cols>" + feuille[f_:], fait

feuilles[1], fait = masquer_colonne(feuilles[1], 28)     # colonne AB
journal["colonne AB masquee"] = fait

# ---- controles et ecriture -------------------------------------------------
for conteneur, enfant in (("cellXfs", "xf"), ("fills", "fill"), ("fonts", "font")):
    declare = int(re.search(r'<%s count="(\d+)"' % conteneur, styles).group(1))
    reel = len(elements(bloc(styles, conteneur)[0], enfant))
    assert declare == reel, "%s : %d declares, %d reels" % (conteneur, declare, reel)

wbx = zin.read("xl/workbook.xml").decode("utf8")
wbx = re.sub(r"<calcPr\b[^>]*/>", '<calcPr calcId="191029" fullCalcOnLoad="1"/>', wbx) \
    if "<calcPr" in wbx else \
    wbx.replace("</workbook>", '<calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')

inverse = {v: k for k, v in FEUILLES.items()}
zout = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for n in zin.namelist():
    if n == "xl/calcChain.xml":
        continue
    d = zin.read(n)
    if n == "xl/styles.xml":       d = styles.encode("utf8")
    elif n in inverse:             d = feuilles[inverse[n]].encode("utf8")
    elif n == "xl/workbook.xml":   d = wbx.encode("utf8")
    zout.writestr(n, d)
zout.close()
for k, v in journal.items():
    print("  %-24s %d" % (k, v))
