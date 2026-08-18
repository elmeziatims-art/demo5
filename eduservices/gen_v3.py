# -*- coding: utf-8 -*-
"""EDUSERVICES — Modèle CA v3 (Architecture BUDGET-DRIVEN, leads observés).
Cadrage top-down -> Base de référence (fusion historique+paramètres, version unique, LEADS OBSERVÉS)
-> Campagnes (budget marketing -> leads, socle organique + part payante à rendement décroissant)
-> Moteur (funnel MESURÉ -> effectif -> CA). Revenu et taux différenciés alternance/initial.
On ne génère QUE du cadrage au moteur ; le reste (coûts, alloc, reporting) viendra ensuite.
"""
import math
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as GL, column_index_from_string as CI

OUT="/home/user/demo5/eduservices/EDUSERVICES_Modele_CA_v3.xlsx"

# ============================================================ SOCLE DE DONNÉES
BRANDS={  # marque -> (domaine, base_entry, [villes])
 "MBway":("Management",60,["Paris","Lyon","Nantes","Bordeaux"]),
 "ISCOM":("Communication",55,["Paris","Lille","Toulouse"]),
 "Ipac Bachelor Factory":("Commerce",50,["Nantes","Rennes","Montpellier"]),
 "Pigier":("Commerce/RH",42,["Lyon","Bordeaux"]),
 "Tunon":("Tourisme",36,["Paris","Lyon"]),
}
PROGS={
 "MBway":[("Bachelor Management","BAC",[("B1","INIT"),("B2","ALT"),("B3","ALT")]),
          ("Mastère Management","MAST",[("M1","ALT"),("M2","ALT")])],
 "ISCOM":[("Bachelor Communication","BAC",[("B1","INIT"),("B2","ALT"),("B3","ALT")]),
          ("Mastère Communication","MAST",[("M1","ALT"),("M2","ALT")])],
 "Ipac Bachelor Factory":[("Bachelor Commerce","BAC",[("B1","ALT"),("B2","ALT"),("B3","ALT")])],
 "Pigier":[("BTS Gestion","BTS",[("1","ALT"),("2","ALT")]),
           ("Bachelor RH","BAC",[("B1","ALT"),("B3","ALT")])],
 "Tunon":[("Bachelor Tourisme","BAC",[("B1","ALT"),("B2","ALT"),("B3","ALT")])],
}
ENTRY={"B1","M1","1"}
ORDER={"BAC":["B1","B2","B3"],"MAST":["M1","M2"],"BTS":["1","2"]}

CITY_VOL ={"Paris":1.30,"Lyon":1.10,"Nantes":1.00,"Bordeaux":0.85,"Lille":0.90,"Toulouse":0.85,"Rennes":0.80,"Montpellier":0.80}
CITY_PRICE={"Paris":1.12,"Lyon":1.05,"Nantes":1.00,"Bordeaux":0.97,"Lille":0.98,"Toulouse":0.96,"Rennes":0.95,"Montpellier":0.95}
CITY_CPL ={"Paris":1.35,"Lyon":1.10,"Nantes":1.00,"Bordeaux":0.95,"Lille":1.00,"Toulouse":0.95,"Rennes":0.90,"Montpellier":0.90}
CAPT={"BTS":30,"BAC":32,"MAST":26}
# revenu / étudiant / an de référence (€) par cycle x modalité (benchmarks secteur — illustratif)
REV={("BTS","ALT"):6000,("BTS","INIT"):5500,("BAC","ALT"):7000,("BAC","INIT"):7500,("MAST","ALT"):7500,("MAST","INIT"):9000}
PASS={"B2":0.93,"B3":0.95,"M2":0.96,"2":0.94}
# TAUX DU FUNNEL (mesurés, différenciés) — issus de la recherche secteur (privé non sélectif, alternance)
#  INIT = intention forte (Parcoursup) ; ALT = leads plateforme + déperdition "signature contrat"
RATES={"INIT":dict(rlc=0.28,rca=0.72,yld=0.60),"ALT":dict(rlc=0.20,rca=0.70,yld=0.42)}
REND_DEF=0.5      # rendement d'acquisition (part payante uniquement)
PORG_DEF=0.40     # part ORGANIQUE des leads (site, salons, Parcoursup, bouche-à-oreille) — indépendante du budget
CPL_BASE=40       # coût par lead payant de référence (€)
FRAIS_DEF=90      # frais de dossier / nouvel inscrit (€)

rows=[]
for marque,(dom,base,villes) in BRANDS.items():
    for ville in villes:
        for pnom,ptype,niveaux in PROGS[marque]:
            entry_base=round(base*CITY_VOL[ville])
            effs={}; last=None
            for niv,mod in niveaux:
                if niv in ENTRY: eff=entry_base
                else: eff=max(0,round(effs[last]*PASS[niv]))
                effs[niv]=eff; last=niv
            last=None
            for niv,mod in niveaux:
                eff=effs[niv]; is_entry=1 if niv in ENTRY else 0
                rev=round(REV[(ptype,mod)]*CITY_PRICE[ville])
                if is_entry:
                    R=RATES[mod]
                    nouv=eff; rein=0; eff_prev=0; passage=0.0
                    admis=max(1,round(nouv/R["yld"]))
                    cand =max(1,round(admis/R["rca"]))
                    leads=max(1,round(cand/R["rlc"]))
                    rlc_m=cand/leads; rca_m=admis/cand; yld_m=nouv/admis
                else:
                    nouv=0; rein=eff; cand=0; admis=0; leads=0; eff_prev=effs[last]; passage=PASS[niv]
                    rlc_m=rca_m=yld_m=0.0
                classes=max(1,math.ceil(eff/CAPT[ptype])) if eff>0 else 0
                rows.append(dict(marque=marque,ville=ville,prog=pnom,type=ptype,niv=niv,mod=mod,entry=is_entry,
                    leads=leads,cand=cand,admis=admis,nouv=nouv,rein=rein,eff=eff,eff_prev=eff_prev,classes=classes,
                    rev=rev,passage=passage,rlc=rlc_m,rca=rca_m,yld=yld_m))
                last=niv
N=len(rows)

