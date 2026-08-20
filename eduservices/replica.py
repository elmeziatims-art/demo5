#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replique Python fidele des 4 moteurs de CAD_SAAD_LIVE.xlsx (moteur, cap, P&L,
allocation), reproduisant EXACTEMENT l'algebre des formules _CALC_*. Sert a :
 (1) valider la baseline vs Tagetik (24,12M / 3,876M / 3,2915M / 434174),
 (2) perturber les variables et mesurer la reaction de chaque sortie."""
import openpyxl, copy

wb = openpyxl.load_workbook("CAD_SAAD_LIVE.xlsx", data_only=True)

def rows(tab, lo, hi, cols):
    ws = wb[tab]
    out = []
    for r in range(lo, hi + 1):
        d = {c: ws["%s%d" % (c, r)].value for c in cols}
        if any(v is not None for v in d.values()):
            out.append(d)
    return out

# ---- source data (valeurs figees) ----
SOC = rows("Socle", 2, 175, list("CDEFG") + list("HKNPVWXY"))      # base 2026
CAM = {r["C"]: r for r in rows("Campagne", 2, 15, list("CDEFKM"))}  # by entity
MOT = rows("Moteur", 2, 175, list("BDEFGH"))                        # keys per row
CPT = rows("Compta", 2, 675, list("ABCF"))                          # entity,acct,ex,amt
ALL = rows("Allocation", 2, 175, list("CDEFGH") + list("IJK"))     # keys+VOL_EFF/CLS/CA
PIL = rows("Pilotage", 13, 26, ["F", "M", "N"])                     # entity,cap,budref

# compta index: (entity,account,exercice)->sum
CPTI = {}
for r in CPT:
    k = (r["A"], str(r["B"]), str(r["C"]))
    CPTI[k] = CPTI.get(k, 0.0) + (r["F"] or 0.0)
def cpt(ent, acc, ex="2026"):
    return CPTI.get((ent, acc, ex), 0.0)

# socle index by (entity,prog,an,mod) 2026
SOCI = {}
for r in SOC:
    if str(r["G"]) != "2026":
        continue
    k = (r["C"], r["D"], r["E"], r["F"])
    SOCI.setdefault(k, []).append(r)
def socsum(ent, prog, an, mod, col):
    return sum((x[col] or 0.0) for x in SOCI.get((ent, prog, an, mod), []))
def socnew(ent, prog, an, mod):  # VOL_NEW = col K
    return sum((x["K"] or 0.0) for x in SOCI.get((ent, prog, an, mod), []))

PROD = {"7062", "706", "708"}
ENTRY = {"B1", "M1", "BTS1"}

# ---- baseline inputs (depuis cad/Pilotage) ----
def base_inputs():
    cad = wb["cad"]
    def g(cell): return cad[cell].value
    lev = {  # name -> (V01,V02,V03) from rows
        "ACQ":(g("I21"),g("J21"),g("K21")), "BRAND":(g("I22"),g("J22"),g("K22")),
        "PRICE":(g("I23"),g("J23"),g("K23")), "GLC":(g("I24"),g("J24"),g("K24")),
        "GCV":(g("I25"),g("J25"),g("K25")), "PASS":(g("I26"),g("J26"),g("K26")),
        "INFL":(g("I27"),g("J27"),g("K27")), "SAL":(g("I28"),g("J28"),g("K28")),
        "FTE":(g("I29"),g("J29"),g("K29")), "PROD":(g("I30"),g("J30"),g("K30")),
        "STRUCT":(g("I31"),g("J31"),g("K31")), "FEE":(g("I37"),g("J37"),g("K37")),
    }
    lev = {k: [0.0 if v is None else v for v in t] for k, t in lev.items()}
    pcoef = {"MBWAY":g("I9"),"ISCOM":g("I10"),"IPAC":g("I11"),"PIGIER":g("I12"),"TUNON":g("I13")}
    pil = wb["Pilotage"]
    cap = {r["F"]: (pil["M%d" % (13 + i)].value) for i, r in enumerate(PIL)}
    budref = {r["F"]: r["N"] for r in PIL}
    keys = {"K1": pil["E9"].value, "K2": pil["E8"].value, "K3": pil["E10"].value}  # GRP_BRAND, BRAND_CAMP, CAMP_CLASS
    return dict(lev=lev, pcoef=pcoef, cap=cap, budref=budref, keys=keys)

VI = {"V01":0, "V02":1, "V03":2}

def simulate(ov=None):
    inp = base_inputs()
    if ov:
        for path, val in ov.items():  # e.g. ("lev","ACQ","V01"), ("pcoef","MBWAY"), ("cap","MBWAY_PAR"), ("keys","K1")
            if path[0]=="lev": inp["lev"][path[1]][VI[path[2]]] = val
            elif path[0]=="pcoef": inp["pcoef"][path[1]] = val
            elif path[0]=="cap": inp["cap"][path[1]] = val
            elif path[0]=="keys": inp["keys"][path[1]] = val
    lev, pcoef, cap, budref, keys = inp["lev"], inp["pcoef"], inp["cap"], inp["budref"], inp["keys"]

    # ---- CAP : rejoue par entite (zero-sum) ----
    N = [budref[r["F"]] for r in PIL]; M = [cap[r["F"]] for r in PIL]
    sN = sum(N); sp = sum(n*m for n, m in zip(N, M))
    rejoue = {}
    for r in PIL:
        n, m = budref[r["F"]], cap[r["F"]]
        rejoue[r["F"]] = n*m*(sN/sp) if sp else 0.0

    # ---- MOTEUR : CA & EFFECTIF live par version ----
    ca_ver = {"V01":0.0,"V02":0.0,"V03":0.0}
    eff_ver = {"V01":0.0,"V02":0.0,"V03":0.0}
    for m in MOT:
        ver, ent, mrq, prog, an, mod = m["B"], m["D"], m["E"], m["F"], m["G"], m["H"]
        vi = VI[ver]
        G = socsum(ent,prog,an,mod,"H"); H = socsum(ent,prog,an,mod,"N")
        I = socsum(ent,prog,an,mod,"P"); J = socsum(ent,prog,an,mod,"W")
        K = socsum(ent,prog,an,mod,"X"); L = socsum(ent,prog,an,mod,"Y")
        PSG = socsum(ent,prog,an,mod,"V")
        c = CAM.get(ent, {})
        O=c.get("D",0) or 0; P=c.get("E",0) or 0; Q=c.get("F",0) or 0
        R=c.get("K",0) or 0; S=c.get("M",0) or 0
        T = rejoue.get(ent,0.0); U = budref.get(ent,0.0)
        ACQ=lev["ACQ"][vi]; BRAND=lev["BRAND"][vi]; PRICE=lev["PRICE"][vi]
        GLC=lev["GLC"][vi]; GCV=lev["GCV"][vi]; PASS=lev["PASS"][vi]; FEE=lev["FEE"][vi]
        PC = pcoef.get(mrq, pcoef["TUNON"])
        entry = 1 if an in ENTRY else 0
        base_acq = ((T/U)*(1+ACQ)) if U else 0.0
        nouv = (O*(1+BRAND)**S + P*(base_acq**R)) * ((G/Q) if Q else 0.0) * (J+GLC) * K * (L+GCV)
        nouveaux = nouv if entry else 0.0
        effectif = nouv if entry else H*(PSG+PASS)
        prix = I*(1+PRICE*PC)
        cah = effectif*prix + nouveaux*FEE
        ca_ver[ver] += cah
        eff_ver[ver] += effectif
    # produits 2026 & CAF
    prod26 = sum(cpt(r["A"], str(r["B"]), "2026") for r in CPT if str(r["B"]) in PROD)
    # prod26 double counts; recompute cleanly:
    prod26 = sum(v for (e,a,ex),v in CPTI.items() if a in PROD and ex=="2026")
    caf = {v: (ca_ver[v]/prod26 if prod26 else 0.0) for v in ("V01","V02","V03")}

    # ---- P&L : EBITDA V01 (grain compte) ----
    def factor(acc, vi):
        ACQ=lev["ACQ"][vi]; BRAND=lev["BRAND"][vi]; INFL=lev["INFL"][vi]
        SAL=lev["SAL"][vi]; FTE=lev["FTE"][vi]; PROD_=lev["PROD"][vi]; STR=lev["STRUCT"][vi]
        CF=caf[["V01","V02","V03"][vi]]
        if acc in PROD: return CF
        if acc=="6231": return 1+ACQ
        if acc=="6236": return 1+BRAND
        if acc in ("621","604","6063"): return CF*(1-PROD_)
        if acc in ("6411","6413","6414","645"): return (1+SAL)*(1+FTE)
        if acc in ("613","615","616","6226","625","626","6281"): return (1+INFL)*(1-PROD_)*(1+STR)
        if acc in ("6331","63511","6333"): return (1+INFL)*(1-PROD_)
        if acc=="6811": return 1+INFL
        return 1.0
    # aggregate compta 2026 by account, apply factor, EBITDA=prod-charges(6xxx sauf 6811)
    acc26 = {}
    for (e,a,ex),v in CPTI.items():
        if ex=="2026": acc26[a]=acc26.get(a,0.0)+v
    ebitda = 0.0
    for a,v in acc26.items():
        amt = v*factor(a,0)  # V01
        if a in PROD: ebitda += amt
        elif a.startswith("6") and a!="6811": ebitda -= amt

    # ---- ALLOCATION : marge complete (cle-dependante, zero-sum sur total) ----
    # pre-agregations sur les cles stockees (Alloc I/J/K, exercice 2026)
    ex_all = "2026"
    def sel(key, ca, eff, cls):
        return ca if key=="Chiffre d'affaires" else (eff if key=="Effectif" else cls)
    # campus (entity), marque, group totals
    E_EFF={}; E_CLS={}; E_CA={}; M_EFF={}; M_CLS={}; M_CA={}
    G_EFF=G_CLS=G_CA=0.0
    for a in ALL:
        e=a["D"]; mq=a["E"]; I=a["I"] or 0; J=a["J"] or 0; K=a["K"] or 0
        E_EFF[e]=E_EFF.get(e,0)+I; E_CLS[e]=E_CLS.get(e,0)+J; E_CA[e]=E_CA.get(e,0)+K
        M_EFF[mq]=M_EFF.get(mq,0)+I; M_CLS[mq]=M_CLS.get(mq,0)+J; M_CA[mq]=M_CA.get(mq,0)+K
        G_EFF+=I; G_CLS+=J; G_CA+=K
    # HRS per row & E_HRS/E_NEW per campus
    def hrs_of(prog, mod, vclass):
        p3 = str(prog)[:3]
        if p3=="BAC" and mod=="INIT": h=600
        elif p3=="BAC": h=480
        elif p3=="MAS" and mod=="INIT": h=520
        elif p3=="MAS": h=420
        elif mod=="INIT": h=1000
        else: h=700
        return (vclass or 0)*h
    E_HRS={}; E_NEW={}
    rowcache=[]
    for a in ALL:
        e=a["D"]; prog=a["F"]; an=a["G"]; mod=a["H"]
        vclass=a["J"] or 0; veff=a["I"] or 0; ca=a["K"] or 0
        hrs=hrs_of(prog,mod,vclass)
        vnew=socnew(e,prog,an,mod)
        E_HRS[e]=E_HRS.get(e,0)+hrs; E_NEW[e]=E_NEW.get(e,0)+vnew
        rowcache.append((e,a["E"],prog,an,mod,veff,vclass,ca,hrs,vnew))
    k1,k2,k3 = keys["K1"],keys["K2"],keys["K3"]
    marge_tot=0.0; marge_by_class={}
    for (e,mq,prog,an,mod,veff,vclass,ca,hrs,vnew) in rowcache:
        VAC=cpt(e,"621",ex_all); PERM=cpt(e,"6411",ex_all)
        ODIR=cpt(e,"604",ex_all)+cpt(e,"6063",ex_all); MKT=cpt(e,"6231",ex_all)
        STRUCT_CAMP=sum(cpt(e,x,ex_all) for x in ("6413","645","613","615","616","625","63511"))
        SIEGE=sum(cpt("GRP",x,ex_all) for x in ("6414","6226","6236","626","6281","6331","6333"))
        D3C=sel(k3,ca,veff,vclass); D3E=sel(k3,E_CA[e],E_EFF[e],E_CLS[e])
        D2E=sel(k2,E_CA[e],E_EFF[e],E_CLS[e]); D2M=sel(k2,M_CA[mq],M_EFF[mq],M_CLS[mq])
        D1M=sel(k1,M_CA[mq],M_EFF[mq],M_CLS[mq]); D1G=sel(k1,G_CA,G_EFF,G_CLS)
        cvac=VAC*(hrs/E_HRS[e] if E_HRS[e] else 0)
        cperm=PERM*(hrs/E_HRS[e] if E_HRS[e] else 0)
        codir=ODIR*(veff/E_EFF[e] if E_EFF[e] else 0)+MKT*(vnew/E_NEW[e] if E_NEW[e] else 0)
        cstruct=STRUCT_CAMP*(D3C/D3E if D3E else 0)
        csiege=SIEGE*(D1M/D1G if D1G else 0)*(D2E/D2M if D2M else 0)*(D3C/D3E if D3E else 0)
        marge=ca-(cvac+cperm+codir+cstruct+csiege)
        marge_tot+=marge
        ck=(e,prog,an,mod); marge_by_class[ck]=marge

    return dict(CA=ca_ver["V01"], EFF=eff_ver["V01"], EBITDA=ebitda, MARGE=marge_tot,
                REJ_PAR=rejoue["MBWAY_PAR"], REJ_LYO=rejoue["MBWAY_LYO"],
                REJ_TOT=sum(rejoue.values()), _mclass=marge_by_class)

if __name__ == "__main__":
    b = simulate()
    print("BASELINE   CA=%.0f  EFF=%.1f  EBITDA=%.0f  MARGE=%.0f  REJ_TOT=%.0f  REJ_PAR=%.0f  REJ_LYO=%.0f"
          % (b["CA"], b["EFF"], b["EBITDA"], b["MARGE"], b["REJ_TOT"], b["REJ_PAR"], b["REJ_LYO"]))
    print("ATTENDU    CA=24120981  EBITDA=3875895  MARGE=3291530  REJ_TOT=434174  EFF~3175")
