# -*- coding: utf-8 -*-
"""Modèle de pilotage EDUSERVICES v2 — cohortes, marketing mesuré sur l'historique,
params programme×année, seuil=point mort, cadrage top-down, simulateur de décisions, sensibilité."""
import math
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as GL, column_index_from_string as CI
exec(open("/home/user/demo5/eduservices/gen_v2_data.py").read().split('if __name__')[0])

OUT="/home/user/demo5/eduservices/EDUSERVICES_Modele_Pilotage_Budget.xlsx"
# ---------- styles ----------
NAVY,BLUE2,LIGHT,YEL,TOT,RISK="1F3864","2E5496","D9E1F2","FFF2CC","E2EFDA","FCE4E4"
F="Arial"
CIN=Font(name=F,color="0000FF"); CINB=Font(name=F,color="0000FF",bold=True)
CF=Font(name=F,color="000000"); CFB=Font(name=F,color="000000",bold=True)
CL=Font(name=F,color="008000"); CHDR=Font(name=F,color="FFFFFF",bold=True)
CTIT=Font(name=F,color="FFFFFF",bold=True,size=14); CB=Font(name=F,bold=True)
CIT=Font(name=F,italic=True,color="595959",size=9); CREG=Font(name=F)
FNAVY=PatternFill("solid",fgColor=NAVY); FBLUE=PatternFill("solid",fgColor=BLUE2)
FLIGHT=PatternFill("solid",fgColor=LIGHT); FYEL=PatternFill("solid",fgColor=YEL)
FTOT=PatternFill("solid",fgColor=TOT); FRISK=PatternFill("solid",fgColor=RISK)
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
    cc=ws[f"{a}{row}"]; cc.value=text; cc.font=font; cc.alignment=Alignment(horizontal="left",vertical="center"); ws.row_dimensions[row].height=h

wb=openpyxl.Workbook()

# distinct programmes list (nom -> type,domaine) preserving order
PROGN=[];
for (m,pnom,ptype,dom) in prog_list: PROGN.append((pnom,ptype,dom))
# param prog×année : liste unique (programme,niveau)
PPA=[]
seen=set()
for r in rows:
    k=(r["prog"],r["niv"])
    if k in seen: continue
    seen.add(k); PPA.append((r["prog"],r["type"],r["niv"],r["mod"],r["cap"],r["heures"],r["taux"],r["pedago"],r["cacv"],r["passage"],
                             next(d for (mm,pn,pt,d) in prog_list if pn==r["prog"])))
# campus aggregates (entité marque+ville)
campus=[]; seenc=set()
for r in rows:
    key=(r["marque"],r["ville"])
    if key in seenc: continue
    seenc.add(key); cells=[x for x in rows if (x["marque"],x["ville"])==key]
    eff=sum(x["eff"] for x in cells); nouv=sum(x["nouv"] for x in cells)
    ca=sum(x["eff"]*x["tarif"]*sf(x["mod"],SECU_N1)+x["nouv"]*FRAIS for x in cells)
    ens=sum(x["classes"]*x["heures"]*x["taux"] for x in cells)
    ped=sum(x["eff"]*x["pedago"] for x in cells)
    mkt=sum(x["nouv"]*x["cacv"] for x in cells)   # variable par programme uniquement (le global est fixe, en structure)
    autres=eff*AUTRES_ETU
    contrib=ca-ens-ped-mkt-autres
    loyer=round(0.11*ca/1000)*1000; etp=round(eff/28)+2; da=round(DA_PCT*ca/1000)*1000; m2=eff*8
    campus.append(dict(marque=r["marque"],ville=r["ville"],eff=eff,nouv=nouv,ca=ca,contrib=contrib,loyer=loyer,etp=etp,da=da,m2=m2))
CG=len(campus)
MARQUES=list(BRANDS.keys())
grp_ca_n1=sum(c["ca"] for c in campus)
grp_ebitda_n1=sum(c["contrib"] for c in campus)-sum(c["loyer"] for c in campus)-sum(c["etp"]*ETPC for c in campus)-STRUCT_FIXE
print("[py] CA N-1=%.0f EBITDA N-1=%.0f (%.1f%%)"%(grp_ca_n1,grp_ebitda_n1,grp_ebitda_n1/grp_ca_n1*100))

# ============================================================ refs paramètres
P=lambda a:f"'02_Leviers'!{a}"
PMKT,PPRIX,PDCONV,PSECU,PPASS,PINFL,PSAL=P("$G$6"),P("$G$7"),P("$G$8"),P("$G$9"),P("$G$10"),P("$G$11"),P("$G$12")
KETPC,KFRAIS,KSTRUCT,KRECOUV,KAUTRES,KSECUN1,KELAST,KCONV=(P("$D$15"),P("$D$16"),P("$D$17"),P("$D$18"),P("$D$19"),P("$D$20"),P("$D$21"),P("$D$22"))

