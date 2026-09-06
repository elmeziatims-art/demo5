-- =============================================================================
-- V_FUNNEL — Faits de conversion (lead -> candidat -> admis -> inscrit)
-- Source : AW_002_000002_000001 (Socle CRM).
-- =============================================================================
-- Vue PLATE, indexée sur les dimensions Tagetik, MESURES ADDITIVES uniquement.
-- Les taux de passage se calculent DANS la matrice Tagetik (multidim à
-- n'importe quelle maille : groupe, marque, campus, programme, cycle, modalité).
-- On n'écrase aucune maille et on ne pré-agrège aucun ratio.
--   TX lead->cand   = SUM(CANDIDATS) / SUM(LEADS)
--   TX cand->admis  = SUM(ADMIS)     / SUM(CANDIDATS)
--   TX admis->insc  = SUM(INSCRITS)  / SUM(ADMIS)
-- =============================================================================
CREATE OR ALTER VIEW V_FUNNEL AS
SELECT
    EXERCICE,
    ENTITY,                         -- campus (roule vers marque via la dim Entity)
    PROGRAMME,
    AN_ETUDE,                       -- roule vers Cycle (Bachelor/BTS/Master)
    MODALITE,                       -- INIT / ALT
    SUM(VOL_LEAD)   AS LEADS,
    SUM(VOL_CAND)   AS CANDIDATS,
    SUM(VOL_ADMIS)  AS ADMIS,
    SUM(VOL_NEW)    AS INSCRITS
FROM AW_002_000002_000001
GROUP BY EXERCICE, ENTITY, PROGRAMME, AN_ETUDE, MODALITE;
