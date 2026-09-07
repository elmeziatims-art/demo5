# Les requêtes du cockpit EDUSERVICES — jeu courant

Version du 07/09/2026. Tout ce qui est listé ici tourne sur `TGK_MSSQL_07`,
scénario `2027BUD_V1`, exercices 2025 et 2026.

## Les trois règles qui n'ont jamais bougé

Le loader Tagetik enveloppe la requête dans `SELECT COUNT(*) FROM ( … ) X`.
D'où, dans **toutes** les requêtes de restitution :

- **pas de CTE** (`WITH`), **pas de `ORDER BY`** au niveau extérieur, **pas de `;`**
  final. Un `ORDER BY` reste permis à l'intérieur d'un `TOP 1` — c'est le cas
  dans `Q_COCKPIT_COMPLET`, et c'est le seul.
- **pas de crochets** dans les alias : Tagetik les refuse. Guillemets doubles,
  `AS "Libellé compte"`.
- le périmètre s'hérite de la cellule cliquée :
  `WHERE ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})`. Les accolades sont
  obligatoires. `.lowest` résout un nœud en ses feuilles et une feuille en
  elle-même : **une seule requête sert les trois niveaux**, groupe, marque et
  campus.

Deux disciplines de fond, qui expliquent la forme de la plupart de ces requêtes :

- **aucune division dans une requête.** Une moyenne, un taux, un indice ne
  survivent pas à une somme. La requête rend le numérateur et le dénominateur,
  le classeur divise après avoir sommé. C'est ce qui rend les pages justes à
  tous les niveaux de la hiérarchie sans que la requête sache où elle tourne.
- **une structure de lignes stable.** Les listes de comptes sont écrites dans
  un bloc `VALUES` joint en `LEFT JOIN` : un compte sans mouvement rend zéro,
  il ne disparaît pas. Le nombre de lignes est donc connu d'avance, et les
  graphes n'ont plus de trous.

---

## Le socle

| Fichier | Ce que c'est |
|---|---|
| `V_ALLOCATION.sql` | la vue qui porte le modèle : CA du socle CRM, coûts variables et directs lus en compta, siège redescendu par la cascade K1..K4. **Tout le reste s'appuie dessus.** |

## Le cockpit

| Fichier | Rend | Paramétré |
|---|---|---|
| `Q_COCKPIT_COMPLET.sql` | une ligne par campus — 14 par exercice — avec marque et les six colonnes N-1 | non — c'est la source du rapport, Tagetik filtre sur son propre axe |
| `Q_COCKPIT_DETAIL.sql` | **exactement la même structure** que `Q_COCKPIT_COMPLET` — mêmes colonnes, mêmes noms, même `OUTER APPLY`, même `PART_EBITDA` — plus `PROGRAMME` et `MODALITE`. 23 colonnes, **30 lignes** par exercice. On s'arrête là : Tagetik descend à l'année d'étude nativement, au double-clic | idem |

`Q_PORTEFEUILLE_CLASSES.sql` est la version **population** de la même chose :
pas de paramètre d'entité, 60 lignes, 20 colonnes, et surtout **les codes de
dimension** (`Marque`, `Campus`) à côté de leurs libellés — sans eux une matrice
s'affiche mais ne se pilote pas. C'est la requête du *Portefeuille — marque &
campus*.

`Q_D4_CLASSES.sql` est le **drill natif** sur une ligne de campus : double-clic
dans Tagetik, et le campus s'ouvre en 4 à 6 lignes — programme × année d'étude ×
modalité, 17 colonnes, les deux exercices côte à côte. Le cockpit garde ses 14
lignes. C'est la voie à préférer à `Q_COCKPIT_DETAIL`, qui descend le grain de
la vue elle-même.

`Q_COCKPIT_DETAIL` **peut remplacer** `Q_COCKPIT_COMPLET` : toutes ses mesures
sont additives, donc sommer les lignes d'un campus redonne exactement la ligne
de campus — vérifié à l'écart nul sur les 14 campus. Ne se somment jamais, ici
comme ailleurs : le CAC, le remplissage, la marge en %. Ce sont des rapports,
ils se calculent après la somme.

## Les trois graphes

Chacune rend **exactement** le tableau que le graphe consomme, pas une colonne
de plus, et porte la marque pour qu'une matrice puisse filtrer dessus.

| Fichier | Graphe | Colonnes |
|---|---|---|
| `Q_G1_PONT.sql` | bridge EBITDA 2025 → 2026 | 5 — Étape, Socle invisible, Ancre, Hausse, Baisse |
| `Q_G2_MARGE.sql` | marge EBITDA par marque | 4 — dynamique : marques sur un nœud, campus sur une marque |
| `Q_G3_TENSION.sql` | acquisition, dépenses contre inscrits, base 100 | 3 |

