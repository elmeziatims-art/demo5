# SPÉCIFICATION DES RESTITUTIONS — EDUSERVICES (budget 2027)

But : construire les 3 restitutions dans Tagetik en croisé dynamique.
Pour chacune : **dimensions** (lignes/colonnes) · **éléments** (mesures + composition) · **vue source**.

**Principe : aucune nouvelle vue.** Tout s'appuie sur l'existant :
`V_CAMPAGNES` · `V_MOTEUR` · `V_ALLOCATION` (+ `V_CADRAGE_LEVIERS` pour les leviers).
Les marges/effets sont des **membres calculés** du rapport, jamais une dimension Compte.

---

## 1. RAPPORT « MOTEUR » — acquisition + organique

Objet : expliquer/prouver comment le budget (payant **et** marque) devient des inscrits puis du CA.
Deux blocs, deux grains.

### 1A · Calibration (les coefficients) — grain CAMPUS
**Vue source : `V_CAMPAGNES`** (1 ligne par campus). Regrouper par Marque dans le rapport.

| Élément (mesure) | Colonne de `V_CAMPAGNES` |
|---|---|
| Élasticité **acquisition** | `REND_ACQ` |
| Élasticité **marque (organique)** | `REND_BRAND` |
| Coût par lead (payant) | `CPL` |
| Conversion lead → inscrit | `CONVERSION` |
| CAC marginal | `CAC_MARGINAL` |
| Part organique | `PART_ORG` |
| Leads réf. (total / payants / organiques) | `LEAD_REF` / `PAID_REF` / `ORG_REF` |
| Budget acquisition / marque réf. | `SPEND_ACQ_REF` / `SPEND_BRAND_REF` |

Dimension : `ENTITY` (campus). Membre calculé éventuel : `+10% budget → leads = (1,1 ^ REND_ACQ) − 1`.

### 1B · Effet d'un geste (+Δ%) — grain CAMPUS, ventilable au PROGRAMME
**Vues : `V_CAMPAGNES`** (coeff campus) **+ `V_MOTEUR`** (mix/conversion/prix par maille fine).
Dimensions : `MARQUE ▸ ENTITY ▸ PROGRAMME ▸ AN_ETUDE ▸ MODALITE`.

Éléments = **membres calculés** :

| Élément | Formule (colonnes de vue) | Grain |
|---|---|---|
| Δ budget acquisition | `SPEND_ACQ_REF × Δ%` | campus |
| Leads gagnés (payants) | `PAID_REF × ((1+Δ%) ^ REND_ACQ − 1)` | campus |
| Leads gagnés (organiques) | `ORG_REF × ((1+Δ%marque) ^ REND_BRAND − 1)` | campus |
| Inscrits gagnés | `leads gagnés × CONVERSION` | campus |
| CA gagné | `inscrits gagnés × CA/inscrit réel` | campus |
| CAC marginal du geste | `Δ budget ÷ inscrits gagnés` | campus |

**Ventilation au programme (prorata historique, exact) :**
`leads gagnés du campus × (VOL_LEAD maille ÷ VOL_LEAD campus) × conversion maille × prix maille`
où `VOL_LEAD`, `VOL_NEW`, `REV_STUD`, `REV_FRAIS_INS` viennent de `V_MOTEUR`/socle par maille.
CA/inscrit maille = `(VOL_NEW×REV_STUD + VOL_NEW×REV_FRAIS_INS) ÷ VOL_NEW`.

> Note : l'élasticité vit au **campus** (le budget est décidé au campus). Le programme
> reçoit sa part au prorata historique. Somme des mailles = effet campus, à l'euro près.

---

## 2. RAPPORT « ALLOUÉ » — P&L chargé (avant / après allocation)

**Vue source : `V_ALLOCATION`** (datasource `Q_RAPPORT_ALLOUE`). 1 ligne par classe.
Dimensions : `EXERCICE · VERSION · MARQUE · ENTITY(campus) · PROGRAMME · AN_ETUDE · MODALITE`.
Hiérarchie d'affichage : `MARQUE ▸ Campus ▸ Programme ▸ Année ▸ Modalité`.

| Élément (mesure) | Composition (comptes) / colonne | Depuis `V_ALLOCATION` |
|---|---|---|
| Effectif | `VOL_EFF` | `VOL_EFF` |
| CA | `706 + 7062 + 708` | `CA` |
| Coût vacataires | `621` (aux heures) | `COST_VAC` |
| Coût permanents | `6411` (aux heures) | `COST_PERM` |
| Autres directs + acquisition | `604 + 6063 + 6231` | `COST_ODIR` |
| Structure campus | `6413 + 645 + 613 + 615 + 616 + 625 + 63511` | `COST_STRUCT` |
| Marketing marque (siège) | `6236` | `COST_MARQUE` |
| Holding (siège) | `6414 + 6226 + 626 + 6281 + 6331 + 6333` | `COST_HOLDING` |
| **EBITDA propre** (avant siège) | `CA − (VAC+PERM+ODIR+STRUCT)` | membre calculé |
| **Quote-part siège** | `COST_MARQUE + COST_HOLDING` | `COST_SIEGE` |
| **EBITDA net** (après siège) | `CA − tous les coûts ci-dessus` | `MARGE_COMPLETE` |
| Marge % | `EBITDA net ÷ CA` | membre calculé |

Hors périmètre EBITDA : dotations `6811` (exclues). Contrôle : EBITDA net 2026 = **3 291 530**.

---

## 3. RAPPORT « ÉVOLUTION » — marge chargée dans le temps

**Vue source : `V_ALLOCATION`** (datasource `Q_RAPPORT_EVOLUTION`), filtre `VERSION='ACT'`, `EXERCICE ∈ {2024,2025,2026}`.
Dimensions : `MARQUE ▸ Campus ▸ Programme ▸ Année ▸ Modalité` en lignes · **`EXERCICE` en colonnes**.

| Élément (mesure) | Composition | Depuis `V_ALLOCATION` |
|---|---|---|
| CA | `706 + 7062 + 708` | `CA` |
| EBITDA net | `CA − (621+6411 + 604/6063/6231 + structure + 6236 + holding)` | `MARGE_COMPLETE` |
| **Marge nette %** | `EBITDA net ÷ CA` (par exercice) | membre calculé |
| **Δ (points)** | `Marge 2026 − Marge 2024` (comparaison de colonnes) | membre calculé |

---

## Récapitulatif des vues (rien de nouveau)

| Restitution | Vue(s) | Datasource(s) |
|---|---|---|
| Moteur — calibration | `V_CAMPAGNES` | `Q_MOTEUR_COEFFS` |
| Moteur — effet | `V_CAMPAGNES` + `V_MOTEUR` | `Q_MOTEUR_EFFET` |
| Alloué | `V_ALLOCATION` | `Q_RAPPORT_ALLOUE` |
| Évolution | `V_ALLOCATION` | `Q_RAPPORT_EVOLUTION` |

Clés d'allocation (dans `V_ALLOCATION`, lues de `AW_002_000001_000001`) :
`K1` holding→marque, `K2` marque→campus, `K3` campus→classe, `K4` frais de marque→marque.
