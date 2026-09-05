/* =============================================================================
   V_PORTEFEUILLE  —  SQL SERVER (T-SQL)
   La grille « Portefeuille — marque & campus » du cockpit.

   DIMENSIONS : SCENARIO · VERSION · PERIODE · EXERCICE · MARQUE · ENTITY
   MESURES    : que des mesures ADDITIVES, et rien d'autre.

   -------------------------------------------------------------------------
   POURQUOI AUCUN RATIO DANS CETTE VUE
   -------------------------------------------------------------------------
   Tagetik somme les mesures sur les noeuds. Une marge, un taux de
   remplissage, un mix ou une variation ne se somment pas : la somme des
   marges de 4 campus n'est pas la marge de la marque. Toute colonne de ce
   type placee dans la vue serait FAUSSE des le premier total, sans aucune
   erreur pour te prevenir.

   La vue expose donc les COMPOSANTES, et le rapport recompose. Chaque
   composante est additive, donc chaque ratio reste juste a TOUS les niveaux.

   -------------------------------------------------------------------------
   LES 10 COLONNES DE LA GRILLE, ET D'OU ELLES VIENNENT
   -------------------------------------------------------------------------
     CA 2026        =  CA                                        (mesure)
     D CA           =  CA / CA_N1 - 1                            (calcul)
     EBITDA         =  EBITDA                                    (mesure)
     D EBITDA       =  EBITDA / EBITDA_N1 - 1                    (calcul)
     Part EBITDA    =  EBITDA / EBITDA(ligne GROUPE)             (calcul, ref
                       absolue sur la cellule EBITDA du total)
     Marge EBITDA   =  EBITDA / CA                               (calcul)
     D marge        =  (EBITDA/CA - EBITDA_N1/CA_N1) * 100       (calcul, POINTS)
     Inscrits       =  INSCRITS                                  (mesure)
     Rempl.         =  EFFECTIFS / PLACES                        (calcul)
     Mix alt.       =  EFFECTIFS_ALT / EFFECTIFS                 (calcul)

   Bonus deja additifs, utiles au cadrage :
     PLACES_LIBRES  =  PLACES - EFFECTIFS      (le gisement de croissance)
     SPEND_ACQ      ->  CAC = SPEND_ACQ / INSCRITS

   N-1 est une COLONNE, pas une ligne : un filtre sur l'exercice ne fait donc
   pas disparaitre la base de comparaison.

   Ne depend que de V_ALLOCATION et de AW_002_000002_000001.
   ============================================================================= */
CREATE OR ALTER VIEW V_PORTEFEUILLE AS
WITH cls AS (
    SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
            a.VOL_EFF, a.VOL_NEW, a.CA, a.COST_COMPLET, a.COST_SIEGE,
            CASE WHEN a.MODALITE = 'ALT' THEN a.VOL_EFF ELSE 0 END  AS VOL_EFF_ALT,
            a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                               WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                               ELSE 30 END                          AS PLACES
    FROM    V_ALLOCATION AS a
),
agg AS (
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
acq AS (
    SELECT  s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY,
            SUM(s.DEPENSE_ACQ) AS SPEND_ACQ
    FROM    AW_002_000002_000001 AS s
    GROUP BY s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY
),
k AS (
    SELECT  g.*, COALESCE(q.SPEND_ACQ, 0) AS SPEND_ACQ
    FROM    agg AS g
    LEFT JOIN acq AS q
           ON q.SCENARIO = g.SCENARIO AND q.PERIODE = g.PERIODE
          AND q.EXERCICE = g.EXERCICE AND q.ENTITY  = g.ENTITY
)
SELECT
    /* ---------- dimensions ---------- */
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.MARQUE,
    n.ENTITY,

    /* ---------- mesures : toutes additives ---------- */
    n.CA                                                 AS CA,
    COALESCE(p.CA,            0)                         AS CA_N1,
    n.EBITDA                                             AS EBITDA,
    COALESCE(p.EBITDA,        0)                         AS EBITDA_N1,
    n.INSCRITS                                           AS INSCRITS,
    COALESCE(p.INSCRITS,      0)                         AS INSCRITS_N1,
    n.EFFECTIFS                                          AS EFFECTIFS,
    COALESCE(p.EFFECTIFS,     0)                         AS EFFECTIFS_N1,
    n.EFFECTIFS_ALT                                      AS EFFECTIFS_ALT,
    COALESCE(p.EFFECTIFS_ALT, 0)                         AS EFFECTIFS_ALT_N1,
    n.EFFECTIFS - n.EFFECTIFS_ALT                        AS EFFECTIFS_INIT,
    n.PLACES                                             AS PLACES,
    COALESCE(p.PLACES,        0)                         AS PLACES_N1,
    n.PLACES - n.EFFECTIFS                               AS PLACES_LIBRES,
    n.SPEND_ACQ                                          AS SPEND_ACQ,
    COALESCE(p.SPEND_ACQ,     0)                         AS SPEND_ACQ_N1
FROM       k AS n
LEFT JOIN  k AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1;
