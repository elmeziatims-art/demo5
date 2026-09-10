-- Arbitrage du budget d'acquisition : 3 caps proposes + cap retenu, par campus.
-- Chaque cap = budget de reference x coefficient de la logique correspondante.
CREATE OR ALTER VIEW V_CAP_ARBITRAGE AS
SELECT ENTITY AS CAMPUS, SUBSTR_BEFORE(ENTITY,'_') AS MARQUE,
    CAC_MARGINAL,
    BUDGET_ACQ_REF                    AS BUDGET_REFERENCE,
    BUDGET_ACQ_REF * CAP_EFF          AS CAP_EFFICIENT,   -- pilote par le CAC marginal
    BUDGET_ACQ_REF * CAP_MOM          AS CAP_MOMENTUM,    -- pilote par la croissance des leads
    BUDGET_ACQ_REF * CAP_POT          AS CAP_POTENTIEL,   -- pilote par l'intensite marche
    BUDGET_ACQ_REF * CAP_RETENU       AS CAP_RETENU       -- saisie : l'arbitrage du DAF
FROM AW_002_000008_000002;
