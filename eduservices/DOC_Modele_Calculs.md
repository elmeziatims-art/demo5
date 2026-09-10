# Modèle de pilotage budgétaire EDUSERVICES — Documentation des calculs

> Référence technique du classeur `EDUSERVICES_Modele_CA_v3.xlsx` (généré par `gen_v3.py`).
> Architecture **budget-driven** : le budget marketing pilote les leads, qui alimentent le funnel jusqu'au CA ; le cadrage top-down pilote CA **et** coûts jusqu'à l'EBITDA/EBIT.

---

## 1. Vue d'ensemble

Le modèle relie une **cible top-down** (direction) au **détail opérationnel** (jusqu'à la cellule marque × ville × programme × année × modalité), dans les deux sens, à partir d'un **scénario historique de référence**.

**Flux général :**

```
Budget marketing €  →  LEADS  →  Candidatures  →  Admis  →  Inscrits (nouveaux) ┐
   (03_Campagnes)      (socle organique + payant)   (funnel mesuré, 04_Moteur)   ├→ EFFECTIF → CA
Effectif année inf.  →  Réinscrits (cohorte × taux de passage) ──────────────────┘        ↓
                                                                                    COÛTS (P&L) → EBITDA → EBIT
```

**Les 8 feuilles :**

| Feuille | Rôle |
|---|---|
| `00_Notice` | Sommaire + principe d'ancrage |
| `01_Cadrage` | Poste de commande CFO : objectif, scénarios, leviers (CA + coûts), coefficients prix |
| `02_Base` | Base de référence unique : historique + paramètres, leads observés, taux mesurés |
| `03_Campagnes` | Moteur d'acquisition (campus) : budget → leads |
| `04_Moteur` | Moteur de CA (cellule) : funnel → effectif → CA |
| `05_Plan_Comptable` | Charte de comptes PCG + double hiérarchie (comptable & gestion) |
| `06_Compta` | Jeu de données chargé (format long, clés + codes version) |
| `07_PnL` | Compte de résultat SIG : N-2 · N-1 · atterrissage · Budget N+1 |

**Principe d'ancrage (fondateur) :** au **budget de référence, tous leviers à 0** (scénario *Référence*), le moteur **reproduit l'historique exactement** (écart mesuré : 0,009 %, pur arrondi). Seul l'**écart** au budget de référence fait bouger les volumes. Le modèle est calé sur le réel, pas une boîte noire.

---

## 2. Base de référence — `02_Base`

Une ligne = une **cellule** : marque × ville × programme × **année** × **modalité**. Version **unique** (dernier atterrissage) : pas de N-1/N-2 pour la projection du CA (ils reviennent seulement côté coûts/P&L).

Colonnes clés :
- **Leads hist** : donnée **observée** (source CRM) — pas reconstruite.
- **Cand / Admis / Nouveaux / Réinscrits / Effectif hist** : le réalisé.
- **Revenu/étudiant** : différencié par **modalité** — alternance (financé OPCO) vs initial (payé étudiant) — et par ville.
- **Taux mesurés** (= aval ÷ amont, donc *mesurés*, pas supposés) :
  - `Taux lead→cand` = Candidatures ÷ Leads
  - `Taux cand→admis` = Admis ÷ Candidatures
  - `Yield (admis→inscrit)` = Nouveaux ÷ Admis
- **Taux de passage** : rétention de la cohorte d'une année à l'autre.

**Grille des taux de funnel** (différenciés, issus de benchmarks secteur — privé non sélectif, déperdition alternance) :

| Taux | Initial | Alternance |
|---|---|---|
| Lead → Candidature | 28 % | 20 % |
| Candidature → Admis | 72 % | 70 % |
| Admis → Inscrit (yield) | 60 % | 42 % |

> L'alternance a un yield plus bas : l'admis doit **signer un contrat entreprise** pour s'inscrire (passage obligé qui ampute la conversion).

---

## 3. Moteur d'acquisition — `03_Campagnes` (niveau campus)

Le budget marketing génère les leads, avec un **socle organique** (indépendant du budget) et une **part payante** à **rendement décroissant**.

```
Leads réf (campus)      = Σ Leads hist des cellules d'entrée du campus
Leads organiques        = Leads réf × part_organique            (fixe, hors budget)
Leads payants réf       = Leads réf × (1 − part_organique)
Budget payant réf       = Leads payants réf × CPL réf
Budget payant actif     = Budget payant réf × (1 + levier_marketing)
Leads payants actif     = Leads payants réf × (Budget actif / Budget réf) ^ rendement
Leads actif TOTAL        = Leads organiques + Leads payants actif
CPL effectif (résultat) = Budget payant actif ÷ Leads payants actif
```

- **Socle organique** (~40 %) : site, salons, Parcoursup, bouche-à-oreille → **couper le budget ne met pas les leads à zéro**.
- **Rendement** (`^0,5`) : rendement décroissant. Doubler le budget payant → **+41 %** de leads (pas +100 %). Le **CPL effectif monte** avec le volume (le lead marginal coûte plus cher).
- **CPL** = coût par lead. Aujourd'hui posé (~40 € × facteur ville) ; en cible, **mesuré** = budget payant réel ÷ leads payants réels.

---

## 4. Moteur de CA — `04_Moteur` (niveau cellule)

### 4.1 Répartition des leads (le mix)
```
Part de leads (cellule) = Leads hist cellule ÷ Σ Leads hist du campus     (années d'entrée)
Leads cellule            = Leads actif TOTAL (campus) × Part de leads
```

### 4.2 Funnel (années d'entrée uniquement)
```
Candidatures = Leads cellule × (taux lead→cand mesuré + gain_conversion_L→C)
Admis        = Candidatures × taux cand→admis mesuré
Nouveaux     = Admis × (yield mesuré + gain_conversion_admis→inscrit)
```

### 4.3 Cohorte (années de poursuite)
```
Réinscrits = Effectif année inférieure × (taux de passage + amélioration_passage)
```

### 4.4 Effectif, prix, CA
```
Effectif      = Nouveaux + Réinscrits
Revenu actif  = Revenu/étudiant × (1 + hausse_tarifaire × coeff_prix[marque×ville])
CA            = Effectif × Revenu actif + Nouveaux × frais_de_dossier
```

> **Vérification d'ancrage :** au scénario *Référence* (tous leviers = 0), `Leads cellule = Leads hist`, donc `Candidatures = Cand hist`, `Nouveaux = Nouv hist`, etc. → le CA reproduit l'atterrissage.

---

## 5. Poste de commande — `01_Cadrage`

### 5.1 Scénarios
Menu : **Référence** (leviers à 0 = reproduit l'atterrissage) · **Cadrage** · **Optimiste** · **Prudent**. La colonne **ACTIF** de chaque levier = `INDEX(Référence:Prudent, MATCH(scénario, en-têtes))`.

### 5.2 Leviers (colonne ACTIF, pilotent le moteur)
| # | Levier | Agit sur |
|---|---|---|
| 1 | Variation du budget marketing | Leads payants (03) |
| 2 | Hausse tarifaire | Revenu actif (04) |
| 3 | Gain taux lead → candidature | Funnel (04) |
| 4 | Gain conversion admis → inscrit | Funnel (04) |
| 5 | Amélioration du taux de passage | Cohorte (04) |
| 6 | **Inflation des charges externes** | Coûts (P&L Budget) |
| 7 | **Politique salariale** | Personnel (P&L Budget) |

### 5.3 Constantes (scénarisables)
Rendement d'acquisition (`0,5`) · Part organique des leads (`40 %`) · Frais de dossier (`90 €`).

### 5.4 Coefficients prix (marque × ville)
Modulent la **sensibilité à la hausse tarifaire** par école (une marque premium peut augmenter plus). À ne pas confondre avec le **niveau** de prix (dans `02_Base`).

### 5.5 Cadrage top-down
```
Reste à trouver = MAX(0 ; Objectif − Budget construit)
```
Le *Budget construit* = total du moteur (scénario actif) ; l'*Objectif* est saisi (jaune).

---

## 6. Coûts & compte de résultat — `05`, `06`, `07`

### 6.1 Plan comptable — `05_Plan_Comptable`
23 comptes PCG : **classe 7** (produits : 706, 7062, 708) et **classe 6** (charges : 60 achats, 61/62 services extérieurs, 63 impôts, 64 personnel, 68 dotations). Chaque compte porte : ligne SIG, agrégat SIG, rattachement (campus/groupe), driver, % du CA, nature V/F.

**Double hiérarchie prête Tagetik :**
- **Comptable (PCG)** : Classe → Poste → Compte.
- **Gestion (SIG, parent→enfant)** : Résultat d'exploitation → EBITDA → Marge de contribution → {Produits, Coûts directs} ; EBITDA → {Personnel, Structure, Impôts} ; Résultat → Dotations.

### 6.2 Compta chargée — `06_Compta`
Format **long** (une ligne = une écriture) : `Code entité · Entité · Marque · Ville · Compte · Poste · Sens · Ligne SIG · Version · Exercice · Montant`.

**3 versions** (dimension Version, codes Tagetik) :
`2023ACT_VDEF` (N-2) · `2024ACT_VDEF` (N-1) · `2025ATT_VDEF` (atterrissage).

**Allocation** : chaque charge est répartie à son niveau naturel (campus / groupe) par son **driver** (part du campus dans le CA, l'effectif ou les classes).

### 6.3 Calibrage des coûts
Les charges sont calées sur une **marge EBITDA cible par version** (progression douce = levier opérationnel réaliste) :

```
Montant charge (compte, version) = %_du_CA × CA_version × (1 − marge_cible) ÷ Σ(%_charges hors D&A)
Montant D&A                       = 6 % × CA_version
CA_version                        = CA_atterrissage ÷ 1,06 ^ (années en arrière)
```

| Version | CA | Marge EBITDA cible |
|---|---|---|
| 2023 (N-2) | 19,5 M€ | 13,2 % |
| 2024 (N-1) | 20,7 M€ | 14,0 % |
| 2025 (Atterr.) | 21,9 M€ | **14,6 %** |

### 6.4 Compte de résultat — `07_PnL`
Cascade SIG alimentée par **`SUMIFS`** sur la compta (par compte × version) :
```
Chiffre d'affaires
 − Coûts directs           → MARGE DE CONTRIBUTION
 − Personnel − Structure − Impôts & taxes → EBITDA
 − Dotations (D&A)         → EBIT
```

### 6.5 Colonne Budget N+1 (pilotée par le cadrage)
Chaque ligne : `Budget = Atterrissage × facteur`, avec un facteur par **nature de compte** :

| Nature | Facteur budget |
|---|---|
| Produits & coûts directs (variables) | `CA moteur ÷ CA atterrissage` |
| Personnel | `(Effectif moteur ÷ Effectif atterr.) × (1 + politique salariale)` |
| Structure / Impôts / Dotations (fixes) | `1 + inflation charges` |

> Le budget CA de la colonne = exactement le total du moteur (scénario actif). En *Référence*, la colonne Budget = l'atterrissage (14,6 %).

---

## 7. Récapitulatif des formules clés

| Grandeur | Formule |
|---|---|
| Leads payants actif | `Leads payants réf × (Budget actif / Budget réf) ^ rendement` |
| Leads actif total | `Leads organiques + Leads payants actif` |
| CPL effectif | `Budget payant actif / Leads payants actif` |
| Part de leads | `Leads hist cellule / Σ Leads hist campus` |
| Candidatures | `Leads cellule × (taux L→C + gain L→C)` |
| Nouveaux | `Candidatures × taux C→A × (yield + gain conv.)` |
| Réinscrits | `Effectif année inf. × (taux passage + amélioration)` |
| Effectif | `Nouveaux + Réinscrits` |
| CA | `Effectif × Revenu × (1 + hausse × coeff_prix) + Nouveaux × frais` |
| Charge (version) | `%_CA × CA_version × (1 − marge_cible) / Σ%_charges` |
| Budget charge | `Atterrissage × facteur_nature` |

---

## 8. Périmètre de démonstration (chiffres calés sur le consolidé 345,8 M€)

- **5 marques** (MBway, ISCOM, Ipac Bachelor Factory, Pigier, Tunon), **14 campus**, **58 cellules**.
- **CA 21,9 M€** · effectif **2 952** · **86 % alternance**.
- **17 197 leads** de référence · budget marketing payant **453 k€** (part organique 40 %).
- **EBITDA 14,6 %** · EBIT 8,6 % · personnel 45,5 % · D&A 6 % (conformes au consolidé).

---

## 9. Ce qui est mesuré vs illustratif (honnêteté)

| Élément | Statut |
|---|---|
| Structure des formules, ancrage, cascade SIG | **Modèle réel**, vérifié (0 erreur, ancrage 0,009 %) |
| Ratios de calibrage (EBITDA 14,6 %, personnel 46 %, D&A 6 %) | Calés sur le **consolidé EDUSERVICES** |
| Leads, CPL, taux de funnel, revenus, montants de charges | **Illustratifs** (ordres de grandeur sectoriels) — en déploiement, **chargés du CRM / de la compta** et **mesurés** |

> En production, leads (CRM), dépense marketing (compta) et taux de conversion ne sont **pas supposés** : ils sont **mesurés** depuis les données sources. Le rôle des valeurs actuelles est de poser une démo réaliste.

---

## 10. Étapes suivantes (non encore construites)

1. Allocation des coûts **jusqu'à la classe** (driver de descente).
2. Flip **CPL mesuré** (budget marketing observé → CPL résultat).
3. Codes version Tagetik étendus (statut, workflow).
4. Bridges de variance (pont d'explication CA & EBITDA).
5. Reporting / dashboards.
