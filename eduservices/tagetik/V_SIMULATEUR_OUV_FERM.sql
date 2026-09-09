-- =============================================================================
-- V_SIMULATEUR_OUV_FERM — le simulateur d'ouverture / fermeture, en une vue
-- SQL Server. Rend EXACTEMENT les colonnes du masque « 12_Simulateur », mais sur
-- les données réelles : V_ALLOCATION (2027, la version du POV) au lieu du modèle
-- illustratif.
--
-- LE PRINCIPE, qui est tout le sujet : fermer une classe ne fait pas disparaître
-- le fixe, il se RÉALLOUE. Deux poches, deux portées :
--
--   STRUCTURE_CAMPUS = permanents (6411) + structure du campus (613 · 615 · 616
--                      · 625 · 645 · 6413 · 63511). Celle des classes fermées se
--                      redistribue sur les survivantes DU MÊME CAMPUS.
--   SIEGE            = frais de marque (6236) + holding (6414 · 6226 · 626 ·
--                      6281 · 6331 · 6333). Celui des fermées se redistribue sur
--                      TOUTES les survivantes du groupe.
--
-- La redistribution suit le DRIVER, c'est-à-dire la clé ③ ALLOC_CAMP_CLASS telle
-- qu'elle est saisie dans le cadrage — REV_CA, VOL_EFF ou VOL_CLASS. Changez la
-- clé, et ce ne sont plus les mêmes classes qui paraissent déficitaires : c'est
-- la démonstration à faire devant le CFO.
--
-- LA DÉCISION se saisit dans le cube d'hypothèses AW_002_000001_000001 :
--   PARAMETRE = 'SIM_FERMER'   ENTITY = campus   KEY_ALLOC = 'PROG|AN|MOD'
--   MEASURE   = 1 pour fermer  (absent ou 0 = on garde)
-- Les cinq lecteurs du cube filtrent déjà sur ENTITY='GRP', HYP_PRICE_COEF ou
-- ALLOC_% : aucun ne voit ces lignes, le cadrage n'est pas touché.
--
-- SEULES LES ANNÉES D'ENTRÉE sont pilotables (B1 · M1 · BTS1). Une 2e ou 3e
-- année est une cohorte déjà inscrite : on ne la ferme pas, on la subit. La
-- colonne DECISION le dit ('cohorte') et la fermeture y est ignorée.
--
-- DEUX DRAPEAUX pour la synthèse, à sommer côté rapport :
--   DEFICIT_AVANT  la classe était déjà en déficit au coût complet
--   BASCULE        elle était saine AVANT et passe en déficit APRÈS, uniquement
--                  à cause d'une fermeture voisine. C'est le compteur d'effet
--                  domino, et c'est le chiffre qui fait taire la salle.
-- =============================================================================
CREATE OR ALTER VIEW V_SIMULATEUR_OUV_FERM AS
WITH
cle AS (        -- la clé ③ campus -> classe, dernière saisie (le cube est incrémental)
    SELECT MAX(CASE WHEN PARAMETRE = 'ALLOC_CAMP_CLASS' THEN KEY_ALLOC END) AS K3
    FROM (
        SELECT PARAMETRE, KEY_ALLOC,
               ROW_NUMBER() OVER (PARTITION BY PARAMETRE ORDER BY DATEUPD DESC) AS RN
        FROM AW_002_000001_000001
        WHERE PARAMETRE = 'ALLOC_CAMP_CLASS'
    ) z WHERE z.RN = 1
),
dec AS (        -- la décision de fermeture, une ligne par classe
    SELECT SCENARIO, ENTITY, KEY_ALLOC, SUM(MEASURE) AS FERMER
    FROM AW_002_000001_000001
    WHERE PARAMETRE = 'SIM_FERMER'
    GROUP BY SCENARIO, ENTITY, KEY_ALLOC
),
b AS (
    SELECT a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY, a.MARQUE,
        a.PROGRAMME, a.AN_ETUDE, a.MODALITE,
        a.VOL_EFF                                        AS EFFECTIF,
        a.VOL_CLASS                                      AS SECTIONS,
        a.CA,
        a.COST_VARIABLE                                  AS VARIABLE,
        (a.CA - a.COST_VARIABLE)                         AS CONTRIBUTION,
        (a.COST_PERM + a.COST_STRUCT)                    AS STRUCTURE_CAMPUS,
        a.COST_SIEGE                                     AS SIEGE,
        CASE WHEN a.AN_ETUDE IN ('B1','M1','BTS1') THEN 1 ELSE 0 END AS PILOTABLE,
        --  une fermeture n'est retenue que sur une année d'entrée
        CASE WHEN a.AN_ETUDE IN ('B1','M1','BTS1')
              AND COALESCE(d.FERMER, 0) >= 1 THEN 1 ELSE 0 END        AS FERMEE,
        CASE k.K3 WHEN 'REV_CA'  THEN a.CA
                  WHEN 'VOL_EFF' THEN a.VOL_EFF
                  ELSE a.VOL_CLASS END                   AS DRIVER,
        k.K3
    FROM V_ALLOCATION a
    CROSS JOIN cle k
    LEFT JOIN dec d ON d.SCENARIO = a.SCENARIO AND d.ENTITY = a.ENTITY
                   AND d.KEY_ALLOC = a.PROGRAMME + '|' + a.AN_ETUDE + '|' + a.MODALITE
    WHERE a.EXERCICE = '2027'
),
w AS (
    SELECT b.*,
        --  poches libérées par les fermetures, et assiette des survivantes
        SUM(CASE WHEN b.FERMEE = 1 THEN b.STRUCTURE_CAMPUS ELSE 0 END)
            OVER (PARTITION BY b.SCENARIO, b.VERSION, b.ENTITY)  AS POOL_CAMPUS,
        SUM(CASE WHEN b.FERMEE = 0 THEN b.DRIVER ELSE 0 END)
            OVER (PARTITION BY b.SCENARIO, b.VERSION, b.ENTITY)  AS SURV_CAMPUS,
        SUM(CASE WHEN b.FERMEE = 1 THEN b.SIEGE ELSE 0 END)
            OVER (PARTITION BY b.SCENARIO, b.VERSION)            AS POOL_SIEGE,
        SUM(CASE WHEN b.FERMEE = 0 THEN b.DRIVER ELSE 0 END)
            OVER (PARTITION BY b.SCENARIO, b.VERSION)            AS SURV_SIEGE
    FROM b
),
c AS (
    SELECT w.*,
        (w.STRUCTURE_CAMPUS + w.SIEGE)                                   AS STRUCTURE_ALLOUEE,
        (w.VARIABLE + w.STRUCTURE_CAMPUS + w.SIEGE)                      AS COUT_COMPLET,
        (w.CA - w.VARIABLE - w.STRUCTURE_CAMPUS - w.SIEGE)               AS MARGE_COMPLETE,
        CASE WHEN w.FERMEE = 1 THEN NULL ELSE
            w.STRUCTURE_CAMPUS + 1.0 * w.POOL_CAMPUS * w.DRIVER / NULLIF(w.SURV_CAMPUS, 0)
          + w.SIEGE            + 1.0 * w.POOL_SIEGE  * w.DRIVER / NULLIF(w.SURV_SIEGE,  0)
        END                                                              AS STRUCTURE_APRES
    FROM w
)
SELECT
    c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.ENTITY, c.MARQUE,
    --  la ville, en clair : ENTITY vaut MBWAY_PAR, on veut « Paris »
    CASE RIGHT(c.ENTITY, LEN(c.ENTITY) - CHARINDEX('_', c.ENTITY))
         WHEN 'PAR' THEN 'Paris'      WHEN 'LYO' THEN 'Lyon'
         WHEN 'NAN' THEN 'Nantes'     WHEN 'BOR' THEN 'Bordeaux'
         WHEN 'LIL' THEN 'Lille'      WHEN 'TLS' THEN 'Toulouse'
         WHEN 'REN' THEN 'Rennes'     WHEN 'MTP' THEN 'Montpellier'
         ELSE RIGHT(c.ENTITY, LEN(c.ENTITY) - CHARINDEX('_', c.ENTITY)) END AS VILLE,
    CASE c.PROGRAMME
         WHEN 'BAC_MGT' THEN 'Bachelor Management'   WHEN 'MAS_MGT' THEN 'Mastère Management'
         WHEN 'BAC_COM' THEN 'Bachelor Communication' WHEN 'MAS_COM' THEN 'Mastère Communication'
         WHEN 'BAC_CCE' THEN 'Bachelor Commerce'     WHEN 'BAC_RH'  THEN 'Bachelor Ressources humaines'
         WHEN 'BAC_TOU' THEN 'Bachelor Tourisme'     WHEN 'BTS_GES' THEN 'BTS Gestion'
         ELSE c.PROGRAMME END                                            AS PROGRAMME_LIB,
    c.PROGRAMME, c.AN_ETUDE AS NIVEAU, c.MODALITE,
    c.EFFECTIF, c.SECTIONS, c.CA, c.VARIABLE, c.CONTRIBUTION,
    c.STRUCTURE_ALLOUEE, c.COUT_COMPLET, c.MARGE_COMPLETE,
    --  point mort : combien d'étudiants pour que la contribution couvre la
    --  structure allouée. NULL quand la contribution est nulle ou négative.
    CASE WHEN c.CONTRIBUTION > 0
         THEN CEILING(1.0 * c.STRUCTURE_ALLOUEE / c.CONTRIBUTION * c.EFFECTIF)
         END                                                             AS POINT_MORT,
    CASE WHEN c.CONTRIBUTION > 0
         THEN 1 - 1.0 * c.STRUCTURE_ALLOUEE / c.CONTRIBUTION
         END                                                             AS MARGE_SECURITE,
    CASE WHEN c.PILOTABLE = 0 THEN 'cohorte'
         WHEN c.FERMEE = 1    THEN 'Fermer'
         ELSE 'Garder' END                                               AS DECISION,
    c.STRUCTURE_APRES,
    CASE WHEN c.FERMEE = 1 THEN NULL
         ELSE c.CA - c.VARIABLE - c.STRUCTURE_APRES END                  AS MARGE_COMPLETE_APRES,
    CASE WHEN c.FERMEE = 1 THEN -c.CONTRIBUTION ELSE 0 END               AS IMPACT_EBITDA,
    --  les deux drapeaux de la synthèse
    CASE WHEN c.MARGE_COMPLETE < 0 THEN 1 ELSE 0 END                     AS DEFICIT_AVANT,
    CASE WHEN c.FERMEE = 0 AND c.MARGE_COMPLETE >= 0
              AND (c.CA - c.VARIABLE - c.STRUCTURE_APRES) < 0
         THEN 1 ELSE 0 END                                               AS BASCULE,
    --  la lecture, écrite par la vue : le rapport n'a plus qu'à l'afficher
    CASE
      WHEN c.FERMEE = 1 THEN 'Fermer = perdre ' + FORMAT(c.CONTRIBUTION, 'N0')
           + ' EUR de contribution. Le fixe, lui, reste.'
      WHEN c.PILOTABLE = 0 THEN 'Cohorte deja inscrite : non pilotable cette annee.'
      WHEN c.MARGE_COMPLETE >= 0 AND (c.CA - c.VARIABLE - c.STRUCTURE_APRES) < 0
           THEN 'BASCULE : saine avant, en deficit a cause d une fermeture voisine.'
      WHEN c.MARGE_COMPLETE < 0 AND c.CONTRIBUTION > 0
           THEN 'Deficit au cout complet mais contribution POSITIVE : ne pas fermer, c est un artefact d allocation.'
      WHEN c.MARGE_COMPLETE < 0 THEN 'Contribution negative : vrai point dur.'
      ELSE 'Rentable. Point mort '
           + FORMAT(CEILING(1.0 * c.STRUCTURE_ALLOUEE / c.CONTRIBUTION * c.EFFECTIF), 'N0')
           + ' etudiants, marge de securite '
           + FORMAT(1 - 1.0 * c.STRUCTURE_ALLOUEE / c.CONTRIBUTION, 'P0') + '.'
    END                                                                  AS LECTURE,
    c.K3                                                                 AS CLE_ALLOCATION,
    c.DRIVER
FROM c
