# 🎨 WIREFRAMES VISUELS - NEOMIND ADVISORY

## 📋 Vue d'ensemble

Ce dossier contient **10 wireframes HTML/CSS interactifs** représentant l'intégralité du site Neomind Advisory, prêts à être communiqués à un développeur Webflow.

---

## 📂 Structure des fichiers

```
/app/wireframes/
├── index.html                    # Page d'accueil des wireframes (navigation)
├── styles.css                    # Styles globaux
├── 01-homepage.html              # Homepage complète
├── 02-offres.html                # Page mère des offres
├── 03-offre-detail.html          # Offre détaillée (Pilotage performance)
├── 04-services.html              # Page services
├── 05-partenaires.html           # Page partenaires
├── 06-approche.html              # Notre approche
├── 07-realisations.html          # Réalisations clients
├── 08-blog.html                  # Blog avec articles
├── 09-rejoignez-nous.html        # Recrutement
├── 10-contact.html               # Formulaire contact
└── README.md                     # Ce fichier
```

---

## 🚀 Comment utiliser ces wireframes

### Option 1: Ouvrir directement dans un navigateur

1. Naviguez vers `/app/wireframes/`
2. Ouvrez `index.html` dans votre navigateur
3. Cliquez sur les cartes pour naviguer entre les pages

### Option 2: Via la ligne de commande

```bash
cd /app/wireframes
python3 -m http.server 8080
# Puis ouvrez http://localhost:8080 dans votre navigateur
```

---

## 📄 Pages incluses

### 01 - HOMEPAGE ✅
- Hero section avec CTAs
- 6 offres en cartes
- Section approche (3 colonnes)
- Chiffres clés
- Témoignages
- Partenaires
- Blog preview
- CTA final

### 02 - OFFRES ✅
- Hero
- Grid 2x3 des 6 offres avec détails
- Navigation vers pages détaillées

### 03 - OFFRE DÉTAILLÉE ✅
- Hero avec breadcrumb
- Introduction texte
- 4 accordéons pour sous-domaines
- Livrables typiques
- Projets liés (3 case studies)
- CTA final

### 04 - SERVICES ✅
- Hero
- 7 accordéons pour les services
- Détails complets (objectif + livrables)
- CTA vers approche

### 05 - PARTENAIRES ✅
- Hero
- 3 partenaires stratégiques (cartes détaillées)
- Écosystème technologique (logos)
- Note importante sur indépendance

### 06 - NOTRE APPROCHE ✅
- Hero
- 5 principes fondateurs (cartes)
- Timeline méthodologie 4 phases
- Focus gouvernance & data quality
- Différenciation (liste à puces)

### 07 - RÉALISATIONS ✅
- Hero
- Filtres (tous, consolidation, budgeting, etc.)
- Grid 3 colonnes de case studies
- Tags + KPIs par projet
- CTA final

### 08 - BLOG ✅
- Hero
- Filtres catégories
- Article hero (featured)
- Grid d'articles (3 colonnes)
- Newsletter signup

### 09 - REJOIGNEZ-NOUS ✅
- Hero
- Qui sommes-nous
- 4 valeurs de culture (grid 2x2)
- 3 profils recherchés
- Pourquoi nous rejoindre
- Timeline processus recrutement (4 étapes)
- CTA postuler

### 10 - CONTACT ✅
- Hero
- Formulaire complet (2 colonnes)
- Coordonnées (adresse, email, téléphone, LinkedIn)
- Placeholder Google Maps

---

## 🎨 Éléments de design

### Palette de couleurs
- **Primaire:** #1a2b4a (Bleu nuit)
- **Secondaire:** #4a90e2 (Bleu ciel)
- **Accent:** #d4af37 (Or)
- **Success:** #10b981 (Vert)
- **Warning:** #f59e0b (Orange)
- **Neutre:** #6b7280 (Gris)

### Typographie
- **Font:** Inter, -apple-system, BlinkMacSystemFont
- **H1:** 3rem
- **H2:** 2.5rem
- **H3:** 1.5-1.8rem
- **Body:** 1rem-1.2rem

### Composants interactifs
- ✅ Accordéons (cliquables)
- ✅ Filtres (actifs au clic)
- ✅ Hover effects sur cartes
- ✅ Navigation sticky
- ✅ Responsive grid

---

## 📝 Notes pour le développeur Webflow

### Collections CMS à créer

1. **Collection "Blog"**
   - Titre, Slug, Catégorie, Auteur, Date
   - Temps lecture, Image header, Extrait
   - Contenu (Rich Text), Tags, Featured

2. **Collection "Réalisations"**
   - Titre, Slug, Secteur, Type projet
   - Solution, Image, Contexte, Résultats
   - Témoignage, KPIs, Tags

3. **Collection "Catégories" (référence)**
   - Nom, Slug, Description

4. **Collection "Tags" (référence)**
   - Nom, Slug, Couleur

### Interactions Webflow

1. **Animations scroll:**
   - Fade-in sections (opacity 0 → 1)
   - Slide-in éléments
   - Counter animation (chiffres clés)

2. **Hover effects:**
   - Cartes: élévation + shadow
   - Logos: grayscale → color
   - Boutons: color + underline

3. **Filtres dynamiques:**
   - Blog: filtrer par catégorie
   - Réalisations: filtrer par type/secteur/solution

4. **Accordéons:**
   - Toggle active class
   - Smooth expand/collapse

5. **Mega-menu:**
   - Menu OFFRES avec sous-sections

### Variables d'environnement
- URLs backend (si applicable)
- Keys API (formulaires)
- Google Maps API key

---

## ✅ Checklist avant livraison au développeur

- [x] 10 pages complètes créées
- [x] Navigation cohérente entre pages
- [x] Header/Footer sur toutes les pages
- [x] Styles CSS centralisés
- [x] Composants réutilisables
- [x] Interactions de base implémentées
- [x] Structure responsive
- [x] Accordéons fonctionnels
- [x] Filtres fonctionnels
- [x] Formulaire contact complet
- [x] Contenu réaliste (pas de lorem ipsum)

---

## 📦 Prochaines étapes

1. **Révision client:** Parcourir toutes les pages et valider la structure
2. **Ajustements:** Noter les modifications souhaitées
3. **Images:** Préparer les vraies images (hero, articles, projets)
4. **Contenu final:** Rédiger les textes définitifs
5. **Développement Webflow:** Transmettre au développeur
6. **Intégrations:** Formulaires, CMS, analytics

---

## 🎯 Contact & Support

Pour toute question sur ces wireframes:
- **Email:** votre-email@example.com
- **Documentation complète:** Voir le document Word fourni

---

**✨ Ces wireframes sont prêts à être utilisés comme référence visuelle pour le développement Webflow !**
