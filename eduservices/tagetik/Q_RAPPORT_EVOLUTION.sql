-- =============================================================================
-- Q_RAPPORT_EVOLUTION — datasource Tagetik : CA · Charges · Marge dans le temps
-- Lit V_ALLOCATION. 1 dimension = 1 colonne ; EXERCICE se pivote en colonnes.
--
-- PAS besoin de filtrer VERSION='ACT' : dans V_ALLOCATION le budget est
-- exclusivement 2027 (branche V_MOTEUR). Donc EXERCICE ∈ {2024,2025,2026} =
-- le réel, par construction. (Si un jour tu charges du budget sur ces années,
-- rajoute le filtre VERSION.)
--
-- ── DIMENSIONS ──────────────────────────────────────────────────────────────
--   EXERCICE (→ colonnes) · MARQUE · CAMPUS(ENTITY) · PROGRAMME · AN_ETUDE · MODALITE
--
-- ── MESURES (colonnes) ──────────────────────────────────────────────────────
--   EFFECTIF = VOL_EFF
--   CA       = 706 + 7062 + 708                         (colonne CA)
--   CHARGES  = coût complet chargé                       (colonne COST_COMPLET)
--   EBITDA_NET = CA − CHARGES                            (colonne MARGE_COMPLETE)
--   -> Marge % = EBITDA_NET / CA        (membre calculé)
--   -> Écart € = valeur 2026 − valeur 2024   ·   Évolution % = 2026/2024 − 1  (membres calculés)
-- =============================================================================
SELECT
    EXERCICE,
    MARQUE,
    ENTITY          AS CAMPUS,
    PROGRAMME,
    AN_ETUDE,
    MODALITE,
    VOL_EFF         AS EFFECTIF,
    CA              AS CA,
    COST_COMPLET    AS CHARGES,
    MARGE_COMPLETE  AS EBITDA_NET
FROM V_ALLOCATION
WHERE EXERCICE IN ('2024','2025','2026')
;
