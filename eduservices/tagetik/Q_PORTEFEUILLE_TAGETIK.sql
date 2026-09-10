/* =============================================================================
   Q_PORTEFEUILLE_TAGETIK  —  SQL SERVER (T-SQL)
   La grille du cockpit, concue pour etre MAPPEE sur la dimension Entity.

   -------------------------------------------------------------------------
   LE PRINCIPE
   -------------------------------------------------------------------------
   ENTITY est TOUJOURS rempli : code campus, code marque, ou le noeud racine.
   NIVEAU dit sur quel palier on se trouve : 'CAMPUS' | 'MARQUE' | 'GROUPE'.

   Chaque ratio existe en TROIS colonnes, remplies uniquement sur les lignes
   de leur niveau et a ZERO ailleurs. C'est ce qui les rend sommables :
   au noeud MBway, CA_VAR_M vaut 0 sur les 4 campus + la vraie valeur sur la
   ligne MBway = la vraie valeur. Tagetik peut sommer sans rien casser.

   Dans le rapport, une seule formule par colonne affichee :
       D CA = IF(NIVEAU="CAMPUS"; CA_VAR_C;
              IF(NIVEAU="MARQUE"; CA_VAR_M; CA_VAR_G))

   -------------------------------------------------------------------------
   LA CONTREPARTIE, A NE PAS RATER
   -------------------------------------------------------------------------
   Les MESURES DE BASE (CA, EBITDA, INSCRITS...) ne sont remplies que sur les
   lignes CAMPUS, et valent 0 sur MARQUE et GROUPE. Sinon le noeud MBway
   compterait la somme de ses campus PLUS sa propre ligne, soit le double.
   Tagetik les agrege naturellement vers n'importe quel noeud, y compris un
   noeud qui n'existe pas dans cette requete.

   Suffixes :  _C = CAMPUS   _M = MARQUE   _G = GROUPE
   Le code du noeud racine est 'GROUPE' : remplace-le par le tien.
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
src AS (
    SELECT  c.*, COALESCE(q.SPEND_ACQ, 0) AS SPEND_ACQ
    FROM    cls AS c
    LEFT JOIN acq AS q
           ON q.SCENARIO = c.SCENARIO AND q.PERIODE = c.PERIODE
          AND q.EXERCICE = c.EXERCICE AND q.ENTITY  = c.ENTITY
),
lvl AS (
    SELECT
        CASE WHEN GROUPING(x.ENTITY) = 0 THEN 'CAMPUS'
             WHEN GROUPING(x.MARQUE) = 0 THEN 'MARQUE'
             ELSE 'GROUPE' END                          AS NIVEAU,
        x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE,
        COALESCE(x.ENTITY, x.MARQUE, 'GROUPE')          AS ENTITY_NODE,
        COALESCE(x.MARQUE, 'GROUPE')                    AS MARQUE_NODE,
        COALESCE(x.MARQUE, '#')                         AS K_MARQUE,
        COALESCE(x.ENTITY, '#')                         AS K_ENTITY,
        SUM(x.CA)                                       AS CA,
        SUM(x.CA - x.COST_COMPLET + x.COST_SIEGE)       AS EBITDA,
        SUM(x.VOL_NEW)                                  AS INSCRITS,
        SUM(x.VOL_EFF)                                  AS EFFECTIFS,
        SUM(x.VOL_EFF_ALT)                              AS EFFECTIFS_ALT,
        SUM(x.PLACES)                                   AS PLACES,
        SUM(x.SPEND_ACQ)                                AS SPEND_ACQ
    FROM src AS x
    GROUP BY GROUPING SETS (
        (x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE),
        (x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE, x.MARQUE),
        (x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE, x.MARQUE, x.ENTITY)
    )
)
SELECT
    /* ---------- dimensions : ENTITY est toujours rempli ---------- */
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.ENTITY_NODE                                            AS ENTITY,
    n.MARQUE_NODE                                            AS MARQUE,
    n.NIVEAU,

    /* ---------- mesures de base : SUR LES CAMPUS UNIQUEMENT ----------
       zero sur les lignes MARQUE et GROUPE, sinon Tagetik compterait
       les campus PLUS la ligne du noeud, soit le double.            */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.CA ELSE 0 END                                                  AS CA,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN p.CA ELSE 0 END                                                  AS CA_N1,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.EBITDA ELSE 0 END                                              AS EBITDA,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN p.EBITDA ELSE 0 END                                              AS EBITDA_N1,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.INSCRITS ELSE 0 END                                            AS INSCRITS,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN p.INSCRITS ELSE 0 END                                            AS INSCRITS_N1,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.EFFECTIFS ELSE 0 END                                           AS EFFECTIFS,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN p.EFFECTIFS ELSE 0 END                                           AS EFFECTIFS_N1,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.EFFECTIFS_ALT ELSE 0 END                                       AS EFFECTIFS_ALT,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.PLACES ELSE 0 END                                              AS PLACES,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.PLACES - n.EFFECTIFS ELSE 0 END                                AS PLACES_LIBRES,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN n.SPEND_ACQ ELSE 0 END                                           AS SPEND_ACQ,
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN p.SPEND_ACQ ELSE 0 END                                           AS SPEND_ACQ_N1,

    /* MARGE — marge EBITDA */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.EBITDA / NULLIF(n.CA, 0) ELSE 0 END AS MARGE_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.EBITDA / NULLIF(n.CA, 0) ELSE 0 END AS MARGE_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.EBITDA / NULLIF(n.CA, 0) ELSE 0 END AS MARGE_G,

    /* CA_VAR — croissance du CA */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.CA / NULLIF(p.CA, 0) - 1 ELSE 0 END AS CA_VAR_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.CA / NULLIF(p.CA, 0) - 1 ELSE 0 END AS CA_VAR_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.CA / NULLIF(p.CA, 0) - 1 ELSE 0 END AS CA_VAR_G,

    /* EBITDA_VAR — croissance de l'EBITDA */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.EBITDA / NULLIF(p.EBITDA, 0) - 1 ELSE 0 END AS EBITDA_VAR_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.EBITDA / NULLIF(p.EBITDA, 0) - 1 ELSE 0 END AS EBITDA_VAR_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.EBITDA / NULLIF(p.EBITDA, 0) - 1 ELSE 0 END AS EBITDA_VAR_G,

    /* MARGE_VAR_PT — ecart de marge, EN POINTS */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN (1.0 * n.EBITDA / NULLIF(n.CA, 0) - 1.0 * p.EBITDA / NULLIF(p.CA, 0)) * 100 ELSE 0 END AS MARGE_VAR_PT_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN (1.0 * n.EBITDA / NULLIF(n.CA, 0) - 1.0 * p.EBITDA / NULLIF(p.CA, 0)) * 100 ELSE 0 END AS MARGE_VAR_PT_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN (1.0 * n.EBITDA / NULLIF(n.CA, 0) - 1.0 * p.EBITDA / NULLIF(p.CA, 0)) * 100 ELSE 0 END AS MARGE_VAR_PT_G,

    /* PART_EBITDA — part dans l'EBITDA groupe */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.EBITDA / NULLIF(g.EBITDA, 0) ELSE 0 END AS PART_EBITDA_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.EBITDA / NULLIF(g.EBITDA, 0) ELSE 0 END AS PART_EBITDA_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.EBITDA / NULLIF(g.EBITDA, 0) ELSE 0 END AS PART_EBITDA_G,

    /* INSCRITS_VAR — croissance des inscrits */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.INSCRITS / NULLIF(p.INSCRITS, 0) - 1 ELSE 0 END AS INSCRITS_VAR_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.INSCRITS / NULLIF(p.INSCRITS, 0) - 1 ELSE 0 END AS INSCRITS_VAR_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.INSCRITS / NULLIF(p.INSCRITS, 0) - 1 ELSE 0 END AS INSCRITS_VAR_G,

    /* REMPLISSAGE — taux de remplissage */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.EFFECTIFS / NULLIF(n.PLACES, 0) ELSE 0 END AS REMPLISSAGE_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.EFFECTIFS / NULLIF(n.PLACES, 0) ELSE 0 END AS REMPLISSAGE_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.EFFECTIFS / NULLIF(n.PLACES, 0) ELSE 0 END AS REMPLISSAGE_G,

    /* MIX_ALT — part d'alternants */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.EFFECTIFS_ALT / NULLIF(n.EFFECTIFS, 0) ELSE 0 END AS MIX_ALT_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.EFFECTIFS_ALT / NULLIF(n.EFFECTIFS, 0) ELSE 0 END AS MIX_ALT_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.EFFECTIFS_ALT / NULLIF(n.EFFECTIFS, 0) ELSE 0 END AS MIX_ALT_G,

    /* CAC — cout d'acquisition */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0) ELSE 0 END AS CAC_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0) ELSE 0 END AS CAC_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0) ELSE 0 END AS CAC_G,

    /* CAC_VAR — croissance du CAC */
    CASE WHEN n.NIVEAU = 'CAMPUS' THEN 1.0 * (1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0)) / NULLIF(1.0 * p.SPEND_ACQ / NULLIF(p.INSCRITS, 0), 0) - 1 ELSE 0 END AS CAC_VAR_C,
    CASE WHEN n.NIVEAU = 'MARQUE' THEN 1.0 * (1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0)) / NULLIF(1.0 * p.SPEND_ACQ / NULLIF(p.INSCRITS, 0), 0) - 1 ELSE 0 END AS CAC_VAR_M,
    CASE WHEN n.NIVEAU = 'GROUPE' THEN 1.0 * (1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0)) / NULLIF(1.0 * p.SPEND_ACQ / NULLIF(p.INSCRITS, 0), 0) - 1 ELSE 0 END AS CAC_VAR_G
FROM       lvl AS n
LEFT JOIN  lvl AS p
       ON  p.NIVEAU   = n.NIVEAU
      AND  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.K_MARQUE = n.K_MARQUE
      AND  p.K_ENTITY = n.K_ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
LEFT JOIN  lvl AS g
       ON  g.NIVEAU   = 'GROUPE'
      AND  g.SCENARIO = n.SCENARIO
      AND  g.VERSION  = n.VERSION
      AND  g.PERIODE  = n.PERIODE
      AND  g.EXERCICE = n.EXERCICE
ORDER BY  n.EXERCICE,
          CASE n.NIVEAU WHEN 'GROUPE' THEN 1 WHEN 'MARQUE' THEN 2 ELSE 3 END,
          n.MARQUE_NODE, n.ENTITY_NODE;
