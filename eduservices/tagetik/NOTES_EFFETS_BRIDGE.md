# Méthode — Analyse d'écart (bridge PVM) & décomposition du CAC

Note de référence pour narrer les bridges de la démo. À réutiliser tel quel.

## Le concept : le bridge PVM (Prix / Volume / Mix)

Un **bridge** (ou analyse d'écart) décompose une **variation** en ses **causes**.
C'est un classique du contrôle de gestion / FP&A, et le cœur de ce qu'un EPM
(Tagetik) sait produire.

- Sur le **chiffre d'affaires** (une somme : CA = Σ prix × volume) → décomposition
  **propre** en : **effet volume** (vendre plus), **effet prix** (tarifs), **effet mix**
  (répartition produits). C'est le bridge le plus canonique. → **Acte 3** (`V_BRIDGE_CA`).
- Sur un **ratio** (ex. CAC = dépenses / inscrits) → même logique, variante « ratio » :
  **effet numérateur** (dépenses) + **effet dénominateur** (volume).

## La décomposition du CAC (2025 → 2026)

`CAC = dépenses d'acquisition ÷ inscrits`

| | Dépenses | Inscrits | CAC |
|---|--:|--:|--:|
| 2025 | 394 702 | 1 159 | **340,6 €** |
| 2026 | 434 174 | 1 229 | **353,3 €** |

Variation : **+12,7 €**. On la sépare en deux forces :

**① Effet dépenses = +34 €**  *(on fige les inscrits à 2025)*
```
434 174 / 1 159 = 374,6 €   →   374,6 − 340,6 = +34 €
```
→ dépenser ~39 k€ de plus sur le **même** nombre d'étudiants alourdit le coût/tête de +34 €.

**② Effet volume = −21 €**  *(on passe aux inscrits 2026)*
```
434 174 / 1 229 = 353,3 €   →   353,3 − 374,6 = −21 €
```
→ répartir la **même** dépense sur **plus** d'étudiants dilue le coût/tête de −21 €.

**Net : +34 − 21 = +13 €**  →  CAC 341 € → 353 €.

## L'intuition (à dire)

> « Plus d'inscrits = **bon** pour le CAC (ça dilue la dépense). Plus de dépenses =
> **mauvais**. Ici la dépense l'emporte sur le volume → le CAC monte quand même.
> L'enjeu du budget 2027 : faire croître le volume **sans** laisser filer le CAC. »

## Méthode & limite (à connaître)

- Méthode utilisée : **séquentielle** — effet dépenses à volume constant (base 2025),
  puis effet volume à dépenses 2026. Le total **réconcilie toujours** exactement.
- Limite du ratio : quand numérateur ET dénominateur bougent, il existe un petit
  **terme d'interaction**. Selon la convention (affecté au volume, aux dépenses, ou
  isolé), le split bouge **légèrement** — pas le total. Sur le **CA** (somme), pas de
  ce souci : la décomposition prix/volume/mix est propre. → le bridge de CA est le
  plus « canonique ».

## Réglages du graphe waterfall

- Écarts petits devant la base (~30 € sur ~345 €) → **tronquer l'axe** (ex. 320-385)
  + **étiquettes de valeurs**, sinon les pas sont écrasés. Troncature légitime tant
  que l'axe est étiqueté.
- Alternative sans troncature : **barres de contribution** autour de zéro (+34 / −21).
