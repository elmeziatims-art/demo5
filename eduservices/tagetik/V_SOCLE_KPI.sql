-- =============================================================================
-- VUE KPI SOCLE — EDUSERVICES  (corps SELECT ; Tagetik crée l'objet vue)
-- Source : AW_002_000002_000001 (dataset Socle, scénario 2027BUD_V1) — SAP HANA
-- Objet  : recalcule les mesures DÉRIVÉES (non chargées) depuis les mesures brutes.
--          IFERROR(x,0)  ->  COALESCE(x / NULLIF(dénominateur,0), 0)
-- NB : les 4 mesures marketing ne sont pas dans ce dataset (elles vivent dans la
--      compta : comptes 6231 / 6236). VOL_LEAD_TOTAL est donc retiré ; si tu les
--      charges un jour, rajoute : (t.<org> + t.<payant>) AS VOL_LEAD_TOTAL,
-- =============================================================================
SELECT
    t.*,

    -- Taux de passage (rétention intra-cycle) = EFFECTIF / EFFECTIF année inférieure
    COALESCE(t.VOL_EFF   / NULLIF(t.VOL_EFF_INF, 0), 0)    AS TX_PASSAGE,

    -- Taux lead -> candidature                = CANDIDATURES / LEADS
    COALESCE(t.VOL_CAND  / NULLIF(t.VOL_LEAD,    0), 0)    AS TX_LEAD_CAND,

    -- Taux candidature -> admis               = ADMIS / CANDIDATURES
    COALESCE(t.VOL_ADMIS / NULLIF(t.VOL_CAND,    0), 0)    AS TX_CAND_ADMIS,

    -- Yield admis -> inscrit                  = NOUVEAUX / ADMIS
    COALESCE(t.VOL_NEW   / NULLIF(t.VOL_ADMIS,   0), 0)    AS TX_YIELD_ADMIS_INSC,

    -- Chiffre d'affaires                      = EFFECTIF x REVENU/étu + NOUVEAUX x FRAIS
    (t.VOL_EFF * t.REV_STUD + t.VOL_NEW * t.REV_FRAIS_INS) AS CA
FROM AW_002_000002_000001 t
