-- =============================================================================
-- DRILL « ET DANS LA COMPTA, QUELS COMPTES ONT BOUGE ? »
--
-- Le second drill a poser sur la MEME cellule. Le premier dit POURQUOI
-- (effets economiques), celui-ci dit OU dans le plan de comptes -- c'est lui
-- qui ramene a la donnee comptable, compte par compte.
--
-- Memes parametres herites du contexte de la cellule.
--   :SCENARIO  :VERSION  :PERIODE  :EXERCICE  :ENTITY
--
-- REMPLACER AW_COMPTA par le nom reel de la table comptable chargee, et
-- COMPTE / MONTANT par ses colonnes. Le reste ne bouge pas.
-- =============================================================================
WITH c AS (
    SELECT c.COMPTE,
           SUM(CASE WHEN c.EXERCICE = :EXERCICE THEN c.MONTANT ELSE 0 END) AS M_N,
           SUM(CASE WHEN CAST(c.EXERCICE AS INTEGER) = CAST(:EXERCICE AS INTEGER) - 1
                    THEN c.MONTANT ELSE 0 END)                             AS M_P
    FROM AW_COMPTA c
    WHERE c.SCENARIO = :SCENARIO
      AND c.VERSION  = :VERSION
      AND c.PERIODE  = :PERIODE
      AND c.ENTITY   = :ENTITY
      AND CAST(c.EXERCICE AS INTEGER) IN (CAST(:EXERCICE AS INTEGER), CAST(:EXERCICE AS INTEGER) - 1)
      AND c.COMPTE NOT LIKE 'TEC%'          -- comptes techniques exclus
    GROUP BY c.COMPTE
)
SELECT c.COMPTE,
       CASE SUBSTRING(c.COMPTE, 1, 3)
            WHEN '706' THEN 'Scolarite initiale'
            WHEN '708' THEN 'Produits annexes'
            WHEN '621' THEN 'Vacataires'
            WHEN '604' THEN 'Achats de prestations'
            WHEN '641' THEN 'Masse salariale permanente'
            WHEN '623' THEN 'Acquisition et marque'
            ELSE 'Autres'
       END                                            AS LIBELLE,
       ROUND(c.M_P)                                   AS MONTANT_N1,
       ROUND(c.M_N)                                   AS MONTANT_N,
       ROUND(c.M_N - c.M_P)                           AS VARIATION,
       ROUND(100 * 1.0 * (c.M_N - c.M_P) / NULLIF(ABS(c.M_P), 0), 1) AS VARIATION_PCT
FROM c
WHERE ABS(c.M_N - c.M_P) > 0
ORDER BY ABS(c.M_N - c.M_P) DESC          -- ce qui a le plus bouge en premier
;
