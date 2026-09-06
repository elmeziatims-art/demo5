-- =============================================================================
-- V_MOTEUR — CA construit 2027 (projection 2026 -> 2027), TOUTES versions — SQL Server
-- Appelle : V_CAMPAGNES (rendement, part org, volumes réf) · V_CAP (cap -> budget rejoué)
--           · V_CADRAGE_LEVIERS (leviers par version) · AW cadrage (coeff prix marque)
-- Logique : projette l'atterrissage 2026 avec les leviers de CHAQUE version (V01/V02/V03).
--   Entrées : leads = f(budget rejoué^rendement) -> funnel (rlc+ΔLC, rca, yld+ΔADM) -> nouveaux
--   Continuation : effectif = VOL_EFF_INF × (passage + Δpassage)   [cohorte]
--   Prix = REV_STUD × (1 + Δprix × coeff_marque) ; CA = effectif×prix + nouveaux×frais
-- Vérifié : V01 24 120 315 (+7,0%) · V02 26 307 244 (+16,7%) · V03 22 701 560 (+0,7%).
-- =============================================================================
CREATE OR ALTER VIEW V_MOTEUR AS
WITH
lev AS (
    SELECT VERSION,
        COALESCE(LEV_ACQ_BUD,0)       AS ACQ,   COALESCE(LEV_BRAND_BUD,0)     AS BRAND,
        COALESCE(LEV_PRICE,0)         AS PRICE, COALESCE(LEV_CNV_LEAD_CAND,0) AS GLC,
        COALESCE(LEV_CNV_ADM_INS,0)   AS GCV,   COALESCE(LEV_PASS_RATE,0)     AS PASS,
        COALESCE(FILE_FEE,90)         AS FEE
    FROM V_CADRAGE_LEVIERS WHERE VERSION IN ('V01','V02','V03')
),
pcoef AS (
    SELECT ENTITY, MEASURE AS PRICE_COEF FROM AW_002_000001_000001 WHERE PARAMETRE = 'HYP_PRICE_COEF'
),
cell AS (
    SELECT s.SCENARIO, s.PERIODE, s.ENTITY, SUBSTR_BEFORE(s.ENTITY,'_') AS MARQUE,
        s.PROGRAMME, s.AN_ETUDE, s.MODALITE, s.VOL_LEAD, s.VOL_EFF_INF, s.REV_STUD,
        CASE WHEN s.AN_ETUDE IN ('B1','M1','BTS1') THEN 1 ELSE 0 END        AS IS_ENTRY,
        COALESCE(1.0 * s.VOL_CAND / NULLIF(s.VOL_LEAD,   0), 0)                   AS RLC,
        COALESCE(1.0 * s.VOL_ADMIS / NULLIF(s.VOL_CAND,   0), 0)                   AS RCA,
        COALESCE(1.0 * s.VOL_NEW / NULLIF(s.VOL_ADMIS,  0), 0)                   AS YLD,
        COALESCE(1.0 * s.VOL_EFF / NULLIF(s.VOL_EFF_INF,0), 0)                   AS PASSAGE
    FROM AW_002_000002_000001 s WHERE s.EXERCICE = '2026'
)
SELECT
    f.SCENARIO, f.VERSION, f.PERIODE, f.ENTITY, f.MARQUE, f.PROGRAMME, f.AN_ETUDE, f.MODALITE,
    '2027' AS EXERCICE,
    f.NOUVEAUX, f.EFFECTIF, f.PRIX,
    (f.EFFECTIF * f.PRIX + f.NOUVEAUX * f.FEE) AS CA
FROM (
    SELECT e.*,
        CASE WHEN e.IS_ENTRY = 1 THEN e.NOUV_CALC ELSE 0 END                       AS NOUVEAUX,
        CASE WHEN e.IS_ENTRY = 1 THEN e.NOUV_CALC ELSE e.VOL_EFF_INF*(e.PASSAGE+e.PASS) END AS EFFECTIF,
        e.REV_STUD * (1 + e.PRICE * e.PRICE_COEF)                                  AS PRIX
    FROM (
        SELECT
            c.SCENARIO, l.VERSION, c.PERIODE, c.ENTITY, c.MARQUE, c.PROGRAMME, c.AN_ETUDE, c.MODALITE,
            c.VOL_EFF_INF, c.REV_STUD, c.IS_ENTRY, c.PASSAGE, l.PRICE, l.PASS, l.FEE,
            COALESCE(pc.PRICE_COEF, 1) AS PRICE_COEF,
            ( ( cm.ORG_REF  * POWER(1 + l.BRAND, cm.REND_BRAND)
              + cm.PAID_REF * POWER( (1.0 * cap.BUDGET_ACQ_REJOUE / NULLIF(cap.BUDGET_ACQ_REF,0)) * (1 + l.ACQ), cm.REND_ACQ) )
              * (1.0 * c.VOL_LEAD / NULLIF(cm.LEAD_REF, 0)) )
              * (c.RLC + l.GLC) * c.RCA * (c.YLD + l.GCV)                          AS NOUV_CALC
        FROM cell c
        CROSS JOIN lev l
        LEFT JOIN V_CAMPAGNES cm ON cm.ENTITY = c.ENTITY
        LEFT JOIN V_CAP       cap ON cap.ENTITY = c.ENTITY
        LEFT JOIN pcoef       pc  ON pc.ENTITY = c.MARQUE + '_REF'
    ) e
) f
