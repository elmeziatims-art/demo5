-- =============================================================================
-- VUE KPI SOCLE — EDUSERVICES
-- Source : AW_002_000002_000001 (dataset Socle, scénario 2027BUD_V1)
-- Objet  : recalcule les mesures DÉRIVÉES (non chargées) à partir des mesures brutes.
--          IFERROR(x,0)  ->  COALESCE(x / NULLIF(dénominateur,0), 0)
-- Portable Oracle / SAP HANA (CREATE OR REPLACE). SQL Server : CREATE OR ALTER VIEW.
-- -----------------------------------------------------------------------------
-- NB marketing : la ligne VOL_LEAD_TOTAL suppose les colonnes VOL_LEAD_ORG et
--    VOL_LEAD_PAY. Si tu les as nommées autrement, ajuste UNIQUEMENT cette ligne.
-- =============================================================================
CREATE OR REPLACE VIEW V_SOCLE_KPI AS
SELECT
    t.*,

    -- Taux de passage (rétention intra-cycle)  = EFFECTIF / EFFECTIF année inférieure
    COALESCE(t.VOL_EFF   / NULLIF(t.VOL_EFF_INF, 0), 0)              AS TX_PASSAGE,

    -- Taux lead -> candidature                 = CANDIDATURES / LEADS
    COALESCE(t.VOL_CAND  / NULLIF(t.VOL_LEAD,    0), 0)              AS TX_LEAD_CAND,

    -- Taux candidature -> admis                = ADMIS / CANDIDATURES
    COALESCE(t.VOL_ADMIS / NULLIF(t.VOL_CAND,    0), 0)              AS TX_CAND_ADMIS,

    -- Yield admis -> inscrit                   = NOUVEAUX / ADMIS
    COALESCE(t.VOL_NEW   / NULLIF(t.VOL_ADMIS,   0), 0)              AS TX_YIELD_ADMIS_INSC,

    -- Leads totaux                             = organiques + payants
    (t.VOL_LEAD_ORG + t.VOL_LEAD_PAY)                               AS VOL_LEAD_TOTAL,

    -- Chiffre d'affaires                       = EFFECTIF x REVENU/étu + NOUVEAUX x FRAIS
    (t.VOL_EFF * t.REV_STUD + t.VOL_NEW * t.REV_FRAIS_INS)          AS CA
FROM AW_002_000002_000001 t;
