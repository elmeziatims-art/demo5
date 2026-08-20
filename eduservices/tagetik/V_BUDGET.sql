-- =============================================================================
-- VUE V_BUDGET — EBITDA CONSTRUIT 2027 (par entité x version)  (SAP HANA)
-- Revenus  : CA construit du moteur (V_MOTEUR), agrégé par entité.
-- Coûts    : compta 2026 (AW_002_000004_000001) projetée par les leviers de coût
--            (V_CADRAGE_LEVIERS), même mapping SIG que V_PNL.
-- Facteurs (repris de la logique modèle) :
--   6231 (mkt acquisition)  x (1 + ACQ_BUD)          -> reste en Coûts directs
--   6236 (mkt marque)       x (1 + BRAND_BUD)         -> reste en Structure
--   autres directs          x CAF x (1 - PRODUCTIVITY)   (CAF = volume groupe)
--   personnel               x (1 + SALARY) x (1 + FTE_PERM)
--   structure (hors 6236)   x (1 + INFL_EXT) x (1 - PRODUCTIVITY) x (1 + STRUCT_COST)
--   impôts & taxes          x (1 + INFL_EXT) x (1 - PRODUCTIVITY)
--   dotations               x (1 + INFL_EXT)
-- GRP (siège) : produits = 0, coûts projetés (personnel 6414, 6226, 6236, taxes…).
-- Grain sortie : ENTITY x VERSION, EXERCICE = '2027'. Colonnes = postes SIG,
--                identiques à V_PNL -> UNION directe.
-- Tie-out V01 (Σ entités) : Produits 24 120 981 · EBITDA 3 875 895 (16,1%) · EBIT 2 496 158
-- =============================================================================
CREATE OR REPLACE VIEW V_BUDGET AS
WITH
lev AS (
    SELECT VERSION,
        COALESCE(LEV_ACQ_BUD,0)     AS ACQ,   COALESCE(LEV_BRAND_BUD,0)   AS BRAND,
        COALESCE(LEV_INFL_EXT,0)    AS INFL,  COALESCE(LEV_SALARY,0)      AS SAL,
        COALESCE(LEV_FTE_PERM,0)    AS FTE,   COALESCE(LEV_PRODUCTIVITY,0) AS PROD,
        COALESCE(LEV_STRUCT_COST,0) AS STRUCT
    FROM V_CADRAGE_LEVIERS
    WHERE VERSION IN ('V01','V02','V03')
),
cpt AS (   -- compta 2026 ventilée par nature (6231 et 6236 isolés pour leurs leviers)
    SELECT ENTITY,
        SUM(CASE WHEN ACCOUNT IN ('7062','706','708')                        THEN AMOUNT ELSE 0 END) AS PRODUITS,
        SUM(CASE WHEN ACCOUNT IN ('621','604','6063')                        THEN AMOUNT ELSE 0 END) AS DIRECTS_AUTRES,
        SUM(CASE WHEN ACCOUNT = '6231'                                       THEN AMOUNT ELSE 0 END) AS MKT_ACQ,
        SUM(CASE WHEN ACCOUNT = '6236'                                       THEN AMOUNT ELSE 0 END) AS MKT_BRAND,
        SUM(CASE WHEN ACCOUNT IN ('6411','6413','6414','645')                THEN AMOUNT ELSE 0 END) AS PERSONNEL,
        SUM(CASE WHEN ACCOUNT IN ('613','615','616','6226','625','626','6281') THEN AMOUNT ELSE 0 END) AS STRUCTURE_AUTRES,
        SUM(CASE WHEN ACCOUNT IN ('6331','63511','6333')                     THEN AMOUNT ELSE 0 END) AS IMPOTS,
        SUM(CASE WHEN ACCOUNT = '6811'                                       THEN AMOUNT ELSE 0 END) AS DOTATIONS
    FROM AW_002_000004_000001
    WHERE EXERCICE = '2026'
    GROUP BY ENTITY
),
mot AS (   -- CA + effectif construits 2027 par entité et version (agrégé du moteur)
    SELECT ENTITY, VERSION, SUM(CA) AS CA_2027, SUM(EFFECTIF) AS EFF_2027
    FROM V_MOTEUR
    GROUP BY ENTITY, VERSION
),
caf AS (   -- facteur volume groupe par version = Σ CA moteur / Σ produits 2026
    SELECT m.VERSION, SUM(m.CA_2027) / NULLIF(g.TOT_PROD,0) AS CAF
    FROM mot m CROSS JOIN (SELECT SUM(PRODUITS) AS TOT_PROD FROM cpt) g
    GROUP BY m.VERSION, g.TOT_PROD
)
SELECT
    c.ENTITY,
    '2027'        AS EXERCICE,
    l.VERSION,
    '2027BUD_V1'  AS SCENARIO,
    '12'          AS PERIOD,   -- texte : PERIOD est une dimension caractère, pas un nombre
    COALESCE(m.CA_2027,0)                                                                       AS SIG_PRODUITS,
    COALESCE(m.EFF_2027,0)                                                                       AS EFFECTIF,
    (c.DIRECTS_AUTRES * f.CAF * (1 - l.PROD) + c.MKT_ACQ * (1 + l.ACQ))                          AS C_DIRECTS,
    (c.PERSONNEL * (1 + l.SAL) * (1 + l.FTE))                                                    AS C_PERSONNEL,
    (c.STRUCTURE_AUTRES * (1 + l.INFL) * (1 - l.PROD) * (1 + l.STRUCT) + c.MKT_BRAND * (1 + l.BRAND)) AS C_STRUCTURE,
    (c.IMPOTS * (1 + l.INFL) * (1 - l.PROD))                                                     AS C_IMPOTS,
    (c.DOTATIONS * (1 + l.INFL))                                                                 AS C_DOTATIONS
FROM cpt c
CROSS JOIN lev l
LEFT JOIN mot m ON m.ENTITY = c.ENTITY AND m.VERSION = l.VERSION
JOIN caf f      ON f.VERSION = l.VERSION;
