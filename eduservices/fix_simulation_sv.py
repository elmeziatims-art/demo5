# -*- coding: utf-8 -*-
"""Repare les colonnes S a V de l'onglet « Cockpit 2 » du classeur SIMULATION.

QUATRE DEFAUTS, dont trois silencieux.

 1. DECALAGE DE 59 LIGNES. La formule de la ligne 13 lit R72, J72, K72, L72,
    O72. Le bloc a ete colle 59 lignes au-dessus de celui pour lequel il avait
    ete ecrit. Chaque ligne repond donc pour une AUTRE classe -- et sans erreur
    Excel, ce qui est le pire cas.
 2. _xlfn.IFERROR et _xlfn.SUMIFS. Tagetik a prefixe les fonctions standard :
    #NOM? a l'ecran. Les formules reecrites n'utilisent plus IFERROR du tout.
 3. COLONNES SOURCES INEXISTANTES. Les SUMIFS pointent $T$6:$T$65, $A$6:$A$65,
    $O$6:$O$124 et des auxiliaires W13 / Y13 -- vestiges de la maquette
    12_Simulateur, ou T portait la structure campus, U le siege et V le driver.
    Ici la restitution ne ramene que M = STRUCTURE_ALLOUEE, et W..Z sont vides.
 4. S S'ARRETE LIGNE 63. Neuf classes n'avaient plus de formule du tout.

CE QUE FAIT LA REALLOCATION REECRITE. La structure allouee des classes fermees
se redistribue sur les classes GARDEES DU MEME CAMPUS -- le campus etant le
couple (MARQUE, VILLE), seules colonnes d'identite disponibles -- au prorata du
nombre de sections, qui est la cle ALLOC_CAMP_CLASS par defaut.

LIMITE ASSUMEE, ET COMMENT LA LEVER. La restitution ne ramene que la structure
allouee TOTALE. Or ses deux moities ne se propagent pas pareil : la structure du
campus (6411 + murs) reste dans le campus, le siege (6236 + holding) se
redistribue sur TOUT le groupe. Tout garder dans le campus surestime donc la
charge qui retombe sur les voisines du campus, et ignore celle qui devrait
partir sur les autres campus -- l'enveloppe groupe reste juste, sa ventilation
non. Pour l'exactitude, ajouter STRUCTURE_CAMPUS et SIEGE a la requete : la vue
V_SIMULATEUR_OUV_FERM les expose deja.

Le classeur porte 5 graphiques et 3 images : openpyxl les detruirait. Patch XML.
"""
import zipfile, re, shutil

SRC, DST = "_up2.xlsx", "SIMULATION_CORRIGE.xlsx"
SHEET = "xl/worksheets/sheet3.xml"        # « Cockpit 2 »
R0, R1 = 13, 72                           # les 60 classes

def esc(f):
    return f.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

#  SUMIFS et IFERROR datent de 2007 : Tagetik les reprefixe en _xlfn a CHAQUE
#  rafraichissement, et la formule tombe en #NOM?. SUMPRODUCT et COUNT sont
#  anterieurs a 2003, Tagetik n'y touche pas. On n'utilise donc plus que ceux-la.
#  La forme a deux arguments -- conditions d'un cote, valeurs de l'autre -- est
#  volontaire : SUMPRODUCT y traite le non-numerique comme zero, donc une ligne
#  vide dans la plage ne fait pas tomber le calcul en #VALEUR!.
#
#  LE DRIVER EST LA STRUCTURE ALLOUEE ELLE-MEME, PAS LES SECTIONS.
#  V_ALLOCATION n'utilise pas une cle mais DEUX : les permanents (6411, ~24 %
#  de la structure) sont alloues aux HEURES, tout le reste -- murs, marque,
#  siege -- par la cle ALLOC_CAMP_CLASS. Les heures dependent du programme
#  (BAC initial 600, BAC alternance 480, MAS alternance 420, BTS 700 par
#  classe), donc sur un campus a plusieurs programmes la structure allouee
#  N'EST PAS proportionnelle aux sections : l'ecart monte a 6,1 %.
#  Verifie sur les 60 lignes : la structure allouee se reconstruit a 0,001 %
#  pres avec ces deux cles, contre 6,1 % avec les sections seules.
#  Repartir la poche liberee au prorata de STRUCTURE_ALLOUEE respecte donc les
#  deux cles a la fois, puisque M les porte deja. Mesure sur la fermeture du
#  Mastere M1 de MBway Paris, contre la reallocation exacte a deux cles :
#      au prorata des SECTIONS    ecart max 4 967 EUR (0,84 %)
#      au prorata de LA STRUCTURE ecart max   670 EUR (0,11 %)   <- retenu

#  Une ligne vide ne doit rien afficher. Deux tests, parce qu'une restitution
#  peut echouer des deux facons : plus d'identite (le POV ne ramene pas la
#  ligne) ou plus de chiffres (la ligne existe mais la mesure est absente).
CAMP = '($C$%d:$C$%d=$C{r})*($D$%d:$D$%d=$D{r})' % (R0, R1, R0, R1)
TOUT = 'SUMPRODUCT(' + CAMP + ',$M$%d:$M$%d)' % (R0, R1)
SURV = ('SUMPRODUCT(' + CAMP + '*($R$%d:$R$%d<>"Fermer")' % (R0, R1)
        + ',$M$%d:$M$%d)' % (R0, R1))

