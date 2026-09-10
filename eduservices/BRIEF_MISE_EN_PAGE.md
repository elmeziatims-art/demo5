# Brief — cockpit EDUSERVICES, feuille « 2 »

Document destiné à un designer / dataviz à qui l'on demande de **challenger et
améliorer cette mise en page**. Il décrit ce qui existe, pourquoi, et surtout ce
qui **bouge à l'exécution** — c'est le point le plus souvent raté quand on
redessine un rapport EPM à partir d'une capture d'écran.

---

## 1. Ce que ce fichier est réellement

Ce n'est pas un tableau de bord Excel. C'est un **rapport Tagetik** (release
5.3.35.526, base SQL Server `TGK_MSSQL_07`). Le classeur est un **gabarit** :
au lancement, Tagetik écrase des zones entières avec le résultat de requêtes
SQL, puis rend la feuille à l'utilisateur.

Conséquence directe pour le design : **on ne dessine pas un état, on dessine un
gabarit qui doit rester juste pour tous les états possibles.**

Groupe : 5 marques, 14 campus, 8 programmes, 2 modalités (initial / alternance).

---

## 2. La géométrie actuelle

Feuille `2`. Quadrillage masqué. Colonne A = gouttière (largeur 2,5).

| Zone | Lignes | Contenu |
|---|---|---|
| Bandeau titre | 1–3 | fond navy `172033`, titre + sous-titre |
| Filtres | 5 | Scénario / Version / Entité, fond bleu très clair |
| Six cartes KPI | 8–10 | libellé, grande valeur, variation |
| Trois graphes | 12–35 | pont d'EBITDA, marge par marque, tension acquisition |
| Titre du tableau | 36 | |
| En-têtes | 37 | fond `526071`, texte blanc |
| Données | 38 → 87 | 50 lignes servies aujourd'hui, **variable** (voir §5) |
| Notes de source | 89–90 | italique, gris |

### Colonnes visibles (B → Q)

| Col | Contenu | Largeur | Format |
|---|---|---|---|
| **B** | **Niveau hiérarchique (2/3/4/5) — MASQUÉE** | 4,5 | entier |
| C | Entité (groupe / marque / campus) | 33 | texte |
| D | Programme | 13 | texte |
| E | Modalité | 11 | texte |
| F | CA | 11 | `#,##0` |
| G | Δ CA | 11 | `"▲ "0.0%;"▼ "0.0%;""` |
| H | EBITDA | 11 | `#,##0` |
| I | Δ EBITDA | 11 | idem G |
| J | Part EBITDA | 11 | `0.0%` + barre de données |
| K | Marge EBITDA | 11 | `0.0%` + échelle de couleur |
| L | Δ Marge (pt) | 11 | `"▲ "0.00;"▼ "0.00;""` |
| M | Inscrits | 11 | `#,##0` |
| N | Remplissage | 11 | `0.0%` + échelle de couleur |
| O | Mix alternance | 11 | `0.0%` |
| P | Effectifs | 11 | `#,##0` |
| Q | Places | 11 | `#,##0` |

---

## 3. Les colonnes techniques, et pourquoi elles sont masquées

**Rien de ce qui suit ne doit jamais apparaître à l'écran.** Ce sont des
matériaux de calcul, pas de l'information.

### 3.1 La colonne de niveau (B) — le cas à comprendre

Elle porte un entier : `2` groupe, `3` marque, `4` campus, `5` programme ×
modalité. **Elle ne sert qu'à piloter la mise en forme conditionnelle** : les
quatre règles de hiérarchie testent `$B38=2`, `=3`, `=4`, `=5`.

Elle est **masquée**. Une règle conditionnelle évalue `$B` sans difficulté sur
une colonne masquée — la visibilité ne change rien à l'évaluation. C'est le bon
réflexe : masquer plutôt que peindre en couleur de fond, parce qu'une colonne
peinte occupe quand même de la largeur et se réveille dès qu'on change le fond.

