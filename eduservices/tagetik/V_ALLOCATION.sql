-- =============================================================================
-- V_ALLOCATION — coût complet par CLASSE — SAP HANA
-- Sources : AW_002_000002_000001 (socle, drivers) + AW_002_000004_000001 (compta, charges)
-- Reproduit 10_Allocation, calculé à la volée, pour chaque EXERCICE :
--   - enseignement 621 vac -> variable / 6411 perm -> structure, réparti par HEURES (INITIAL>ALT)
--   - autres directs : 604+6063 par effectif, 6231 par entrants (-> variable)
--   - structure campus (loyer, admin, charges, assur, entretien, CFE) par classes
--   - siège (GRP) cascadé Groupe->Marque(CA) x Marque->Campus(effectif) x Campus->Classe(classes)
-- CONTROLE 2026 : SUM coût = 19 253 195, SUM CA = 22 544 725, EBITDA = 3 291 530.
-- =============================================================================
CREATE OR REPLACE VIEW V_ALLOCATION AS
SELECT
    x.SCENARIO, x.PERIODE, x.EXERCICE, x.ENTITY, x.MARQUE,
    x.PROGRAMME, x.AN_ETUDE, x.MODALITE,
    x.VOL_EFF, x.VOL_CLASS, x.CA,
    x.COST_VAC, x.COST_PERM, x.COST_ODIR, x.COST_STRUCT, x.COST_SIEGE,
    (x.COST_VAC  + x.COST_ODIR)                                              AS COST_VARIABLE,
    (x.COST_PERM + x.COST_STRUCT + x.COST_SIEGE)                             AS COST_STRUCTURE,
    (x.COST_VAC + x.COST_ODIR + x.COST_PERM + x.COST_STRUCT + x.COST_SIEGE)  AS COST_COMPLET,
    (x.CA - (x.COST_VAC + x.COST_ODIR + x.COST_PERM + x.COST_STRUCT + x.COST_SIEGE)) AS MARGE_COMPLETE
FROM (
    SELECT
        b.SCENARIO, b.PERIODE, b.EXERCICE, b.ENTITY, b.MARQUE,
        b.PROGRAMME, b.AN_ETUDE, b.MODALITE, b.VOL_EFF, b.VOL_CLASS, b.CA,
        cmp.VAC  * (b.HRS / NULLIF(b.E_HRS,0))                            AS COST_VAC,
        cmp.PERM * (b.HRS / NULLIF(b.E_HRS,0))                            AS COST_PERM,
        cmp.ODIR_EFF * (b.VOL_EFF / NULLIF(b.E_EFF,0))
          + cmp.MKT  * (b.VOL_NEW / NULLIF(b.E_NEW,0))                    AS COST_ODIR,
        cmp.STRUCT_CAMP * (b.VOL_CLASS / NULLIF(b.E_CLS,0))              AS COST_STRUCT,
        sieg.SIEGE_TOT
          * (b.M_CA      / NULLIF(b.G_CA,0))
          * (b.E_EFF     / NULLIF(b.M_EFF,0))
          * (b.VOL_CLASS / NULLIF(b.E_CLS,0))                            AS COST_SIEGE
    FROM (
        SELECT s.*,
            SUM(s.HRS)       OVER (PARTITION BY s.EXERCICE, s.ENTITY) AS E_HRS,
            SUM(s.VOL_EFF)   OVER (PARTITION BY s.EXERCICE, s.ENTITY) AS E_EFF,
            SUM(s.VOL_NEW)   OVER (PARTITION BY s.EXERCICE, s.ENTITY) AS E_NEW,
            SUM(s.VOL_CLASS) OVER (PARTITION BY s.EXERCICE, s.ENTITY) AS E_CLS,
            SUM(s.VOL_EFF)   OVER (PARTITION BY s.EXERCICE, s.MARQUE) AS M_EFF,
            SUM(s.CA)        OVER (PARTITION BY s.EXERCICE, s.MARQUE) AS M_CA,
            SUM(s.CA)        OVER (PARTITION BY s.EXERCICE)           AS G_CA
        FROM (
            SELECT
                s0.SCENARIO, s0.PERIODE, s0.EXERCICE, s0.ENTITY,
                SUBSTR_BEFORE(s0.ENTITY,'_') AS MARQUE,
                s0.PROGRAMME, s0.AN_ETUDE, s0.MODALITE,
                s0.VOL_EFF, s0.VOL_CLASS, s0.VOL_NEW,
                (s0.VOL_EFF * s0.REV_STUD + s0.VOL_NEW * s0.REV_FRAIS_INS) AS CA,
                s0.VOL_CLASS * CASE
                    WHEN s0.PROGRAMME LIKE 'BAC%' AND s0.MODALITE = 'INIT' THEN 600
                    WHEN s0.PROGRAMME LIKE 'BAC%'                          THEN 480
                    WHEN s0.PROGRAMME LIKE 'MAS%' AND s0.MODALITE = 'INIT' THEN 520
                    WHEN s0.PROGRAMME LIKE 'MAS%'                          THEN 420
                    WHEN s0.MODALITE = 'INIT'                              THEN 1000
                    ELSE 700
                END AS HRS
            FROM AW_002_000002_000001 s0
        ) s
    ) b
    JOIN (
        SELECT c.ENTITY, c.EXERCICE,
            SUM(CASE WHEN c.ACCOUNT = '621'  THEN c.AMOUNT ELSE 0 END) AS VAC,
            SUM(CASE WHEN c.ACCOUNT = '6411' THEN c.AMOUNT ELSE 0 END) AS PERM,
            SUM(CASE WHEN c.ACCOUNT IN ('604','6063') THEN c.AMOUNT ELSE 0 END) AS ODIR_EFF,
            SUM(CASE WHEN c.ACCOUNT = '6231' THEN c.AMOUNT ELSE 0 END) AS MKT,
            SUM(CASE WHEN c.ACCOUNT IN ('6413','645','613','615','616','625','63511') THEN c.AMOUNT ELSE 0 END) AS STRUCT_CAMP
        FROM AW_002_000004_000001 c
        GROUP BY c.ENTITY, c.EXERCICE
    ) cmp ON cmp.ENTITY = b.ENTITY AND cmp.EXERCICE = b.EXERCICE
    JOIN (
        SELECT c.EXERCICE,
            SUM(CASE WHEN c.ACCOUNT IN ('6414','6226','6236','626','6281','6331','6333') THEN c.AMOUNT ELSE 0 END) AS SIEGE_TOT
        FROM AW_002_000004_000001 c
        WHERE c.ENTITY = 'GRP'
        GROUP BY c.EXERCICE
    ) sieg ON sieg.EXERCICE = b.EXERCICE
) x
