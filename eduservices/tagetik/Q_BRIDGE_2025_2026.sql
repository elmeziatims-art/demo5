/* =============================================================================
   Q_BRIDGE_2025_2026  —  SQL SERVER, a lancer telle quelle.
   Cinq lignes, quatre colonnes, rien d'autre :

     RANG  ETAPE            SOCLE       ANCRE      HAUSSE      BAISSE
       1   EBITDA 2025          0   3 467 768           0           0
       2   Activite     3 467 768           0   1 157 203           0
       3   Prix / mix   4 624 364           0           0         607
       4   Couts        3 845 790           0           0     778 574
       5   EBITDA 2026          0   3 845 790           0           0

   Empilement du graphe : SOCLE en bas et invisible, puis ANCRE, HAUSSE et
   BAISSE en trois series. RANG donne l'ordre des barres.

   Le perimetre est passe par le parametre Tagetik, sur les DEUX annees :
   les deux filtres doivent porter la meme selection, sinon le bridge compare
   deux perimetres differents et ne boucle plus.

       AND a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})

   La substitution Tagetik se fait entre ${ }, comme dans Q_DRILL_COCKPIT ou
   l'on ecrit deja  IN (${$Entity.code})  et  IN (${$Account.code}).

   Si la vue expose la colonne sous son nom Tagetik, remplacer a.ENTITY par
   a.COD_AZIENDA aux deux endroits.

   Les exercices sont poses en dur, 2025 vers 2026, un dans chaque bloc. Pour
   glisser d'une annee il suffit de changer les deux constantes et les deux
   libelles d'ancre.

   La somme du perimetre est faite AVANT le test de signe : c'est ce qui
   permet de sortir SOCLE, ANCRE, HAUSSE et BAISSE deja mis en forme. Ne pas
   faire re-agreger ces quatre colonnes par une matrice -- un MIN et un test
   de signe ne survivent pas a une somme.

   Decomposition exacte : Activite + Prix/mix + Couts redonne EBITDA 2026
   moins EBITDA 2025 sans residu, sur n'importe quel perimetre.

     Activite     (EFF_26 - EFF_25) x (CA/eleve_25 - CVAR/eleve_25)
     Prix / mix   (CA/eleve_26 - CA/eleve_25) x EFF_26
     Couts        cout variable unitaire + couts directs + siege

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    e.RANG,
    e.ETAPE,

    CASE e.RANG
        WHEN 2 THEN CASE WHEN g.E_VOL  < 0 THEN g.EBITDA_P + g.E_VOL
                         ELSE g.EBITDA_P END
        WHEN 3 THEN CASE WHEN g.E_PRIX < 0 THEN g.EBITDA_P + g.E_VOL + g.E_PRIX
                         ELSE g.EBITDA_P + g.E_VOL END
        WHEN 4 THEN CASE WHEN g.E_COUT < 0 THEN g.EBITDA_N
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
    END                                                     AS BAISSE
FROM (
        SELECT
            SUM(x.EBITDA_P)                                 AS EBITDA_P,
            SUM(x.EBITDA_N)                                 AS EBITDA_N,
            SUM(x.E_VOL)                                    AS E_VOL,
            SUM(x.E_PRIX)                                   AS E_PRIX,
            SUM(x.E_CVAR + x.E_CDIR + x.E_SIEGE)            AS E_COUT
        FROM (
                SELECT
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
                        SELECT  a.ENTITY,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        WHERE   CAST(a.EXERCICE AS INT) = 2026
                          AND   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                        GROUP BY a.ENTITY
                     ) AS n
                INNER JOIN (
                        SELECT  a.ENTITY,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        WHERE   CAST(a.EXERCICE AS INT) = 2025
                          AND   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                        GROUP BY a.ENTITY
                     ) AS p
                       ON  p.ENTITY = n.ENTITY
             ) AS x
     ) AS g
CROSS JOIN (
        VALUES (1, N'EBITDA 2025'),
               (2, N'Activité'),
               (3, N'Prix / mix'),
               (4, N'Coûts'),
               (5, N'EBITDA 2026')
     ) AS e(RANG, ETAPE)
