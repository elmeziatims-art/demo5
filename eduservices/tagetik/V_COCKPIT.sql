-- =============================================================================
-- V_COCKPIT — brique de données de l'ÉCRAN D'OUVERTURE (SAP HANA)
-- =============================================================================
-- Acte 1 de la démo. 1 ligne = ENTITY x EXERCICE (réel 2024-2026).
-- Grain campus -> la hiérarchie Tagetik agrège au GROUPE et laisse driller
-- vers marque puis campus (tuile cockpit -> P&L comparatif ①).
--
-- MESURES ADDITIVES uniquement. Les ratios du cockpit se calculent DANS la
-- matrice Tagetik, jamais ici (on ne pré-agrège jamais un ratio) :
--     CAC     = SUM(DEPENSE_ACQ) / SUM(INSCRITS)
--     Marge % = SUM(EBITDA)      / SUM(CA_COMPTA)
--
-- LE HÉROS DU COCKPIT — la réconciliation :
--     CA_CRM    = socle, effectifs x frais (VOL_EFF*REV_STUD + VOL_NEW*REV_FRAIS_INS)
--     CA_COMPTA = grand livre, comptes de produits 706 / 7062 / 708
--     ECART_CA  = CA_COMPTA - CA_CRM   -> attendu 0 € (deux chemins, un chiffre)
--
-- EBITDA cohérent avec Q_SCENARIOS et le P&L : produits (706/7062/708)
-- moins charges d'exploitation (6x hors 6811 amortissements).
-- =============================================================================
CREATE OR REPLACE VIEW V_COCKPIT AS
WITH fin AS (                         -- ===== côté COMPTA (grand livre) =====
    SELECT ENTITY, EXERCICE,
        SUM(CASE WHEN ACCOUNT IN ('706','7062','708') THEN AMOUNT ELSE 0 END)
            AS CA_COMPTA,
        SUM(CASE WHEN ACCOUNT IN ('706','7062','708')            THEN  AMOUNT
                 WHEN ACCOUNT LIKE '6%' AND ACCOUNT <> '6811'    THEN -AMOUNT
                 ELSE 0 END)
            AS EBITDA
    FROM AW_002_000004_000001                     -- compta = réel pur (2024-2026)
    GROUP BY ENTITY, EXERCICE
),
com AS (                              -- ===== côté CRM (socle) =====
    SELECT ENTITY, EXERCICE,
        SUM(VOL_EFF * REV_STUD + VOL_NEW * REV_FRAIS_INS)  AS CA_CRM,
        SUM(VOL_LEAD_ORG + VOL_LEAD_PAY)                   AS LEADS,
        SUM(VOL_NEW)                                       AS INSCRITS,
        SUM(DEPENSE_ACQ)                                   AS DEPENSE_ACQ
    FROM AW_002_000002_000001
    GROUP BY ENTITY, EXERCICE
)
SELECT
    COALESCE(fin.ENTITY,   com.ENTITY)                     AS ENTITY,
    SUBSTR_BEFORE(COALESCE(fin.ENTITY, com.ENTITY), '_')   AS MARQUE,
    COALESCE(fin.EXERCICE, com.EXERCICE)                   AS EXERCICE,
    -- réconciliation (le bandeau héros)
    com.CA_CRM                                             AS CA_CRM,
    fin.CA_COMPTA                                          AS CA_COMPTA,
    fin.CA_COMPTA - com.CA_CRM                             AS ECART_CA,   -- = 0
    -- finance
    fin.EBITDA                                             AS EBITDA,
    -- commercial
    com.LEADS                                              AS LEADS,
    com.INSCRITS                                           AS INSCRITS,
    com.DEPENSE_ACQ                                        AS DEPENSE_ACQ
FROM fin
FULL OUTER JOIN com
    ON  fin.ENTITY   = com.ENTITY
    AND fin.EXERCICE = com.EXERCICE;
