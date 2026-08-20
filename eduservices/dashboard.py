#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apercu 'aide a la decision' du cockpit Pilotage, avec les vrais chiffres
(replique prouvee) : synthese par campus + 4 graphes CFO."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import openpyxl, importlib.util

# --- charge la logique per-campus depuis validate_synth (reutilise replica) ---
import replica as R
inp=R.base_inputs(); lev=inp["lev"]; pcoef=inp["pcoef"]; cap=inp["cap"]; budref=inp["budref"]
PILF=[p['F'] for p in R.PIL]
sN=sum(budref[e] for e in PILF); sp=sum(budref[e]*cap[e] for e in PILF)
rejoue={e:budref[e]*cap[e]*(sN/sp) for e in PILF}
CAMPUS=[("MBWAY_PAR","MBway","Paris"),("MBWAY_LYO","MBway","Lyon"),("MBWAY_NAN","MBway","Nantes"),
 ("MBWAY_BOR","MBway","Bordeaux"),("ISCOM_PAR","ISCOM","Paris"),("ISCOM_LIL","ISCOM","Lille"),
 ("ISCOM_TLS","ISCOM","Toulouse"),("IPAC_NAN","Ipac","Nantes"),("IPAC_REN","Ipac","Rennes"),
 ("IPAC_MTP","Ipac","Montpellier"),("PIGIER_LYO","Pigier","Lyon"),("PIGIER_BOR","Pigier","Bordeaux"),
 ("TUNON_PAR","Tunon","Paris"),("TUNON_LYO","Tunon","Lyon")]
ca_c={c[0]:0.0 for c in CAMPUS}; eff_c={c[0]:0.0 for c in CAMPUS}
for m in R.MOT:
    if m['B']!="V01": continue
    ent,mrq,prog,an,mod=m['D'],m['E'],m['F'],m['G'],m['H']
    G=R.socsum(ent,prog,an,mod,"H");H=R.socsum(ent,prog,an,mod,"N");I=R.socsum(ent,prog,an,mod,"P")
    J=R.socsum(ent,prog,an,mod,"W");K=R.socsum(ent,prog,an,mod,"X");L=R.socsum(ent,prog,an,mod,"Y")
    PSG=R.socsum(ent,prog,an,mod,"V");c=R.CAM.get(ent,{})
    O=c.get("D",0) or 0;P=c.get("E",0) or 0;Q=c.get("F",0) or 0;Rr=c.get("K",0) or 0;Sr=c.get("M",0) or 0
    T=rejoue.get(ent,0);U=budref.get(ent,0)
    ACQ,BRAND,PRICE,GLC,GCV,PASS,FEE=(lev[x][0] for x in("ACQ","BRAND","PRICE","GLC","GCV","PASS","FEE"))
    PC=pcoef.get(mrq,pcoef["TUNON"]);entry=1 if an in R.ENTRY else 0
    ba=((T/U)*(1+ACQ)) if U else 0
    nouv=(O*(1+BRAND)**Sr+P*(ba**Rr))*((G/Q) if Q else 0)*(J+GLC)*K*(L+GCV)
    eff=nouv if entry else H*(PSG+PASS);nx=nouv if entry else 0
    if ent in ca_c: ca_c[ent]+=eff*(I*(1+PRICE*PC))+nx*FEE; eff_c[ent]+=eff
prod26=sum(v for (e,a,ex),v in R.CPTI.items() if a in R.PROD and ex=="2026")
caf=sum(ca_c.values())/prod26
def fac(a):
    ACQ,BRAND,INFL,SAL,FTE,PROD_,STR=(lev[x][0] for x in("ACQ","BRAND","INFL","SAL","FTE","PROD","STRUCT"))
    if a in R.PROD: return caf
    return {"6231":1+ACQ,"6236":1+BRAND}.get(a) or (
        caf*(1-PROD_) if a in("621","604","6063") else
        (1+SAL)*(1+FTE) if a in("6411","6413","6414","645") else
        (1+INFL)*(1-PROD_)*(1+STR) if a in("613","615","616","6226","625","626","6281") else
        (1+INFL)*(1-PROD_) if a in("6331","63511","6333") else
        (1+INFL) if a=="6811" else 1.0)
ea={}
for (e,a,ex),v in R.CPTI.items():
    if ex=="2026": ea[(e,a)]=ea.get((e,a),0)+v
