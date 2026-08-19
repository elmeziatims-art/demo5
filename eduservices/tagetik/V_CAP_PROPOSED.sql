-- =============================================================================
-- VUE CAP PROPOSÉ par campus  (corps SELECT ; SAP HANA)
-- Sources : AW_002_000002_000001 (socle) + AW_002_000004_000001 (compta, cpte 6231)
-- 3 indicateurs mesurés + 3 caps normalisés à moyenne 1 (seul le relatif compte)
--   Cap éff. ∝ 1/CAC · Cap mom. ∝ croissance leads · Cap pot. ∝ 1/intensité mkt
-- CAP_RETENU = 1 (graine par défaut ; devient saisissable dans la table stockée).
-- =============================================================================
SELECT
    r.SCENARIO, r.PERIODE, r.ENTITY,
    r.CAC_MARGINAL,
    r.CROISS_LEADS,
    r.INTENSITE_MKT,
    r.INV_CAC      / NULLIF(AVG(r.INV_CAC)      OVER (PARTITION BY r.SCENARIO, r.PERIODE), 0) AS CAP_EFF,
    r.CROISS_LEADS / NULLIF(AVG(r.CROISS_LEADS) OVER (PARTITION BY r.SCENARIO, r.PERIODE), 0) AS CAP_MOM,
    r.INV_INT      / NULLIF(AVG(r.INV_INT)      OVER (PARTITION BY r.SCENARIO, r.PERIODE), 0) AS CAP_POT,
    1 AS CAP_RETENU
FROM (
    SELECT
        sagg.SCENARIO, sagg.PERIODE, sagg.ENTITY,
        sp.SPEND_2026  / NULLIF(sagg.NEW_2026, 0)       AS CAC_MARGINAL,     -- CAC = dépense acq / inscrit
        sagg.LEAD_2026 / NULLIF(sagg.LEAD_2024, 0) - 1  AS CROISS_LEADS,     -- croissance leads 2024->2026
        sp.SPEND_2026  / NULLIF(sagg.CA_2026, 0)        AS INTENSITE_MKT,    -- dépense acq / CA
        sagg.NEW_2026  / NULLIF(sp.SPEND_2026, 0)       AS INV_CAC,          -- 1/CAC (pour Cap éff.)
        sagg.CA_2026   / NULLIF(sp.SPEND_2026, 0)       AS INV_INT           -- 1/intensité (pour Cap pot.)
    FROM (
        SELECT
            s.SCENARIO, s.PERIODE, s.ENTITY,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_EFF * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS ELSE 0 END) AS CA_2026,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_NEW  ELSE 0 END) AS NEW_2026,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_LEAD ELSE 0 END) AS LEAD_2026,
            SUM(CASE WHEN s.EXERCICE = '2024' THEN s.VOL_LEAD ELSE 0 END) AS LEAD_2024
        FROM AW_002_000002_000001 s
        GROUP BY s.SCENARIO, s.PERIODE, s.ENTITY
    ) sagg
    LEFT JOIN (
        SELECT c.ENTITY, SUM(c.AMOUNT) AS SPEND_2026
        FROM AW_002_000004_000001 c
        WHERE c.ACCOUNT = '6231' AND c.EXERCICE = '2026'
        GROUP BY c.ENTITY
    ) sp ON sp.ENTITY = sagg.ENTITY
) r
