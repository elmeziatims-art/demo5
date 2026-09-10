# -*- coding: utf-8 -*-
"""La formule etait bien arrivee, le parametre non.

En transplantant les colonnes S a V, la cellule I74 -- la part du siege -- est
restee vide. Excel lit une cellule vide comme 0 : la part siege valait 0 %, la
part campus 100 %, et le masque retrouvait exactement son comportement d'avant.

Deux corrections : le parametre est repose, ET la formule ne depend plus de lui
pour fonctionner -- si la cellule est vide, elle retombe sur 22 %.
"""
import re, zipfile, shutil, os

SRC, DST = "src.xlsx", "SIM2_nav11_corrige.xlsx"
S_SIM = "xl/worksheets/sheet2.xml"
SIG = 'IF($I$74="",0.22,$I$74)'

def esc(f):
    return f.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

zin = zipfile.ZipFile(SRC); tmp = DST + ".tmp"
zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
XF = None
for it in zin.infolist():
    data = zin.read(it.filename)

    if it.filename == "xl/styles.xml":
        s = data.decode("utf-8")
        n = int(re.search(r'<cellXfs count="(\d+)">', s).group(1))
        XF = (n, n + 1, n + 2)
        neuf = ('<xf numFmtId="0" fontId="72" fillId="0" borderId="0" xfId="0" '
                'applyFont="1" applyAlignment="1"><alignment horizontal="left" '
                'vertical="center"/></xf>'
                '<xf numFmtId="164" fontId="72" fillId="2" borderId="0" xfId="0" '
                'applyNumberFormat="1" applyFont="1" applyFill="1" applyAlignment="1">'
                '<alignment horizontal="center" vertical="center"/></xf>'
                '<xf numFmtId="187" fontId="72" fillId="0" borderId="0" xfId="0" '
                'applyNumberFormat="1" applyFont="1" applyAlignment="1">'
                '<alignment horizontal="right" vertical="center"/></xf>')
        s = s.replace('<cellXfs count="%d">' % n, '<cellXfs count="%d">' % (n + 3))
        s = s.replace("</cellXfs>", neuf + "</cellXfs>")
        data = s.encode("utf-8")
        print("styles : formats %d, %d, %d ajoutes" % XF)
    zout.writestr(it, data)
zout.close(); zin.close()

LAB, IN, CTRL = XF
zin = zipfile.ZipFile(tmp); tmp2 = DST + ".tmp2"
zout = zipfile.ZipFile(tmp2, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = zin.read(it.filename)

    if it.filename == S_SIM:
        s = data.decode("utf-8")
        #  1. la formule ne tombe plus si le parametre manque
        m = re.search(r'(<c r="S13"[^>]*><f t="shared" ref="[^"]+" si="\d+">)(.*?)(</f>)', s, re.S)
        assert m, "S13 introuvable"
        f = m.group(2)
        assert f.count("$I$74") == 2, f.count("$I$74")
        s = s[:m.start(2)] + f.replace("$I$74", esc(SIG)) + s[m.end(2):]

        #  2. le parametre et le controle, reposes
        rempl = {
            "C74": '<c r="C74" s="%d" t="inlineStr"><is><t>Part du siège dans la '
                   'structure allouée</t></is></c>' % LAB,
            "I74": '<c r="I74" s="%d"><v>0.22</v></c>' % IN,
            "J74": '<c r="J74" s="%d" t="inlineStr"><is><t>&lt;- elle se réalloue sur '
                   'TOUT le groupe. Le reste, murs et permanents, ne sort pas du '
                   'campus.</t></is></c>' % LAB,
            "C75": '<c r="C75" s="%d" t="inlineStr"><is><t>Contrôle d\'enveloppe — '
                   'doit rester à 0 €</t></is></c>' % LAB,
        }
        for ref, neuf in rempl.items():
            pat = re.compile(r'<c r="%s"(?:[^>]*?/>|[^>]*?>.*?</c>)' % ref, re.S)
            mm = pat.search(s)
            assert mm and len(mm.group(0)) < 300, ref
            s = s[:mm.start()] + neuf + s[mm.end():]
        #  S75 n'existe pas : on l'insere apres R75
        ctl = ('<c r="S75" s="%d"><f>SUMPRODUCT(($R$13:$R$72&lt;&gt;"Fermer")*1,'
               '$S$13:$S$72)-SUM($M$13:$M$72)</f></c>' % CTRL)
        mm = re.search(r'<c r="R75"(?:[^>]*?/>|[^>]*?>.*?</c>)', s, re.S)
        assert mm, "R75 introuvable"
        s = s[:mm.end()] + ctl + s[mm.end():]
        data = s.encode("utf-8")

    elif it.filename == "xl/workbook.xml":
        s = data.decode("utf-8")
        s = re.sub(r'<calcPr[^/]*/>', '<calcPr calcId="0" fullCalcOnLoad="1"/>', s)
        data = s.encode("utf-8")

    zout.writestr(it, data)
zout.close(); zin.close()
os.remove(tmp); shutil.move(tmp2, DST)
print("ecrit :", DST)
