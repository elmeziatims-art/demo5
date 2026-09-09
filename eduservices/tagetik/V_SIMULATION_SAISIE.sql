-- =============================================================================
-- V_SIMULATION_SAISIE — la simulation d'ouverture / fermeture, côté serveur
-- SQL Server. Rejoue EXACTEMENT l'arithmétique du masque SIMULATION_CLASSES.xlsx,
-- mais à partir de ce que le directeur de campus a SAISI dans Tagetik.
--
-- OÙ SE SAISIT LA DÉCISION. Dans le cube d'hypothèses AW_002_000001_000001,
-- qui porte déjà une colonne libre KEY_ALLOC. La classe y tient entière :
--
--   PARAMETRE      ENTITY      KEY_ALLOC              MEASURE
--   SIM_DGROUPES   MBWAY_PAR   MAS_MGT|M1|ALT         +1     un groupe de plus
--   SIM_DGROUPES   PIGIER_BOR  BAC_RH|B2|ALT          -1     un groupe de moins
--   SIM_DELEVES    MBWAY_PAR   BAC_MGT|B2|ALT         12     douze inscrits achetés
--   SIM_ECO_PERM   PIGIER_BOR  (vide)                 0,30   30 % des permanents
--   SIM_ECO_STRUCT PIGIER_BOR  (vide)                 0,00   rien sur la structure
--
-- POURQUOI C'EST SANS RISQUE. Les cinq lecteurs du cube filtrent déjà :
-- V_CADRAGE_LEVIERS et Q_HYPOTHESES sur ENTITY='GRP', V_MOTEUR sur
-- PARAMETRE='HYP_PRICE_COEF', V_ALLOCATION et DIAG_COCKPIT_VIDE sur
-- PARAMETRE LIKE 'ALLOC_%'. Aucun ne voit ces lignes. Le cadrage reste intact,
-- et la simulation se lit à côté — c'est bien une simulation, pas un budget.
--
-- Le cube stocke des DÉFORMATIONS (PROVENIENZA = INPUT_DEFORM) : la valeur d'un
-- paramètre est la SOMME de ses lignes. D'où le SUM, et pas un MAX.
-- =============================================================================
CREATE OR ALTER VIEW V_SIMULATION_SAISIE AS
WITH
sai AS (          -- la décision, au grain campus x classe
    SELECT SCENARIO, VERSION, ENTITY, KEY_ALLOC,
        SUM(CASE WHEN PARAMETRE = 'SIM_DGROUPES' THEN MEASURE ELSE 0 END) AS D_GROUPES,
        SUM(CASE WHEN PARAMETRE = 'SIM_DELEVES'  THEN MEASURE ELSE 0 END) AS D_ELEVES
    FROM AW_002_000001_000001
    WHERE PARAMETRE IN ('SIM_DGROUPES', 'SIM_DELEVES')
    GROUP BY SCENARIO, VERSION, ENTITY, KEY_ALLOC
),
eco AS (          -- les deux curseurs de récupération, au grain campus
    SELECT SCENARIO, VERSION, ENTITY,
        SUM(CASE WHEN PARAMETRE = 'SIM_ECO_PERM'   THEN MEASURE ELSE 0 END) AS ECO_PERM,
        SUM(CASE WHEN PARAMETRE = 'SIM_ECO_STRUCT' THEN MEASURE ELSE 0 END) AS ECO_STRUCT
    FROM AW_002_000001_000001
    WHERE PARAMETRE IN ('SIM_ECO_PERM', 'SIM_ECO_STRUCT')
    GROUP BY SCENARIO, VERSION, ENTITY
),
b AS (
    SELECT s.SCENARIO, s.VERSION, s.PERIODE, s.EXERCICE, s.ENTITY, s.MARQUE,
        s.PROGRAMME, s.AN_ETUDE, s.MODALITE, s.IS_ENTREE,
        s.GROUPES, s.CAPACITE, s.PLACES, s.EFFECTIF, s.CA, s.COST_STRUCT,
        s.VAC_GROUPE, s.PERM_GROUPE, s.CONSO_ELEVE, s.CAC_MARGINAL, s.MARGE_COMPLETE,
        COALESCE(sa.D_GROUPES, 0) AS D_GROUPES, COALESCE(sa.D_ELEVES, 0) AS D_ELEVES,
        COALESCE(e.ECO_PERM, 0)   AS ECO_PERM,  COALESCE(e.ECO_STRUCT, 0) AS ECO_STRUCT,
        --  ce que les places d'aujourd'hui permettent réellement de livrer
        CASE WHEN s.EFFECTIF < s.PLACES THEN s.EFFECTIF ELSE s.PLACES END AS EFF_PLACABLE
    FROM V_SIMULATION_CLASSES s
    LEFT JOIN sai sa ON sa.SCENARIO = s.SCENARIO AND sa.VERSION = s.VERSION
                    AND sa.ENTITY   = s.ENTITY
                    AND sa.KEY_ALLOC = s.PROGRAMME + '|' + s.AN_ETUDE + '|' + s.MODALITE
    LEFT JOIN eco e   ON e.SCENARIO  = s.SCENARIO AND e.VERSION  = s.VERSION
                    AND e.ENTITY    = s.ENTITY
),
c AS (
    SELECT b.*,
        (b.GROUPES + b.D_GROUPES) * b.CAPACITE AS PLACES_APRES,
        CASE WHEN b.EFFECTIF + b.D_ELEVES < (b.GROUPES + b.D_GROUPES) * b.CAPACITE
             THEN b.EFFECTIF + b.D_ELEVES
             ELSE (b.GROUPES + b.D_GROUPES) * b.CAPACITE END AS EFF_RETENU,
        --  la demande déjà présente qui trouve une place après décision : elle ne
        --  s'achète pas, elle était dans l'entonnoir. Seul le delta au-dessus coûte.
        CASE WHEN b.EFFECTIF < (b.GROUPES + b.D_GROUPES) * b.CAPACITE
             THEN b.EFFECTIF
             ELSE (b.GROUPES + b.D_GROUPES) * b.CAPACITE END AS EFF_SANS_ACHAT
    FROM b
),
d AS (
    SELECT c.*,
        (c.EFF_RETENU - c.EFF_PLACABLE) * c.CA / NULLIF(c.EFFECTIF, 0)  AS DELTA_CA,
        c.D_GROUPES * c.VAC_GROUPE                                      AS DELTA_VACATAIRES,
        (c.EFF_RETENU - c.EFF_PLACABLE) * c.CONSO_ELEVE                 AS DELTA_CONSO,
        CASE WHEN c.EFF_RETENU > c.EFF_SANS_ACHAT
             THEN (c.EFF_RETENU - c.EFF_SANS_ACHAT) * c.CAC_MARGINAL ELSE 0 END AS COUT_ACQUISITION,
        CASE WHEN c.D_GROUPES < 0
             THEN -c.D_GROUPES * c.PERM_GROUPE * c.ECO_PERM ELSE 0 END  AS ECONOMIE_PERM,
        CASE WHEN c.D_GROUPES < 0
             THEN -c.D_GROUPES * c.COST_STRUCT / NULLIF(c.GROUPES, 0) * c.ECO_STRUCT
             ELSE 0 END                                                 AS ECONOMIE_STRUCT,
        --  ce que le cadrage a construit sans place pour l'accueillir
        (c.EFF_PLACABLE - c.EFFECTIF) * c.CA / NULLIF(c.EFFECTIF, 0)
          - (c.EFF_PLACABLE - c.EFFECTIF) * c.CONSO_ELEVE               AS EBITDA_NON_LIVRABLE
    FROM c
)
SELECT
    d.SCENARIO, d.VERSION, d.PERIODE, d.EXERCICE, d.ENTITY, d.MARQUE,
    d.PROGRAMME, d.AN_ETUDE, d.MODALITE, d.IS_ENTREE,
    d.GROUPES, d.D_GROUPES, (d.GROUPES + d.D_GROUPES) AS GROUPES_APRES,
    d.CAPACITE, d.PLACES, d.PLACES_APRES,
    d.EFFECTIF, d.EFF_PLACABLE, d.D_ELEVES, d.EFF_RETENU,
    d.CA, d.MARGE_COMPLETE, d.EBITDA_NON_LIVRABLE,
    d.DELTA_CA, d.DELTA_VACATAIRES, d.DELTA_CONSO, d.COUT_ACQUISITION,
    d.ECONOMIE_PERM, d.ECONOMIE_STRUCT,
    (d.DELTA_VACATAIRES + d.DELTA_CONSO + d.COUT_ACQUISITION
     - d.ECONOMIE_PERM - d.ECONOMIE_STRUCT)                             AS DELTA_COUT,
    (d.DELTA_CA - (d.DELTA_VACATAIRES + d.DELTA_CONSO + d.COUT_ACQUISITION
                   - d.ECONOMIE_PERM - d.ECONOMIE_STRUCT))              AS DELTA_EBITDA
FROM d
