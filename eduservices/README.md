# EDUSERVICES GROUP — Modèle de pilotage budgétaire (v2)

Modèle Excel de pilotage budgétaire à maille fine, préparé avant implémentation dans **CCH Tagetik**.
Générateur : `gen_v2.py` (+ socle de données `gen_v2_data.py`). Livrable : **`EDUSERVICES_Modele_Pilotage_Budget.xlsx`** (15 feuilles).

## Maille
Marque × Campus × Programme × **Année d'études** × Modalité (initial/alternance) — ~58 cellules, 14 campus, **~82 % alternance**.

## Les feuilles
| # | Feuille | Rôle |
|---|---|---|
| 00 | Notice | Guide + légende |
| 01 | **Objectifs** | Cadrage top-down : CA & EBITDA **cibles €** → écart vs budget construit |
| 02 | Leviers | Hypothèses de pilotage + scénario + constantes de référence |
| 03 | Coeff_Strateg | Coefficients stratégiques par marque (marketing / prix) |
| 04 | Referentiel | Dimensions, comptes (fixe/variable) |
| 05 | **Param_Prog_Annee** | Données de référence **par programme × année** (capacité, heures, taux, pédago, CAC variable, taux de passage) |
| 06 | Historique | Réalisé N-1 par cellule + **historique marketing N-2/N-1 → élasticité mesurée** |
| 07 | Structure | Réalisé par campus |
| 08 | Moteur | Budget par cellule : **cohortes**, **marketing→volume**, seuil = **point mort** |
| 09 | Allocation | Frais de structure alloués par driver |
| 10 | PnL | P&L consolidé N-1 vs Budget + **pont à 4 effets** |
| 11 | **Simulateur** | Décisions ouvrir/fermer/redistribuer → **EBITDA AVANT → APRÈS** |
| 12 | **Sensibilite** | Impact € sur l'EBITDA **par levier** (sens unique) |
| 13 | Simulation | KPIs, taux d'alternance/sécurisation, **€ à sécuriser** |
| 14 | Mapping_Tagetik | Passerelle Tagetik |

## Logique clé (tout est mesuré / lié)
- **Cohortes** : effectif d'une année budget = effectif de l'année inférieure N-1 × **taux de passage** (réinscription **dès la 2ᵉ année**). Les entrants (B1/M1/BTS1) viennent du funnel marketing.
- **Marketing → volume, mesuré sur l'historique** : `élasticité = %Δ candidatures ÷ %Δ marketing` (N-2→N-1). Augmenter le budget marketing → + candidatures → + inscrits → **ROI net** visible.
- **CAC en deux composantes** : global partagé (groupe) + variable par programme (achat de leads).
- **Seuil d'ouverture = point mort calculé** (pas un chiffre en dur).
- **Alternance / financement** : sécurisation ≤ 3 mois → OPCO rétroactif 100 % ; reste à charge **employeur** (recouvrement paramétrable, défaut **100 % légal**). Le **taux de sécurisation** pilote l'**exposition** (« € à sécuriser ») ; son effet **EBITDA** n'apparaît que si le recouvrement < 100 %.
- **Cadrage top-down** : cibles CA/EBITDA € → écart → à combler via les leviers (voir Sensibilité).

## Vérifications
- **0 erreur** sur 5 273 cellules (moteur `formulas`).
- Marge EBITDA **N-1 19,1 % · Budget 20,0 %** ; scénarios Cadrage 20 % · Optimiste 27 % · Prudent 19 %.
- Pont CA (Volume/Tarif/Sécurisation/Frais) **réconcilie exactement**.
- Élasticité marketing **mesurée** (~0,5) ; simulateur et marketing→volume **dynamiques** ; recalcul auto à l'ouverture.

## Convention de couleurs
🔵 saisie · ⚫ formule · 🟢 lien inter-feuilles · 🟡 hypothèse à remplir.

> Marques/campus **réels** EDUSERVICES, montants **illustratifs** calibrés sur des ordres de grandeur sourcés (scolarité 8-11 k€, NPEC ~7-10 k€, marge ~20 %, classe ~30). À remplacer par le réel.
