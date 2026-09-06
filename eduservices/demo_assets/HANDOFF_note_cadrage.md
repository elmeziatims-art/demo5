# Passation — Retravailler la NOTE DE CADRAGE (EDUSERVICES / EPM Tagetik)

> Brief pour une nouvelle session Claude. Objectif : **perfectionner la note de cadrage** (pre-read CFO). Ne pas repartir de zéro : le contenu existe (`eduservices/demo_assets/note_cadrage.html`).

## 1. Contexte commercial (à qui / pourquoi)
- L'utilisateur est **intégrateur/éditeur d'un EPM = CCH Tagetik** ; il **prospecte EDUSERVICES** (groupe français d'enseignement supérieur privé : ~42 000 étudiants dont ~32 000 en alternance, 21+ marques, 45+ campus, LBO Parquest, exercice clos au 31/08).
- **Un 1er call de prospection a eu lieu.** L'utilisateur a présenté son offre et cité comme **références sectorielles OMNES Education et Galileo Global Education** (utilisent l'EPM). Le CFO a répondu en substance : *« montrez-moi un case study, et si je peux avoir un peu de lecture avant, je suis preneur. »*
- **Livrables en cours** : (a) un **mail de follow-up** au CFO, (b) cette **note de cadrage** en pièce jointe (le « peu de lecture »).

## 2. Ce qui existe déjà (NE PAS refaire — c'est le décor)
- Une **maquette Excel de bout en bout** du pilotage budgétaire (repo, branche `claude/hello-xvtu00`, dossier `eduservices/`, générée par `gen_v2.py`). Contient : cadrage top-down (poste de commande CFO), moteur budget par inducteurs (cohortes, funnel→volume, prix), simulateur de décisions (ouvrir/fermer/mutualiser), allocation par drivers + cascade, référentiel Tagetik (codes/hiérarchies) + table de faits format long, reporting.
- **Calibrage** (à connaître, à ne pas contredire) : marge EBITDA **14,6 %**, personnel **~46 %** du CA, D&A **6 %**, CA/étudiant **~8 200 €**.
- **Périmètre de démo** : échantillon représentatif = **5 marques** (MBway, ISCOM, Ipac Bachelor Factory, Pigier, Tunon), **14 campus**, **~2 415 étudiants**, **~20 M€ de CA**, calé sur les ratios du **consolidé (345,8 M€)**.
- Des **packs de reporting** (HTML) existent — **mais le CFO NE veut PAS de visuels de reporting dans la note.**

## 3. La note de cadrage — état actuel
- Fichier source : **`eduservices/demo_assets/note_cadrage.html`** (mise en page A4, convertible en PDF).
- Structure actuelle : en-tête + objet ; §1 Périmètre ; §2 Parti pris (top-down éclaté à la maille fine via un scénario historique de base + allocations dynamiques) + **schéma conceptuel** Groupe→Marque→Campus→Programme→Classe ; §3 Fil de la démo en 5 étapes ; §4 Ce que ça démontre ; §5 Invitation à l'input. Pied de page + placeholders.

## 4. CONTRAINTES & PRÉFÉRENCES (impératif)
- **Langue** : français. **Audience** : CFO. **Ton** : professionnel, prospection, **concis** (lecture 2–3 min).
- **AUCUN visuel de reporting** (pas de graphiques de perf, pas de chiffres de résultat mis en scène). Un **schéma conceptuel de méthode** est autorisé.
- **Message central à défendre** : un **top-down pilotable**, **éclatable jusqu'à la maille la plus fine** (marque→campus→programme→classe) grâce à un **scénario historique de base** (clé de répartition), avec **allocations dynamiques** par inducteurs (CA, effectifs, nb de classes), recalcul automatique, et **réconciliation top-down ↔ bottom-up**.
- **Vocabulaire** : dire **« chargement multisource »** (compta, CRM/admissions, RH) — **PAS** « historique » pour l'étape de chargement.
- **Périmètre** : formuler « **restreint et représentatif, calibré sur les ratios de vos comptes consolidés** » (le chiffre ~20 M€ est optionnel — l'utilisateur peut vouloir le retirer).
- **Références** OMNES / Galileo : à garder (rappeler de vérifier le droit de citer nommément ; sinon « des groupes comparables du sup privé »).
- **Placeholders `[crochets]`** partout (nom du CFO, société, date, coordonnées) — l'utilisateur personnalisera.
- **Honnêteté** : montants **illustratifs** calibrés sur ordres de grandeur ; ne rien affirmer de faux sur EDUSERVICES.

## 5. MISSION de la nouvelle session
**Perfectionner la note** : resserrer et muscler le propos (idéalement **1 page**), rendre la proposition de valeur EPM plus percutante autour du triptyque **top-down → maille fine (via scénario de base) → allocations dynamiques**, soigner l'accroche et l'appel à l'action. **Commencer par demander à l'utilisateur** : longueur cible (1 page ?), faut-il un exemple concret (sans reporting), branding/charte, et le niveau de formalité.

## 6. Régénérer le PDF (HTML → PDF)
```python
from playwright.sync_api import sync_playwright
import glob, pathlib
exe=glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome')[0]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=exe)
    pg=b.new_page(); pg.goto('file://'+str(pathlib.Path('note_cadrage.html').resolve()), wait_until='networkidle')
    pg.pdf(path='Note_de_cadrage_EDUSERVICES.pdf', format='A4', print_background=True); b.close()
```
(`pip install playwright` si besoin ; les navigateurs sont déjà dans `/opt/pw-browsers`.)

## 7. Prompt de démarrage suggéré (à coller dans la nouvelle session)
> « Lis `eduservices/demo_assets/HANDOFF_note_cadrage.md` et `eduservices/demo_assets/note_cadrage.html`. On prépare une note de cadrage (pre-read CFO) pour une prospection EPM/Tagetik chez EDUSERVICES. Retravaille-la selon les contraintes du handoff (français, CFO, concis, AUCUN visuel de reporting, message = top-down éclaté à la maille fine via scénario historique de base + allocations dynamiques, "chargement multisource"). Commence par me poser les 2-3 questions de cadrage, puis propose une version améliorée + régénère le PDF. »
