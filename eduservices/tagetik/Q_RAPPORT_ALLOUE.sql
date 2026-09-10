-- =============================================================================
-- Q_RAPPORT_ALLOUE — datasource Tagetik du P&L CHARGÉ (avant / après allocation)
-- Lit V_ALLOCATION. Forme Tagetik : 1 DIMENSION = 1 COLONNE, les mesures sont des
-- colonnes calculées (les marges ne sont PAS un compte, ce sont des calculs).
--
-- ── DIMENSIONS DU CROISEMENT (à mettre en lignes / filtres du rapport) ───────
--   EXERCICE    : millésime            (2024 / 2025 / 2026 réel ; 2027 budget)
--   VERSION     : 'ACT' (réel) | V01/V02/V03 (budget)
--   MARQUE      : MBway / Iscom / Ipac / Pigier / Tunon
--   CAMPUS      : ENTITY (ex. MBWAY_LYO)
--   PROGRAMME   : ex. BAC_MGT, MAS_COM…
--   AN_ETUDE    : B1/B2/B3, M1/M2…
--   MODALITE    : INIT (initial) | ALT (alternance)
--   -> hiérarchie d'affichage conseillée : MARQUE ▸ CAMPUS ▸ PROGRAMME ▸ AN_ETUDE ▸ MODALITE
--
-- ── MESURES (colonnes) et COMPOSITION EN COMPTES ────────────────────────────
--   EFFECTIF          = VOL_EFF (statistique)
--   CA                = produits 706 + 7062 + 708   (= socle : REV_STUD×VOL_EFF + REV_FRAIS_INS×VOL_NEW)
--   COST_VAC          = 621                          (enseignants vacataires ; alloué aux heures)
--   COST_PERM         = 6411                         (enseignants permanents ; aux heures)
--   COST_ODIR         = 604 + 6063 + 6231            (achats directs + acquisition ; à l'effectif/entrants)
--   COST_STRUCT       = 6413 + 645 + 613 + 615 + 616 + 625 + 63511   (structure campus ; clé K3)
--   COST_MARQUE       = 6236                         (marketing de marque ; cascade K4 groupe→marque→…)
--   COST_HOLDING      = 6414 + 6226 + 626 + 6281 + 6331 + 6333       (siège ; cascade K1)
--
--   EBITDA_PROPRE     = CA − (COST_VAC+COST_PERM+COST_ODIR+COST_STRUCT)     (avant siège)
--   QUOTE_PART_SIEGE  = COST_MARQUE + COST_HOLDING                          (ce que le siège coûte)
--   EBITDA_NET        = EBITDA_PROPRE − QUOTE_PART_SIEGE  (= CA − tous les coûts ci-dessus)
--   HORS EBITDA : dotations 6811 exclues.
--   Marges % = membres calculés du rapport (mesure ÷ CA).
-- =============================================================================
SELECT
    -- ── dimensions (une par colonne) ──
    d.EXERCICE,
    d.VERSION,
    d.MARQUE,
    d.ENTITY        AS CAMPUS,
    d.PROGRAMME,
    d.AN_ETUDE,
    d.MODALITE,
    -- ── mesures ──
    d.VOL_EFF                               AS EFFECTIF,
    d.CA                                    AS CA,
    (d.CA - (d.COST_VAC + d.COST_PERM + d.COST_ODIR + d.COST_STRUCT)) AS EBITDA_PROPRE,
    d.COST_SIEGE                            AS QUOTE_PART_SIEGE,   -- = COST_MARQUE + COST_HOLDING
    d.MARGE_COMPLETE                        AS EBITDA_NET,
    -- ── détail des coûts (pour composer toute marge côté rapport) ──
    d.COST_VAC, d.COST_PERM, d.COST_ODIR, d.COST_STRUCT, d.COST_MARQUE, d.COST_HOLDING
FROM V_ALLOCATION d
-- Filtre par défaut du rapport « avant/après » : un millésime à la fois.
-- ex. réel 2026 :  WHERE d.VERSION = 'ACT' AND d.EXERCICE = '2026'
-- ex. budget V01 : WHERE d.VERSION = 'V01' AND d.EXERCICE = '2027'
;
