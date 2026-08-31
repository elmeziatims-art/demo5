-- =============================================================================
-- Q_RAPPORT_EVOLUTION — datasource Tagetik de la marge CHARGÉE dans le temps
-- Lit V_ALLOCATION (réel). Forme Tagetik : 1 DIMENSION = 1 COLONNE ; EXERCICE
-- sera mis EN COLONNES côté rapport (2024 | 2025 | 2026) pour lire la trajectoire.
-- La marge n'est pas un compte : c'est un membre calculé (EBITDA_NET ÷ CA).
--
-- ── DIMENSIONS DU CROISEMENT ────────────────────────────────────────────────
--   EXERCICE    : 2024 / 2025 / 2026        (→ à pivoter en colonnes)
--   MARQUE      : MBway / Iscom / Ipac / Pigier / Tunon
--   CAMPUS      : ENTITY
--   PROGRAMME / AN_ETUDE / MODALITE          (mailles fines dépliables)
--   -> lignes : MARQUE ▸ CAMPUS ▸ PROGRAMME ▸ AN_ETUDE ▸ MODALITE ; colonnes : EXERCICE
--   VERSION fixée à 'ACT' (réel) : on trace l'historique, pas le budget.
--
-- ── MESURES (colonnes) et COMPOSITION EN COMPTES ────────────────────────────
--   EFFECTIF    = VOL_EFF
--   CA          = produits 706 + 7062 + 708
--   EBITDA_NET  = CA − ( 621 + 6411                       (enseignement)
--                        + 604+6063+6231                  (autres directs + acquisition)
--                        + 6413+645+613+615+616+625+63511 (structure campus)
--                        + 6236                            (marketing marque, siège)
--                        + 6414+6226+626+6281+6331+6333 ) (holding, siège)
--               = MARGE_COMPLETE de V_ALLOCATION (coût complet chargé, hors dotations 6811).
--   MARGE_NETTE_%  = EBITDA_NET ÷ CA   → membre calculé du rapport.
--   Δ (points)     = comparaison de colonnes (marge 2026 − marge 2024) → membre calculé.
-- =============================================================================
SELECT
    -- ── dimensions ──
    d.EXERCICE,
    d.MARQUE,
    d.ENTITY     AS CAMPUS,
    d.PROGRAMME,
    d.AN_ETUDE,
    d.MODALITE,
    -- ── mesures ──
    d.VOL_EFF          AS EFFECTIF,
    d.CA               AS CA,
    d.MARGE_COMPLETE   AS EBITDA_NET
FROM V_ALLOCATION d
WHERE d.VERSION = 'ACT'
  AND d.EXERCICE IN ('2024','2025','2026')
;
