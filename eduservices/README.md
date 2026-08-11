# EDUSERVICES GROUP — Modèle Budget & Simulation (pré-Tagetik)

Modèle Excel de **budget annuel N+1** piloté par les inducteurs, à préparer sous Excel
avant l'implémentation dans **CCH Tagetik**.

## Fichier livrable

**`EDUSERVICES_Budget_Simulation.xlsx`** — classeur autoportant (9 feuilles) :

| Feuille | Rôle |
|---|---|
| `00_Notice` | Guide d'utilisation + légende des couleurs |
| `01_Note_cadrage` | Note de cadrage : objectifs, hypothèses, règles de gestion |
| `02_Parametres` | **Leviers de simulation** + sélecteur de scénario (cellule jaune `C3`) |
| `03_Referentiel` | Dimensions : Groupe → Marque → Campus, plan de comptes |
| `04_Historique` | Réalisé N-1 par campus (données à remplacer par le réel) |
| `05_Moteur` | Moteur de budget par campus (100 % formules) |
| `06_PnL` | Compte de résultat consolidé N-1 vs Budget + synthèse par marque |
| `07_Simulation` | Tableau de bord : KPIs et comparatif de scénarios |
| `08_Mapping_Tagetik` | Correspondance modèle Excel ↔ objets Tagetik |

## Utilisation

1. Renseigner le réalisé dans `04_Historique`.
2. Fixer les hypothèses par scénario dans `02_Parametres`.
3. Choisir le scénario actif en `02_Parametres!C3` (Cadrage / Optimiste / Prudent) :
   **tout le modèle se recalcule**.
4. Lire le budget consolidé (`06_PnL`) et le tableau de bord (`07_Simulation`).

## Convention de couleurs

- 🔵 Bleu = saisie / donnée en dur  ·  ⚫ Noir = formule  ·  🟢 Vert = lien inter-feuilles  ·  🟡 Jaune = hypothèse clé / cellule à remplir.

## Régénérer le fichier

`python generer_modele.py` (nécessite `openpyxl`).

> ⚠️ Les montants pré-remplis sont **illustratifs** (marques, campus, effectifs, euros) pour
> faire tourner la démo ; ils doivent être remplacés par les données réelles d'EDUSERVICES GROUP.
