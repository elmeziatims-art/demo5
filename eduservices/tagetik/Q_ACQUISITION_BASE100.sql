/* =============================================================================
   Q_ACQUISITION_BASE100  —  SQL SERVER, forme enrobable par Tagetik.
   Le tableau EXACT qui est derriere le graphe "Acquisition : depenses vs
   inscrits, base 100".

   Une ligne par CAMPUS x EXERCICE. ENTITY ne contient que des elements
   finaux, MARQUE est portee sur chaque ligne.

   Regles Tagetik : pas de CTE, pas de ORDER BY, pas de ';'.

   --------------------------------------------------------------------------
   LE PROBLEME DE LA BASE 100

   Un indice est un rapport : il ne s'additionne pas. Un campus a 118 et un
   autre a 104 ne font pas 222 sur la marque.

   La solution est la meme que pour une marge : on expose les deux termes. La
   requete porte sur CHAQUE ligne la valeur de l'annee de reference du campus,
   repetee. Le report divise APRES la somme :

       Indice depenses  =  SUM(SPEND_ACQ) / SUM(SPEND_ACQ_REF) * 100
       Indice inscrits  =  SUM(INSCRITS)  / SUM(INSCRITS_REF)  * 100

   Ces deux formules sont justes a tous les niveaux, parce que le denominateur
   est une somme de montants reels, pas une moyenne d'indices.

   L'annee de reference est le PLUS PETIT exercice present dans le perimetre
   charge (ici 2024). Elle est renvoyee en clair dans EXERCICE_REF pour que le
   titre du graphe puisse la nommer.

   --------------------------------------------------------------------------
   CE QUE LE GRAPHE MONTRE

   Les deux courbes partent de 100. Si la courbe des depenses monte plus vite
   que celle des inscrits, chaque inscrit coute de plus en plus cher : le
   recrutement s'achete au lieu de se gagner. C'est exactement ce que dit la
   troisieme mesure, additive elle aussi par ses deux termes :

       CAF, cout d'acquisition par inscrit  =  SUM(SPEND_ACQ) / SUM(INSCRITS)
       Ecart des deux indices, en points    =  indice depenses - indice inscrits

   --------------------------------------------------------------------------
   Sources : V_ALLOCATION (inscrits, marque) et AW_002_000002_000001
   (DEPENSE_ACQ). Cette depense est identique au compte 6231 de la compta,
   verifie au centime sur les trois exercices.
   ============================================================================= */
SELECT
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.EXERCICE_REF,
    n.MARQUE,
    n.ENTITY,

    n.SPEND_ACQ                         AS SPEND_ACQ,
    n.INSCRITS                          AS INSCRITS,
    COALESCE(r.SPEND_ACQ, 0)            AS SPEND_ACQ_REF,
    COALESCE(r.INSCRITS,  0)            AS INSCRITS_REF,

    COALESCE(p.SPEND_ACQ, 0)            AS SPEND_ACQ_N1,
    COALESCE(p.INSCRITS,  0)            AS INSCRITS_N1
FROM (
        SELECT  m.SCENARIO, m.VERSION, m.PERIODE, m.EXERCICE, m.MARQUE, m.ENTITY,
                m.SPEND_ACQ, m.INSCRITS,
                MIN(CAST(m.EXERCICE AS INT))
                    OVER (PARTITION BY m.SCENARIO, m.VERSION, m.PERIODE) AS EXERCICE_REF
        FROM (
                SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                        SUM(a.VOL_NEW)                     AS INSCRITS,
                        MAX(COALESCE(s.SPEND_ACQ, 0))      AS SPEND_ACQ
                FROM    V_ALLOCATION AS a
                LEFT JOIN (
                        SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                                SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                        FROM    AW_002_000002_000001 AS z
                        GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY
                     ) AS s
                       ON  s.SCENARIO = a.SCENARIO
                      AND  s.PERIODE  = a.PERIODE
                      AND  s.EXERCICE = a.EXERCICE
                      AND  s.ENTITY   = a.ENTITY
                GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
             ) AS m
     ) AS n
LEFT JOIN (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                SUM(a.VOL_NEW)                     AS INSCRITS,
                MAX(COALESCE(s.SPEND_ACQ, 0))      AS SPEND_ACQ
        FROM    V_ALLOCATION AS a
        LEFT JOIN (
                SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                        SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                FROM    AW_002_000002_000001 AS z
                GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY
             ) AS s
               ON  s.SCENARIO = a.SCENARIO
              AND  s.PERIODE  = a.PERIODE
              AND  s.EXERCICE = a.EXERCICE
              AND  s.ENTITY   = a.ENTITY
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
     ) AS r
       ON  r.SCENARIO = n.SCENARIO
      AND  r.VERSION  = n.VERSION
      AND  r.PERIODE  = n.PERIODE
      AND  r.ENTITY   = n.ENTITY
      AND  CAST(r.EXERCICE AS INT) = n.EXERCICE_REF
LEFT JOIN (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                SUM(a.VOL_NEW)                     AS INSCRITS,
                MAX(COALESCE(s.SPEND_ACQ, 0))      AS SPEND_ACQ
        FROM    V_ALLOCATION AS a
        LEFT JOIN (
                SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                        SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                FROM    AW_002_000002_000001 AS z
                GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY
             ) AS s
               ON  s.SCENARIO = a.SCENARIO
              AND  s.PERIODE  = a.PERIODE
              AND  s.EXERCICE = a.EXERCICE
              AND  s.ENTITY   = a.ENTITY
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
     ) AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
