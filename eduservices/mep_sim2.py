# -*- coding: utf-8 -*-
"""Mise en page de l'onglet Simulation, alignee sur le cockpit.

La feuille portait DEJA la bande de sept tuiles -- bordures, polices, formats,
tout etait la -- mais VIDE : un grand rectangle blanc entre le titre et le
tableau. On la remplit avec ce qui compte pour un simulateur de fermeture.
Les libelles techniques de l'en-tete passent en francais, et les quatre
colonnes de decision cessent d'etre un bloc bleu rapporte.

Patch XML : cinq graphes, vingt customProperty.bin, six customXml et
xl/webextensions a preserver.
"""
import re, zipfile, shutil, os

SRC, DST = "SIM2_nav11_corrige.xlsx", "SIM2_MEP.xlsx"
SH = "xl/worksheets/sheet2.xml"

def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

#  --- les sept tuiles : colonne de tete, libelle, valeur, note --------------
TUILES = [
 ("C", "  CLASSES SIMULÉES",     'SUMPRODUCT(($C$13:$C$72<>"")*1)',                        "NB",
  "au budget 2027, maille campus x programme"),
 ("G", "  CLASSES FERMÉES",      'SUMPRODUCT(($R$13:$R$72="Fermer")*1)',                   "NB",
  "décidées ci-dessous"),
 ("I", "  EFFECTIF PERDU",       'SUMPRODUCT(($R$13:$R$72="Fermer")*1,$H$13:$H$72)',       "NB",
  "étudiants"),
 ("K", "  CONTRIBUTION PERDUE",  '-SUMPRODUCT(($R$13:$R$72="Fermer")*1,$L$13:$L$72)',      "EUS",
  "ce que la fermeture coûte vraiment"),
 ("M", "  STRUCTURE RÉALLOUÉE",  'SUMPRODUCT(($R$13:$R$72="Fermer")*1,$M$13:$M$72)',       "EU",
  "elle change de porteur"),
 ("O", "  BASCULES",             'SUMPRODUCT((LEFT($V$13:$V$72,7)="BASCULE")*1)',          "NB",
  "saines avant, en déficit après"),
 ("Q", "  IMPACT EBITDA",        'SUM($U$13:$U$72)',                                       "EUS",
  "effet sur le groupe"),
]

#  --- l'en-tete du tableau, en francais ------------------------------------
ENTETES = {"C": "Marque", "D": "Campus", "E": "Programme", "F": "Année",
           "G": "Modalité", "H": "Effectif", "I": "Sections", "J": "Chiffre d'affaires",
           "K": "Coût variable", "L": "Contribution", "M": "Structure allouée",
           "N": "Coût complet", "O": "Marge complète", "P": "Point mort",
           "Q": "Marge de sécurité", "R": "DÉCISION", "S": "Structure après",
           "T": "Marge après", "U": "Impact EBITDA", "V": "Lecture"}

zin = zipfile.ZipFile(SRC); tmp = DST + ".tmp"
zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
XF = None
for it in zin.infolist():
    data = zin.read(it.filename)
    if it.filename == "xl/styles.xml":
        s = data.decode("utf-8")
        n = int(re.search(r'<cellXfs count="(\d+)">', s).group(1))
        XF = dict(NB=n, EU=n + 1, EUS=n + 2, NOTE=n + 3, PCT=n + 4)
        tuile = ('<xf numFmtId="%s" fontId="21" fillId="23" borderId="13" xfId="56" '
                 'applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" '
                 'applyAlignment="1"><alignment horizontal="left" vertical="center" '
                 'indent="1"/></xf>')
        neuf = (tuile % "3") + (tuile % "170") + (tuile % "182") + (
                '<xf numFmtId="0" fontId="69" fillId="23" borderId="0" xfId="56" '
                'applyFont="1" applyFill="1" applyAlignment="1"><alignment '
                'horizontal="left" vertical="center" indent="1"/></xf>'
                '<xf numFmtId="164" fontId="3" fillId="0" borderId="2" xfId="38" '
                'applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1">'
                '<alignment horizontal="right" vertical="center"/></xf>')
        s = s.replace('<cellXfs count="%d">' % n, '<cellXfs count="%d">' % (n + 5))
        s = s.replace("</cellXfs>", neuf + "</cellXfs>")
        data = s.encode("utf-8")
        print("styles : cinq formats ajoutes", XF)
    zout.writestr(it, data)
