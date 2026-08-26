-- =============================================================================
-- Restitution des 3 charges allouees DESCENDUES A LA MARQUE, par scenario (2027).
-- Pont entre l'enveloppe groupe (V_ALLOC_CHARGES) et la maille fine campus/classe :
--   somme des marques d'un scenario = le total de V_ALLOC_CHARGES pour ce scenario.
-- S'appuie sur V_ALLOCATION (COST_* deja calcules par classe).
-- =============================================================================
SELECT
    CASE VERSION WHEN 'V01' THEN 'Cadrage'
                 WHEN 'V02' THEN 'Optimiste'
                 WHEN 'V03' THEN 'Prudent'
                 ELSE VERSION END                        AS "Scénario",
    MARQUE                                               AS "Marque",
    SUM(COST_STRUCT)                                     AS "Structure Campus",
    SUM(COST_MARQUE)                                     AS "Frais de marque",
    SUM(COST_HOLDING)                                    AS "Holding",
    SUM(COST_STRUCT + COST_MARQUE + COST_HOLDING)        AS "Total alloué"
FROM V_ALLOCATION
WHERE EXERCICE = '2027'
  AND VERSION IN ('V01','V02','V03')
GROUP BY VERSION, MARQUE
ORDER BY VERSION, MARQUE;
