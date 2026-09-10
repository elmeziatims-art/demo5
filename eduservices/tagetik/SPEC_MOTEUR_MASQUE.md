# Le bloc ① du moteur — ce que la vue rend, ce que le masque calcule

`V_MOTEUR_CAL` rend **une ligne par campus, 17 colonnes**. Le masque calcule
tout le reste. La coupure est nette : **rien de ce qui dépend du Δ de budget
n'est dans la vue**, sinon bouger 8 % en 12 % obligerait à relancer.

## Ce que la vue rend

| Colonne | Additive ? |
|---|---|
| `ENTITY` · `MARQUE` · `CAMPUS` | dimensions |
| `LEAD_PAY_2024/2025/2026` | oui |
| `SPEND_ACQ_2024/2025/2026` | oui |
| **`ELASTICITE`** | **non — voir plus bas** |
| `LEAD_TOT_N` · `INSCRITS_N` · `CA_NEW_N` | oui |
| `EFFECTIFS_N` · `PLACES_N` · `CLASSES_N` | oui |
| `COUT_CONSO_N` (604 + 6063) · `COUT_VACAT_N` (621) | oui |
| `ECART_LEADS` | contrôle, doit valoir 0 |

**Aucun taux n'est pré-calculé.** Chacun est exposé en numérateur et
dénominateur, pour qu'une ligne de marque ou de groupe reste juste après la
somme. C'était le défaut du classeur : la conversion des nœuds y était écrite
en dur, et sur le groupe la moyenne des taux se trompait de **0,25 point**.

## Ce que le masque calcule — les six dérivées

```
Conversion          = INSCRITS_N / LEAD_TOT_N
CA par inscrit      = CA_NEW_N / INSCRITS_N
Conso par élève     = COUT_CONSO_N / EFFECTIFS_N
Vacataire / classe  = COUT_VACAT_N / CLASSES_N
Capacité moyenne    = PLACES_N / CLASSES_N
Places libres       = PLACES_N − EFFECTIFS_N
```

Toutes se recalculent après la somme sur une ligne de nœud. Aucune ne se somme.

## Ce que le masque calcule — le geste

`Δ` est **la saisie**. Six formules, dans cet ordre :

```
Δ budget            = SPEND_ACQ_2026 × Δ
Inscrits gagnés     = LEAD_PAY_2026 × ((1 + Δ) ^ ELASTICITE − 1) × Conversion
CA gagné            = Inscrits gagnés × CA par inscrit

Coût variable/élève = SI( Inscrits gagnés <= Places libres ;
                          Conso par élève ;
                          Conso par élève + Vacataire-classe / Capacité moyenne )

EBITDA gagné        = CA gagné − Δ budget − Inscrits gagnés × Coût variable
CAC marginal        = Δ budget / Inscrits gagnés
```

La quatrième ligne est celle qui change tout : **le coût bascule tout seul**.

```
tant qu'il reste des places      363 €/élève    les consommables seuls
s'il faut ouvrir une classe      750 €/élève    + la quote-part du vacataire
```

Groupe 2026 : **135 classes, 4 088 places, 3 114 élèves, 974 places libres**,
remplissage 76,2 %. À +8 %, le geste gagne 27 inscrits — ils tiennent tous dans
les sièges libres, donc 363 €.

Le compte **6231 n'est jamais dans ce coût** : c'est le budget d'acquisition,
déjà soustrait comme Δ budget. L'y remettre le compterait deux fois.

## Sur une ligne de nœud

| Colonne | Comportement |
|---|---|
| Leads, budget, Δ budget, inscrits gagnés, CA gagné, EBITDA gagné | **somme** |
| Conversion, CA/inscrit, conso/élève, CAC marginal, remplissage | **recalcul après somme** |
| **Élasticité** | **tiret** |

L'élasticité vit au campus. Sur le groupe, les trois façons de l'agréger
donnent trois nombres différents :

```
régression sur les séries agrégées   0,4937
moyenne simple des quatorze          0,5031
moyenne pondérée par le budget       0,4881
```

Afficher un tiret est plus honnête que choisir en silence. Si vous voulez
vraiment une élasticité de groupe, c'est la première — refaire la régression
sur les séries sommées — et c'est une autre requête.

## Pourquoi on ne s'arrête pas au CA

Un DAF n'arbitre pas sur du chiffre d'affaires. **« +205 651 € de CA »** sans le
coût en face est exactement le genre de nombre qui fait rejeter un modèle en
comité. Maintenant que le coût se **calcule** au lieu de se supposer, la chaîne
va jusqu'à l'EBITDA — la seule grandeur sur laquelle on décide.
