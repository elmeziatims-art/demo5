#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apercu demo-grade du Pilotage reorganise (vraies valeurs)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import replica as R
import numpy as np

# ---- campus (replique) ----
inp=R.base_inputs(); lev=inp["lev"]; pcoef=inp["pcoef"]; cap=inp["cap"]; budref=inp["budref"]
PILF=[p['F'] for p in R.PIL]
sN=sum(budref[e] for e in PILF); sp=sum(budref[e]*cap[e] for e in PILF)
rejoue={e:budref[e]*cap[e]*(sN/sp) for e in PILF}
CAMP=[("MBWAY_PAR","MBway","Paris"),("MBWAY_LYO","MBway","Lyon"),("MBWAY_NAN","MBway","Nantes"),
 ("MBWAY_BOR","MBway","Bordeaux"),("ISCOM_PAR","ISCOM","Paris"),("ISCOM_LIL","ISCOM","Lille"),
 ("ISCOM_TLS","ISCOM","Toulouse"),("IPAC_NAN","Ipac","Nantes"),("IPAC_REN","Ipac","Rennes"),
 ("IPAC_MTP","Ipac","Montpellier"),("PIGIER_LYO","Pigier","Lyon"),("PIGIER_BOR","Pigier","Bordeaux"),
 ("TUNON_PAR","Tunon","Paris"),("TUNON_LYO","Tunon","Lyon")]
ca_c={c[0]:0.0 for c in CAMP}; eff_c={c[0]:0.0 for c in CAMP}
for m in R.MOT:
    if m['B']!="V01": continue
    ent,mrq,prog,an,mod=m['D'],m['E'],m['F'],m['G'],m['H']
    G=R.socsum(ent,prog,an,mod,"H");H=R.socsum(ent,prog,an,mod,"N");I=R.socsum(ent,prog,an,mod,"P")
    J=R.socsum(ent,prog,an,mod,"W");K=R.socsum(ent,prog,an,mod,"X");L=R.socsum(ent,prog,an,mod,"Y")
    PSG=R.socsum(ent,prog,an,mod,"V");c=R.CAM.get(ent,{})
    O=c.get("D",0)or 0;P=c.get("E",0)or 0;Q=c.get("F",0)or 0;Rr=c.get("K",0)or 0;Sr=c.get("M",0)or 0
    T=rejoue.get(ent,0);U=budref.get(ent,0)
    ACQ,BRAND,PRICE,GLC,GCV,PASS,FEE=(lev[x][0] for x in("ACQ","BRAND","PRICE","GLC","GCV","PASS","FEE"))
    PC=pcoef.get(mrq,pcoef["TUNON"]);entry=1 if an in R.ENTRY else 0
    ba=((T/U)*(1+ACQ)) if U else 0
    nouv=(O*(1+BRAND)**Sr+P*(ba**Rr))*((G/Q)if Q else 0)*(J+GLC)*K*(L+GCV)
    eff=nouv if entry else H*(PSG+PASS);nx=nouv if entry else 0
    if ent in ca_c: ca_c[ent]+=eff*(I*(1+PRICE*PC))+nx*FEE; eff_c[ent]+=eff
prod26=sum(v for(e,a,ex),v in R.CPTI.items() if a in R.PROD and ex=="2026")
caf=sum(ca_c.values())/prod26
def fac(a):
    ACQ,BRAND,INFL,SAL,FTE,PROD_,STR=(lev[x][0] for x in("ACQ","BRAND","INFL","SAL","FTE","PROD","STRUCT"))
    if a in R.PROD:return caf
    return {"6231":1+ACQ,"6236":1+BRAND}.get(a) or (caf*(1-PROD_) if a in("621","604","6063") else
      (1+SAL)*(1+FTE) if a in("6411","6413","6414","645") else
      (1+INFL)*(1-PROD_)*(1+STR) if a in("613","615","616","6226","625","626","6281") else
      (1+INFL)*(1-PROD_) if a in("6331","63511","6333") else (1+INFL) if a=="6811" else 1.0)
ea={}
for(e,a,ex),v in R.CPTI.items():
    if ex=="2026":ea[(e,a)]=ea.get((e,a),0)+v
eb_c={c[0]:0.0 for c in CAMP};grp=0.0
for(e,a),v in ea.items():
    amt=v*fac(a);sgn=amt if a in R.PROD else(-amt if(a.startswith("6")and a!="6811")else 0)
    if e in eb_c:eb_c[e]+=sgn
    elif e=="GRP":grp+=sgn
