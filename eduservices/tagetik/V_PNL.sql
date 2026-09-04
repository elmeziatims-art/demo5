-- =============================================================================
-- VUE P&L UNIFIÉE — EDUSERVICES, AU GRAIN COMPTE  (SQL Server / T-SQL)
-- 1 ligne = ENTITY x ACCOUNT x EXERCICE x VERSION, 1 mesure AMOUNT.
--   • RÉEL   2024-2026 ← compta AW_002_000004_000001            (VERSION = 'ACT')
--   • BUDGET 2027      ← V_BUDGET (compta 2026 projetée)         (VERSION = V01/V02/V03)
--   • EFFECTIF (réel socle + budget moteur) = compte STATISTIQUE 'EFFECTIF'
-- PAS d'agrégation SIG ici : la hiérarchie de la dimension Compte, DANS TAGETIK,
-- remonte Produits -> Marge -> EBITDA -> EBIT. Le compte 'EFFECTIF' doit être
-- STATISTIQUE (hors hiérarchie P&L, non monétaire) -> ratios CA/étudiant &
-- EBITDA/étudiant calculés dans la matrice Tagetik.
-- PERIOD = dimension caractère. Un seul SCENARIO (2027BUD_V1), plusieurs EXERCICE.
-- =============================================================================
CREATE OR ALTER VIEW V_PNL AS
-- ===== RÉEL 2024-2026 : compta (comptes financiers) =====
SELECT ENTITY, ACCOUNT, EXERCICE, 'ACT' AS VERSION, SCENARIO,
       CAST(PERIOD AS VARCHAR(10)) AS PERIOD, AMOUNT
FROM AW_002_000004_000001

UNION ALL
-- ===== BUDGET 2027 : compta projetée (comptes financiers) =====
SELECT ENTITY, ACCOUNT, EXERCICE, VERSION, SCENARIO, PERIOD, AMOUNT
FROM V_BUDGET

UNION ALL
-- ===== EFFECTIF RÉEL 2024-2026 (socle) — compte statistique =====
SELECT ENTITY, 'EFFECTIF' AS ACCOUNT, EXERCICE, 'ACT' AS VERSION, SCENARIO,
       CAST('12' AS VARCHAR(10)) AS PERIOD, SUM(VOL_EFF) AS AMOUNT
FROM AW_002_000002_000001
GROUP BY ENTITY, EXERCICE, SCENARIO

UNION ALL
-- ===== EFFECTIF BUDGET 2027 (moteur) — compte statistique =====
SELECT ENTITY, 'EFFECTIF' AS ACCOUNT, '2027' AS EXERCICE, VERSION, '2027BUD_V1' AS SCENARIO,
       CAST('12' AS VARCHAR(10)) AS PERIOD, SUM(EFFECTIF) AS AMOUNT
FROM V_MOTEUR
GROUP BY ENTITY, VERSION;
