#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bascule l'allocation sur 2027, EN PLACE (aucun onglet ajouté) :
- pools de charges <- _CALC_PNL projeté 2027 (mapping PCG), version active
- volumes node (G eff, I CA, J new) <- Moteur budget 2027 (version active)
- classes (H) dérivées : effectif 2027 x (classes/effectif) 2026 (Socle)
- agrégats E_/M_/G_ <- SUMIFS internes sur les volumes 2027
- ALLOC : CA (D) = coût complet (K) + marge (L) -> CA 2027 live cohérent
Le grain reste porté par la vue Allocation (millésime 2026 = porteur budget)."""
from tgk_surgery import Book
b=Book("TEST3_fix2.xlsm")
al=b.sheet("_CALC_ALLOC")
POOLS_CAMP={"W":["621"],"X":["6411"],"Y":["604","6063"],"Z":["6231"],
            "AA":["6413","645","613","615","616","625","63511"]}
POOLS_GRP={"AB":["6414","6226","626","6281","6331","6333"],"AO":["6236"]}
def g(r,inner): return f'IF($A{r}="","",{inner})'
for r in range(2,176):
    def PNL(acc,ent=None):
        e=ent or f"$B{r}"
        return (f'SUMIFS(_CALC_PNL!$P$1:$P$1347,_CALC_PNL!$A$1:$A$1347,{e},'
                f'_CALC_PNL!$B$1:$B$1347,"{acc}",_CALC_PNL!$C$1:$C$1347,"2027",'
                f'_CALC_PNL!$D$1:$D$1347,cad!$P$1)')
    def MOT(col):
        return (f'SUMIFS(Moteur!${col}$1:${col}$175,Moteur!$D$1:$D$175,$B{r},'
                f'Moteur!$F$1:$F$175,$D{r},Moteur!$G$1:$G$175,$E{r},'
                f'Moteur!$H$1:$H$175,$F{r},Moteur!$B$1:$B$175,cad!$P$1)')
    def SOC(col):
        return (f'SUMIFS(Socle!${col}$1:${col}$175,Socle!$C$1:$C$175,$B{r},'
                f'Socle!$D$1:$D$175,$D{r},Socle!$E$1:$E$175,$E{r},'
                f'Socle!$F$1:$F$175,$F{r},Socle!$G$1:$G$175,"2026")')
    def AGG(col,lvl):
        crit={"E":f',$B$1:$B$175,$B{r}',"M":f',$C$1:$C$175,$C{r}',"G":''}[lvl]
        return f'SUMIFS(${col}$1:${col}$175,$A$1:$A$175,$A{r}{crit})'
    def put(ref,inner): al.set_formula(ref,g(r,inner),s=al.get_style(ref))
    # volumes node <- Moteur 2027
    put(f"G{r}",MOT("P")); put(f"I{r}",MOT("R")); put(f"J{r}",MOT("O"))
    put(f"H{r}",f'$G{r}*IFERROR({SOC("O")}/{SOC("M")},0)')       # classes dérivées
    # agrégats internes
    for col,c in (("L","G"),("M","H"),("N","I")): put(f"{col}{r}",AGG(c,"E"))
    for col,c in (("Q","G"),("R","H"),("S","I")): put(f"{col}{r}",AGG(c,"M"))
    for col,c in (("T","G"),("U","H"),("V","I")): put(f"{col}{r}",AGG(c,"G"))
    # pools <- _CALC_PNL 2027
    for col,accs in POOLS_CAMP.items(): put(f"{col}{r}","+".join(PNL(a) for a in accs))
    for col,accs in POOLS_GRP.items():  put(f"{col}{r}","+".join(PNL(a,'"GRP"') for a in accs))

# ALLOC : CA (D) = coût complet (K) + marge (L) => CA 2027 cohérent
alloc=b.sheet("ALLOC")
n=0
for r in range(18,96):
    if alloc.get_cell(f"D{r}") is not None:
        alloc.set_formula(f"D{r}",f"K{r}+L{r}",s=alloc.get_style(f"D{r}")); n+=1
b.save("TEST3_2027.xlsm")
print(f"OK -> TEST3_2027.xlsm (bascule 2027 ; {n} lignes CA ALLOC recâblées)")
