/* =============================================================================
   Q_D2_SOCLE  —  DRILL-THROUGH sur une cellule d'EBITDA, second drill.
   "DE QUOI CET EBITDA EST-IL FAIT" : le retour a la comptabilite de gestion.

   QUATORZE LIGNES, SIX COLONNES.

     Compte        LA CLE. Un vrai numero pour les douze comptes, et deux codes
                   techniques, CA et SIEGE, pour les deux lignes calculees.
     Famille       Produits, Cout variable, Couts directs, Siege
     Poste         le libelle complet, pour le tableau
     Poste court   le libelle abrege, pour l'axe du graphe
     Montant 2025  contribution SIGNEE a l'EBITDA
     Montant 2026  idem

   PLUS DE COLONNE DE RANG. Elle ne portait que l'ordre d'affichage, et l'ordre
   n'est plus l'affaire de la requete : le classeur va chercher chaque ligne
   par son Compte, avec une RECHERCHEV. Il fixe donc lui-meme la sequence, et
   la requete peut rendre ses lignes dans n'importe quel ordre -- ce qui tombe
   bien, puisque le loader Tagetik interdit ORDER BY.

   C'est aussi pour cela que les deux lignes calculees portent desormais un
   code : sans lui, elles seraient introuvables par la recherche.

   LES MONTANTS SONT SIGNES : produit en positif, charges en negatif. Leur
   somme vaut exactement l'EBITDA.

   =============================================================================
   UNE STRUCTURE COMPTABLE STABLE, ET C'EST VOULU

   Le nombre de lignes ne depend pas de ce que la donnee contient. La liste des
   douze comptes est ecrite dans un bloc VALUES joint en LEFT JOIN a la
   comptabilite : un compte sans mouvement renvoie zero, il ne disparait pas.
   Quatorze lignes, toujours, quel que soit le noeud clique. Le jour ou un
   compte s'ajoute au plan, on l'ajoute a la liste et le compte passe a quinze,
   en connaissance de cause.

   =============================================================================
   TROIS SOURCES, ET C'EST L'INTERET DE CE DRILL

   1. LE CHIFFRE D'AFFAIRES ne vient pas des comptes de produits mais du socle
      CRM. Les comptes existent -- 706 pour la scolarite des initiaux, 7062
      pour celle des alternants, 708 pour les frais d'inscription -- mais
      V_ALLOCATION ne les lit jamais. Q_D2_CA_COMPTA met les deux cote a cote.

   2. LES DOUZE COMPTES DE CHARGE sont lus tels quels sur le campus, dans
      AW_002_000004_000001. Ce sont de vraies ecritures, drillables plus loin.

   3. LE SIEGE n'est pas un compte du campus. Il est porte par GRP et
      redescendu par la cascade K1..K4 de V_ALLOCATION : la ligne est une
      ALLOCATION, pas une ecriture, et le libelle le dit.

   Verifie sur 2026 : 23 098 985 - 15 684 868 - 3 568 327 = 3 845 790.

   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Perimetre herite de la cellule cliquee, exercices en dur comme le cockpit.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    'CA'                                                    AS "Compte",
    'Produits'                                              AS "Famille",
    'Chiffre d''affaires (socle CRM)'                       AS "Poste",
    'Chiffre d''affaires'                                   AS "Poste court",
    SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2025 THEN a.CA ELSE 0 END)  AS "Montant 2025",
    SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2026 THEN a.CA ELSE 0 END)  AS "Montant 2026"
FROM    V_ALLOCATION AS a
WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(a.EXERCICE AS INT) IN (2025, 2026)

UNION ALL

SELECT
    r.COMPTE,
    r.FAMILLE,
    COALESCE(c.DESC_CONTO0, r.POSTE),
    r.COURT,
    -1 * SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2025 THEN d.AMOUNT ELSE 0 END),
    -1 * SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2026 THEN d.AMOUNT ELSE 0 END)
FROM (
        VALUES ('621',   'Cout variable', 'Personnel exterieur (vacataires)', 'Vacataires'),
               ('604',   'Cout variable', 'Achats d''etudes',                 'Achats d''etudes'),
               ('6063',  'Cout variable', 'Fournitures',                      'Fournitures'),
               ('6231',  'Cout variable', 'Publicite et acquisition',         'Acquisition'),
               ('6411',  'Couts directs', 'Salaires des permanents',          'Salaires'),
               ('6413',  'Couts directs', 'Primes',                           'Primes'),
               ('645',   'Couts directs', 'Charges sociales',                 'Charges sociales'),
               ('613',   'Couts directs', 'Loyers',                           'Loyers'),
               ('615',   'Couts directs', 'Entretien',                        'Entretien'),
               ('616',   'Couts directs', 'Assurances',                       'Assurances'),
               ('625',   'Couts directs', 'Deplacements',                     'Deplacements'),
               ('63511', 'Couts directs', 'Taxes',                            'Taxes')
     ) AS r(COMPTE, FAMILLE, POSTE, COURT)
LEFT JOIN AW_002_000004_000001 AS d
       ON  d.ACCOUNT = r.COMPTE
      AND  d.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
      AND  CAST(d.EXERCICE AS INT) IN (2025, 2026)
LEFT JOIN conto AS c
       ON  c.COD_CONTO = r.COMPTE
GROUP BY r.COMPTE, r.FAMILLE, COALESCE(c.DESC_CONTO0, r.POSTE), r.COURT

UNION ALL

SELECT
    'SIEGE'                                                 AS "Compte",
    'Siege'                                                 AS "Famille",
    'Siege redescendu (allocation, pas une ecriture)'       AS "Poste",
    'Siege'                                                 AS "Poste court",
    -1 * SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2025 THEN a.COST_SIEGE ELSE 0 END),
    -1 * SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2026 THEN a.COST_SIEGE ELSE 0 END)
FROM    V_ALLOCATION AS a
WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(a.EXERCICE AS INT) IN (2025, 2026)
