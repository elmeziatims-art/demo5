# EDUSERVICES GROUP — Modèle de pilotage budgétaire (v2)

Modèle Excel de pilotage budgétaire à maille fine, préparé avant implémentation dans **CCH Tagetik**.
Générateur : `gen_v2.py` (+ socle de données `gen_v2_data.py`). Livrable : **`EDUSERVICES_Modele_Pilotage_Budget.xlsx`** (16 feuilles).

## Maille
Marque × Campus × Programme × **Année d'études** × Modalité (initial/alternance) — ~58 cellules, 14 campus, **~82 % alternance**.

## Les feuilles
| # | Feuille | Rôle |
|---|---|---|
| 00 | Notice | Guide + légende |
| 01 | **Objectifs** | Cadrage top-down : CA & EBITDA **cibles €** → écart vs budget construit |
| 02 | Leviers | Hypothèses de pilotage + scénario + constantes de référence |
| 03 | Coeff_Strateg | Coefficients stratégiques **par marque × campus** (marketing / prix) |
| 04 | Referentiel | Dimensions, comptes (fixe/variable) |
| 05 | **Param_Prog_Annee** | Données de référence **par programme × année** (capacité, heures, taux, pédago, CAC variable, taux de passage) |
| 06 | Historique | Réalisé N-1 par cellule + **historique marketing N-2/N-1 → élasticité mesurée** |
| 07 | Structure | Réalisé par campus |
| 08 | Moteur | Budget par cellule : **cohortes**, **marketing→volume**, seuil = **point mort** |
| 09 | Allocation | Frais de structure alloués par driver |
| 10 | PnL | P&L consolidé N-1 vs Budget + **pont à 4 effets** |
| 11 | **Simulateur** | Décisions ouvrir/fermer/regrouper (**maille promo**, garde-fou capacité) → **EBITDA AVANT → APRÈS** |
| 11b | **Mutualisation** | Regroupement inter-sections (**maille campus × cycle**) : sections économisables & économie potentielle |
| 12 | **Sensibilite** | Impact € sur l'EBITDA **par levier** (sens unique) |
| 13 | Simulation | KPIs, taux d'alternance/sécurisation, **€ à sécuriser** |
| 14 | Mapping_Tagetik | Passerelle Tagetik |

## Logique clé (tout est mesuré / lié)
- **Cohortes** : effectif d'une année budget = effectif de l'année inférieure N-1 × **taux de passage** (réinscription **dès la 2ᵉ année**, rétention **93–96 %**). Les entrants (B1/M1/BTS1) viennent du funnel marketing.
- **Capacité de classe CONSTANTE par cycle** (Bachelor 32, Mastère 26, BTS 30) : une salle ne rétrécit pas d'une année à l'autre.
- **Coefficients stratégiques par marque × campus** : on peut pousser le marketing/prix différemment à Paris et à Bordeaux pour une même marque.
- **Regroupement à deux mailles** : *simulateur* (promo, garde-fou capacité de la promo) et *mutualisation* (campus × cycle, plancher = arrondi.sup(effectif/capacité), jamais de dépassement).
- **Marketing → volume, mesuré sur l'historique** : `élasticité = %Δ candidatures ÷ %Δ marketing` (N-2→N-1). Augmenter le budget marketing → + candidatures → + inscrits → **ROI net** visible.
- **CAC en deux composantes** : global partagé (groupe) + variable par programme (achat de leads).
- **Seuil d'ouverture = point mort calculé** (pas un chiffre en dur).
- **Alternance / financement** : sécurisation ≤ 3 mois → OPCO rétroactif 100 % ; reste à charge **employeur** (recouvrement paramétrable, défaut **100 % légal**). Le **taux de sécurisation** pilote l'**exposition** (« € à sécuriser ») ; son effet **EBITDA** n'apparaît que si le recouvrement < 100 %.
- **Cadrage top-down** : cibles CA/EBITDA € → écart → à combler via les leviers (voir Sensibilité).

