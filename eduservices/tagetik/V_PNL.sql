-- =============================================================================
-- VUE P&L / EBITDA — EDUSERVICES  (SAP HANA)
-- Source : AW_002_000004_000001 (compta)   colonnes : ENTITY, ACCOUNT, EXERCICE,
--          SCENARIO, PERIOD, AMOUNT (montants POSITIFS en entrée ; le sens est
--          porté par le COMPTE, mappé en CASE ci-dessous).
-- Grain de sortie : ENTITY x EXERCICE (x SCENARIO x PERIOD).
-- Multi-exercice : un seul SCENARIO (2027BUD_V1), plusieurs EXERCICE (2024..2026).
--          -> la croissance/Δ se calcule d'un EXERCICE à l'autre (LAG).
-- Cascade  : Produits - Directs = MARGE CONTRIB
--            - Personnel - Structure - Impôts = EBITDA
--            - Dotations = EBIT
-- Tie-out (Σ entités) vérifié :
--   2024  Produits 20 064 725  EBITDA 2 648 550 (13,2%)  EBIT 1 444 664
--   2025  Produits 21 268 606  EBITDA 2 977 604 (14,0%)  EBIT 1 701 489
--   2026  Produits 22 544 725  EBITDA 3 291 530 (14,6%)  EBIT 1 938 847
--   (0 compte non mappé)
-- Note : le budget 2027 (construit) n'est PAS dans la compta -> il viendra de
--        V_BUDGET (moteur + leviers de coûts) et pourra s'UNIONner ici ensuite.
-- =============================================================================
CREATE OR REPLACE VIEW V_PNL AS
SELECT
    m.ENTITY, m.EXERCICE, m.SCENARIO, m.PERIOD,
    -- soldes intermédiaires de gestion
    m.SIG_PRODUITS,
    m.C_DIRECTS, m.C_PERSONNEL, m.C_STRUCTURE, m.C_IMPOTS, m.C_DOTATIONS,
    m.MARGE_CONTRIB,
    m.EBITDA,
    m.EBIT,
    -- ratios
    COALESCE(m.MARGE_CONTRIB / NULLIF(m.SIG_PRODUITS, 0), 0) AS MARGE_CONTRIB_PCT,
    COALESCE(m.EBITDA        / NULLIF(m.SIG_PRODUITS, 0), 0) AS MARGE_EBITDA_PCT,
    COALESCE(m.EBIT          / NULLIF(m.SIG_PRODUITS, 0), 0) AS MARGE_EBIT_PCT,
    -- évolution d'un exercice à l'autre (même scénario)
    COALESCE(
        m.SIG_PRODUITS
        / NULLIF(LAG(m.SIG_PRODUITS) OVER (PARTITION BY m.ENTITY, m.SCENARIO
                                           ORDER BY TO_INTEGER(m.EXERCICE)), 0) - 1,
        0)                                                  AS TX_CROISSANCE_CA,
    m.EBITDA - LAG(m.EBITDA) OVER (PARTITION BY m.ENTITY, m.SCENARIO
                                   ORDER BY TO_INTEGER(m.EXERCICE))
                                                            AS DELTA_EBITDA
FROM (
    SELECT
        s.ENTITY, s.EXERCICE, s.SCENARIO, s.PERIOD,
        s.SIG_PRODUITS, s.C_DIRECTS, s.C_PERSONNEL, s.C_STRUCTURE, s.C_IMPOTS, s.C_DOTATIONS,
        (s.SIG_PRODUITS - s.C_DIRECTS)                                                        AS MARGE_CONTRIB,
        (s.SIG_PRODUITS - s.C_DIRECTS - s.C_PERSONNEL - s.C_STRUCTURE - s.C_IMPOTS)            AS EBITDA,
        (s.SIG_PRODUITS - s.C_DIRECTS - s.C_PERSONNEL - s.C_STRUCTURE - s.C_IMPOTS - s.C_DOTATIONS) AS EBIT
    FROM (
        SELECT
            t.ENTITY, t.EXERCICE, t.SCENARIO, t.PERIOD,
            SUM(CASE WHEN t.ACCOUNT IN ('7062','706','708')                              THEN t.AMOUNT ELSE 0 END) AS SIG_PRODUITS,
            SUM(CASE WHEN t.ACCOUNT IN ('621','604','6063','6231')                       THEN t.AMOUNT ELSE 0 END) AS C_DIRECTS,
            SUM(CASE WHEN t.ACCOUNT IN ('6411','6413','6414','645')                      THEN t.AMOUNT ELSE 0 END) AS C_PERSONNEL,
            SUM(CASE WHEN t.ACCOUNT IN ('613','615','616','6226','6236','625','626','6281') THEN t.AMOUNT ELSE 0 END) AS C_STRUCTURE,
            SUM(CASE WHEN t.ACCOUNT IN ('6331','63511','6333')                           THEN t.AMOUNT ELSE 0 END) AS C_IMPOTS,
            SUM(CASE WHEN t.ACCOUNT IN ('6811')                                          THEN t.AMOUNT ELSE 0 END) AS C_DOTATIONS
        FROM AW_002_000004_000001 t
        GROUP BY t.ENTITY, t.EXERCICE, t.SCENARIO, t.PERIOD
    ) s
) m;
