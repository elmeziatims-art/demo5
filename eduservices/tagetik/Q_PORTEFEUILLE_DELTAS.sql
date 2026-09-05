/* =============================================================================
   Q_PORTEFEUILLE_DELTAS  —  SQL SERVER (T-SQL)
   Δ CA · Δ EBITDA · Δ marge · Remplissage · Mix alternance,
   directement en colonnes, justes a chaque niveau.

   Une ligne par CAMPUS : ENTITY ne contient que des elements finaux.
   Le ratio d'un noeud est reparti sur ses feuilles (divise par le nombre de
   campus du noeud) : en sommant, Tagetik reconstitue exactement sa valeur.

   Suffixes :  _C = campus   _M = niveau marque   _G = niveau groupe

   FORMULE DE RAPPORT, une par colonne affichee :
       D CA = IF(NB_G = 1 ; CA_VAR_G ;
              IF(NB_M = 1 ; CA_VAR_M ;
              IF(NB   = 1 ; CA_VAR_C ; "")))
   L'ordre compte : au niveau groupe NB_G vaut 1 ET NB_M vaut 5.
   Le "" final laisse la cellule vide si le perimetre n'est pas un noeud.

   A SAVOIR : ces cinq ratios se calculent aussi, et plus surement, par une
   simple division des mesures additives -- CA / CA_N1 - 1, EFFECTIFS / PLACES,
   EFFECTIFS_ALT / EFFECTIFS. Cette forme-la est juste sur N'IMPORTE QUEL
   perimetre, y compris un sous-ensemble choisi a la main. Les triplets
   ci-dessous apportent le confort, pas la justesse.

   Ne depend que de V_ALLOCATION et de AW_002_000002_000001.
   ============================================================================= */
