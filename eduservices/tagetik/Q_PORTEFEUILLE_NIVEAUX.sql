/* =============================================================================
   V_PORTEFEUILLE_NIVEAUX  —  SQL SERVER (T-SQL)
   La grille du cockpit avec LES RATIOS DEJA CALCULES, justes a chaque niveau.

   L'idee : au lieu de laisser Tagetik sommer et donc casser les ratios, la requête
   PRE-AGREGE elle-meme les trois niveaux (GROUPE / MARQUE / CAMPUS) en une
   seule passe, grace a GROUPING SETS. Chaque ligne est deja agregee AVANT la
   division, donc chaque ratio est juste.

   Le rapport n'a plus qu'a filtrer sur NIVEAU et pointer les colonnes.
   IMPORTANT : ne JAMAIS totaliser plusieurs niveaux entre eux -- la ligne
   GROUPE contient deja la somme des campus. Filtre toujours sur UN niveau.

   NIVEAU   'GROUPE' | 'MARQUE' | 'CAMPUS'
   LIBELLE  l'intitule a afficher, quel que soit le niveau
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
lvl AS (                       -- les 3 niveaux en une passe
    SELECT
        CASE WHEN GROUPING(x.ENTITY) = 0 THEN 'CAMPUS'
             WHEN GROUPING(x.MARQUE) = 0 THEN 'MARQUE'
             ELSE 'GROUPE' END                          AS NIVEAU,
        x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE,
        x.MARQUE, x.ENTITY,
        COALESCE(x.MARQUE, '#')                         AS K_MARQUE,
        COALESCE(x.ENTITY, '#')                         AS K_ENTITY,
        COALESCE(x.ENTITY, x.MARQUE, 'GROUPE')          AS LIBELLE,
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
    n.NIVEAU, n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE,
    n.MARQUE, n.ENTITY, n.LIBELLE,

    /* ---------- les colonnes de la grille, prêtes à afficher ---------- */
    n.CA                                                          AS CA,
    1.0 * n.CA / NULLIF(p.CA, 0) - 1                              AS CA_VAR,
    n.EBITDA                                                      AS EBITDA,
    1.0 * n.EBITDA / NULLIF(p.EBITDA, 0) - 1                      AS EBITDA_VAR,
    1.0 * n.EBITDA / NULLIF(g.EBITDA, 0)                          AS PART_EBITDA,
    1.0 * n.EBITDA / NULLIF(n.CA, 0)                              AS MARGE,
    (1.0 * n.EBITDA / NULLIF(n.CA, 0)
       - 1.0 * p.EBITDA / NULLIF(p.CA, 0)) * 100                  AS MARGE_VAR_PT,
    n.INSCRITS                                                    AS INSCRITS,
    1.0 * n.INSCRITS / NULLIF(p.INSCRITS, 0) - 1                  AS INSCRITS_VAR,
    1.0 * n.EFFECTIFS / NULLIF(n.PLACES, 0)                       AS REMPLISSAGE,
    1.0 * n.EFFECTIFS_ALT / NULLIF(n.EFFECTIFS, 0)                AS MIX_ALT,
    1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0)                     AS CAC,
    1.0 * (1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0))
        / NULLIF(1.0 * p.SPEND_ACQ / NULLIF(p.INSCRITS, 0), 0) - 1 AS CAC_VAR,

    /* ---------- les composantes, si tu preferes recomposer ---------- */
    n.EFFECTIFS, n.EFFECTIFS_ALT, n.PLACES,
    n.PLACES - n.EFFECTIFS                                        AS PLACES_LIBRES,
    n.SPEND_ACQ,
    p.CA AS CA_N1, p.EBITDA AS EBITDA_N1, p.INSCRITS AS INSCRITS_N1

FROM       lvl AS n
LEFT JOIN  lvl AS p                       -- l'exercice precedent, meme niveau
       ON  p.NIVEAU   = n.NIVEAU
      AND  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.K_MARQUE = n.K_MARQUE        -- cle neutralisee : NULL ne joint pas
      AND  p.K_ENTITY = n.K_ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
LEFT JOIN  lvl AS g                       -- la ligne GROUPE, pour la part d'EBITDA
       ON  g.NIVEAU   = 'GROUPE'
      AND  g.SCENARIO = n.SCENARIO
      AND  g.VERSION  = n.VERSION
      AND  g.PERIODE  = n.PERIODE
      AND  g.EXERCICE = n.EXERCICE
WHERE n.EXERCICE = '2026'
ORDER BY  CASE n.NIVEAU WHEN 'GROUPE' THEN 1 WHEN 'MARQUE' THEN 2 ELSE 3 END,
          n.MARQUE, n.LIBELLE;
