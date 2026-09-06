#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Option (b) : l'allocation lit le budget FIGÉ (vue Allocation + Compta), clés
live, exercice centralisé sur ALLOC!C11. Repart de TEST3_fix2 (sourcing vue
d'origine + ratios câblés) — pas de moteurs live. Fichier unique, à splitter."""
from tgk_surgery import Book
from tgk_style import StyleBank
b=Book("TEST3_fix2.xlsm")
sb=StyleBank(b.styles_xml())
NAVY="1F3864"; CREAM="FFF2CC"; GOLDB="E0A800"
XLBL=sb.xf(font=sb.font(11,True,False,NAVY),halign="left",valign="center")
XVAL=sb.xf(font=sb.font(11,True,False,"1B5FA6"),fill=sb.fill(CREAM),
           border=sb.border(top=(GOLDB,"thin"),bottom=(GOLDB,"thin"),left=(GOLDB,"thin"),right=(GOLDB,"thin")),
           halign="center",valign="center")
al=b.sheet("ALLOC")
n=0
for rn,cells in al.rows.items():
    for cn,(attrs,content) in list(cells.items()):
        if content and '$C$1:$C$175,"2026"' in content:
            al.rows[rn][cn]=(attrs, content.replace('$C$1:$C$175,"2026"','$C$1:$C$175,$C$11')); n+=1
al.set_text("B11","Exercice restitué (2026 réel / 2027 budget)",s=XLBL)
al.set_text("C11","2026",s=XVAL)   # 2026 testable maintenant ; passer à 2027 après 1re soumission
b.set_styles(sb.render())
b.save("TEST3_final.xlsm")
print(f"OK -> TEST3_final.xlsm | {n} filtres sur C11 | sourcing = vue+Compta (figé)")
