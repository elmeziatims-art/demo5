/* =============================================================================
   Q_COCKPIT_COMPLET  —  SQL SERVER, forme enrobable par Tagetik.
   Une seule requete pour LE BANDEAU DE TUILES et LA GRILLE DU PORTEFEUILLE.

   Une ligne par CAMPUS : ENTITY ne contient que des elements finaux, MARQUE
   est portee sur chaque ligne. Toutes les mesures sont ADDITIVES : Tagetik
   agrege sur le noeud qu'il veut, le resultat reste juste.

   Regles Tagetik : pas de CTE, pas de ORDER BY, pas de ';'
   -- le loader enrobe la requete dans SELECT COUNT(*) FROM ( ... ) X.

   =============================================================================
   CE QUI A CHANGE, ET POURQUOI LES COLONNES N-1 SORTAIENT A ZERO
   =============================================================================

   1. LE N-1 NE DEPEND PLUS DE LA VERSION.
      L'ancienne version exigeait p.VERSION = n.VERSION. Or V_ALLOCATION force
      'ACT' en dur sur la branche historique et reprend m.VERSION de V_MOTEUR
      sur la branche budget. Des que les deux different, aucune ligne N ne
      retrouve son N-1 et le COALESCE renvoie 0 : c'est exactement le symptome
      sur INSCRITS_N1 et SPEND_ACQ_N1.
      Le OUTER APPLY ci-dessous prend le N-1 de la MEME version quand il
      existe, et se rabat sur l'autre sinon. Une annee de budget retrouve donc
      son realise N-1, ce qui est le comportement attendu d'un cockpit.
      -> pour revenir au comportement strict : ajouter dans le WHERE du APPLY
         la ligne   AND x.VERSION = n.VERSION   et supprimer le ORDER BY.

   2. L'ACQUISITION EST REMONTEE DANS LES DEUX AGREGATS.
      Elle etait raccrochee par deux LEFT JOIN separes (q et q1) qui
      ignoraient VERSION alors que n la portait. SPEND_ACQ et SPEND_ACQ_N1
      viennent maintenant du meme bloc que le reste : une seule cle, un seul
      endroit ou se tromper. Deux jointures de moins.

   3. QUATRE COLONNES N-1 EN PLUS.
      EFFECTIFS_N1 et PLACES_N1 permettent l'ecart de remplissage en POINTS,
      CA_N1 et EBITDA_N1 etaient deja la. Tout ce qu'il faut pour que chaque
      tuile ait son evolution sans seconde requete.

   =============================================================================
   LE BANDEAU (lu a la racine)
       Chiffre d'affaires   =  CA
       EBITDA               =  EBITDA
       Marge EBITDA         =  EBITDA / CA
       Inscrits             =  INSCRITS
       Cout d'acquisition   =  SPEND_ACQ / INSCRITS
       Remplissage          =  EFFECTIFS / PLACES
       Places libres        =  PLACES_LIBRES

   LA GRILLE (juste a TOUS les niveaux)
       D CA          =  CA / CA_N1 - 1
       D EBITDA      =  EBITDA / EBITDA_N1 - 1
       D inscrits    =  INSCRITS / INSCRITS_N1 - 1
       D acquisition =  SPEND_ACQ / SPEND_ACQ_N1 - 1
       D CAC         = (SPEND_ACQ / INSCRITS) / (SPEND_ACQ_N1 / INSCRITS_N1) - 1
       D marge       = (EBITDA / CA - EBITDA_N1 / CA_N1) * 100
       D remplissage = (EFFECTIFS / PLACES - EFFECTIFS_N1 / PLACES_N1) * 100
       Mix alt.      =  EFFECTIFS_ALT / EFFECTIFS
       Part EBITDA   =  PART_EBITDA

   Les deux D en POINTS portent un * 100 : ce sont des ecarts de taux, pas des
   variations relatives. Toutes ces formules divisent des SOMMES, jamais des
   ratios : elles restent justes sur un campus comme sur le groupe.

   Si un exercice n'a pas de N-1 charge, ses colonnes N-1 valent 0 et les
   evolutions doivent etre gardees par un IF( ..._N1 = 0 ; vide ; ... ).

   Sources : V_ALLOCATION et AW_002_000002_000001 (DEPENSE_ACQ, identique au
   compte 6231 de la compta, verifie au centime sur les trois exercices).
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
    n.INSCRITS                          AS INSCRITS,
    n.EFFECTIFS                         AS EFFECTIFS,
    n.EFFECTIFS_ALT                     AS EFFECTIFS_ALT,
    n.PLACES                            AS PLACES,
    n.PLACES - n.EFFECTIFS              AS PLACES_LIBRES,
    n.SPEND_ACQ                         AS SPEND_ACQ,

    COALESCE(p.CA,         0)           AS CA_N1,
    COALESCE(p.EBITDA,     0)           AS EBITDA_N1,
    COALESCE(p.INSCRITS,   0)           AS INSCRITS_N1,
    COALESCE(p.EFFECTIFS,  0)           AS EFFECTIFS_N1,
    COALESCE(p.PLACES,     0)           AS PLACES_N1,
    COALESCE(p.SPEND_ACQ,  0)           AS SPEND_ACQ_N1,

    1.0 * n.EBITDA
        / NULLIF(SUM(n.EBITDA) OVER (PARTITION BY n.SCENARIO, n.VERSION,
                                                  n.PERIODE,  n.EXERCICE), 0)
                                        AS PART_EBITDA
FROM (
        SELECT  v.SCENARIO, v.VERSION, v.PERIODE, v.EXERCICE, v.MARQUE, v.ENTITY,
                v.CA, v.EBITDA, v.INSCRITS, v.EFFECTIFS, v.EFFECTIFS_ALT, v.PLACES,
                COALESCE(s.SPEND_ACQ, 0) AS SPEND_ACQ
        FROM (
                SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                        SUM(a.CA)                          AS CA,
                        SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                        SUM(a.VOL_NEW)                     AS INSCRITS,
                        SUM(a.VOL_EFF)                     AS EFFECTIFS,
                        SUM(CASE WHEN a.MODALITE = 'ALT' THEN a.VOL_EFF ELSE 0 END) AS EFFECTIFS_ALT,
                        SUM(a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                                               WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                                               ELSE 30 END) AS PLACES
                FROM    V_ALLOCATION AS a
                GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
             ) AS v
        LEFT JOIN (
                SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                        SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                FROM    AW_002_000002_000001 AS z
                GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY
             ) AS s
               ON  s.SCENARIO = v.SCENARIO
              AND  s.PERIODE  = v.PERIODE
              AND  s.EXERCICE = v.EXERCICE
              AND  s.ENTITY   = v.ENTITY
     ) AS n
OUTER APPLY (
        SELECT TOP 1
                x.CA, x.EBITDA, x.INSCRITS, x.EFFECTIFS, x.PLACES, x.SPEND_ACQ
        FROM (
                SELECT  w.SCENARIO, w.VERSION, w.PERIODE, w.EXERCICE, w.ENTITY,
                        w.CA, w.EBITDA, w.INSCRITS, w.EFFECTIFS, w.PLACES,
                        COALESCE(s2.SPEND_ACQ, 0) AS SPEND_ACQ
                FROM (
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                SUM(a.CA)                  AS CA,
                                SUM(a.CA - a.COST_COMPLET) AS EBITDA,
                                SUM(a.VOL_NEW)             AS INSCRITS,
                                SUM(a.VOL_EFF)             AS EFFECTIFS,
                                SUM(a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                                                       WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                                                       ELSE 30 END) AS PLACES
                        FROM    V_ALLOCATION AS a
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
                     ) AS w
                LEFT JOIN (
                        SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                                SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                        FROM    AW_002_000002_000001 AS z
                        GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY
                     ) AS s2
                       ON  s2.SCENARIO = w.SCENARIO
                      AND  s2.PERIODE  = w.PERIODE
                      AND  s2.EXERCICE = w.EXERCICE
                      AND  s2.ENTITY   = w.ENTITY
             ) AS x
        WHERE   x.SCENARIO = n.SCENARIO
          AND   x.PERIODE  = n.PERIODE
          AND   x.ENTITY   = n.ENTITY
          AND   CAST(x.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
        ORDER BY CASE WHEN x.VERSION = n.VERSION THEN 0 ELSE 1 END
     ) AS p