## Précisions d'architecture (données vs décisions)
- **Frais de structure & marketing groupe = montant FIXE** (siège, IT, marque), alloué par driver — plus un % du CA.
- **CAC** : global (fixe, en structure) + **variable par programme** (achat de leads, per inscrit).
- **Sécurisation N-1** et **conversion candidature→inscrit** : **déduites de l'historique** (par programme / par cellule), puis bougées par les curseurs. Les valeurs globales ne sont que des replis.
- **Coût ETP permanent** ~58 k€ chargé ; **taux de passage** B1→B2 85 %…

## Simulateur & conseil de décisions (feuille 11) — logique CFO
Cascade à deux niveaux : **CA − coûts directs évitables = MARGE DE CONTRIBUTION** (la métrique de décision) puis **− structure allouée = résultat tout compris** (info). Principe : **on décide sur la contribution, jamais sur le résultat tout compris** — car la **structure (loyer, permanents, siège) est non-évitable** : fermer une promo ne l'économise pas, elle **se redilue** sur les autres (indicateur *structure/étudiant avant → après*). Reco : 🔴 Ne pas ouvrir (contribution < 0) · 🟢 Ouvrir +1 (saturé) · 🟡 Surveiller (sous-rempli mais contribution positive → **garder**) · 🟢 Maintenir.

## Calibrage sur le réel (comptes consolidés EDUSERVICES 4.0, clos 31/08/2025)
Le modèle (échantillon représentatif ~20 M€ de CA) ne prétend pas reproduire les montants réels — que le groupe ne partagera jamais à cette maille — mais **reproduit les ratios** du consolidé (CA 345,8 M€). Structure de coûts en % du CA :

| Poste | Modèle | Réel (conso 4.0) | Source du montant unitaire |
|---|---|---|---|
| **Personnel total** | **45,5 %** | **46,0 %** | compte de résultat consolidé |
| · enseignement (vacation) | 18,8 % | — | taux horaire chargé 55-74 € × heures/classe |
| · permanents | 26,7 % | — | ~1 ETP / 26 étudiants, coût chargé 58 k€ (SIRH type) |
| Achats/autres + pédagogie | 16,9 % | ~16-17 % | 934 €/étu autres + 350-670 €/étu pédago |
| Loyers | 11,0 % | ~9-11 % | 11 % du CA (immobilier écoles urbaines) |
| Marketing variable | 2,0 % | — | CAC 250-600 €/lead (achat de leads, benchmark web) |
| Structure / siège (fixe) | 10,0 % | — | 2 M€ fixe (siège, IT, marque, équipe centrale) |
| **D&A** | **6,0 %** | **6,0 %** | % du CA (consolidé) |
| **EBITDA** | **14,6 %** | **14,6 %** | consolidé |
| **CA / étudiant** | **8 276 €** | **~8 232 €** | consolidé (scolarité + frais + OPCO) |

Effectif 2 415 · **alternance 82 %** · 5 marques · 14 campus.

> **Coût pédago/étu** = coût de *production* de la formation par étudiant, **hors salaires des intervenants** (ceux-ci sont dans « enseignement ») : supports & ressources, licences logicielles pédagogiques, LMS, jury/examens, certifications, consommables/projets. 350-670 €/an selon le domaine.

## Vérifications
- **0 erreur** sur ~5 500 cellules (moteur `formulas`).
- Marge EBITDA **N-1 14,6 %** (= réel) ; pont CA (Volume/Tarif/Sécurisation/Frais) **réconcilie exactement**.
- Fermeture d'une promo : EBITDA groupe = − contribution (structure inchangée, rediluée) — **vérifié**.
- Élasticité marketing **mesurée** ; simulateur, reco et marketing→volume **dynamiques** ; recalcul auto à l'ouverture.

## Convention de couleurs
🔵 saisie · ⚫ formule · 🟢 lien inter-feuilles · 🟡 hypothèse à remplir.

> Marques/campus **réels** EDUSERVICES, montants **illustratifs** calibrés sur des ordres de grandeur sourcés (scolarité 8-11 k€, NPEC ~7-10 k€, marge ~20 %, classe ~30). À remplacer par le réel.
