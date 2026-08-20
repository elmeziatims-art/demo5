#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rend le moteur vivant DYNAMIQUE et robuste a la croissance des restitutions
Tagetik (socle/compta/PNL/allocation qui grossissent, filtrage, hierarchie) :
  - toutes les plages sources en COLONNE ENTIERE (SUMIFS auto-extensibles) ;
  - chaque formule GARDEE  =IF(cle="","",...)  -> lignes vides gratuites & propres ;
  - colonnes calculees pre-etendues a de grandes bornes ;
  - le reel (non-budget) affiche sa propre valeur (colonne live jamais 'morte').
Bornes (modifiables) : moteur/alloc = 2000, PNL = 6000, cap = 512.
"""
import openpyxl
F="CAD_SAAD_LIVE.xlsx"; wb=openpyxl.load_workbook(F)
NM=2000; NP=6000; NC=512
def G(inner,key="$A{r}"):   # garde : renvoie "" si cle vide
    return '=IF('+key+'="","",'+inner+')'

# ============================================================ _CALC_MOTEUR
cm=wb["_CALC_MOTEUR"]
SOC="Socle!$%s:$%s,Socle!$C:$C,$A{r},Socle!$D:$D,$C{r},Socle!$E:$E,$D{r},Socle!$F:$F,$E{r},Socle!$G:$G,\"2026\""
def soc(col): return "SUMIFS("+SOC%(col,col)+")"
CAMP="SUMIFS(Campagne!$%s:$%s,Campagne!$C:$C,$A{r})"
def lever_m(col16):  # V01/V02/V03 -> cad E/F/G row
    return 'IF($B{r}="V01",cad!$E$%d,IF($B{r}="V02",cad!$F$%d,cad!$G$%d))'%(col16,col16,col16)
COEF=('IF($F{r}="MBWAY",cad!$K$7,IF($F{r}="ISCOM",cad!$K$8,IF($F{r}="IPAC",cad!$K$9,'
      'IF($F{r}="PIGIER",cad!$K$10,cad!$K$11))))')
mot={
 "A":'=IF(Moteur!D{r}="","",Moteur!D{r})',"B":'=IF(Moteur!B{r}="","",Moteur!B{r})',
 "C":'=IF(Moteur!F{r}="","",Moteur!F{r})',"D":'=IF(Moteur!G{r}="","",Moteur!G{r})',
 "E":'=IF(Moteur!H{r}="","",Moteur!H{r})',"F":'=IF(Moteur!E{r}="","",Moteur!E{r})',
 "G":G(soc("H")),"H":G(soc("N")),"I":G(soc("P")),"J":G(soc("W")),"K":G(soc("X")),
 "L":G(soc("Y")),"M":G(soc("V")),
 "N":G('IF(OR($D{r}="B1",$D{r}="M1",$D{r}="BTS1"),1,0)'),
 "O":G(CAMP%("D","D")),"P":G(CAMP%("E","E")),"Q":G(CAMP%("F","F")),
 "R":G(CAMP%("K","K")),"S":G(CAMP%("M","M")),
 "T":G('SUMIFS(Pilotage!$Q:$Q,Pilotage!$F:$F,$A{r})'),
 "U":G('SUMIFS(Pilotage!$N:$N,Pilotage!$F:$F,$A{r})'),
 "V":G(lever_m(16)),"W":G(lever_m(17)),"X":G(lever_m(18)),"Y":G(lever_m(19)),
 "Z":G(lever_m(20)),"AA":G(lever_m(21)),"AB":G(lever_m(30)),"AC":G(COEF),
 "AD":G('($O{r}*(1+$W{r})^$S{r}+$P{r}*IFERROR((($T{r}/$U{r})*(1+$V{r}))^$R{r},0))'
        '*IFERROR($G{r}/$Q{r},0)*($J{r}+$Y{r})*$K{r}*($L{r}+$Z{r})'),
 "AE":G('IF($N{r}=1,$AD{r},0)'),
 "AF":G('IF($N{r}=1,$AD{r},$H{r}*($M{r}+$AA{r}))'),
 "AG":G('$I{r}*(1+$X{r}*$AC{r})'),
 "AH":G('$AF{r}*$AG{r}+$AE{r}*$AB{r}'),
}
for r in range(2,NM+1):
    for col,tpl in mot.items(): cm["%s%d"%(col,r)]=tpl.format(r=r)

# Moteur a-cote O,P,Q,R,S
mo=wb["Moteur"]
for r in range(2,NM+1):
    g='Moteur!D%d'%r
    mo["O%d"%r]='=IF(D%d="","",_CALC_MOTEUR!AE%d)'%(r,r)
    mo["P%d"%r]='=IF(D%d="","",_CALC_MOTEUR!AF%d)'%(r,r)
    mo["Q%d"%r]='=IF(D%d="","",_CALC_MOTEUR!AG%d)'%(r,r)
    mo["R%d"%r]='=IF(D%d="","",_CALC_MOTEUR!AH%d)'%(r,r)
    mo["S%d"%r]='=IF(D%d="","",R%d-M%d)'%(r,r,r)
    for c in ("O","P","Q","R","S"): mo["%s%d"%(c,r)].number_format="# ##0"

# ============================================================ _CALC_PNL
cp=wb["_CALC_PNL"]
# CAF scalars -> colonnes entieres
cp["R1"]=('=SUMIFS(Compta!$F:$F,Compta!$B:$B,"7062",Compta!$C:$C,"2026")'
          '+SUMIFS(Compta!$F:$F,Compta!$B:$B,"706",Compta!$C:$C,"2026")'
          '+SUMIFS(Compta!$F:$F,Compta!$B:$B,"708",Compta!$C:$C,"2026")')
for i,v in [(2,"V01"),(3,"V02"),(4,"V03")]:
    cp["R%d"%i]='=SUMIFS(Moteur!$R:$R,Moteur!$B:$B,"%s")/$R$1'%v
def lever_p(row):
    return 'IF($D{r}="V01",cad!$E$%d,IF($D{r}="V02",cad!$F$%d,cad!$G$%d))'%(row,row,row)
FAC=('IF(OR($B{r}="7062",$B{r}="706",$B{r}="708"),$N{r},'
     'IF($B{r}="6231",1+$G{r},IF($B{r}="6236",1+$H{r},'
     'IF(OR($B{r}="621",$B{r}="604",$B{r}="6063"),$N{r}*(1-$L{r}),'
     'IF(OR($B{r}="6411",$B{r}="6413",$B{r}="6414",$B{r}="645"),(1+$J{r})*(1+$K{r}),'
     'IF(OR($B{r}="613",$B{r}="615",$B{r}="616",$B{r}="6226",$B{r}="625",$B{r}="626",$B{r}="6281"),(1+$I{r})*(1-$L{r})*(1+$M{r}),'
     'IF(OR($B{r}="6331",$B{r}="63511",$B{r}="6333"),(1+$I{r})*(1-$L{r}),'
     'IF($B{r}="6811",1+$I{r},1)))))))')
pnl={
 "A":'=IF(PNL!A{r}="","",PNL!A{r})',"B":'=IF(PNL!B{r}="","",PNL!B{r})',
 "C":'=IF(PNL!C{r}="","",PNL!C{r})',"D":'=IF(PNL!D{r}="","",PNL!D{r})',
 "E":G('IF(AND($C{r}="2027",OR($D{r}="V01",$D{r}="V02",$D{r}="V03")),1,0)'),
 "F":G('IF($E{r}=1,SUMIFS(Compta!$F:$F,Compta!$A:$A,$A{r},Compta!$B:$B,$B{r},Compta!$C:$C,"2026"),0)'),
 "G":G(lever_p(16)),"H":G(lever_p(17)),"I":G(lever_p(22)),"J":G(lever_p(23)),
 "K":G(lever_p(24)),"L":G(lever_p(25)),"M":G(lever_p(26)),
 "N":G('IF($D{r}="V01",$R$2,IF($D{r}="V02",$R$3,$R$4))'),
 "O":G(FAC),
 "P":G('IF($E{r}=1,$F{r}*$O{r},PNL!G{r})'),   # reel -> sa propre valeur
 "T":G('IF($E{r}=1,IF(OR($B{r}="7062",$B{r}="706",$B{r}="708"),$P{r},'
       'IF(AND(LEFT($B{r},1)="6",$B{r}<>"6811"),-$P{r},0)),0)'),
}
for r in range(2,NP+1):
    for col,tpl in pnl.items(): cp["%s%d"%(col,r)]=tpl.format(r=r)

# PNL a-cote H,I
pn=wb["PNL"]
for r in range(2,NP+1):
    pn["H%d"%r]='=IF(PNL!A%d="","",_CALC_PNL!P%d)'%(r,r)
    pn["I%d"%r]='=IF(PNL!A%d="","",IF(_CALC_PNL!E%d=1,H%d-G%d,""))'%(r,r,r,r)
    pn["H%d"%r].number_format="# ##0"

# ============================================================ _CALC_ALLOC
ca=wb["_CALC_ALLOC"]
def allk(col,c1,k1,c2=None,k2=None):
    s="SUMIFS(Allocation!$%s:$%s,Allocation!$%s:$%s,%s"%(col,col,c1,c1,k1)
    if c2: s+=",Allocation!$%s:$%s,%s"%(c2,c2,k2)
    return s+")"
def cpt(acct,ent="$B{r}",ex="$A{r}"):
    return 'SUMIFS(Compta!$F:$F,Compta!$A:$A,%s,Compta!$B:$B,"%s",Compta!$C:$C,%s)'%(ent,acct,ex)
alloc={
 "A":'=IF(Allocation!C{r}="","",Allocation!C{r})',"B":'=IF(Allocation!D{r}="","",Allocation!D{r})',
 "C":'=IF(Allocation!E{r}="","",Allocation!E{r})',"D":'=IF(Allocation!F{r}="","",Allocation!F{r})',
 "E":'=IF(Allocation!G{r}="","",Allocation!G{r})',"F":'=IF(Allocation!H{r}="","",Allocation!H{r})',
 "G":'=IF(Allocation!D{r}="","",Allocation!I{r})',"H":'=IF(Allocation!D{r}="","",Allocation!J{r})',
 "I":'=IF(Allocation!D{r}="","",Allocation!K{r})',
 "J":G('SUMIFS(Socle!$K:$K,Socle!$C:$C,$B{r},Socle!$D:$D,$D{r},Socle!$E:$E,$E{r},Socle!$F:$F,$F{r},Socle!$G:$G,$A{r})'),
 "K":G('$H{r}*IF(AND(LEFT($D{r},3)="BAC",$F{r}="INIT"),600,IF(LEFT($D{r},3)="BAC",480,'
       'IF(AND(LEFT($D{r},3)="MAS",$F{r}="INIT"),520,IF(LEFT($D{r},3)="MAS",420,IF($F{r}="INIT",1000,700)))))'),
 "L":G(allk("I","C","$A{r}","D","$B{r}")),"M":G(allk("J","C","$A{r}","D","$B{r}")),
 "N":G(allk("K","C","$A{r}","D","$B{r}")),
 "O":G('SUMIFS($K:$K,$A:$A,$A{r},$B:$B,$B{r})'),"P":G('SUMIFS($J:$J,$A:$A,$A{r},$B:$B,$B{r})'),
 "Q":G(allk("I","C","$A{r}","E","$C{r}")),"R":G(allk("J","C","$A{r}","E","$C{r}")),
 "S":G(allk("K","C","$A{r}","E","$C{r}")),
 "T":G(allk("I","C","$A{r}")),"U":G(allk("J","C","$A{r}")),"V":G(allk("K","C","$A{r}")),
 "W":G(cpt("621")),"X":G(cpt("6411")),
 "Y":G(cpt("604")+"+"+cpt("6063")),"Z":G(cpt("6231")),
 "AA":G("+".join(cpt(a) for a in ("6413","645","613","615","616","625","63511"))),
 "AB":G("+".join(cpt(a,ent='"GRP"') for a in ("6414","6226","6236","626","6281","6331","6333"))),
 "AC":G('IF(Pilotage!$E$10="Chiffre d\'affaires",$I{r},IF(Pilotage!$E$10="Effectif",$G{r},$H{r}))'),
 "AD":G('IF(Pilotage!$E$10="Chiffre d\'affaires",$N{r},IF(Pilotage!$E$10="Effectif",$L{r},$M{r}))'),
 "AE":G('IF(Pilotage!$E$8="Chiffre d\'affaires",$N{r},IF(Pilotage!$E$8="Effectif",$L{r},$M{r}))'),
 "AF":G('IF(Pilotage!$E$8="Chiffre d\'affaires",$S{r},IF(Pilotage!$E$8="Effectif",$Q{r},$R{r}))'),
 "AG":G('IF(Pilotage!$E$9="Chiffre d\'affaires",$S{r},IF(Pilotage!$E$9="Effectif",$Q{r},$R{r}))'),
 "AH":G('IF(Pilotage!$E$9="Chiffre d\'affaires",$V{r},IF(Pilotage!$E$9="Effectif",$T{r},$U{r}))'),
 "AI":G('$W{r}*IFERROR($K{r}/$O{r},0)'),"AJ":G('$X{r}*IFERROR($K{r}/$O{r},0)'),
 "AK":G('$Y{r}*IFERROR($G{r}/$L{r},0)+$Z{r}*IFERROR($J{r}/$P{r},0)'),
 "AL":G('$AA{r}*IFERROR($AC{r}/$AD{r},0)'),
 "AM":G('$AB{r}*IFERROR($AG{r}/$AH{r},0)*IFERROR($AE{r}/$AF{r},0)*IFERROR($AC{r}/$AD{r},0)'),
 "AN":G('$I{r}-($AI{r}+$AJ{r}+$AK{r}+$AL{r}+$AM{r})'),
}
for r in range(2,NM+1):
    for col,tpl in alloc.items(): ca["%s%d"%(col,r)]=tpl.format(r=r)

# Allocation a-cote V-AB
al=wb["Allocation"]
acote={"V":"AI","W":"AJ","X":"AK","Y":"AL","Z":"AM","AA":"AN"}
for r in range(2,NM+1):
    for dst,src in acote.items():
        al["%s%d"%(dst,r)]='=IF(Allocation!D%d="","",_CALC_ALLOC!%s%d)'%(r,src,r)
    al["AB%d"%r]='=IF(Allocation!D%d="","",AA%d-T%d)'%(r,r,r)
    for c in ("V","W","X","Y","Z","AA"): al["%s%d"%(c,r)].number_format="# ##0"

# ============================================================ CAP (Pilotage) rejoue
# NB : le cap (13-26) partage la feuille Pilotage avec la synthese (28-46) qui
# reutilise les colonnes N/M/Q -> la plage zero-somme reste STRICTEMENT 13:26.
ps=wb["Pilotage"]
CR=26  # derniere ligne du cap (14 campus). Si +de campus : on agrandit ce bloc.
for r in range(13,CR+1):
    ps["Q%d"%r]=('=IF($F%d="","",$N%d*$M%d*(SUM($N$13:$N$%d)/SUMPRODUCT($N$13:$N$%d,$M$13:$M$%d)))'
                 %(r,r,r,CR,CR,CR))
    ps["R%d"%r]='=IF($F%d="","",$Q%d-$O%d)'%(r,r,r)
    ps["Q%d"%r].number_format="# ##0"

# ============================================================ Synthese / rollup / reconciliation -> colonnes entieres
D3="cad!$D$3"
for i in range(14):
    r=30+i
    ps["G%d"%r]='=SUMIFS(Moteur!$P:$P,Moteur!$D:$D,$D%d,Moteur!$B:$B,%s)'%(r,D3)
    ps["H%d"%r]='=SUMIFS(Moteur!$R:$R,Moteur!$D:$D,$D%d,Moteur!$B:$B,%s)'%(r,D3)
    ps["K%d"%r]=('=SUMIFS(_CALC_PNL!$T:$T,_CALC_PNL!$A:$A,$D%d,_CALC_PNL!$D:$D,%s,_CALC_PNL!$C:$C,"2027")'%(r,D3))
    ps["M%d"%r]="=IFERROR(K%d/G%d,0)"%(r,r)
    ps["N%d"%r]='=SUMIFS(Pilotage!$Q:$Q,Pilotage!$F:$F,$D%d)'%r
    ps["O%d"%r]='=SUMIFS(Pilotage!$G:$G,Pilotage!$F:$F,$D%d)'%r
ps["K45"]=('=SUMIFS(_CALC_PNL!$T:$T,_CALC_PNL!$A:$A,"GRP",_CALC_PNL!$D:$D,%s,_CALC_PNL!$C:$C,"2027")'%D3)
for i in range(5):
    r=30+i
    ps["Y%d"%r]='=SUMIFS(Moteur!$R:$R,Moteur!$E:$E,$W%d,Moteur!$B:$B,%s)'%(r,D3)
# reconciliation cad
cad=wb["cad"]
cad["E7"]='=SUMIFS(Moteur!$R:$R,Moteur!$B:$B,$D$3)'
cad["E8"]='=SUMIFS(_CALC_PNL!$T:$T,_CALC_PNL!$D:$D,$D$3,_CALC_PNL!$C:$C,"2027")'
cad["E10"]='=SUMIFS(Moteur!$P:$P,Moteur!$B:$B,$D$3)'

wb.calculation.fullCalcOnLoad=True
wb.save(F)
print("OK dynamic : full-column + gardes, moteur/alloc<=%d, PNL<=%d, cap<=%d. Recalc force a l'ouverture."%(NM,NP,NC))
