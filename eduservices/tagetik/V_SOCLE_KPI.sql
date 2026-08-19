-- =============================================================================
-- VUE KPI SOCLE — EDUSERVICES  (corps SELECT ; Tagetik crée l'objet vue)
-- Source : AW_002_000002_000001 (dataset Socle, scénario 2027BUD_V1) — SAP HANA
-- Objet  : recalcule les mesures DÉRIVÉES depuis les mesures brutes.
--          IFERROR(x,0)  ->  COALESCE(x / NULLIF(dénominateur,0), 0)
-- IMPORTANT : colonnes listées explicitement (PAS de SELECT *) → on exclut les
--   colonnes techniques Tagetik (OID, PROVENIENZA, USERUPD, DATEUPD, EN_VERSION)
--   qui déclenchent « inserted label is a database reserved keyword ».
-- NB : mesures marketing absentes de ce dataset (portées par la compta 6231/6236).
-- =============================================================================
SELECT
    t.SCENARIO,
    t.PERIODE,
    t.ENTITY,
    t.PROGRAMME,
    t.AN_ETUDE,
    t.MODALITE,
    t.EXERCICE,
    t.VOL_LEAD,
    t.VOL_CAND,
    t.VOL_ADMIS,
    t.VOL_NEW,
    t.VOL_REINS,
    t.VOL_EFF,
    t.VOL_EFF_INF,
    t.VOL_CLASS,
    t.REV_STUD,
    t.REV_FRAIS_INS,

    -- Taux de passage        = EFFECTIF / EFFECTIF année inférieure
    COALESCE(t.VOL_EFF   / NULLIF(t.VOL_EFF_INF, 0), 0)    AS TX_PASSAGE,
    -- Taux lead -> cand      = CANDIDATURES / LEADS
    COALESCE(t.VOL_CAND  / NULLIF(t.VOL_LEAD,    0), 0)    AS TX_LEAD_CAND,
    -- Taux cand -> admis     = ADMIS / CANDIDATURES
    COALESCE(t.VOL_ADMIS / NULLIF(t.VOL_CAND,    0), 0)    AS TX_CAND_ADMIS,
    -- Yield admis -> inscrit = NOUVEAUX / ADMIS
    COALESCE(t.VOL_NEW   / NULLIF(t.VOL_ADMIS,   0), 0)    AS TX_YIELD_ADMIS_INSC,
    -- Chiffre d'affaires     = EFFECTIF x REVENU/étu + NOUVEAUX x FRAIS
    (t.VOL_EFF * t.REV_STUD + t.VOL_NEW * t.REV_FRAIS_INS) AS CA
FROM AW_002_000002_000001 t
