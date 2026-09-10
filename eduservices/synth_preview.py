#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apercu de la Synthese par campus avec heatmaps (vraies valeurs replique)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np, replica as R

inp=R.base_inputs(); lev=inp["lev"]; pcoef=inp["pcoef"]; cap=inp["cap"]; budref=inp["budref"]
PILF=[p['F'] for p in R.PIL]; sN=sum(budref[e] for e in PILF); sp=sum(budref[e]*cap[e] for e in PILF)
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
    ba=((T/U)*(1+ACQ))if U else 0
    nouv=(O*(1+BRAND)**Sr+P*(ba**Rr))*((G/Q)if Q else 0)*(J+GLC)*K*(L+GCV)
    eff=nouv if entry else H*(PSG+PASS);nx=nouv if entry else 0
    if ent in ca_c: ca_c[ent]+=eff*(I*(1+PRICE*PC))+nx*FEE; eff_c[ent]+=eff
prod26=sum(v for(e,a,ex),v in R.CPTI.items() if a in R.PROD and ex=="2026");caf=sum(ca_c.values())/prod26
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
CAtot=sum(ca_c.values())
rows=[]
for code,mq,ville in CAMP:
    rows.append([mq+" "+ville, eff_c[code], ca_c[code], ca_c[code]/CAtot, eb_c[code],
                 eb_c[code]/ca_c[code], eb_c[code]/eff_c[code], rejoue[code]])
cols=["Campus","Effectif","CA 2027","Part CA","EBITDA campus","Mrg EBITDA","EBITDA/etud","Rejoue"]
heatcols=[1,2,3,4,5,6]  # which columns get heatmap
arr=np.array([[r[i] for r in rows] for i in range(1,8)],dtype=float)

fig,ax=plt.subplots(figsize=(15,7)); ax.axis("off")
ax.set_title("Synthese par campus — Budget 2027 V01 (live, heatmaps)",fontsize=14,fontweight="bold",color="#1F3864",pad=16)
ncol=len(cols); nrow=len(rows)
cmap=mcolors.LinearSegmentedColormap.from_list("rag",["#F8696B","#FFEB84","#63BE7B"])
def norm(vals):
    lo,hi=np.percentile(vals,10),np.percentile(vals,90);
    return np.clip((vals-lo)/(hi-lo+1e-9),0,1)
colmaps={}
for ci in [1,2,3,4,5,6]:
    vals=np.array([r[ci] for r in rows]); colmaps[ci]=norm(vals)
def fmt(ci,v):
    if ci==0:return v
    if ci in(3,5):return "%.1f%%"%(v*100)
    if ci in(1,):return "%.0f"%v
    return "{:,.0f}".format(v).replace(",", " ")
w=[0.16,0.09,0.13,0.09,0.13,0.10,0.11,0.11]
x0=[sum(w[:i]) for i in range(ncol+1)]
for j in range(ncol):
    ax.add_patch(plt.Rectangle((x0[j],1.0),w[j],0.06,color="#548235"))
    ax.text(x0[j]+w[j]/2,1.03,cols[j],ha="center",va="center",color="white",fontsize=9,fontweight="bold")
for i,r in enumerate(rows):
    y=0.94-i*0.066
    for j in range(ncol):
        bg="white"
        if j in colmaps: bg=mcolors.to_hex(cmap(colmaps[j][i]))
        ax.add_patch(plt.Rectangle((x0[j],y),w[j],0.062,facecolor=bg,edgecolor="#DDDDDD",lw=0.4))
        ax.text(x0[j]+ (0.01 if j==0 else w[j]-0.01), y+0.031, fmt(j,r[j]),
                ha="left" if j==0 else "right", va="center", fontsize=8.2,
                color="#1F3864" if j==0 else "#000000", fontweight="bold" if j==0 else "normal")
# total rows
tot=["Sous-total campus",sum(eff_c.values()),CAtot,1.0,sum(eb_c.values()),sum(eb_c.values())/CAtot,sum(eb_c.values())/sum(eff_c.values()),sum(rejoue.values())]
sieg=["Siege / holding (GRP)","","","",grp,"","",""]
grpn=["GROUPE 2027 V01",sum(eff_c.values()),CAtot,1.0,sum(eb_c.values())+grp,(sum(eb_c.values())+grp)/CAtot,"",sum(rejoue.values())]
for k,(rr,bgc,fc) in enumerate([(tot,"#DDEBF7","#1F3864"),(sieg,"#FCE4D6","#843C0C"),(grpn,"#1F3864","white")]):
    y=0.94-(nrow+k)*0.066
    for j in range(ncol):
        ax.add_patch(plt.Rectangle((x0[j],y),w[j],0.062,facecolor=bgc,edgecolor="#DDDDDD",lw=0.4))
        val=rr[j]
        if val!="":
            t=fmt(j,val) if isinstance(val,(int,float)) else val
            ax.text(x0[j]+(0.01 if j==0 else w[j]-0.01),y+0.031,t,ha="left" if j==0 else "right",
                    va="center",fontsize=8.2,color=fc,fontweight="bold")
ax.set_xlim(0,1); ax.set_ylim(0.94-(nrow+3)*0.066,1.08)
plt.savefig("/tmp/synth.png",dpi=115,bbox_inches="tight",facecolor="white")
print("wrote /tmp/synth.png ; groupe EBITDA=%.0f"%(sum(eb_c.values())+grp))
