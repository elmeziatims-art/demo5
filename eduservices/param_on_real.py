#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sur le VRAI design (TEST3_new) : centralise l'exercice ALLOC sur C11.
Seul delta pour le deux-temps 2027. Rien d'autre touché."""
from tgk_surgery import Book
from tgk_style import StyleBank
b=Book("TEST3_new.xlsm")
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
al.set_text("C11","2026",s=XVAL)
b.set_styles(sb.render()); b.save("TEST3_2steps.xlsm")
print(f"OK -> TEST3_2steps.xlsm | {n} filtres centralisés sur C11")
