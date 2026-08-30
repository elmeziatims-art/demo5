-- =============================================================================
-- Q_RAPPORT_ALLOUE — datasource du rapport "choc de l'allocation" (avant / après)
-- DYNAMIQUE : lit V_ALLOCATION (qui lit elle-même tes clés KEY_ALLOC du cadrage).
-- Tagetik fait le pli/dépli sur les dimensions ; ici on ne fait qu'exposer les
-- mesures dans la forme avant/après. Aucune allocation recodée : tout vient de la vue.
--
-- Mapping des mesures (depuis les colonnes de V_ALLOCATION) :
--   EBITDA propre (avant siège) = MARGE_COMPLETE + COST_SIEGE
--   Quote-part siège            = COST_SIEGE            (= COST_MARQUE + COST_HOLDING)
--   EBITDA net (après)          = MARGE_COMPLETE
--   Δ points                    = calculé côté rapport (net% − propre%)
--
-- Grain : ENTITY x MARQUE x PROGRAMME x AN_ETUDE x MODALITE (la maille de la vue).
-- Millésime : filtre EXERCICE / VERSION au masque (ex. 2026 réel = VERSION 'ACT').
-- =============================================================================
SELECT
    EXERCICE, VERSION, ENTITY, MARQUE, PROGRAMME, AN_ETUDE, MODALITE,
    VOL_EFF                              AS "Effectif",
    CA                                   AS "CA",
    (MARGE_COMPLETE + COST_SIEGE)        AS "EBITDA propre",
    COST_SIEGE                           AS "Quote-part siège",
    MARGE_COMPLETE                       AS "EBITDA net",
    -- décomposition du siège si on veut détailler la refacturation :
    COST_MARQUE                          AS "dont marketing marque",
    COST_HOLDING                         AS "dont holding"
FROM V_ALLOCATION
WHERE VERSION = ${$ANL_VERSION.code}     -- ex. 'ACT' pour le réel
  AND EXERCICE IN (${$ANL_EXERCICE.code})
-- Tagetik agrège/plie sur MARQUE -> ENTITY -> PROGRAMME -> AN_ETUDE -> MODALITE.
-- Marge % (propre & nette) et Δ pt = membres calculés du rapport (mesure / CA).
;
