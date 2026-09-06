/* =============================================================================
   Q_BRIDGE_WATERFALL_DIRECT  —  SQL SERVER, a lancer TELLE QUELLE.
   Sort directement le tableau du graphe en cascade, deja agrege :

       Etape          SOCLE       ANCRE      HAUSSE      BAISSE
       EBITDA N-1         0   3 467 768           0           0
       Activite   3 467 768           0   1 157 203           0
       Prix / mix 4 624 364           0           0         607
       Couts      3 845 790           0           0     778 574
       EBITDA N           0   3 845 790           0           0

   Cinq lignes pour le GROUPE, cinq lignes par MARQUE, dans le meme jet.
   Filtrer NIVEAU = 'GROUPE' pour le graphe consolide, NIVEAU = 'MARQUE' pour
   le petit multiple par enseigne. RANG donne l'ordre des barres.

   =============================================================================
   POURQUOI CELLE-CI PEUT SE PERMETTRE CES QUATRE COLONNES

   SOCLE, ANCRE, HAUSSE et BAISSE reposent sur un MIN et sur un test de signe,
   qui ne survivent pas a une somme : SUM(MAX(x,0)) n'est pas MAX(SUM(x),0).
   Sur 2025 -> 2026 l'effet prix est positif sur les deux Pigier et negatif sur
   les douze autres campus ; sommer des colonnes calculees par campus
   afficherait au groupe une hausse ET une baisse sur la meme barre.

   Ici l'agregation est faite AVANT le test de signe, a l'interieur de la
   requete, par un GROUP BY GROUPING SETS qui produit d'un coup le niveau
   marque et le niveau groupe. Les quatre colonnes sont donc exactes aux deux
   niveaux -- a condition de lancer la requete telle quelle et de ne pas la
   faire re-agreger par une matrice. Pour une matrice qui agrege librement,
   c'est Q_BRIDGE_WATERFALL qu'il faut, avec son trio additif.

   =============================================================================
   LES CINQ ETAPES

     1  EBITDA N-1     ancre de depart
     2  Activite       (EFF_N - EFF_P) x (CA/eleve_P - CVAR/eleve_P)
     3  Prix / mix     (CA/eleve_N - CA/eleve_P) x EFF_N
     4  Couts          cout variable unitaire + couts directs + siege
     5  EBITDA N       ancre d'arrivee

   Decomposition exacte : 2 + 3 + 4 redonne EBITDA_N moins EBITDA_P, sans
   residu. Empilement du graphe : SOCLE en bas et invisible, puis ANCRE,
   HAUSSE et BAISSE en trois series.

   Filtrer EXERCICE = 2026 donne le bridge 2025 -> 2026.
   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    g.NIVEAU,
    g.MARQUE,
    g.SCENARIO,
    g.VERSION,
    g.PERIODE,
    g.EXERCICE,
    g.EXERCICE_N1,
    e.RANG,
    e.ETAPE,

    CASE e.RANG
        WHEN 2 THEN g.EBITDA_P
        WHEN 3 THEN CASE WHEN g.E_PRIX < 0
                         THEN g.EBITDA_P + g.E_VOL + g.E_PRIX
                         ELSE g.EBITDA_P + g.E_VOL END
        WHEN 4 THEN CASE WHEN g.E_COUT < 0
                         THEN g.EBITDA_N
                         ELSE g.EBITDA_P + g.E_VOL + g.E_PRIX END
        ELSE        0
    END                                                     AS SOCLE,

    CASE e.RANG
        WHEN 1 THEN g.EBITDA_P
        WHEN 5 THEN g.EBITDA_N
        ELSE        0
    END                                                     AS ANCRE,

    CASE e.RANG
        WHEN 2 THEN CASE WHEN g.E_VOL  > 0 THEN g.E_VOL  ELSE 0 END
        WHEN 3 THEN CASE WHEN g.E_PRIX > 0 THEN g.E_PRIX ELSE 0 END
        WHEN 4 THEN CASE WHEN g.E_COUT > 0 THEN g.E_COUT ELSE 0 END
        ELSE        0
    END                                                     AS HAUSSE,

    CASE e.RANG
        WHEN 2 THEN CASE WHEN g.E_VOL  < 0 THEN -1 * g.E_VOL  ELSE 0 END
        WHEN 3 THEN CASE WHEN g.E_PRIX < 0 THEN -1 * g.E_PRIX ELSE 0 END
        WHEN 4 THEN CASE WHEN g.E_COUT < 0 THEN -1 * g.E_COUT ELSE 0 END
        ELSE        0
    END                                                     AS BAISSE,

    CASE e.RANG
        WHEN 1 THEN g.EBITDA_P
        WHEN 2 THEN g.E_VOL
        WHEN 3 THEN g.E_PRIX
        WHEN 4 THEN g.E_COUT
        ELSE        g.EBITDA_N
    END                                                     AS MONTANT
FROM (
        SELECT
            CASE WHEN GROUPING(x.MARQUE) = 1 THEN 'GROUPE' ELSE 'MARQUE' END AS NIVEAU,
            COALESCE(x.MARQUE, '(TOUTES)')                  AS MARQUE,
            x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE, x.EXERCICE_N1,
            SUM(x.EBITDA_P)                                 AS EBITDA_P,
            SUM(x.EBITDA_N)                                 AS EBITDA_N,
            SUM(x.E_VOL)                                    AS E_VOL,
            SUM(x.E_PRIX)                                   AS E_PRIX,
            SUM(x.E_CVAR + x.E_CDIR + x.E_SIEGE)            AS E_COUT
        FROM (
                SELECT
                    n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE, n.MARQUE,
                    p.EXERCICE                              AS EXERCICE_N1,
                    p.EBITDA                                AS EBITDA_P,
                    n.EBITDA                                AS EBITDA_N,
                    (n.EFFECTIFS - p.EFFECTIFS)
                      * (1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)
                         - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0))         AS E_VOL,
                    (1.0 * n.CA / NULLIF(n.EFFECTIFS, 0)
                     - 1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS     AS E_PRIX,
                    -1 * (1.0 * n.COST_VAR / NULLIF(n.EFFECTIFS, 0)
                          - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS AS E_CVAR,
                    -1 * (n.COST_DIR - p.COST_DIR)                            AS E_CDIR,
                    -1 * (n.COST_SIEGE - p.COST_SIEGE)                        AS E_SIEGE
                FROM (
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
                     ) AS n
                INNER JOIN (
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
                     ) AS p
                       ON  p.SCENARIO = n.SCENARIO
                      AND  p.VERSION  = n.VERSION
                      AND  p.PERIODE  = n.PERIODE
                      AND  p.ENTITY   = n.ENTITY
                      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
             ) AS x
        GROUP BY GROUPING SETS (
                    (x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE, x.EXERCICE_N1, x.MARQUE),
                    (x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE, x.EXERCICE_N1)
                 )
     ) AS g
CROSS JOIN (
        VALUES (1, 'EBITDA N-1'),
               (2, 'Activite'),
               (3, 'Prix / mix'),
               (4, 'Couts'),
               (5, 'EBITDA N')
     ) AS e(RANG, ETAPE)
