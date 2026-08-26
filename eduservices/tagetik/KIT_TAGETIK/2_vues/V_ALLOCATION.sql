-- =============================================================================
-- V_ALLOCATION — coût complet par CLASSE, DYNAMIQUE sur les clés d'allocation — SAP HANA
-- RESTITUE 2 MILLÉSIMES par UNION des sources, puis UNE SEULE cascade au-dessus :
--   • 2026 réel   (VERSION='ACT') : volumes = Socle AW_002_000002_000001
--                                   charges = Compta AW_002_000004_000001
--   • 2027 budget (VERSION V01/V02/V03) : volumes/CA = V_MOTEUR (projeté cadrage figé)
--                                   charges = V_BUDGET (compta 2026 × leviers, même maille)
--   VOL_CLASS / HRS = STRUCTURELS (option A) : figés sur la structure Socle 2026,
--   ne bougent pas avec la simulation (l'ouverture/fermeture de classes est gérée à part).
-- Clés d'allocation (Cadrage AW_002_000001_000001, KEY_ALLOC) pilotent la cascade :
--   ALLOC_GRP_BRAND  (K1) : holding groupe -> marque
--   ALLOC_GRP_MARQUE (K4) : FRAIS DE MARQUE (6236) groupe -> marque   [pool distinct]
--   ALLOC_BRAND_CAMP (K2) : marque -> campus
--   ALLOC_CAMP_CLASS (K3) : campus -> classe  (et répartition de la STRUCTURE campus)
-- Valeurs de clé : REV_CA / VOL_EFF / VOL_CLASS.
-- Le SIÈGE est scindé en 2 pools qui télescopent -> total groupe constant :
--   HOLDING = 6414,6226,626,6281,6331,6333 (cascade K1) ; MARQUE = 6236 (cascade K4).
-- Enseignement (621 vac / 6411 perm) = HEURES ; autres directs = effectif/entrants.
-- Contrôle 2026 réel : marge complète 3 291 530 (inchangée par le split).
-- Le millésime restitué se filtre sur EXERCICE / VERSION (côté masque ou rapport).
-- =============================================================================
CREATE OR REPLACE VIEW V_ALLOCATION AS
SELECT
    c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.ENTITY, c.MARQUE, c.PROGRAMME, c.AN_ETUDE, c.MODALITE,
    c.VOL_EFF, c.VOL_CLASS, c.CA,
    c.COST_VAC, c.COST_PERM, c.COST_ODIR, c.COST_STRUCT, c.COST_MARQUE, c.COST_HOLDING,
    (c.COST_MARQUE + c.COST_HOLDING)                                       AS COST_SIEGE,
    (c.COST_VAC + c.COST_ODIR)                                             AS COST_VARIABLE,
    (c.COST_PERM + c.COST_STRUCT + c.COST_MARQUE + c.COST_HOLDING)         AS COST_STRUCTURE,
    (c.COST_VAC + c.COST_ODIR + c.COST_PERM + c.COST_STRUCT + c.COST_MARQUE + c.COST_HOLDING) AS COST_COMPLET,
    (c.CA - (c.COST_VAC + c.COST_ODIR + c.COST_PERM + c.COST_STRUCT + c.COST_MARQUE + c.COST_HOLDING)) AS MARGE_COMPLETE,
    -- ==== Entrées brutes ajoutées en fin de vue (mapping A→T inchangé) ====
    -- lues par l'instantané Excel _CALC_ALLOC en mode autonome (fichier Alloc séparé) :
    c.VOL_NEW,
    c.POOL_VAC, c.POOL_PERM, c.POOL_ODIR, c.POOL_MKT, c.POOL_STRUCT, c.POOL_HOLDING, c.POOL_FRAIS_MARQUE
FROM (
    SELECT s.SCENARIO, s.VERSION, s.PERIODE, s.EXERCICE, s.ENTITY, s.MARQUE, s.PROGRAMME, s.AN_ETUDE, s.MODALITE,
        s.VOL_EFF, s.VOL_CLASS, s.CA, s.VOL_NEW,
        -- Pools bruts exposes pour alimenter l'instantane Excel (masque autonome) :
        s.VAC AS POOL_VAC, s.PERM AS POOL_PERM, s.ODIR_EFF AS POOL_ODIR, s.MKT AS POOL_MKT,
        s.STRUCT_CAMP AS POOL_STRUCT, s.HOLDING_TOT AS POOL_HOLDING, s.MARQUE_TOT AS POOL_FRAIS_MARQUE,
        s.VAC  * (s.HRS / NULLIF(s.E_HRS,0))                                AS COST_VAC,
        s.PERM * (s.HRS / NULLIF(s.E_HRS,0))                                AS COST_PERM,
        s.ODIR_EFF * (s.VOL_EFF / NULLIF(s.E_EFF,0)) + s.MKT * (s.VOL_NEW / NULLIF(s.E_NEW,0)) AS COST_ODIR,
        s.STRUCT_CAMP * (s.D3C / NULLIF(s.D3E,0))                           AS COST_STRUCT,
        -- FRAIS DE MARQUE (6236) : cascade K4 (groupe->marque) puis K2, K3
        s.MARQUE_TOT  * (s.D1M4 / NULLIF(s.D1G4,0)) * (s.D2E / NULLIF(s.D2M,0)) * (s.D3C / NULLIF(s.D3E,0)) AS COST_MARQUE,
        -- HOLDING : cascade K1 (groupe->marque) puis K2, K3
        s.HOLDING_TOT * (s.D1M  / NULLIF(s.D1G,0))  * (s.D2E / NULLIF(s.D2M,0)) * (s.D3C / NULLIF(s.D3E,0)) AS COST_HOLDING
    FROM (
        SELECT b.*,
            CASE b.K3 WHEN 'REV_CA' THEN b.CA   WHEN 'VOL_EFF' THEN b.VOL_EFF ELSE b.VOL_CLASS END AS D3C,
            CASE b.K3 WHEN 'REV_CA' THEN b.E_CA WHEN 'VOL_EFF' THEN b.E_EFF   ELSE b.E_CLS     END AS D3E,
            CASE b.K2 WHEN 'REV_CA' THEN b.E_CA WHEN 'VOL_EFF' THEN b.E_EFF   ELSE b.E_CLS     END AS D2E,
            CASE b.K2 WHEN 'REV_CA' THEN b.M_CA WHEN 'VOL_EFF' THEN b.M_EFF   ELSE b.M_CLS     END AS D2M,
            CASE b.K1 WHEN 'REV_CA' THEN b.M_CA WHEN 'VOL_EFF' THEN b.M_EFF   ELSE b.M_CLS     END AS D1M,
            CASE b.K1 WHEN 'REV_CA' THEN b.G_CA WHEN 'VOL_EFF' THEN b.G_EFF   ELSE b.G_CLS     END AS D1G,
            CASE b.K4 WHEN 'REV_CA' THEN b.M_CA WHEN 'VOL_EFF' THEN b.M_EFF   ELSE b.M_CLS     END AS D1M4,
            CASE b.K4 WHEN 'REV_CA' THEN b.G_CA WHEN 'VOL_EFF' THEN b.G_EFF   ELSE b.G_CLS     END AS D1G4
        FROM (
            SELECT w.*, cmp.VAC, cmp.PERM, cmp.ODIR_EFF, cmp.MKT, cmp.STRUCT_CAMP,
                sieg.HOLDING_TOT, sieg.MARQUE_TOT,
                k.K1, k.K2, k.K3, k.K4
            FROM (
                SELECT s0.*,
                    SUM(s0.HRS)       OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.ENTITY) AS E_HRS,
                    SUM(s0.VOL_EFF)   OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.ENTITY) AS E_EFF,
                    SUM(s0.VOL_NEW)   OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.ENTITY) AS E_NEW,
                    SUM(s0.VOL_CLASS) OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.ENTITY) AS E_CLS,
                    SUM(s0.CA)        OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.ENTITY) AS E_CA,
                    SUM(s0.VOL_EFF)   OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.MARQUE) AS M_EFF,
                    SUM(s0.VOL_CLASS) OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.MARQUE) AS M_CLS,
                    SUM(s0.CA)        OVER (PARTITION BY s0.EXERCICE, s0.VERSION, s0.MARQUE) AS M_CA,
                    SUM(s0.VOL_EFF)   OVER (PARTITION BY s0.EXERCICE, s0.VERSION) AS G_EFF,
                    SUM(s0.VOL_CLASS) OVER (PARTITION BY s0.EXERCICE, s0.VERSION) AS G_CLS,
                    SUM(s0.CA)        OVER (PARTITION BY s0.EXERCICE, s0.VERSION) AS G_CA
                FROM (
                    -- ===== DIMENSION VOLUMES : 2026 réel (Socle) ⊔ 2027 budget (V_MOTEUR) =====
                    SELECT v.SCENARIO, v.VERSION, v.PERIODE, v.EXERCICE, v.ENTITY, v.MARQUE,
                        v.PROGRAMME, v.AN_ETUDE, v.MODALITE, v.VOL_EFF, v.VOL_CLASS, v.VOL_NEW, v.CA,
                        v.VOL_CLASS * CASE
                            WHEN v.PROGRAMME LIKE 'BAC%' AND v.MODALITE='INIT' THEN 600
                            WHEN v.PROGRAMME LIKE 'BAC%'                       THEN 480
                            WHEN v.PROGRAMME LIKE 'MAS%' AND v.MODALITE='INIT' THEN 520
                            WHEN v.PROGRAMME LIKE 'MAS%'                       THEN 420
                            WHEN v.MODALITE='INIT'                             THEN 1000
                            ELSE 700 END AS HRS
                    FROM (
                        -- 2026 réel : volumes & CA depuis le Socle
                        SELECT s00.SCENARIO, 'ACT' AS VERSION, s00.PERIODE, s00.EXERCICE, s00.ENTITY,
                            SUBSTR_BEFORE(s00.ENTITY,'_') AS MARQUE,
                            s00.PROGRAMME, s00.AN_ETUDE, s00.MODALITE,
                            s00.VOL_EFF, s00.VOL_CLASS, s00.VOL_NEW,
                            (s00.VOL_EFF * s00.REV_STUD + s00.VOL_NEW * s00.REV_FRAIS_INS) AS CA
                        FROM AW_002_000002_000001 s00
                        UNION ALL
                        -- 2027 budget : volumes/CA projetés (V_MOTEUR) + VOL_CLASS structurel figé (Socle 2026)
                        SELECT m.SCENARIO, m.VERSION, m.PERIODE, m.EXERCICE, m.ENTITY, m.MARQUE,
                            m.PROGRAMME, m.AN_ETUDE, m.MODALITE,
                            m.EFFECTIF AS VOL_EFF, s26.VOL_CLASS, m.NOUVEAUX AS VOL_NEW, m.CA
                        FROM V_MOTEUR m
                        LEFT JOIN AW_002_000002_000001 s26
                               ON s26.EXERCICE='2026' AND s26.ENTITY=m.ENTITY
                              AND s26.PROGRAMME=m.PROGRAMME AND s26.AN_ETUDE=m.AN_ETUDE
                              AND s26.MODALITE=m.MODALITE
                    ) v
                ) s0
            ) w
            JOIN (
                -- ===== POOLS DE CHARGES CAMPUS : Compta 2026 réel ⊔ V_BUDGET 2027 =====
                SELECT p.ENTITY, p.EXERCICE, p.VERSION,
                    SUM(CASE WHEN p.ACCOUNT='621'  THEN p.AMOUNT ELSE 0 END) AS VAC,
                    SUM(CASE WHEN p.ACCOUNT='6411' THEN p.AMOUNT ELSE 0 END) AS PERM,
                    SUM(CASE WHEN p.ACCOUNT IN ('604','6063') THEN p.AMOUNT ELSE 0 END) AS ODIR_EFF,
                    SUM(CASE WHEN p.ACCOUNT='6231' THEN p.AMOUNT ELSE 0 END) AS MKT,
                    SUM(CASE WHEN p.ACCOUNT IN ('6413','645','613','615','616','625','63511') THEN p.AMOUNT ELSE 0 END) AS STRUCT_CAMP
                FROM (
                    SELECT ENTITY, EXERCICE, 'ACT' AS VERSION, ACCOUNT, AMOUNT FROM AW_002_000004_000001
                    UNION ALL
                    SELECT ENTITY, EXERCICE, VERSION, ACCOUNT, AMOUNT FROM V_BUDGET
                ) p
                GROUP BY p.ENTITY, p.EXERCICE, p.VERSION
            ) cmp ON cmp.ENTITY = w.ENTITY AND cmp.EXERCICE = w.EXERCICE AND cmp.VERSION = w.VERSION
            JOIN (
                -- ===== POOLS SIÈGE (GRP) : Compta 2026 réel ⊔ V_BUDGET 2027 =====
                SELECT p.EXERCICE, p.VERSION,
                    SUM(CASE WHEN p.ACCOUNT IN ('6414','6226','626','6281','6331','6333') THEN p.AMOUNT ELSE 0 END) AS HOLDING_TOT,
                    SUM(CASE WHEN p.ACCOUNT = '6236' THEN p.AMOUNT ELSE 0 END) AS MARQUE_TOT
                FROM (
                    SELECT ENTITY, EXERCICE, 'ACT' AS VERSION, ACCOUNT, AMOUNT FROM AW_002_000004_000001
                    UNION ALL
                    SELECT ENTITY, EXERCICE, VERSION, ACCOUNT, AMOUNT FROM V_BUDGET
                ) p
                WHERE p.ENTITY='GRP'
                GROUP BY p.EXERCICE, p.VERSION
            ) sieg ON sieg.EXERCICE = w.EXERCICE AND sieg.VERSION = w.VERSION
            CROSS JOIN (
                SELECT
                    MAX(CASE WHEN PARAMETRE='ALLOC_GRP_BRAND'  THEN KEY_ALLOC END) AS K1,
                    MAX(CASE WHEN PARAMETRE='ALLOC_BRAND_CAMP' THEN KEY_ALLOC END) AS K2,
                    MAX(CASE WHEN PARAMETRE='ALLOC_CAMP_CLASS' THEN KEY_ALLOC END) AS K3,
                    MAX(CASE WHEN PARAMETRE='ALLOC_GRP_MARQUE' THEN KEY_ALLOC END) AS K4
                FROM AW_002_000001_000001
                WHERE PARAMETRE IN ('ALLOC_GRP_BRAND','ALLOC_BRAND_CAMP','ALLOC_CAMP_CLASS','ALLOC_GRP_MARQUE')
            ) k
        ) b
    ) s
) c;