VIDE = 'OR($C{r}="",COUNT($H{r}:$Q{r})=0)'

FORM = {
    #  structure APRES : la sienne, plus sa part de celle des classes fermees
    #  du meme campus. Le garde-fou sert au cas ou tout un campus ferme.
    "S": ('IF(' + VIDE + ',"",IF($R{r}="Fermer","",'
          'IF(' + SURV + '=0,$M{r},$M{r}*' + TOUT + '/' + SURV + ')))'),
    "T": 'IF(' + VIDE + ',"",IF($R{r}="Fermer","",$J{r}-$K{r}-$S{r}))',
    "U": 'IF(' + VIDE + ',"",IF($R{r}="Fermer",-$L{r},0))',
    "V": ('IF(' + VIDE + ',"",IF($R{r}="Fermer",'
          '"Fermer = perdre "&TEXT($L{r},"#,##0")&" € de contribution. Le fixe, lui, reste.",'
          'IF(AND($O{r}>=0,$T{r}<0),'
          '"BASCULE : saine avant, en déficit à cause d\'une fermeture voisine.",'
          'IF(AND($O{r}<0,$L{r}>0),'
          '"Déficit au coût complet mais contribution positive : ne pas fermer, '
          'c\'est un artefact d\'allocation.",'
          'IF($O{r}<0,"Contribution négative : vrai point dur.",'
          '"Rentable. Point mort "&TEXT($P{r},"#,##0")&" étudiants, marge de sécurité "'
          '&TEXT($Q{r},"0%")&".")))))'),
}

z = zipfile.ZipFile(SRC)
d = z.read(SHEET).decode("utf-8")

#  les styles a reutiliser : ceux de la ligne 13, qui les a tous
styles = {}
for col in "STUV":
    m = re.search(r'<c r="%s13"((?: [a-z]+="[^"]*")*)' % col, d)
    styles[col] = re.search(r's="(\d+)"', m.group(1)).group(1) if m and 's="' in m.group(1) else None
print("styles repris de la ligne 13 :", styles)

remplacees, creees = 0, 0
for r in range(R0, R1 + 1):
    mrow = re.search(r'(<row r="%d"[^>]*>)(.*?)(</row>)' % r, d, re.S)
    assert mrow, "ligne %d introuvable" % r
    tete, corps, pied = mrow.group(1), mrow.group(2), mrow.group(3)
    #  on decoupe la ligne en cellules, on jette S a V, on remet les neuves a
    #  leur place : Excel exige que les cellules d'une ligne soient dans l'ordre
    #  des colonnes, et la ligne porte aussi des cellules vides en W..AA.
    cel = re.findall(r'<c r="([A-Z]+)\d+"[^>]*(?:/>|>.*?</c>)', corps, re.S)
    frag = re.findall(r'<c r="[A-Z]+\d+"[^>]*(?:/>|>.*?</c>)', corps, re.S)
    garde = [(c, f) for c, f in zip(cel, frag) if c not in ("S", "T", "U", "V")]
    for col in "STUV":
        if col in cel: remplacees += 1
        else: creees += 1
        garde.append((col, '<c r="%s%d"%s><f>%s</f></c>' % (
            col, r, ' s="%s"' % styles[col] if styles[col] else "",
            esc(FORM[col].replace("{r}", str(r))))))
    rang = lambda c: sum((ord(ch) - 64) * 26 ** i for i, ch in enumerate(reversed(c)))
    garde.sort(key=lambda t: rang(t[0]))
    d = d[:mrow.start()] + tete + "".join(f for _, f in garde) + pied + d[mrow.end():]

#  Excel doit tout recalculer a l'ouverture
d = re.sub(r'\s*fullCalcOnLoad="[^"]*"', "", d)
d = d.replace("<sheetData>", "<sheetData>", 1)
print("cellules remplacees %d, creees %d" % (remplacees, creees))

wbx = z.read("xl/workbook.xml").decode("utf-8")
if "<calcPr" in wbx:
    wbx = re.sub(r'<calcPr[^>]*/>', '<calcPr calcId="191029" fullCalcOnLoad="1"/>', wbx)
else:
    wbx = wbx.replace("</workbook>", '<calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')

zo = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for it in z.infolist():
    if it.filename == "xl/calcChain.xml":      # obsolete des qu'on touche aux formules
        continue
    if it.filename == SHEET:      zo.writestr(it, d.encode("utf-8"))
    elif it.filename == "xl/workbook.xml": zo.writestr(it, wbx.encode("utf-8"))
    elif it.filename == "[Content_Types].xml":
        ct = z.read(it.filename).decode("utf-8")
        ct = ct.replace('<Override PartName="/xl/calcChain.xml" '
                        'ContentType="application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.calcChain+xml"/>', "")
        zo.writestr(it, ct.encode("utf-8"))
    else: zo.writestr(it, z.read(it.filename))
zo.close()
print("ecrit :", DST)
