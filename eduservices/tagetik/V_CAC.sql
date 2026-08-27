-- =============================================================================
-- V_CAC — Faits d'acquisition (dépense, leads payants, inscrits)
-- Source : AW_002_000002_000001 (Socle CRM).
-- =============================================================================
-- Vue PLATE, indexée sur les dimensions Tagetik, MESURES ADDITIVES uniquement.
-- CPL et CAC se calculent DANS la matrice Tagetik, à n'importe quelle maille
-- (groupe, marque, campus, programme, cycle, modalité) :
--   CPL = SUM(DEPENSE_ACQ) / SUM(LEADS_PAYANTS)
--   CAC = SUM(DEPENSE_ACQ) / SUM(INSCRITS)
-- Aucun ratio pré-agrégé, aucune maille écrasée.
-- =============================================================================
CREATE OR REPLACE VIEW V_CAC AS
SELECT
    EXERCICE,
    ENTITY,                         -- campus (roule vers marque via la dim Entity)
    PROGRAMME,
    AN_ETUDE,
    MODALITE,
    SUM(DEPENSE_ACQ)    AS DEPENSE_ACQ,
    SUM(VOL_LEAD_PAY)   AS LEADS_PAYANTS,
    SUM(VOL_LEAD)       AS LEADS,
    SUM(VOL_NEW)        AS INSCRITS
FROM AW_002_000002_000001
GROUP BY EXERCICE, ENTITY, PROGRAMME, AN_ETUDE, MODALITE;
