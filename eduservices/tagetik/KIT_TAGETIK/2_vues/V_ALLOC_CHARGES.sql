-- =============================================================================
-- V_ALLOC_CHARGES — restitution rapide des 3 charges REELLEMENT allouees
-- (les seules qui descendent en cascade jusqu'a la classe) :
--   1) STRUCT_CAMP  : structure du campus (6413,645,613,615,616,625,63511)
--                     -> allouee aux classes du campus (cle K3)
--   2) FRAIS_MARQUE : publicite de la marque (6236, niveau GROUPE)
--                     -> groupe->marque (K4) puis marque->campus->classe
--   3) HOLDING      : siege & fonctions centrales (6414,6226,626,6281,6331,6333, GROUPE)
--                     -> groupe->marque (K1) puis marque->campus->classe
-- Un montant par EXERCICE x VERSION : 2026 reel (Compta, VERSION='ACT')
-- et 2027 budget (V_BUDGET, V01/V02/V03). Meme sources que V_ALLOCATION.
-- =============================================================================
CREATE OR REPLACE VIEW V_ALLOC_CHARGES AS
SELECT
    p.EXERCICE, p.VERSION,
    SUM(CASE WHEN p.ACCOUNT IN ('6413','645','613','615','616','625','63511')
             THEN p.AMOUNT ELSE 0 END)                                   AS STRUCT_CAMP,
    SUM(CASE WHEN p.ENTITY='GRP' AND p.ACCOUNT='6236'
             THEN p.AMOUNT ELSE 0 END)                                   AS FRAIS_MARQUE,
    SUM(CASE WHEN p.ENTITY='GRP' AND p.ACCOUNT IN ('6414','6226','626','6281','6331','6333')
             THEN p.AMOUNT ELSE 0 END)                                   AS HOLDING,
    SUM(CASE WHEN p.ACCOUNT IN ('6413','645','613','615','616','625','63511')
              OR (p.ENTITY='GRP' AND p.ACCOUNT IN ('6236','6414','6226','626','6281','6331','6333'))
             THEN p.AMOUNT ELSE 0 END)                                   AS TOTAL_ALLOUE
FROM (
    SELECT ENTITY, EXERCICE, 'ACT' AS VERSION, ACCOUNT, AMOUNT FROM AW_002_000004_000001
    UNION ALL
    SELECT ENTITY, EXERCICE, VERSION, ACCOUNT, AMOUNT FROM V_BUDGET
) p
GROUP BY p.EXERCICE, p.VERSION;
