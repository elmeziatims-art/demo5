# EDUSERVICES GROUP — Modèles budgétaires (pré-Tagetik)

Modélisation Excel préparée avant l'implémentation dans **CCH Tagetik**.

## 🎯 Livrable principal — `EDUSERVICES_Modele_Pilotage_Budget.xlsx`

Modèle de **pilotage budgétaire à maille fine**, tout lié, calibré sur des ordres de grandeur
sectoriels sourcés. Générateur : `generer_modele_pilotage.py`.

**Maille :** Marque × Campus × Programme × Niveau × Modalité (initial/alternance) — 58 cellules fines, 14 campus.

| Feuille | Rôle |
|---|---|
| `00_Notice` | Guide + légende + avertissement |
| `01_Note_cadrage` | Objectifs et hypothèses directrices |
| `02_Parametres` | Sélecteur de scénario + leviers + constantes + driver d'allocation |
| `03_Coeff_Strateg` | Coefficients stratégiques par marque (challenger + ou –) |
| `04_Referentiel` | Dimensions : entités, comptes (fixe/variable) — mapping Tagetik |
| `05_Historique` | Réalisé N-1 par cellule : **funnel CRM** (candidatures→inscrits) + effectifs + classes |
| `06_Structure` | Réalisé par campus : loyers, ETP permanents, D&A, m² |
| `07_Moteur` | Moteur de budget par cellule (100 % formules) |
| `08_Allocation` | Frais de structure groupe **alloués par driver** (effectif / CA / m²) |
| `09_PnL` | P&L consolidé N-1 vs Budget + **pont Prix/Volume** |
| `10_Decision` | **Ouvrir/fermer une classe**, remplissage, point mort, scoring 🟢🟡🔴 |
| `11_Simulation` | Tableau de bord : KPIs, scénarios, levier conversion |
| `12_Mapping_Tagetik` | Passerelle : dimensions, versions/snapshot, workflow bottom-up |

### La logique (tout est lié)
1. **Note de cadrage** (% volume & prix globaux) × **coefficients stratégiques** par marque → % appliqué à chaque cellule.
2. **Funnel CRM** : candidatures × croissance × (conversion N-1 + gain conversion) → nouveaux inscrits.
3. **Effectif** = réinscrits + nouveaux → **nombre de classes dérivé** (capacité cible) → coûts d'enseignement.
4. **Contribution** par cellule → **EBITDA** après loyers, personnel permanent, structure allouée.
5. **Décision** : classes nécessaires vs actuelles → signal ouvrir/fermer chiffré ; point mort et scoring par cellule.

### Calibrage (sourcé)
Frais de scolarité 8–11 k€ (initial) · NPEC alternance ~7–10 k€ · CAC ~0,8–2 k€ · marge EBITDA cible ~20 % ·
capacité classe ~30 · ratio d'encadrement calibré. Marques et campus **réels** EDUSERVICES ; montants **illustratifs**.

### Vérifications
- **0 erreur** sur 4 342 cellules (moteur de calcul `formulas`).
- P&L et **pont Prix/Volume réconcilient** exactement.
- Bascule scénario : Cadrage 20,4 % · Optimiste 25,6 % · Prudent 14,4 %.
- Recalcul automatique à l'ouverture activé (Excel calcule les valeurs dès l'ouverture).

## 📄 Version simple (annuelle) — `EDUSERVICES_Budget_Simulation.xlsx`
Première version : budget annuel par campus, plus simple. Générateur : `generer_modele.py`.

## Utilisation
1. Renseigner le réalisé (`05_Historique`, `06_Structure`).
2. Fixer les hypothèses (`02_Parametres`) et les coefficients (`03_Coeff_Strateg`).
3. Choisir le scénario en `02_Parametres!C3` → tout se recalcule.
4. Lire `09_PnL`, `10_Decision`, `11_Simulation`. Basculer vers Tagetik via `12_Mapping_Tagetik`.

## Convention de couleurs
🔵 saisie · ⚫ formule · 🟢 lien inter-feuilles · 🟡 hypothèse clé.
