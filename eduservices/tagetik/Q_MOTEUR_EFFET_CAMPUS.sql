-- =============================================================================
-- Q_MOTEUR_EFFET_CAMPUS — effet marginal d'un +Δ% (acquisition + marque) par campus
-- Source : V_CAMPAGNES (élasticités, réfs, conversion) + socle pour le CA/inscrit réel.
-- Δ acquisition = 8 %, Δ marque = 10 % (remplacer par des paramètres Tagetik au besoin).
-- Coût variable/élève = 300 (hypothèse marginale). Aucune nouvelle vue.
-- =============================================================================
SELECT
    cp.ENTITY                                                   AS CAMPUS,
    cp.SPEND_ACQ_REF * 0.08                                     AS DELTA_BUDGET_ACQ,
    cp.PAID_REF * (POWER(1.08, cp.REND_ACQ) - 1)                AS LEADS_GAGNES_ACQ,
    cp.ORG_REF  * (POWER(1.10, cp.REND_BRAND) - 1)              AS LEADS_GAGNES_ORG,
    ( cp.PAID_REF * (POWER(1.08, cp.REND_ACQ) - 1)
    + cp.ORG_REF  * (POWER(1.10, cp.REND_BRAND) - 1) ) * cp.CONVERSION   AS INSCRITS_GAGNES,
    ( ( cp.PAID_REF * (POWER(1.08, cp.REND_ACQ) - 1)
      + cp.ORG_REF  * (POWER(1.10, cp.REND_BRAND) - 1) ) * cp.CONVERSION ) * pn.CA_PAR_INSCRIT   AS CA_GAGNE,
    -- EBITDA 1re année = CA gagné − budget dépensé − coût variable (300/élève)
    ( ( cp.PAID_REF * (POWER(1.08, cp.REND_ACQ) - 1)
      + cp.ORG_REF  * (POWER(1.10, cp.REND_BRAND) - 1) ) * cp.CONVERSION ) * pn.CA_PAR_INSCRIT
      - cp.SPEND_ACQ_REF * 0.08
      - ( cp.PAID_REF * (POWER(1.08, cp.REND_ACQ) - 1)
        + cp.ORG_REF  * (POWER(1.10, cp.REND_BRAND) - 1) ) * cp.CONVERSION * 300   AS EBITDA_1RE_ANNEE,
    -- CAC marginal = budget dépensé ÷ inscrits gagnés
    1.0 * ( cp.SPEND_ACQ_REF * 0.08 ) / NULLIF(( cp.PAID_REF * (POWER(1.08, cp.REND_ACQ) - 1)
               + cp.ORG_REF  * (POWER(1.10, cp.REND_BRAND) - 1) ) * cp.CONVERSION, 0)           AS CAC_MARGINAL_GESTE
FROM V_CAMPAGNES cp
JOIN (
    SELECT ENTITY,
           1.0 * SUM(VOL_NEW * REV_STUD + VOL_NEW * REV_FRAIS_INS) / NULLIF(SUM(VOL_NEW),0) AS CA_PAR_INSCRIT
    FROM AW_002_000002_000001
    WHERE n.EXERCICE = '2026'
    GROUP BY ENTITY
) pn ON pn.ENTITY = cp.ENTITY
ORDER BY cp.ENTITY;
