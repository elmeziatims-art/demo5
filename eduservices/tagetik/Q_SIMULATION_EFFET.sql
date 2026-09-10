-- =============================================================================
-- Q_SIMULATION_EFFET — restitution de la simulation saisie dans Tagetik
-- Ce que le CFO relit apres que les campus ont ouvert et ferme leurs groupes.
-- Contraintes loader : pas de CTE, pas de ORDER BY, pas de ';', alias entre
-- guillemets doubles, pas d'accent dans les libelles.
-- =============================================================================
SELECT
    s.ENTITY                        AS "CAMPUS",
    s.MARQUE                        AS "MARQUE",
    s.PROGRAMME                     AS "PROGRAMME",
    s.AN_ETUDE                      AS "ANNEE",
    s.MODALITE                      AS "MODALITE",
    s.GROUPES                       AS "GROUPES CADRAGE",
    s.D_GROUPES                     AS "GROUPES OUVERTS OU FERMES",
    s.GROUPES_APRES                 AS "GROUPES APRES",
    s.PLACES                        AS "PLACES",
    s.PLACES_APRES                  AS "PLACES APRES",
    s.EFFECTIF                      AS "EFFECTIF CONSTRUIT",
    s.EFF_PLACABLE                  AS "EFFECTIF PLACABLE",
    s.D_ELEVES                      AS "ETUDIANTS RECRUTES",
    s.EFF_RETENU                    AS "EFFECTIF RETENU",
    s.CA                            AS "CA CONSTRUIT",
    s.MARGE_COMPLETE                AS "MARGE COMPLETE",
    s.EBITDA_NON_LIVRABLE           AS "EBITDA NON LIVRABLE FAUTE DE PLACES",
    s.DELTA_CA                      AS "DELTA CA",
    s.DELTA_VACATAIRES              AS "DELTA VACATAIRES",
    s.DELTA_CONSO                   AS "DELTA ACHATS ET FOURNITURES",
    s.COUT_ACQUISITION              AS "COUT D ACQUISITION",
    s.ECONOMIE_PERM                 AS "PERMANENTS SUPPRIMES",
    s.ECONOMIE_STRUCT               AS "STRUCTURE SUPPRIMEE",
    s.DELTA_COUT                    AS "DELTA COUTS",
    s.DELTA_EBITDA                  AS "DELTA EBITDA"
FROM V_SIMULATION_SAISIE s
WHERE s.SCENARIO = '2027BUD_V1' AND s.VERSION = 'V01'
