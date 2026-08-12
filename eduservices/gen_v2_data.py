# -*- coding: utf-8 -*-
"""Socle de données v2 : cohortes + historique marketing N-2/N-1 + params programme×année.
Ce module teste la génération du modèle de données avant d'y brancher les feuilles Excel."""
import math

# ---- référentiel ----
BRANDS={  # marque -> (domaine, coeff_vol, coeff_prix, base_entry, [villes])
 "MBway":("Management",1.20,1.00,60,["Paris","Lyon","Nantes","Bordeaux"]),
 "ISCOM":("Communication",1.00,1.20,55,["Paris","Lille","Toulouse"]),
 "Ipac Bachelor Factory":("Commerce",1.30,0.80,50,["Nantes","Rennes","Montpellier"]),
 "Pigier":("Commerce/RH",0.70,1.00,42,["Lyon","Bordeaux"]),
 "Tunon":("Tourisme",1.00,1.10,36,["Paris","Lyon"]),
}
CITY={"Paris":1.30,"Lyon":1.10,"Nantes":1.00,"Bordeaux":0.85,"Lille":0.90,"Toulouse":0.85,"Rennes":0.80,"Montpellier":0.80}
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

# ---- paramètres opérationnels PAR PROGRAMME × ANNÉE ----
def op_params(prog, ptype, niveau, domaine):
    heures={"BTS":{"1":720,"2":680},"BAC":{"B1":600,"B2":560,"B3":520},"MAST":{"M1":480,"M2":440}}[ptype][niveau]
    cap  ={"BTS":{"1":30,"2":30},"BAC":{"B1":34,"B2":32,"B3":30},"MAST":{"M1":26,"M2":24}}[ptype][niveau]
    taux =55 if ptype=="BTS" else (70 if ptype=="MAST" else 58)
    if domaine=="Communication": taux+=4
    if domaine=="Tourisme": taux-=2
    ped ={"Management":400,"Communication":550,"Commerce":380,"Commerce/RH":380,"Tourisme":450}.get(domaine,400)
    if ptype=="BTS": ped=350
    if ptype=="MAST": ped+=120
    cacv=({"BTS":250,"BAC":320,"MAST":600}[ptype]) if niveau in ENTRY else 0  # CAC variable (leads) : seulement en année d'ENTRÉE (on ne recrute pas en poursuite)
    passage=0 if niveau in ENTRY else {"B2":0.85,"B3":0.90,"M2":0.92,"2":0.90}[niveau]
    return dict(cap=cap,heures=heures,taux=taux,pedago=ped,cacv=cacv,passage=passage)

def tarif(t,mod):
    if t=="BTS":  return 7000 if mod=="ALT" else 6500
    if t=="MAST": return 9000 if mod=="ALT" else 9500
    return 8000 if mod=="ALT" else 8500

def lvl_factor(t,niv):
    return {"BAC":{"B1":1.00,"B2":0.85,"B3":0.75},"MAST":{"M1":0.60,"M2":0.54},"BTS":{"1":0.80,"2":0.70}}[t][niv]

# constantes calibrées sur les COMPTES CONSOLIDÉS EDUSERVICES 4.0 (CA 345,8M€, EBITDA 14,6%, D&A 6%)
CAP_D,HRS_D,TXH_D,PEDA_D,ETPC,FRAIS,DA_PCT=30,550,60,400,58000,90,0.06  # ETP chargé 58 k€ ; D&A 6% du CA (réel)
CONV_N1,ADM_N1=0.372,0.62
AUTRES_ETU=934   # autres charges d'exploitation / étudiant (achats pédago, sous-traitance, IT, missions, honoraires) -> cale l'EBITDA à 14,6% et les achats/autres à ~11% du CA (réel)
STRUCT_FIXE=2000000   # frais de structure & marketing groupe : montant FIXE (siège, IT, marque, équipe centrale)
SECU_N1,RECOUV=0.86,1.00
ELAST_DEF=0.5    # élasticité marketing par défaut (repli si historique mince)
# taux de sécurisation ≤3 mois N-1, mesuré PAR PROGRAMME (issu de l'historique)
def secu_prog(dom): return {"Management":0.88,"Communication":0.85,"Commerce":0.87,"Commerce/RH":0.84,"Tourisme":0.83}.get(dom,SECU_N1)