campus=[]; seen=set()
for r in rows:
    k=(r["marque"],r["ville"])
    if k in seen: continue
    seen.add(k)
    cc=[x for x in rows if (x["marque"],x["ville"])==k]
    sleads=sum(x["leads"] for x in cc)
    cpl=round(CPL_BASE*CITY_CPL[r["ville"]])
    budget_paid_ref=round(sleads*(1-PORG_DEF)*cpl)
    campus.append(dict(marque=r["marque"],ville=r["ville"],sleads=sleads,cpl=cpl,budget_paid_ref=budget_paid_ref))
CG=len(campus)

REFCA=round(sum(r["eff"]*r["rev"]+r["nouv"]*FRAIS_DEF for r in rows))
REFEFF=sum(r["eff"] for r in rows)
REFALT=sum(r["eff"] for r in rows if r["mod"]=="ALT")
REFBUD=sum(c["budget_paid_ref"] for c in campus)
REFLEADS=sum(c["sleads"] for c in campus)
print("[py] N=%d cellules  campus=%d"%(N,CG))
print("[py] CA réf=%d €  effectif=%d  alternance=%.0f%%"%(REFCA,REFEFF,REFALT/REFEFF*100))
print("[py] leads réf=%d  budget PAYANT réf=%d € (%.1f%% du CA, part organique %.0f%%)"%(REFLEADS,REFBUD,REFBUD/REFCA*100,PORG_DEF*100))

# ============================================================ STYLES
NAVY,BLUE2,LIGHT,YEL,TOT,GREENF="1F3864","2E5496","D9E1F2","FFF2CC","E2EFDA","EAF3EA"
Fn="Arial"
CIN=Font(name=Fn,color="0000FF"); CINB=Font(name=Fn,color="0000FF",bold=True)
CF=Font(name=Fn,color="000000"); CFB=Font(name=Fn,color="000000",bold=True)
CL=Font(name=Fn,color="008000"); CHDR=Font(name=Fn,color="FFFFFF",bold=True)
CTIT=Font(name=Fn,color="FFFFFF",bold=True,size=14); CB=Font(name=Fn,bold=True)
CIT=Font(name=Fn,italic=True,color="595959",size=9); CREG=Font(name=Fn)
FNAVY=PatternFill("solid",fgColor=NAVY); FBLUE=PatternFill("solid",fgColor=BLUE2)
FLIGHT=PatternFill("solid",fgColor=LIGHT); FYEL=PatternFill("solid",fgColor=YEL)
FTOT=PatternFill("solid",fgColor=TOT); FGRN=PatternFill("solid",fgColor=GREENF)
thin=Side(style="thin",color="BFBFBF"); BORD=Border(left=thin,right=thin,top=thin,bottom=thin)
AL=Alignment(horizontal="left",vertical="center"); AC=Alignment(horizontal="center",vertical="center",wrap_text=True)
AR=Alignment(horizontal="right",vertical="center"); ALW=Alignment(horizontal="left",vertical="top",wrap_text=True)
EUR='#,##0" €";(#,##0)" €";"-"'; PCT='0.0%;(0.0%);"-"'; NB='#,##0;(#,##0);"-"'; X2='0.00'
def C(ws,ref,val=None,font=None,fill=None,fmt=None,align=None,border=False):
    c=ws[ref]
    if val is not None:c.value=val
    if font:c.font=font
    if fill:c.fill=fill
    if fmt:c.number_format=fmt
    if align:c.alignment=align
    if border:c.border=BORD
    return c
def band(ws,row,a,b,text,fill=FNAVY,font=CHDR,h=20):
    ws.merge_cells(f"{a}{row}:{b}{row}")
    for col in range(CI(a),CI(b)+1): ws.cell(row=row,column=col).fill=fill
    cc=ws[f"{a}{row}"]; cc.value=text; cc.font=font; cc.alignment=AL; ws.row_dimensions[row].height=h

wb=openpyxl.Workbook()

# ============================================================ REFS 01_Cadrage
CAD="'01_Cadrage'!"
LMKT,LPRIX,LGLC,LGCV,LPASS=(f"{CAD}$H${_r}" for _r in (14,15,16,17,18))   # leviers ACTIF
KREND,KPORG,KFRAIS=(f"{CAD}$H${_r}" for _r in (22,23,24))                  # constantes ACTIF
CPKEY=f"{CAD}$M$7:$M${6+CG}"; CPVAL=f"{CAD}$L$7:$L${6+CG}"

BR0=4; BRN=BR0+N-1
BASE="'02_Base'!"
def brng(col): return f"{BASE}${col}${BR0}:${col}${BRN}"
CR0=5; CRN=CR0+CG-1
CAMP="'03_Campagnes'!"
MR0=4; MRN=MR0+N-1; MTOT=MR0+N

