-- =============================================================================
-- Q_MOTEUR_COEFFS — restitution des coefficients du moteur, DEPUIS LA VUE
-- Lit V_CAMPAGNES : la brique que V_MOTEUR (le cadrage) utilise lui-même.
-- => les valeurs affichées sont EXACTEMENT celles qui pilotent la simulation,
--    aucune formule Excel reproduite (pas de LN recalculé à côté qui pourrait
--    diverger). « Sous le capot » = la vérité du moteur, pas une copie.
-- Grain : par campus (ENTITY). Agréger côté rapport pour le niveau marque/groupe.
-- =============================================================================
SELECT
    ENTITY                                  AS "Campus",
    REND_ACQ                                AS "Élasticité acquisition",
    REND_BRAND                              AS "Élasticité marque",
    CPL                                     AS "Coût par lead (€)",
    CONVERSION                              AS "Conversion lead→inscrit",
    CAC_MARGINAL                            AS "CAC marginal (€)",
    PART_ORG                                AS "Part organique",
    LEAD_REF                                AS "Leads réf.",
    PAID_REF                                AS "dont payants",
    ORG_REF                                 AS "dont organiques",
    SPEND_ACQ_REF                           AS "Budget acquisition (€)",
    SPEND_BRAND_REF                         AS "Budget marque (€)"
FROM V_CAMPAGNES
ORDER BY ENTITY;
