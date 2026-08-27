# Guide de développement Tagetik — Démo EDUSERVICES 2027

Ordre de construction (dépendances), chaque objet avec sa spec et son statut.
On remplit ce guide au fur et à mesure.

**Légende statut**
- ✅ **Livré** — brique de données / spec prête dans le repo (`tagetik/`).
- ⬜ **À développer** — objet à créer dans Tagetik (toi).
- 🔗 **Câblage** — drill-through ou hyperlink à poser.

**Principe de build** : pour chaque écran, on construit dans l'ordre
**① vue SQL → ② objet Tagetik (board/report) → ③ câblage (drill/hyperlink)**.
Une vue expose les clés de dimension → tu fais le multidim par-dessus.
Les ratios (CAC, marge, taux) se calculent **dans la matrice**, jamais dans la vue.

---

## Socle (prérequis — transverses à toute la démo)

| # | Objet | Type | Statut | Note |
|---|---|---|---|---|
| S1 | Dimensions (Entity, Compte, Exercice, Programme, Année/Cycle, Modalité) | Dimensions | ✅ (toi) | Entity : marque→campus ; Compte : nature→EBITDA |
| S2 | Datasets chargés : socle CRM `AW_002_000002_000001`, compta `AW_002_000004_000001` | Datasets | ✅ (toi) | Réel 2024-2026, un seul scénario |
| S3 | Hiérarchie Compte + FST `010-EBITDA` | Hiérarchie + FST | ✅ (toi) | Produits→Coûts directs→Personnel→Structure→Impôts→**EBITDA**→Dotations→EBIT |
| S4 | `MAPPING_COMPTES.csv` — pont nature → rôle d'allocation | Référence | ✅ (repo) | Sert le P&L ② (FST contribution) et l'allocation |

---

## ACTE 1 — Poser le décor (après le chargement : SEUL le cockpit s'affiche)

### ① Vues SQL (briques de données) — toutes ✅ livrées
| # | Vue | Grain / clés | Mesures (additives) | Statut |
|---|---|---|---|---|
| V1 | `V_COCKPIT` | ENTITY × EXERCICE | CA_CRM, CA_COMPTA, ECART_CA, EBITDA, LEADS, INSCRITS, DEPENSE_ACQ | ✅ |
| V2 | `V_PNL` | ENTITY × ACCOUNT × EXERCICE × VERSION | AMOUNT (+ compte statistique EFFECTIF) | ✅ |
| V3 | `V_TENDANCE` | EXERCICE × ENTITY × PROGRAMME × AN_ETUDE × MODALITE | LEADS, INSCRITS, CA, DEPENSE_ACQ, DEPENSE_MARQUE | ✅ |
| V4 | `V_CAC` | idem V3 | DEPENSE_ACQ, LEADS_PAYANTS, LEADS, INSCRITS | ✅ |
| V5 | `V_FUNNEL` | idem V3 | LEADS, CANDIDATS, ADMIS, INSCRITS | ✅ |
| Q1 | `Q_CA_CONSTITUTION_CRM` | drill-through (POV cellule) | Effectifs, tarif moyen, CA scolarité, CA frais insc., CA total | ✅ |
| Q2 | `Q_CA_CONSTITUTION_COMPTA` | drill-through (POV cellule) | Montant par compte de produit (706/7062/708) | ✅ |

### ② Objets Tagetik à développer
**T1 — Board « Cockpit »**  ⬜
- Source : `V_COCKPIT`, niveau **Groupe**.
- Contenu : bandeau réconciliation (`CA_CRM` = `CA_COMPTA`, `ECART_CA` = 0) ;
  6 tuiles KPI : **CA · EBITDA · Marge % · Leads · Inscrits · CAC**.
- Graphes : 1 **sparkline** par tuile (série 2024→2026) ; CAC marqué « tension ».
- Ratios : Marge % = ΣEBITDA/ΣCA ; CAC = ΣDEPENSE_ACQ/ΣINSCRITS (dans le board).
- Réf. rendu : feuille `Cockpit` de `MAQUETTES_RAPPORTS.xlsx`.

**T2 — Report « P&L ① »** (compte de résultat comparatif)  ⬜
- Source : `V_PNL` (VERSION = `ACT`), via le **FST 010-EBITDA**.
- Lignes : hiérarchie Compte → EBITDA → EBIT. Colonnes : Exercice **2024/2025/2026**.
- POV : Marque (vide = groupe). Réf. rendu : feuille `P&L ①`.

**T3 — Report « Tendance »** (fin du Bloc 1)  ⬜
- Source : `V_TENDANCE`. Graphe **2 courbes base 100** : Activité (CA) vs Dépenses acq.
- Réf. rendu : graphe de la feuille `Cockpit`.

**T4 — Report « Funnel & CAC »** (un seul rapport)  ⬜
- Source : matrice multidim sur `V_FUNNEL` + `V_CAC`.
- Contenu : funnel (leads→cand→admis→inscrits + taux) **et** CPL/CAC, par marque + Groupe.
- POV : Groupe, drill marque → campus. Réf. rendu : feuille `Funnel & CAC`.

### ③ Câblage (navigation)
| # | Depuis | Vers | Mécanisme | Statut |
|---|---|---|---|---|
| C1 | Cockpit · tuile **CA** | Constitution du CA (Q1 ‖ Q2) | drill-through ×2 | 🔗 |
| C2 | Cockpit · tuile **EBITDA/Marge** | Report P&L ① (T2) | hyperlink (POV groupe) | 🔗 |
| C3 | Cockpit · tuile **CAC** | Report Funnel & CAC (T4) | hyperlink (POV groupe) | 🔗 |
| C4 | P&L ① · ligne **marque** | P&L POV marque → campus | hyperlink | 🔗 |
| C5 | Funnel & CAC · cellule **campus** | Funnel du campus | hyperlink (POV campus) | 🔗 |

**Ordre de dev conseillé Acte 1 :** T2 (P&L, le plus simple, FST natif) → T4 (Funnel & CAC) → T3 (Tendance) → T1 (Cockpit, qui référence les autres) → câblages C1..C5.

---

## ACTE 2 — Diagnostiquer & construire *(à détailler à l'étape suivante)*
Cadrage → arbitrage des caps → moteur → levier prix → 3 scénarios → bridge → **P&L ②** (marge directe, 2ᵉ FST) → soumission V1.
Vues concernées : `V_CADRAGE_LEVIERS`, `V_CAP_ARBITRAGE`, `V_MOTEUR`, `V_BUDGET`, `Q_SCENARIOS`, `V_BRIDGE_CA`.

## ACTE 3 — Révéler le coût complet *(à détailler)*
Allocation à la classe (`V_ALLOCATION`) → **P&L ③** coût complet par marque. Le seul acte qui déplace des montants entre entités (moteur d'allocation).

## ACTE 4 — Agir & boucler *(à détailler)*
Contribution campus → ouverture/fermeture de classe → V2 → **P&L ④** (V1 vs V2 × 3 scénarios) → boucle CAC → clôture.

---
*Colonne vertébrale : le même P&L comparatif revient 4 fois — ① ouverture · ② après construction · ③ coût complet · ④ V1 vs V2.*
