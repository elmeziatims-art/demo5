# Spécification de mise en forme — cockpit EDUSERVICES

À reproduire dans Tagetik. Le fichier `COCKPIT_TAGETIK.xlsx` en est le rendu de
référence : il part de votre navigation du 07/09, la restyle et corrige cinq
défauts. Ce document dit **quoi poser, où, et pourquoi**.

La référence visuelle est vos trois rapports de démo Tagetik (E150, E221, E223).

---

## 1. Le système, en une page

### Police — Arial, et rien d'autre

| Rôle | Police | Taille | Graisse | Couleur |
|---|---|---|---|---|
| Titre de page | Arial | 14 | gras | blanc sur `262626` |
| Sous-titre | Arial | 8 | normal | `A6D0EA` |
| Phrase de réponse (drills) | Arial | 12,5 | gras | `262626` |
| Titre de bloc | Arial | 9,5 | gras | `262626` |
| En-tête de tableau | Arial | 8 | gras | `262626` |
| Corps de tableau | Arial | 8 | normal | `262626` |
| Grand nombre (carte KPI) | Arial | **20** | normal | `262626` |
| Libellé de carte | Arial | 7 | gras | `6B7075` |
| Note, source, légende | Arial | 7 | italique | `6B7075` |

**Fira Sans est abandonnée.** Vos trois rapports de référence n'utilisent
qu'Arial ; c'est ce qui rend correctement sur Tagetik Web, où une police non
installée retombe silencieusement sur autre chose.

### Palette — celle de votre thème Tagetik

```
262626   encre, bandeau, filets de total          (dk1)
007AC3   azur Tagetik : filets d'accent, séries   (accent1)
E5202E   rouge sémantique                          (accent2)
85BC20   vert sémantique                           (accent3)
A6D0EA   bleu pâle : barres de données, série N-2  (accent5)
E7E6E6   gris clair : fond des lignes de total     (lt2)

Deux variantes assombries, pour le TEXTE uniquement — E5202E et 85BC20
manquent de contraste en 8 pt sur fond clair :
5F8A17   vert de texte          C41822   rouge de texte

Nos deux ajouts :
F5F6F7   fond de page (le seul écart à la référence, voir §2)
D5D7DA   filet fin
6B7075   texte secondaire
```

Échelle de couleur, dérivée des deux accents :
`F6C9CC` bas · `F4F4F2` milieu · `DCEBC0` haut.

### Grammaire — des filets, pas des aplats

Vos rapports de référence ne contiennent **aucun remplissage** autre que le
blanc. Toute la structure est portée par des traits horizontaux :

```
trait fin    D5D7DA   sous chaque ligne de données
trait fin    262626   sous une ligne de sous-total
trait medium 262626   au-dessus et au-dessous d'un total
trait medium 007AC3   sous une ligne d'en-tête, et au-dessus d'une carte KPI
```

**Aucun trait vertical, nulle part.**

---

## 2. Le seul écart assumé à la référence

Le fond de page est `F5F6F7`, pas blanc, et les lignes servies sont blanches.

Ce n'est pas un choix esthétique : c'est ce qui fait qu'**une ligne non servie
disparaît**. Le tableau couvre 83 lignes de règles pour absorber n'importe quel
nœud ; lancé sur Tunon il n'en sert que 3. Sur fond blanc, les 80 lignes vides
bordées se lisent comme un tableau vide. Sur fond gris, elles n'existent pas.

D'où la règle qui en découle : **le fond et les bordures des lignes de données
ne sont jamais posés en dur**. Ils viennent uniquement des règles de niveau,
qui ne se déclenchent que si la ligne porte un niveau.

---

## 3. Cockpit — la géométrie

| Ligne | Contenu | Hauteur |
|---|---|---|
| 1–3 | bandeau `262626` · titre en C2, sous-titre en C3 | 6 / 22 / 13 |
| 4 | **filet d'accent `007AC3` pleine largeur** | 3 |
| 5 | filtres : Scénario C, Version G, Entité K | 18 |
| 7 | filet `007AC3` en tête de carte, colonnes F à Q | 3 |
| 8–10 | six cartes KPI, panneau blanc | 12 / 24 / 13 |
| 12 | titres des trois graphes | 18 |
| 13–33 | les trois graphes | 14 |
| 36 | titre du tableau | 18 |
| 37 | en-têtes | 26 |
| 38 → | données | 14,25 |

### Colonnes

