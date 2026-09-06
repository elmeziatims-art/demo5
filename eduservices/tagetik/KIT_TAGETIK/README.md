# KIT TAGETIK — EDUSERVICES · Budget 2027 (scénario 2027BUD_V1)

Tout pour reproduire le modèle : **3 fichiers de charge** + **8 vues HANA**.
Principe : on **charge** le socle, la compta et le cadrage ; **tout le reste
est calculé à la volée par des vues** (campagnes, cap, moteur, budget,
allocation, P&L). Multi-exercice sur **un seul scénario** (`2027BUD_V1`),
les versions `V01/V02/V03` = Cadrage / Optimiste / Prudent.

---

## 1. Fichiers de charge (`1_charge/`)

Colonnes **métier uniquement** (Tagetik regénère USERUPD/DATEUPD/PROVENIENZA).
Séparateur `;`, décimale `,`.

| Fichier | Table | Grain | Colonnes |
|---|---|---|---|
| `AW_002_000002_000001_SOCLE.csv`   | Socle (volumes) | ENTITY × PROGRAMME × AN_ETUDE × MODALITE × EXERCICE | SCENARIO;PERIODE;ENTITY;PROGRAMME;AN_ETUDE;MODALITE;EXERCICE;VOL_LEAD;VOL_CAND;VOL_ADMIS;VOL_NEW;VOL_REINS;VOL_EFF;VOL_EFF_INF;VOL_CLASS;REV_STUD;REV_FRAIS_INS |
| `AW_002_000004_000001_COMPTA.csv`  | Compta | ENTITY × ACCOUNT × EXERCICE | ENTITY;ACCOUNT;EXERCICE;SCENARIO;PERIOD;AMOUNT |
| `AW_002_000001_000001_CADRAGE.csv` | Cadrage (leviers, cibles, clés) | ENTITY × VERSION × PARAMETRE | SCENARIO;PERIODE;ENTITY;VERSION;PARAMETRE;MEASURE;KEY_ALLOC |

**Ordre de chargement** : Socle → Compta → Cadrage (indépendants, ordre libre).

### Conventions de modélisation figées
- **Leviers `HYP_*`** : stockés **par version** (V01/V02/V03) sur ENTITY=GRP.
- **Cibles `TEC_PL` / `TEC_EBITDA`** : stockées **une seule fois sur `VERSION=GEN`**
  (l'ambition ne varie pas par scénario). *(déjà nettoyé dans ce fichier)*
- **Coef prix par marque `HYP_PRICE_COEF`** : sur `GEN`, ENTITY=`<MARQUE>_REF`.
- **Clés d'allocation `ALLOC_*`** : sur `GEN`.
- **Montants compta positifs** ; le sens produit/charge est porté par le COMPTE.

---

## 2. Vues (`2_vues/`) — ORDRE DE CRÉATION

Chaque vue dépend des précédentes → créer **dans cet ordre** :

```
1. V_CADRAGE_LEVIERS   (pivot des leviers par version)
2. V_SOCLE_KPI         (taux & KPI du funnel)
3. V_CAMPAGNES         (rendements acquisition/marque par campus)
4. V_CAP               (cap stratégique + budget rejoué)
5. V_MOTEUR            (CA construit 2027 : funnel × leviers × cap)   → par version
6. V_BUDGET            (P&L 2027 construit, au grain compte)          → par version
7. V_ALLOCATION        (coût complet par classe, clés d'allocation)
8. V_PNL               (P&L unifié 2024-2026 réel + 2027 budget)
```

> `V_MOTEUR` lit le coef prix par une sous-requête interne sur le cadrage
> (`HYP_PRICE_COEF`) — pas de vue séparée à créer.

---

## 3. À créer côté référentiel : compte statistique `EFFECTIF`

`V_PNL` embarque l'effectif comme un **compte `EFFECTIF`** (réel ← socle,
budget ← moteur). Dans la dimension **Compte**, ce membre doit être :
- **statistique** (HORS hiérarchie P&L — ne remonte pas dans CA/EBITDA),
- **non monétaire** (pas de €), agrégation **SUM** sur les entités.

Les ratios **CA/étudiant** et **EBITDA/étudiant** se calculent alors dans la
**matrice Tagetik** (compte financier ÷ compte EFFECTIF).
*(Si tu utilises un autre code que `EFFECTIF`, remplace-le dans `V_PNL.sql`.)*

---

## 4. Contrôles (tie-out) après création des vues

```sql
-- P&L : EBITDA par exercice/version (via la hiérarchie de comptes Tagetik)
--   2024 ACT ≈ 2 648 550 (13,2%)   2025 ACT ≈ 2 977 604 (14,0%)
--   2026 ACT ≈ 3 291 530 (14,6%)   2027 V01 ≈ 3 875 895 (16,1%)
-- Effectif (compte EFFECTIF) : 2024=2704 · 2025=2860 · 2026=3036 · 2027 V01≈3175
-- CA construit 2027 V01 (V_MOTEUR) : 24 120 981
```

> Écart Excel vs Tagetik sur 2027 : le dataset utilise **prix +2,0 %** (V01)
> là où le prototype Excel était à +2,5 % — d'où EBITDA 3,88 M€ vs 3,99 M€.
> C'est le chiffre juste côté Tagetik.
