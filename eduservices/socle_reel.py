#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""socle_reel.py — LE SOCLE, construit sur le VRAI referentiel (14 campus, 5 marques).
Tous les inducteurs viennent de gen_v3.py : base_entry, CITY_VOL, CITY_PRICE, retention,
REV par cycle x modalite, croissance organique par marque. Le resultat est normalise sur
les ancres groupe reelles : CA 23 098 985 / EBITDA 3 845 790 / effectifs 3 114 / inscrits 1 229.
Importe par build_cockpit_xlsx.py et build_drill_xlsx.py -> une seule source de verite."""

from math import ceil

# ---------- referentiel (copie conforme de gen_v3.py) ----------
BRANDS={"MBway":("Management",60,["Paris","Lyon","Nantes","Bordeaux"]),
        "ISCOM":("Communication",55,["Paris","Lille","Toulouse"]),
        "Ipac Bachelor Factory":("Commerce",50,["Nantes","Rennes","Montpellier"]),
        "Pigier":("Commerce/RH",42,["Lyon","Bordeaux"]),
        "Tunon":("Tourisme",36,["Paris","Lyon"])}
PROGS={"MBway":[("Bachelor Management","BAC",[("B1","INIT"),("B2","ALT"),("B3","ALT")]),
                ("Mastère Management","MAST",[("M1","ALT"),("M2","ALT")])],
       "ISCOM":[("Bachelor Communication","BAC",[("B1","INIT"),("B2","ALT"),("B3","ALT")]),
                ("Mastère Communication","MAST",[("M1","ALT"),("M2","ALT")])],
       "Ipac Bachelor Factory":[("Bachelor Commerce","BAC",[("B1","ALT"),("B2","ALT"),("B3","ALT")])],
       "Pigier":[("BTS Gestion","BTS",[("1","ALT"),("2","ALT")]),
                 ("Bachelor RH","BAC",[("B1","ALT"),("B2","ALT"),("B3","ALT")])],
       "Tunon":[("Bachelor Tourisme","BAC",[("B1","ALT"),("B2","ALT"),("B3","ALT")])]}
ENTRY={"B1","M1","1"}
CITY_VOL  ={"Paris":1.30,"Lyon":1.10,"Nantes":1.00,"Bordeaux":0.85,"Lille":0.90,"Toulouse":0.85,"Rennes":0.80,"Montpellier":0.80}
CITY_PRICE={"Paris":1.12,"Lyon":1.05,"Nantes":1.00,"Bordeaux":0.97,"Lille":0.98,"Toulouse":0.96,"Rennes":0.95,"Montpellier":0.95}
MARQUE_CODE={"MBway":"MBWAY","ISCOM":"ISCOM","Ipac Bachelor Factory":"IPAC","Pigier":"PIGIER","Tunon":"TUNON"}
VILLE_CODE ={"Paris":"PAR","Lyon":"LYO","Nantes":"NAN","Bordeaux":"BOR","Lille":"LIL","Toulouse":"TLS","Rennes":"REN","Montpellier":"MTP"}
CAPT={"BTS":30,"BAC":32,"MAST":26}
REV={("BTS","ALT"):6000,("BTS","INIT"):5500,("BAC","ALT"):7000,("BAC","INIT"):7500,
     ("MAST","ALT"):7500,("MAST","INIT"):9000}
PASS={"B2":0.97,"B3":0.98,"M2":0.98,"2":0.97}
GORG={"MBway":1.07,"ISCOM":1.03,"Ipac Bachelor Factory":1.09,"Pigier":1.04,"Tunon":1.02}

# ---------- ancres groupe reelles ----------
ANCRES={"CA":{2024:20552827,2025:21775820,2026:23098985},
        "EB":{2024: 3136652,2025: 3484818,2026: 3845790},
        "EFF":3114,"INSCRITS":1229}
# trajectoire de marge par marque (l'histoire du cockpit) — normalisee ensuite sur l'ancre
MARGE={"MBway":{2024:.1560,2025:.1640,2026:.1742},
       "ISCOM":{2024:.1501,2025:.1605,2026:.1639},
       "Ipac Bachelor Factory":{2024:.1120,2025:.1240,2026:.1350},   # jeune reseau, montee en charge
       "Pigier":{2024:.1868,2025:.1938,2026:.2020},
       "Tunon":{2024:.0578,2025:.0519,2026:.0400}}

def _cohortes(marque):
    """[(programme, annee, modalite, cycle, poids_effectif)] — poids relatif a la cohorte d'entree."""
    out=[]
    for lib,cyc,annees in PROGS[marque]:
        code=lib.split()[0][:3].upper()+"_"+("MGT" if "Manage" in lib else "COM" if "Commu" in lib else
              "CCE" if "Commerce" in lib else "RH" if "RH" in lib else "GES" if "Gestion" in lib else "TOU")
        code={"BAC":"BAC","MAST":"MAS","BTS":"BTS"}[cyc]+"_"+code.split("_")[1]
        w=1.0
        for an,mod in annees:
            if an not in ENTRY: w*=PASS[an]
            out.append((code,an,mod,cyc,w))
    return out

