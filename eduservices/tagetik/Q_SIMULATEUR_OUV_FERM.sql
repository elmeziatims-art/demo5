-- =============================================================================
-- Q_SIMULATEUR_OUV_FERM — la restitution du simulateur ouverture / fermeture
-- Rend les memes colonnes que le masque 12_Simulateur, sur les donnees reelles.
-- Contraintes loader Tagetik : pas de CTE, pas de ORDER BY, pas de ';', alias
-- entre guillemets doubles, pas d'accent dans les libelles.
--
-- SYNTHESE cote rapport, par simple somme des colonnes :
--   Delta EBITDA                  = SOMME(IMPACT EBITDA)
--   Classes fermees               = NB.SI(DECISION ; "Fermer")
--   Deficits au cout complet      = SOMME(DEFICIT AVANT)
--   Bascules provoquees (domino)  = SOMME(BASCULE)
-- =============================================================================
SELECT
    s.MARQUE                      AS "MARQUE",
    s.VILLE                       AS "VILLE",
    s.PROGRAMME_LIB               AS "PROGRAMME",
    s.NIVEAU                      AS "NIVEAU",
    s.MODALITE                    AS "MODALITE",
    s.ENTITY                      AS "CAMPUS",
    s.PROGRAMME                   AS "CODE PROGRAMME",
    s.EFFECTIF                    AS "EFFECTIF",
    s.SECTIONS                    AS "SECTIONS",
    s.CA                          AS "CA",
    s.VARIABLE                    AS "VARIABLE",
    s.CONTRIBUTION                AS "CONTRIBUTION",
    s.STRUCTURE_ALLOUEE           AS "STRUCTURE ALLOUEE",
    s.COUT_COMPLET                AS "COUT COMPLET",
    s.MARGE_COMPLETE              AS "MARGE COMPLETE",
    s.POINT_MORT                  AS "POINT MORT",
    s.MARGE_SECURITE              AS "MARGE DE SECURITE",
    s.DECISION                    AS "DECISION",
    s.STRUCTURE_APRES             AS "STRUCTURE APRES",
    s.MARGE_COMPLETE_APRES        AS "MARGE COMPLETE APRES",
    s.IMPACT_EBITDA               AS "IMPACT EBITDA",
    s.DEFICIT_AVANT               AS "DEFICIT AVANT",
    s.BASCULE                     AS "BASCULE",
    s.LECTURE                     AS "LECTURE",
    s.CLE_ALLOCATION              AS "CLE ALLOCATION"
FROM V_SIMULATEUR_OUV_FERM s
WHERE s.SCENARIO = '2027BUD_V1' AND s.VERSION = 'V01'