| Col | Contenu | Largeur |
|---|---|---|
| A | gouttière | 2,4 |
| **B** | **niveau 2/3/4/5 — MASQUÉE** | 4,5 |
| C | Entité | 30 |
| D | Programme | 13 |
| E | Modalité | 11 |
| F → Q | les douze mesures | 10,7 |
| R → | bloc technique et zones de restitution — **masquées** | |

### Les six cartes KPI

Elles occupent F à Q, deux colonnes chacune, **alignées sur le bloc chiffré** —
pas sur les colonnes d'identité. Chaque carte : un filet `007AC3` de 3 px en
ligne 7, un panneau blanc sur 8–10, un filet `D5D7DA` en bas.

```
ligne 8   libellé      Arial 7 gras 6B7075, en majuscules
ligne 9   valeur       Arial 20, format 0.0,," M€" ou #,##0 ou 0.0%
ligne 10  variation    Arial 8 gras, format à flèche
```

**Le format de nombre porte la flèche, la règle conditionnelle porte le
jugement.** `"▲ "0.0%;"▼ "0.0%;"—"` donne le sens ; la couleur dit si c'est une
bonne nouvelle. Sur le coût d'acquisition les deux sont **inversés** : une
flèche vers le haut est rouge.

Sous le million, une règle conditionnelle bascule le format de `0.0,," M€"` vers
`#,##0" €"` — sans elle, un EBITDA de 81 728 € s'affiche « 0,1 M€ », ce qui
arrive dès qu'on descend sur Tunon.

### Les trois graphes — titres numérotés

```
01 · LES MOTEURS DE LA VARIATION      pont d'EBITDA 2025 → 2026
02 · PERFORMANCE PAR ENTITÉ           marge EBITDA, trois exercices
03 · ACQUISITION & INSCRIPTIONS       base 2024 = 100
```

- **01** colonnes empilées : socle invisible, ancre `262626`, hausse `85BC20`,
  baisse `E5202E`. Pas de légende. Axe **libre** — il était figé 3–5 M€ et le
  graphe sortait vide sur les cinq marques.
- **02** barres **horizontales** groupées : `A6D0EA` / `4FA3D9` / `007AC3`.
  L'horizontale se lit mieux avec cinq libellés longs.
- **03** courbe à marqueurs : dépenses `E5202E`, inscrits `007AC3`, axe 95–125.

Les séries pointent des **plages internes** (`'Cockpit'!$AD$7:$AD$11`), **jamais
un nom défini** : un nom défini porte le nom du classeur, et Excel supprime la
série dès que le fichier est renommé.

### Les règles conditionnelles, dans l'ordre

1. **Échelle de couleur**, bornes **absolues** — Marge EBITDA (col K) 2 % / 12 %
   / 22 % ; Remplissage (col N) 55 % / 75 % / 95 %. Absolues et non
   percentiles : un campus doit garder sa couleur quand on change de périmètre.
2. **Barre de données** sur Part EBITDA (col J), `A6D0EA`, bornée 0 → 100 %.
   La barre dit une **magnitude**, l'échelle une **performance**. On ne met
   jamais les deux sur la même colonne.
3. **Variations** (G, I, L) : couleur de police seule, `5F8A17` / `C41822`. Une
   règle qui ne pose qu'une couleur de police se compose par-dessus tout le
   reste.
4. **Les quatre niveaux**, pilotés par `$B` sur `B38:Q120` :

| Niveau | Fond | Graisse | Filet |
|---|---|---|---|
| 2 groupe | `E7E6E6` | gras | medium `262626` dessus et dessous |
| 3 marque | blanc | gras | fin `262626` dessous |
| 4 campus | blanc | normal | fin `D5D7DA` dessous |
| 5 classe | blanc | normal `6B7075` | hairline `D5D7DA` |

**Un seul aplat, celui du total.** Les autres niveaux se distinguent par la
graisse et le filet — c'est la grammaire de vos rapports de référence, et c'est
beaucoup plus léger à l'écran que trois aplats de bleu.

---

## 4. Drill EBITDA 2 — les trois demandes

### La colonne Nature, à droite

Colonne I, après « Part des charges ». Elle **traduit** la famille, elle ne
l'invente pas :

```
=SI($C34="";"";SI($C34="Produits";"produit";SI($C34="Siège";"allocation";"charge")))
```

`produit` en `5F8A17`, `allocation` en `007AC3`, `charge` en gris — trois règles
d'expression sur `I34:I49`.

