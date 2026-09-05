/* =============================================================================
   Q_PORTEFEUILLE_FEUILLES  —  SQL SERVER (T-SQL)
   Une seule ligne par CAMPUS : ENTITY ne contient que des elements finaux,
   donc mappables tels quels sur la dimension Entity de Tagetik.

   -------------------------------------------------------------------------
   COMMENT LES RATIOS DE NIVEAU SUPERIEUR TIENNENT SANS LIGNE DE NOEUD
   -------------------------------------------------------------------------
   Le ratio d'un noeud est REPARTI sur ses feuilles : la marge de MBway est
   stockee sur chacun de ses 4 campus, divisee par 4. En sommant les 4 lignes,
   Tagetik reconstitue exactement la marge de la marque.
       MARGE_M = (EBITDA marque / CA marque) / nombre de campus de la marque
       MARGE_G = (EBITDA groupe / CA groupe) / nombre de campus du groupe

   Suffixes :  _C = valeur du campus   _M = niveau marque   _G = niveau groupe
   Les mesures de base (CA, EBITDA, INSCRITS...) sont les valeurs propres du
   campus : elles s'agregent normalement vers n'importe quel noeud.

   -------------------------------------------------------------------------
   LE PIEGE A CONNAITRE
   -------------------------------------------------------------------------
   Une colonne _M n'est juste que si TOUS les campus de la marque sont dans le
   perimetre affiche. Filtre un seul campus et MARGE_M vaudra le quart de la
   marge de la marque -- un chiffre qui ne veut rien dire.
   Les colonnes _C et les mesures de base, elles, restent justes sur
   n'importe quel sous-ensemble.

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
acq AS (
    SELECT  s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY,
            SUM(s.DEPENSE_ACQ) AS SPEND_ACQ
    FROM    AW_002_000002_000001 AS s
    GROUP BY s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY
),
camp AS (
    SELECT  c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY,
            SUM(c.CA)                                  AS CA,
            SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE)  AS EBITDA,
            SUM(c.VOL_NEW)                             AS INSCRITS,
            SUM(c.VOL_EFF)                             AS EFFECTIFS,
            SUM(c.VOL_EFF_ALT)                         AS EFFECTIFS_ALT,
            SUM(c.PLACES)                              AS PLACES,
            COALESCE(MAX(q.SPEND_ACQ), 0)              AS SPEND_ACQ
    FROM    cls AS c
    LEFT JOIN acq AS q
           ON q.SCENARIO = c.SCENARIO AND q.PERIODE = c.PERIODE
          AND q.EXERCICE = c.EXERCICE AND q.ENTITY  = c.ENTITY
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY
),
duo AS (
    SELECT  n.*,
            COALESCE(p.CA,        0) AS P_CA,
            COALESCE(p.EBITDA,    0) AS P_EBITDA,
            COALESCE(p.INSCRITS,  0) AS P_INSCRITS,
            COALESCE(p.EFFECTIFS, 0) AS P_EFFECTIFS,
            COALESCE(p.PLACES,    0) AS P_PLACES,
            COALESCE(p.SPEND_ACQ, 0) AS P_SPEND_ACQ
    FROM    camp AS n
    LEFT JOIN camp AS p
           ON p.SCENARIO = n.SCENARIO AND p.VERSION = n.VERSION
          AND p.PERIODE  = n.PERIODE  AND p.ENTITY  = n.ENTITY
          AND CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
),
w AS (
    SELECT  w0.*,
        /* --- agregats MARQUE --- */
        SUM(w0.CA)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)                  AS CA_M,
        SUM(w0.EBITDA)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)              AS EBITDA_M,
        SUM(w0.INSCRITS)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)            AS INSCRITS_M,
        SUM(w0.EFFECTIFS)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)           AS EFFECTIFS_M,
        SUM(w0.EFFECTIFS_ALT)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)       AS EFFECTIFS_ALT_M,
        SUM(w0.PLACES)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)              AS PLACES_M,
        SUM(w0.SPEND_ACQ)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)           AS SPEND_ACQ_M,
        SUM(w0.P_CA) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)                AS P_CA_M,
        SUM(w0.P_EBITDA) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)            AS P_EBITDA_M,
        SUM(w0.P_INSCRITS) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)          AS P_INSCRITS_M,
        SUM(w0.P_SPEND_ACQ) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE)         AS P_SPEND_ACQ_M,
        COUNT(*)      OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE, w0.MARQUE) AS NB_M,
        /* --- agregats GROUPE --- */
        SUM(w0.CA)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)                  AS CA_G,
        SUM(w0.EBITDA)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)              AS EBITDA_G,
        SUM(w0.INSCRITS)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)            AS INSCRITS_G,
        SUM(w0.EFFECTIFS)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)           AS EFFECTIFS_G,
        SUM(w0.EFFECTIFS_ALT)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)       AS EFFECTIFS_ALT_G,
        SUM(w0.PLACES)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)              AS PLACES_G,
        SUM(w0.SPEND_ACQ)   OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)           AS SPEND_ACQ_G,
        SUM(w0.P_CA) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)                AS P_CA_G,
        SUM(w0.P_EBITDA) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)            AS P_EBITDA_G,
        SUM(w0.P_INSCRITS) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)          AS P_INSCRITS_G,
        SUM(w0.P_SPEND_ACQ) OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE)         AS P_SPEND_ACQ_G,
        COUNT(*)      OVER (PARTITION BY w0.SCENARIO, w0.VERSION, w0.PERIODE, w0.EXERCICE) AS NB_G
    FROM duo AS w0
)
SELECT
    w.SCENARIO, w.VERSION, w.PERIODE, w.EXERCICE, w.ENTITY, w.MARQUE,

    /* ---------- mesures de base : les valeurs propres du campus ---------- */
    w.CA, w.P_CA AS CA_N1,
    w.EBITDA, w.P_EBITDA AS EBITDA_N1,
    w.INSCRITS, w.P_INSCRITS AS INSCRITS_N1,
    w.EFFECTIFS, w.P_EFFECTIFS AS EFFECTIFS_N1,
    w.EFFECTIFS_ALT,
    w.PLACES, w.PLACES - w.EFFECTIFS AS PLACES_LIBRES,
    w.SPEND_ACQ, w.P_SPEND_ACQ AS SPEND_ACQ_N1,

    /* MARGE —        marge EBITDA */
    1.0 * w.EBITDA / NULLIF(w.CA, 0) AS MARGE_C,
    (1.0 * w.EBITDA_M / NULLIF(w.CA_M, 0))
        / NULLIF(w.NB_M, 0) AS MARGE_M,
    (1.0 * w.EBITDA_G / NULLIF(w.CA_G, 0))
        / NULLIF(w.NB_G, 0) AS MARGE_G,

    /* CA_VAR —       croissance du CA */
    1.0 * w.CA / NULLIF(w.P_CA, 0) - 1 AS CA_VAR_C,
    (1.0 * w.CA_M / NULLIF(w.P_CA_M, 0) - 1)
        / NULLIF(w.NB_M, 0) AS CA_VAR_M,
    (1.0 * w.CA_G / NULLIF(w.P_CA_G, 0) - 1)
        / NULLIF(w.NB_G, 0) AS CA_VAR_G,

    /* EBITDA_VAR —   croissance de l'EBITDA */
    1.0 * w.EBITDA / NULLIF(w.P_EBITDA, 0) - 1 AS EBITDA_VAR_C,
    (1.0 * w.EBITDA_M / NULLIF(w.P_EBITDA_M, 0) - 1)
        / NULLIF(w.NB_M, 0) AS EBITDA_VAR_M,
    (1.0 * w.EBITDA_G / NULLIF(w.P_EBITDA_G, 0) - 1)
        / NULLIF(w.NB_G, 0) AS EBITDA_VAR_G,

    /* MARGE_VAR_PT —  ecart de marge, EN POINTS */
    (1.0 * w.EBITDA / NULLIF(w.CA, 0) - 1.0 * w.P_EBITDA / NULLIF(w.P_CA, 0)) * 100 AS MARGE_VAR_PT_C,
    ((1.0 * w.EBITDA_M / NULLIF(w.CA_M, 0) - 1.0 * w.P_EBITDA_M / NULLIF(w.P_CA_M, 0)) * 100)
        / NULLIF(w.NB_M, 0) AS MARGE_VAR_PT_M,
    ((1.0 * w.EBITDA_G / NULLIF(w.CA_G, 0) - 1.0 * w.P_EBITDA_G / NULLIF(w.P_CA_G, 0)) * 100)
        / NULLIF(w.NB_G, 0) AS MARGE_VAR_PT_G,

    /* PART_EBITDA —  part dans l'EBITDA groupe */
    1.0 * w.EBITDA / NULLIF(w.EBITDA_G, 0) AS PART_EBITDA_C,
    (1.0 * w.EBITDA_M / NULLIF(w.EBITDA_G, 0))
        / NULLIF(w.NB_M, 0) AS PART_EBITDA_M,
    (1.0 * w.EBITDA_G / NULLIF(w.EBITDA_G, 0))
        / NULLIF(w.NB_G, 0) AS PART_EBITDA_G,

    /* INSCRITS_VAR —  croissance des inscrits */
    1.0 * w.INSCRITS / NULLIF(w.P_INSCRITS, 0) - 1 AS INSCRITS_VAR_C,
    (1.0 * w.INSCRITS_M / NULLIF(w.P_INSCRITS_M, 0) - 1)
        / NULLIF(w.NB_M, 0) AS INSCRITS_VAR_M,
    (1.0 * w.INSCRITS_G / NULLIF(w.P_INSCRITS_G, 0) - 1)
        / NULLIF(w.NB_G, 0) AS INSCRITS_VAR_G,

    /* REMPLISSAGE —  taux de remplissage */
    1.0 * w.EFFECTIFS / NULLIF(w.PLACES, 0) AS REMPLISSAGE_C,
    (1.0 * w.EFFECTIFS_M / NULLIF(w.PLACES_M, 0))
        / NULLIF(w.NB_M, 0) AS REMPLISSAGE_M,
    (1.0 * w.EFFECTIFS_G / NULLIF(w.PLACES_G, 0))
        / NULLIF(w.NB_G, 0) AS REMPLISSAGE_G,

    /* MIX_ALT —      part d'alternants */
    1.0 * w.EFFECTIFS_ALT / NULLIF(w.EFFECTIFS, 0) AS MIX_ALT_C,
    (1.0 * w.EFFECTIFS_ALT_M / NULLIF(w.EFFECTIFS_M, 0))
        / NULLIF(w.NB_M, 0) AS MIX_ALT_M,
    (1.0 * w.EFFECTIFS_ALT_G / NULLIF(w.EFFECTIFS_G, 0))
        / NULLIF(w.NB_G, 0) AS MIX_ALT_G,

    /* CAC —          cout d'acquisition */
    1.0 * w.SPEND_ACQ / NULLIF(w.INSCRITS, 0) AS CAC_C,
    (1.0 * w.SPEND_ACQ_M / NULLIF(w.INSCRITS_M, 0))
        / NULLIF(w.NB_M, 0) AS CAC_M,
    (1.0 * w.SPEND_ACQ_G / NULLIF(w.INSCRITS_G, 0))
        / NULLIF(w.NB_G, 0) AS CAC_G,

    /* CAC_VAR —      croissance du CAC */
    (1.0 * w.SPEND_ACQ / NULLIF(w.INSCRITS, 0)) / NULLIF(1.0 * w.P_SPEND_ACQ / NULLIF(w.P_INSCRITS, 0), 0) - 1 AS CAC_VAR_C,
    ((1.0 * w.SPEND_ACQ_M / NULLIF(w.INSCRITS_M, 0)) / NULLIF(1.0 * w.P_SPEND_ACQ_M / NULLIF(w.P_INSCRITS_M, 0), 0) - 1)
        / NULLIF(w.NB_M, 0) AS CAC_VAR_M,
    ((1.0 * w.SPEND_ACQ_G / NULLIF(w.INSCRITS_G, 0)) / NULLIF(1.0 * w.P_SPEND_ACQ_G / NULLIF(w.P_INSCRITS_G, 0), 0) - 1)
        / NULLIF(w.NB_G, 0) AS CAC_VAR_G
FROM w
ORDER BY w.EXERCICE, w.MARQUE, w.ENTITY;
