/* =============================================================================
   Q_D1_GRAPHE  —  DRILL-THROUGH sur une cellule d'EBITDA.
   "Pourquoi l'EBITDA a bouge" : la cascade, sept lignes, cinq colonnes.

     ETAPE    la categorie de l'axe
     SOCLE    la part invisible, en bas de l'empilement
     ANCRE    les deux barres de niveau, depart et arrivee
     HAUSSE   les effets favorables
     BAISSE   les effets defavorables

   Meme moteur et meme contexte herite que Q_D1_TABLEAU : l'entite et
   l'exercice de la cellule cliquee. Seule la mise en forme change -- le
   tableau donne les montants signes, le graphe les quatre series a empiler.

       AND a.ENTITY   IN (${$Entity(HIERARCHY("EDU")).lowest})
       AND a.EXERCICE IN (${$ANL_EXERCICE.code})

   Le socle vaut le plus bas des deux cumuls, avant et apres l'effet : c'est ce
   qui fait flotter la barre au bon endroit, qu'elle monte ou qu'elle descende.
   Ce test, comme celui du signe, est fait APRES la somme du perimetre. Ces
   quatre colonnes ne doivent donc PAS etre re-agregees par une matrice.

   L'ordre des sept barres n'est pas garanti sans ORDER BY, que le loader
   interdit. Si elles sortent melangees, ajouter e.RANG en premiere colonne et
   trier dessus cote report.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    e.ETAPE,

    /* le bas de la barre : le plus petit des deux cumuls */
    CAST(ROUND(
        CASE e.RANG
            WHEN 2 THEN CASE WHEN g.E_VOL   < 0 THEN g.EBITDA_P + g.E_VOL
                             ELSE g.EBITDA_P END
            WHEN 3 THEN CASE WHEN g.E_PRIX  < 0 THEN g.EBITDA_P + g.E_VOL + g.E_PRIX
                             ELSE g.EBITDA_P + g.E_VOL END
            WHEN 4 THEN CASE WHEN g.E_CVAR  < 0 THEN g.EBITDA_P + g.E_VOL + g.E_PRIX + g.E_CVAR
                             ELSE g.EBITDA_P + g.E_VOL + g.E_PRIX END
            WHEN 5 THEN CASE WHEN g.E_CDIR  < 0 THEN g.EBITDA_P + g.E_VOL + g.E_PRIX + g.E_CVAR + g.E_CDIR
                             ELSE g.EBITDA_P + g.E_VOL + g.E_PRIX + g.E_CVAR END
            WHEN 6 THEN CASE WHEN g.E_SIEGE < 0 THEN g.EBITDA_N
                             ELSE g.EBITDA_P + g.E_VOL + g.E_PRIX + g.E_CVAR + g.E_CDIR END
            ELSE        0
        END
    , 0) AS DECIMAL(18, 0))                                 AS SOCLE,

    CAST(ROUND(
        CASE e.RANG WHEN 1 THEN g.EBITDA_P WHEN 7 THEN g.EBITDA_N ELSE 0 END
    , 0) AS DECIMAL(18, 0))                                 AS ANCRE,

    CAST(ROUND(
        CASE e.RANG
            WHEN 2 THEN CASE WHEN g.E_VOL   > 0 THEN g.E_VOL   ELSE 0 END
            WHEN 3 THEN CASE WHEN g.E_PRIX  > 0 THEN g.E_PRIX  ELSE 0 END
            WHEN 4 THEN CASE WHEN g.E_CVAR  > 0 THEN g.E_CVAR  ELSE 0 END
            WHEN 5 THEN CASE WHEN g.E_CDIR  > 0 THEN g.E_CDIR  ELSE 0 END
            WHEN 6 THEN CASE WHEN g.E_SIEGE > 0 THEN g.E_SIEGE ELSE 0 END
            ELSE        0
        END
    , 0) AS DECIMAL(18, 0))                                 AS HAUSSE,

    CAST(ROUND(
        CASE e.RANG
            WHEN 2 THEN CASE WHEN g.E_VOL   < 0 THEN -1 * g.E_VOL   ELSE 0 END
            WHEN 3 THEN CASE WHEN g.E_PRIX  < 0 THEN -1 * g.E_PRIX  ELSE 0 END
            WHEN 4 THEN CASE WHEN g.E_CVAR  < 0 THEN -1 * g.E_CVAR  ELSE 0 END
            WHEN 5 THEN CASE WHEN g.E_CDIR  < 0 THEN -1 * g.E_CDIR  ELSE 0 END
            WHEN 6 THEN CASE WHEN g.E_SIEGE < 0 THEN -1 * g.E_SIEGE ELSE 0 END
            ELSE        0
        END
    , 0) AS DECIMAL(18, 0))                                 AS BAISSE
FROM (
        SELECT
            SUM(x.EBITDA_P) AS EBITDA_P, SUM(x.EBITDA_N) AS EBITDA_N,
            SUM(x.E_VOL)    AS E_VOL,    SUM(x.E_PRIX)   AS E_PRIX,
            SUM(x.E_CVAR)   AS E_CVAR,   SUM(x.E_CDIR)   AS E_CDIR,
            SUM(x.E_SIEGE)  AS E_SIEGE
        FROM (
                SELECT
                    p.EBITDA AS EBITDA_P, n.EBITDA AS EBITDA_N,
                    (n.EFFECTIFS - p.EFFECTIFS)
                      * (1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)
                         - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0))         AS E_VOL,
                    (1.0 * n.CA / NULLIF(n.EFFECTIFS, 0)
                     - 1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS     AS E_PRIX,
                    -1 * (1.0 * n.COST_VAR / NULLIF(n.EFFECTIFS, 0)
                          - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS AS E_CVAR,
                    -1 * (n.COST_DIR   - p.COST_DIR)                          AS E_CDIR,
                    -1 * (n.COST_SIEGE - p.COST_SIEGE)                        AS E_SIEGE
                FROM (
                        SELECT  a.ENTITY, a.EXERCICE,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        WHERE   a.ENTITY   IN (${$Entity(HIERARCHY("EDU")).lowest})
                          AND   a.EXERCICE IN (${$ANL_EXERCICE.code})
                        GROUP BY a.ENTITY, a.EXERCICE
                     ) AS n
                INNER JOIN (
                        SELECT  a.ENTITY, a.EXERCICE,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                        GROUP BY a.ENTITY, a.EXERCICE
                     ) AS p
                       ON  p.ENTITY = n.ENTITY
                      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
             ) AS x
     ) AS g
CROSS JOIN (
        VALUES (1, 'EBITDA N-1'),
               (2, 'Effet effectifs'),
               (3, 'Effet prix et mix'),
               (4, 'Effet cout variable unitaire'),
               (5, 'Effet couts directs'),
               (6, 'Effet siege'),
               (7, 'EBITDA N')
     ) AS e(RANG, ETAPE)
