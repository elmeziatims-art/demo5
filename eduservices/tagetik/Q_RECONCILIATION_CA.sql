-- =============================================================================
-- Q_RECONCILIATION_CA — Bandeau réconciliation du cockpit (2026 uniquement)
-- =============================================================================
-- Le héros du cockpit : deux sources, un même total, écart 0.
--   CA CRM         = socle,   Σ (effectifs × frais scolarité + nouveaux × frais inscription)
--   CA Budget 2026 = finance, Σ comptes de produits 706 / 7062 / 708
-- Une seule ligne (2026). Écart attendu = 0 €.
--
-- Drills associés (déjà livrés) :
--   CA CRM         -> Q_CA_CONSTITUTION_CRM     (détail CRM : effectifs × tarif)
--   CA Budget 2026 -> Q_CA_CONSTITUTION_COMPTA  (détail Finance : par compte)
-- =============================================================================
SELECT
    crm.CA_CRM                        AS "CA CRM",
    cpt.CA_BUDGET                     AS "CA Budget 2026",
    cpt.CA_BUDGET - crm.CA_CRM        AS "Écart"
FROM (
        SELECT SUM(VOL_EFF * REV_STUD + VOL_NEW * REV_FRAIS_INS) AS CA_CRM
        FROM AW_002_000002_000001
        WHERE n.EXERCICE = '2026'
     ) crm
CROSS JOIN (
        SELECT SUM(AMOUNT) AS CA_BUDGET
        FROM AW_002_000004_000001
        WHERE n.EXERCICE = '2026'
          AND ACCOUNT IN ('706', '7062', '708')
     ) cpt;