WITH cls AS (
    SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
            a.VOL_EFF, a.VOL_NEW, a.CA, a.COST_COMPLET, a.COST_SIEGE,
            CASE WHEN a.MODALITE = 'ALT' THEN a.VOL_EFF ELSE 0 END  AS VOL_EFF_ALT,
            a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                               WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                               ELSE 30 END                          AS PLACES
    FROM    V_ALLOCATION AS a
),
camp AS (
    SELECT  c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY,
            SUM(c.CA)                                  AS CA,
            SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE)  AS EBITDA,
            SUM(c.VOL_NEW)                             AS INSCRITS,
            SUM(c.VOL_EFF)                             AS EFFECTIFS,
            SUM(c.VOL_EFF_ALT)                         AS EFFECTIFS_ALT,
            SUM(c.PLACES)                              AS PLACES
    FROM    cls AS c
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY
),
duo AS (
    SELECT  n.*,
            COALESCE(p.CA,       0) AS P_CA,
            COALESCE(p.EBITDA,   0) AS P_EBITDA,
            COALESCE(p.INSCRITS, 0) AS P_INSCRITS
    FROM    camp AS n
    LEFT JOIN camp AS p
           ON p.SCENARIO = n.SCENARIO AND p.VERSION = n.VERSION
          AND p.PERIODE  = n.PERIODE  AND p.ENTITY  = n.ENTITY
          AND CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
),
w AS (
    SELECT  w0.*,
        /* agregats MARQUE */
        SUM(w0.CA)              OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS CA_M,
        SUM(w0.EBITDA)          OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS EBITDA_M,
        SUM(w0.INSCRITS)        OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS INSCRITS_M,
        SUM(w0.EFFECTIFS)       OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS EFFECTIFS_M,
        SUM(w0.EFFECTIFS_ALT)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS EFFECTIFS_ALT_M,
        SUM(w0.PLACES)          OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS PLACES_M,
        SUM(w0.P_CA)            OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS P_CA_M,
        SUM(w0.P_EBITDA)        OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS P_EBITDA_M,
        COUNT(*)         OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS NB_M,
        /* agregats GROUPE */
        SUM(w0.CA)              OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS CA_G,
        SUM(w0.EBITDA)          OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS EBITDA_G,
        SUM(w0.INSCRITS)        OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS INSCRITS_G,
        SUM(w0.EFFECTIFS)       OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS EFFECTIFS_G,
        SUM(w0.EFFECTIFS_ALT)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS EFFECTIFS_ALT_G,
        SUM(w0.PLACES)          OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS PLACES_G,
        SUM(w0.P_CA)            OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS P_CA_G,
        SUM(w0.P_EBITDA)        OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS P_EBITDA_G,
        COUNT(*)         OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS NB_G
    FROM duo AS w0
)
SELECT
    w.SCENARIO, w.VERSION, w.PERIODE, w.EXERCICE, w.MARQUE, w.ENTITY,

    /* ---- mesures additives : justes sur n'importe quel perimetre ---- */
    w.CA, w.P_CA AS CA_N1,
    w.EBITDA, w.P_EBITDA AS EBITDA_N1,
    w.INSCRITS, w.P_INSCRITS AS INSCRITS_N1,
    w.EFFECTIFS, w.EFFECTIFS_ALT,
    w.PLACES, w.PLACES - w.EFFECTIFS AS PLACES_LIBRES,

    /* ---- detecteurs de niveau, pour le SI du rapport ---- */
    1                       AS NB,
    1.0 / NULLIF(w.NB_M, 0) AS NB_M,
    1.0 / NULLIF(w.NB_G, 0) AS NB_G,

    /* ---- Δ CA — croissance du chiffre d'affaires ---- */
    1.0 * w.CA / NULLIF(w.P_CA, 0) - 1 AS CA_VAR_C,
    (1.0 * w.CA_M / NULLIF(w.P_CA_M, 0) - 1)
        / NULLIF(w.NB_M, 0) AS CA_VAR_M,
    (1.0 * w.CA_G / NULLIF(w.P_CA_G, 0) - 1)
        / NULLIF(w.NB_G, 0) AS CA_VAR_G,

    /* ---- Δ EBITDA — croissance de l'EBITDA ---- */
    1.0 * w.EBITDA / NULLIF(w.P_EBITDA, 0) - 1 AS EBITDA_VAR_C,
    (1.0 * w.EBITDA_M / NULLIF(w.P_EBITDA_M, 0) - 1)
        / NULLIF(w.NB_M, 0) AS EBITDA_VAR_M,
    (1.0 * w.EBITDA_G / NULLIF(w.P_EBITDA_G, 0) - 1)
        / NULLIF(w.NB_G, 0) AS EBITDA_VAR_G,

    /* ---- Δ marge — ecart de marge EN POINTS ---- */
    (1.0 * w.EBITDA / NULLIF(w.CA, 0) - 1.0 * w.P_EBITDA / NULLIF(w.P_CA, 0)) * 100 AS MARGE_VAR_PT_C,
    ((1.0 * w.EBITDA_M / NULLIF(w.CA_M, 0) - 1.0 * w.P_EBITDA_M / NULLIF(w.P_CA_M, 0)) * 100)
        / NULLIF(w.NB_M, 0) AS MARGE_VAR_PT_M,
    ((1.0 * w.EBITDA_G / NULLIF(w.CA_G, 0) - 1.0 * w.P_EBITDA_G / NULLIF(w.P_CA_G, 0)) * 100)
        / NULLIF(w.NB_G, 0) AS MARGE_VAR_PT_G,

    /* ---- Rempl. — taux de remplissage ---- */
    1.0 * w.EFFECTIFS / NULLIF(w.PLACES, 0) AS REMPLISSAGE_C,
    (1.0 * w.EFFECTIFS_M / NULLIF(w.PLACES_M, 0))
        / NULLIF(w.NB_M, 0) AS REMPLISSAGE_M,
    (1.0 * w.EFFECTIFS_G / NULLIF(w.PLACES_G, 0))
        / NULLIF(w.NB_G, 0) AS REMPLISSAGE_G,

    /* ---- Mix alt. — part d'alternants ---- */
    1.0 * w.EFFECTIFS_ALT / NULLIF(w.EFFECTIFS, 0) AS MIX_ALT_C,
    (1.0 * w.EFFECTIFS_ALT_M / NULLIF(w.EFFECTIFS_M, 0))
        / NULLIF(w.NB_M, 0) AS MIX_ALT_M,
    (1.0 * w.EFFECTIFS_ALT_G / NULLIF(w.EFFECTIFS_G, 0))
        / NULLIF(w.NB_G, 0) AS MIX_ALT_G
FROM w
ORDER BY w.EXERCICE, w.MARQUE, w.ENTITY;