### L'échelle de couleur sur la variation

Sur **`G37:G49` seulement**, pas sur les seize lignes. La variation du chiffre
d'affaires vaut +1 147 240 € et celle d'un poste de charge −72 000 € : une
échelle commune serait écrasée par le CA et les treize charges tomberaient
toutes au milieu, indistinctes. **On ne chauffe pas un produit contre une
charge, ce sont deux populations.** Les trois lignes de produit gardent la
flèche et la couleur de police, qui suffisent.

Échelle : `min → F6C9CC`, `0 → F4F4F2`, `max → DCEBC0`.

### Le signe, qui double l'échelle

Format `"▲ "#,##0;"▼ "#,##0;"—"` plus une couleur de police conditionnelle
`5F8A17` / `C41822`. Deux encodages pour deux lectures : la flèche donne le
sens, la couleur donne le jugement, l'échelle donne l'ampleur.

> **Une seule règle suffit pour les seize lignes, produits ET charges.** Les
> montants sont **signés** : une variation positive veut toujours dire « cette
> ligne apporte plus à l'EBITDA » — que ce soit un produit qui monte ou une
> charge qui baisse. Vert au positif, rouge au négatif, sans cas particulier.
> C'est le point qu'un relecteur signale souvent à tort.

---

## 5. Les cinq corrections de fond

**1. Drill 2, B5 — quatre plages fausses dans une seule formule.** Elle était
restée sur le tableau à 14 lignes alors qu'il en porte 16 depuis que le CA est
ouvert en trois comptes.

```
lu     TEXT(F34)        -SUM(F35:F47)    SUM(F34:F47)    /F34
juste  SUM(F34:F36)     -SUM(F37:F49)    SUM(F34:F49)    /SUM(F34:F36)
```

Le CA affiché était celui du seul compte 706, les charges amputées de deux
lignes, le taux de marge divisé par le mauvais total.

**2. Cockpit, D38:E57 — « Programme » et « Modalité » sur les vingt lignes.**
L'axe de lignes s'arrête au campus ; ces deux dimensions n'ont pas de membre à
ce niveau et Tagetik y a recopié l'intitulé. Les cellules doivent être vides
tant qu'il n'y a pas de membre.

**3. Les accents des libellés de graphe.** L'axe du pont affichait `Activite` et
`Couts`. Ce n'est **pas** un défaut d'encodage à corriger : un littéral SQL
accentué ne survit pas au canal du loader. La bonne réponse est de **choisir des
mots sans accent** — `Volume` et `Charges`. Même sens, français correct.
`Q_G1_PONT.sql` est mis à jour.

**4. Drill 1, ligne 43 — le TOTAL.** Il portait un tiret sous « CA par élève
2025 » et rien sous les quatre autres colonnes unitaires. Une valeur unitaire ne
se somme pas : les cinq portent le même tiret.

**5. `_xlfn.IFERROR` — à vérifier chez vous.** Votre navigation contient **265
occurrences** de `_xlfn.IFERROR`. Ce préfixe est réservé aux fonctions inconnues
du format ; `IFERROR` est standard depuis 2007. Si des cellules affichent
`#NOM?` à l'ouverture, c'est cela — le fichier de référence les écrit sans
préfixe.

---

## 6. Ce qui reste vrai quel que soit le nœud

| Comportement | Conséquence de mise en page |
|---|---|
| 3 à 50 lignes selon le nœud | règles jusqu'à la ligne 120, aucun fond en dur |
| niveaux absents (pas de groupe sur une marque) | ne jamais ancrer le design sur la ligne EDUSERVICES |
| libellés de 11 à 33 signes | colonne C calée sur le pire cas, 30 |
| ordres de grandeur de 1 à 300 | bascule de format sous le million |
| le graphe 02 change de population | marques sur un nœud, campus sur une marque — axe libre |
| D et E vides aux niveaux 2, 3 et 4 | ne pas les traiter comme toujours remplies |

---

## 7. Contrôles avant démo

```
Cockpit      ligne 38 : CA 23 098 985 · EBITDA 3 845 817 · inscrits 1 229
Drill 1      C21 doit valoir 0,00 €  (les cinq effets moins la variation)
Drill 2      E51/F51 = l'EBITDA du périmètre, somme des seize lignes
Drill 2      ligne 56, Écart = 0 €   (comptes de produit contre socle CRM)
```

Aucune cellule fusionnée dans les grilles de données, aucun nom défini, aucun
lien externe.
