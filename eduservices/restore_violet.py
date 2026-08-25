#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restaure les formules des colonnes 'violettes' (hypotheses) qui etaient
tombees en sentinelle 1000 dans TEST3. References DIRECTES vers cad (aucune
zone nommee), styles preserves, briques Tagetik intactes."""
from tgk_surgery import Book
b=Book("TEST3.xlsm")
def IFV(A,V,c,d,e):  # switch de version (V01/V02/V03) -> cad C/D/E ligne donnee
    return f'IF({A}="","",IF({V}="V01",cad!{c},IF({V}="V02",cad!{d},cad!{e})))'
# ---- _CALC_MOTEUR : V..AC (version=$B, marque=$F), lignes 2..175 ----
cm=b.sheet("_CALC_MOTEUR")
MOT={ "V":23,"W":24,"X":25,"Y":26,"Z":27,"AA":28,"AB":39 }   # colonne -> ligne cad (C/D/E)
for r in range(2,176):
    A=f"$A{r}"; V=f"$B{r}"; F=f"$F{r}"
    for col,cr in MOT.items():
        f=IFV(A,V,f"$C${cr}",f"$D${cr}",f"$E${cr}")
        cm.set_formula(f"{col}{r}", f, s=cm.get_style(f"{col}{r}"))
    # AC = coef prix par marque -> cad J12..J16
    ac=(f'IF({A}="","",IF({F}="MBWAY",cad!$J$12,IF({F}="ISCOM",cad!$J$13,'
        f'IF({F}="IPAC",cad!$J$14,IF({F}="PIGIER",cad!$J$15,cad!$J$16)))))')
    cm.set_formula(f"AC{r}", ac, s=cm.get_style(f"AC{r}"))
# ---- _CALC_PNL : G..M (version=$D), lignes 2..1347 ----
cp=b.sheet("_CALC_PNL")
PNL={ "G":23,"H":24,"I":32,"J":33,"K":34,"L":35,"M":36 }
for r in range(2,1348):
    A=f"$A{r}"; V=f"$D{r}"
    for col,cr in PNL.items():
        f=IFV(A,V,f"$C${cr}",f"$D${cr}",f"$E${cr}")
        cp.set_formula(f"{col}{r}", f, s=cp.get_style(f"{col}{r}"))
b.save("TEST3_fix.xlsm")
print("OK -> TEST3_fix.xlsm")
