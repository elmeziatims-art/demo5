/* =============================================================================
   Q_MARGE_PAR_MARQUE  —  SQL SERVER, forme enrobable par Tagetik.
   Le tableau EXACT qui est derriere le graphe "Marge EBITDA par marque".

   Une ligne par CAMPUS x EXERCICE. ENTITY ne contient que des elements
   finaux, MARQUE est portee sur chaque ligne : la matrice se filtre sur la
   marque, ou l'utilise en axe, et Tagetik somme les campus qui la composent.

   Regles Tagetik : pas de CTE, pas de ORDER BY, pas de ';'.

   --------------------------------------------------------------------------
   POURQUOI IL N'Y A PAS DE COLONNE "MARGE"

   Une marge ne s'additionne pas. Si la requete renvoyait 18,3 % pour un campus
   et 21,6 % pour un autre, Tagetik afficherait 39,9 % sur la marque. La regle
   ne change pas : la requete expose le NUMERATEUR et le DENOMINATEUR, le
   report fait la division APRES la somme.

       Marge EBITDA      =  SUM(EBITDA) / SUM(CA)
       Marge N-1         =  SUM(EBITDA_N1) / SUM(CA_N1)
       Ecart en points   = (SUM(EBITDA)/SUM(CA) - SUM(EBITDA_N1)/SUM(CA_N1)) * 100

   Ces trois formules sont justes a TOUS les niveaux : campus, marque, groupe.

   --------------------------------------------------------------------------
   LES AUTRES MESURES, toutes additives elles aussi, servent a expliquer la
   marge sans changer de requete :

       CA par eleve            =  SUM(CA) / SUM(EFFECTIFS)
       Cout complet par eleve  =  SUM(COST_COMPLET) / SUM(EFFECTIFS)
       Poids du siege          =  SUM(COST_SIEGE) / SUM(CA)
       Marge avant siege       = (SUM(CA) - SUM(COST_VARIABLE)
                                  - SUM(COST_DIRECT)) / SUM(CA)

   La derniere est celle qui compte pour juger un directeur de campus : elle
   ne le tient pas comptable d'une charge de siege qu'il ne pilote pas.

   Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.MARQUE,
    n.ENTITY,

    n.CA                                AS CA,
    n.EBITDA                            AS EBITDA,
    n.EFFECTIFS                         AS EFFECTIFS,
    n.COST_VARIABLE                     AS COST_VARIABLE,
    n.COST_DIRECT                       AS COST_DIRECT,
    n.COST_SIEGE                        AS COST_SIEGE,
    n.COST_COMPLET                      AS COST_COMPLET,

    COALESCE(p.CA, 0)                   AS CA_N1,
    COALESCE(p.EBITDA, 0)               AS EBITDA_N1,
    COALESCE(p.EFFECTIFS, 0)            AS EFFECTIFS_N1
FROM (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                SUM(a.CA)                          AS CA,
                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                SUM(a.COST_VARIABLE)               AS COST_VARIABLE,
                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIRECT,
                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                SUM(a.COST_COMPLET)                AS COST_COMPLET
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
     ) AS n
LEFT JOIN (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                SUM(a.CA)                          AS CA,
                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                SUM(a.VOL_EFF)                     AS EFFECTIFS
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
     ) AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
