-- =============================================================================
-- VUE P&L / EBITDA — EDUSERVICES  (corps CREATE OR REPLACE VIEW V_PNL AS
SELECT ; SAP HANA)
-- Source : AW_002_000004_000001 (compta)
-- Le sens (Produit/Charge) et le SIG sont des attributs du COMPTE → mappés en CASE.
-- Grain : ENTITY x EXERCICE (x SCENARIO x PERIOD).  Montants positifs en entrée.
-- Contrôles 2026 (Σ entités) : Produits 22 544 725 · EBITDA 3 291 530 (14,6%) · EBIT 1 938 847
-- =============================================================================
SELECT
    s.ENTITY, s.EXERCICE, s.SCENARIO, s.PERIOD,
    s.SIG_PRODUITS,
    s.C_DIRECTS, s.C_PERSONNEL, s.C_STRUCTURE, s.C_IMPOTS, s.C_DOTATIONS,
    (s.SIG_PRODUITS - s.C_DIRECTS)                                              AS MARGE_CONTRIB,
    (s.SIG_PRODUITS - s.C_DIRECTS - s.C_PERSONNEL - s.C_STRUCTURE - s.C_IMPOTS) AS EBITDA,
    (s.SIG_PRODUITS - s.C_DIRECTS - s.C_PERSONNEL - s.C_STRUCTURE - s.C_IMPOTS - s.C_DOTATIONS) AS EBIT
FROM (
    SELECT
        t.ENTITY, t.EXERCICE, t.SCENARIO, t.PERIOD,
        SUM(CASE WHEN t.ACCOUNT IN ('7062','706','708')                THEN t.AMOUNT ELSE 0 END) AS SIG_PRODUITS,
        SUM(CASE WHEN t.ACCOUNT IN ('621','604','6063','6231')         THEN t.AMOUNT ELSE 0 END) AS C_DIRECTS,
        SUM(CASE WHEN t.ACCOUNT IN ('6411','6413','6414','645')        THEN t.AMOUNT ELSE 0 END) AS C_PERSONNEL,
        SUM(CASE WHEN t.ACCOUNT IN ('613','615','616','6226','6236','625','626','6281') THEN t.AMOUNT ELSE 0 END) AS C_STRUCTURE,
        SUM(CASE WHEN t.ACCOUNT IN ('6331','63511','6333')             THEN t.AMOUNT ELSE 0 END) AS C_IMPOTS,
        SUM(CASE WHEN t.ACCOUNT IN ('6811')                            THEN t.AMOUNT ELSE 0 END) AS C_DOTATIONS
    FROM AW_002_000004_000001 t
    GROUP BY t.ENTITY, t.EXERCICE, t.SCENARIO, t.PERIOD
) s