### 3.2 Le bloc N-1 et les dénominateurs (R → AA)

`EFFECTIFS_ALT`, `EBITDA_N1`, `CA_N1`, `SPEND_ACQ`, `SPEND_ACQ_N1`,
`MARGE_EBITDA_N1`, `PLACES_N1`, `INSCRITS_N1`, `EFFECTIFS_N1`,
`PCT_NOUVEAUX_INSCRITS`.

Ils existent parce que **le rapport ne divise jamais avant d'avoir sommé**. Une
marge, un taux de remplissage, un coût d'acquisition sont des **rapports** : la
marge de trois campus n'est pas la moyenne de leurs marges. La requête rend donc
le numérateur *et* le dénominateur, et la division se fait dans la cellule,
après le `SUBTOTAL`. C'est ce qui rend le tableau juste à ses quatre niveaux de
repli sans que la requête sache où elle est dépliée.

### 3.3 Les zones de restitution des graphes (AB → AO)

Trois blocs contigus où Tagetik dépose le résultat de trois requêtes :

- `AB:AF` — pont d'EBITDA : `ETAPE, SOCLE, ANCRE, HAUSSE, BAISSE`
- `AH:AK` — marge par marque : `LIBELLE, MARGE_2024, MARGE_2025, MARGE_2026`
- `AM:AO` — tension : `EXERCICE, IND_DEPENSES, IND_INSCRITS`

Les graphes lisent **directement** ces plages, en références internes
(`'2'!$AB$7:$AB$11`), **sans aucun nom défini**. C'est délibéré : une série qui
référence un nom défini porte le nom du classeur (`'Classeur.xlsx'!zone`), et
Excel **supprime la série** dès que le fichier est renommé ou copié. Ce piège
a vidé les trois graphes trois fois avant qu'on le trouve.

---

## 4. La mise en forme conditionnelle — l'inventaire et le raisonnement

**L'ordre des règles compte.** Excel retient la première règle qui pose une
propriété donnée. Les règles sont donc posées dans cet ordre précis.

### 4.1 Les deux échelles de couleur — bornes ABSOLUES, pas des percentiles

| Colonne | Bas | Milieu | Haut |
|---|---|---|---|
| K — Marge EBITDA | 2 % `F7CFCF` | 12 % `FDF0CE` | 22 % `CDE9DF` |
| N — Remplissage | 55 % `F7CFCF` | 75 % `FDF0CE` | 95 % `CDE9DF` |

**Pourquoi des bornes fixes et non des percentiles :** un campus doit garder sa
couleur quand on change de périmètre. Avec des percentiles, descendre sur une
marque repeint tout et la lecture n'est plus comparable d'un lancement à
l'autre — le pire campus d'un bon réseau paraîtrait rouge. Les bornes couvrent
l'amplitude réelle observée (Tunon 4,2 % contre Pigier 21,1 %).

### 4.2 La barre de données — J, Part EBITDA, bornée 0 → 100 %

Barre et échelle de couleur ne disent pas la même chose : **la barre montre une
magnitude, l'échelle une performance relative**. Part d'EBITDA est une
magnitude ; marge et remplissage sont des performances. Chacune a l'encodage qui
lui revient, et on ne mélange pas les deux sur une même colonne.

Bornée à 100 % et non à 30 % : la colonne mélange quatre niveaux — le groupe y
vaut 100 %, une marque jusqu'à 45 %, un campus 1 à 16 %, une classe moins de
5 %. À 30 %, tout ce qui dépasse une marque saturait et la barre ne disait plus
rien.

### 4.3 Les variations — couleur de police seule (G, I, L)

Vert `1E9E89` si > 0, rouge `D64545` si < 0. **Couleur de police uniquement**,
donc ces règles se composent par-dessus les fonds de niveau et par-dessus la
heatmap sans les écraser.

