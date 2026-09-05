/* =============================================================================
   Q_COCKPIT_AUTONOME  —  SQL SERVER (T-SQL)
   Le bandeau du cockpit, grain campus, en UNE requete autonome.

   Ne depend que de deux objets qui existent depuis le debut :
       V_ALLOCATION              (grain classe : CA, couts, effectifs)
       AW_002_000002_000001      (socle enrichi : depense d'acquisition)
   La logique de V_CAMPUS_CLASSE et de V_MOTEUR_CAL est inlinee ici.

   Que des mesures ADDITIVES, chacune doublee de son N-1 EN COLONNE :
   le resultat reste juste quel que soit le niveau sur lequel Tagetik filtre
   (campus, marque, noeud, groupe), et un filtre sur l'exercice ne fait pas
   disparaitre la base de comparaison.

   Les 7 ratios se posent a cote de la matrice -- ils restent alors justes a
   TOUS les niveaux, parce qu'ils partent de mesures additives :
       Marge        = EBITDA / CA
       Croiss. CA   = CA / CA_N1 - 1
       Croiss. EB   = EBITDA / EBITDA_N1 - 1
       Ecart marge  = (EBITDA/CA - EBITDA_N1/CA_N1) * 100          (en points)
       CAC          = SPEND_ACQ / INSCRITS
       Croiss. CAC  = (SPEND_ACQ/INSCRITS) / (SPEND_ACQ_N1/INSCRITS_N1) - 1
       Remplissage  = EFFECTIFS / PLACES
   ============================================================================= */
WITH cls AS (                      -- grain classe + capacite  (= V_CAMPUS_CLASSE)
    SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
            a.VOL_EFF, a.VOL_NEW, a.CA, a.COST_COMPLET, a.COST_SIEGE,
            a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                               WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                               ELSE 30 END                    AS PLACES
    FROM    V_ALLOCATION AS a
),
agg AS (                           -- remontee au grain campus
    SELECT  c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY,
            SUM(c.CA)                                  AS CA,
            SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE)  AS EBITDA,
            SUM(c.VOL_NEW)                             AS INSCRITS,
            SUM(c.VOL_EFF)                             AS EFFECTIFS,
            SUM(c.PLACES)                              AS PLACES
    FROM    cls AS c
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY
),
acq AS (                           -- depense d'acquisition  (= V_MOTEUR_CAL)
    SELECT  s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY,
            SUM(s.DEPENSE_ACQ) AS SPEND_ACQ
    FROM    AW_002_000002_000001 AS s
    GROUP BY s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY
),
k AS (
    SELECT  g.*, COALESCE(q.SPEND_ACQ, 0) AS SPEND_ACQ
    FROM    agg AS g
    LEFT JOIN acq AS q
           ON q.SCENARIO = g.SCENARIO
          AND q.PERIODE  = g.PERIODE
          AND q.EXERCICE = g.EXERCICE
          AND q.ENTITY   = g.ENTITY
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