# ============================================================ 00_Notice
ws=wb.active; ws.title="00_Notice"; ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":30,"C":66,"D":20}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:D2"); C(ws,"B2","EDUSERVICES GROUP — Pilotage budgétaire (v2)",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=30
ws.merge_cells("B3:D3"); C(ws,"B3","Cohortes · marketing mesuré sur l'historique · maille programme×année · cadrage cible · simulateur de décisions",CIT)
band(ws,5,"B","D","Les feuilles")
sh=[("01_Objectifs","CADRAGE top-down : CA & EBITDA cibles € → écart vs budget construit"),
 ("02_Leviers","Hypothèses de pilotage + scénario + constantes de référence"),
 ("03_Coeff_Strateg","Coefficients stratégiques par marque (marketing / prix)"),
 ("04_Referentiel","Dimensions : entités, comptes (fixe/variable)"),
 ("05_Param_Prog_Annee","DONNÉES DE RÉFÉRENCE par programme×année (capacité, heures, taux, pédago, CAC variable, passage)"),
 ("06_Historique","Réalisé N-1 par cellule (funnel, cohorte) + historique marketing N-2/N-1 → élasticité mesurée"),
 ("07_Structure","Réalisé par campus (loyers, ETP, D&A, m²)"),
 ("08_Moteur","Moteur budget par cellule (cohortes, marketing→volume, seuil=point mort)"),
 ("09_Allocation","Frais de structure alloués par driver"),
 ("10_PnL","P&L consolidé N-1 vs Budget + pont à 4 effets"),
 ("11_Simulateur","Décisions ouvrir/fermer/redistribuer → EBITDA AVANT → APRÈS"),
 ("12_Sensibilite","Impact € sur l'EBITDA par levier (sens unique)"),
 ("13_Simulation","KPIs, € à risque, taux d'alternance/sécurisation"),
 ("14_Mapping_Tagetik","Passerelle Tagetik")]
r=6
for a,b in sh:
    C(ws,f"B{r}",a,CB,FLIGHT,align=AL,border=True); ws.merge_cells(f"C{r}:D{r}"); C(ws,f"C{r}",b,CREG,align=ALW,border=True); r+=1
band(ws,r+1,"B","D","Légende"); r+=2
for t,ft,fl in [("Saisie / donnée réelle",CIN,None),("Formule",CF,None),("Lien inter-feuilles",CL,None),("Hypothèse à remplir",CB,FYEL)]:
    C(ws,f"B{r}"," exemple ",ft,fl,align=AC,border=True); ws.merge_cells(f"C{r}:D{r}"); C(ws,f"C{r}",t,CREG,align=AL,border=True); r+=1
ws.merge_cells(f"B{r+1}:D{r+2}")
C(ws,f"B{r+1}","Marques/campus réels EDUSERVICES ; montants ILLUSTRATIFS calibrés sur des ordres de grandeur sourcés "
 "(scolarité 8-11 k€, NPEC ~7-10 k€, marge EBITDA ~20 %, classe ~30). À remplacer par le réel.",CIT,align=ALW)

# ============================================================ 02_Leviers
ws=wb.create_sheet("02_Leviers"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":42,"C":13,"D":13,"E":13,"F":13,"G":14}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:G2"); C(ws,"B2","Leviers de pilotage & scénarios",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=28
C(ws,"B3","Scénario actif :",CB,align=AR); C(ws,"C3","Cadrage",CINB,FYEL,align=AC,border=True)
dv=DataValidation(type="list",formula1='"Cadrage,Optimiste,Prudent"',allow_blank=False); ws.add_data_validation(dv); dv.add(ws["C3"])
C(ws,"E3","◄ tout bascule",CIT); ws.merge_cells("E3:G3")
C(ws,"B5","Levier (décision)",CHDR,FBLUE,align=AL,border=True); C(ws,"C5","Unité",CHDR,FBLUE,align=AC,border=True)
for col,n in (("D","Cadrage"),("E","Optimiste"),("F","Prudent")): C(ws,f"{col}5",n,CHDR,FBLUE,align=AC,border=True)
C(ws,"G5","ACTIF",CHDR,FNAVY,align=AC,border=True)
levs=[("Variation du budget marketing (→ volume)","%",0.10,0.20,-0.05,PCT),
 ("Hausse tarifaire (prix)","%",0.03,0.04,0.02,PCT),
 ("Gain de conversion admissions","pts",0.015,0.04,0.0,PCT),
 ("Taux de sécurisation contrat (≤3 mois)","%",0.88,0.93,0.80,PCT),
 ("Amélioration du taux de passage","pts",0.01,0.03,-0.01,PCT),
 ("Inflation des charges (groupe)","%",0.02,0.015,0.03,PCT),
 ("Politique salariale (groupe)","%",0.025,0.02,0.03,PCT)]
r=6
for lib,u,cad,opt,pru,fmt in levs:
    C(ws,f"B{r}",lib,CREG,align=AL,border=True); C(ws,f"C{r}",u,CREG,align=AC,border=True)
    C(ws,f"D{r}",cad,CIN,fmt=fmt,align=AC,border=True); C(ws,f"E{r}",opt,CIN,fmt=fmt,align=AC,border=True); C(ws,f"F{r}",pru,CIN,fmt=fmt,align=AC,border=True)
    C(ws,f"G{r}",f"=INDEX(D{r}:F{r},MATCH($C$3,$D$5:$F$5,0))",CF,FLIGHT,fmt=fmt,align=AC,border=True); r+=1
C(ws,"B14","Constantes de référence (le réel = à charger · repli = si historique mince)",CHDR,FBLUE,align=AL,border=True)
for col in ("C","D","E","F","G"): C(ws,f"{col}14"," ",fill=FBLUE,border=True)
consts=[("Coût chargé / ETP permanent","€",ETPC,EUR,"réel (SIRH)"),
 ("Frais de dossier / nouvel inscrit","€",FRAIS,EUR,"réel"),
 ("Frais de structure & marketing groupe (€ FIXE)","€",STRUCT_FIXE,EUR,"réel (siège, IT, marque)"),
 ("Recouvrement reste à charge (employeur)","%",RECOUV,PCT,"hypothèse (100% légal)"),
 ("Autres charges d'exploitation / étudiant","€",AUTRES_ETU,EUR,"réel (achats, sous-traitance, IT)"),
 ("Sécurisation N-1 — défaut (si hist. manquant)","%",SECU_N1,PCT,"défaut (sinon mesuré par programme)"),
 ("Élasticité marketing — défaut (si hist. manquant)","x",ELAST_DEF,X2,"défaut (sinon mesurée N-2/N-1)"),
 ("Conversion cand.→inscrit — défaut (si hist. manquant)","%",CONV_N1,PCT,"défaut (sinon mesurée par cellule)")]
r=15
for lib,u,val,fmt,note in consts:
    C(ws,f"B{r}",lib,CREG,align=AL,border=True); C(ws,f"C{r}",u,CREG,align=AC,border=True)
    C(ws,f"D{r}",val,(CINB if ('hypothèse' in note or 'repli' in note) else CIN),(FYEL if ('hypothèse' in note or 'repli' in note) else None),fmt=fmt,align=AC,border=True)
    C(ws,f"E{r}",note,CIT,align=AL,border=True); ws.merge_cells(f"E{r}:F{r}")
    C(ws,f"G{r}",f"=D{r}",CF,FLIGHT,fmt=fmt,align=AC,border=True); r+=1
C(ws,"B24","Driver d'allocation :",CB,align=AR); ws.merge_cells("B24:C24")
C(ws,"D24","Effectifs",CINB,FYEL,align=AC,border=True)
dv2=DataValidation(type="list",formula1='"Effectifs,Chiffre d\'affaires,Surface m2"',allow_blank=False); ws.add_data_validation(dv2); dv2.add(ws["D24"])
DRIVER="'02_Leviers'!$D$24"

# ============================================================ 03_Coeff_Strateg
ws=wb.create_sheet("03_Coeff_Strateg"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":26,"C":18,"D":16,"E":14}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:E2"); C(ws,"B2","Coefficients stratégiques par marque",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=28
ws.merge_cells("B3:E3"); C(ws,"B3","On pousse + ou – selon la marque : effort appliqué = levier × coefficient.",CIT)
for i,h in enumerate(["Marque","Intensité MARKETING","Intensité PRIX","Posture"]): C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
CO0=6; r=CO0
for marque,(dom,cv,cp,base,villes) in BRANDS.items():
    C(ws,f"B{r}",marque,CREG,align=AL,border=True)
    C(ws,f"C{r}",cv,CIN,fmt=X2,align=AC,border=True); C(ws,f"D{r}",cp,CIN,fmt=X2,align=AC,border=True)
    C(ws,f"E{r}",f'=IF(C{r}>=1.15,"Pousser",IF(C{r}<=0.85,"Défendre","Maintenir"))',CF,align=AC,border=True); r+=1
CON=r-1
CVRANGE=f"'03_Coeff_Strateg'!$C${CO0}:$C${CON}"; CPRANGE=f"'03_Coeff_Strateg'!$D${CO0}:$D${CON}"; CMRANGE=f"'03_Coeff_Strateg'!$B${CO0}:$B${CON}"

# ============================================================ 04_Referentiel
ws=wb.create_sheet("04_Referentiel"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":24,"C":16,"D":22,"E":14,"F":12}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:F2"); C(ws,"B2","Référentiel — dimensions",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=26
band(ws,4,"B","F","Entités : Groupe → Marque → Campus")
for i,h in enumerate(["Marque","Ville","Domaine","Niveau","Devise"]): C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
r=6; C(ws,f"B{r}","EDUSERVICES GROUP",CINB,FTOT,align=AL,border=True); C(ws,f"C{r}","—",CREG,FTOT,align=AC,border=True)
C(ws,f"D{r}","Tous",CREG,FTOT,align=AC,border=True); C(ws,f"E{r}","Groupe",CB,FTOT,align=AC,border=True); C(ws,f"F{r}","EUR",CREG,FTOT,align=AC,border=True); r+=1
for marque,(dom,cv,cp,base,villes) in BRANDS.items():
    for ville in villes:
        C(ws,f"B{r}",marque,CIN,align=AL,border=True); C(ws,f"C{r}",ville,CIN,align=AC,border=True)
        C(ws,f"D{r}",dom,CREG,align=AC,border=True); C(ws,f"E{r}","Campus",CREG,align=AC,border=True); C(ws,f"F{r}","EUR",CREG,align=AC,border=True); r+=1
band(ws,r+1,"B","F","Comptes (nature fixe/variable)"); r+=2
for i,h in enumerate(["Compte","Libellé","Rubrique","Nature","Inducteur"]): C(ws,f"{GL(2+i)}{r}",h,CHDR,FBLUE,align=AC,border=True)
r+=1
for cpt,lib,rub,nat,ind in [("70600","Scolarité","CA","—","Effectif × tarif"),("70800","Frais de dossier","CA","—","Nouveaux"),
 ("64100","Enseignement","Coût direct","Semi-fixe/classe","Classes × heures"),("60700","Pédagogie","Coût direct","Variable","Effectif"),
 ("62300","Marketing","Coût direct","Variable","Nouveaux / budget"),("61300","Loyers","Structure","Fixe","Campus"),
 ("64000","Personnel permanent","Structure","Fixe","ETP"),("65000","Structure groupe","Structure","Fixe (alloué)","Driver"),("68000","D&A","D&A","Fixe","Campus")]:
    C(ws,f"B{r}",cpt,CIN,align=AL,border=True); C(ws,f"C{r}",lib,CREG,align=AL,border=True); C(ws,f"D{r}",rub,CREG,align=AC,border=True)
    C(ws,f"E{r}",nat,CREG,align=AC,border=True); C(ws,f"F{r}",ind,CREG,align=AL,border=True); r+=1

# ============================================================ 05_Param_Prog_Annee
ws=wb.create_sheet("05_Param_Prog_Annee"); ws.sheet_view.showGridLines=False
hh=["Clé (prog|année)","Programme","Année","Mod.","Capacité","Heures/classe","Taux horaire","Coût pédago/étu","CAC variable","Taux de passage"]
hw=[20,20,7,6,10,12,11,13,12,13]
for i,w in enumerate(hw): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells("A1:J1"); C(ws,"A1","Données de référence par programme × année (issues du réalisé — à charger)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=24
ws.merge_cells("A2:J2"); C(ws,"A2","Bleu = saisie. Capacité, heures, taux, pédago, CAC variable et taux de passage varient par programme ET par année.",CIT)
for i,h in enumerate(hh): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
PA0=4; r=PA0
for (prog,ptype,niv,mod,cap,heures,taux,ped,cacv,passage,dom) in PPA:
    C(ws,f"A{r}",f"{prog}|{niv}",CIN,align=AL,border=True); C(ws,f"B{r}",prog,CIN,align=AL,border=True); C(ws,f"C{r}",niv,CIN,align=AC,border=True); C(ws,f"D{r}",mod,CIN,align=AC,border=True)
    C(ws,f"E{r}",cap,CIN,fmt=NB,align=AC,border=True); C(ws,f"F{r}",heures,CIN,fmt=NB,align=AC,border=True); C(ws,f"G{r}",taux,CIN,fmt=EUR,align=AC,border=True)
    C(ws,f"H{r}",ped,CIN,fmt=EUR,align=AC,border=True); C(ws,f"I{r}",cacv,CIN,fmt=EUR,align=AC,border=True)
    C(ws,f"J{r}",(passage if passage else None),CIN,fmt=PCT,align=AC,border=True); r+=1
PAN=r-1
PA=lambda col:f"'05_Param_Prog_Annee'!${col}${PA0}:${col}${PAN}"
PAKEY=PA("A")

# ============================================================ 06_Historique (+ bloc marketing)
ws=wb.create_sheet("06_Historique"); ws.sheet_view.showGridLines=False
hc=["Marque","Ville","Programme","Type","Année","Mod.","Entrée","Cand N-1","Nouv N-1","Réins N-1","Effectif N-1","Eff. année inf. N-1","Tarif N-1","Classes N-1"]
hw=[15,10,18,6,7,6,7,9,9,9,10,13,9,9]
for i,w in enumerate(hw): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells("A1:N1"); C(ws,"A1","Réalisé N-1 par cellule (funnel + cohorte)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
for i,h in enumerate(hc): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
HR0=4; r=HR0
for rr in rows:
    vals=[rr["marque"],rr["ville"],rr["prog"],rr["type"],rr["niv"],rr["mod"],rr["entry"],rr["cand"],rr["nouv"],rr["rein"],rr["eff"],rr["eff_prev"],rr["tarif"],rr["classes"]]
    for i,v in enumerate(vals):
        fmt=NB if i in (7,8,9,10,11,13) else (EUR if i==12 else None)
        al=AC if i>=4 else AL
        C(ws,f"{GL(1+i)}{r}",v,CIN,fmt=fmt,align=al,border=True)
    r+=1
HRN=HR0+N-1
# bloc marketing par programme (N-2/N-1 -> élasticité)
mrow=HRN+3
C(ws,f"A{mrow}","Historique marketing & sécurisation par programme (issu du réalisé)",CB,align=AL); ws.merge_cells(f"A{mrow}:G{mrow}")
mrow+=1
for i,h in enumerate(["Programme","Cand N-2","Cand N-1","Marketing N-2","Marketing N-1","Élasticité mesurée","Sécurisation N-1"]): C(ws,f"{GL(1+i)}{mrow}",h,CHDR,FBLUE,align=AC,border=True)
ME0=mrow+1; r=ME0
for (m,pnom,ptype,dom) in prog_list:
    h=mkt_hist[(m,pnom)]
    C(ws,f"A{r}",pnom,CIN,align=AL,border=True); C(ws,f"B{r}",h["cand_n2"],CIN,fmt=NB,align=AC,border=True); C(ws,f"C{r}",h["cand_n1"],CIN,fmt=NB,align=AC,border=True)
    C(ws,f"D{r}",h["mkt_n2"],CIN,fmt=EUR,align=AR,border=True); C(ws,f"E{r}",h["mkt_n1"],CIN,fmt=EUR,align=AR,border=True)
    C(ws,f"F{r}",f"=IFERROR((C{r}/B{r}-1)/(E{r}/D{r}-1),{KELAST})",CF,fmt=X2,align=AC,border=True)
    C(ws,f"G{r}",secu_prog(dom),CIN,fmt=PCT,align=AC,border=True); r+=1
MEN=r-1
MEKEY=f"'06_Historique'!$A${ME0}:$A${MEN}"; MEELA=f"'06_Historique'!$F${ME0}:$F${MEN}"; MESECU=f"'06_Historique'!$G${ME0}:$G${MEN}"
def hc_(col,rr): return f"'06_Historique'!{col}{rr}"

# ============================================================ 07_Structure
ws=wb.create_sheet("07_Structure"); ws.sheet_view.showGridLines=False
sc=["Marque","Ville","Effectif N-1","CA N-1","Contribution N-1","Loyer N-1","ETP perm.","Masse perm. N-1","D&A N-1","Surface m²","EBITDA campus N-1"]
sw=[15,10,11,13,14,12,10,14,11,10,15]
for i,w in enumerate(sw): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells("A1:K1"); C(ws,"A1","Réalisé N-1 par campus (structure)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
for i,h in enumerate(sc): C(ws,f"{GL(1+i)}3",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[3].height=30
SR0=4; r=SR0
for cc in campus:
    C(ws,f"A{r}",cc["marque"],CIN,align=AL,border=True); C(ws,f"B{r}",cc["ville"],CIN,align=AC,border=True)
    C(ws,f"C{r}",cc["eff"],CIN,fmt=NB,align=AC,border=True); C(ws,f"D{r}",cc["ca"],CIN,fmt=EUR,align=AR,border=True)
    C(ws,f"E{r}",round(cc["contrib"]),CIN,fmt=EUR,align=AR,border=True); C(ws,f"F{r}",cc["loyer"],CIN,fmt=EUR,align=AR,border=True)
    C(ws,f"G{r}",cc["etp"],CIN,fmt=NB,align=AC,border=True); C(ws,f"H{r}",f"=G{r}*{KETPC}",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"I{r}",cc["da"],CIN,fmt=EUR,align=AR,border=True); C(ws,f"J{r}",cc["m2"],CIN,fmt=NB,align=AC,border=True)
    C(ws,f"K{r}",f"=E{r}-F{r}-H{r}",CF,fmt=EUR,align=AR,border=True); r+=1
SRN=SR0+CG-1; r=SR0+CG
C(ws,f"A{r}","TOTAL",CFB,FTOT,align=AL,border=True); C(ws,f"B{r}"," ",fill=FTOT,border=True)
for col in ["C","D","E","F","G","H","I","J","K"]:
    C(ws,f"{col}{r}",f"=SUM({col}{SR0}:{col}{SRN})",CFB,FTOT,fmt=(NB if col in("C","G","J") else EUR),align=(AC if col in("C","G","J") else AR),border=True)
STOT=r
STC=lambda col:f"'07_Structure'!{col}{STOT}"

# ============================================================ 08_Moteur
ws=wb.create_sheet("08_Moteur"); ws.sheet_view.showGridLines=False
mcols=["Marque","Ville","Programme","Année","Mod","Entrée","Eff N-1","Nouv N-1","Réins N-1","Cand N-1","EffInf N-1","Tarif N-1","Cl N-1","clé",
 "Cap","Heures","Taux","Pédago","CACvar","Passage","Coût/cl","cMkt","cPrix","Élast","Effort","Cand Bud","Conv","Nouv Bud","Réins Bud","Effectif Bud",
 "Tarif Bud","SecFac","SecN-1","CA Bud","Cl besoin","Enseign","Pédago€","Mktg","Contrib","Rempl","Contr/étu","Pt mort"]
for i,w in enumerate([15,9,17,6,5,6]+[9]*(len(mcols)-6)): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells("A1:AP1"); C(ws,"A1","Moteur de budget par cellule (cohortes · marketing→volume mesuré · seuil=point mort)",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
for i,h in enumerate(mcols): C(ws,f"{GL(1+i)}2",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[2].height=28
MR0=3
for idx in range(N):
    r=MR0+idx; hr=HR0+idx
    lk=lambda c:f"={hc_(c,hr)}"
    C(ws,f"A{r}",lk('A'),CL,align=AL,border=True); C(ws,f"B{r}",lk('B'),CL,align=AC,border=True); C(ws,f"C{r}",lk('C'),CL,align=AL,border=True)
    C(ws,f"D{r}",lk('E'),CL,align=AC,border=True); C(ws,f"E{r}",lk('F'),CL,align=AC,border=True); C(ws,f"F{r}",lk('G'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"G{r}",lk('K'),CL,fmt=NB,align=AC,border=True); C(ws,f"H{r}",lk('I'),CL,fmt=NB,align=AC,border=True); C(ws,f"I{r}",lk('J'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"J{r}",lk('H'),CL,fmt=NB,align=AC,border=True); C(ws,f"K{r}",lk('L'),CL,fmt=NB,align=AC,border=True); C(ws,f"L{r}",lk('M'),CL,fmt=EUR,align=AC,border=True); C(ws,f"M{r}",lk('N'),CL,fmt=NB,align=AC,border=True)
    C(ws,f"N{r}",f'=C{r}&"|"&D{r}',CF,align=AC,border=True)
    C(ws,f"O{r}",f"=INDEX({PA('E')},MATCH(N{r},{PAKEY},0))",CF,fmt=NB,align=AC,border=True)
    C(ws,f"P{r}",f"=INDEX({PA('F')},MATCH(N{r},{PAKEY},0))",CF,fmt=NB,align=AC,border=True)
    C(ws,f"Q{r}",f"=INDEX({PA('G')},MATCH(N{r},{PAKEY},0))",CF,fmt=EUR,align=AC,border=True)
    C(ws,f"R{r}",f"=INDEX({PA('H')},MATCH(N{r},{PAKEY},0))",CF,fmt=EUR,align=AC,border=True)
    C(ws,f"S{r}",f"=INDEX({PA('I')},MATCH(N{r},{PAKEY},0))",CF,fmt=EUR,align=AC,border=True)
    C(ws,f"T{r}",f"=IFERROR(INDEX({PA('J')},MATCH(N{r},{PAKEY},0)),0)",CF,fmt=PCT,align=AC,border=True)
    C(ws,f"U{r}",f"=P{r}*Q{r}*(1+{PSAL})",CF,fmt=EUR,align=AC,border=True)
    C(ws,f"V{r}",f"=INDEX({CVRANGE},MATCH(A{r},{CMRANGE},0))",CF,fmt=X2,align=AC,border=True)
    C(ws,f"W{r}",f"=INDEX({CPRANGE},MATCH(A{r},{CMRANGE},0))",CF,fmt=X2,align=AC,border=True)
    C(ws,f"X{r}",f"=IFERROR(INDEX({MEELA},MATCH(C{r},{MEKEY},0)),{KELAST})",CF,fmt=X2,align=AC,border=True)
    C(ws,f"Y{r}",f"={PMKT}*V{r}",CF,fmt=PCT,align=AC,border=True)
    C(ws,f"Z{r}",f"=IF(F{r}=1,J{r}*(1+X{r}*Y{r}),0)",CF,fmt=NB,align=AC,border=True)
    C(ws,f"AA{r}",f"=IF(F{r}=1,IFERROR(H{r}/J{r},{KCONV})+{PDCONV},0)",CF,fmt=PCT,align=AC,border=True)  # conversion mesurée par cellule + gain
    C(ws,f"AB{r}",f"=Z{r}*AA{r}",CF,fmt=NB,align=AC,border=True)
    C(ws,f"AC{r}",f"=IF(F{r}=1,0,K{r}*(T{r}+{PPASS}))",CF,fmt=NB,align=AC,border=True)
    C(ws,f"AD{r}",f"=AB{r}+AC{r}",CFB,fmt=NB,align=AC,border=True)
    C(ws,f"AE{r}",f"=L{r}*(1+{PPRIX}*W{r})",CF,fmt=EUR,align=AC,border=True)
    C(ws,f"AF{r}",f'=IF(E{r}="ALT",{PSECU}+(1-{PSECU})*{KRECOUV},1)',CF,fmt=X2,align=AC,border=True)
    C(ws,f"AG{r}",f'=IF(E{r}="ALT",IFERROR(INDEX({MESECU},MATCH(C{r},{MEKEY},0)),{KSECUN1})+(1-IFERROR(INDEX({MESECU},MATCH(C{r},{MEKEY},0)),{KSECUN1}))*{KRECOUV},1)',CF,fmt=X2,align=AC,border=True)  # sécu N-1 par programme
    C(ws,f"AH{r}",f"=AD{r}*AE{r}*AF{r}+AB{r}*{KFRAIS}",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"AI{r}",f"=IF(AD{r}<=0,0,MAX(1,ROUNDUP(AD{r}/O{r},0)))",CF,fmt=NB,align=AC,border=True)
    C(ws,f"AJ{r}",f"=AI{r}*U{r}",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"AK{r}",f"=AD{r}*R{r}*(1+{PINFL})",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"AL{r}",f"=H{r}*S{r}*(1+Y{r})",CF,fmt=EUR,align=AR,border=True)  # marketing variable (achat de leads) × (1+effort) ; le global est en structure fixe
    C(ws,f"AM{r}",f"=AH{r}-AJ{r}-AK{r}-AL{r}-AD{r}*{KAUTRES}*(1+{PINFL})",CFB,fmt=EUR,align=AR,border=True)
    C(ws,f"AN{r}",f"=IFERROR(AD{r}/(AI{r}*O{r}),0)",CF,fmt=PCT,align=AC,border=True)
    C(ws,f"AO{r}",f"=IFERROR(AM{r}/AD{r},0)",CF,fmt=EUR,align=AC,border=True)
    C(ws,f"AP{r}",f"=IFERROR(AI{r}*U{r}/(AE{r}*AF{r}-R{r}*(1+{PINFL})),0)",CF,fmt=NB,align=AC,border=True)
MRN=MR0+N-1; r=MR0+N
C(ws,f"A{r}","TOTAL",CFB,FTOT,align=AL,border=True)
for col in ["B","C","D","E"]: C(ws,f"{col}{r}"," ",fill=FTOT,border=True)
for col,fmt in [("F",NB),("G",NB),("H",NB),("AB",NB),("AC",NB),("AD",NB),("AH",EUR),("AI",NB),("AJ",EUR),("AK",EUR),("AL",EUR),("AM",EUR)]:
    C(ws,f"{col}{r}",f"=SUM({col}{MR0}:{col}{MRN})",CFB,FTOT,fmt=fmt,align=(AC if fmt==NB else AR),border=True)
MTOT=r; ws.freeze_panes="G3"
MO=lambda col:f"'08_Moteur'!{col}"
def mrng(col): return f"'08_Moteur'!${col}${MR0}:${col}${MRN}"
def msum(col): return f"SUM({mrng(col)})"
# ============================================================ 09_Allocation
ws=wb.create_sheet("09_Allocation"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":16,"C":11,"D":13,"E":11,"F":13,"G":12,"H":11,"I":13,"J":13,"K":11,"L":13}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:L2"); C(ws,"B2","Allocation des frais de structure par driver",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=24
C(ws,"B3","Driver actif :",CB,align=AR); C(ws,"C3",f"={DRIVER}",CL,FYEL,align=AC,border=True)
C(ws,"E3","Frais de structure (fixe) à allouer :",CB,align=AR); ws.merge_cells("E3:G3")
C(ws,"H3",f"={KSTRUCT}*(1+{PINFL})",CFB,fmt=EUR,align=AR,border=True); ws.merge_cells("H3:I3")
for i,h in enumerate(["Marque","Ville","Contribution","Loyer","Masse perm.","Driver","Part","Alloué","EBITDA campus","D&A","EBIT"]):
    C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[5].height=28
AR0=6; GC="$H$3"
for idx,cc in enumerate(campus):
    r=AR0+idx; sr=SR0+idx; vl=cc["ville"]
    crit=f'{mrng("A")},"{cc["marque"]}",{mrng("B")},"{vl}"'
    C(ws,f"B{r}",cc["marque"],CL,align=AL,border=True); C(ws,f"C{r}",vl,CL,align=AC,border=True)
    C(ws,f"D{r}",f"=SUMIFS({mrng('AM')},{crit})",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"E{r}",f"='07_Structure'!F{sr}*(1+{PINFL})",CL,fmt=EUR,align=AR,border=True)
    C(ws,f"F{r}",f"='07_Structure'!G{sr}*{KETPC}*(1+{PSAL})",CL,fmt=EUR,align=AR,border=True)
    effb=f"SUMIFS({mrng('AD')},{crit})"; cab=f"SUMIFS({mrng('AH')},{crit})"; m2=f"'07_Structure'!J{sr}"
    C(ws,f"G{r}",f"=IF($C$3=\"Effectifs\",{effb},IF($C$3=\"Chiffre d'affaires\",{cab},{m2}))",CF,fmt=NB,align=AR,border=True)
    C(ws,f"H{r}",f"=IFERROR(G{r}/SUM($G${AR0}:$G${AR0+CG-1}),0)",CF,fmt=PCT,align=AC,border=True)
    C(ws,f"I{r}",f"=H{r}*{GC}",CF,fmt=EUR,align=AR,border=True)
    C(ws,f"J{r}",f"=D{r}-E{r}-F{r}-I{r}",CFB,fmt=EUR,align=AR,border=True)
    C(ws,f"K{r}",f"='07_Structure'!I{sr}",CL,fmt=EUR,align=AR,border=True)
    C(ws,f"L{r}",f"=J{r}-K{r}",CF,fmt=EUR,align=AR,border=True)
ARN=AR0+CG-1; r=AR0+CG
C(ws,f"B{r}","TOTAL",CFB,FTOT,align=AL,border=True); C(ws,f"C{r}"," ",fill=FTOT,border=True)
for col in ["D","E","F","I","J","K","L"]: C(ws,f"{col}{r}",f"=SUM({col}{AR0}:{col}{ARN})",CFB,FTOT,fmt=EUR,align=AR,border=True)
C(ws,f"G{r}",f"=SUM(G{AR0}:G{ARN})",CFB,FTOT,fmt=NB,align=AR,border=True); C(ws,f"H{r}"," ",fill=FTOT,border=True)
ATOT=r; ALc=lambda col:f"'09_Allocation'!{col}{ATOT}"

# ============================================================ 10_PnL
ws=wb.create_sheet("10_PnL"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":34,"C":15,"D":15,"E":14,"F":11}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:F2"); C(ws,"B2","Compte de résultat consolidé — Budget vs N-1",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=24
C(ws,"B3","Scénario :",CB,align=AR); C(ws,"C3","='02_Leviers'!C3",CL,align=AC)
for i,h in enumerate(["Rubrique","Réalisé N-1","Budget N+1","Écart €","Écart %"]): C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
n1_eff=STC("C"); n1_ca=STC("D"); n1_ctb=STC("E"); n1_loy=STC("F"); n1_perm=STC("H"); n1_da=STC("I"); n1_str=str(STRUCT_FIXE)
def pl(r,lib,n1,bud,fmt,bold,pct=False):
    ft=CFB if bold else CREG; fl=FLIGHT if bold else None
    C(ws,f"B{r}",lib,ft,fl,align=AL,border=True); C(ws,f"C{r}",n1,(CFB if bold else CL),fl,fmt=fmt,align=AR,border=True); C(ws,f"D{r}",bud,(CFB if bold else CF),fl,fmt=fmt,align=AR,border=True)
    if pct: C(ws,f"E{r}",f"=D{r}-C{r}",ft,fl,fmt=PCT,align=AR,border=True); C(ws,f"F{r}"," ",fill=fl,border=True)
    else: C(ws,f"E{r}",f"=D{r}-C{r}",ft,fl,fmt=fmt,align=AR,border=True); C(ws,f"F{r}",f"=IFERROR(D{r}/C{r}-1,0)",ft,fl,fmt=PCT,align=AR,border=True)
r=6
pl(r,"Effectifs",f"={n1_eff}",f"={msum('AD')}",NB,False); r+=1
pl(r,"Chiffre d'affaires",f"={n1_ca}",f"={msum('AH')}",EUR,True); r+=1
pl(r,"  Coûts directs (ens.+pédago+mktg+autres)",f"=-({n1_ca}-{n1_ctb})",f"=-({msum('AJ')}+{msum('AK')}+{msum('AL')}+{KAUTRES}*(1+{PINFL})*{msum('AD')})",EUR,False); r+=1
pl(r,"Marge de contribution",f"={n1_ctb}",f"={msum('AM')}",EUR,True); r+=1
pl(r,"  Loyers",f"=-{n1_loy}",f"=-{ALc('E')}",EUR,False); r+=1
pl(r,"  Personnel permanent",f"=-{n1_perm}",f"=-{ALc('F')}",EUR,False); r+=1
pl(r,"  Frais de structure groupe",f"=-{n1_str}",f"=-{ALc('I')}",EUR,False); r+=1
pl(r,"EBITDA",f"={n1_ctb}-{n1_loy}-{n1_perm}-{n1_str}",f"={ALc('J')}",EUR,True); r+=1
pl(r,"  Marge EBITDA %",f"=IFERROR(({n1_ctb}-{n1_loy}-{n1_perm}-{n1_str})/{n1_ca},0)",f"=IFERROR({ALc('J')}/{msum('AH')},0)",PCT,False,pct=True); r+=1
pl(r,"  D&A",f"=-{n1_da}",f"=-{ALc('K')}",EUR,False); r+=1
pl(r,"EBIT",f"={n1_ctb}-{n1_loy}-{n1_perm}-{n1_str}-{n1_da}",f"={ALc('L')}",EUR,True); r+=1
band(ws,r+1,"B","F","Pont Chiffre d'affaires (N-1 → Budget)"); r+=2
for i,h in enumerate(["Effet","Montant"]): C(ws,f"{GL(2+i)}{r}",h,CHDR,FBLUE,align=AC,border=True)
r+=1
vol=f"=SUMPRODUCT(({mrng('AD')}-{mrng('G')})*{mrng('L')}*{mrng('AG')})"
tar=f"=SUMPRODUCT({mrng('AD')}*({mrng('AE')}-{mrng('L')})*{mrng('AG')})"
sig=f"=SUMPRODUCT({mrng('AD')}*{mrng('AE')}*({mrng('AF')}-{mrng('AG')}))"
fra=f"=SUMPRODUCT({mrng('AB')})*{KFRAIS}-SUMPRODUCT({mrng('H')})*{KFRAIS}"
for lib,f2,fl in [("CA Réalisé N-1",f"={n1_ca}",None),("  + Effet Volume",vol,None),("  + Effet Tarif",tar,None),
 ("  + Effet Sécurisation",sig,None),("  + Effet Frais",fra,None),("CA Budget N+1",f"={msum('AH')}",FTOT)]:
    C(ws,f"B{r}",lib,(CFB if fl else CREG),fl,align=AL,border=True); C(ws,f"C{r}",f2,(CFB if fl else CF),fl,fmt=EUR,align=AR,border=True); r+=1

# ============================================================ 01_Objectifs (Cadrage top-down)  [tab position 1]
ws=wb.create_sheet("01_Objectifs",1); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":34,"C":16,"D":16,"E":14}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:E2"); C(ws,"B2","Cadrage — objectifs top-down vs budget construit",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=26
ws.merge_cells("B3:E3"); C(ws,"B3","La direction pose les cibles € ; le modèle affiche l'écart avec la construction par les drivers.",CIT)
for i,h in enumerate(["Indicateur","Cible (direction)","Budget construit","Écart"]): C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
C(ws,"B6","Chiffre d'affaires",CB,align=AL,border=True)
C(ws,"C6",round(grp_ca_n1*1.06),CINB,FYEL,fmt=EUR,align=AR,border=True); C(ws,"D6",f"={msum('AH')}",CL,fmt=EUR,align=AR,border=True); C(ws,"E6","=D6-C6",CF,fmt=EUR,align=AR,border=True)
C(ws,"B7","EBITDA",CB,align=AL,border=True)
C(ws,"C7",round(grp_ca_n1*1.06*0.21),CINB,FYEL,fmt=EUR,align=AR,border=True); C(ws,"D7",f"={ALc('J')}",CL,fmt=EUR,align=AR,border=True); C(ws,"E7","=D7-C7",CF,fmt=EUR,align=AR,border=True)
C(ws,"B8","Marge EBITDA %",CB,align=AL,border=True)
C(ws,"C8","=IFERROR(C7/C6,0)",CF,fmt=PCT,align=AR,border=True); C(ws,"D8","=IFERROR(D7/D6,0)",CF,fmt=PCT,align=AR,border=True); C(ws,"E8","=D8-C8",CF,fmt=PCT,align=AR,border=True)
C(ws,"B10","Reste à trouver (EBITDA) :",CB,align=AR); ws.merge_cells("B10:C10")
C(ws,"D10","=IF(E7<0,-E7,0)",CFB,FRISK,fmt=EUR,align=AR,border=True)
ws.merge_cells("B12:E14")
C(ws,"B12","Cibles en JAUNE (saisie direction). Le budget construit vient du moteur (feuille 08) et bouge avec tes leviers. "
 "Utilise la feuille 12_Sensibilite pour savoir quels leviers actionner afin de combler l'écart.",CIT,align=ALW)

# ============================================================ 11_Simulateur (logique CFO 360° : dilution symétrique)
ws=wb.create_sheet("11_Simulateur"); ws.sheet_view.showGridLines=False
sc=["Marque","Ville","Programme","Année","Effectif","CA","Coûts directs\névitables","MARGE DE\nCONTRIBUTION","Rempl.","🤖 Reco","Motif","Décision",
 "Effectif\naprès","Contribution\naprès","Structure allouée\n(après, dilution)","Résultat tout\ncompris (après)","Δ EBITDA"]
for i,w in enumerate([13,9,15,6,8,11,12,13,7,19,40,17,9,12,12,12,11]): ws.column_dimensions[GL(1+i)].width=w
ws.merge_cells("A1:Q1"); C(ws,"A1","Simulateur & conseil de décisions — logique CFO 360° : décider sur la CONTRIBUTION ; ouvrir/fermer redilue la structure sur TOUS",CTIT,FNAVY,align=AL); ws.row_dimensions[1].height=22
DR0=6; last=DR0+N-1
STRUCT_TOT=f"({ALc('E')}+{ALc('F')}+{ALc('I')})"; STRUCT_ETU=f"{STRUCT_TOT}/{msum('AD')}"
EFF_AP=f"SUM(M{DR0}:M{last})"   # effectif total APRÈS décisions (pilote la dilution, dans les deux sens)
C(ws,"A2","EBITDA groupe AVANT :",CB,align=AR); ws.merge_cells("A2:C2"); C(ws,"D2",f"={ALc('J')}",CFB,fmt=EUR,align=AR,border=True)
C(ws,"E2","Σ Δ décisions :",CB,align=AR); ws.merge_cells("E2:F2"); C(ws,"G2",f"=SUM(Q{DR0}:Q{last})",CFB,fmt=EUR,align=AR,border=True); ws.merge_cells("G2:H2")
C(ws,"I2","EBITDA groupe APRÈS :",CB,align=AR); ws.merge_cells("I2:J2"); C(ws,"K2","=D2+G2",CFB,FTOT,fmt=EUR,align=AR,border=True); ws.merge_cells("K2:L2")
C(ws,"A3","Structure / étudiant — AVANT :",CB,align=AR); ws.merge_cells("A3:C3"); C(ws,"D3",f"={STRUCT_ETU}",CFB,fmt=EUR,align=AR,border=True)
C(ws,"E3","APRÈS :",CB,align=AR); ws.merge_cells("E3:F3"); C(ws,"G3",f"=IFERROR({STRUCT_TOT}/{EFF_AP},0)",CFB,FRISK,fmt=EUR,align=AR,border=True); ws.merge_cells("G3:H3")
C(ws,"I3","Effectif total APRÈS :",CB,align=AR); ws.merge_cells("I3:J3"); C(ws,"K3",f"={EFF_AP}",CFB,fmt=NB,align=AC,border=True)
C(ws,"M3","⚠ Fermer retire des étudiants → structure/étudiant ↑ (tous absorbent +). Ouvrir en capte → structure/étudiant ↓ (tous s'enrichissent). La structure totale ne bouge pas ; l'EBITDA groupe ne varie que des contributions.",CIT,align=ALW); ws.merge_cells("M3:Q3"); ws.row_dimensions[3].height=30
C(ws,"A4","🧪 BAC À SABLE : ces décisions montrent un impact SIMULÉ (encadré ci-dessus) — elles n'affectent PAS le budget officiel (feuilles 09_Allocation / 10_PnL / 13_Simulation), qui se pilote via les LEVIERS (feuille 02_Leviers).",CITB if False else Font(name=F,italic=True,bold=True,color="C00000"),align=AL); ws.merge_cells("A4:Q4"); ws.row_dimensions[4].height=16
for i,h in enumerate(sc): C(ws,f"{GL(1+i)}5",h,CHDR,FBLUE,align=AC,border=True)
ws.row_dimensions[5].height=34
# deux jeux de décisions : ENTRÉE (recrutement décidable) vs POURSUITE (cohorte déjà inscrite → seulement l'organisation des classes)
dv_ent=DataValidation(type="list",formula1='"Maintenir,Ne pas lancer,Ouvrir +1 classe,Regrouper (-1 classe)"',allow_blank=False); ws.add_data_validation(dv_ent)
dv_pou=DataValidation(type="list",formula1='"Maintenir,Regrouper (-1 classe)"',allow_blank=False); ws.add_data_validation(dv_pou)
for idx in range(N):
    r=DR0+idx; mr=MR0+idx; entry=rows[idx]["entry"]
    am=MO('AM')+str(mr); an=MO('AN')+str(mr); u=MO('U')+str(mr); ai=MO('AI')+str(mr); cap=MO('O')+str(mr)
    metu=f"({MO('AE')+str(mr)}*{MO('AF')+str(mr)}-({MO('R')+str(mr)}+{KAUTRES})*(1+{PINFL})-{MO('S')+str(mr)})"  # contribution marginale / étudiant capté
    C(ws,f"A{r}",f"={MO('A')+str(mr)}",CL,align=AL,border=True); C(ws,f"B{r}",f"={MO('B')+str(mr)}",CL,align=AC,border=True)
    C(ws,f"C{r}",f"={MO('C')+str(mr)}",CL,align=AL,border=True); C(ws,f"D{r}",f"={MO('D')+str(mr)}",CL,align=AC,border=True)
    C(ws,f"E{r}",f"={MO('AD')+str(mr)}",CL,fmt=NB,align=AC,border=True); C(ws,f"F{r}",f"={MO('AH')+str(mr)}",CL,fmt=EUR,align=AR,border=True)
    C(ws,f"G{r}",f"=F{r}-{am}",CF,fmt=EUR,align=AR,border=True)                       # coûts directs évitables
    C(ws,f"H{r}",f"={am}",CFB,FLIGHT,fmt=EUR,align=AR,border=True)                     # CONTRIBUTION (métrique de décision)
    C(ws,f"I{r}",f"={an}",CL,fmt=PCT,align=AC,border=True)
    if entry:  # année d'entrée : recrutement décidable
        reco=f'=IF(H{r}<0,"🔴 Ne pas lancer",IF(I{r}>=0.95,"🟢 Ouvrir +1 (capter+diluer)",IF(I{r}<0.55,"🟡 Surveiller","🟢 Maintenir")))'
        motif=f'=IF(H{r}<0,"Entrée à contribution négative → ne pas lancer cette cohorte",IF(I{r}>=0.95,"Saturé → ouvrir capte des étudiants ET dilue la structure pour tous",IF(I{r}<0.55,"Sous-rempli mais contribution positive → garder","Sain")))'
        dv=dv_ent
    else:      # année de poursuite : cohorte inscrite → seule l'organisation des classes est décidable
        reco=f'=IF(H{r}<0,"🔴 Restructurer (mutualiser)",IF(I{r}<0.55,"🟡 Regrouper les classes","🟢 Maintenir"))'
        motif=f'="Poursuite : cohorte déjà inscrite (issue de l\'année inférieure) → ni lancement ni capture ; seul levier = regrouper / mutualiser les classes"'
        dv=dv_pou
    C(ws,f"J{r}",reco,CF,align=AL,border=True)
    C(ws,f"K{r}",motif,CIT,align=ALW,border=True)
    C(ws,f"L{r}","Maintenir",CINB,FYEL,align=AC,border=True); dv.add(ws[f"L{r}"])
    C(ws,f"M{r}",f'=IF(L{r}="Ne pas lancer",0,IF(L{r}="Ouvrir +1 classe",E{r}+{cap},E{r}))',CF,fmt=NB,align=AC,border=True)   # effectif après
    C(ws,f"N{r}",f'=IF(L{r}="Ne pas lancer",0,IF(L{r}="Ouvrir +1 classe",H{r}+{cap}*{metu}-{u},IF(L{r}="Regrouper (-1 classe)",H{r}+({ai}-MAX(1,{ai}-1))*{u},H{r})))',CF,fmt=EUR,align=AR,border=True)  # contribution après
    C(ws,f"O{r}",f"=M{r}*IFERROR({STRUCT_TOT}/{EFF_AP},0)",CF,fmt=EUR,align=AR,border=True)   # structure allouée après (dilution symétrique)
    C(ws,f"P{r}",f"=N{r}-O{r}",CF,fmt=EUR,align=AR,border=True)                        # résultat tout compris après
    C(ws,f"Q{r}",f"=N{r}-H{r}",CFB,fmt=EUR,align=AR,border=True)                       # Δ EBITDA groupe (= Δ contribution)
ws.freeze_panes="E6"

# ============================================================ 12_Sensibilite
ws=wb.create_sheet("12_Sensibilite"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":40,"C":16,"D":44}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:D2"); C(ws,"B2","Sensibilité — impact € sur l'EBITDA par levier",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=26
ws.merge_cells("B3:D3"); C(ws,"B3","Sens unique : tes leviers → EBITDA. Approximations vivantes au point courant. Pour combler l'écart de cadrage, lis quel levier pèse le plus.",CIT)
for i,h in enumerate(["Levier (pas)","Impact EBITDA","Lecture"]): C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
scol=f"SUMPRODUCT({mrng('AD')}*{mrng('AE')}*{mrng('AF')})"
altn=f'SUMPRODUCT(({mrng("E")}="ALT")*{mrng("AD")}*{mrng("AE")})'
newc=f'SUMPRODUCT(({mrng("F")}=1)*{mrng("AM")})'
varm=f'SUMPRODUCT(({mrng("F")}=1)*{mrng("H")}*{mrng("S")}*(1+{mrng("Y")}))'
reinb=f'SUMPRODUCT(({mrng("F")}=0)*{mrng("K")})'
ctb_etu=f"IFERROR({msum('AM')}/{msum('AD')},0)"
rows_sens=[("+1 % de hausse tarifaire",f"=0.01*{scol}","Tombe quasi intégralement en EBITDA."),
 ("+1 point de sécurisation (≤3 mois)",f"=0.01*{altn}*(1-{KRECOUV})","Nul si recouvrement=100 % ; sinon réduit la perte."),
 ("+1 % de budget marketing",f"=0.01*{KELAST}*{newc}-0.01*{varm}","Plus de leads → plus d'inscrits, net du coût."),
 ("+1 point de taux de passage",f"=0.01*{reinb}*{ctb_etu}","Rétention : + d'étudiants qui poursuivent.")]
r=6
for lib,f2,lec in rows_sens:
    C(ws,f"B{r}",lib,CB,align=AL,border=True); C(ws,f"C{r}",f2,CF,fmt=EUR,align=AR,border=True); C(ws,f"D{r}",lec,CIT,align=ALW,border=True); ws.row_dimensions[r].height=26; r+=1
C(ws,f"B{r+1}","Exposition financement alternance (€ à sécuriser) :",CB,align=AR); ws.merge_cells(f"B{r+1}:C{r+1}")
C(ws,f"D{r+1}",f'=SUMPRODUCT(({mrng("E")}="ALT")*{mrng("AD")}*{mrng("AE")})*(1-{PSECU})',CFB,FRISK,fmt=EUR,align=AR)

# ============================================================ 13_Simulation
ws=wb.create_sheet("13_Simulation"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":30,"C":16,"D":16,"E":14}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:E2"); C(ws,"B2","Tableau de bord — simulation",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=24
C(ws,"B3","Scénario :",CB,align=AR); C(ws,"C3","='02_Leviers'!C3",CL,FYEL,align=AC,border=True)
for i,h in enumerate(["Indicateur","Budget","N-1","Évolution"]): C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
ebit=ALc('J'); ebn1=f"{n1_ctb}-{n1_loy}-{n1_perm}-{n1_str}"
altR=f'SUMPRODUCT(({mrng("E")}="ALT")*{mrng("AD")})'; altF=f'SUMPRODUCT(({mrng("E")}="ALT")*{mrng("G")})'
kp=[("Effectif total",f"={msum('AD')}",f"={n1_eff}",NB),("Chiffre d'affaires",f"={msum('AH')}",f"={n1_ca}",EUR),
 ("Marge de contribution",f"={msum('AM')}",f"={n1_ctb}",EUR),("EBITDA",f"={ebit}",f"={ebn1}",EUR),
 ("Marge EBITDA %",f"=IFERROR({ebit}/{msum('AH')},0)",f"=IFERROR(({ebn1})/{n1_ca},0)",PCT),
 ("Nombre de classes",f"={msum('AI')}",f"={msum('M')}",NB),("Nouveaux inscrits",f"={msum('AB')}",f"={msum('H')}",NB),
 ("Taux d'alternance",f"=IFERROR({altR}/{msum('AD')},0)",f"=IFERROR({altF}/{msum('G')},0)",PCT),
 ("Taux de sécurisation",f"={PSECU}",f"={KSECUN1}",PCT),
 ("€ à sécuriser (exposition)",f'=SUMPRODUCT(({mrng("E")}="ALT")*{mrng("AD")}*{mrng("AE")})*(1-{PSECU})',
   f'=SUMPRODUCT(({mrng("E")}="ALT")*{mrng("G")}*{mrng("L")})*(1-{KSECUN1})',EUR)]
r=6
for lib,bud,n1,fmt in kp:
    fill=FRISK if "sécuriser" in lib else None
    C(ws,f"B{r}",lib,CB,fill,align=AL,border=True); C(ws,f"C{r}",bud,CF,fill,fmt=fmt,align=AC,border=True); C(ws,f"D{r}",n1,CF,fill,fmt=fmt,align=AC,border=True)
    C(ws,f"E{r}",(f"=C{r}-D{r}" if fmt==PCT else f"=IFERROR(C{r}/D{r}-1,0)"),CF,fill,fmt=PCT,align=AC,border=True); r+=1

# ============================================================ 14_Mapping_Tagetik
ws=wb.create_sheet("14_Mapping_Tagetik"); ws.sheet_view.showGridLines=False
for c,w in {"A":2,"B":28,"C":28,"D":48}.items(): ws.column_dimensions[c].width=w
ws.merge_cells("B2:D2"); C(ws,"B2","Passerelle vers CCH Tagetik",CTIT,FNAVY,align=AL); ws.row_dimensions[2].height=24
band(ws,4,"B","D","Correspondance modèle → Tagetik")
for i,h in enumerate(["Concept","Objet Tagetik","Détail"]): C(ws,f"{GL(2+i)}5",h,CHDR,FBLUE,align=AC,border=True)
r=6
for a,b,c in [("Marque / Campus","Entity","Hiérarchie Groupe→Marque→Campus"),("Programme × Année × Modalité","Dimensions analytiques","Maille fine, attributs initial/alternance"),
 ("Params (capacité, heures…)","Attributs de dimension / driver","Données de référence par programme×année (feuille 05)"),
 ("Historique N-2/N-1","Category ACTUAL (multi-années)","Plus de profondeur = élasticité marketing robuste"),
 ("Cohortes / taux de passage","Règle de calcul","Progression B1→B2→B3"),("Sécurisation & recouvrement","Comptes techniques","Financement alternance, exposition"),
 ("Objectifs (cadrage)","Version cible + écart","Top-down vs bottom-up"),("Décisions ouvrir/fermer","Scénarios / versions","Simulateur → snapshot"),
 ("Allocation structure","Cost allocation (driver)","Effectif/CA/m²")]:
    C(ws,f"B{r}",a,CB,align=ALW,border=True); C(ws,f"C{r}",b,CREG,align=ALW,border=True); C(ws,f"D{r}",c,CREG,align=ALW,border=True); ws.row_dimensions[r].height=28; r+=1

# ============================================================ NOTES explicatives sur chaque entête (info-bulles)
from openpyxl.comments import Comment
def norm(s): return str(s).replace("\n"," ").replace("  "," ").strip()
GLOSS={
 # communs
 "Marque":"Marque / école du groupe (dimension Entity dans Tagetik).",
 "Marque / École":"Marque / école du groupe.",
 "Ville":"Campus (ville). Une entité = Marque + Ville.",
 "Programme":"Programme de formation (ex. Bachelor Management).",
 "Année":"Année d'études : B1/B2/B3 (Bachelor), M1/M2 (Mastère), 1/2 (BTS).",
 "Niveau":"Année d'études (B1, B2, B3, M1, M2…).",
 "Mod":"Modalité : INIT = initial (payé par la famille) · ALT = alternance (financé OPCO/NPEC).",
 "Mod.":"Modalité : INIT = initial · ALT = alternance (financée OPCO/NPEC).",
 "Modalité":"INIT = initial (famille) · ALT = alternance (OPCO/NPEC).",
 "Type":"Type de diplôme : BAC (Bachelor), MAST (Mastère), BTS.",
 "Domaine":"Domaine d'activité de la marque.",
 "Devise":"Devise de reporting.",
 # 05 Param_Prog_Annee
 "Clé (prog|année)":"Clé technique 'programme|année' pour relier les paramètres au moteur.",
 "Capacité":"Capacité cible d'une classe (nb d'étudiants).","Capacité cible":"Capacité cible par classe.",
 "Seuil ouverture":"Seuil historique d'ouverture (indicatif ; le point mort réel est calculé dans le moteur).",
 "Heures / classe":"Heures d'enseignement délivrées par classe et par an.",
 "Taux horaire":"Coût horaire chargé de l'enseignement (vacation), en €.",
 "Coût pédago / étu":"Coût pédagogique variable par étudiant (supports, plateforme, examens), en €.",
 "CAC variable":"Coût d'acquisition variable (achat de leads) par nouvel inscrit. N'existe qu'en année d'entrée.",
 "Taux de passage":"Taux de progression de l'année inférieure vers celle-ci (réinscription). Vide en année d'entrée.",
 # 06 Historique
 "Entrée":"1 = année d'entrée (on recrute) · 0 = année de poursuite (cohorte progressée).",
 "Candidatures N-1":"Candidatures reçues l'an dernier (haut de l'entonnoir admissions).",
 "Cand N-1":"Candidatures l'an dernier.","Cand Bud":"Candidatures budget = candidatures N-1 × (1 + élasticité × effort marketing).",
 "Nouv N-1":"Nouveaux inscrits l'an dernier (entrants).","Nouv Bud":"Nouveaux inscrits budget = candidatures budget × taux de conversion.",
 "Réins N-1":"Réinscrits l'an dernier (étudiants qui poursuivent).","Réins Bud":"Réinscrits budget = effectif de l'année inférieure (N-1) × (taux de passage + amélioration).",
 "Effectif N-1":"Effectif réel l'an dernier.","Eff N-1":"Effectif réel l'an dernier.",
 "Eff. année inf. N-1":"Effectif de l'année juste inférieure l'an dernier — base de la cohorte pour calculer la progression.",
 "EffInf N-1":"Effectif de l'année inférieure l'an dernier (base de progression de la cohorte).",
 "Tarif N-1":"Tarif moyen l'an dernier (€/étudiant/an).","Tarif Bud":"Tarif budget = tarif N-1 × (1 + hausse prix × coefficient marque).",
 "Classes N-1":"Nombre de classes l'an dernier.","Cl N-1":"Nombre de classes l'an dernier.",
 "Élasticité mesurée":"Élasticité marketing = %Δ candidatures ÷ %Δ marketing, mesurée sur N-2/N-1.",
 "Sécurisation N-1":"Part des alternants dont le contrat a été sécurisé dans les 3 mois l'an dernier (financement OPCO à 100 %).",
 # 07 Structure
 "Effectif N-1 ":"Effectif réel l'an dernier.","CA N-1":"Chiffre d'affaires réel l'an dernier.",
 "Contribution N-1":"Marge de contribution réelle l'an dernier (CA − coûts directs).",
 "Loyer N-1":"Loyer du campus l'an dernier (coût de structure, fixe).",
 "ETP perm.":"Effectifs permanents (équivalent temps plein) du campus.",
 "Masse perm. N-1":"Masse salariale permanente = ETP × coût chargé par ETP.",
 "D&A N-1":"Dotations aux amortissements l'an dernier.","Surface m²":"Surface du campus (utilisée comme driver d'allocation possible).",
 "EBITDA campus N-1":"EBITDA du campus = contribution − loyer − masse salariale permanente.",
 # 08 Moteur
 "clé":"Clé programme|année pour retrouver les paramètres (feuille 05).",
 "Cap":"Capacité cible par classe (lue dans 05).","Heures":"Heures d'enseignement par classe/an (05).",
 "Taux":"Taux horaire chargé de l'enseignement (05).","Pédago":"Coût pédagogique par étudiant (05).",
 "CACvar":"Coût d'acquisition variable par nouvel inscrit (05).",
 "Passage":"Taux de passage de l'année inférieure (05). 0 en année d'entrée.",
 "Coût/cl":"Coût d'une classe = heures × taux horaire × (1 + politique salariale).",
 "cMkt":"Coefficient stratégique MARKETING de la marque (feuille 03) — module l'effort par marque.",
 "cPrix":"Coefficient stratégique PRIX de la marque (feuille 03) — module la hausse tarifaire par marque.",
 "Élast":"Élasticité marketing mesurée (06). Repli si historique manquant.",
 "Effort":"Effort marketing appliqué = levier 'variation budget marketing' × coefficient marque.",
 "Conv":"Taux de conversion candidature→inscrit (mesuré par cellule) + gain du levier conversion.",
 "Effectif Bud":"Effectif budget = nouveaux + réinscrits.",
 "SecFac":"Facteur de financement alternance BUDGET (sécurisation + reste à charge recouvré). = 1 en initial.",
 "SecN-1":"Facteur de financement alternance N-1 (référence pour le pont).",
 "CA Bud":"CA budget = effectif × tarif × facteur financement + frais de dossier.",
 "Cl besoin":"Classes nécessaires = arrondi supérieur (effectif / capacité).",
 "Enseign":"Coût d'enseignement = classes × coût par classe.",
 "Pédago€":"Coût pédagogique = effectif × coût pédago/étudiant × (1 + inflation).",
 "Mktg":"Marketing = nouveaux × CAC variable × (1 + effort). = 0 en année de poursuite.",
 "Contrib":"MARGE DE CONTRIBUTION = CA − enseignement − pédago − marketing − autres charges.",
 "Rempl":"Taux de remplissage = effectif / (classes × capacité).",
 "Rempl.":"Taux de remplissage = effectif / (classes × capacité).",
 "Contr/étu":"Contribution par étudiant.","Pt mort":"Point mort = nb d'étudiants pour couvrir le coût des classes.",
 # 09 Allocation
 "Contribution":"Marge de contribution (CA − coûts directs évitables).",
 "Loyer":"Loyer du campus (structure fixe).","Masse perm.":"Masse salariale permanente (structure fixe).",
 "Driver":"Valeur du driver d'allocation (effectif, CA ou m² selon 02_Leviers).",
 "Part":"Part du campus dans le driver total.","Alloué":"Frais de structure groupe alloués à ce campus.",
 "EBITDA campus":"EBITDA du campus = contribution − loyer − permanents − structure allouée.",
 "D&A":"Dotations aux amortissements.","EBIT":"Résultat d'exploitation = EBITDA − D&A.","EBIT campus":"EBIT du campus = EBITDA campus − D&A.",
 # 10 PnL
 "Rubrique":"Ligne du compte de résultat.","Réalisé N-1":"Valeur réelle de l'an dernier.","Budget N+1":"Valeur budgétée.",
 "Écart €":"Budget − Réalisé (en €).","Écart %":"Variation en % vs l'an dernier.","Effet":"Composante du pont de passage.","Montant":"Montant de l'effet (en €).",
 # 11 Simulateur
 "Effectif":"Effectif budget de la promo.","CA":"Chiffre d'affaires budget de la promo.",
 "Coûts directs évitables":"Coûts qui DISPARAISSENT si on ferme la promo (enseignement, pédago, marketing, autres variables).",
 "MARGE DE CONTRIBUTION":"CA − coûts directs évitables. C'est LA métrique de décision : on ne ferme que si elle est négative.",
 "Structure allouée (après, dilution)":"Quote-part de structure fixe (loyer, permanents, siège) portée par la promo, RECALCULÉE après décisions : moins d'étudiants au total → chacun en porte plus (dilution).",
 "Résultat tout compris (après)":"Contribution après − structure allouée. Vue INFORMATIVE — surtout PAS un critère de fermeture.",
 "🤖 Reco":"Recommandation automatique (contribution + remplissage). Dépend de l'année : entrée (lancer/capter) vs poursuite (regrouper).",
 "Motif":"Explication de la recommandation.","Décision":"Ton choix. Menu restreint selon l'année : entrée = lancer/capter ; poursuite = seulement regrouper.",
 "Effectif après":"Effectif après ta décision (0 si 'ne pas lancer' ; +1 classe captée si 'ouvrir').",
 "Contribution après":"Contribution recalculée selon ta décision.",
 "Δ EBITDA":"Impact sur l'EBITDA groupe = contribution après − contribution avant.",
 # 12 Sensibilite
 "Levier (pas)":"Levier testé et son incrément.","Impact EBITDA":"Effet € sur l'EBITDA d'un pas du levier (approximation vivante).","Lecture":"Interprétation.",
 # 13 Simulation
 "Indicateur":"Indicateur de pilotage.","Budget":"Valeur budgétée.","N-1":"Valeur réelle de l'an dernier.","Évolution":"Variation Budget vs N-1.",
 # 03 Coeff
 "Intensité MARKETING":"Coefficient appliqué à l'effort marketing du cadrage pour cette marque (>1 = on pousse).",
 "Intensité PRIX":"Coefficient appliqué à la hausse tarifaire du cadrage pour cette marque.","Posture":"Lecture du positionnement (pousser / défendre / maintenir).",
 # 01 Objectifs
 "Cible (direction)":"Objectif fixé par la direction (saisie).","Budget construit":"Résultat du budget construit par les drivers (moteur).","Écart":"Budget construit − cible.",
}
GLOSS={norm(k):v for k,v in GLOSS.items()}
HEADER_ROW={"01_Objectifs":5,"03_Coeff_Strateg":5,"04_Referentiel":5,"05_Param_Prog_Annee":3,"06_Historique":3,
 "07_Structure":3,"08_Moteur":2,"09_Allocation":5,"10_PnL":5,"11_Simulateur":5,"12_Sensibilite":5,"13_Simulation":5,"14_Mapping_Tagetik":5}
def add_note(cell,text):
    cm=Comment(text,"Guide"); cm.width=300; cm.height=120; cell.comment=cm
for shname,hr in HEADER_ROW.items():
    ws=wb[shname]
    for col in range(1,46):
        cell=ws.cell(row=hr,column=col)
        if cell.value is not None:
            key=norm(cell.value)
            if key in GLOSS: add_note(cell,GLOSS[key])
# 02_Leviers : notes sur chaque levier et constante (colonne B) + entêtes scénarios
ws=wb["02_Leviers"]
lev_notes={6:"Croissance du budget d'acquisition → pilote le volume via l'élasticité mesurée.",
 7:"Hausse tarifaire moyenne, modulée par marque (coeff prix).",
 8:"Points de conversion candidature→inscrit gagnés (pilotage admissions).",
 9:"Part des contrats d'alternance sécurisés dans les 3 mois → financement OPCO à 100 %.",
 10:"Amélioration du taux de passage (réinscription) vs l'historique.",
 11:"Inflation appliquée aux charges (pédago, loyers, autres).",
 12:"Revalorisation des rémunérations chargées (permanents + enseignement)."}
for rr,tx in lev_notes.items(): add_note(ws.cell(row=rr,column=2),tx)
for col,tx in {"D":"Valeurs du scénario Cadrage (central).","E":"Valeurs du scénario Optimiste.","F":"Valeurs du scénario Prudent.","G":"Valeur ACTIVE = celle du scénario sélectionné en C3."}.items():
    add_note(ws[f"{col}5"],tx)
add_note(ws["C3"],"Scénario actif : change cette cellule et TOUT le budget se recalcule.")

try: wb.calculation.fullCalcOnLoad=True
except Exception:
    from openpyxl.workbook.properties import CalcProperties; wb.calculation=CalcProperties(fullCalcOnLoad=True)
wb.save(OUT); print("TOUTES LES FEUILLES OK (avec notes d'entêtes)")
