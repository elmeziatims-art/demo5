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
    n.PLACES                 AS PLACES,

    /* PART_EBITDA — la part dans l'EBITDA du groupe, DEJA ADDITIVE.
       Son diviseur est le meme sur toutes les lignes, donc la somme des
       parts est la part de la somme : au noeud MBway on obtient 45,5 %,
       a la racine 100 %. Aucune formule a ecrire dans le rapport.
       Le diviseur est une FENETRE sur le perimetre de la requete : elle
       se replie sur ce qui est filtre. Passer MBway en parametre fait donc
       de MBway le 100 %, et ses campus se repartissent dessus -- Paris
       34,3 %, Lyon 26,1 %, Nantes 22,1 %, Bordeaux 17,6 %.
       C'est la lecture 'part dans ce que je regarde'. Pour la lecture
       'part dans le groupe', remplacer la fenetre par une sous-requete
       separee jointe sur scenario/version/periode/exercice seulement.
       Le diviseur lui-meme ne peut PAS etre expose en colonne : repete
       sur 14 lignes, il serait somme a 14 fois l'EBITDA groupe.          */
    1.0 * n.EBITDA
        / NULLIF(SUM(n.EBITDA) OVER (PARTITION BY n.SCENARIO, n.VERSION,
                                                  n.PERIODE,  n.EXERCICE), 0)
                             AS PART_EBITDA
FROM (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                SUM(a.CA)                                 AS CA,
                SUM(a.CA - a.COST_COMPLET)                AS EBITDA,
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
                SUM(a.CA - a.COST_COMPLET)                AS EBITDA
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
     ) AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