zout.close(); zin.close()

zin = zipfile.ZipFile(tmp); tmp2 = DST + ".tmp2"
zout = zipfile.ZipFile(tmp2, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = zin.read(it.filename)
    if it.filename == SH:
        s = data.decode("utf-8")

        def num(col):
            n = 0
            for ch in col:
                n = n * 26 + ord(ch) - 64
            return n

        def pose(ref, xml):
            """Remplace la cellule si elle existe, l'insere a sa place sinon :
            l'ordre des cellules dans une ligne doit rester croissant."""
            global s
            col = re.match(r"([A-Z]+)(\d+)", ref).group(1)
            lig = re.match(r"([A-Z]+)(\d+)", ref).group(2)
            pat = re.compile(r'<c r="%s"(?:[^>]*?/>|[^>]*?>.*?</c>)' % ref, re.S)
            m = pat.search(s)
            if m:
                assert len(m.group(0)) < 400, ref
                s = s[:m.start()] + xml + s[m.end():]
                return
            mr = re.search(r'<row r="%s"[^>]*>(.*?)</row>' % lig, s, re.S)
            assert mr, "ligne %s absente" % lig
            corps, base = mr.group(1), mr.start(1)
            pos = mr.end(1)
            for mc in re.finditer(r'<c r="([A-Z]+)%s"' % lig, corps):
                if num(mc.group(1)) > num(col):
                    pos = base + mc.start()
                    break
            s = s[:pos] + xml + s[pos:]

        #  le titre revient au bord gauche, comme sur le cockpit
        pose("G2", '<c r="G2" s="144"/>')
        pose("C2", '<c r="C2" s="144" t="inlineStr"><is><t>SIMULATION — OUVRIR OU '
                   'FERMER UNE CLASSE</t></is></c>')
        pose("C3", '<c r="C3" s="145" t="inlineStr"><is><t>Budget 2027 · la décision '
                   'se prend en colonne DÉCISION, tout le tableau suit</t></is></c>')

        #  le bandeau ne couvrait que G a K : un rectangle clair pose au milieu
        #  de la page. Il court maintenant sur toute la largeur du tableau.
        for col in ("D", "E", "F", "H", "I", "J", "L", "M", "N", "O", "P", "Q", "R",
                    "S", "T", "U", "V"):
            pose(col + "2", '<c r="%s2" s="144"/>' % col)
            pose(col + "3", '<c r="%s3" s="145"/>' % col)

        #  la bande de tuiles, enfin remplie
        for col, lib, form, kind, note in TUILES:
            pose(col + "9",  '<c r="%s9" s="155" t="inlineStr"><is><t>%s</t></is></c>'
                             % (col, esc(lib)))
            pose(col + "10", '<c r="%s10" s="%d"><f>%s</f></c>'
                             % (col, XF[kind], esc(form)))
            pose(col + "11", '<c r="%s11" s="%d" t="inlineStr"><is><t>%s</t></is></c>'
                             % (col, XF["NOTE"], esc(note)))

        #  l'en-tete : du francais, et les quatre colonnes de decision rentrent
        #  dans le rang (style 177, celui de tout l'en-tete)
        for col, lib in ENTETES.items():
            pose(col + "12", '<c r="%s12" s="177" t="inlineStr"><is><t>%s</t></is></c>'
                             % (col, esc(lib)))

        #  la marge de securite est un POURCENTAGE : elle sortait a 0
        for r in range(13, 73):
            pose("Q%d" % r, re.sub(r' s="\d+"', ' s="%d"' % XF["PCT"],
                                   re.search(r'<c r="Q%d"(?:[^>]*?/>|[^>]*?>.*?</c>)' % r,
                                             s, re.S).group(0)))
        data = s.encode("utf-8")
    zout.writestr(it, data)
zout.close(); zin.close()
os.remove(tmp); shutil.move(tmp2, DST)
print("ecrit :", DST)
