#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cadrage_ebitda.py — LE CADRAGE INVERSE.

Le budget classique part des couts et laisse tomber l'EBITDA. Personne ne le
valide. Ici on renverse : la direction saisit une CIBLE d'EBITDA, le CA est un
CONSTAT (il vient du CRM, la rentree est deja engagee), et l'ecart se ferme
avec quatre leviers de gestion, chacun assis sur une grandeur reelle.

Toutes les assiettes sont lues sur la base (socle_reel), rien n'est invente :
seules les LOIS de passage 2026 -> 2027 sont des hypotheses, et elles sont
toutes exposees comme des parametres saisissables.
"""
import csv, json, os
from collections import defaultdict
from socle_reel import construire, EXERCICES

ICI = os.path.dirname(os.path.abspath(__file__))
PERM  = {"6411", "6413", "645"}
VAC   = {"621"}
ACQ   = {"6231"}
AUTRE = {"604", "6063", "613", "615", "616", "625", "63511"}
SIEGE = {"6236", "6414", "6226", "626", "6281", "6331", "6333"}

def base_reelle():
    """Assiettes 2024-2026 par poste de levier, lues sur la compta."""
    C = construire()
    b = defaultdict(lambda: defaultdict(float))
    with open(os.path.join(ICI, "data", "compta.csv"), encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            ex = int(r["EXERCICE"]); a = r["ACCOUNT"]; m = float(r["AMOUNT"])
            if ex not in EXERCICES: continue
            if r["ENTITY"] == "GRP":
                if a in SIEGE: b["SIEGE"][ex] += m
            elif a in PERM:  b["PERM"][ex]  += m
            elif a in VAC:   b["VAC"][ex]   += m
            elif a in ACQ:   b["ACQ"][ex]   += m
            elif a in AUTRE: b["AUTRE"][ex] += m
    b["EFF"]      = {e: sum(c["eff"][e]      for c in C) for e in EXERCICES}
    b["INSCRITS"] = {e: sum(c["inscrits"][e] for c in C) for e in EXERCICES}
    b["CA"]       = {e: sum(c["ca"][e]       for c in C) for e in EXERCICES}
    b["EBITDA"]   = {e: sum(c["eb"][e]       for c in C) for e in EXERCICES}
    return b

# ---------------------------------------------------------------- hypotheses
# le CONSTAT : ce que le reseau apporte, la finance ne le negocie pas
CONSTAT = dict(croiss_eff=0.060,      # rythme observe 2024->2026
               prix=0.000)           # historique : CA/eleve strictement plat
# le TENDANCIEL : chaque cout unitaire 2026 reconduit, indexe de son inflation
TENDANCIEL = dict(nao=0.025,          # politique salariale au fil de l'eau
                  taux_vac=0.020,     # revalorisation du taux horaire vacataire
                  inflation=0.020,    # autres couts campus et siege
                  derive_caf=0.070)   # l'acquisition coute 7 %/an de plus par inscrit
# les LEVIERS : la decision de gestion. 0 = on ne fait rien.
LEVIERS = dict(nao=0.0,               # pts retires a la NAO tendancielle
               encadrement=0.0,       # % d'eleves en plus par ETP permanent
               heures_vac=0.0,        # % d'heures vacataires en moins par eleve
               caf=0.0,               # % de CAF en moins par inscrit
               siege=0.0,             # % de cout siege par eleve en moins
               prix=0.0)              # % de revalorisation de la grille tarifaire
CIBLE_MARGE = 0.175
# le scenario d'atterrissage propose : cinq gestes tenables, aucun spectaculaire
SCENARIO = dict(nao=0.010, encadrement=0.020, heures_vac=0.030,
                caf=0.065, siege=0.050, prix=0.005)

def cadrer(b, constat=None, tend=None, leviers=None, cible=CIBLE_MARGE):
    ct = dict(CONSTAT,    **(constat or {}))
    td = dict(TENDANCIEL, **(tend    or {}))
    lv = dict(LEVIERS,    **(leviers or {}))
    u  = lambda k: b[k][2026] / b["EFF"][2026]          # cout unitaire 2026

    eff = b["EFF"][2026] * (1 + ct["croiss_eff"])
    ins = b["INSCRITS"][2026] / b["EFF"][2026] * eff     # taux d'entree maintenu
    ca  = b["CA"][2026] / b["EFF"][2026] * (1 + ct["prix"] + lv["prix"]) * eff
    ca0 = b["CA"][2026] / b["EFF"][2026] * (1 + ct["prix"]) * eff

    # colonne 1 : le tendanciel, toujours calcule SANS levier, il ne bouge jamais
    # colonne 2 : le retenu, apres decision de gestion
    def poste(cle, infl, gain, infl_ret=None):
        return (u(cle) * (1 + infl) * eff,
                u(cle) * (1 + (infl if infl_ret is None else infl_ret)) * eff * (1 - gain))
    p = {}
    p["PERM"]  = poste("PERM",  td["nao"], lv["encadrement"], td["nao"] - lv["nao"])
    p["VAC"]   = poste("VAC",   td["taux_vac"],  lv["heures_vac"])
    p["AUTRE"] = poste("AUTRE", td["inflation"], 0.0)
    p["SIEGE"] = poste("SIEGE", td["inflation"], lv["siege"])
    caf = b["ACQ"][2026] / b["INSCRITS"][2026] * (1 + td["derive_caf"])
    p["ACQ"] = (caf * ins, caf * ins * (1 - lv["caf"]))

    tendanciel = ca0 - sum(v[0] for v in p.values())
    retenu     = ca  - sum(v[1] for v in p.values())
    return dict(eff=eff, inscrits=ins, ca=ca, ca0=ca0, postes=p, caf=caf,
                effet_prix=ca - ca0,
                eb_tendanciel=tendanciel, eb_retenu=retenu,
                eb_cible=cible * ca0, cible=cible,
                ecart=cible * ca0 - tendanciel, solde=cible * ca0 - retenu)

LIB = {"PERM": "Masse salariale permanents", "VAC": "Vacataires",
       "ACQ": "Acquisition etudiants", "AUTRE": "Autres couts campus",
       "SIEGE": "Couts de siege"}
EFFET = {"PERM": ("nao", "encadrement"), "VAC": ("heures_vac",),
         "ACQ": ("caf",), "SIEGE": ("siege",), "AUTRE": ()}

def afficher(b, leviers=None, cible=CIBLE_MARGE):
    r = cadrer(b, leviers=leviers, cible=cible)
    eur = lambda x: f"{x:,.0f}".replace(",", " ")
    print("\n  CONSTAT 2027 — ce que le reseau apporte, non negociable")
    print("    effectifs %s (+%.1f %%)   inscrits %s   CA/eleve %s EUR   CA %s EUR"
          % (eur(r["eff"]), 100 * CONSTAT["croiss_eff"], eur(r["inscrits"]),
             eur(r["ca0"] / r["eff"]), eur(r["ca0"])))
    print("\n  %-28s %13s %13s %13s" % ("", "tendanciel", "retenu", "effet levier"))
    print("  " + "-" * 70)
    print("  %-28s %13s %13s %13s" % ("Chiffre d'affaires", eur(r["ca0"]), eur(r["ca"]),
                                      eur(r["effet_prix"]) if r["effet_prix"] > 1 else "—"))
    for k in ("PERM", "VAC", "ACQ", "AUTRE", "SIEGE"):
        t, x = r["postes"][k]
        print("  %-28s %13s %13s %13s" % (LIB[k], eur(t), eur(x),
                                          eur(x - t) if abs(x - t) > 1 else "—"))
    tt = sum(v[0] for v in r["postes"].values()); tx = sum(v[1] for v in r["postes"].values())
    print("  " + "-" * 70)
    print("  %-28s %13s %13s %13s" % ("Cout complet", eur(tt), eur(tx), eur(tx - tt)))
    print("  %-28s %13s %13s %13s" % ("EBITDA", eur(r["eb_tendanciel"]), eur(r["eb_retenu"]),
                                       eur(r["eb_retenu"] - r["eb_tendanciel"])))
    print("  %-28s %12.2f%% %12.2f%%" % ("Marge", 100 * r["eb_tendanciel"] / r["ca0"],
                                         100 * r["eb_retenu"] / r["ca"]))
    print("\n  CIBLE %.1f %% du CA constate = %s EUR (figee avant cadrage)"
          % (100 * r["cible"], eur(r["eb_cible"])))
    print("  ecart a combler %s EUR    trouve %s EUR    SOLDE %s EUR"
          % (eur(r["ecart"]), eur(r["eb_retenu"] - r["eb_tendanciel"]), eur(r["solde"])))
    return r

# ------------------------------------------------------------- sensibilites
CRAN = dict(nao=0.01, encadrement=0.01, heures_vac=0.01, caf=0.01, siege=0.01, prix=0.005)
LIB_LEV = {"nao": "NAO : 1 pt retire a la politique salariale",
           "encadrement": "Encadrement : +1 % d'eleves par ETP permanent",
           "heures_vac": "Vacataires : -1 % d'heures par eleve",
           "caf": "Acquisition : -1 % de CAF par inscrit",
           "siege": "Siege : -1 % de cout par eleve",
           "prix": "Grille tarifaire : +0,5 % de revalorisation"}

def puissance(b, cible=CIBLE_MARGE):
    """Effet EBITDA d'un cran sur chaque levier, tout le reste inchange."""
    ref = cadrer(b, cible=cible)["eb_retenu"]
    return {k: cadrer(b, leviers={k: v}, cible=cible)["eb_retenu"] - ref
            for k, v in CRAN.items()}

def afficher_puissance(b, cible=CIBLE_MARGE):
    r = cadrer(b, cible=cible); P = puissance(b, cible)
    eur = lambda x: f"{x:,.0f}".replace(",", " ")
    print("\n  PUISSANCE DES LEVIERS — effet d'un cran sur l'EBITDA 2027")
    print("  %-46s %11s %8s %9s" % ("", "effet EUR", "en pts", "% ecart"))
    print("  " + "-" * 78)
    for k, _ in sorted(P.items(), key=lambda x: -x[1]):
        print("  %-46s %11s %7.2f %8.0f %%"
              % (LIB_LEV[k], eur(P[k]), 100 * P[k] / r["ca0"], 100 * P[k] / r["ecart"]))
    return P

if __name__ == "__main__":
    b = base_reelle()
    print("=" * 78)
    print("  CADRAGE 2027 — SANS ACTION (le budget au fil de l'eau)")
    print("=" * 78)
    afficher(b)
    afficher_puissance(b)
    print("\n" + "=" * 78)
    print("  CADRAGE 2027 — SCENARIO D'ATTERRISSAGE")
    print("=" * 78)
    afficher(b, leviers=SCENARIO)
