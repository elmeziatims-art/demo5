-- =============================================================================
-- V_ALLOCATION — coût complet par CLASSE, DYNAMIQUE sur les clés d'allocation — SAP HANA
-- Sources : AW_002_000002_000001 (socle) + AW_002_000004_000001 (compta) + AW_002_000001_000001 (cadrage: KEY_ALLOC)
-- Les 3 clés (ALLOC_GRP_BRAND / ALLOC_BRAND_CAMP / ALLOC_CAMP_CLASS) pilotent la cascade du SIÈGE
-- et la répartition de la STRUCTURE campus. Valeurs de clé : REV_CA / VOL_EFF / VOL_CLASS.
-- Enseignement (621 vac / 6411 perm) = HEURES (fixe) ; autres directs = effectif/entrants (fixe).
-- Changer une clé redistribue le coût à TOTAL GROUPE CONSTANT (somme nulle). Contrôle 2026 : marge 3 291 530.
-- =============================================================================
CREATE OR REPLACE VIEW V_ALLOCATION AS
SELECT
    c.SCENARIO, c.PERIODE, c.EXERCICE, c.ENTITY, c.MARQUE, c.PROGRAMME, c.AN_ETUDE, c.MODALITE,
    c.VOL_EFF, c.VOL_CLASS, c.CA,
    c.COST_VAC, c.COST_PERM, c.COST_ODIR, c.COST_STRUCT, c.COST_SIEGE,
    (c.COST_VAC + c.COST_ODIR)                                              AS COST_VARIABLE,
    (c.COST_PERM + c.COST_STRUCT + c.COST_SIEGE)                            AS COST_STRUCTURE,
    (c.COST_VAC + c.COST_ODIR + c.COST_PERM + c.COST_STRUCT + c.COST_SIEGE) AS COST_COMPLET,
    (c.CA - (c.COST_VAC + c.COST_ODIR + c.COST_PERM + c.COST_STRUCT + c.COST_SIEGE)) AS MARGE_COMPLETE
