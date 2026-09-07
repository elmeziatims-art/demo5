/* =============================================================================
   Q_COCKPIT_DETAIL  —  le cockpit descendu au grain de la CLASSE.
   Campus x programme x annee d'etude x modalite. Soixante lignes par exercice
   la ou Q_COCKPIT_COMPLET en rend quatorze.

   =============================================================================
   ELLE PEUT REMPLACER Q_COCKPIT_COMPLET, ET C'EST VOULU

   Toutes les mesures sont ADDITIVES. Sommer les soixante lignes d'un campus
   redonne exactement la ligne de campus : CA, EBITDA, inscrits, effectifs,
   places, depense d'acquisition, et les six colonnes N-1. PART_EBITDA aussi --
   c'est une part d'un total unique, donc les parts s'additionnent.

   Ne se somment JAMAIS, ici comme ailleurs : le CAC, le taux de remplissage,
   la marge en pourcentage. Ce sont des rapports. Le rapport se calcule APRES
   la somme, dans le rapport Tagetik ou dans le classeur -- jamais ici.

   =============================================================================
   TROIS PIEGES DU GRAIN FIN, ET COMMENT ILS SONT TRAITES

   1. LA DEPENSE D'ACQUISITION. Q_COCKPIT_COMPLET l'agrege par campus. Reprise
      telle quelle au grain fin, le total du campus se serait repete sur chacune
      de ses lignes et l'acquisition aurait ete comptee jusqu'a six fois.
      Verification faite : DEPENSE_ACQ est portee LIGNE PAR LIGNE dans
      AW_002_000002_000001. On la prend donc directement, sans agregat.

      Mieux : elle n'est portee que par les ANNEES D'ENTREE -- B1, BTS1, M1 --
      et vaut zero ailleurs. C'est exact : on depense pour recruter des
      entrants. Le CAC devient donc lisible ligne a ligne, la ou il n'avait
      aucun sens sur une B3.
      Controle 2026 : 23 lignes servies sur 60, total 434 174, soit le compte
      6231 au centime.

   2. LES PLACES. VOL_CLASS x capacite, comme avant. Le risque etait qu'un meme
      couple campus x programme x annee existe en initial ET en alternance : les
      classes auraient ete comptees deux fois. Verification faite sur 2026 :
      ZERO couple dans ce cas. Une classe est d'une modalite ou de l'autre.
      Le remplissage reste donc juste a tous les niveaux.

   3. LE N-1. Il se raccroche maintenant sur ENTITY + PROGRAMME + AN_ETUDE +
      MODALITE. Attention a ce que cela compare :

         c'est la MEME PLACE DANS LA STRUCTURE, pas la meme cohorte.

      Le B1 de 2026 est confronte au B1 de 2025, pas aux memes etudiants -- eux
      sont passes en B2. C'est la bonne comparaison pour piloter : "mon entree
      a-t-elle grossi", "ma M1 se remplit-elle mieux". Pour suivre une COHORTE
      il faudrait decaler l'annee d'etude dans le raccord, et c'est une autre
      question.
      Verification faite : les soixante cles de 2026 existent toutes en 2025.
      Aucune ligne orpheline, aucun +100 % artificiel.

   =============================================================================
   CE QUI A ETE AJOUTE

     PROGRAMME, AN_ETUDE, MODALITE   les trois dimensions demandees
     CAMPUS                          le libelle, pas le code (DESC_AZIENDA0)
     CYCLE                           Bachelor / Mastere / BTS, deduit du prefixe
     MODALITE_LIB                    Initial / Alternance
     CLASSE                          un libelle lisible d'un coup d'oeil
     PART_EBITDA_CAMPUS              la part de la ligne DANS SON CAMPUS

   PART_EBITDA garde son sens d'origine : la part du groupe. Au grain fin elle
   devient minuscule, d'ou l'ajout de la part campus, qui est celle qu'on lit
   quand on ouvre un campus.

   Il n'existe pas de table de libelles pour PROGRAMME -- seules azienda et
   conto en portent. CYCLE et MODALITE_LIB sont donc deduits, ce qui est sur :
   le prefixe et la modalite ne laissent aucune place au doute. Le code du
   programme est conserve tel quel plutot qu'invente.

   EFFECTIFS_ALT est conservee pour ne rien casser dans le rapport existant,
   mais au grain fin elle est redondante : une ligne est entierement ALT ou
   entierement INIT. Elle reste utile des qu'on somme.

   =============================================================================
   Regles Tagetik : pas de CTE, pas de ORDER BY exterieur, pas de ';'. Le seul
   ORDER BY est celui du TOP 1 dans le OUTER APPLY -- il ne remonte pas au
   niveau que le loader enveloppe. Pas de crochets dans les alias.
   ============================================================================= */
