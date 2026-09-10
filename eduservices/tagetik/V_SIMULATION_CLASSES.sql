-- =============================================================================
-- V_SIMULATION_CLASSES — la base du masque OUVERTURE / FERMETURE DE GROUPE
-- SQL Server. Wrapper mince sur V_CAMPUS_CLASSE, exactement comme celle-ci est
-- un wrapper mince sur V_ALLOCATION. Ajoute V_CAMPAGNES pour le CAC marginal
-- et V_MOTEUR pour le prix.
--
-- CE QU'ELLE NE REFAIT PAS. La capacité (BAC 32 · MAS 26 · BTS 30), les PLACES,
-- le REMPLISSAGE, la CONTRIBUTION et le POINT MORT sont déjà définis dans
-- V_CAMPUS_CLASSE, qui alimente le cockpit directeur et le drill. Les redéfinir
-- ici créerait deux vérités qui divergeraient au premier changement de norme.
--
-- CE QU'ELLE AJOUTE, ET RIEN D'AUTRE
--   SUREFFECTIF / PLACES_VIDES  l'écart entre l'effectif que le cadrage a
--                               construit et les places réellement ouvertes.
--                               Le top-down ne plafonne pas : il sort 86,7
--                               étudiants en M1 chez MBway Paris pour 78 places.
--   VAC_GROUPE   (621)          ce qu'un groupe de plus ou de moins emporte
--   PERM_GROUPE  (6411)         ce qu'il emporterait SI on décidait de le
--                               supprimer — par défaut il reste
--   CONSO_ELEVE  (604 + 6063)   le vrai coût marginal d'un élève de plus.
--                               Le 6231 en est exclu : le CAC marginal le porte
--                               déjà, l'y remettre compterait l'acquisition
--                               deux fois — même règle que le masque du moteur.
--   COST_RECRUT  (6231)         isolé, pour pouvoir le montrer sans le compter
--   CAC_MARGINAL                CPL / (rendement × conversion), de V_CAMPAGNES
--   PRIX                        de V_MOTEUR, pour valoriser un élève de plus
-- =============================================================================
CREATE OR ALTER VIEW V_SIMULATION_CLASSES AS
WITH
c AS (
    SELECT k.*,
        SUM(k.VOL_EFF) OVER (PARTITION BY k.SCENARIO, k.VERSION, k.EXERCICE, k.ENTITY)
                                                                    AS EFF_CAMPUS
    FROM V_CAMPUS_CLASSE k
    WHERE k.EXERCICE = '2027'
)
SELECT
    c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.ENTITY, c.MARQUE,
    c.PROGRAMME, c.AN_ETUDE, c.MODALITE,
    CASE WHEN c.AN_ETUDE IN ('B1','M1','BTS1') THEN 1 ELSE 0 END     AS IS_ENTREE,
    c.VOL_CLASS                                                      AS GROUPES,
    c.CAPACITE, c.PLACES,
    c.VOL_EFF                                                        AS EFFECTIF,
    c.VOL_NEW                                                        AS NOUVEAUX,
    c.REMPLISSAGE, c.POINT_MORT,
    1.0 * c.VOL_EFF / NULLIF(c.VOL_CLASS, 0)                         AS EFFECTIF_PAR_GROUPE,
    CASE WHEN c.VOL_EFF > c.PLACES THEN c.VOL_EFF - c.PLACES ELSE 0 END AS SUREFFECTIF,
    CASE WHEN c.PLACES > c.VOL_EFF THEN c.PLACES - c.VOL_EFF ELSE 0 END AS PLACES_VIDES,
    COALESCE(m.PRIX, 0)                                              AS PRIX,
    c.CA, c.CONTRIBUTION, c.MARGE_COMPLETE, c.COST_COMPLET, c.COST_VARIABLE,
    -- tout ce qui ne part PAS avec le groupe, en un seul montant
    (c.COST_PERM + c.COST_STRUCT + c.COST_MARQUE + c.COST_HOLDING)   AS COST_STRUCTURE,
    c.COST_VAC, c.COST_ODIR, c.COST_PERM, c.COST_STRUCT,
    c.COST_MARQUE, c.COST_HOLDING, c.COST_SIEGE,
    -- ---- coûts unitaires : de quoi chiffrer un groupe de plus ou de moins ----
    1.0 * c.COST_VAC  / NULLIF(c.VOL_CLASS, 0)                       AS VAC_GROUPE,
    1.0 * c.COST_PERM / NULLIF(c.VOL_CLASS, 0)                       AS PERM_GROUPE,
    1.0 * c.COST_ODIR / NULLIF(c.VOL_EFF, 0)                         AS ODIR_ELEVE,
    1.0 * c.POOL_ODIR / NULLIF(c.EFF_CAMPUS, 0)                      AS CONSO_ELEVE,
    (c.COST_ODIR - 1.0 * c.POOL_ODIR * c.VOL_EFF / NULLIF(c.EFF_CAMPUS, 0)) AS COST_RECRUT,
    COALESCE(cm.CAC_MARGINAL, 0)                                     AS CAC_MARGINAL
FROM c
LEFT JOIN V_MOTEUR m
       ON m.SCENARIO = c.SCENARIO AND m.VERSION = c.VERSION AND m.ENTITY = c.ENTITY
      AND m.PROGRAMME = c.PROGRAMME AND m.AN_ETUDE = c.AN_ETUDE AND m.MODALITE = c.MODALITE
LEFT JOIN V_CAMPAGNES cm
       ON cm.SCENARIO = c.SCENARIO AND cm.ENTITY = c.ENTITY
