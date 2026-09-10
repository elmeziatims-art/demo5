-- =============================================================================
-- V_CADRAGE_LEVIERS_CASCADE — les leviers RESOLUS PAR CAMPUS  (SQL Server)
--
-- A QUOI CA SERT. Le cadrage du CFO se saisit au grain GRP. Un directeur de
-- campus qui challenge ecrit le MEME parametre avec ENTITY = son campus. Cette
-- vue tranche : pour chaque campus et chaque version, elle prend la valeur du
-- campus si elle existe, sinon celle de la marque, sinon celle du groupe.
--
--     campus  ->  marque (<MARQUE>_REF)  ->  GRP
--
-- Un campus qui ne challenge pas herite du cadrage sans qu'on ait rien a faire.
--
-- ELLE NE TOUCHE A RIEN. V_CADRAGE_LEVIERS filtre ENTITY = 'GRP' : les lignes
-- campus lui sont invisibles, et la chaine actuelle continue de tourner a
-- l'identique. Le challenge est purement additif.
--
-- LA SOMME, JAMAIS LE DERNIER. La table stocke des deformations
-- (PROVENIENZA = INPUT_DEFORM) : une meme cle porte plusieurs lignes et la
-- valeur du levier est LEUR SOMME. HYP_PRICE V01 = 0,0200 puis -0,0171 = 0,0029.
-- Un MAX ou un TOP 1 rendrait 0,0200, sept fois trop, sans erreur a l'ecran.
--
-- LE PERIMETRE VIENT DU SOCLE, pas du cube d'hypotheses : la cascade ne cree
-- jamais un campus, elle ne fait que resoudre ceux qui existent.
-- =============================================================================
CREATE OR ALTER VIEW V_CADRAGE_LEVIERS_CASCADE AS
WITH
ent AS (   -- les campus reels, et leur marque
    SELECT DISTINCT s.SCENARIO, s.PERIODE, s.ENTITY,
           SUBSTR_BEFORE(s.ENTITY, '_') AS MARQUE
    FROM   AW_002_000002_000001 s
    WHERE  s.EXERCICE = '2026'
),
ver AS (
    SELECT DISTINCT VERSION FROM V_CADRAGE_LEVIERS
    WHERE  VERSION IN ('V01', 'V02', 'V03')
),
par AS (   -- les onze leviers versionnes ; le coefficient prix est a part
    SELECT DISTINCT t.PARAMETRE
    FROM   AW_002_000001_000001 t
    WHERE  t.PARAMETRE LIKE 'HYP[_]%' AND t.PARAMETRE <> 'HYP_PRICE_COEF'
),
sai AS (   -- toute saisie, a n'importe quelle maille, SOMMEE
    SELECT t.SCENARIO, t.PERIODE, t.VERSION, t.ENTITY, t.PARAMETRE,
           SUM(t.MEASURE) AS VALEUR
    FROM   AW_002_000001_000001 t
    WHERE  t.PARAMETRE LIKE 'HYP[_]%' AND t.PARAMETRE <> 'HYP_PRICE_COEF'
    GROUP BY t.SCENARIO, t.PERIODE, t.VERSION, t.ENTITY, t.PARAMETRE
),
res AS (   -- la cascade, un parametre a la fois
    SELECT e.SCENARIO, e.PERIODE, v.VERSION, e.ENTITY, e.MARQUE, p.PARAMETRE,
           COALESCE(sc.VALEUR, sm.VALEUR, sg.VALEUR) AS VALEUR,
           CASE WHEN sc.VALEUR IS NOT NULL THEN 'CAMPUS'
                WHEN sm.VALEUR IS NOT NULL THEN 'MARQUE'
                WHEN sg.VALEUR IS NOT NULL THEN 'GROUPE'
                ELSE 'DEFAUT' END                    AS ORIGINE
    FROM ent e
    CROSS JOIN ver v
    CROSS JOIN par p
    LEFT JOIN sai sc ON sc.SCENARIO  = e.SCENARIO AND sc.PERIODE = e.PERIODE
                    AND sc.VERSION   = v.VERSION  AND sc.PARAMETRE = p.PARAMETRE
                    AND sc.ENTITY    = e.ENTITY
    LEFT JOIN sai sm ON sm.SCENARIO  = e.SCENARIO AND sm.PERIODE = e.PERIODE
                    AND sm.VERSION   = v.VERSION  AND sm.PARAMETRE = p.PARAMETRE
                    AND sm.ENTITY    = e.MARQUE + '_REF'
    LEFT JOIN sai sg ON sg.SCENARIO  = e.SCENARIO AND sg.PERIODE = e.PERIODE
                    AND sg.VERSION   = v.VERSION  AND sg.PARAMETRE = p.PARAMETRE
                    AND sg.ENTITY    = 'GRP'
)
SELECT
    r.SCENARIO, r.PERIODE, r.VERSION, r.ENTITY, r.MARQUE,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_ACQ_BUD'       THEN r.VALEUR END) AS LEV_ACQ_BUD,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_BRAND_BUD'     THEN r.VALEUR END) AS LEV_BRAND_BUD,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_PRICE'         THEN r.VALEUR END) AS LEV_PRICE,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_CNV_LEAD_CAND' THEN r.VALEUR END) AS LEV_CNV_LEAD_CAND,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_CNV_ADM_INS'   THEN r.VALEUR END) AS LEV_CNV_ADM_INS,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_PASS_RATE'     THEN r.VALEUR END) AS LEV_PASS_RATE,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_INFL_EXT'      THEN r.VALEUR END) AS LEV_INFL_EXT,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_SALARY'        THEN r.VALEUR END) AS LEV_SALARY,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_FTE_PERM'      THEN r.VALEUR END) AS LEV_FTE_PERM,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_PRODUCTIVITY'  THEN r.VALEUR END) AS LEV_PRODUCTIVITY,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_STRUCT_COST'   THEN r.VALEUR END) AS LEV_STRUCT_COST,
    MAX(CASE WHEN r.PARAMETRE = 'HYP_FILE_FEE'      THEN r.VALEUR END) AS FILE_FEE,
    --  combien de leviers ce campus a-t-il repris a son compte
    SUM(CASE WHEN r.ORIGINE = 'CAMPUS' THEN 1 ELSE 0 END)              AS NB_CHALLENGE
FROM res r
GROUP BY r.SCENARIO, r.PERIODE, r.VERSION, r.ENTITY, r.MARQUE;
