/* =============================================================================
   Q_COCKPIT_MESURES  —  SQL SERVER (T-SQL)
   Restitution rapide, grain campus, sans parametre.

   Que des mesures ADDITIVES : le resultat reste juste quel que soit le niveau
   sur lequel Tagetik filtre (campus, marque, noeud, groupe).
   N-1 est une COLONNE, pas une ligne : un filtre sur EXERCICE = 2026 ne
   l'emporte donc pas, la base de comparaison suit toujours.

   Aucun ratio ici, volontairement : une somme de marges ou de CAC n'a pas de
   sens sur un noeud. Les ratios se calculent a cote de la matrice, a partir
   de ces colonnes :
       Marge        = EBITDA / CA
       Croiss. CA   = CA / CA_N1 - 1
       Croiss. EB   = EBITDA / EBITDA_N1 - 1
       Ecart marge  = (EBITDA/CA - EBITDA_N1/CA_N1) * 100      (en points)
       CAC          = SPEND_ACQ / INSCRITS
       Croiss. CAC  = (SPEND_ACQ/INSCRITS) / (SPEND_ACQ_N1/INSCRITS_N1) - 1
       Remplissage  = EFFECTIFS / PLACES
   ============================================================================= */
WITH agg AS (
    SELECT  c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY,
            SUM(c.CA)                                  AS CA,
            SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE)  AS EBITDA,
            SUM(c.VOL_NEW)                             AS INSCRITS,
            SUM(c.VOL_EFF)                             AS EFFECTIFS,
            SUM(c.PLACES)                              AS PLACES
    FROM    V_CAMPUS_CLASSE AS c
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY
),
acq AS (
    SELECT  m.SCENARIO, m.PERIODE, m.EXERCICE, m.ENTITY,
            SUM(m.SPEND_ACQ) AS SPEND_ACQ
    FROM    V_MOTEUR_CAL AS m
    GROUP BY m.SCENARIO, m.PERIODE, m.EXERCICE, m.ENTITY
),
k AS (
    SELECT  a.*, COALESCE(q.SPEND_ACQ, 0) AS SPEND_ACQ
    FROM    agg AS a
    LEFT JOIN acq AS q
           ON q.SCENARIO = a.SCENARIO
          AND q.PERIODE  = a.PERIODE
          AND q.EXERCICE = a.EXERCICE
          AND q.ENTITY   = a.ENTITY
)
SELECT
    n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE, n.MARQUE, n.ENTITY,
    n.CA,                       COALESCE(p.CA,        0) AS CA_N1,
    n.EBITDA,                   COALESCE(p.EBITDA,    0) AS EBITDA_N1,
    n.INSCRITS,                 COALESCE(p.INSCRITS,  0) AS INSCRITS_N1,
    n.EFFECTIFS,                COALESCE(p.EFFECTIFS, 0) AS EFFECTIFS_N1,
    n.PLACES,                   COALESCE(p.PLACES,    0) AS PLACES_N1,
    n.PLACES - n.EFFECTIFS                               AS PLACES_LIBRES,
    n.SPEND_ACQ,                COALESCE(p.SPEND_ACQ, 0) AS SPEND_ACQ_N1
FROM       k AS n
LEFT JOIN  k AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
ORDER BY   n.EXERCICE, n.MARQUE, n.ENTITY;