eb_c={c[0]:0.0 for c in CAMPUS}; grp_eb=0.0
for (e,a),v in ea.items():
    amt=v*fac(a); sign=+amt if a in R.PROD else (-amt if (a.startswith("6") and a!="6811") else 0)
    if e in eb_c: eb_c[e]+=sign
    elif e=="GRP": grp_eb+=sign
_pil=openpyxl.load_workbook("CAD_SAAD_LIVE.xlsx",data_only=True)["Pilotage"]
cac={_pil["F%d"%r].value:_pil["G%d"%r].value for r in range(13,27)}

# ---------- figure ----------
fig=plt.figure(figsize=(20,13)); fig.patch.set_facecolor("white")
gs=fig.add_gridspec(3,3,height_ratios=[1.15,1,1],hspace=0.42,wspace=0.28)
codes=[c[0] for c in CAMPUS]; labels=[c[1]+"\n"+c[2] for c in CAMPUS]
CA=[ca_c[c] for c in codes]; EFF=[eff_c[c] for c in codes]; EB=[eb_c[c] for c in codes]
EBE=[eb_c[c]/eff_c[c] if eff_c[c] else 0 for c in codes]
BR=[budref[c] for c in codes]; RJ=[rejoue[c] for c in codes]; CC=[cac[c] for c in codes]
MK={"MBway":"#2E75B6","ISCOM":"#548235","Ipac":"#BF8F00","Pigier":"#843C0C","Tunon":"#7030A0"}
mcol=[MK[c[1]] for c in CAMPUS]

# --- panel 1 (large top-left, 2 cols) : table synthese ---
ax=fig.add_subplot(gs[0,:2]); ax.axis("off")
ax.set_title("Synthese par campus — Budget 2027 V01 (live)",fontsize=13,fontweight="bold",color="#1F3864",pad=14)
cols=["Campus","Eff.","CA 2027","EBITDA","Mrg%","EBITDA/et.","Rejoue"]
rows=[]
for c in CAMPUS:
    e=c[0]; rows.append([c[1]+" "+c[2], "%d"%eff_c[e], "{:,.0f}".format(ca_c[e]).replace(",", " "),
        "{:,.0f}".format(eb_c[e]).replace(",", " "), "%.0f%%"%(eb_c[e]/ca_c[e]*100),
        "{:,.0f}".format(eb_c[e]/eff_c[e]).replace(",", " "), "{:,.0f}".format(rejoue[e]).replace(",", " ")])
tot_ca=sum(CA); tot_eff=sum(EFF); tot_eb=sum(EB)
rows.append(["Sous-total campus","%d"%tot_eff,"{:,.0f}".format(tot_ca).replace(",", " "),
    "{:,.0f}".format(tot_eb).replace(",", " "),"%.0f%%"%(tot_eb/tot_ca*100),
    "{:,.0f}".format(tot_eb/tot_eff).replace(",", " "),"{:,.0f}".format(sum(RJ)).replace(",", " ")])
rows.append(["Siege / holding (GRP)","","","{:,.0f}".format(grp_eb).replace(",", " "),"","",""])
gg=tot_eb+grp_eb
rows.append(["GROUPE 2027 V01","%d"%tot_eff,"{:,.0f}".format(tot_ca).replace(",", " "),
    "{:,.0f}".format(gg).replace(",", " "),"%.1f%%"%(gg/tot_ca*100),"","{:,.0f}".format(sum(RJ)).replace(",", " ")])
tb=ax.table(cellText=rows,colLabels=cols,loc="center",cellLoc="right")
tb.auto_set_font_size(False); tb.set_fontsize(8.5); tb.scale(1,1.28)
for j in range(len(cols)):
    tb[0,j].set_facecolor("#548235"); tb[0,j].set_text_props(color="white",fontweight="bold")
n=len(rows)
for i in range(1,n+1):
    tb[i,0].set_text_props(ha="left")
    if i<=14:
        for j in range(len(cols)): tb[i,j].set_facecolor("#FFFFFF" if i%2 else "#F2F2F2")
    elif i==15:
        for j in range(len(cols)): tb[i,j].set_facecolor("#DDEBF7"); tb[i,j].set_text_props(fontweight="bold")
    elif i==16:
        for j in range(len(cols)): tb[i,j].set_facecolor("#FCE4D6"); tb[i,j].set_text_props(color="#843C0C",fontweight="bold")
    else:
        for j in range(len(cols)): tb[i,j].set_facecolor("#1F3864"); tb[i,j].set_text_props(color="white",fontweight="bold")

