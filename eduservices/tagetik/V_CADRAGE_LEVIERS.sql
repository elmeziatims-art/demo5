-- =============================================================================
-- VUE CADRAGE — LEVIERS DE GROUPE (pivot)  (corps SELECT ; SQL Server)
-- Source : AW_002_000001_000001 (cadrage)
-- Les leviers sont stockés en LONG (1 ligne = 1 PARAMETRE x VERSION) → on pivote
-- en 1 ligne par VERSION (V01/V02/V03…), colonnes = leviers. ENTITY = 'GRP'.
--
-- ⚠ IMPORTANT — la base est INCRÉMENTALE (saisie en delta, PROVENIENZA=INPUT_DEFORM) :
--   une modif d'un levier AJOUTE une ligne (le delta) au lieu de remplacer la valeur.
--   Ex. HYP_PRICE V01 : 0,020 (08-19) puis -0,0171 (08-31) → valeur réelle = 0,0029.
--   -> il faut SOMMER les lignes d'un même paramètre, PAS prendre le MAX
--      (MAX(0,020 ; -0,0171)=0,020 renverrait l'ancien prix et ignorerait la correction).
--   SUM(CASE …) est correct aussi quand il n'y a qu'une ligne (SUM d'un singleton = la valeur).
-- NB : le coefficient prix par marque (HYP_PRICE_COEF) est à un autre grain
--      (ENTITY = <marque>_REF, VERSION = GEN) → voir V_CADRAGE_PRICE_COEF plus bas.
-- =============================================================================
CREATE OR ALTER VIEW V_CADRAGE_LEVIERS AS
SELECT
    t.SCENARIO, t.PERIODE, t.VERSION,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_ACQ_BUD'       THEN t.MEASURE END) AS LEV_ACQ_BUD,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_BRAND_BUD'     THEN t.MEASURE END) AS LEV_BRAND_BUD,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_PRICE'         THEN t.MEASURE END) AS LEV_PRICE,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_CNV_LEAD_CAND' THEN t.MEASURE END) AS LEV_CNV_LEAD_CAND,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_CNV_ADM_INS'   THEN t.MEASURE END) AS LEV_CNV_ADM_INS,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_PASS_RATE'     THEN t.MEASURE END) AS LEV_PASS_RATE,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_INFL_EXT'      THEN t.MEASURE END) AS LEV_INFL_EXT,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_SALARY'        THEN t.MEASURE END) AS LEV_SALARY,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_FTE_PERM'      THEN t.MEASURE END) AS LEV_FTE_PERM,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_PRODUCTIVITY'  THEN t.MEASURE END) AS LEV_PRODUCTIVITY,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_STRUCT_COST'   THEN t.MEASURE END) AS LEV_STRUCT_COST,
    SUM(CASE WHEN t.PARAMETRE = 'HYP_FILE_FEE'      THEN t.MEASURE END) AS FILE_FEE
FROM AW_002_000001_000001 t
WHERE t.ENTITY = 'GRP'
GROUP BY t.SCENARIO, t.PERIODE, t.VERSION

-- --- V_CADRAGE_PRICE_COEF (coeff prix par marque) : à créer comme vue séparée ---
-- SELECT t.ENTITY, t.MEASURE AS PRICE_COEF
-- FROM AW_002_000001_000001 t
-- WHERE t.PARAMETRE = 'HYP_PRICE_COEF'
