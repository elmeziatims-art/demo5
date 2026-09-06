/* =============================================================================
   Q_D2_SOCLE  —  DRILL-THROUGH sur une cellule d'EBITDA, second drill.
   "DE QUOI CET EBITDA EST-IL FAIT" : le retour a la comptabilite.

   Le premier drill dit POURQUOI l'EBITDA a bouge. Celui-ci dit DE QUOI il est
   fait, poste par poste, jusqu'au numero de compte.

   Quatorze lignes, six colonnes :

     Rang            l'ordre de lecture, du produit vers l'EBITDA
     Famille         Produits, Cout variable, Couts directs, Siege
     Compte          le numero de compte, vide sur les deux lignes calculees
     Poste           le libelle
     Montant 2025    contribution SIGNEE a l'EBITDA
     Montant 2026    idem

   LES MONTANTS SONT SIGNES : les produits en positif, les charges en negatif.
   Leur somme vaut donc exactement l'EBITDA, ce qui rend le controle immediat
   et permet au classeur de tracer une cascade sans retraitement.

   =============================================================================
   TROIS SOURCES, ET C'EST LE POINT INTERESSANT DE CE DRILL

   1. LE CHIFFRE D'AFFAIRES NE VIENT PAS DE LA COMPTA. Il est reconstruit dans
      le socle CRM, effectifs x droits de scolarite plus nouveaux x frais
      d'inscription. Les comptes 706, 7062 et 708 existent en base mais
      V_ALLOCATION ne les utilise pas.

   2. LES DOUZE COMPTES DE CHARGE sont lus tels quels sur le campus, dans
      AW_002_000004_000001. Ce sont de vraies ecritures, drillables plus loin.

   3. LE SIEGE N'EST PAS UN COMPTE DU CAMPUS. Il est porte par l'entite GRP et
      redescendu par la cascade K1..K4 de V_ALLOCATION. La ligne est donc une
      ALLOCATION, pas une ecriture : le libelle le dit.

   Les trois sommees redonnent l'EBITDA au centime. Verifie sur 2026 :
   23 098 985 - 15 684 868 - 3 568 327 = 3 845 790.

   =============================================================================
   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Perimetre herite de la cellule cliquee, exercices en dur comme le cockpit.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    1                                                       AS "Rang",
    'Produits'                                              AS "Famille",
    ''                                                      AS "Compte",
    'Chiffre d''affaires (socle CRM)'                       AS "Poste",
    SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2025 THEN a.CA ELSE 0 END)  AS "Montant 2025",
    SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2026 THEN a.CA ELSE 0 END)  AS "Montant 2026"
FROM    V_ALLOCATION AS a
WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(a.EXERCICE AS INT) IN (2025, 2026)

UNION ALL

SELECT
    r.RANG,
    r.FAMILLE,
    r.COMPTE,
    COALESCE(c.DESC_CONTO0, r.POSTE),
    -1 * SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2025 THEN d.AMOUNT ELSE 0 END),
    -1 * SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2026 THEN d.AMOUNT ELSE 0 END)
FROM (
        VALUES (2, 'Cout variable', '621',   'Personnel exterieur (vacataires)'),
               (3, 'Cout variable', '604',   'Achats d''etudes'),
               (4, 'Cout variable', '6063',  'Fournitures'),
               (5, 'Cout variable', '6231',  'Publicite et acquisition'),
               (6, 'Couts directs', '6411',  'Salaires des permanents'),
               (7, 'Couts directs', '6413',  'Primes'),
               (8, 'Couts directs', '645',   'Charges sociales'),
               (9, 'Couts directs', '613',   'Loyers'),
               (10,'Couts directs', '615',   'Entretien'),
               (11,'Couts directs', '616',   'Assurances'),
               (12,'Couts directs', '625',   'Deplacements'),
               (13,'Couts directs', '63511', 'Taxes')
     ) AS r(RANG, FAMILLE, COMPTE, POSTE)
LEFT JOIN AW_002_000004_000001 AS d
       ON  d.ACCOUNT = r.COMPTE
      AND  d.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
      AND  CAST(d.EXERCICE AS INT) IN (2025, 2026)
LEFT JOIN conto AS c
       ON  c.COD_CONTO = r.COMPTE
GROUP BY r.RANG, r.FAMILLE, r.COMPTE, COALESCE(c.DESC_CONTO0, r.POSTE)

UNION ALL

SELECT
    14                                                      AS "Rang",
    'Siege'                                                 AS "Famille",
    ''                                                      AS "Compte",
    'Siege redescendu (allocation, pas une ecriture)'       AS "Poste",
    -1 * SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2025 THEN a.COST_SIEGE ELSE 0 END),
    -1 * SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2026 THEN a.COST_SIEGE ELSE 0 END)
FROM    V_ALLOCATION AS a
WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(a.EXERCICE AS INT) IN (2025, 2026)
