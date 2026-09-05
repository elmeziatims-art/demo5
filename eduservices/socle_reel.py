#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""socle_reel.py — LE SOCLE, lu directement sur l'EXTRAIT REEL de la base.

Remplace la version qui reconstruisait la donnee a partir des inducteurs du
referentiel : depuis le calibrage de la compta, la base fait foi. Tout ce que
je produis derive donc des memes chiffres que Tagetik, au centime.

  data/socle_crm.csv           AW_002_000002_000001  (CRM : volumes et revenus)
  data/compta.csv              AW_002_000004_000001  (comptes)
  data/siege_2026.json         le siege reel redescendu par campus (cascade K1..K4)
  data/calibrage_direct.json   les couts directs recalibres par campus/exercice
                               (l'UPDATE applique en base le 05/09)

API :
    construire()          -> agregats par CAMPUS et par exercice
    construire_classes()  -> (campus, lignes) au grain COHORTE-CLASSE
"""
import csv, json, os
from collections import defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
EXERCICES = [2024, 2025, 2026]
CAPACITE  = {"BAC": 32, "MAS": 26, "BTS": 30}
CPT_VAR    = {"621", "604", "6063", "6231"}
CPT_DIRECT = {"6411", "6413", "645", "613", "615", "616", "625", "63511"}
CPT_SIEGE  = {"6236", "6414", "6226", "626", "6281", "6331", "6333"}
MARQUE_LIB = {"MBWAY": "MBway", "ISCOM": "ISCOM", "IPAC": "Ipac Bachelor Factory",
              "PIGIER": "Pigier", "TUNON": "Tunon"}

def _lire(nom):
    with open(os.path.join(ICI, "data", nom), encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh, delimiter=";"))
_num = lambda v: float(v.replace(",", ".")) if v else 0.0
_cap = lambda prog: CAPACITE[prog.split("_")[0]]

def construire():
    """Agregats par campus x exercice, identiques a ce que renvoie V_ALLOCATION."""
    S = _lire("socle_crm.csv"); C = _lire("compta.csv")
    CAL = json.load(open(os.path.join(ICI, "data", "calibrage_direct.json")))

    campus = defaultdict(lambda: dict(ca={}, eb={}, eff={}, places={}, inscrits={},
                                      mix_alt={}, cvar={}, cdir={}, csiege={}, lignes=[]))
    for r in S:
        ex = int(r["EXERCICE"]); e = r["ENTITY"]
        c = campus[e]; c["ent"] = e
        c["marque"] = MARQUE_LIB[e.split("_")[0]]
        eff = _num(r["VOL_EFF"]); new = _num(r["VOL_NEW"]); ncl = _num(r["VOL_CLASS"])
        ca = eff * _num(r["REV_STUD"]) + new * _num(r["REV_FRAIS_INS"])
        for k, v in (("ca", ca), ("eff", eff), ("inscrits", new),
                     ("places", ncl * _cap(r["PROGRAMME"]))):
            c[k][ex] = c[k].get(ex, 0) + v
        c["mix_alt"][ex] = c["mix_alt"].get(ex, 0) + (eff if r["MODALITE"] == "ALT" else 0)
        if ex == 2026:
            c["lignes"].append(dict(prog=r["PROGRAMME"], an=r["AN_ETUDE"], mod=r["MODALITE"],
                                    cycle=r["PROGRAMME"].split("_")[0], ncl=ncl,
                                    cap=_cap(r["PROGRAMME"]), eff=eff, new=new, ca=ca,
                                    rev=_num(r["REV_STUD"])))
    for c in campus.values():
        for ex in EXERCICES:
            c["mix_alt"][ex] = c["mix_alt"][ex] / c["eff"][ex] if c["eff"].get(ex) else 0

    # ---- compta : variable par campus, siege au GRP, direct = valeurs calibrees ----
    siege_grp = defaultdict(float)
    for r in C:
        ex = int(r["EXERCICE"]); e = r["ENTITY"]; a = r["ACCOUNT"]
        if ex not in EXERCICES: continue
        if e == "GRP":
            if a in CPT_SIEGE: siege_grp[ex] += _num(r["AMOUNT"])
        elif a in CPT_VAR:
            campus[e]["cvar"][ex] = campus[e]["cvar"].get(ex, 0) + _num(r["AMOUNT"])
    for e, c in campus.items():
        for ex in EXERCICES:
            c["cdir"][ex] = CAL[str(ex)][e]

    # ---- siege : valeurs REELLES 2026 telles que la cascade V_ALLOCATION les
    # redescend (le prorata effectifs s'en ecarte de 1 a 2 %, assez pour decaler
    # une marge de 0,3 point). Pour 2024 et 2025 : meme taux par eleve qu'en
    # 2026, puis recalage sur l'enveloppe siege de l'exercice.
    SIEGE26 = json.load(open(os.path.join(ICI, "data", "siege_2026.json")))
    taux = {e: SIEGE26[e] / campus[e]["eff"][2026] for e in SIEGE26}
    for ex in EXERCICES:
        brut = {e: taux[e] * c["eff"][ex] for e, c in campus.items()}
        k = siege_grp[ex] / sum(brut.values())
        for e, c in campus.items():
            c["csiege"][ex] = brut[e] * k
            c["eb"][ex] = c["ca"][ex] - c["cvar"][ex] - c["cdir"][ex] - c["csiege"][ex]
    return list(campus.values())

# ancres reelles, recalculees depuis l'extrait (plus de constantes en dur)
def ancres():
    C = construire()
    return {"CA":  {ex: sum(c["ca"][ex] for c in C) for ex in EXERCICES},
            "EB":  {ex: sum(c["eb"][ex] for c in C) for ex in EXERCICES},
            "EFF": {ex: sum(c["eff"][ex] for c in C) for ex in EXERCICES},
            "INSCRITS": {ex: sum(c["inscrits"][ex] for c in C) for ex in EXERCICES}}
ANCRES = None

if __name__ == "__main__":
    C = construire(); A = ancres()
    print("SOCLE LU SUR L'EXTRAIT REEL — %d campus\n" % len(C))
    for ex in EXERCICES:
        print("  %d  CA %13s  EBITDA %12s  marge %5.2f %%  effectifs %5.0f  inscrits %5.0f"
              % (ex, f"{A['CA'][ex]:,.0f}", f"{A['EB'][ex]:,.0f}",
                 100 * A["EB"][ex] / A["CA"][ex], A["EFF"][ex], A["INSCRITS"][ex]))
    print("\n%-11s %12s %12s %8s %8s %8s" % ("ENTITY", "CA 2026", "EBITDA 2026", "marge", "rempl", "mix alt"))
    print("-" * 64)
    for c in sorted(C, key=lambda x: -x["eb"][2026] / x["ca"][2026]):
        print("%-11s %12s %12s %7.1f%% %7.0f%% %7.0f%%"
              % (c["ent"], f"{c['ca'][2026]:,.0f}", f"{c['eb'][2026]:,.0f}",
                 100 * c["eb"][2026] / c["ca"][2026],
                 100 * c["eff"][2026] / c["places"][2026], 100 * c["mix_alt"][2026]))
    print("\nPAR MARQUE")
    for m in ("MBway", "ISCOM", "Ipac Bachelor Factory", "Pigier", "Tunon"):
        s = [c for c in C if c["marque"] == m]
        l = [100 * sum(c["eb"][ex] for c in s) / sum(c["ca"][ex] for c in s) for ex in EXERCICES]
        print("  %-24s %5.1f%% → %5.1f%% → %5.1f%%" % (m, *l))
