#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Centralise l'exercice porteur de l'allocation sur UNE cellule (ALLOC!C11)
au lieu de 624 "2026" en dur. Le jour de la 1re soumission (slot 2027 réel),
on change juste C11 -> "2027" et tout bascule."""
from tgk_surgery import Book
from tgk_style import StyleBank
b=Book("TEST3_2027.xlsm")
sb=StyleBank(b.styles_xml())
NAVY="1F3864"; CREAM="FFF2CC"; GOLDB="E0A800"
XLBL=sb.xf(font=sb.font(11,True,False,NAVY),halign="left",valign="center")
XVAL=sb.xf(font=sb.font(11,True,False,"1B5FA6"),fill=sb.fill(CREAM),
           border=sb.border(top=(GOLDB,"thin"),bottom=(GOLDB,"thin"),left=(GOLDB,"thin"),right=(GOLDB,"thin")),
           halign="center",valign="center")
al=b.sheet("ALLOC")
# 1) remplace le filtre d'exercice par la cellule paramètre, partout
n=0
for rn,cells in al.rows.items():
    for cn,(attrs,content) in list(cells.items()):
        if content and '$C$1:$C$175,"2026"' in content:
            al.rows[rn][cn]=(attrs, content.replace('$C$1:$C$175,"2026"','$C$1:$C$175,$C$11'))
            n+=1
# 2) pose la cellule paramètre (libellée), porteur = 2026 pour l'instant
al.set_text("B11","Exercice restitué (porteur du budget)",s=XLBL)
al.set_text("C11","2026",s=XVAL)
b.set_styles(sb.render())
b.save("TEST3_2027b.xlsm")
print(f"OK -> TEST3_2027b.xlsm | {n} filtres centralisés sur ALLOC!C11")