SELECT
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.MARQUE,
    n.ENTITY,
    COALESCE(az.DESC_AZIENDA0, n.ENTITY)    AS CAMPUS,
    n.PROGRAMME,
    CASE WHEN n.PROGRAMME LIKE 'BAC%' THEN 'Bachelor'
         WHEN n.PROGRAMME LIKE 'MAS%' THEN 'Mastere'
         ELSE 'BTS' END                     AS CYCLE,
    n.AN_ETUDE,
    n.MODALITE,
    CASE WHEN n.MODALITE = 'ALT' THEN 'Alternance' ELSE 'Initial' END AS MODALITE_LIB,
    n.PROGRAMME + ' ' + n.AN_ETUDE + ' - '
      + CASE WHEN n.MODALITE = 'ALT' THEN 'alternance' ELSE 'initial' END AS CLASSE,

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
                                        AS PART_EBITDA,
    1.0 * n.EBITDA
        / NULLIF(SUM(n.EBITDA) OVER (PARTITION BY n.SCENARIO, n.VERSION,
                                                  n.PERIODE,  n.EXERCICE,
                                                  n.ENTITY), 0)
                                        AS PART_EBITDA_CAMPUS
FROM (
        SELECT  v.SCENARIO, v.VERSION, v.PERIODE, v.EXERCICE, v.MARQUE, v.ENTITY,
                v.PROGRAMME, v.AN_ETUDE, v.MODALITE,
                v.CA, v.EBITDA, v.INSCRITS, v.EFFECTIFS, v.EFFECTIFS_ALT, v.PLACES,
                COALESCE(s.SPEND_ACQ, 0) AS SPEND_ACQ
        FROM (
                SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                        a.PROGRAMME, a.AN_ETUDE, a.MODALITE,
                        SUM(a.CA)                          AS CA,
                        SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                        SUM(a.VOL_NEW)                     AS INSCRITS,
                        SUM(a.VOL_EFF)                     AS EFFECTIFS,
                        SUM(CASE WHEN a.MODALITE = 'ALT' THEN a.VOL_EFF ELSE 0 END) AS EFFECTIFS_ALT,
                        SUM(a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                                               WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                                               ELSE 30 END) AS PLACES
                FROM    V_ALLOCATION AS a
                GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                         a.PROGRAMME, a.AN_ETUDE, a.MODALITE
             ) AS v
        LEFT JOIN (
                SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                        z.PROGRAMME, z.AN_ETUDE, z.MODALITE,
                        SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                FROM    AW_002_000002_000001 AS z
                GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                         z.PROGRAMME, z.AN_ETUDE, z.MODALITE
             ) AS s
               ON  s.SCENARIO  = v.SCENARIO
              AND  s.PERIODE   = v.PERIODE
              AND  s.EXERCICE  = v.EXERCICE
              AND  s.ENTITY    = v.ENTITY
              AND  s.PROGRAMME = v.PROGRAMME
              AND  s.AN_ETUDE  = v.AN_ETUDE
              AND  s.MODALITE  = v.MODALITE
     ) AS n
LEFT JOIN azienda AS az
       ON  az.COD_AZIENDA = n.ENTITY
OUTER APPLY (
        SELECT TOP 1
                x.CA, x.EBITDA, x.INSCRITS, x.EFFECTIFS, x.PLACES, x.SPEND_ACQ
        FROM (
                SELECT  w.SCENARIO, w.VERSION, w.PERIODE, w.EXERCICE, w.ENTITY,
                        w.PROGRAMME, w.AN_ETUDE, w.MODALITE,
                        w.CA, w.EBITDA, w.INSCRITS, w.EFFECTIFS, w.PLACES,
                        COALESCE(s2.SPEND_ACQ, 0) AS SPEND_ACQ
                FROM (
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                a.PROGRAMME, a.AN_ETUDE, a.MODALITE,
                                SUM(a.CA)                  AS CA,
                                SUM(a.CA - a.COST_COMPLET) AS EBITDA,
                                SUM(a.VOL_NEW)             AS INSCRITS,
                                SUM(a.VOL_EFF)             AS EFFECTIFS,
                                SUM(a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                                                       WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                                                       ELSE 30 END) AS PLACES
                        FROM    V_ALLOCATION AS a
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                 a.PROGRAMME, a.AN_ETUDE, a.MODALITE
                     ) AS w
                LEFT JOIN (
                        SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                                z.PROGRAMME, z.AN_ETUDE, z.MODALITE,
                                SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                        FROM    AW_002_000002_000001 AS z
                        GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                                 z.PROGRAMME, z.AN_ETUDE, z.MODALITE
                     ) AS s2
                       ON  s2.SCENARIO  = w.SCENARIO
                      AND  s2.PERIODE   = w.PERIODE
                      AND  s2.EXERCICE  = w.EXERCICE
                      AND  s2.ENTITY    = w.ENTITY
                      AND  s2.PROGRAMME = w.PROGRAMME
                      AND  s2.AN_ETUDE  = w.AN_ETUDE
                      AND  s2.MODALITE  = w.MODALITE
             ) AS x
        WHERE   x.SCENARIO  = n.SCENARIO
          AND   x.PERIODE   = n.PERIODE
          AND   x.ENTITY    = n.ENTITY
          AND   x.PROGRAMME = n.PROGRAMME
          AND   x.AN_ETUDE  = n.AN_ETUDE
          AND   x.MODALITE  = n.MODALITE
          AND   CAST(x.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
        ORDER BY CASE WHEN x.VERSION = n.VERSION THEN 0 ELSE 1 END
     ) AS p
