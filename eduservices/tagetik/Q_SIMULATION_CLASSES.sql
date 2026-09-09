-- =============================================================================
-- Q_SIMULATION_CLASSES — requête du masque OUVERTURE / FERMETURE DE CLASSE
-- Alimente l'onglet Donnees de SIMULATION_CLASSES.xlsx (60 lignes par version).
-- Contraintes loader Tagetik respectées : pas de CTE, pas de ORDER BY, pas de ';',
-- alias entre guillemets doubles, pas d'accent dans les libellés.
-- Le POV se fait sur SCENARIO / VERSION (paramètres du rapport).
-- =============================================================================
SELECT
    s.ENTITY                                        AS "CAMPUS",
    s.MARQUE                                        AS "MARQUE",
    s.PROGRAMME                                     AS "PROGRAMME",
    s.AN_ETUDE                                      AS "ANNEE",
    s.MODALITE                                      AS "MODALITE",
    s.ENTITY + '|' + s.PROGRAMME + '|' + s.AN_ETUDE + '|' + s.MODALITE AS "CLE",
    s.IS_ENTREE                                     AS "ENTREE",
    s.GROUPES                                       AS "GROUPES",
    s.CAPACITE                                      AS "CAPACITE",
    s.PLACES                                        AS "PLACES",
    s.EFFECTIF                                      AS "EFFECTIF",
    s.NOUVEAUX                                      AS "NOUVEAUX",
    s.SUREFFECTIF                                   AS "SUREFFECTIF",
    s.PLACES_VIDES                                  AS "PLACES VIDES",
    s.REMPLISSAGE                                   AS "REMPLISSAGE",
    s.PRIX                                          AS "PRIX MOYEN",
    s.CA                                            AS "CA",
    s.COST_VAC                                      AS "VACATAIRES",
    s.COST_ODIR                                     AS "AUTRES DIRECTS",
    s.COST_PERM                                     AS "PERMANENTS",
    s.COST_STRUCT                                   AS "STRUCTURE CAMPUS",
    s.COST_VARIABLE                                 AS "COUT VARIABLE",
    s.COST_STRUCTURE                                AS "COUT DE STRUCTURE",
    s.COST_COMPLET                                  AS "COUT COMPLET",
    s.MARGE_COMPLETE                                AS "MARGE COMPLETE",
    s.CONTRIBUTION                                  AS "CONTRIBUTION",
    s.VAC_GROUPE                                    AS "VACATAIRES PAR GROUPE",
    s.PERM_GROUPE                                   AS "PERMANENTS PAR GROUPE",
    s.ODIR_ELEVE                                    AS "AUTRES DIRECTS PAR ELEVE",
    s.CONSO_ELEVE                                   AS "CONSOMMABLES PAR ELEVE",
    s.COST_RECRUT                                   AS "RECRUTEMENT",
    s.COST_MARQUE                                   AS "FRAIS DE MARQUE",
    s.COST_HOLDING                                  AS "SIEGE",
    s.CAC_MARGINAL                                  AS "COUT DU PROCHAIN INSCRIT"
FROM V_SIMULATION_CLASSES s
WHERE s.SCENARIO = '2027BUD_V1' AND s.VERSION = 'V01'