FROM (
    SELECT s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY, s.MARQUE, s.PROGRAMME, s.AN_ETUDE, s.MODALITE,
        s.VOL_EFF, s.VOL_CLASS, s.CA,
        s.VAC  * (s.HRS / NULLIF(s.E_HRS,0))                                AS COST_VAC,
        s.PERM * (s.HRS / NULLIF(s.E_HRS,0))                                AS COST_PERM,
        s.ODIR_EFF * (s.VOL_EFF / NULLIF(s.E_EFF,0)) + s.MKT * (s.VOL_NEW / NULLIF(s.E_NEW,0)) AS COST_ODIR,
        s.STRUCT_CAMP * (s.D3C / NULLIF(s.D3E,0))                           AS COST_STRUCT,
        s.SIEGE_TOT * (s.D1M / NULLIF(s.D1G,0)) * (s.D2E / NULLIF(s.D2M,0)) * (s.D3C / NULLIF(s.D3E,0)) AS COST_SIEGE
    FROM (
        SELECT b.*,
            CASE b.K3 WHEN 'REV_CA' THEN b.CA   WHEN 'VOL_EFF' THEN b.VOL_EFF ELSE b.VOL_CLASS END AS D3C,
            CASE b.K3 WHEN 'REV_CA' THEN b.E_CA WHEN 'VOL_EFF' THEN b.E_EFF   ELSE b.E_CLS     END AS D3E,
            CASE b.K2 WHEN 'REV_CA' THEN b.E_CA WHEN 'VOL_EFF' THEN b.E_EFF   ELSE b.E_CLS     END AS D2E,
            CASE b.K2 WHEN 'REV_CA' THEN b.M_CA WHEN 'VOL_EFF' THEN b.M_EFF   ELSE b.M_CLS     END AS D2M,
            CASE b.K1 WHEN 'REV_CA' THEN b.M_CA WHEN 'VOL_EFF' THEN b.M_EFF   ELSE b.M_CLS     END AS D1M,
            CASE b.K1 WHEN 'REV_CA' THEN b.G_CA WHEN 'VOL_EFF' THEN b.G_EFF   ELSE b.G_CLS     END AS D1G
        FROM (
            SELECT w.*, cmp.VAC, cmp.PERM, cmp.ODIR_EFF, cmp.MKT, cmp.STRUCT_CAMP, sieg.SIEGE_TOT,
                k.K1, k.K2, k.K3
            FROM (
                SELECT s0.*,
                    SUM(s0.HRS)       OVER (PARTITION BY s0.EXERCICE, s0.ENTITY) AS E_HRS,
                    SUM(s0.VOL_EFF)   OVER (PARTITION BY s0.EXERCICE, s0.ENTITY) AS E_EFF,
                    SUM(s0.VOL_NEW)   OVER (PARTITION BY s0.EXERCICE, s0.ENTITY) AS E_NEW,
                    SUM(s0.VOL_CLASS) OVER (PARTITION BY s0.EXERCICE, s0.ENTITY) AS E_CLS,
                    SUM(s0.CA)        OVER (PARTITION BY s0.EXERCICE, s0.ENTITY) AS E_CA,
                    SUM(s0.VOL_EFF)   OVER (PARTITION BY s0.EXERCICE, s0.MARQUE) AS M_EFF,
                    SUM(s0.VOL_CLASS) OVER (PARTITION BY s0.EXERCICE, s0.MARQUE) AS M_CLS,
                    SUM(s0.CA)        OVER (PARTITION BY s0.EXERCICE, s0.MARQUE) AS M_CA,
                    SUM(s0.VOL_EFF)   OVER (PARTITION BY s0.EXERCICE) AS G_EFF,
                    SUM(s0.VOL_CLASS) OVER (PARTITION BY s0.EXERCICE) AS G_CLS,
                    SUM(s0.CA)        OVER (PARTITION BY s0.EXERCICE) AS G_CA
                FROM (
                    SELECT s00.SCENARIO, s00.PERIODE, s00.EXERCICE, s00.ENTITY,
                        SUBSTR_BEFORE(s00.ENTITY,'_') AS MARQUE,
                        s00.PROGRAMME, s00.AN_ETUDE, s00.MODALITE, s00.VOL_EFF, s00.VOL_CLASS, s00.VOL_NEW,
                        (s00.VOL_EFF * s00.REV_STUD + s00.VOL_NEW * s00.REV_FRAIS_INS) AS CA,
                        s00.VOL_CLASS * CASE
                            WHEN s00.PROGRAMME LIKE 'BAC%' AND s00.MODALITE='INIT' THEN 600
                            WHEN s00.PROGRAMME LIKE 'BAC%'                         THEN 480
                            WHEN s00.PROGRAMME LIKE 'MAS%' AND s00.MODALITE='INIT' THEN 520
                            WHEN s00.PROGRAMME LIKE 'MAS%'                         THEN 420
                            WHEN s00.MODALITE='INIT'                               THEN 1000
                            ELSE 700 END AS HRS
                    FROM AW_002_000002_000001 s00
                ) s0
            ) w
            JOIN (
                SELECT cc.ENTITY, cc.EXERCICE,
                    SUM(CASE WHEN cc.ACCOUNT='621'  THEN cc.AMOUNT ELSE 0 END) AS VAC,
                    SUM(CASE WHEN cc.ACCOUNT='6411' THEN cc.AMOUNT ELSE 0 END) AS PERM,
                    SUM(CASE WHEN cc.ACCOUNT IN ('604','6063') THEN cc.AMOUNT ELSE 0 END) AS ODIR_EFF,
                    SUM(CASE WHEN cc.ACCOUNT='6231' THEN cc.AMOUNT ELSE 0 END) AS MKT,
                    SUM(CASE WHEN cc.ACCOUNT IN ('6413','645','613','615','616','625','63511') THEN cc.AMOUNT ELSE 0 END) AS STRUCT_CAMP
                FROM AW_002_000004_000001 cc GROUP BY cc.ENTITY, cc.EXERCICE
            ) cmp ON cmp.ENTITY = w.ENTITY AND cmp.EXERCICE = w.EXERCICE
            JOIN (
                SELECT cc.EXERCICE,
                    SUM(CASE WHEN cc.ACCOUNT IN ('6414','6226','6236','626','6281','6331','6333') THEN cc.AMOUNT ELSE 0 END) AS SIEGE_TOT
                FROM AW_002_000004_000001 cc WHERE cc.ENTITY='GRP' GROUP BY cc.EXERCICE
            ) sieg ON sieg.EXERCICE = w.EXERCICE
            CROSS JOIN (
                SELECT
                    MAX(CASE WHEN PARAMETRE='ALLOC_GRP_BRAND'  THEN KEY_ALLOC END) AS K1,
                    MAX(CASE WHEN PARAMETRE='ALLOC_BRAND_CAMP' THEN KEY_ALLOC END) AS K2,
                    MAX(CASE WHEN PARAMETRE='ALLOC_CAMP_CLASS' THEN KEY_ALLOC END) AS K3
                FROM AW_002_000001_000001
                WHERE PARAMETRE IN ('ALLOC_GRP_BRAND','ALLOC_BRAND_CAMP','ALLOC_CAMP_CLASS')
            ) k
        ) b
    ) s
) c
