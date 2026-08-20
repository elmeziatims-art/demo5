-- =============================================================================
-- VUE P&L / EBITDA UNIFIÉE — EDUSERVICES  (SAP HANA)
-- TOUS les exercices dans une seule vue :
--   • RÉEL   2024-2026  ← compta AW_002_000004_000001  + effectif socle AW_002_000002_000001  (VERSION='ACT')
--   • BUDGET 2027       ← V_BUDGET (moteur + leviers)                                          (VERSION=V01/V02/V03)
-- Un seul SCENARIO (2027BUD_V1), plusieurs EXERCICE. PERIOD = dimension caractère.
-- Cascade : Produits - Directs = MARGE CONTRIB ; - Personnel - Structure - Impôts
--           = EBITDA ; - Dotations = EBIT.  + EFFECTIF et ratios /étudiant.
-- Tie-out (Σ entités) :
--   2024 ACT  EBITDA 2 648 550 (13,2%)  eff 2 704 | 2025 2 977 604 (14,0%)  eff 2 860
--   2026 ACT  EBITDA 3 291 530 (14,6%)  eff 3 036 | 2027 V01 3 875 895 (16,1%)  eff ~3 175
-- =============================================================================
CREATE OR REPLACE VIEW V_PNL AS
SELECT
    m.ENTITY, m.EXERCICE, m.VERSION, m.SCENARIO, m.PERIOD,
    m.SIG_PRODUITS, m.EFFECTIF,
    m.C_DIRECTS, m.C_PERSONNEL, m.C_STRUCTURE, m.C_IMPOTS, m.C_DOTATIONS,
    m.MARGE_CONTRIB, m.EBITDA, m.EBIT,
    COALESCE(m.MARGE_CONTRIB / NULLIF(m.SIG_PRODUITS,0), 0) AS MARGE_CONTRIB_PCT,
    COALESCE(m.EBITDA        / NULLIF(m.SIG_PRODUITS,0), 0) AS MARGE_EBITDA_PCT,
    COALESCE(m.EBIT          / NULLIF(m.SIG_PRODUITS,0), 0) AS MARGE_EBIT_PCT,
    COALESCE(m.SIG_PRODUITS  / NULLIF(m.EFFECTIF,0), 0)     AS CA_PAR_ETUDIANT,
    COALESCE(m.EBITDA        / NULLIF(m.EFFECTIF,0), 0)     AS EBITDA_PAR_ETUDIANT,
    -- croissance d'un exercice à l'autre au sein d'une même version (2027 = NULL -> restitution)
    COALESCE(
        m.SIG_PRODUITS
        / NULLIF(LAG(m.SIG_PRODUITS) OVER (PARTITION BY m.ENTITY, m.VERSION
                                           ORDER BY TO_INTEGER(m.EXERCICE)), 0) - 1, 0) AS TX_CROISSANCE_CA
FROM (
    SELECT
        u.ENTITY, u.EXERCICE, u.VERSION, u.SCENARIO, u.PERIOD,
        u.SIG_PRODUITS, u.EFFECTIF,
        u.C_DIRECTS, u.C_PERSONNEL, u.C_STRUCTURE, u.C_IMPOTS, u.C_DOTATIONS,
        (u.SIG_PRODUITS - u.C_DIRECTS)                                                             AS MARGE_CONTRIB,
        (u.SIG_PRODUITS - u.C_DIRECTS - u.C_PERSONNEL - u.C_STRUCTURE - u.C_IMPOTS)                 AS EBITDA,
        (u.SIG_PRODUITS - u.C_DIRECTS - u.C_PERSONNEL - u.C_STRUCTURE - u.C_IMPOTS - u.C_DOTATIONS) AS EBIT
    FROM (
        -- ===== RÉEL 2024-2026 : compta (SIG) + effectif socle =====
        SELECT
            p.ENTITY, p.EXERCICE, 'ACT' AS VERSION, p.SCENARIO, CAST(p.PERIOD AS NVARCHAR(10)) AS PERIOD,
            p.SIG_PRODUITS,
            COALESCE(e.EFFECTIF, 0) AS EFFECTIF,
            p.C_DIRECTS, p.C_PERSONNEL, p.C_STRUCTURE, p.C_IMPOTS, p.C_DOTATIONS
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
        ) p
        LEFT JOIN (
            SELECT ENTITY, EXERCICE, SUM(VOL_EFF) AS EFFECTIF
            FROM AW_002_000002_000001
            GROUP BY ENTITY, EXERCICE
        ) e ON e.ENTITY = p.ENTITY AND e.EXERCICE = p.EXERCICE

        UNION ALL

        -- ===== BUDGET 2027 (construit) =====
        SELECT
            b.ENTITY, b.EXERCICE, b.VERSION, b.SCENARIO, b.PERIOD,
            b.SIG_PRODUITS, b.EFFECTIF,
            b.C_DIRECTS, b.C_PERSONNEL, b.C_STRUCTURE, b.C_IMPOTS, b.C_DOTATIONS
        FROM V_BUDGET b
    ) u
) m;