### 4.4 Les quatre niveaux de hiérarchie — pilotés par `$B`

| Niveau | Test | Graisse | Fond | Bordure |
|---|---|---|---|---|
| 2 groupe | `$B38=2` | gras | `D9E2EF` | filet épais au-dessus |
| 3 marque | `$B38=3` | gras | `EAF2FC` | filet fin en dessous |
| 4 campus | `$B38=4` | gras | `FFFFFF` | filet fin |
| 5 classe | `$B38=5` | normal, encre `69778B` | `FBFCFE` | filet fin |

Plage `B38:Q120`. **Le retrait par niveau a été retiré volontairement** — il est
géré côté Tagetik. La hiérarchie se lit donc par la graisse, le fond et le
filet, sans indentation.

**Point technique** : une règle conditionnelle Excel ne sait pas poser une
indentation. Le seul levier est le format de nombre (`'"      "@'`), ce qui
fonctionne mais reste un bricolage — d'où l'abandon.

### 4.5 Le bandeau KPI

- **Les flèches sont dans le FORMAT DE NOMBRE, pas dans le texte** :
  `"▲ "0.0%;"▼ "0.0%;"—"`. La section positive porte le triangle haut, la
  négative le bas, la troisième un tiret. La flèche dit donc le **sens**.
- **La couleur conditionnelle dit si c'est une bonne nouvelle**, et c'est
  indépendant : sur le coût d'acquisition, une flèche vers le haut est **rouge**.
  Les deux encodages ne se confondent pas, et c'est voulu.
- **Le format bascule sous le million** : une règle conditionnelle sur `F9` et
  `H9` passe de `0.0,," M€"` à `#,##0" €"` en dessous de 1 000 000. Sans elle,
  un EBITDA de 81 725 € s'affiche « 0,1 M€ » — toute la précision perdue, ce qui
  arrive dès qu'on descend sur Ipac, Pigier ou Tunon.

### 4.6 Le fond et les bordures ne sont JAMAIS posés en dur

Police, alignement et formats de nombre sont posés en dur jusqu'à la ligne 120.
**Le fond et les bordures viennent uniquement des règles de niveau.**

Raison : une navigation sur Tunon ne sert que 7 lignes. Si le fond et les
bordures étaient en dur, on verrait 80 lignes blanches bordées en dessous — qui
se lisent comme un tableau vide, pas comme la fin du tableau. Une ligne non
servie doit **se confondre avec le fond de page**.

---

## 5. CE QUI EST DYNAMIQUE — à lire avant de redessiner quoi que ce soit

C'est la section décisive. Une maquette qui suppose l'état actuel casse au
premier lancement.

1. **Le nombre de lignes varie du simple au décuple.** Lancé sur le groupe : 50
   lignes. Sur la marque Tunon : 7. Sur un seul campus : 3 ou 4. Les règles
   conditionnelles couvrent jusqu'à la ligne **120** pour absorber tout nœud
   sans retouche.

2. **Les niveaux présents varient.** Lancé sur une marque, il n'y a pas de ligne
   de niveau 2. Lancé sur un campus, ni 2 ni 3. Une maquette qui met en scène la
   ligne « EDUSERVICES » comme point d'ancrage visuel perd son ancre.

3. **Les libellés varient en longueur.** « Ipac Bachelor Factory Montpellier »
   fait 33 signes, « ISCOM Lille » en fait 11. La colonne C est calée sur le
   pire cas.

4. **Les ordres de grandeur varient de 1 à 300.** CA groupe 23 M€, CA d'une
   classe 80 k€. D'où la bascule de format sous le million.

5. **Les graphes se recomposent.** Le graphe de marge affiche **les marques**
   quand on est sur un nœud, et **les campus** quand on est descendu sur une
   marque. Son axe est **libre** : il était figé entre 3 et 5 M€, ce qui
   convenait au groupe mais laissait le graphe complètement vide sur les cinq
   marques (ISCOM culmine à 1,3 M€, Tunon à 0,2 M€). Un cadrage qui ne marche
   que sur un nœud sur six n'est pas un cadrage.

