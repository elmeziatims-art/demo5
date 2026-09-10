# -*- coding: utf-8 -*-
"""Colonnes S a V : la fermeture porte maintenant sur DEUX perimetres.

Jusqu'ici la structure de la classe fermee etait redistribuee dans le SEUL
campus (criteres marque + ville), et ponderee par les SECTIONS. Deux defauts :

  - le perimetre : les frais de siege -- publicite de marque et holding -- ne
    sont pas des murs, ils se repartissent sur tout le groupe. Fermer une
    classe a Bordeaux allege aussi Lyon et Paris. Rien ne bougeait ailleurs.
  - la cle : la structure allouee n'est PAS proportionnelle aux sections
    (33 lignes sur 60 s'en ecartent), parce que V_ALLOCATION repartit les
    permanents aux HEURES et le reste aux sections. Repartir au prorata de la
    structure elle-meme est sept fois plus juste.

Le patch est chirurgical : ce classeur porte cinq graphes, vingt
customProperty.bin, six customXml et xl/webextensions.
"""
import re, zipfile, shutil
S_SIM = "xl/worksheets/sheet2.xml"
SRC, DST = "src.xlsx", "SIM2_corrige.xlsx"

def esc(f):
    return f.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

CAMP = '($C$13:$C$72=$C13)*($D$13:$D$72=$D13)'
SURV = '($R$13:$R$72<>"Fermer")'
S_NEW = (
 'IF(OR($C13="",COUNT($H13:$Q13)=0),"",IF($R13="Fermer","",$M13*('
 #  la part campus : murs et permanents, elle ne sort pas du campus
 '(1-$I$74)*IF(SUMPRODUCT({c}*{s},$M$13:$M$72)=0,0,'
 'SUMPRODUCT({c}*1,$M$13:$M$72)/SUMPRODUCT({c}*{s},$M$13:$M$72))'
 #  la part siege : marque et holding, elle se repartit sur tout le groupe
 '+$I$74*IF(SUMPRODUCT({s}*1,$M$13:$M$72)=0,0,'
 'SUM($M$13:$M$72)/SUMPRODUCT({s}*1,$M$13:$M$72))'
 ')))').format(c=CAMP, s=SURV)
assert S_NEW.count("(") == S_NEW.count(")"), "parentheses desequilibrees"

V_NEW = ('IF(OR($C13="",COUNT($H13:$Q13)=0),"",IF($R13="Fermer",'
         '"Fermer = perdre "&TEXT($L13,"#,##0")&" € de contribution. Le fixe, lui, reste.",'
         'IF(AND($O13>=0,$T13<0),'
         '"BASCULE : saine avant, en déficit après les fermetures décidées.",'
         'IF(AND($O13<0,$L13>0),'
         '"Déficit au coût complet mais contribution positive : ne pas fermer, '
         'c\'est un artefact d\'allocation.",'
         'IF($O13<0,"Contribution négative : vrai point dur.",'
         '"Rentable. Point mort "&TEXT($P13,"#,##0")&" étudiants, marge de sécurité "'
         '&TEXT($Q13,"0%")&".")))))')
assert V_NEW.count("(") == V_NEW.count(")")

CTRL = ('SUMPRODUCT({s}*1,$S$13:$S$72)-SUM($M$13:$M$72)').format(s=SURV)

zin = zipfile.ZipFile(SRC); tmp = DST + ".tmp"
zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = zin.read(it.filename)

    if it.filename == "xl/styles.xml":
        s = data.decode("utf-8")
        n = int(re.search(r'<cellXfs count="(\d+)">', s).group(1))
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
        globals()["XF"] = (n, n + 1, n + 2)
        data = s.encode("utf-8")
        print("styles : trois formats ajoutes (%d, %d, %d)" % (n, n + 1, n + 2))

    zout.writestr(it, data)
zout.close(); zin.close()

#  seconde passe : la feuille, une fois les styles connus
XF_LAB, XF_IN, XF_CTRL = XF
zin = zipfile.ZipFile(tmp); tmp2 = DST + ".tmp2"
zout = zipfile.ZipFile(tmp2, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = zin.read(it.filename)
    if it.filename == S_SIM:
        s = data.decode("utf-8")
        for ref, txt in (("S13", S_NEW), ("V13", V_NEW)):
            m = re.search(r'(<c r="%s"[^>]*><f t="shared" ref="[^"]+" si="\d+">)(.*?)(</f>)'
                          % ref, s, re.S)
            assert m, ref
            s = s[:m.start(2)] + esc(txt) + s[m.end(2):]
            #  la valeur en cache de la ligne maitre est perimee
            s = re.sub(r'(<c r="%s"[^>]*>(?:<f[^>]*>.*?</f>))<v>.*?</v>' % ref,
                       r"\1", s, count=1, flags=re.S)
        #  le parametre et le controle, sous le tableau
        L = ('<row r="74" spans="2:22">'
             '<c r="C74" s="%d" t="inlineStr"><is><t>Part du siège dans la structure '
             'allouée</t></is></c>'
             '<c r="I74" s="%d"><v>0.22</v></c>'
             '<c r="J74" s="%d" t="inlineStr"><is><t>&lt;- elle se réalloue sur TOUT le '
             'groupe. Le reste, murs et permanents, ne sort pas du campus.</t></is></c>'
             '</row>'
             '<row r="75" spans="2:22">'
             '<c r="C75" s="%d" t="inlineStr"><is><t>Contrôle d\'enveloppe — doit rester '
             'à 0 €</t></is></c>'
             '<c r="S75" s="%d"><f>%s</f></c>'
             '</row>') % (XF_LAB, XF_IN, XF_LAB, XF_LAB, XF_CTRL, esc(CTRL))
        for r in (74, 75):
            s = re.sub(r'<row r="%d"[^>]*(?:/>|>.*?</row>)' % r, "", s, count=1, flags=re.S)
        s = re.sub(r'(<row r="76")', L + r"\1", s, count=1)
        data = s.encode("utf-8")
    elif it.filename == "xl/workbook.xml":
        s = data.decode("utf-8")
        s = re.sub(r'<calcPr[^/]*/>', '<calcPr calcId="0" fullCalcOnLoad="1"/>', s)
        data = s.encode("utf-8")
    zout.writestr(it, data)
zout.close(); zin.close()
import os
os.remove(tmp); shutil.move(tmp2, DST)
print("ecrit :", DST)
