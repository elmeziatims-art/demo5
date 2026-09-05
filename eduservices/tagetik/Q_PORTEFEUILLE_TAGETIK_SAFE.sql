/* =============================================================================
   Q_PORTEFEUILLE  —  SQL SERVER, forme ENROBABLE par Tagetik.

   Tagetik n'execute pas la requete telle quelle : son loader l'enrobe dans une
   sous-requete (SELECT ... FROM ( ta requete ) X) pour compter les lignes.
   D'ou trois regles a respecter, sinon "Incorrect syntax near ..." :
       1. PAS de CTE  (WITH)   -> une CTE ne peut pas ouvrir une table derivee
       2. PAS de ORDER BY      -> interdit dans une sous-requete sans TOP
       3. PAS de point-virgule final
   D'ou cette version : sous-requetes en clair, aucune de ces trois choses.

   Une ligne par CAMPUS, huit mesures toutes ADDITIVES.
   ENTITY ne contient que des elements finaux.
   Tagetik agrege sur le noeud qu'il veut, le resultat reste juste.

   LES 10 COLONNES DE LA GRILLE :
       CA 2026       =  CA
       D CA          =  CA / CA_N1 - 1
       EBITDA        =  EBITDA
       D EBITDA      =  EBITDA / EBITDA_N1 - 1
       Part EBITDA   =  EBITDA / EBITDA de la ligne racine   (ref absolue)
       Marge EBITDA  =  EBITDA / CA
       D marge       =  (EBITDA/CA - EBITDA_N1/CA_N1) * 100  (en POINTS)
       Inscrits      =  INSCRITS
       Rempl.        =  EFFECTIFS / PLACES
       Mix alt.      =  EFFECTIFS_ALT / EFFECTIFS
   ============================================================================= */
SELECT
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.MARQUE,
    n.ENTITY,
    n.CA                     AS CA,
    COALESCE(p.CA, 0)        AS CA_N1,
    n.EBITDA                 AS EBITDA,
    COALESCE(p.EBITDA, 0)    AS EBITDA_N1,
    n.INSCRITS               AS INSCRITS,
    n.EFFECTIFS              AS EFFECTIFS,
    n.EFFECTIFS_ALT          AS EFFECTIFS_ALT,
    n.PLACES                 AS PLACES
FROM (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                SUM(a.CA)                                 AS CA,
                SUM(a.CA - a.COST_COMPLET + a.COST_SIEGE) AS EBITDA,
                SUM(a.VOL_NEW)                            AS INSCRITS,
                SUM(a.VOL_EFF)                            AS EFFECTIFS,
                SUM(CASE WHEN a.MODALITE = 'ALT' THEN a.VOL_EFF ELSE 0 END) AS EFFECTIFS_ALT,
                SUM(a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                                       WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                                       ELSE 30 END)       AS PLACES
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
     ) AS n
LEFT JOIN (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                SUM(a.CA)                                 AS CA,
                SUM(a.CA - a.COST_COMPLET + a.COST_SIEGE) AS EBITDA
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
     ) AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
