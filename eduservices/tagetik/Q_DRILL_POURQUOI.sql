/* =============================================================================
   Q_DRILL_POURQUOI  —  SQL SERVER. Requete de DRILL sur une cellule EBITDA.
   « Pourquoi l'EBITDA de ce campus a-t-il varie ? »

   Parametres herites du contexte de la cellule :
       :SCENARIO   :VERSION   :EXERCICE   :ENTITY
   (adapter aux placeholders de ton drill Tagetik)

   Renvoie un PONT de 7 lignes, pas un extrait de donnees. La decomposition
   est EXACTE par construction : dCA et dCVAR sont chacun eclates en
   volume x unitaire, donc les effets se somment exactement a la variation.
   Le total retombe sur la cellule cliquee.

   Le SIEGE a sa propre ligne : c'est la question ouverte sur les campus
   parisiens, autant la poser explicitement.

   Pas de CTE, pas de point-virgule. Trier sur ORDRE dans le rapport.
   ============================================================================= */
SELECT 1 AS ORDRE,
       'EBITDA ' + CAST(CAST(:EXERCICE AS INT) - 1 AS VARCHAR(4)) AS ETAPE,
       ROUND((p.CA - p.CVAR - p.CDIR - p.CSIEGE), 0) AS MONTANT,
       NULL AS DETAIL,
       'point de depart' AS LECTURE
FROM (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
     ) AS n
CROSS JOIN (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
     ) AS p
UNION ALL
SELECT 2 AS ORDRE,
       '+ Effet effectifs' AS ETAPE,
       ROUND((n.EFF - p.EFF) * ((1.0 * p.CA / NULLIF(p.EFF, 0)) - (1.0 * p.CVAR / NULLIF(p.EFF, 0))), 0) AS MONTANT,
       CAST(p.EFF AS VARCHAR(10)) + ' -> ' + CAST(n.EFF AS VARCHAR(10)) + ' eleves' AS DETAIL,
       'volume, valorise a la marge variable N-1' AS LECTURE
FROM (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
     ) AS n
CROSS JOIN (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
     ) AS p
UNION ALL
SELECT 3 AS ORDRE,
       '+ Effet prix / mix' AS ETAPE,
       ROUND(((1.0 * n.CA / NULLIF(n.EFF, 0)) - (1.0 * p.CA / NULLIF(p.EFF, 0))) * n.EFF, 0) AS MONTANT,
       CAST(CAST(1.0 * p.CA / NULLIF(p.EFF, 0) AS INT) AS VARCHAR(10)) + ' -> ' + CAST(CAST(1.0 * n.CA / NULLIF(n.EFF, 0) AS INT) AS VARCHAR(10)) + ' EUR / eleve' AS DETAIL,
       'tarif, mix initiale/alternance, mix programmes' AS LECTURE
FROM (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
     ) AS n
CROSS JOIN (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
     ) AS p
UNION ALL
SELECT 4 AS ORDRE,
       '- Effet cout variable unitaire' AS ETAPE,
       ROUND(-((1.0 * n.CVAR / NULLIF(n.EFF, 0)) - (1.0 * p.CVAR / NULLIF(p.EFF, 0))) * n.EFF, 0) AS MONTANT,
       CAST(CAST(1.0 * p.CVAR / NULLIF(p.EFF, 0) AS INT) AS VARCHAR(10)) + ' -> ' + CAST(CAST(1.0 * n.CVAR / NULLIF(n.EFF, 0) AS INT) AS VARCHAR(10)) + ' EUR / eleve' AS DETAIL,
       'vacataires, achats directs et marketing, par eleve' AS LECTURE
FROM (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
     ) AS n
CROSS JOIN (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
     ) AS p
UNION ALL
SELECT 5 AS ORDRE,
       '- Effet couts directs' AS ETAPE,
       ROUND(-(n.CDIR - p.CDIR), 0) AS MONTANT,
       CAST(CAST(p.CDIR/1000 AS INT) AS VARCHAR(10)) + ' -> ' + CAST(CAST(n.CDIR/1000 AS INT) AS VARCHAR(10)) + ' k EUR' AS DETAIL,
       'permanents et structure : ils ne suivent pas l activite' AS LECTURE
FROM (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
     ) AS n
CROSS JOIN (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
     ) AS p
UNION ALL
SELECT 6 AS ORDRE,
       '- Effet siege' AS ETAPE,
       ROUND(-(n.CSIEGE - p.CSIEGE), 0) AS MONTANT,
       CAST(CAST(p.CSIEGE/1000 AS INT) AS VARCHAR(10)) + ' -> ' + CAST(CAST(n.CSIEGE/1000 AS INT) AS VARCHAR(10)) + ' k EUR' AS DETAIL,
       'quote-part marque et holding' AS LECTURE
FROM (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
     ) AS n
CROSS JOIN (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
     ) AS p
UNION ALL
SELECT 7 AS ORDRE,
       'EBITDA ' + CAST(:EXERCICE AS VARCHAR(4)) AS ETAPE,
       ROUND((n.CA - n.CVAR - n.CDIR - n.CSIEGE), 0) AS MONTANT,
       'marge ' + CAST(CAST(ROUND(100.0 * (n.CA - n.CVAR - n.CDIR - n.CSIEGE) / NULLIF(n.CA,0), 1) AS DECIMAL(6,1)) AS VARCHAR(10)) + ' %' AS DETAIL,
       'doit egaler la cellule cliquee' AS LECTURE
FROM (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
     ) AS n
CROSS JOIN (
        SELECT  SUM(a.VOL_EFF)                                   AS EFF,
                SUM(a.CA)                                        AS CA,
                SUM(a.COST_VARIABLE)                             AS CVAR,
                SUM(a.COST_PERM + a.COST_STRUCT)                 AS CDIR,
                SUM(a.COST_SIEGE)                                AS CSIEGE
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   = :ENTITY
          AND   a.SCENARIO = :SCENARIO
          AND   a.VERSION  = :VERSION
          AND   CAST(a.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
     ) AS p
