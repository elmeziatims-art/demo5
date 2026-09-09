-- =============================================================================
-- VUE V_BUDGET — BUDGET 2027 CONSTRUIT, AU GRAIN COMPTE  (SQL Server / T-SQL)
-- Sortie : 1 ligne par ENTITY x ACCOUNT x VERSION (EXERCICE='2027'), 1 mesure AMOUNT.
-- => MÊME forme que la compta (AW_002_000004_000001). C'est la hiérarchie de la
--    dimension Compte, DANS TAGETIK, qui agrège Produits -> Marge -> EBITDA -> EBIT.
--    (aucune agrégation SIG en dur ici)
-- Projection 2026 -> 2027 par compte (leviers de V_CADRAGE_LEVIERS) :
--   produits (7062,706,708)        x CAF                (CAF = CA moteur / produits 2026,
--                                                        PAR ENTITE depuis la correction)
--   6231 mkt acquisition           x (1 + ACQ_BUD)
--   6236 mkt marque                x (1 + BRAND_BUD)
--   autres directs (621,604,6063)  x CAF x (1 - PRODUCTIVITY)
--   personnel (6411,6413,6414,645) x (1 + SALARY) x (1 + FTE_PERM)
--   structure (613..6281 hors 6236) x (1 + INFL) x (1 - PROD) x (1 + STRUCT)
--   impôts (6331,63511,6333)       x (1 + INFL) x (1 - PROD)
--   dotations (6811)               x (1 + INFL)
-- Montants POSITIFS (comme la compta ; le sens produit/charge est porté par le compte).
-- Tie-out V01 (Σ) : Produits 24 120 981 · EBITDA 3 875 895 (16,1%).
-- =============================================================================
CREATE OR ALTER VIEW V_BUDGET AS
WITH
lev AS (
    SELECT VERSION,
        COALESCE(LEV_ACQ_BUD,0)     AS ACQ,   COALESCE(LEV_BRAND_BUD,0)    AS BRAND,
        COALESCE(LEV_INFL_EXT,0)    AS INFL,  COALESCE(LEV_SALARY,0)       AS SAL,
        COALESCE(LEV_FTE_PERM,0)    AS FTE,   COALESCE(LEV_PRODUCTIVITY,0) AS PROD,
        COALESCE(LEV_STRUCT_COST,0) AS STRUCT
    FROM V_CADRAGE_LEVIERS
    WHERE VERSION IN ('V01','V02','V03')
),
cpt AS (   -- compta 2026 au grain compte
    SELECT ENTITY, ACCOUNT, SUM(AMOUNT) AS AMOUNT
    FROM AW_002_000004_000001
    WHERE EXERCICE = '2026'
    GROUP BY ENTITY, ACCOUNT
),
caf_grp AS (   -- garde-fou : le facteur groupe, pour les entites sans produits (GRP)
    SELECT mv.VERSION, 1.0 * mv.CA_2027 / NULLIF(gp.TOT_PROD,0) AS CAF
    FROM (SELECT VERSION, SUM(CA) AS CA_2027 FROM V_MOTEUR GROUP BY VERSION) mv
    CROSS JOIN (
        SELECT SUM(AMOUNT) AS TOT_PROD FROM AW_002_000004_000001
        WHERE EXERCICE='2026' AND ACCOUNT IN ('7062','706','708')
    ) gp
),
caf_ent AS (   -- LE FACTEUR DE CHAQUE CAMPUS : son moteur sur sa propre compta 2026.
               -- Avant, un facteur unique etait applique aux quatorze : la ventilation
               -- 2027 etait donc celle de 2026, et un ajustement local se diluait sur
               -- tout le reseau. Le total groupe ne bouge pas -- la somme des
               -- compta26 x (moteur/compta26) vaut la somme des moteurs, soit ce que
               -- rendait deja le facteur groupe -- seule la repartition se corrige.
    SELECT mv.ENTITY, mv.VERSION, 1.0 * mv.CA_2027 / NULLIF(gp.PROD_2026,0) AS CAF
    FROM (SELECT ENTITY, VERSION, SUM(CA) AS CA_2027 FROM V_MOTEUR
          GROUP BY ENTITY, VERSION) mv
    JOIN (SELECT ENTITY, SUM(AMOUNT) AS PROD_2026 FROM AW_002_000004_000001
          WHERE EXERCICE='2026' AND ACCOUNT IN ('7062','706','708')
          GROUP BY ENTITY) gp ON gp.ENTITY = mv.ENTITY
)
SELECT
    c.ENTITY,
    c.ACCOUNT,
    '2027'                     AS EXERCICE,
    l.VERSION,
    '2027BUD_V1'               AS SCENARIO,
    CAST('12' AS NVARCHAR(10)) AS PERIOD,
    CASE
        WHEN c.ACCOUNT IN ('7062','706','708')                          THEN c.AMOUNT * COALESCE(fe.CAF, fg.CAF)
        WHEN c.ACCOUNT = '6231'                                         THEN c.AMOUNT * (1 + l.ACQ)
        WHEN c.ACCOUNT = '6236'                                         THEN c.AMOUNT * (1 + l.BRAND)
        WHEN c.ACCOUNT IN ('621','604','6063')                          THEN c.AMOUNT * COALESCE(fe.CAF, fg.CAF) * (1 - l.PROD)
        WHEN c.ACCOUNT IN ('6411','6413','6414','645')                  THEN c.AMOUNT * (1 + l.SAL) * (1 + l.FTE)
        WHEN c.ACCOUNT IN ('613','615','616','6226','625','626','6281') THEN c.AMOUNT * (1 + l.INFL) * (1 - l.PROD) * (1 + l.STRUCT)
        WHEN c.ACCOUNT IN ('6331','63511','6333')                       THEN c.AMOUNT * (1 + l.INFL) * (1 - l.PROD)
        WHEN c.ACCOUNT = '6811'                                         THEN c.AMOUNT * (1 + l.INFL)
        ELSE c.AMOUNT
    END AS AMOUNT
FROM cpt c
CROSS JOIN lev l
LEFT JOIN caf_ent fe ON fe.VERSION = l.VERSION AND fe.ENTITY = c.ENTITY
JOIN      caf_grp fg ON fg.VERSION = l.VERSION;
