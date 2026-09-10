-- =============================================================================
-- V_SOCLE_KPI (enrichie marketing) — SAP HANA
-- =============================================================================
CREATE OR REPLACE VIEW V_SOCLE_KPI AS
SELECT ; SAP HANA)
-- Source : AW_002_000002_000001 (socle, 14 mesures dont marketing)
-- Colonnes explicites (pas de SELECT * → on exclut OID/PROVENIENZA/USERUPD/DATEUPD/EN_VERSION)
-- IFERROR(x,0) -> COALESCE(x / NULLIF(dénominateur,0), 0)
-- =============================================================================
SELECT
    t.SCENARIO, t.PERIODE, t.ENTITY, t.PROGRAMME, t.AN_ETUDE, t.MODALITE, t.EXERCICE,
    t.VOL_LEAD, t.VOL_CAND, t.VOL_ADMIS, t.VOL_NEW, t.VOL_REINS,
    t.VOL_EFF, t.VOL_EFF_INF, t.VOL_CLASS, t.REV_STUD, t.REV_FRAIS_INS,
    t.VOL_LEAD_ORG, t.VOL_LEAD_PAY, t.DEPENSE_ACQ, t.DEPENSE_MARQUE,

    -- Funnel
    COALESCE(t.VOL_EFF   / NULLIF(t.VOL_EFF_INF, 0), 0)    AS TX_PASSAGE,
    COALESCE(t.VOL_CAND  / NULLIF(t.VOL_LEAD,    0), 0)    AS TX_LEAD_CAND,
    COALESCE(t.VOL_ADMIS / NULLIF(t.VOL_CAND,    0), 0)    AS TX_CAND_ADMIS,
    COALESCE(t.VOL_NEW   / NULLIF(t.VOL_ADMIS,   0), 0)    AS TX_YIELD_ADMIS_INSC,

    -- Marketing dérivé
    (t.VOL_LEAD_ORG + t.VOL_LEAD_PAY)                                        AS VOL_LEAD_TOTAL,
    COALESCE(t.VOL_LEAD_ORG / NULLIF(t.VOL_LEAD_ORG + t.VOL_LEAD_PAY, 0), 0) AS PART_ORG,
    COALESCE(t.DEPENSE_ACQ / NULLIF(t.VOL_LEAD_PAY, 0), 0)                       AS CPL,

    -- CA
    (t.VOL_EFF * t.REV_STUD + t.VOL_NEW * t.REV_FRAIS_INS)                   AS CA
FROM AW_002_000002_000001 t