CA=sum(ca_c.values());EB=sum(eb_c.values())+grp;EF=sum(eff_c.values())
cac={R.PIL[i]['F']:R.CAM.get(R.PIL[i]['F'],{}).get('N',0) for i in range(14)}
import openpyxl
_p=openpyxl.load_workbook("CAD_SAAD_LIVE.xlsx",data_only=True)["Pilotage"]
cacv={_p["F%d"%r].value:_p["G%d"%r].value for r in range(13,27)}

# ---- 2026 allocation per marque (stored) ----
ALLOC={"MBway":[603646,1528197,631277,3627661,1514315,1662359],
 "ISCOM":[422552,1058481,416570,2418520,995970,980457],
 "Ipac":[217314,412435,192895,876763,408800,474593],
 "Pigier":[193166,432359,179140,895232,340648,111675],
 "Tunon":[144876,409445,143974,880365,308594,62446]}
MK={"MBway":"#2E75B6","ISCOM":"#548235","Ipac":"#BF8F00","Pigier":"#843C0C","Tunon":"#7030A0"}
order=["MBway","ISCOM","Ipac","Pigier","Tunon"]

fig=plt.figure(figsize=(20,15)); fig.patch.set_facecolor("white")
gs=fig.add_gridspec(4,3,height_ratios=[0.5,1,1,1.05],hspace=0.5,wspace=0.26)

# --- KPI band ---
axk=fig.add_subplot(gs[0,:]); axk.axis("off"); axk.set_xlim(0,5); axk.set_ylim(0,1)
kpis=[("CA 2027","{:,.0f} EUR".format(CA).replace(",", " "),"#2E75B6"),
      ("EBITDA (apres siege)","{:,.0f} EUR".format(EB).replace(",", " "),"#548235"),
      ("Marge EBITDA","%.1f%%"%(EB/CA*100),"#1F3864"),
      ("Effectif","{:,.0f}".format(EF).replace(",", " "),"#3B3B3B"),
      ("Croissance CA vs 2026","+%.1f%%"%((CA/22544725-1)*100),"#BF8F00")]
for i,(lab,val,col) in enumerate(kpis):
    axk.add_patch(FancyBboxPatch((i+0.04,0.05),0.92,0.9,boxstyle="round,pad=0.02",
                  facecolor="white",edgecolor=col,lw=2))
    axk.add_patch(FancyBboxPatch((i+0.04,0.72),0.92,0.28,boxstyle="round,pad=0.02",facecolor=col,edgecolor=col))
    axk.text(i+0.5,0.86,lab,color="white",fontsize=9.5,fontweight="bold",ha="center",va="center")
    axk.text(i+0.5,0.38,val,color=col,fontsize=15,fontweight="bold",ha="center",va="center")
fig.text(0.5,0.965,"PILOTAGE · Cockpit de decision CFO — Budget 2027 (scenario V01, live)",
         fontsize=17,fontweight="bold",color="#1F3864",ha="center")

codes=[c[0] for c in CAMP]; labs=[c[1]+"\n"+c[2] for c in CAMP]
BR=[budref[c] for c in codes]; RJ=[rejoue[c] for c in codes]; CCv=[cacv[c] for c in codes]
CAc=[ca_c[c] for c in codes]; EBc=[eb_c[c] for c in codes]

# --- 1. Cap combo ---
ax=fig.add_subplot(gs[1,:2]); x=np.arange(len(codes)); w=0.4
ax.bar(x-w/2,[v/1000 for v in BR],w,label="Budget ref (k EUR)",color="#BDD7EE")
ax.bar(x+w/2,[v/1000 for v in RJ],w,label="Budget rejoue (k EUR)",color="#2E75B6")
ax.set_xticks(x); ax.set_xticklabels(labs,fontsize=7.5); ax.legend(fontsize=9,loc="upper right")
ax.set_title("1 · Cap strategique : budget d'acquisition reference -> rejoue",fontsize=12,fontweight="bold",color="#1F3864")
ax2=ax.twinx(); ax2.plot(x,CCv,"o-",color="#C00000",lw=1.5,label="CAC marginal")
ax2.set_ylabel("CAC (EUR)",color="#C00000"); ax2.legend(fontsize=9,loc="upper left"); ax.grid(axis="y",alpha=0.3)