def sf(mod,secu,recouv=RECOUV): return 1.0 if mod!="ALT" else secu+(1-secu)*recouv

# ---- génération des cellules avec cohortes ----
rows=[]
for marque,(dom,cv,cp,base,villes) in BRANDS.items():
    for ville in villes:
        for pnom,ptype,niveaux in PROGS[marque]:
            entry=round(base*CITY[ville])
            eff_by_niv={}
            for niv,mod in niveaux:
                eff=max(0,round(entry*lvl_factor(ptype,niv))); eff_by_niv[niv]=eff
            for niv,mod in niveaux:
                eff=eff_by_niv[niv]; op=op_params(pnom,ptype,niv,dom)
                is_entry=1 if niv in ENTRY else 0
                if is_entry:
                    nouv=eff; rein=0; cand=round(nouv/CONV_N1); admis=round(cand*ADM_N1)
                    eff_prev=0
                else:
                    order=ORDER[ptype]; prev=order[order.index(niv)-1]
                    eff_prev=eff_by_niv.get(prev,0)
                    rein=eff; nouv=0; cand=0; admis=0
                rows.append(dict(marque=marque,ville=ville,prog=pnom,type=ptype,niv=niv,mod=mod,
                    entry=is_entry,eff=eff,nouv=nouv,rein=rein,cand=cand,admis=admis,eff_prev=eff_prev,
                    tarif=tarif(ptype,mod),classes=max(1,math.ceil(eff/op["cap"])) if eff>0 else 0,**op))
N=len(rows)

# ---- historique marketing par PROGRAMME (N-2, N-1) pour élasticité mesurée ----
prog_list=[]
for m,(dom,cv,cp,base,villes) in BRANDS.items():
    for pnom,ptype,niveaux in PROGS[m]:
        if (m,pnom) not in [(x[0],x[1]) for x in prog_list]:
            prog_list.append((m,pnom,ptype,dom))
mkt_hist={}
for (m,pnom,ptype,dom) in prog_list:
    cells=[r for r in rows if r["marque"]==m and r["prog"]==pnom and r["entry"]==1]
    cand_n1=sum(c["cand"] for c in cells)
    mkt_n1=sum(c["nouv"]*c["cacv"] for c in cells)
    # N-2 : légèrement plus bas (candidatures +5% et marketing +10% entre N-2 et N-1 -> élasticité 0,5)
    cand_n2=round(cand_n1/1.05); mkt_n2=round(mkt_n1/1.10)
    mkt_hist[(m,pnom)]=dict(cand_n1=cand_n1,cand_n2=cand_n2,mkt_n1=round(mkt_n1),mkt_n2=mkt_n2)

if __name__=="__main__":
    print(f"cellules N={N}  programmes={len(prog_list)}")
    tot_eff=sum(r["eff"] for r in rows); tot_alt=sum(r["eff"] for r in rows if r["mod"]=="ALT")
    print(f"effectif total={tot_eff}  alternance={tot_alt/tot_eff*100:.0f}%")
    # exemple cohorte
    ex=[r for r in rows if r["marque"]=="MBway" and r["ville"]=="Paris" and r["prog"]=="Bachelor Management"]
    for r in ex: print(f"  {r['niv']:3} {r['mod']:4} eff={r['eff']:4} entry={r['entry']} rein={r['rein']} eff_prev={r['eff_prev']} passage={r['passage']} cap={r['cap']} heures={r['heures']}")
    # élasticité mesurée exemple
    for k in list(mkt_hist)[:3]:
        h=mkt_hist[k];
        el=((h['cand_n1']/h['cand_n2'])-1)/((h['mkt_n1']/h['mkt_n2'])-1)
        print(f"  élasticité {k[1]}: {el:.2f}  (cand {h['cand_n2']}->{h['cand_n1']}, mkt {h['mkt_n2']}->{h['mkt_n1']})")
