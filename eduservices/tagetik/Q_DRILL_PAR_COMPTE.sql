/* =============================================================================
   Q_DRILL_PAR_COMPTE  —  SQL SERVER. Le second drill, sur la MEME cellule.
   « Et dans la compta, quels comptes ont bouge ? »

   Le drill Q_DRILL_POURQUOI donne la cause economique ; celui-ci dit quelle
   ligne comptable la porte. Trie par variation absolue decroissante.

   Parametres : :ENTITY  :EXERCICE  :VERSION
   Les libelles suivent le decoupage reel de V_ALLOCATION :
       621                              -> vacataires        (cout variable)
       604, 6063                        -> achats directs    (cout variable)
       6231                             -> acquisition       (cout variable)
       6411                             -> masse permanente  (cout direct)
       6413,645,613,615,616,625,63511   -> structure campus  (cout direct)
   Le siege (6236 marque, 6414/6226/626/6281/6331/6333 holding) est porte par
   l'entite GRP : il n'apparait donc pas ici, il arrive par allocation.

   Pas de CTE, pas de point-virgule.
   ============================================================================= */
SELECT
    x.ACCOUNT                                         AS COMPTE,
    CASE
        WHEN x.ACCOUNT = '621'                        THEN 'Vacataires'
        WHEN x.ACCOUNT IN ('604','6063')              THEN 'Achats directs'
        WHEN x.ACCOUNT = '6231'                       THEN 'Acquisition'
        WHEN x.ACCOUNT = '6411'                       THEN 'Masse salariale permanente'
        WHEN x.ACCOUNT = '613'                        THEN 'Loyers et charges locatives'
        WHEN x.ACCOUNT IN ('6413','645')              THEN 'Personnel administratif'
        WHEN x.ACCOUNT IN ('615','616','625','63511') THEN 'Autres charges de structure'
        ELSE 'Autres'
    END                                               AS LIBELLE,
    CASE
        WHEN x.ACCOUNT IN ('621','604','6063','6231') THEN 'variable'
        ELSE 'direct'
    END                                               AS NATURE,
    ROUND(SUM(CASE WHEN CAST(x.EXERCICE AS INT) = CAST(:EXERCICE AS INT) - 1
                   THEN x.AMOUNT ELSE 0 END), 0)      AS MONTANT_N1,
    ROUND(SUM(CASE WHEN CAST(x.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
                   THEN x.AMOUNT ELSE 0 END), 0)      AS MONTANT_N,
    ROUND(SUM(CASE WHEN CAST(x.EXERCICE AS INT) = CAST(:EXERCICE AS INT)
                   THEN x.AMOUNT ELSE -x.AMOUNT END), 0) AS VARIATION
FROM (
        SELECT ENTITY, EXERCICE, 'ACT' AS VERSION, ACCOUNT, AMOUNT
        FROM   AW_002_000004_000001
        UNION ALL
        SELECT ENTITY, EXERCICE, VERSION, ACCOUNT, AMOUNT
        FROM   V_BUDGET
     ) AS x
WHERE  x.ENTITY  = :ENTITY
  AND  x.VERSION = :VERSION
  AND  CAST(x.EXERCICE AS INT) IN (CAST(:EXERCICE AS INT), CAST(:EXERCICE AS INT) - 1)
  AND  x.ACCOUNT IN ('621','604','6063','6231','6411','6413','645','613','615','616','625','63511')
GROUP BY x.ACCOUNT
