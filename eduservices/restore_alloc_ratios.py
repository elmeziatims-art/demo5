#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cable les ratios de cle d'allocation (_CALC_ALLOC AC-AH, AP-AQ) : chaque ratio
SELECTIONNE le bon total (node/campus/marque/groupe) selon la cle choisie
(ALLOC!N1-N4 <- saisies C6-C9). Rend l'allocation live et sensible a la cle."""
from tgk_surgery import Book
b=Book("TEST3_fix.xlsm")
al=b.sheet("_CALC_ALLOC")
def SEL(r,keycell,eff,cls,ca):
    return (f'IF($A{r}="","",IF(ALLOC!${keycell}="VOL_EFF",${eff}{r},'
            f'IF(ALLOC!${keycell}="VOL_CLASS",${cls}{r},${ca}{r})))')
# col -> (cellule cle, colEFF, colCLS, colCA)
SPEC={
 "AC":("N$4","G","H","I"),   # D3C : node par N4
 "AD":("N$4","L","M","N"),   # D3E : total campus par N4
 "AE":("N$3","L","M","N"),   # D2E : total campus par N3
 "AF":("N$3","Q","R","S"),   # D2M : total marque par N3
 "AG":("N$1","Q","R","S"),   # D1M : total marque par N1
 "AH":("N$1","T","U","V"),   # D1G : total groupe par N1
 "AP":("N$2","Q","R","S"),   # D1M_K4 : total marque par N2
 "AQ":("N$2","T","U","V"),   # D1G_K4 : total groupe par N2
}
for r in range(2,176):
    for col,(kc,eff,cls,ca) in SPEC.items():
        ref=f"{col}{r}"
        al.set_formula(ref, SEL(r,kc,eff,cls,ca), s=al.get_style(ref))
b.save("TEST3_fix2.xlsm")
print("OK -> TEST3_fix2.xlsm (ratios d'allocation cables)")
