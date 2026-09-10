/* =============================================================================
   Q_D2_CA_CRM  —  la restitution CRM du second drill.
   Le chiffre d'affaires vu par les INDUCTEURS : effectifs x droits de
   scolarite. Trois lignes, quatre colonnes.

     Compte         LA CLE, la meme que dans le tableau du drill 2
     Poste          le libelle
     Montant 2025
     Montant 2026

   Elle est la jumelle exacte de Q_D2_CA_COMPTA : meme forme, meme clef, meme
   nombre de lignes. C'est voulu -- le rapprochement du bas de page les met
   cote a cote, et l'ecart doit rester a zero.

   =============================================================================
   POURQUOI CETTE REQUETE EXISTE

   Le tableau du drill 2 lit les COMPTES DE PRODUIT : 706, 7062, 708. C'est le
   CONSTAT. Cette requete-ci prend l'autre chemin, celui du PILOTAGE : elle
   part des volumes et des tarifs du socle CRM et reconstruit le meme montant.

   Un chiffre qui arrive deux fois par deux chemins differents est un chiffre
   verifie. Depuis le realignement du 06/09 les deux tombent au centime sur les
   trois exercices ; si l'ecart reapparait, c'est que le socle CRM a bouge sans
   que les comptes de produit suivent, et FIX_CA_COMPTA_2024_2025.sql les remet
   d'accord.

   =============================================================================
   LA CORRESPONDANCE

       706    scolarite des etudiants en INITIAL   VOL_EFF x REV_STUD
       7062   scolarite des ALTERNANTS             VOL_EFF x REV_STUD
       708    frais d'inscription                  VOL_NEW x REV_FRAIS_INS

   Les frais d'inscription se paient une fois, a l'entree : leur volume est
   VOL_NEW, les nouveaux inscrits, pas l'effectif total.

   TROIS LIGNES, TOUJOURS. Chaque branche est une agregation SANS GROUP BY :
   elle rend exactement une ligne, meme si le perimetre ne contient aucun
   etudiant en initial -- le cas des campus Ipac, Pigier et Tunon, ou le 706
   sort a zero au lieu de disparaitre. Les COALESCE sont la pour cela : une
   somme sur zero ligne vaut NULL, pas 0.

   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Perimetre herite de la cellule cliquee, exercices en dur comme le cockpit.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    '706'                                       AS "Compte",
    'Scolarite des etudiants en initial'        AS "Poste",
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0) AS "Montant 2025",
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0) AS "Montant 2026"
FROM    AW_002_000002_000001 AS s
WHERE   s.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(s.EXERCICE AS INT) IN (2025, 2026)
  AND   s.MODALITE = 'INIT'

UNION ALL

SELECT
    '7062',
    'Scolarite des alternants',
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0)
FROM    AW_002_000002_000001 AS s
WHERE   s.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(s.EXERCICE AS INT) IN (2025, 2026)
  AND   s.MODALITE = 'ALT'

UNION ALL

SELECT
    '708',
    'Frais d''inscription',
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_NEW * s.REV_FRAIS_INS ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_NEW * s.REV_FRAIS_INS ELSE 0 END), 0)
FROM    AW_002_000002_000001 AS s
WHERE   s.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(s.EXERCICE AS INT) IN (2025, 2026)
