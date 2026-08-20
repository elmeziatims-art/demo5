-- =============================================================================
-- VUE P&L UNIFIÉE — EDUSERVICES, AU GRAIN COMPTE  (SAP HANA)
-- 1 ligne = ENTITY x ACCOUNT x EXERCICE x VERSION, 1 mesure AMOUNT.
--   • RÉEL   2024-2026 ← compta AW_002_000004_000001            (VERSION = 'ACT')
--   • BUDGET 2027      ← V_BUDGET (compta 2026 projetée)         (VERSION = V01/V02/V03)
-- PAS d'agrégation SIG ici : c'est la HIÉRARCHIE de la dimension Compte, DANS
-- TAGETIK, qui remonte Produits -> Marge de contribution -> EBITDA -> EBIT.
-- Montants positifs (le sens produit/charge est porté par le compte).
-- PERIOD = dimension caractère. Un seul SCENARIO (2027BUD_V1), plusieurs EXERCICE.
-- =============================================================================
CREATE OR REPLACE VIEW V_PNL AS
-- ===== RÉEL 2024-2026 (compta, tel quel) =====
SELECT
    ENTITY,
    ACCOUNT,
    EXERCICE,
    'ACT'                       AS VERSION,
    SCENARIO,
    CAST(PERIOD AS NVARCHAR(10)) AS PERIOD,
    AMOUNT
FROM AW_002_000004_000001

UNION ALL

-- ===== BUDGET 2027 (construit) =====
SELECT
    ENTITY,
    ACCOUNT,
    EXERCICE,
    VERSION,
    SCENARIO,
    PERIOD,
    AMOUNT
FROM V_BUDGET;
