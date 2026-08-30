-- =============================================================================
-- Q_RAPPORT_EVOLUTION — datasource du rapport "évolution de la marge chargée"
-- DYNAMIQUE : lit V_ALLOCATION. La trajectoire de la marge nette (après allocation)
-- par maille, sur les millésimes réels. Tagetik met EXERCICE en colonnes et plie
-- les dimensions en lignes.
--
-- Mesures exposées par maille & par exercice :
--   CA            = CA
--   EBITDA net    = MARGE_COMPLETE
--   Marge nette % = MARGE_COMPLETE / CA   (membre calculé côté rapport)
-- Le Δ (pt) entre deux exercices = comparaison de colonnes dans le rapport.
--
-- Grain : ENTITY x MARQUE x PROGRAMME x AN_ETUDE x MODALITE x EXERCICE.
-- On reste sur le réel (VERSION='ACT') pour la trajectoire historique ;
-- pour comparer réel vs budget, enlever le filtre VERSION.
-- =============================================================================
SELECT
    EXERCICE, ENTITY, MARQUE, PROGRAMME, AN_ETUDE, MODALITE,
    VOL_EFF          AS "Effectif",
    CA               AS "CA",
    MARGE_COMPLETE   AS "EBITDA net"
FROM V_ALLOCATION
WHERE VERSION = 'ACT'
  AND EXERCICE IN ('2024','2025','2026')
-- Tagetik : EXERCICE en colonnes (2024/2025/2026), maille en lignes pliables,
-- Marge nette % = EBITDA net / CA, Δ pt = colonne calculée (2026 − 2024).
;