## Drill 1 — « pourquoi l'EBITDA a bougé »

| Fichier | Rend |
|---|---|
| `Q_D1_SOCLE.sql` | **la version courante.** 15 colonnes, une ligne par campus : effectifs, valeurs unitaires, coûts directs, siège, EBITDA. La requête envoie tout le matériau, `DRILL1_EXCEL.xlsx` calcule les cinq effets. |
| `Q_D1_TABLEAU.sql` | variante où la requête calcule elle-même les 7 lignes d'effets |
| `Q_D1_GRAPHE.sql` | variante idem, mise en forme cascade (5 colonnes) |

Les deux variantes restent valables ; elles calculent en base ce que le
classeur calcule aujourd'hui. À garder si vous préférez un drill sans formule.

## Drill 2 — « de quoi cet EBITDA est fait »

| Fichier | Rend |
|---|---|
| `Q_D2_CA_CRM.sql` | la restitution CRM du rapprochement : 3 lignes, 4 colonnes, jumelle exacte de `Q_D2_CA_COMPTA` |
| `Q_D2_SOCLE.sql` | **16 lignes, 6 colonnes.** Le compte d'exploitation poste par poste : 3 comptes de produit (706, 7062, 708), 12 comptes de charge, plus le siège. Montants signés — leur somme vaut l'EBITDA. |
| `Q_D2_CA_COMPTA.sql` | contrôle autonome : le CA vu par les comptes de produit, une ligne |

`DRILL2_EXCEL.xlsx` va chercher chaque ligne par son `Compte` avec une
`RECHERCHEV`. **L'ordre n'est pas l'affaire de la requête** — le classeur le
fixe lui-même, ce qui tombe bien puisque `ORDER BY` est interdit.

## Drill 3 — « d'où vient ce chiffre d'affaires »

Deux requêtes qui répondent à la même question par deux chemins. Un chiffre qui
arrive deux fois par deux chemins différents est un chiffre vérifié.

| Fichier | Chaîne | Rend |
|---|---|---|
| `Q_D3_CA_CRM.sql` | le **pilotage** — effectifs × droits de scolarité | 3 lignes, 8 colonnes : volumes et montants, jamais de prix moyen |
| `Q_D3_CA_COMPTA.sql` | le **constat** — comptes 706, 7062, 708 | 3 lignes, 4 colonnes |

`DRILL3_EXCEL.xlsx` les met face à face, puis décompose la variation en effet
volume et effet prix. Sans terme croisé : volume valorisé au prix de N-1, prix
appliqué au volume de N.

## Le moteur

| Fichier | Rend |
|---|---|
| `V_MOTEUR_CAL.sql` | **la vue** : une ligne par campus, 17 colonnes. Elle restitue, le masque calcule — rien de ce qui dépend du Δ de budget n'y est. Voir `SPEC_MOTEUR_MASQUE.md` pour les douze formules du masque. |
| `Q_MOTEUR_CALIBRATION.sql` | la version requête, une ligne par campus, 13 colonnes : les séries leads/budget sur 3 exercices, **l'élasticité calculée en SQL**, la conversion et le CA par inscrit. Alimente l'onglet *Le moteur (modèle)*. |

L'élasticité est une **régression des moindres carrés**, donc une agrégation :
elle s'écrit avec des `SUM`, sans CTE. Vérifiée identique à `SLOPE` d'Excel au
dix-millième sur les 14 campus. Le Δ de budget reste une **saisie** : les cinq
colonnes du geste restent dans le classeur.

## Maintenance

| Fichier | Ce que ça fait |
|---|---|
| `FIX_CA_COMPTA_2024_2025.sql` | **à lancer dans SSMS, pas dans le loader.** Réaligne les comptes de produit sur le socle CRM en recalculant depuis le CRM — aucun montant en dur, donc relançable. Passé le 06/09 : les trois exercices tombent au centime. |

---

## La correspondance des comptes

Vérifiée sur les 70 lignes de 2026, sans une seule exception.

| Compte | Ce que c'est | Inducteur CRM |
|---|---|---|
| `706` | scolarité des étudiants en **initial** | `VOL_EFF × REV_STUD` |
| `7062` | scolarité des **alternants** | `VOL_EFF × REV_STUD` |
| `708` | **frais d'inscription** | `VOL_NEW × REV_FRAIS_INS` |

Les frais d'inscription se paient une fois, à l'entrée : leur volume est
`VOL_NEW`, pas l'effectif total. C'est pourquoi les trois volumes ne
s'additionnent jamais entre eux.

**Coûts variables** : 621, 604, 6063, 6231.
**Coûts directs** : 6411, 6413, 645, 613, 615, 616, 625, 63511.
**Siège** (porté par GRP, redescendu) : 6236, 6414, 6226, 626, 6281, 6331, 6333.
