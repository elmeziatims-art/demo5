-- =============================================================================
-- V_MOTEUR_CHALLENGE — le moteur, mais leviers RESOLUS PAR CAMPUS
--
-- Jumeau de V_MOTEUR. Une seule difference, et c'est tout le sujet : les
-- leviers viennent de V_CADRAGE_LEVIERS_CASCADE au lieu de V_CADRAGE_LEVIERS,
-- donc chaque campus applique SES valeurs quand il en a saisi.
--
--   V_MOTEUR            leviers GRP           -> la proposition top-down
--   V_MOTEUR_CHALLENGE  cascade par campus    -> le budget apres ajustement
--
-- Tant qu'aucun campus n'a challenge, LES DEUX VUES RENDENT LE MEME CHIFFRE.
-- C'est le controle de non-regression : si elles different avant toute saisie,
-- la cascade est fausse.
--
-- Deux corrections au passage, absentes de V_MOTEUR :
--   le CROSS JOIN sur les leviers devient une jointure sur ENTITY -- sans quoi
--   chaque cellule serait multipliee par le nombre de campus ;
--   pcoef SOMME les deformations au lieu de lire une ligne brute. Aujourd'hui
--   il n'y a qu'une ligne par marque et ca passe ; le jour ou quelqu'un corrige
--   un coefficient, la version non sommee duplique.
-- =============================================================================
CREATE OR ALTER VIEW V_MOTEUR_CHALLENGE AS
WITH
lev AS (
    SELECT ENTITY, VERSION,
        COALESCE(LEV_ACQ_BUD,0)       AS ACQ,   COALESCE(LEV_BRAND_BUD,0)     AS BRAND,
        COALESCE(LEV_PRICE,0)         AS PRICE, COALESCE(LEV_CNV_LEAD_CAND,0) AS GLC,
        COALESCE(LEV_CNV_ADM_INS,0)   AS GCV,   COALESCE(LEV_PASS_RATE,0)     AS PASS,
        COALESCE(FILE_FEE,90)         AS FEE
    FROM V_CADRAGE_LEVIERS_CASCADE WHERE VERSION IN ('V01','V02','V03')
),
pcoef AS (
    SELECT ENTITY, SUM(MEASURE) AS PRICE_COEF
    FROM   AW_002_000001_000001 WHERE PARAMETRE = 'HYP_PRICE_COEF'
    GROUP BY ENTITY
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
        JOIN lev l ON l.ENTITY = c.ENTITY
        LEFT JOIN V_CAMPAGNES cm ON cm.ENTITY = c.ENTITY
        LEFT JOIN V_CAP       cap ON cap.ENTITY = c.ENTITY
        LEFT JOIN pcoef       pc  ON pc.ENTITY = c.MARQUE + '_REF'
    ) e
) f;