6. **Les colonnes D et E sont vides sur les lignes 2, 3 et 4.** Programme et
   modalité n'existent qu'au niveau 5. Un design qui les traite comme des
   colonnes toujours remplies produira des trous.

---

## 6. Contraintes non négociables

### Tagetik

- **Aucune cellule fusionnée**, nulle part. Tagetik réécrit des plages entières
  et une fusion fait exploser l'insertion de lignes.
- **Aucun nom défini** pointant vers l'extérieur, aucun lien externe.
- Les zones de restitution doivent rester **contiguës et à hauteur fixe** ; on
  ne peut pas insérer de colonne de relais au milieu.
- Le fichier est un `.xlsm` avec VBA hérité : il doit rester macro-enabled.

### Dataviz — les règles qu'on s'est imposées

- **Un encodage = une information.** Magnitude → barre. Performance → échelle de
  couleur. Sens → flèche. Jugement → couleur de police. On ne double jamais.
- **Jamais de moyenne de ratios.** Tout rapport est calculé après somme.
- **Bornes absolues** sur toute échelle de couleur, pour que la lecture reste
  comparable d'un périmètre à l'autre.
- **Les couleurs sémantiques** (`1E9E89` bon, `D64545` critique, `B97800`
  alerte) sont réservées au jugement et ne servent jamais de couleur de série.

---

## 7. Palette et typographie actuelles

```
NAVY    172033    bandeau                 CANVAS  F3F6FA   fond de page
SLATE   526071    en-têtes de tableau     PANEL   FFFFFF   ligne servie
INK     202733    texte principal         SOFT    EAF2FC   fond marque
MUTED   69778B    texte secondaire        PARENT  D9E2EF   fond groupe
ONDARK  B8C6DA    texte sur navy          SEP     E9EDF3   filets

BLUE    2A78D6 / BLUE2 6FA5DC / BLUE3 B8CFEC     séries de graphe
ORANGE  F07B32    seconde série de la courbe de tension
GOOD    1E9E89    WARN B97800    CRIT D64545     sémantique

heatmap : bas F7CFCF · milieu FDF0CE · haut CDE9DF

Titres et grandes valeurs : Fira Sans Medium
Corps de tableau : Arial 8,5
```

**Le fond de page n'est pas blanc** (`F3F6FA`), et c'est assumé : il fait
ressortir les lignes servies, qui sont blanches, et fait disparaître les lignes
non servies. On souhaite garder ce parti pris.

---

## 8. Ce qui est ouvert au challenge

**Ouvert, et on attend des propositions :**

- la composition générale : où placer les cartes, les graphes, le tableau ;
- la hiérarchie typographique et les tailles ;
- le choix des trois graphes et leur forme ;
- l'encodage de la hiérarchie sans retrait — quatre fonds et deux graisses,
  est-ce le meilleur système ?
- la densité : 16 colonnes visibles, est-ce trop ? lesquelles sacrifier ?
- la palette, tant qu'elle reste lisible en projection et à l'impression.

**Fermé, pour les raisons données plus haut :**

- pas de cellules fusionnées ;
- pas de nom défini pour les séries de graphe ;
- pas de fond ni de bordure en dur sur les lignes de données ;
- pas de percentile dans une échelle de couleur ;
- pas de ratio calculé avant la somme ;
- la colonne de niveau reste masquée mais reste présente.

---

## 9. La question posée

> Améliore cette mise en page pour qu'elle tienne devant un comité de direction,
> en respectant les six contraintes fermées et les six comportements dynamiques
> du §5. Dis explicitement, pour chaque proposition, ce qu'elle devient quand le
> rapport est lancé sur une marque (7 lignes, pas de niveau 2) plutôt que sur le
> groupe (50 lignes).
