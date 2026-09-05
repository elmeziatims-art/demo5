/* =============================================================================
   Q_COCKPIT_MESURES  —  variante SANS ACQUISITION  (SQL SERVER)
   A utiliser tant que V_MOTEUR_CAL n'existe pas.
   Ne lit que V_CAMPUS_CLASSE : livre 5 des 6 tuiles du bandeau.
   SPEND_ACQ reste NULL (et non 0) pour que la tuile CAC s'affiche VIDE au lieu
   d'afficher 0 EUR -- une valeur absente doit se voir, pas se deguiser en zero.
   Les colonnes gardent exactement les memes noms : quand tu creeras
   V_MOTEUR_CAL, tu bascules sur la requete complete sans retoucher le masque.
   ============================================================================= */
WITH k AS (
    SELECT  c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY,
            SUM(c.CA)                                  AS CA,
            SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE)  AS EBITDA,
            SUM(c.VOL_NEW)                             AS INSCRITS,
            SUM(c.VOL_EFF)                             AS EFFECTIFS,
            SUM(c.PLACES)                              AS PLACES
    FROM    V_CAMPUS_CLASSE AS c
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY
)
SELECT
    n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE, n.MARQUE, n.ENTITY,
    n.CA,                       COALESCE(p.CA,        0) AS CA_N1,
    n.EBITDA,                   COALESCE(p.EBITDA,    0) AS EBITDA_N1,
    n.INSCRITS,                 COALESCE(p.INSCRITS,  0) AS INSCRITS_N1,
    n.EFFECTIFS,                COALESCE(p.EFFECTIFS, 0) AS EFFECTIFS_N1,
    n.PLACES,                   COALESCE(p.PLACES,    0) AS PLACES_N1,
    n.PLACES - n.EFFECTIFS                               AS PLACES_LIBRES,
    CAST(NULL AS DECIMAL(18,2))                          AS SPEND_ACQ,
    CAST(NULL AS DECIMAL(18,2))                          AS SPEND_ACQ_N1
FROM       k AS n
LEFT JOIN  k AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
ORDER BY   n.EXERCICE, n.MARQUE, n.ENTITY;
