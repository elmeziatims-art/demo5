/* =============================================================================
   Q_G1_PONT  —  SQL SERVER, a lancer telle quelle.
   CINQ COLONNES, CINQ LIGNES. Rien que ce que le graphe en cascade consomme.

     ETAPE        la categorie de l'axe
     SOCLE        la part invisible, en bas de l'empilement
     ANCRE        les deux barres de niveau, depart et arrivee
     HAUSSE       les effets favorables
     BAISSE       les effets defavorables

   Empilement : SOCLE sans remplissage, puis ANCRE, HAUSSE, BAISSE.

   L'ORDRE DES LIGNES. Il n'y a plus de colonne de rang, donc les cinq lignes
   arrivent dans l'ordre ou le moteur les rend. Sur ce CROSS JOIN il suit la
   liste VALUES, mais SQL Server ne le garantit pas sans ORDER BY -- et le
   loader Tagetik interdit ORDER BY. Si les barres sortent melangees, remettre
   e.RANG en premiere colonne et trier dessus cote report.

   Perimetre par le parametre, sur les DEUX annees, meme selection des deux
   cotes. Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   =============================================================================

   =============================================================================
   LES EN-TETES SONT EN CLAIR, entre GUILLEMETS DOUBLES -- Tagetik n'accepte
   pas les crochets. Le drill-through affiche la
   sortie telle quelle a l'utilisateur : autant qu'il lise "CA par eleve N-1"
   plutot que CAE_P.

   Si le canal du loader ne conserve pas les accents -- c'est ce qui avait
   transforme "Activite" en "Activit?" sur des litteraux -- retirer simplement
   les accents dans les crochets. La requete ne change pas autrement.
   =============================================================================
   */
SELECT
    e.ETAPE AS "Étape",

    CAST(ROUND(
        CASE e.RANG
            WHEN 2 THEN CASE WHEN g.E_VOL  < 0 THEN g.EBITDA_P + g.E_VOL
                             ELSE g.EBITDA_P END
            WHEN 3 THEN CASE WHEN g.E_PRIX < 0 THEN g.EBITDA_P + g.E_VOL + g.E_PRIX
                             ELSE g.EBITDA_P + g.E_VOL END
            WHEN 4 THEN CASE WHEN g.E_COUT < 0 THEN g.EBITDA_N
                             ELSE g.EBITDA_P + g.E_VOL + g.E_PRIX END
            ELSE        0
        END
    , 0) AS DECIMAL(18, 0))                                 AS "Socle invisible",

    CAST(ROUND(
        CASE e.RANG WHEN 1 THEN g.EBITDA_P WHEN 5 THEN g.EBITDA_N ELSE 0 END
    , 0) AS DECIMAL(18, 0))                                 AS "Ancre",

    CAST(ROUND(
        CASE e.RANG
            WHEN 2 THEN CASE WHEN g.E_VOL  > 0 THEN g.E_VOL  ELSE 0 END
            WHEN 3 THEN CASE WHEN g.E_PRIX > 0 THEN g.E_PRIX ELSE 0 END
            WHEN 4 THEN CASE WHEN g.E_COUT > 0 THEN g.E_COUT ELSE 0 END
            ELSE        0
        END
    , 0) AS DECIMAL(18, 0))                                 AS "Hausse",

    CAST(ROUND(
        CASE e.RANG
            WHEN 2 THEN CASE WHEN g.E_VOL  < 0 THEN -1 * g.E_VOL  ELSE 0 END
            WHEN 3 THEN CASE WHEN g.E_PRIX < 0 THEN -1 * g.E_PRIX ELSE 0 END
            WHEN 4 THEN CASE WHEN g.E_COUT < 0 THEN -1 * g.E_COUT ELSE 0 END
            ELSE        0
        END
    , 0) AS DECIMAL(18, 0))                                 AS "Baisse"
FROM (
        SELECT
            SUM(x.EBITDA_P)                      AS EBITDA_P,
            SUM(x.EBITDA_N)                      AS EBITDA_N,
            SUM(x.E_VOL)                         AS E_VOL,
            SUM(x.E_PRIX)                        AS E_PRIX,
            SUM(x.E_CVAR + x.E_CDIR + x.E_SIEGE) AS E_COUT
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
        VALUES (1, 'EBITDA 2025'),
               (2, 'Activite'),
               (3, 'Prix / mix'),
               (4, 'Couts'),
               (5, 'EBITDA 2026')
     ) AS e(RANG, ETAPE)
