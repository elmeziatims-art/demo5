#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calcule la Synthese par campus depuis la replique prouvee, pour cross-check
avec la table vivante Excel, et verifie que la somme retombe sur le groupe."""
import replica as R

CAMPUS=[c[0] for c in [("MBWAY_PAR",),("MBWAY_LYO",),("MBWAY_NAN",),("MBWAY_BOR",),
 ("ISCOM_PAR",),("ISCOM_LIL",),("ISCOM_TLS",),("IPAC_NAN",),("IPAC_REN",),("IPAC_MTP",),
 ("PIGIER_LYO",),("PIGIER_BOR",),("TUNON_PAR",),("TUNON_LYO",)]]

inp=R.base_inputs(); lev=inp["lev"]; pcoef=inp["pcoef"]; cap=inp["cap"]; budref=inp["budref"]
# rejoue
N=[budref[e] for e in [p['F'] for p in R.PIL]]; M=[cap[e] for e in [p['F'] for p in R.PIL]]
sN=sum(N); sp=sum(n*m for n,m in zip(N,M))
rejoue={p['F']: budref[p['F']]*cap[p['F']]*(sN/sp) for p in R.PIL}

# moteur per campus (V01): CA, EFF
ca_c={c:0.0 for c in CAMPUS}; eff_c={c:0.0 for c in CAMPUS}
for m in R.MOT:
    if m['B']!="V01": continue
    ent=m['D']; mrq=m['E']; prog=m['F']; an=m['G']; mod=m['H']
    G=R.socsum(ent,prog,an,mod,"H"); H=R.socsum(ent,prog,an,mod,"N")
    I=R.socsum(ent,prog,an,mod,"P"); J=R.socsum(ent,prog,an,mod,"W")
    K=R.socsum(ent,prog,an,mod,"X"); L=R.socsum(ent,prog,an,mod,"Y"); PSG=R.socsum(ent,prog,an,mod,"V")
    c=R.CAM.get(ent,{}); O=c.get("D",0) or 0; P=c.get("E",0) or 0; Q=c.get("F",0) or 0
    Rr=c.get("K",0) or 0; Sr=c.get("M",0) or 0
    T=rejoue.get(ent,0); U=budref.get(ent,0)
    ACQ=lev["ACQ"][0]; BRAND=lev["BRAND"][0]; PRICE=lev["PRICE"][0]
    GLC=lev["GLC"][0]; GCV=lev["GCV"][0]; PASS=lev["PASS"][0]; FEE=lev["FEE"][0]
    PC=pcoef.get(mrq,pcoef["TUNON"]); entry=1 if an in R.ENTRY else 0
    ba=((T/U)*(1+ACQ)) if U else 0
    nouv=(O*(1+BRAND)**Sr+P*(ba**Rr))*((G/Q) if Q else 0)*(J+GLC)*K*(L+GCV)
    nouveaux=nouv if entry else 0; eff=nouv if entry else H*(PSG+PASS)
    prix=I*(1+PRICE*PC); cah=eff*prix+nouveaux*FEE
    if ent in ca_c: ca_c[ent]+=cah; eff_c[ent]+=eff

# CAF + EBITDA per campus (V01)
prod26=sum(v for (e,a,ex),v in R.CPTI.items() if a in R.PROD and ex=="2026")
ca_tot=sum(ca_c.values()); caf=ca_tot/prod26
def factor(acc):
    ACQ=lev["ACQ"][0];BRAND=lev["BRAND"][0];INFL=lev["INFL"][0];SAL=lev["SAL"][0]
    FTE=lev["FTE"][0];PROD_=lev["PROD"][0];STR=lev["STRUCT"][0]
    if acc in R.PROD: return caf
    if acc=="6231": return 1+ACQ
    if acc=="6236": return 1+BRAND
    if acc in ("621","604","6063"): return caf*(1-PROD_)
    if acc in ("6411","6413","6414","645"): return (1+SAL)*(1+FTE)
    if acc in ("613","615","616","6226","625","626","6281"): return (1+INFL)*(1-PROD_)*(1+STR)
    if acc in ("6331","63511","6333"): return (1+INFL)*(1-PROD_)
    if acc=="6811": return 1+INFL
    return 1.0
eb_c={c:0.0 for c in CAMPUS}
# compta 2026 per (entity,account)
ea={}
for (e,a,ex),v in R.CPTI.items():
    if ex=="2026": ea[(e,a)]=ea.get((e,a),0)+v
for (e,a),v in ea.items():
    if e not in eb_c: continue
    amt=v*factor(a)
    if a in R.PROD: eb_c[e]+=amt
    elif a.startswith("6") and a!="6811": eb_c[e]-=amt

# marge complete per campus (from stored Allocation via replica logic is heavy; approximate by group check)
print("%-12s %9s %12s %11s %7s"%("CAMPUS","EFFECTIF","CA_2027","EBITDA","MRG%"))
tot=[0,0,0]
for c in CAMPUS:
    mrg=eb_c[c]/ca_c[c] if ca_c[c] else 0
    print("%-12s %9.0f %12.0f %11.0f %6.1f%%"%(c,eff_c[c],ca_c[c],eb_c[c],mrg*100))
    tot[0]+=eff_c[c]; tot[1]+=ca_c[c]; tot[2]+=eb_c[c]
print("%-12s %9.0f %12.0f %11.0f %6.1f%%"%("GROUPE",tot[0],tot[1],tot[2],tot[2]/tot[1]*100))
print("\nControle: CA doit=24120981 (ecart %.2f)  EBITDA doit=3875895 (ecart %.2f)"
      %(tot[1]-24120981, tot[2]-3875895))
