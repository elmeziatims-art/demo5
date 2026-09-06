/* =============================================================================
   Q_BRIDGE_5_LIGNES  —  SQL SERVER, a lancer telle quelle.
   Sort CINQ lignes, exactement le tableau du graphe en cascade :

     RANG  ETAPE          SOCLE       ANCRE      HAUSSE      BAISSE
       1   EBITDA 2025        0   3 467 768           0           0
       2   Activite   3 467 768           0   1 157 203           0
       3   Prix / mix 4 624 364           0           0         607
       4   Couts      3 845 790           0           0     778 574
       5   EBITDA 2026        0   3 845 790           0           0

   Empilement : SOCLE en bas et invisible, puis ANCRE, HAUSSE et BAISSE en
   trois series. RANG donne l'ordre des barres.

   =============================================================================
   LES DEUX PARAMETRES  —  chercher le mot PARAMETRE dans le texte
   =============================================================================

   1. LE PERIMETRE D'ENTITES. Le filtre est ecrit DEUX FOIS, une fois dans le
      bloc de l'annee N et une fois dans celui de l'annee N-1. Les deux doivent
      porter la meme liste, sans quoi le bridge compare deux perimetres
      differents et ne boucle plus.

          AND a.ENTITY IN (?)          -- parametre azienda

   2. L'EXERCICE, une seule fois, sur l'annee N. Ne PAS le poser sur le bloc
      N-1 : c'est la jointure qui va chercher l'annee precedente toute seule.

          AND n.EXERCICE = ?

   Sans aucun filtre, la requete renvoie cinq lignes par exercice ayant un N-1
   disponible, pour le groupe entier.

   =============================================================================
   LES CINQ ETAPES

     1  EBITDA N-1     ancre de depart
     2  Activite       (EFF_N - EFF_P) x (CA/eleve_P - CVAR/eleve_P)
     3  Prix / mix     (CA/eleve_N - CA/eleve_P) x EFF_N
     4  Couts          cout variable unitaire + couts directs + siege
     5  EBITDA N       ancre d'arrivee

   Decomposition exacte : 2 + 3 + 4 redonne EBITDA_N moins EBITDA_P sans
   residu, quel que soit le perimetre choisi. La variation de CA et celle du
   cout variable sont chacune coupees en volume x unitaire, il ne reste rien.

   L'agregation du perimetre est faite AVANT le test de signe : c'est ce qui
   permet de sortir SOCLE, ANCRE, HAUSSE et BAISSE directement. Ne pas faire
   re-agreger ces quatre colonnes par une matrice -- un MIN et un test de
   signe ne survivent pas a une somme. Pour une matrice, prendre
   Q_BRIDGE_WATERFALL et son trio additif MONTANT / BASE / CUMUL.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    e.RANG,
    CASE e.RANG
        WHEN 1 THEN 'EBITDA ' + CAST(g.EXERCICE_N1 AS VARCHAR(4))
        WHEN 5 THEN 'EBITDA ' + CAST(g.EXERCICE    AS VARCHAR(4))
        ELSE        e.ETAPE
    END                                                     AS ETAPE,

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
    END                                                     AS BAISSE,

    g.SCENARIO,
    g.VERSION,
    g.PERIODE,
    g.EXERCICE,
    g.EXERCICE_N1
FROM (
        SELECT
            x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE, x.EXERCICE_N1,
            SUM(x.EBITDA_P)                                 AS EBITDA_P,
            SUM(x.EBITDA_N)                                 AS EBITDA_N,
            SUM(x.E_VOL)                                    AS E_VOL,
            SUM(x.E_PRIX)                                   AS E_PRIX,
            SUM(x.E_CVAR + x.E_CDIR + x.E_SIEGE)            AS E_COUT
        FROM (
                SELECT
                    n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE,
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
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        WHERE   1 = 1
                          /* PARAMETRE  perimetre, annee N
                          AND   a.ENTITY IN (?)
                          */
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
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
                        WHERE   1 = 1
                          /* PARAMETRE  perimetre, annee N-1 : MEME liste qu'au-dessus
                          AND   a.ENTITY IN (?)
                          */
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
                     ) AS p
                       ON  p.SCENARIO = n.SCENARIO
                      AND  p.VERSION  = n.VERSION
                      AND  p.PERIODE  = n.PERIODE
                      AND  p.ENTITY   = n.ENTITY
                      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
                WHERE  1 = 1
                  /* PARAMETRE  exercice : sur l'annee N SEULEMENT
                  AND  n.EXERCICE = ?
                  */
             ) AS x
        GROUP BY x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE, x.EXERCICE_N1
     ) AS g
CROSS JOIN (
        VALUES (1, 'EBITDA N-1'),
               (2, 'Activite'),
               (3, 'Prix / mix'),
               (4, 'Couts'),
               (5, 'EBITDA N')
     ) AS e(RANG, ETAPE)