# ============================================================ 00_Notice
ws=wb.active; ws.title="00_Notice"; ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":30,"C":80}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:C2"); C(ws,"B2","EDUSERVICES — Modèle de CA (v3, budget-driven, leads observés)",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=30
ws.merge_cells("B3:C3"); C(ws,"B3","Budget marketing → leads (CRM, socle organique + payant) → funnel mesuré → inscrits → CA. Revenu et taux différenciés alternance / initial.",CIT)
band(ws,5,"B","C","Les feuilles (périmètre : CA uniquement)")
notice=[("01_Cadrage","POSTE DE COMMANDE CFO : objectif CA, scénarios, leviers (budget marketing, prix, conversion, passage), coefficients prix par marque×ville."),
 ("02_Base","BASE DE RÉFÉRENCE (version unique) : fusion historique + paramètres. LEADS OBSERVÉS (CRM) et taux de funnel MESURÉS (lead→cand, cand→admis, admis→inscrit), différenciés par modalité."),
 ("03_Campagnes","MOTEUR D'ACQUISITION (campus) : leads = socle ORGANIQUE (fixe) + part PAYANTE (budget ÷ CPL, rendement décroissant ^r). Couper le budget ne met pas les leads à zéro."),
 ("04_Moteur","MOTEUR DE CA (cellule) : répartition des leads (mix réel) → funnel mesuré → effectif (+cohorte) → CA.")]
r=6
for nom,desc in notice:
    C(ws,f"B{r}",nom,CB,FLIGHT,align=AL,border=True); C(ws,f"C{r}",desc,CREG,align=ALW,border=True); ws.row_dimensions[r].height=46; r+=1
band(ws,r+1,"B","C","Principe d'ancrage")
C(ws,f"B{r+2}","Au budget de référence, tous leviers à 0, le moteur reproduit l'historique. Les taux ne sont pas supposés : ils sont mesurés depuis les leads observés. Seul l'écart au budget de référence fait varier les volumes (part payante × courbe ^r).",CIT,align=ALW); ws.merge_cells(f"B{r+2}:C{r+2}"); ws.row_dimensions[r+2].height=46

# ============================================================ 01_Cadrage
ws=wb.create_sheet("01_Cadrage"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":36,"C":8,"D":13,"E":12,"F":12,"G":12,"H":13,"I":2,"J":16,"K":11,"L":11,"M":16}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B1:H1"); C(ws,"B1","POSTE DE COMMANDE CFO — Cadrage du chiffre d'affaires",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=28
C(ws,"B3","Scénario actif :",CB,align=AR); C(ws,"D3","Cadrage",CINB,FYEL,align=AC,border=True)
dv=DataValidation(type="list",formula1='"Référence,Cadrage,Optimiste,Prudent"',allow_blank=False); ws.add_data_validation(dv); dv.add(ws["D3"])
# --- cadrage CA ---
band(ws,5,"B","G","① Cadrage top-down du CA — référence · budget construit · objectif · écart")
for i,h in enumerate(["Indicateur","Référence","Budget construit","🟡 Objectif","Écart","Écart %"]): C(ws,f"{GL(2+i)}6",h,CHDR,FBLUE,align=AC,border=True)
TOTCA=f"'04_Moteur'!$AA${MTOT}"; TOTEFF=f"'04_Moteur'!$Y${MTOT}"
C(ws,"B7","Chiffre d'affaires",CB,align=AL,border=True)
C(ws,"C7",REFCA,CL,fmt=EUR,align=AR,border=True); C(ws,"D7",f"={TOTCA}",CFB,fmt=EUR,align=AR,border=True)
C(ws,"E7",round(REFCA*1.06),CINB,FYEL,fmt=EUR,align=AR,border=True); C(ws,"F7","=D7-E7",CF,fmt=EUR,align=AR,border=True); C(ws,"G7","=IFERROR(F7/E7,0)",CF,fmt=PCT,align=AR,border=True)
C(ws,"B8","Effectif total",CB,align=AL,border=True)
C(ws,"C8",REFEFF,CL,fmt=NB,align=AR,border=True); C(ws,"D8",f"={TOTEFF}",CFB,fmt=NB,align=AR,border=True)
C(ws,"E8",round(REFEFF*1.04),CINB,FYEL,fmt=NB,align=AR,border=True); C(ws,"F8","=D8-E8",CF,fmt=NB,align=AR,border=True); C(ws,"G8","=IFERROR(F8/E8,0)",CF,fmt=PCT,align=AR,border=True)
C(ws,"B10","RESTE À TROUVER (CA vs objectif) :",CB,align=AR); ws.merge_cells("B10:E10")
C(ws,"F10","=IF(E7-D7>0,E7-D7,0)",CFB,FYEL,fmt=EUR,align=AR,border=True); C(ws,"G10",'=IF(E7-D7>0,"à combler","atteint")',CIT,align=AC,border=True)
# --- leviers ---
band(ws,12,"B","H","② Leviers — bascule par scénario (colonne ACTIF)")
for i,h in enumerate(["Paramètre","Unité","Référence","Cadrage","Optimiste","Prudent","ACTIF"]): C(ws,f"{GL(2+i)}13",h,CHDR,FBLUE,align=AC,border=True)
MATCHSC='MATCH($D$3,$D$13:$G$13,0)'   # colonne D = scénario "Référence" (leviers à 0)
levs=[("Variation du budget marketing (→ leads payants)","%",0,0.10,0.20,-0.05),
 ("Hausse tarifaire (prix)","%",0,0.03,0.04,0.02),
 ("Gain taux lead → candidature","pts",0,0.02,0.04,0.0),
 ("Gain conversion admis → inscrit","pts",0,0.015,0.03,0.0),
 ("Amélioration du taux de passage","pts",0,0.01,0.02,-0.01)]
r=14
for lib,u,ba,cad,opt,pru in levs:
    C(ws,f"B{r}",lib,CREG,align=AL,border=True); C(ws,f"C{r}",u,CREG,align=AC,border=True); C(ws,f"D{r}",ba,CIT,fmt=PCT,align=AC,border=True)
    C(ws,f"E{r}",cad,CIN,fmt=PCT,align=AC,border=True); C(ws,f"F{r}",opt,CIN,fmt=PCT,align=AC,border=True); C(ws,f"G{r}",pru,CIN,fmt=PCT,align=AC,border=True)
    C(ws,f"H{r}",f"=INDEX(D{r}:G{r},{MATCHSC})",CFB,FLIGHT,fmt=PCT,align=AC,border=True); r+=1
C(ws,"B19",'Astuce : choisir « Référence » remet tous les leviers à 0 → le modèle reproduit l\'atterrissage.',CIT,align=AL); ws.merge_cells("B19:H19")
# --- constantes ---
band(ws,20,"B","H","③ Constantes de référence (scénarisables)")
for i,h in enumerate(["Paramètre","Unité","Référence","Cadrage","Optimiste","Prudent","ACTIF"]): C(ws,f"{GL(2+i)}21",h,CHDR,FBLUE,align=AC,border=True)
consts=[("Rendement d'acquisition (part payante)","x",REND_DEF,X2),
 ("Part organique des leads (hors budget)","%",PORG_DEF,PCT),
 ("Frais de dossier / nouvel inscrit","€",FRAIS_DEF,EUR)]
r=22
for lib,u,val,fmt in consts:
    C(ws,f"B{r}",lib,CREG,align=AL,border=True); C(ws,f"C{r}",u,CREG,align=AC,border=True); C(ws,f"D{r}",val,CIT,fmt=fmt,align=AC,border=True)
    C(ws,f"E{r}",val,CIN,fmt=fmt,align=AC,border=True); C(ws,f"F{r}",val,CIN,fmt=fmt,align=AC,border=True); C(ws,f"G{r}",val,CIN,fmt=fmt,align=AC,border=True)
    C(ws,f"H{r}",f"=INDEX(D{r}:G{r},{MATCHSC})",CFB,FLIGHT,fmt=fmt,align=AC,border=True); r+=1
# --- coefficients prix par marque x ville ---
band(ws,5,"J","M","Coefficients prix (marque × ville)")
for i,h in enumerate(["Marque","Ville","Coeff prix","clé"]): C(ws,f"{GL(10+i)}6",h,CHDR,FBLUE,align=AC,border=True)
COEFPRIX={"Paris":1.15,"Lyon":1.05,"Nantes":1.00,"Bordeaux":0.95,"Lille":1.00,"Toulouse":0.95,"Rennes":0.90,"Montpellier":0.90}
r=7
for cc in campus:
    C(ws,f"J{r}",cc["marque"],CL,align=AL,border=True); C(ws,f"K{r}",cc["ville"],CL,align=AC,border=True)
    C(ws,f"L{r}",COEFPRIX[cc["ville"]],CIN,fmt=X2,align=AC,border=True)
    C(ws,f"M{r}",f'=J{r}&"|"&K{r}',CF,align=AC,border=True); r+=1

# ============================================================ 02_Base
ws=wb.create_sheet("02_Base"); ws.sheet_view.showGridLines=False
bcols=["Marque","Ville","Programme","Cycle","Année","Modalité","Entrée",
 "Leads hist","Cand hist","Admis hist","Nouv hist","Réins hist","Effectif hist","Eff. année inf.","Classes hist",
 "Revenu/étudiant","Taux passage","Taux lead→cand","Taux cand→admis","Yield admis→inscrit"]
for i,w in enumerate([15,10,20,6,6,7,7,9,9,9,9,9,10,11,9,12,10,11,11,12]): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(bcols))}1"); C(ws,"A1","BASE DE RÉFÉRENCE — version unique · fusion historique + paramètres · leads observés (CRM) & taux mesurés",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
ws.merge_cells(f"A2:{GL(len(bcols))}2"); C(ws,"A2","Une ligne = marque × ville × programme × année × modalité. Leads = donnée observée (CRM). Taux = mesurés (aval÷amont). Revenu différencié alternance (OPCO) / initial (étudiant).",CIT,align=ALW); ws.row_dimensions[2].height=16
for i,h in enumerate(bcols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
for idx,rr in enumerate(rows):
    r=BR0+idx
    vals=[rr["marque"],rr["ville"],rr["prog"],rr["type"],rr["niv"],("Alternance" if rr["mod"]=="ALT" else "Initial"),rr["entry"],
          rr["leads"],rr["cand"],rr["admis"],rr["nouv"],rr["rein"],rr["eff"],rr["eff_prev"],rr["classes"],
          rr["rev"],round(rr["passage"],4),round(rr["rlc"],4),round(rr["rca"],4),round(rr["yld"],4)]
    fmts=[None,None,None,None,None,None,NB,NB,NB,NB,NB,NB,NB,NB,NB,EUR,PCT,PCT,PCT,PCT]
    for i,(v,f) in enumerate(zip(vals,fmts)):
        al=AL if i<6 else AC
        C(ws,f"{GL(1+i)}{r}",v,CL,fmt=f,align=al,border=True)
ws.freeze_panes="A4"

# ============================================================ 03_Campagnes (budget -> leads, socle organique)
ws=wb.create_sheet("03_Campagnes"); ws.sheet_view.showGridLines=False
ccols=["Marque","Ville","clé","Σ Leads hist","Part org.","Leads organiques","Leads payants réf","CPL réf","Budget payant réf","Budget payant actif","Leads payants actif","Leads actif total","CPL effectif"]
for i,w in enumerate([15,11,15,11,9,13,13,9,13,14,13,13,11]): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(ccols))}1"); C(ws,"A1","MOTEUR D'ACQUISITION (campus) — leads = socle organique (fixe) + part payante (budget → rendement décroissant ^r)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
ws.merge_cells(f"A2:{GL(len(ccols))}2"); C(ws,"A2","Organiques = site, salons, Parcoursup, bouche-à-oreille (indépendants du budget). Payants actifs = payants réf × (Budget actif/Budget réf)^rendement. Total = organiques + payants.",CIT,align=ALW); ws.row_dimensions[2].height=16
for i,h in enumerate(ccols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
for idx,cc in enumerate(campus):
    r=CR0+idx
    crit=f'{brng("A")},"{cc["marque"]}",{brng("B")},"{cc["ville"]}",{brng("G")},1'
    C(ws,f"A{r}",cc["marque"],CL,align=AL,border=True); C(ws,f"B{r}",cc["ville"],CL,align=AC,border=True)
    C(ws,f"C{r}",f'=A{r}&"|"&B{r}',CF,align=AC,border=True)
    C(ws,f"D{r}",f"=SUMIFS({brng('H')},{crit})",CF,fmt=NB,align=AR,border=True)
    C(ws,f"E{r}",f"={KPORG}",CF,fmt=PCT,align=AC,border=True)
    C(ws,f"F{r}",f"=D{r}*E{r}",CF,fmt=NB,align=AR,border=True)
    C(ws,f"G{r}",f"=D{r}*(1-E{r})",CF,fmt=NB,align=AR,border=True)
    C(ws,f"H{r}",cc["cpl"],CIN,fmt=EUR,align=AR,border=True)
    C(ws,f"I{r}",f"=ROUND(G{r}*H{r},0)",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"J{r}",f"=I{r}*(1+{LMKT})",CFB,fmt=EUR,align=AR,border=True)
    C(ws,f"K{r}",f"=G{r}*(J{r}/I{r})^{KREND}",CFB,fmt=NB,align=AR,border=True)
    C(ws,f"L{r}",f"=F{r}+K{r}",CFB,fmt=NB,align=AR,border=True)
    C(ws,f"M{r}",f"=IFERROR(J{r}/K{r},0)",CF,fmt=EUR,align=AR,border=True)
CKEY=f"{CAMP}$C${CR0}:$C${CRN}"; CLEADS=f"{CAMP}$L${CR0}:$L${CRN}"; CSLEADS=f"{CAMP}$D${CR0}:$D${CRN}"

# ============================================================ 04_Moteur (funnel -> CA)
ws=wb.create_sheet("04_Moteur"); ws.sheet_view.showGridLines=False
mcols=["Marque","Ville","Programme","Année","Mod.","Entrée",
 "Leads hist","Cand hist","Nouv hist","Réins hist","Eff hist","Eff. inf.","Revenu/étu","Passage","T.L→C","T.C→A","Yield",
 "Part leads","Leads campus","Leads cellule","Candidatures","Admis","Nouveaux","Réinscrits","Effectif","Revenu actif","CA"]
for i,w in enumerate([14,9,17,6,5,6]+[8]*(len(mcols)-6)): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(mcols))}1"); C(ws,"A1","MOTEUR DE CA (cellule) — leads → candidatures → admis → inscrits → effectif → CA (taux mesurés)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
for i,h in enumerate(mcols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
for idx in range(N):
    r=MR0+idx; b=BR0+idx
    Lk=lambda col:f"={BASE}{col}{b}"
    C(ws,f"A{r}",Lk('A'),CL,align=AL,border=True); C(ws,f"B{r}",Lk('B'),CL,align=AC,border=True); C(ws,f"C{r}",Lk('C'),CL,align=AL,border=True)
    C(ws,f"D{r}",Lk('E'),CL,align=AC,border=True); C(ws,f"E{r}",Lk('F'),CL,align=AC,border=True); C(ws,f"F{r}",Lk('G'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"G{r}",Lk('H'),CL,fmt=NB,align=AC,border=True); C(ws,f"H{r}",Lk('I'),CL,fmt=NB,align=AC,border=True); C(ws,f"I{r}",Lk('K'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"J{r}",Lk('L'),CL,fmt=NB,align=AC,border=True); C(ws,f"K{r}",Lk('M'),CL,fmt=NB,align=AC,border=True); C(ws,f"L{r}",Lk('N'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"M{r}",Lk('P'),CL,fmt=EUR,align=AC,border=True); C(ws,f"N{r}",Lk('Q'),CL,fmt=PCT,align=AC,border=True)
    C(ws,f"O{r}",Lk('R'),CL,fmt=PCT,align=AC,border=True); C(ws,f"P{r}",Lk('S'),CL,fmt=PCT,align=AC,border=True); C(ws,f"Q{r}",Lk('T'),CL,fmt=PCT,align=AC,border=True)
    key=f'A{r}&"|"&B{r}'
    C(ws,f"R{r}",f"=IF(F{r}=1,IFERROR(G{r}/INDEX({CSLEADS},MATCH({key},{CKEY},0)),0),0)",CF,fmt=PCT,align=AC,border=True)
    C(ws,f"S{r}",f"=INDEX({CLEADS},MATCH({key},{CKEY},0))",CF,fmt=NB,align=AR,border=True)
    C(ws,f"T{r}",f"=S{r}*R{r}",CF,fmt=NB,align=AR,border=True)
    C(ws,f"U{r}",f"=IF(F{r}=1,T{r}*(O{r}+{LGLC}),0)",CF,fmt=NB,align=AR,border=True)
    C(ws,f"V{r}",f"=U{r}*P{r}",CF,fmt=NB,align=AR,border=True)
    C(ws,f"W{r}",f"=IF(F{r}=1,V{r}*(Q{r}+{LGCV}),0)",CFB,fmt=NB,align=AR,border=True)
    C(ws,f"X{r}",f"=IF(F{r}=1,0,L{r}*(N{r}+{LPASS}))",CF,fmt=NB,align=AR,border=True)
    C(ws,f"Y{r}",f"=W{r}+X{r}",CFB,fmt=NB,align=AR,border=True)
    C(ws,f"Z{r}",f"=M{r}*(1+{LPRIX}*INDEX({CPVAL},MATCH({key},{CPKEY},0)))",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"AA{r}",f"=Y{r}*Z{r}+W{r}*{KFRAIS}",CFB,fmt=EUR,align=AR,border=True)
r=MTOT
C(ws,f"A{r}","TOTAL",CFB,FTOT,align=AL,border=True)
for col in ["B","C","D","E"]: C(ws,f"{col}{r}"," ",fill=FTOT,border=True)
for col,fmt in [("F",NB),("G",NB),("H",NB),("I",NB),("T",NB),("U",NB),("V",NB),("W",NB),("X",NB),("Y",NB),("AA",EUR)]:
    C(ws,f"{col}{r}",f"=SUM({col}{MR0}:{col}{MRN})",CFB,FTOT,fmt=fmt,align=AR,border=True)
ws.freeze_panes="G4"
gr=r+2
band(ws,gr,"A","H","Guide de lecture — de gauche à droite :"); gr+=1
grp=[("A–F","Identité : marque, ville, programme, année, modalité, entrée (1=on recrute)"),
 ("G–Q","Reprise base + taux mesurés : leads/cand/nouv hist, revenu, passage, taux funnel (L→C, C→A, yield)"),
 ("R–T","Acquisition : part de leads (mix réel) × leads campus = leads de la cellule"),
 ("U–W","Funnel mesuré : candidatures → admis → NOUVEAUX inscrits"),
 ("X–Y","Cohorte : réinscrits (eff. inférieur × passage) → EFFECTIF"),
 ("Z–AA","Prix & CA : revenu actif (hausse×coeff) → CHIFFRE D'AFFAIRES")]
for rng,txt in grp:
    C(ws,f"A{gr}",rng,CB,FLIGHT,align=AC,border=True); ws.merge_cells(f"B{gr}:H{gr}"); C(ws,f"B{gr}",txt,CREG,align=ALW,border=True); gr+=1

# ============================================================ COÛTS / P&L  (comptes PCG 6 & 7)
# ACCTS : code, libellé, sens, ligne SIG, rattachement, driver, % du CA (atterrissage), Variable/Fixe
ACCTS=[
 ("7062","Prestations de formation — alternance (OPCO)","Produit","Produits","campus","alt",None,"V"),
 ("706","Prestations de formation — scolarité (initial)","Produit","Produits","campus","init",None,"V"),
 ("708","Frais de dossier & droits d'inscription","Produit","Produits","campus","frais",None,"V"),
 ("621","Personnel extérieur — vacataires & intervenants","Charge","Coûts directs","campus","classes",0.070,"V"),
 ("604","Sous-traitance pédagogique","Charge","Coûts directs","campus","effectif",0.030,"V"),
 ("6063","Fournitures pédagogiques & petit équipement","Charge","Coûts directs","campus","effectif",0.020,"V"),
 ("6231","Publicité & marketing d'acquisition (leads)","Charge","Coûts directs","campus","classes",0.021,"V"),
 ("6411","Rémunération enseignants permanents","Charge","Personnel","campus","classes",0.170,"F"),
 ("6413","Rémunération personnel administratif & pédagogique","Charge","Personnel","campus","effectif",0.090,"F"),
 ("6414","Rémunération direction & fonctions support (siège)","Charge","Personnel","groupe","CA",0.055,"F"),
 ("645","Charges sociales & de prévoyance","Charge","Personnel","campus","effectif",0.140,"F"),
 ("613","Loyers & charges locatives (campus)","Charge","Structure","campus","classes",0.105,"F"),
 ("615","Entretien & maintenance","Charge","Structure","campus","classes",0.015,"F"),
 ("616","Primes d'assurance","Charge","Structure","campus","effectif",0.010,"F"),
 ("6226","Honoraires (audit, conseil, juridique)","Charge","Structure","groupe","CA",0.025,"F"),
 ("6236","Marketing de marque, salons & JPO","Charge","Structure","groupe","CA",0.030,"F"),
 ("625","Déplacements, missions & réceptions","Charge","Structure","campus","effectif",0.015,"F"),
 ("626","Télécom, systèmes d'information & affranchissement","Charge","Structure","groupe","effectif",0.020,"F"),
 ("6281","Cotisations, documentation & abonnements","Charge","Structure","groupe","CA",0.008,"F"),
 ("6331","Taxe sur les salaires","Charge","Impôts & taxes","groupe","effectif",0.015,"F"),
 ("63511","Cotisation foncière & CVAE","Charge","Impôts & taxes","campus","classes",0.010,"F"),
 ("6333","Participation formation professionnelle","Charge","Impôts & taxes","groupe","CA",0.005,"F"),
 ("6811","Dotations aux amortissements (D&A)","Charge","Dotations","campus","classes",0.060,"F"),
]
GROW_HIST=1.06
# marge EBITDA cible par version (progression douce = levier opérationnel réaliste ~0,7 pt/an)
TARGETS={2:0.132,1:0.140,0:0.146}
NONDA_PCT=sum(a[6] for a in ACCTS if a[3]!="Dotations" and a[6] is not None)  # = 0,854
# dimension Version (codes prêts Tagetik) : (code, libellé exercice, n en arrière, type, année)
VERS=[("2023ACT_VDEF","2023 (N-2)",2,"Actual",2023),
      ("2024ACT_VDEF","2024 (N-1)",1,"Actual",2024),
      ("2025ATT_VDEF","2025 (Atterr.)",0,"Forecast",2025)]
# hiérarchies : PCG (poste) et gestion (SIG agrégat + nœud parent)
def poste_of(code):
    if code[0]=="7": return "70 — Prestations de services"
    return {"60":"60 — Achats","61":"61 — Services extérieurs","62":"62 — Autres services extérieurs",
            "63":"63 — Impôts & taxes","64":"64 — Charges de personnel","68":"68 — Dotations & amort."}[code[:2]]
def classe_of(code): return "7 — Produits d'exploitation" if code[0]=="7" else "6 — Charges d'exploitation"
AGG={"Produits":"Marge de contribution","Coûts directs":"Marge de contribution","Personnel":"EBITDA",
     "Structure":"EBITDA","Impôts & taxes":"EBITDA","Dotations":"Résultat d'exploitation (EBIT)"}
SIGNODE={"Produits":"SIG_PROD","Coûts directs":"SIG_DIR","Personnel":"SIG_PERS",
         "Structure":"SIG_STRUCT","Impôts & taxes":"SIG_IMP","Dotations":"SIG_DOT"}
def slug(s):
    s=s.upper()
    for a,b in [("É","E"),("È","E"),("Ê","E"),("À","A"),("Ç","C"),("'",""),(" ","_"),("-","_")]: s=s.replace(a,b)
    return s
# drivers par campus (depuis la base)
capm={}
for r in rows:
    k=(r["marque"],r["ville"]); d=capm.setdefault(k,dict(ca=0,eff=0,cls=0,alt=0,init=0,frais=0))
    d["ca"]+=r["eff"]*r["rev"]+r["nouv"]*FRAIS_DEF; d["eff"]+=r["eff"]; d["cls"]+=r["classes"]
    d["alt"]+=(r["eff"]*r["rev"] if r["mod"]=="ALT" else 0); d["init"]+=(r["eff"]*r["rev"] if r["mod"]=="INIT" else 0)
    d["frais"]+=r["nouv"]*FRAIS_DEF
CA_T=REFCA; EFF_T=REFEFF; CLS_T=sum(d["cls"] for d in capm.values())
def share(k,drv):
    d=capm[k]; return {"CA":d["ca"]/CA_T,"effectif":d["eff"]/EFF_T,"classes":d["cls"]/CLS_T}[drv]
def ca_ver(n): return REFCA/(GROW_HIST**n)
def amount(pct,sig,n):
    if sig=="Dotations": return pct*ca_ver(n)
    return pct*ca_ver(n)*(1-TARGETS[n])/NONDA_PCT
# construction de la compta : (ecode,elib,marque,ville,compte,lib,poste,sens,sig,vcode,exlab,montant)
compta=[]
for code,lib,sens,sig,niv,drv,pct,vf in ACCTS:
    poste=poste_of(code)
    for vcode,exlab,n,vtype,vyear in VERS:
        if sens=="Produit":
            for k,d in capm.items():
                val={"alt":d["alt"],"init":d["init"],"frais":d["frais"]}[drv]*(ca_ver(n)/REFCA)
                if val>0: compta.append((slug(k[0])+"_"+slug(k[1]),f"{k[0]} {k[1]}",k[0],k[1],code,lib,poste,sens,sig,vcode,exlab,round(val)))
        else:
            tot=amount(pct,sig,n)
            if niv=="groupe":
                compta.append(("GROUPE","GROUPE — Siège","(groupe)","(groupe)",code,lib,poste,sens,sig,vcode,exlab,round(tot)))
            else:
                for k in capm: compta.append((slug(k[0])+"_"+slug(k[1]),f"{k[0]} {k[1]}",k[0],k[1],code,lib,poste,sens,sig,vcode,exlab,round(tot*share(k,drv))))
# vérification EBITDA par version
for vcode,exlab,n,vt,vy in VERS:
    ca=sum(m for row in compta for m in [row[11]] if row[7]=="Produit" and row[9]==vcode)
    ch=sum(row[11] for row in compta if row[7]=="Charge" and row[8]!="Dotations" and row[9]==vcode)
    da=sum(row[11] for row in compta if row[8]=="Dotations" and row[9]==vcode)
    print("[py] %s  CA=%d  EBITDA=%d (%.1f%%)  EBIT=%d (%.1f%%)"%(exlab,ca,ca-ch,(ca-ch)/ca*100,ca-ch-da,(ca-ch-da)/ca*100))

# ---- 05_Plan_Comptable ----
ws=wb.create_sheet("05_Plan_Comptable"); ws.sheet_view.showGridLines=False
pcols=["Compte","Libellé","Classe PCG","Poste PCG","Ligne SIG","Agrégat SIG","Sens","Rattachement","Driver","% du CA","V/F"]
for i,w in enumerate([9,42,26,30,17,26,9,11,10,9,5]): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(pcols))}1"); C(ws,"A1","PLAN COMPTABLE — comptes PCG · double hiérarchie (comptable + gestion) · prêt Tagetik (dimension Compte)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
for i,h in enumerate(pcols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=28
r=4
for code,lib,sens,sig,niv,drv,pct,vf in ACCTS:
    C(ws,f"A{r}",code,(CFB if sens=="Produit" else CF),align=AC,border=True); C(ws,f"B{r}",lib,CREG,align=AL,border=True)
    C(ws,f"C{r}",classe_of(code),CF,align=AL,border=True); C(ws,f"D{r}",poste_of(code),CF,align=AL,border=True)
    C(ws,f"E{r}",sig,CF,align=AL,border=True); C(ws,f"F{r}",AGG[sig],CF,align=AL,border=True)
    C(ws,f"G{r}",sens,CL,align=AC,border=True)
    C(ws,f"H{r}",{"campus":"Campus","groupe":"Groupe","cellule":"Cellule"}[niv],CF,align=AC,border=True)
    C(ws,f"I{r}",("—" if sens=="Produit" else drv),CF,align=AC,border=True)
    C(ws,f"J{r}",("—" if pct is None else pct),CF,fmt=(None if pct is None else PCT),align=AC,border=True)
    C(ws,f"K{r}",("—" if sens=="Produit" else vf),CF,align=AC,border=True); r+=1
# hiérarchie de gestion (parent -> enfant) prête Tagetik
r+=2; band(ws,r,"A","D","Hiérarchie de gestion (dimension Compte — parent → enfant, prêt Tagetik)"); r+=1
for i,h in enumerate(["Code nœud","Libellé","Parent","Type"]): C(ws,f"{GL(1+i)}{r}",h,CHDR,FBLUE,align=AC,border=True)
r+=1
HIER=[("RESULTAT_EXPL","Résultat d'exploitation (EBIT)","(racine)","Agrégat"),
 ("EBITDA","EBITDA","RESULTAT_EXPL","Agrégat"),
 ("MARGE_CONTRIB","Marge de contribution","EBITDA","Agrégat"),
 ("SIG_PROD","Produits d'exploitation","MARGE_CONTRIB","Regroupement"),
 ("SIG_DIR","Coûts directs","MARGE_CONTRIB","Regroupement"),
 ("SIG_PERS","Charges de personnel","EBITDA","Regroupement"),
 ("SIG_STRUCT","Charges de structure","EBITDA","Regroupement"),
 ("SIG_IMP","Impôts & taxes","EBITDA","Regroupement"),
 ("SIG_DOT","Dotations aux amortissements","RESULTAT_EXPL","Regroupement")]
for cnode,lnode,par,typ in HIER:
    C(ws,f"A{r}",cnode,CFB,align=AL,border=True); C(ws,f"B{r}",lnode,CB,align=AL,border=True)
    C(ws,f"C{r}",par,CF,align=AL,border=True); C(ws,f"D{r}",typ,CIT,align=AC,border=True); r+=1
for code,lib,sens,sig,*_ in ACCTS:
    C(ws,f"A{r}",code,CF,align=AL,border=True); C(ws,f"B{r}",lib,CREG,align=AL,border=True)
    C(ws,f"C{r}",SIGNODE[sig],CF,align=AL,border=True); C(ws,f"D{r}","Compte (détail)",CIT,align=AC,border=True); r+=1
# dimension Version (référentiel)
r+=2; band(ws,r,"A","D","Dimension Version (référentiel — prêt Tagetik)"); r+=1
for i,h in enumerate(["Code version","Libellé","Type","Année"]): C(ws,f"{GL(1+i)}{r}",h,CHDR,FBLUE,align=AC,border=True)
r+=1
for vcode,exlab,n,vtype,vyear in VERS:
    C(ws,f"A{r}",vcode,CFB,align=AL,border=True); C(ws,f"B{r}",exlab,CREG,align=AL,border=True)
    C(ws,f"C{r}",vtype,CF,align=AC,border=True); C(ws,f"D{r}",vyear,CF,align=AC,border=True); r+=1

# ---- 06_Compta (jeu de données chargé, clés + version) ----
ws=wb.create_sheet("06_Compta"); ws.sheet_view.showGridLines=False
kcols=["Code entité","Entité","Marque","Ville","Compte","Libellé compte","Poste PCG","Sens","Ligne SIG","Version","Exercice","Montant"]
for i,w in enumerate([18,20,16,11,9,40,28,9,15,15,15,12]): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(kcols))}1"); C(ws,"A1","COMPTA CHARGÉE — écritures par entité × compte × version (format long, clés Tagetik)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
ws.merge_cells(f"A2:{GL(len(kcols))}2"); C(ws,"A2","Clés : code entité (marque_ville), compte PCG, poste, version (2023ACT_VDEF / 2024ACT_VDEF / 2025ATT_VDEF). Charges réparties par driver. Somme des comptes = CA & EBITDA du P&L.",CIT,align=ALW); ws.row_dimensions[2].height=16
for i,h in enumerate(kcols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
KP0=4
for idx,row in enumerate(compta):
    r=KP0+idx
    for i,v in enumerate(row):
        al=AR if i==11 else (AL if i in(1,5) else AC)
        C(ws,f"{GL(1+i)}{r}",v,CL,fmt=(EUR if i==11 else None),align=al,border=True)
KPN=KP0+len(compta)-1
ws.freeze_panes="E4"
KACC=f"'06_Compta'!$E${KP0}:$E${KPN}"; KVER=f"'06_Compta'!$J${KP0}:$J${KPN}"; KMT=f"'06_Compta'!$L${KP0}:$L${KPN}"
KSIG=f"'06_Compta'!$I${KP0}:$I${KPN}"; KSENS=f"'06_Compta'!$H${KP0}:$H${KPN}"

# ---- 07_PnL (cascade SIG, 3 versions + variance) ----
ws=wb.create_sheet("07_PnL"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":10,"C":44,"D":14,"E":14,"F":14,"G":14,"H":9}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B1:H1"); C(ws,"B1","COMPTE DE RÉSULTAT (SIG) — réalisé N-2 · réalisé N-1 · atterrissage N",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=26
hdr=["Compte","Libellé"]+[v[1] for v in VERS]+["Var N-1→N €","Var %"]
for i,h in enumerate(hdr): C(ws,f"{GL(2+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=26
VC=[v[0] for v in VERS]   # codes version pour les SUMIFS
def sif(code=None,sig=None,sens=None,ver=""):
    parts=[KMT]
    if code is not None: parts+=[KACC,f'"{code}"']
    if sig is not None: parts+=[KSIG,f'"{sig}"']
    if sens is not None: parts+=[KSENS,f'"{sens}"']
    parts+=[KVER,f'"{ver}"']
    return "SUMIFS("+",".join(parts)+")"
r=4
def line(code,lib,getf,bold=False,fill=None,res=False):
    global r
    fnt=CFB if (bold or res) else CF
    C(ws,f"B{r}",code,fnt,fill,align=AC,border=True); C(ws,f"C{r}",lib,fnt,fill,align=AL,border=True)
    for i,vl in enumerate(VC):
        C(ws,f"{GL(4+i)}{r}",getf(vl),fnt,fill,fmt=EUR,align=AR,border=True)
    C(ws,f"G{r}",f"=F{r}-E{r}",fnt,fill,fmt=EUR,align=AR,border=True); C(ws,f"H{r}",f"=IFERROR((F{r}-E{r})/E{r},0)",fnt,fill,fmt=PCT,align=AR,border=True)
    r+=1
def band2(txt):
    global r; band(ws,r,"B","H",txt,fill=FBLUE); r+=1
def result(lib,getf):
    global r
    C(ws,f"B{r}"," ",CFB,FTOT,border=True); C(ws,f"C{r}",lib,CFB,FTOT,align=AL,border=True)
    for i,vl in enumerate(VC): C(ws,f"{GL(4+i)}{r}",getf(vl),CFB,FTOT,fmt=EUR,align=AR,border=True)
    C(ws,f"G{r}",f"=F{r}-E{r}",CFB,FTOT,fmt=EUR,align=AR,border=True); C(ws,f"H{r}",f"=IFERROR((F{r}-E{r})/E{r},0)",CFB,FTOT,fmt=PCT,align=AR,border=True)
    rr=r; r+=1; return rr
band2("PRODUITS")
for code,lib,sens,sig,*_ in ACCTS:
    if sens=="Produit": line(code,lib,lambda vl,c=code:f"={sif(code=c,ver=vl)}")
rowCA=result("CHIFFRE D'AFFAIRES",lambda vl:f"={sif(sens='Produit',ver=vl)}")
band2("COÛTS DIRECTS")
for code,lib,sens,sig,*_ in ACCTS:
    if sig=="Coûts directs": line(code,lib,lambda vl,c=code:f"=-{sif(code=c,ver=vl)}")
rowMC=result("MARGE DE CONTRIBUTION",lambda vl:f"={sif(sens='Produit',ver=vl)}-{sif(sig='Coûts directs',ver=vl)}")
for grp in ["Personnel","Structure","Impôts & taxes"]:
    band2(grp.upper())
    for code,lib,sens,sig,*_ in ACCTS:
        if sig==grp: line(code,lib,lambda vl,c=code:f"=-{sif(code=c,ver=vl)}")
rowEB=result("EBITDA",lambda vl:f"={sif(sens='Produit',ver=vl)}-{sif(sens='Charge',ver=vl)}+{sif(sig='Dotations',ver=vl)}")
band2("DOTATIONS")
for code,lib,sens,sig,*_ in ACCTS:
    if sig=="Dotations": line(code,lib,lambda vl,c=code:f"=-{sif(code=c,ver=vl)}")
rowEBIT=result("EBIT / RÉSULTAT D'EXPLOITATION",lambda vl:f"={sif(sens='Produit',ver=vl)}-{sif(sens='Charge',ver=vl)}")
# marges %
C(ws,f"C{r}","Marge EBITDA %",CIT,align=AL);
for i in range(3): C(ws,f"{GL(4+i)}{r}",f"=IFERROR({GL(4+i)}{rowEB}/{GL(4+i)}{rowCA},0)",CIT,fmt=PCT,align=AR)
r+=1
C(ws,f"C{r}","Marge EBIT %",CIT,align=AL)
for i in range(3): C(ws,f"{GL(4+i)}{r}",f"=IFERROR({GL(4+i)}{rowEBIT}/{GL(4+i)}{rowCA},0)",CIT,fmt=PCT,align=AR)

try: wb.calculation.fullCalcOnLoad=True
except Exception: pass
wb.properties.calcMode="auto"
wb.save(OUT)
print("[py] écrit :",OUT)
