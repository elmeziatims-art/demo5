-- =============================================================================
-- Q_COCKPIT — query pour DATASOURCE Tagetik (cockpit), forme "en ligne" FST-ready
-- =============================================================================
-- Datasource -> matrice multidim. Rien de pré-calculé : le FST calcule CA/EBITDA/marge.
--   Finance    = comptes P&L réels (dont 6231 = dépense acquisition) -> la hiérarchie
--                Compte / FST 010 remonte CA (noeud Produits) et EBITDA. (Ne PAS utiliser TEC_*.)
--   Commercial = comptes STATISTIQUES du référentiel : STA_LEAD, STA_CAND, STA_ADMIS,
--                STA_NOUV (inscrits), STA_EFF.
--   NB : STA_LEAD à créer dans la dim Compte (les autres existent déjà).
-- Membres calculés Tagetik : Marge % = EBITDA/CA ; CAC = 6231 / STA_NOUV.
-- Maille fine : finance = ENTITY×ACCOUNT×EXERCICE×PERIOD ;
--               commercial = + PROGRAMME×AN_ETUDE×MODALITE. Non applicable = 'GEN'.
-- Années retournées telles quelles (2024-2026) ; réalisé/atterrissage = description des membres.
-- =============================================================================
SELECT ENTITY, 'GEN' AS PROGRAMME, 'GEN' AS AN_ETUDE, 'GEN' AS MODALITE,
       ACCOUNT, EXERCICE, CAST(PERIOD AS VARCHAR(10)) AS PERIOD, 'ACT' AS VERSION,
       SUM(AMOUNT) AS AMOUNT
FROM AW_002_000004_000001
GROUP BY ENTITY, ACCOUNT, EXERCICE, CAST(PERIOD AS VARCHAR(10))

UNION ALL
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STA_LEAD', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_LEAD)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STA_CAND', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_CAND)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STA_ADMIS', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_ADMIS)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STA_NOUV', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_NEW)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STA_EFF', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_EFF)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10));