def construire():
    campus=[]
    for marque,(_,base,villes) in BRANDS.items():
        for ville in villes:
            coh=_cohortes(marque)
            eff_entree=base*CITY_VOL[ville]
            lignes=[]
            for code,an,mod,cyc,w in coh:
                e=eff_entree*w
                lignes.append(dict(prog=code,an=an,mod=mod,cycle=cyc,eff_brut=e,
                                   rev=REV[(cyc,mod)]*CITY_PRICE[ville],cap=CAPT[cyc]))
            campus.append(dict(ent=MARQUE_CODE[marque]+"_"+VILLE_CODE[ville],marque=marque,
                               ville=ville,lignes=lignes,
                               eff_brut=sum(l["eff_brut"] for l in lignes),
                               ca_brut=sum(l["eff_brut"]*l["rev"] for l in lignes),
                               ins_brut=sum(l["eff_brut"] for l in lignes if l["an"] in ENTRY)))
    # --- normalisation sur les ancres ---
    ke=ANCRES["EFF"]/sum(c["eff_brut"] for c in campus)
    ki=ANCRES["INSCRITS"]/sum(c["ins_brut"] for c in campus)
    kc=ANCRES["CA"][2026]/sum(c["ca_brut"] for c in campus)
    for c in campus:
        c["eff"]=c["eff_brut"]*ke; c["inscrits"]=c["ins_brut"]*ki
        c["ca"]={2026:c["ca_brut"]*kc}
        for l in c["lignes"]:
            l["eff"]=l["eff_brut"]*ke
            l["ncl"]=max(1,ceil(l["eff"]/l["cap"]))   # jamais au-dessus de la capacite
        c["places"]=sum(l["ncl"]*l["cap"] for l in c["lignes"])
        c["rempl"]=c["eff"]/c["places"]
        c["mix_alt"]=sum(l["eff"] for l in c["lignes"] if l["mod"]=="ALT")/c["eff"]
    # CA 2024 / 2025 : croissance organique par marque, recalee sur l'ancre annuelle
    for ex in (2025,2024):
        brut={c["ent"]:c["ca"][ex+1]/GORG[c["marque"]] for c in campus}
        k=ANCRES["CA"][ex]/sum(brut.values())
        for c in campus: c["ca"][ex]=brut[c["ent"]]*k
    # EBITDA : marge marque + effet taille de ville, recale sur la marge marque puis sur l'ancre groupe
    for ex in (2024,2025,2026):
        for m in BRANDS:
            sel=[c for c in campus if c["marque"]==m]
            ca_m=sum(c["ca"][ex] for c in sel)
            brut={c["ent"]:c["ca"][ex]*(MARGE[m][ex]+(CITY_VOL[c["ville"]]-1.0)*0.04) for c in sel}
            km=(MARGE[m][ex]*ca_m)/sum(brut.values())
            for c in sel: c.setdefault("eb",{})[ex]=brut[c["ent"]]*km
        k=ANCRES["EB"][ex]/sum(c["eb"][ex] for c in campus)
        for c in campus: c["eb"][ex]*=k
    return campus

if __name__=="__main__":
    C=construire()
    print("SOCLE REEL — %d campus, %d marques\n"%(len(C),len({c['marque'] for c in C})))
    print("%-12s %-24s %10s %10s %10s %7s %6s %6s %6s"%("ENTITY","Marque","CA 2026","EBITDA 26","marge","eff","insc","places","rempl"))
    for c in sorted(C,key=lambda x:(x["marque"],x["ent"])):
        print("%-12s %-24s %10s %10s %9.1f%% %7.0f %6.0f %6d %5.0f%%"
              %(c["ent"],c["marque"],f"{c['ca'][2026]:,.0f}",f"{c['eb'][2026]:,.0f}",
                100*c["eb"][2026]/c["ca"][2026],c["eff"],c["inscrits"],c["places"],100*c["eff"]/c["places"]))
    print("\nCONTRÔLE vs ancres groupe")
    for ex in (2024,2025,2026):
        print("  %d  CA %14s / %-14s   EBITDA %12s / %-12s   marge %.2f%%"
              %(ex,f"{sum(c['ca'][ex] for c in C):,.0f}",f"{ANCRES['CA'][ex]:,}",
                f"{sum(c['eb'][ex] for c in C):,.0f}",f"{ANCRES['EB'][ex]:,}",
                100*sum(c['eb'][ex] for c in C)/sum(c['ca'][ex] for c in C)))
    print("  effectifs %.0f / %d      inscrits %.0f / %d"
          %(sum(c["eff"] for c in C),ANCRES["EFF"],sum(c["inscrits"] for c in C),ANCRES["INSCRITS"]))
    print("\nPAR MARQUE (2026)")
    for m in BRANDS:
        s=[c for c in C if c["marque"]==m]; ca=sum(c["ca"][2026] for c in s); eb=sum(c["eb"][2026] for c in s)
        print("  %-24s %2d campus  CA %10s (%4.1f%%)  EBITDA %9s (%4.1f%%)  marge %5.1f%%"
              %(m,len(s),f"{ca:,.0f}",100*ca/ANCRES["CA"][2026],f"{eb:,.0f}",
                100*eb/ANCRES["EB"][2026],100*eb/ca))
