-- =============================================================================
-- V_TENDANCE — Tendance historique (leads, inscrits, CA, dépenses)
-- Source : AW_002_000002_000001 (Socle CRM).
-- =============================================================================
-- Vue PLATE, indexée sur les dimensions, MESURES ADDITIVES uniquement.
-- Sert le graphe de tendance base 100 (Activité = CA vs Dépenses d'acquisition)
-- et tout suivi pluriannuel. L'indexation base 100 et le CAC se calculent dans
-- la matrice / le graphe Tagetik, à n'importe quelle maille.
-- =============================================================================
CREATE OR REPLACE VIEW V_TENDANCE AS
SELECT
    EXERCICE,
    ENTITY,                         -- campus (roule vers marque via la dim Entity)
    PROGRAMME,
    AN_ETUDE,
    MODALITE,
    SUM(VOL_LEAD)                                  AS LEADS,
    SUM(VOL_NEW)                                   AS INSCRITS,
    SUM(VOL_EFF * REV_STUD + VOL_NEW * REV_FRAIS_INS) AS CA,
    SUM(DEPENSE_ACQ)                               AS DEPENSE_ACQ,
    SUM(DEPENSE_MARQUE)                            AS DEPENSE_MARQUE
FROM AW_002_000002_000001
GROUP BY EXERCICE, ENTITY, PROGRAMME, AN_ETUDE, MODALITE;