# --- panel 2 (top-right) : donut poids marque CA ---
ax=fig.add_subplot(gs[0,2])
mca={}; meb={}
for c in CAMPUS: mca[c[1]]=mca.get(c[1],0)+ca_c[c[0]]; meb[c[1]]=meb.get(c[1],0)+eb_c[c[0]]
order=["MBway","ISCOM","Ipac","Pigier","Tunon"]
ax.pie([mca[m] for m in order],labels=order,autopct="%1.0f%%",colors=[MK[m] for m in order],
       wedgeprops=dict(width=0.42,edgecolor="white"),textprops=dict(fontsize=9))
ax.set_title("Poids des marques — CA 2027",fontsize=12,fontweight="bold",color="#1F3864")

# --- panel 3 (mid-left) : CA & EBITDA par campus ---
ax=fig.add_subplot(gs[1,:2]); x=range(len(codes)); w=0.4
ax.bar([i-w/2 for i in x],[v/1000 for v in CA],w,label="CA (k EUR)",color="#2E75B6")
ax.bar([i+w/2 for i in x],[v/1000 for v in EB],w,label="EBITDA campus (k EUR)",color="#548235")
ax.set_xticks(list(x)); ax.set_xticklabels(labels,fontsize=7.5); ax.legend(fontsize=9)
ax.set_title("CA & EBITDA (avant siege) par campus",fontsize=12,fontweight="bold",color="#1F3864")
ax.grid(axis="y",alpha=0.3)

# --- panel 4 (mid-right) : EBITDA/etudiant ---
ax=fig.add_subplot(gs[1,2])
ax.barh(range(len(codes)),EBE,color=mcol); ax.set_yticks(range(len(codes)))
ax.set_yticklabels([c[1][:4]+" "+c[2][:3] for c in CAMPUS],fontsize=7); ax.invert_yaxis()
ax.set_title("EBITDA / etudiant (EUR)",fontsize=12,fontweight="bold",color="#1F3864")
ax.grid(axis="x",alpha=0.3)

# --- panel 5 (bottom, 2 cols) : cap ref->rejoue + CAC ---
ax=fig.add_subplot(gs[2,:2]); x=range(len(codes))
ax.bar([i-w/2 for i in x],[v/1000 for v in BR],w,label="Budget acq. reference (k)",color="#BDD7EE")
ax.bar([i+w/2 for i in x],[v/1000 for v in RJ],w,label="Budget rejoue live (k)",color="#2E75B6")
ax.set_xticks(list(x)); ax.set_xticklabels(labels,fontsize=7.5); ax.legend(fontsize=9,loc="upper right")
ax.set_title("Cap strategique : budget acquisition reference -> rejoue (cap tous = 1 ici)",
             fontsize=12,fontweight="bold",color="#1F3864")
ax2=ax.twinx(); ax2.plot(list(x),CC,"o-",color="#C00000",label="CAC marginal (EUR)")
ax2.set_ylabel("CAC (EUR)",color="#C00000"); ax2.legend(fontsize=9,loc="upper left")
ax.grid(axis="y",alpha=0.3)

# --- panel 6 (bottom-right) : marge EBITDA % par marque ---
ax=fig.add_subplot(gs[2,2])
ax.bar(order,[meb[m]/mca[m]*100 for m in order],color=[MK[m] for m in order])
ax.set_title("Marge EBITDA % par marque (avant siege)",fontsize=12,fontweight="bold",color="#1F3864")
ax.set_ylabel("%"); ax.grid(axis="y",alpha=0.3)
for i,m in enumerate(order): ax.text(i,meb[m]/mca[m]*100+0.5,"%.0f%%"%(meb[m]/mca[m]*100),ha="center",fontsize=9)

fig.suptitle("EDUSERVICES — Cockpit CFO Pilotage (aide a la decision, 2027 V01)",
             fontsize=16,fontweight="bold",color="#1F3864",y=0.995)
plt.savefig("/tmp/dashboard.png",dpi=100,bbox_inches="tight",facecolor="white")
print("wrote /tmp/dashboard.png  | GROUPE EBITDA=%.0f (cible 3875895)"%(gg))
