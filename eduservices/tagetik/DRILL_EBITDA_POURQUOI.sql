-- =============================================================================
-- DRILL « POURQUOI L'EBITDA DE CE CAMPUS A-T-IL REGRESSE ? »
--
-- A brancher comme requete de drill sur la cellule EBITDA du cockpit.
-- Le drill Tagetik execute cette requete en heritant du contexte de la cellule :
-- les parametres ci-dessous sont alimentes par les dimensions de la cellule.
--
--   :SCENARIO   <- dimension Scenario de la cellule        (ex. REEL)
--   :VERSION    <- dimension Version                       (ex. V_FINAL)
--   :PERIODE    <- dimension Periode                       (ex. 12)
--   :EXERCICE   <- dimension Exercice de la cellule        (ex. 2026)  [chaine]
--   :ENTITY     <- dimension Entity de la cellule          (ex. TUNON_PAR)
--
-- L'exercice compare est deduit : :EXERCICE - 1. Rien d'autre a saisir.
--
-- CE QUE LA REQUETE RENVOIE : un BRIDGE, pas un extrait de lignes.
--   EBITDA N-1  +  effet effectifs  +  effet prix/mix
--               -  effet cout variable unitaire  -  effet couts directs
--               =  EBITDA N
--
-- La decomposition est EXACTE par construction (verifiee : ecart nul sur
-- donnees aleatoires). Le total retombe toujours sur la cellule cliquee --
-- c'est la condition pour qu'un CFO fasse confiance au drill.
--
-- Algebre :
--   dCA   = dEFF x (CA/eleve)N-1 + d(CA/eleve) x EFF_N          (exact)
--   dCVAR = dEFF x (CVAR/eleve)N-1 + d(CVAR/eleve) x EFF_N      (exact)
--   dEBITDA = dCA - dCVAR - dCDIR
--           = dEFF x marge variable unitaire N-1                  <- effet effectifs
--           + d(CA/eleve) x EFF_N                                 <- effet prix / mix
--           - d(CVAR/eleve) x EFF_N                               <- effet cout variable
--           - dCDIR                                               <- effet couts directs
-- =============================================================================
WITH base AS (
    SELECT
        a.EXERCICE,
        SUM(a.VOL_EFF)                                        AS EFF,
        SUM(a.CA)                                             AS CA,
        SUM(a.COST_VARIABLE)                                  AS CVAR,
        SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE)  AS CDIR
    FROM V_ALLOCATION a
    WHERE a.SCENARIO = :SCENARIO
      AND a.VERSION  = :VERSION
      AND a.PERIODE  = :PERIODE
      AND a.ENTITY   = :ENTITY
      AND CAST(a.EXERCICE AS INTEGER) IN (CAST(:EXERCICE AS INTEGER), CAST(:EXERCICE AS INTEGER) - 1)
    GROUP BY a.EXERCICE
),
k AS (
    SELECT
        p.EFF AS EFF_P, n.EFF AS EFF_N,
        p.CA  AS CA_P,  n.CA  AS CA_N,
        p.CA - p.CVAR - p.CDIR                AS EB_P,
        n.CA - n.CVAR - n.CDIR                AS EB_N,
        1.0 * p.CA / NULLIF(p.EFF, 0)             AS CAE_P,
        1.0 * n.CA / NULLIF(n.EFF, 0)             AS CAE_N,
        1.0 * p.CVAR / NULLIF(p.EFF, 0)             AS CVE_P,
        1.0 * n.CVAR / NULLIF(n.EFF, 0)             AS CVE_N,
        p.CDIR AS CDIR_P, n.CDIR AS CDIR_N
    FROM      (SELECT * FROM base WHERE EXERCICE = :EXERCICE) n
    CROSS JOIN(SELECT * FROM base WHERE CAST(EXERCICE AS INTEGER) = CAST(:EXERCICE AS INTEGER) - 1) p
)
SELECT 1 AS ORDRE,
       'EBITDA ' + CAST(CAST(:EXERCICE AS INTEGER) - 1 AS VARCHAR(20)) AS ETAPE,
       ROUND(EB_P)                                    AS MONTANT,
       NULL                                           AS DETAIL,
       'point de depart'                              AS LECTURE
FROM k
UNION ALL
SELECT 2, 'Effet effectifs',
       ROUND((EFF_N - EFF_P) * (CAE_P - CVE_P)),
       CAST(EFF_P AS VARCHAR(20)) + ' -> ' + CAST(EFF_N AS VARCHAR(20)) + ' eleves',
       'volume, valorise a la marge variable ' + CAST(CAST(:EXERCICE AS INTEGER) - 1 AS VARCHAR(20))
FROM k
UNION ALL
SELECT 3, 'Effet prix / mix',
       ROUND((CAE_N - CAE_P) * EFF_N),
       CAST(ROUND(CAE_P) AS VARCHAR(20)) + ' -> ' + CAST(ROUND(CAE_N) AS VARCHAR(20)) + ' EUR / eleve',
       'CA par eleve : tarif, mix initiale/alternance, mix programmes'
FROM k
UNION ALL
SELECT 4, 'Effet cout variable unitaire',
       ROUND(-(CVE_N - CVE_P) * EFF_N),
       CAST(ROUND(CVE_P) AS VARCHAR(20)) + ' -> ' + CAST(ROUND(CVE_N) AS VARCHAR(20)) + ' EUR / eleve',
       'vacataires et achats directs, par eleve'
FROM k
UNION ALL
SELECT 5, 'Effet couts directs',
       ROUND(-(CDIR_N - CDIR_P)),
       CAST(ROUND(CDIR_P) AS VARCHAR(20)) + ' -> ' + CAST(ROUND(CDIR_N) AS VARCHAR(20)) + ' EUR',
       'permanents et structure du campus : ne suivent pas l activite'
FROM k
UNION ALL
SELECT 6, 'EBITDA ' + :EXERCICE,
       ROUND(EB_N),
       'marge ' + CAST(ROUND(100 * 1.0 * EB_N / NULLIF(CA_N, 0), 1) AS VARCHAR(20)) + ' %',
       'doit egaler la cellule cliquee'
FROM k
ORDER BY ORDRE
;
