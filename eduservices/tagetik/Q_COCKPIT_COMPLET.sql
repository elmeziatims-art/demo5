/* =============================================================================
   Q_COCKPIT_COMPLET  —  SQL SERVER, forme enrobable par Tagetik.
   Une seule requete pour LE BANDEAU DE TUILES et LA GRILLE DU PORTEFEUILLE.

   Une ligne par CAMPUS : ENTITY ne contient que des elements finaux.
   Dix mesures, toutes ADDITIVES (+ PART_EBITDA, additive elle aussi car son
   diviseur est constant sur toutes les lignes). Tagetik agrege sur le noeud
   qu'il veut, le resultat reste juste.

   Regles Tagetik respectees : pas de CTE, pas de ORDER BY, pas de ';'
   -- le loader enrobe la requete dans une sous-requete pour compter les lignes.

   --------------------------------------------------------------------------
   LE BANDEAU (lu a la racine)
       Chiffre d'affaires  =  CA
       EBITDA              =  EBITDA
       Marge EBITDA        =  EBITDA / CA
       Inscrits            =  INSCRITS
       Cout d'acquisition  =  SPEND_ACQ / INSCRITS
       Remplissage         =  EFFECTIFS / PLACES
       Places libres       =  PLACES_LIBRES

   LA GRILLE (a tous les niveaux)
       CA 2026       =  CA                     Marge EBITDA =  EBITDA / CA
       D CA          =  CA / CA_N1 - 1         D marge      = (EBITDA/CA
       EBITDA        =  EBITDA                                - EBITDA_N1/CA_N1) * 100
       D EBITDA      =  EBITDA / EBITDA_N1 - 1 Inscrits     =  INSCRITS
       Part EBITDA   =  PART_EBITDA            Rempl.       =  EFFECTIFS / PLACES
       D inscrits    =  INSCRITS / INSCRITS_N1 - 1
       Mix alt.      =  EFFECTIFS_ALT / EFFECTIFS
       D CAC         = (SPEND_ACQ/INSCRITS) / (SPEND_ACQ_N1/INSCRITS_N1) - 1

   D marge se lit en POINTS : d'ou le * 100.
   --------------------------------------------------------------------------
   Sources : V_ALLOCATION  et  AW_002_000002_000001 (depense d'acquisition).
   Si cette derniere n'existe pas, supprimer les jointures q et q1 et leurs
   deux colonnes : tout le reste fonctionne, seule la tuile CAC disparait.
   ============================================================================= */
SELECT
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.MARQUE,
    n.ENTITY,

    n.CA                            AS CA,
    COALESCE(p.CA, 0)               AS CA_N1,
    n.EBITDA                        AS EBITDA,
    COALESCE(p.EBITDA, 0)           AS EBITDA_N1,
    n.INSCRITS                      AS INSCRITS,
    COALESCE(p.INSCRITS, 0)         AS INSCRITS_N1,
    n.EFFECTIFS                     AS EFFECTIFS,
    n.EFFECTIFS_ALT                 AS EFFECTIFS_ALT,
    n.PLACES                        AS PLACES,
    n.PLACES - n.EFFECTIFS          AS PLACES_LIBRES,
    COALESCE(q.SPEND_ACQ, 0)        AS SPEND_ACQ,
    COALESCE(q1.SPEND_ACQ, 0)       AS SPEND_ACQ_N1,

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
                SUM(a.CA - a.COST_COMPLET)                AS EBITDA,
                SUM(a.VOL_NEW)                            AS INSCRITS
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
     ) AS p
       ON  p.SCENARIO = n.SCENARIO
      AND  p.VERSION  = n.VERSION
      AND  p.PERIODE  = n.PERIODE
      AND  p.ENTITY   = n.ENTITY
      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
LEFT JOIN (
        SELECT  s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY,
                SUM(s.DEPENSE_ACQ) AS SPEND_ACQ
        FROM    AW_002_000002_000001 AS s
        GROUP BY s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY
     ) AS q
       ON  q.SCENARIO = n.SCENARIO
      AND  q.PERIODE  = n.PERIODE
      AND  q.ENTITY   = n.ENTITY
      AND  q.EXERCICE = n.EXERCICE
LEFT JOIN (
        SELECT  s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY,
                SUM(s.DEPENSE_ACQ) AS SPEND_ACQ
        FROM    AW_002_000002_000001 AS s
        GROUP BY s.SCENARIO, s.PERIODE, s.EXERCICE, s.ENTITY
     ) AS q1
       ON  q1.SCENARIO = n.SCENARIO
      AND  q1.PERIODE  = n.PERIODE
      AND  q1.ENTITY   = n.ENTITY
      AND  CAST(q1.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
