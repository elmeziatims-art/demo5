-- =============================================================================
-- V_SIMULATION_CLASSES — la base du masque OUVERTURE / FERMETURE DE CLASSE
-- SQL Server. Appelle : V_MOTEUR (effectif, prix, CA construits par le top-down)
--                     · V_ALLOCATION (coût complet de la classe, poste par poste)
--                     · V_CAMPAGNES (CAC marginal = coût du prochain inscrit)
--
-- POURQUOI CETTE VUE
--   Le cadrage top-down projette un effectif SANS PLAFOND DE CAPACITÉ : il peut
--   sortir 86,7 étudiants dans un cursus qui n'a que 78 places (MBWAY Paris M1).
--   Symétriquement il maintient des groupes à 53 % de remplissage.
--   Cette vue confronte, classe par classe, l'effectif construit à la capacité
--   réellement ouverte, et donne les coûts UNITAIRES qui permettent de chiffrer
--   un groupe en plus ou en moins.
--
-- CAPACITÉ (norme pédagogique, surchargeable dans le masque)
--   BTS 30 · Bachelor 32 · Mastère 26 places par groupe.
--   GROUPES = VOL_CLASS du socle (structure figée du cadrage).
--
-- CE QUI BOUGE QUAND UN GROUPE S'OUVRE OU SE FERME
--   VAC_GROUPE  (621 vacataires)      part / arrive avec le groupe   -> variable
--   ODIR_ELEVE  (604, 6063, 6231)     suit l'effectif                -> variable
--   PERM_GROUPE (6411 permanents)     RESTE, sauf décision RH explicite
--   STRUCT, MARQUE, SIÈGE             RESTENT et se réallouent sur les survivants
--   CAC_MARGINAL                      à payer si on veut REMPLIR une place de plus
-- =============================================================================
CREATE OR ALTER VIEW V_SIMULATION_CLASSES AS
WITH
cap AS (   -- la norme de places par groupe
    SELECT a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY, a.MARQUE,
        a.PROGRAMME, a.AN_ETUDE, a.MODALITE,
        a.VOL_EFF, a.VOL_CLASS, a.CA,
        a.COST_VAC, a.COST_ODIR, a.COST_PERM, a.COST_STRUCT, a.COST_SIEGE,
        a.COST_VARIABLE, a.COST_STRUCTURE, a.COST_COMPLET, a.MARGE_COMPLETE, a.VOL_NEW,
        a.COST_MARQUE, a.COST_HOLDING, a.POOL_ODIR,
        SUM(a.VOL_EFF) OVER (PARTITION BY a.SCENARIO, a.VERSION, a.ENTITY) AS EFF_CAMPUS,
        CASE WHEN a.AN_ETUDE LIKE 'BTS%' THEN 30
             WHEN a.AN_ETUDE LIKE 'M%'   THEN 26
             ELSE 32 END AS CAPACITE
    FROM V_ALLOCATION a
    WHERE a.EXERCICE = '2027'
)
SELECT
    c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.ENTITY, c.MARQUE,
    c.PROGRAMME, c.AN_ETUDE, c.MODALITE,
    CASE WHEN c.AN_ETUDE IN ('B1','M1','BTS1') THEN 1 ELSE 0 END AS IS_ENTREE,
    c.VOL_CLASS                            AS GROUPES,
    c.CAPACITE,
    c.VOL_CLASS * c.CAPACITE               AS PLACES,
    c.VOL_EFF                              AS EFFECTIF,
    c.VOL_NEW                               AS NOUVEAUX,
    -- ce que le top-down a construit au-delà de ce qui est ouvert (0 si la place existe)
    CASE WHEN c.VOL_EFF > c.VOL_CLASS * c.CAPACITE
         THEN c.VOL_EFF - c.VOL_CLASS * c.CAPACITE ELSE 0 END AS SUREFFECTIF,
    CASE WHEN c.VOL_CLASS * c.CAPACITE > c.VOL_EFF
         THEN c.VOL_CLASS * c.CAPACITE - c.VOL_EFF ELSE 0 END AS PLACES_VIDES,
    1.0 * c.VOL_EFF / NULLIF(c.VOL_CLASS * c.CAPACITE, 0) AS REMPLISSAGE,
    COALESCE(m.PRIX, 0)                    AS PRIX,
    c.CA,
    c.COST_VAC, c.COST_ODIR, c.COST_PERM, c.COST_STRUCT, c.COST_SIEGE,
    c.COST_VARIABLE, c.COST_STRUCTURE, c.COST_COMPLET, c.MARGE_COMPLETE,
    (c.CA - c.COST_VARIABLE)               AS CONTRIBUTION,
    -- ---- coûts unitaires : de quoi chiffrer un groupe de plus ou de moins ----
    1.0 * c.COST_VAC  / NULLIF(c.VOL_CLASS, 0) AS VAC_GROUPE,
    1.0 * c.COST_PERM / NULLIF(c.VOL_CLASS, 0) AS PERM_GROUPE,
    1.0 * c.COST_ODIR / NULLIF(c.VOL_EFF,   0) AS ODIR_ELEVE,
    -- consommables SEULS (604 + 6063) : le vrai coût marginal d'un élève de plus.
    -- Le 6231 (recrutement) en est exclu : il est déjà porté par le CAC marginal,
    -- l'y remettre compterait l'acquisition deux fois.
    1.0 * c.POOL_ODIR / NULLIF(c.EFF_CAMPUS, 0) AS CONSO_ELEVE,
    (c.COST_ODIR - 1.0 * c.POOL_ODIR * c.VOL_EFF / NULLIF(c.EFF_CAMPUS, 0)) AS COST_RECRUT,
    c.COST_MARQUE, c.COST_HOLDING,
    COALESCE(cm.CAC_MARGINAL, 0)           AS CAC_MARGINAL
FROM cap c
LEFT JOIN V_MOTEUR m
       ON m.SCENARIO = c.SCENARIO AND m.VERSION = c.VERSION AND m.ENTITY = c.ENTITY
      AND m.PROGRAMME = c.PROGRAMME AND m.AN_ETUDE = c.AN_ETUDE AND m.MODALITE = c.MODALITE
LEFT JOIN V_CAMPAGNES cm
       ON cm.SCENARIO = c.SCENARIO AND cm.ENTITY = c.ENTITY
