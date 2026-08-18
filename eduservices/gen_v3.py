# -*- coding: utf-8 -*-
"""EDUSERVICES — Modèle CA v3 (Architecture BUDGET-DRIVEN).
Cadrage top-down -> Base de référence (fusion historique+paramètres, version unique)
-> Campagnes (budget marketing -> leads, courbe de rendement) -> Moteur (funnel -> effectif -> CA).
Revenu differencié par modalité (alternance/initial) x marque x ville.
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
#  ALT = pris en charge OPCO/entreprise ; INIT = payé par l'étudiant
REV={("BTS","ALT"):6000,("BTS","INIT"):5500,("BAC","ALT"):7000,("BAC","INIT"):7500,("MAST","ALT"):7500,("MAST","INIT"):9000}
PASS={"B2":0.93,"B3":0.95,"M2":0.96,"2":0.94}   # taux de passage (rétention cohorte)
R_LC,R_CA,R_YIELD=0.30,0.70,0.55                 # funnel : lead->cand, cand->admis, admis->inscrit (base)
REND_DEF=0.5                                      # rendement d'acquisition (courbe budget->leads)
CPL_BASE=40                                        # coût par lead de référence (€)
FRAIS_DEF=90                                       # frais de dossier / nouvel inscrit (€)

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
                    nouv=eff; rein=0; eff_prev=0; passage=0.0
                    cand=max(1,round(nouv/(R_CA*R_YIELD)))
                    yld=nouv/(cand*R_CA)          # calibré pour reproduire nouveaux à la référence
                else:
                    nouv=0; rein=eff; cand=0; yld=0.0
                    eff_prev=effs[last]; passage=PASS[niv]
                classes=max(1,math.ceil(eff/CAPT[ptype])) if eff>0 else 0
                rows.append(dict(marque=marque,ville=ville,prog=pnom,type=ptype,niv=niv,mod=mod,entry=is_entry,
                    cand=cand,nouv=nouv,rein=rein,eff=eff,eff_prev=eff_prev,classes=classes,
                    rev=rev,passage=passage,yld=yld))
                last=niv
N=len(rows)

# campus (marque x ville)
campus=[]; seen=set()
for r in rows:
    k=(r["marque"],r["ville"])
    if k in seen: continue
    seen.add(k)
    cc=[x for x in rows if (x["marque"],x["ville"])==k]
    scand=sum(x["cand"] for x in cc)
    cpl=round(CPL_BASE*CITY_CPL[r["ville"]])
    leads_ref=scand/R_LC
    budget_ref=round(leads_ref*cpl)
    campus.append(dict(marque=r["marque"],ville=r["ville"],scand=scand,cpl=cpl,leads_ref=leads_ref,budget_ref=budget_ref))
CG=len(campus)

REFCA=round(sum(r["eff"]*r["rev"]+r["nouv"]*FRAIS_DEF for r in rows))
REFEFF=sum(r["eff"] for r in rows)
REFALT=sum(r["eff"] for r in rows if r["mod"]=="ALT")
REFBUD=sum(c["budget_ref"] for c in campus)
print("[py] N=%d cellules  campus=%d"%(N,CG))
print("[py] CA réf=%d €  effectif=%d  alternance=%.0f%%  budget mkt réf=%d € (%.1f%% du CA)"%(
    REFCA,REFEFF,REFALT/REFEFF*100,REFBUD,REFBUD/REFCA*100))

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
EUR='#,##0" €";(#,##0)" €";"-"'; PCT='0.0%;(0.0%);"-"'; NB='#,##0;(#,##0);"-"'; NB1='#,##0.0;(#,##0.0);"-"'; X2='0.00'
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
SCEN=f"{CAD}$D$3"
LMKT,LPRIX,LGLC,LGCV,LPASS=(f"{CAD}$H${_r}" for _r in (14,15,16,17,18))     # leviers ACTIF
KREND,KRLC,KRCA,KFRAIS=(f"{CAD}$H${_r}" for _r in (22,23,24,25))             # constantes ACTIF
CPKEY=f"{CAD}$M$6:$M${5+CG}"; CPVAL=f"{CAD}$L$6:$L${5+CG}"                    # coeff prix marque|ville

# base ranges
BR0=4; BRN=BR0+N-1
BASE="'02_Base'!"
def brng(col): return f"{BASE}${col}${BR0}:${col}${BRN}"
# campagnes
CR0=5; CRN=CR0+CG-1
CAMP="'03_Campagnes'!"
# moteur
MR0=4; MRN=MR0+N-1

# ============================================================ 00_Notice
ws=wb.active; ws.title="00_Notice"; ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":30,"C":78}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:C2"); C(ws,"B2","EDUSERVICES — Modèle de CA (v3, budget-driven)",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=30
ws.merge_cells("B3:C3"); C(ws,"B3","Du cadrage top-down au moteur : budget marketing → leads → candidatures → inscrits → CA. Revenu différencié alternance / initial.",CIT)
band(ws,5,"B","C","Les feuilles (périmètre actuel : CA uniquement)")
notice=[("01_Cadrage","POSTE DE COMMANDE CFO : objectif CA, scénarios, leviers (budget marketing, prix, conversion, passage), coefficients prix par marque×ville."),
 ("02_Base","BASE DE RÉFÉRENCE (version unique = dernier atterrissage) : fusion historique + paramètres, à la maille marque×ville×programme×année×modalité. Revenu/étudiant par modalité."),
 ("03_Campagnes","MOTEUR D'ACQUISITION (niveau campus) : budget marketing → leads via une courbe de rendement décroissant (^r). Sort le CPL effectif."),
 ("04_Moteur","MOTEUR DE CA (niveau cellule) : répartition des leads (mix) → funnel lead→candidature→admis→inscrit → effectif (+cohorte) → CA.")]
r=6
for nom,desc in notice:
    C(ws,f"B{r}",nom,CB,FLIGHT,align=AL,border=True); C(ws,f"C{r}",desc,CREG,align=ALW,border=True); ws.row_dimensions[r].height=42; r+=1
band(ws,r+1,"B","C","Principe d'ancrage")
C(ws,f"B{r+2}","Au budget de référence, tous leviers à 0, le moteur reproduit l'historique. Seul l'écart au budget de référence fait varier les volumes (courbe ^r). Modèle calé sur le réel, pas une boîte noire.",CIT,align=ALW); ws.merge_cells(f"B{r+2}:C{r+2}"); ws.row_dimensions[r+2].height=44

# ============================================================ 01_Cadrage
ws=wb.create_sheet("01_Cadrage"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":34,"C":8,"D":13,"E":12,"F":12,"G":12,"H":13,"I":2,"J":16,"K":11,"L":11,"M":16}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B1:H1"); C(ws,"B1","POSTE DE COMMANDE CFO — Cadrage du chiffre d'affaires",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=28
# scénario
C(ws,"B3","Scénario actif :",CB,align=AR); C(ws,"D3","Cadrage",CINB,FYEL,align=AC,border=True)
dv=DataValidation(type="list",formula1='"Cadrage,Optimiste,Prudent"',allow_blank=False); ws.add_data_validation(dv); dv.add(ws["D3"])
# --- cadrage CA ---
band(ws,5,"B","G","① Cadrage top-down du CA — référence · budget construit · objectif · écart")
for i,h in enumerate(["Indicateur","Référence","Budget construit","🟡 Objectif","Écart","Écart %"]): C(ws,f"{GL(2+i)}6",h,CHDR,FBLUE,align=AC,border=True)
MO_CA=f"{CAMP}"  # placeholder unused
TOTCA=f"'04_Moteur'!$X${MRN+1}"; TOTEFF=f"'04_Moteur'!$V${MRN+1}"
C(ws,"B7","Chiffre d'affaires",CB,align=AL,border=True)
C(ws,"C7",REFCA,CL,fmt=EUR,align=AR,border=True); C(ws,"D7",f"={TOTCA}",CFB,fmt=EUR,align=AR,border=True)
C(ws,"E7",round(REFCA*1.06),CINB,FYEL,fmt=EUR,align=AR,border=True); C(ws,"F7","=D7-E7",CF,fmt=EUR,align=AR,border=True); C(ws,"G7","=IFERROR(F7/E7,0)",CF,fmt=PCT,align=AR,border=True)
C(ws,"B8","Effectif total",CB,align=AL,border=True)
C(ws,"C8",REFEFF,CL,fmt=NB,align=AR,border=True); C(ws,"D8",f"={TOTEFF}",CFB,fmt=NB,align=AR,border=True)
C(ws,"E8",round(REFEFF*1.04),CINB,FYEL,fmt=NB,align=AR,border=True); C(ws,"F8","=D8-E8",CF,fmt=NB,align=AR,border=True); C(ws,"G8","=IFERROR(F8/E8,0)",CF,fmt=PCT,align=AR,border=True)
C(ws,"B10","RESTE À TROUVER (CA vs objectif) :",CB,align=AR); ws.merge_cells("B10:E10")
C(ws,"F10","=IF(E7-D7>0,E7-D7,0)",CFB,FYEL,fmt=EUR,align=AR,border=True); C(ws,"G10",'=IF(E7-D7>0,"à combler","atteint")',CIT,align=AC,border=True)
# --- leviers ---
band(ws,12,"B","H","② Leviers — varient en % · bascule par scénario (colonne ACTIF)")
for i,h in enumerate(["Paramètre","Unité","Base","Cadrage","Optimiste","Prudent","ACTIF"]): C(ws,f"{GL(2+i)}13",h,CHDR,FBLUE,align=AC,border=True)
MATCHSC='MATCH($D$3,$E$13:$G$13,0)'
levs=[("Variation du budget marketing (→ leads)","%",0,0.10,0.20,-0.05),
 ("Hausse tarifaire (prix)","%",0,0.03,0.04,0.02),
 ("Gain taux lead → candidature","pts",0,0.02,0.04,0.0),
 ("Gain conversion admis → inscrit","pts",0,0.015,0.03,0.0),
 ("Amélioration du taux de passage","pts",0,0.01,0.02,-0.01)]
r=14
for lib,u,ba,cad,opt,pru in levs:
    C(ws,f"B{r}",lib,CREG,align=AL,border=True); C(ws,f"C{r}",u,CREG,align=AC,border=True); C(ws,f"D{r}",ba,CIT,fmt=PCT,align=AC,border=True)
    C(ws,f"E{r}",cad,CIN,fmt=PCT,align=AC,border=True); C(ws,f"F{r}",opt,CIN,fmt=PCT,align=AC,border=True); C(ws,f"G{r}",pru,CIN,fmt=PCT,align=AC,border=True)
    C(ws,f"H{r}",f"=INDEX(E{r}:G{r},{MATCHSC})",CFB,FLIGHT,fmt=PCT,align=AC,border=True); r+=1
# --- constantes ---
band(ws,20,"B","H","③ Constantes de référence (scénarisables)")
for i,h in enumerate(["Paramètre","Unité","Base","Cadrage","Optimiste","Prudent","ACTIF"]): C(ws,f"{GL(2+i)}21",h,CHDR,FBLUE,align=AC,border=True)
consts=[("Rendement d'acquisition (courbe leads)","x",REND_DEF,X2),
 ("Taux lead → candidature (base)","%",R_LC,PCT),
 ("Taux candidature → admis (base)","%",R_CA,PCT),
 ("Frais de dossier / nouvel inscrit","€",FRAIS_DEF,EUR)]
r=22
for lib,u,val,fmt in consts:
    C(ws,f"B{r}",lib,CREG,align=AL,border=True); C(ws,f"C{r}",u,CREG,align=AC,border=True); C(ws,f"D{r}",val,CIT,fmt=fmt,align=AC,border=True)
    C(ws,f"E{r}",val,CIN,fmt=fmt,align=AC,border=True); C(ws,f"F{r}",val,CIN,fmt=fmt,align=AC,border=True); C(ws,f"G{r}",val,CIN,fmt=fmt,align=AC,border=True)
    C(ws,f"H{r}",f"=INDEX(E{r}:G{r},{MATCHSC})",CFB,FLIGHT,fmt=fmt,align=AC,border=True); r+=1
# --- coefficients prix par marque x ville ---
band(ws,5,"J","M","Coefficients prix (marque × ville)")
for i,h in enumerate(["Marque","Ville","Coeff prix","clé"]): C(ws,f"{GL(10+i)}6",h,CHDR,FBLUE,align=AC,border=True)
# ville price premium relatif normalisé ~1 ; on module la SENSIBILITÉ à la hausse (pas le niveau)
COEFPRIX={"Paris":1.15,"Lyon":1.05,"Nantes":1.00,"Bordeaux":0.95,"Lille":1.00,"Toulouse":0.95,"Rennes":0.90,"Montpellier":0.90}
r=7
for cc in campus:
    C(ws,f"J{r}",cc["marque"],CL,align=AL,border=True); C(ws,f"K{r}",cc["ville"],CL,align=AC,border=True)
    C(ws,f"L{r}",COEFPRIX[cc["ville"]],CIN,fmt=X2,align=AC,border=True)
    C(ws,f"M{r}",f'=J{r}&"|"&K{r}',CF,align=AC,border=True); r+=1
# la plage réelle coeff est J7:M{6+CG}; on corrige CPKEY/CPVAL
CPKEY=f"{CAD}$M$7:$M${6+CG}"; CPVAL=f"{CAD}$L$7:$L${6+CG}"

# ============================================================ 02_Base
ws=wb.create_sheet("02_Base"); ws.sheet_view.showGridLines=False
bcols=["Marque","Ville","Programme","Cycle","Année","Modalité","Entrée",
 "Cand hist","Nouv hist","Réins hist","Effectif hist","Eff. année inf.","Classes hist",
 "Revenu/étudiant","Taux passage","Yield (admis→inscrit)"]
for i,w in enumerate([15,10,20,6,6,7,7,9,9,9,10,11,9,12,10,12]): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(bcols))}1"); C(ws,"A1","BASE DE RÉFÉRENCE — version unique (dernier atterrissage) · fusion historique + paramètres",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
ws.merge_cells(f"A2:{GL(len(bcols))}2"); C(ws,"A2","Une ligne = marque × ville × programme × année × modalité. Le revenu/étudiant est différencié : alternance (OPCO/entreprise) vs initial (étudiant).",CIT,align=ALW); ws.row_dimensions[2].height=16
for i,h in enumerate(bcols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
for idx,rr in enumerate(rows):
    r=BR0+idx
    vals=[rr["marque"],rr["ville"],rr["prog"],rr["type"],rr["niv"],("Alternance" if rr["mod"]=="ALT" else "Initial"),rr["entry"],
          rr["cand"],rr["nouv"],rr["rein"],rr["eff"],rr["eff_prev"],rr["classes"],rr["rev"],rr["passage"],round(rr["yld"],4)]
    fmts=[None,None,None,None,None,None,NB,NB,NB,NB,NB,NB,NB,EUR,PCT,PCT]
    for i,(v,f) in enumerate(zip(vals,fmts)):
        al=AL if i<6 else AC
        C(ws,f"{GL(1+i)}{r}",v,CL,fmt=f,align=al,border=True)
ws.freeze_panes="A4"

# ============================================================ 03_Campagnes  (budget -> leads)
ws=wb.create_sheet("03_Campagnes"); ws.sheet_view.showGridLines=False
ccols=["Marque","Ville","clé","Σ Cand hist","Leads réf","CPL réf","Budget réf","Budget actif","Leads actif","CPL effectif"]
for i,w in enumerate([15,11,15,11,10,9,12,12,10,11]): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(ccols))}1"); C(ws,"A1","MOTEUR D'ACQUISITION (campus) — le budget marketing génère les leads (rendement décroissant ^r)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
ws.merge_cells(f"A2:{GL(len(ccols))}2"); C(ws,"A2","Leads réf = Σ candidatures ÷ taux(lead→cand). Budget actif = Budget réf × (1+levier). Leads actif = Leads réf × (Budget actif/Budget réf)^rendement.",CIT,align=ALW); ws.row_dimensions[2].height=16
for i,h in enumerate(ccols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=28
for idx,cc in enumerate(campus):
    r=CR0+idx
    crit=f'{brng("A")},"{cc["marque"]}",{brng("B")},"{cc["ville"]}",{brng("G")},1'
    C(ws,f"A{r}",cc["marque"],CL,align=AL,border=True); C(ws,f"B{r}",cc["ville"],CL,align=AC,border=True)
    C(ws,f"C{r}",f'=A{r}&"|"&B{r}',CF,align=AC,border=True)
    C(ws,f"D{r}",f"=SUMIFS({crit})",CF,fmt=NB,align=AR,border=True)
    C(ws,f"E{r}",f"=D{r}/{KRLC}",CF,fmt=NB,align=AR,border=True)
    C(ws,f"F{r}",cc["cpl"],CIN,fmt=EUR,align=AR,border=True)
    C(ws,f"G{r}",f"=ROUND(E{r}*F{r},0)",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"H{r}",f"=G{r}*(1+{LMKT})",CFB,fmt=EUR,align=AR,border=True)
    C(ws,f"I{r}",f"=E{r}*(H{r}/G{r})^{KREND}",CFB,fmt=NB,align=AR,border=True)
    C(ws,f"J{r}",f"=IFERROR(H{r}/I{r},0)",CF,fmt=EUR,align=AR,border=True)
# fix SUMIFS: first arg must be sum_range (Σcand) -> rebuild D with sum range = base cand col
for idx,cc in enumerate(campus):
    r=CR0+idx
    crit=f'{brng("A")},"{cc["marque"]}",{brng("B")},"{cc["ville"]}",{brng("G")},1'
    ws[f"D{r}"]=f"=SUMIFS({brng('H')},{crit})"
CKEY=f"{CAMP}$C${CR0}:$C${CRN}"; CLEADS=f"{CAMP}$I${CR0}:$I${CRN}"; CSCAND=f"{CAMP}$D${CR0}:$D${CRN}"

# ============================================================ 04_Moteur (funnel -> CA)
ws=wb.create_sheet("04_Moteur"); ws.sheet_view.showGridLines=False
mcols=["Marque","Ville","Programme","Année","Mod.","Entrée",
 "Cand hist","Nouv hist","Réins hist","Eff hist","Eff. inf.","Revenu/étu","Passage","Yield",
 "Part leads","Leads campus","Leads cellule","Candidatures","Admis","Nouveaux","Réinscrits","Effectif","Revenu actif","CA"]
for i,w in enumerate([14,9,18,6,5,6]+[9]*(len(mcols)-6)): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells(f"A1:{GL(len(mcols))}1"); C(ws,"A1","MOTEUR DE CA (cellule) — leads → candidatures → admis → inscrits → effectif → CA",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
for i,h in enumerate(mcols): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
for idx in range(N):
    r=MR0+idx; b=BR0+idx
    L=lambda col:f"={BASE}{col}{b}"
    C(ws,f"A{r}",L('A'),CL,align=AL,border=True); C(ws,f"B{r}",L('B'),CL,align=AC,border=True); C(ws,f"C{r}",L('C'),CL,align=AL,border=True)
    C(ws,f"D{r}",L('E'),CL,align=AC,border=True); C(ws,f"E{r}",L('F'),CL,align=AC,border=True); C(ws,f"F{r}",L('G'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"G{r}",L('H'),CL,fmt=NB,align=AC,border=True); C(ws,f"H{r}",L('I'),CL,fmt=NB,align=AC,border=True); C(ws,f"I{r}",L('J'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"J{r}",L('K'),CL,fmt=NB,align=AC,border=True); C(ws,f"K{r}",L('L'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"L{r}",L('N'),CL,fmt=EUR,align=AC,border=True); C(ws,f"M{r}",L('O'),CL,fmt=PCT,align=AC,border=True); C(ws,f"N{r}",L('P'),CL,fmt=PCT,align=AC,border=True)
    key=f'A{r}&"|"&B{r}'
    C(ws,f"O{r}",f"=IF(F{r}=1,IFERROR(G{r}/INDEX({CSCAND},MATCH({key},{CKEY},0)),0),0)",CF,fmt=PCT,align=AC,border=True)
    C(ws,f"P{r}",f"=INDEX({CLEADS},MATCH({key},{CKEY},0))",CF,fmt=NB,align=AR,border=True)
    C(ws,f"Q{r}",f"=P{r}*O{r}",CF,fmt=NB,align=AR,border=True)
    C(ws,f"R{r}",f"=IF(F{r}=1,Q{r}*({KRLC}+{LGLC}),0)",CF,fmt=NB,align=AR,border=True)
    C(ws,f"S{r}",f"=R{r}*{KRCA}",CF,fmt=NB,align=AR,border=True)
    C(ws,f"T{r}",f"=IF(F{r}=1,S{r}*(N{r}+{LGCV}),0)",CFB,fmt=NB,align=AR,border=True)
    C(ws,f"U{r}",f"=IF(F{r}=1,0,K{r}*(M{r}+{LPASS}))",CF,fmt=NB,align=AR,border=True)
    C(ws,f"V{r}",f"=T{r}+U{r}",CFB,fmt=NB,align=AR,border=True)
    C(ws,f"W{r}",f"=L{r}*(1+{LPRIX}*INDEX({CPVAL},MATCH({key},{CPKEY},0)))",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"X{r}",f"=V{r}*W{r}+T{r}*{KFRAIS}",CFB,fmt=EUR,align=AR,border=True)
# totals
r=MR0+N
C(ws,f"A{r}","TOTAL",CFB,FTOT,align=AL,border=True)
for col in ["B","C","D","E"]: C(ws,f"{col}{r}"," ",fill=FTOT,border=True)
for col,fmt in [("F",NB),("G",NB),("H",NB),("I",NB),("R",NB),("S",NB),("T",NB),("U",NB),("V",NB),("X",EUR)]:
    C(ws,f"{col}{r}",f"=SUM({col}{MR0}:{col}{MRN})",CFB,FTOT,fmt=fmt,align=AR,border=True)
ws.freeze_panes="G4"
# guide de lecture
gr=r+2
band(ws,gr,"A","H","Guide de lecture — de gauche à droite :"); gr+=1
grp=[("A–F","Identité : marque, ville, programme, année, modalité, entrée (1=on recrute)"),
 ("G–N","Reprise base + paramètres : historique, revenu/étudiant, passage, yield calibré"),
 ("O–Q","Acquisition : part de leads (mix) × leads campus = leads de la cellule"),
 ("R–T","Funnel : candidatures → admis → NOUVEAUX inscrits"),
 ("U–V","Cohorte : réinscrits (eff. inférieur × passage) → EFFECTIF"),
 ("W–X","Prix & CA : revenu actif (hausse×coeff) → CHIFFRE D'AFFAIRES")]
for rng,txt in grp:
    C(ws,f"A{gr}",rng,CB,FLIGHT,align=AC,border=True); ws.merge_cells(f"B{gr}:H{gr}"); C(ws,f"B{gr}",txt,CREG,align=ALW,border=True); gr+=1

# recalc à l'ouverture
try: wb.calculation.fullCalcOnLoad=True
except Exception: pass
wb.properties.calcMode="auto"
wb.save(OUT)
print("[py] écrit :",OUT)
