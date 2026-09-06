-- =============================================================================
-- V_CAP — Cap stratégique par campus (identique à l'Excel bloc ①) — SQL Server
-- Appelle V_CAMPAGNES (CAC marginal, dépense acq réf) + socle (croissance leads, CA).
--   Cap éff. ∝ 1/CAC marginal · Cap mom. ∝ croissance leads (org+payant) · Cap pot. ∝ 1/intensité
--   normalisés à moyenne 1. CAP_RETENU = 1 (saisissable). + rejeu du budget d'acquisition (somme nulle).
-- Vérifié = Excel : MBway Paris 0,81/1,06/0,86 · Tunon Paris 0,55/0,67/0,68.
-- =============================================================================
CREATE OR ALTER VIEW V_CAP AS
SELECT
    n.SCENARIO, n.PERIODE, n.ENTITY,
    n.CAC_MARGINAL, n.CROISS_LEADS, n.INTENSITE_MKT,
    1.0 * n.INV_CAC / NULLIF(AVG(n.INV_CAC)      OVER (PARTITION BY n.SCENARIO, n.PERIODE), 0) AS CAP_EFF,
    1.0 * n.CROISS_LEADS / NULLIF(AVG(n.CROISS_LEADS) OVER (PARTITION BY n.SCENARIO, n.PERIODE), 0) AS CAP_MOM,
    1.0 * n.INV_INT / NULLIF(AVG(n.INV_INT)      OVER (PARTITION BY n.SCENARIO, n.PERIODE), 0) AS CAP_POT,
    n.CAP_RETENU,
    n.BUDGET_ACQ_REF,
    n.BUDGET_ACQ_REF * n.CAP_RETENU
        * ( SUM(n.BUDGET_ACQ_REF) OVER 1.0 * (PARTITION BY n.SCENARIO, n.PERIODE) / NULLIF(SUM(n.BUDGET_ACQ_REF * n.CAP_RETENU) OVER (PARTITION BY n.SCENARIO, n.PERIODE), 0) )
        AS BUDGET_ACQ_REJOUE
FROM (
    SELECT
        cp.SCENARIO, cp.PERIODE, cp.ENTITY,
        cp.CAC_MARGINAL,
        COALESCE(1.0 * sm.LEAD_TOT_26 / NULLIF(sm.LEAD_TOT_24, 0), 0) - 1 AS CROISS_LEADS,
        COALESCE(1.0 * cp.SPEND_ACQ_REF / NULLIF(sm.CA_26, 0), 0)        AS INTENSITE_MKT,
        1.0 * 1.0 / NULLIF(cp.CAC_MARGINAL, 0)                AS INV_CAC,
        1.0 * sm.CA_26 / NULLIF(cp.SPEND_ACQ_REF, 0)              AS INV_INT,
        1              AS CAP_RETENU,
        cp.SPEND_ACQ_REF AS BUDGET_ACQ_REF
    FROM V_CAMPAGNES cp
    JOIN (
        SELECT s.SCENARIO, s.PERIODE, s.ENTITY,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_LEAD_ORG + s.VOL_LEAD_PAY ELSE 0 END) AS LEAD_TOT_26,
            SUM(CASE WHEN s.EXERCICE = '2024' THEN s.VOL_LEAD_ORG + s.VOL_LEAD_PAY ELSE 0 END) AS LEAD_TOT_24,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_EFF * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS ELSE 0 END) AS CA_26
        FROM AW_002_000002_000001 s
        GROUP BY s.SCENARIO, s.PERIODE, s.ENTITY
    ) sm ON sm.ENTITY = cp.ENTITY AND sm.SCENARIO = cp.SCENARIO AND sm.PERIODE = cp.PERIODE
) n