# --- donut poids marque CA ---
ax=fig.add_subplot(gs[1,2])
mca={}
for c in CAMP: mca[c[1]]=mca.get(c[1],0)+ca_c[c[0]]
ax.pie([mca[m] for m in order],labels=order,autopct="%1.0f%%",colors=[MK[m] for m in order],
       wedgeprops=dict(width=0.42,edgecolor="white"),textprops=dict(fontsize=9))
ax.set_title("Poids marques · CA 2027",fontsize=12,fontweight="bold",color="#1F3864")

# --- 2. synthese CA&EBITDA campus ---
ax=fig.add_subplot(gs[2,:2])
ax.bar(x-w/2,[v/1000 for v in CAc],w,label="CA (k)",color="#2E75B6")
ax.bar(x+w/2,[v/1000 for v in EBc],w,label="EBITDA campus (k)",color="#548235")
ax.set_xticks(x); ax.set_xticklabels(labs,fontsize=7.5); ax.legend(fontsize=9)
ax.set_title("2 · Synthese par campus : CA & EBITDA (avant siege)",fontsize=12,fontweight="bold",color="#1F3864")
ax.grid(axis="y",alpha=0.3)

# --- EBITDA/etud ---
ax=fig.add_subplot(gs[2,2])
ebe=[eb_c[c]/eff_c[c] for c in codes]
ax.barh(range(len(codes)),ebe,color=[MK[c[1]] for c in CAMP]); ax.set_yticks(range(len(codes)))
ax.set_yticklabels([c[1][:4]+" "+c[2][:3] for c in CAMP],fontsize=7); ax.invert_yaxis()
ax.set_title("EBITDA / etudiant (EUR)",fontsize=12,fontweight="bold",color="#1F3864"); ax.grid(axis="x",alpha=0.3)

# --- 3. allocation : marge complete par marque (effet cles) ---
ax=fig.add_subplot(gs[3,0])
mg=[ALLOC[m][5] for m in order]
ax.bar(order,[v/1000 for v in mg],color=[MK[m] for m in order])
for i,m in enumerate(order): ax.text(i,mg[i]/1000+15,"%.0fk"%(mg[i]/1000),ha="center",fontsize=8,fontweight="bold")
ax.set_title("3 · Marge complete par marque\n(2026, apres siege — REAGIT aux cles)",fontsize=11,fontweight="bold",color="#843C0C")
ax.set_ylabel("k EUR"); ax.grid(axis="y",alpha=0.3)

# --- decomposition cout complet stacked ---
ax=fig.add_subplot(gs[3,1])
labels5=["VAC","PERM","ODIR","STRUCT","SIEGE"]; cols5=["#9DC3E6","#A9D18E","#FFD966","#F4B183","#C00000"]
bottom=np.zeros(len(order))
for j,lab in enumerate(labels5):
    vals=np.array([ALLOC[m][j]/1000 for m in order])
    ax.bar(order,vals,bottom=bottom,label=lab,color=cols5[j]); bottom+=vals
ax.set_title("Decomposition du cout complet par marque",fontsize=11,fontweight="bold",color="#843C0C")
ax.set_ylabel("k EUR"); ax.legend(fontsize=8,ncol=2); ax.grid(axis="y",alpha=0.3)

# --- marge% avant/apres siege ---
ax=fig.add_subplot(gs[3,2])
before=[mca[m]and (sum(eb_c[c[0]] for c in CAMP if c[1]==m)/mca[m]*100) for m in order]
after=[ALLOC[m][5]/ (ALLOC[m][5]+sum(ALLOC[m][:5]))*100 for m in order]
xx=np.arange(len(order))
ax.bar(xx-0.2,before,0.4,label="avant siege (2027)",color="#A9D18E")
ax.bar(xx+0.2,after,0.4,label="apres siege (2026)",color="#843C0C")
ax.set_xticks(xx); ax.set_xticklabels(order,fontsize=9); ax.legend(fontsize=8)
ax.set_title("Marge % avant / apres allocation siege",fontsize=11,fontweight="bold",color="#843C0C")
ax.set_ylabel("%"); ax.grid(axis="y",alpha=0.3)

plt.savefig("/tmp/cockpit.png",dpi=95,bbox_inches="tight",facecolor="white")
print("wrote /tmp/cockpit.png  CA=%.0f EBITDA=%.0f EFF=%.0f"%(CA,EB,EF))
