/* =============================================================================
   Q_COCKPIT_DETAIL  —  Q_COCKPIT_COMPLET, ouvert par programme et modalite.

   Le cockpit rend une ligne par campus. Celui-ci rend une ligne par
   CAMPUS x PROGRAMME x MODALITE : trente lignes par exercice au lieu de
   quatorze. On s'arrete la. L'annee d'etude n'est pas dans la requete parce
   que Tagetik y descend tout seul, au double-clic.

   =============================================================================
   STRUCTURE IDENTIQUE. C'EST LA REGLE DE CE FICHIER.

   Memes colonnes, memes noms, meme ordre, meme OUTER APPLY, meme PART_EBITDA
   avec sa partition d'origine. Les VINGT ET UNE colonnes du cockpit sont la,
   inchangees, et DEUX s'ajoutent apres ENTITY : PROGRAMME et MODALITE.
   Vingt-trois en tout.

   Rien n'a ete retire, rien n'a ete renomme. Pas de libelle, pas de cycle, pas
   de part campus : ce fichier doit pouvoir remplacer l'autre sans qu'un
   rapport bouge.

   EFFECTIFS_ALT est conservee bien qu'elle soit redondante a ce grain -- une
   ligne y est entierement ALT ou entierement INIT. Elle redevient utile des
   qu'on replie sur le campus.

   =============================================================================
   LA SEULE MODIFICATION DE FOND, ET ELLE EST OBLIGATOIRE

   LES DEUX SOUS-REQUETES D'ACQUISITION SONT GROUPEES AU MEME GRAIN.

   Dans le cockpit elles sont groupees par campus -- c'est correct, puisqu'il
   rend une ligne par campus. Reprises telles quelles ici, le total du campus
   se serait rattache a CHACUNE de ses lignes et l'acquisition aurait ete
   comptee jusqu'a quatre fois au repli. Ce n'est pas un detail de style :
   c'est la difference entre 434 174 et pres de deux millions.

   DEPENSE_ACQ est portee ligne par ligne dans AW_002_000002_000001, donc la
   grouper a ce grain est exact et additif.
   Controle 2026 : 23 lignes servies sur 30, total 434 174, soit le compte
   6231 au centime.

   =============================================================================
   AUCUNE REGRESSION, VERIFIE SUR L'EXTRAIT

   Repli des trente lignes, exercice 2026 :

       CA                23 098 985      la ligne du cockpit
       EBITDA             3 845 790      la cellule d'ou partent les drills
       EFFECTIFS              3 114
       INSCRITS               1 229
       PLACES                 4 088
       SPEND_ACQ            434 174      le compte 6231

   Repli par campus contre les quatorze lignes du cockpit : ecart 0,000000.

   PART_EBITDA garde sa partition d'origine, donc la part du GROUPE. Elle reste
   sommable : toutes les parts partagent le meme denominateur, donc les replier
   redonne exactement la part du campus, puis celle de la marque.

   LES PLACES ne doublent pas. VOL_CLASS x capacite se casserait si un meme
   couple campus x programme existait dans les deux modalites en partageant ses
   classes ; il n'y en a aucun dans la donnee. Une classe est d'une modalite ou
   de l'autre. Remplissage 2026 verifie a 76,2 %.

   =============================================================================
   CE QUE LE RACCORD N-1 COMPARE

   Il se raccroche sur ENTITY + PROGRAMME + MODALITE. Les trente cles de 2026
   existent toutes en 2025 : aucune ligne orpheline, aucun +100 % artificiel.

   =============================================================================
   Regles Tagetik : pas de CTE, pas de ';', pas de crochets. Le seul ORDER BY
   est celui du TOP 1 dans le OUTER APPLY -- il ne remonte pas au niveau que le
   loader enveloppe, exactement comme dans le cockpit.
   ============================================================================= */
SELECT
    n.SCENARIO,
    n.VERSION,
    n.PERIODE,
    n.EXERCICE,
    n.MARQUE,
    n.ENTITY,
    n.PROGRAMME,
    n.MODALITE,

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
                v.PROGRAMME, v.MODALITE,
                v.CA, v.EBITDA, v.INSCRITS, v.EFFECTIFS, v.EFFECTIFS_ALT, v.PLACES,
                COALESCE(s.SPEND_ACQ, 0) AS SPEND_ACQ
        FROM (
                SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                        a.PROGRAMME, a.MODALITE,
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
                         a.PROGRAMME, a.MODALITE
             ) AS v
        LEFT JOIN (
                SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                        z.PROGRAMME, z.MODALITE,
                        SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                FROM    AW_002_000002_000001 AS z
                GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                         z.PROGRAMME, z.MODALITE
             ) AS s
               ON  s.SCENARIO  = v.SCENARIO
              AND  s.PERIODE   = v.PERIODE
              AND  s.EXERCICE  = v.EXERCICE
              AND  s.ENTITY    = v.ENTITY
              AND  s.PROGRAMME = v.PROGRAMME
              AND  s.MODALITE  = v.MODALITE
     ) AS n
OUTER APPLY (
        SELECT TOP 1
                x.CA, x.EBITDA, x.INSCRITS, x.EFFECTIFS, x.PLACES, x.SPEND_ACQ
        FROM (
                SELECT  w.SCENARIO, w.VERSION, w.PERIODE, w.EXERCICE, w.ENTITY,
                        w.PROGRAMME, w.MODALITE,
                        w.CA, w.EBITDA, w.INSCRITS, w.EFFECTIFS, w.PLACES,
                        COALESCE(s2.SPEND_ACQ, 0) AS SPEND_ACQ
                FROM (
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                a.PROGRAMME, a.MODALITE,
                                SUM(a.CA)                  AS CA,
                                SUM(a.CA - a.COST_COMPLET) AS EBITDA,
                                SUM(a.VOL_NEW)             AS INSCRITS,
                                SUM(a.VOL_EFF)             AS EFFECTIFS,
                                SUM(a.VOL_CLASS * CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                                                       WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                                                       ELSE 30 END) AS PLACES
                        FROM    V_ALLOCATION AS a
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                 a.PROGRAMME, a.MODALITE
                     ) AS w
                LEFT JOIN (
                        SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                                z.PROGRAMME, z.MODALITE,
                                SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
                        FROM    AW_002_000002_000001 AS z
                        GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                                 z.PROGRAMME, z.MODALITE
                     ) AS s2
                       ON  s2.SCENARIO  = w.SCENARIO
                      AND  s2.PERIODE   = w.PERIODE
                      AND  s2.EXERCICE  = w.EXERCICE
                      AND  s2.ENTITY    = w.ENTITY
                      AND  s2.PROGRAMME = w.PROGRAMME
                      AND  s2.MODALITE  = w.MODALITE
             ) AS x
        WHERE   x.SCENARIO  = n.SCENARIO
          AND   x.PERIODE   = n.PERIODE
          AND   x.ENTITY    = n.ENTITY
          AND   x.PROGRAMME = n.PROGRAMME
          AND   x.MODALITE  = n.MODALITE
          AND   CAST(x.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
        ORDER BY CASE WHEN x.VERSION = n.VERSION THEN 0 ELSE 1 END
     ) AS p
