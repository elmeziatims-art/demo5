-- =============================================================================
-- V_CAMPUS_CLASSE — la vue qui alimente le COCKPIT DIRECTEUR DE CAMPUS
-- Wrapper mince sur V_ALLOCATION (grain classe) + capacité / remplissage /
-- contribution / point mort. Une seule vue à lire pour le masque campus.
--
-- Grain : SCENARIO × VERSION × PERIODE × EXERCICE × ENTITY × MARQUE
--         × PROGRAMME × AN_ETUDE × MODALITE   (= une classe-cohorte)
--
-- Capacité par cycle (paramétrable) : BAC 32 · MAS 26 · BTS 30.
-- Contribution = CA − COST_VARIABLE  (coûts ÉVITABLES si on ferme :
--   vacataires + achats directs ; les permanents et la structure restent).
-- Point mort (élèves) = coût complet d'UNE classe ÷ marge variable par élève
--   = seuil de « bonne santé » (couvrir le coût complet chargé).
-- =============================================================================
CREATE OR ALTER VIEW V_CAMPUS_CLASSE AS
SELECT
    a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE,
    a.ENTITY, a.MARQUE, a.PROGRAMME, a.AN_ETUDE, a.MODALITE,
    a.VOL_EFF,
    a.VOL_CLASS,
    a.VOL_NEW,
    a.CA,
    CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
         WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
         ELSE 30 END                                                    AS CAPACITE,
    a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                       WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                       ELSE 30 END                                      AS PLACES,
    1.0 * a.VOL_EFF / NULLIF(a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                                  WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                                  ELSE 30 END, 0)                       AS REMPLISSAGE,
    a.COST_VARIABLE,
    (a.CA - a.COST_VARIABLE)                                            AS CONTRIBUTION,
    a.COST_COMPLET,
    a.MARGE_COMPLETE,
    a.COST_SIEGE,
    -- point mort (élèves) = coût complet d'une classe / marge variable par élève
    1.0 * (1.0 * a.COST_COMPLET / NULLIF(a.VOL_CLASS, 0)) / NULLIF((a.CA - a.COST_VARIABLE) / NULLIF(a.VOL_EFF, 0), 0)      AS POINT_MORT
FROM V_ALLOCATION a
;
