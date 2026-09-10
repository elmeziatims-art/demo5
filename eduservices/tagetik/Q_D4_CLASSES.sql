/* =============================================================================
   Q_D4_CLASSES  —  DRILL-THROUGH sur une ligne de campus du cockpit.
   "DE QUOI CE CAMPUS EST-IL FAIT" : le detail par classe.

   Le cockpit garde ses QUATORZE LIGNES. Celle-ci ne s'affiche que quand on
   double-clique -- c'est le drill natif Tagetik qui la declenche, et elle est
   donc filtree sur la cellule cliquee. Un campus rend quatre a six lignes,
   pas soixante : le detail n'encombre jamais la vue de tete.

   =============================================================================
   PAS DE RACCORD N-1, ET C'EST CE QUI SIMPLIFIE TOUT

   Les deux exercices sont en COLONNES, cote a cote, comme dans Q_D1_SOCLE et
   Q_D2_SOCLE. Il n'y a donc ni OUTER APPLY, ni jointure sur l'annee
   precedente, ni la question "meme classe ou meme cohorte" : une ligne porte
   la B1 de 2025 et la B1 de 2026, et le lecteur compare ce qu'il voit.

   =============================================================================
   AUCUN RATIO ICI. QUE DU MATERIAU.

   Ni remplissage, ni CAC, ni marge en pourcentage. Ce sont des rapports, et un
   rapport ne survit pas a une somme : le remplissage de trois classes n'est
   pas la somme de leurs remplissages. La requete rend donc les numerateurs et
   les denominateurs, le rapport les calcule apres avoir somme :

       remplissage  = Effectifs / Places
       CAC          = Acquisition / Nouveaux inscrits
       marge EBITDA = EBITDA / CA

   Toutes les colonnes chiffrees sont additives. Sommer les lignes d'un campus
   redonne exactement sa ligne de cockpit -- verifie a l'ecart nul sur les
   quatorze campus.

   =============================================================================
   DEUX POINTS VERIFIES SUR LA DONNEE, PARCE QUE LE GRAIN FIN LES EXPOSE

   1. L'ACQUISITION. DEPENSE_ACQ est portee LIGNE PAR LIGNE dans le CRM, et
      seulement par les ANNEES D'ENTREE -- B1, BTS1, M1. Elle vaut zero sur une
      B2 ou une B3, ce qui est exact : on depense pour recruter des entrants.
      Le CAC est donc lisible sur les lignes d'entree et vide ailleurs, au lieu
      d'etre faux partout.
      Controle 2026 : 23 lignes servies sur 60, total 434 174, soit le compte
      6231 au centime.

      C'est pour cela que la sous-requete d'acquisition est groupee au MEME
      grain que V_ALLOCATION. Groupee par campus, comme dans le cockpit, elle
      aurait repete le total du campus sur chacune de ses lignes.

   2. LES PLACES. VOL_CLASS x capacite. Un meme couple campus x programme x
      annee present dans les deux modalites aurait compte ses classes deux
      fois. Zero cas dans la donnee : une classe est d'une modalite ou de
      l'autre. Remplissage 2026 verifie a 76,2 %.

   =============================================================================
   LES LIBELLES

   CAMPUS vient de azienda. CYCLE et MODALITE sont deduits -- le prefixe du
   programme et la modalite ne laissent aucune place au doute. Il n'existe pas
   de table de libelles pour PROGRAMME : son code est rendu tel quel plutot
   qu'invente.

   Comme Q_D1_SOCLE et Q_D2_SOCLE, la requete ne filtre pas sur VERSION : sur
   2025 et 2026 la base n'en porte qu'une, et c'est ce qui fait que ces trois
   drills tombent exactement sur le cockpit.

   =============================================================================
   POUR LA TESTER HORS DRILL

   Le parametre ${$Entity(...)} n'a de valeur que dans un contexte de
   drill-through : une cellule cliquee. Lance dans l'editeur, il se resout en
   chaine vide, la clause devient  WHERE V.ENTITY IN ( '' )  -- du SQL
   parfaitement valide, qui ne trouve simplement aucun campus. ZERO LIGNE,
   sans la moindre erreur.

   Pour verifier le SQL lui-meme, remplacer la ligne du WHERE par un campus en
   dur, lancer, puis remettre le parametre :

       WHERE   v.ENTITY IN ('MBWAY_PAR')

   Attendu sur MBway Paris : quatre a six lignes, et la somme de la colonne
   "EBITDA 2026" egale a la valeur de la cellule d'ou part le drill.

   LITTERAUX EN ASCII, ET C'EST OBLIGATOIRE. Les chaines ecrites dans la
   requete -- 'Mastere', 'Alternance' -- ne survivent pas au canal du loader si
   elles portent un accent : elles ressortent en 'Mast?re'. Les ALIAS de
   colonnes, eux, transitent autrement et gardent les leurs.

   =============================================================================
   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Perimetre herite de la cellule cliquee, exercices en dur comme le cockpit.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    COALESCE(az.DESC_AZIENDA0, v.ENTITY)                        AS "Campus",
    v.PROGRAMME                                                 AS "Programme",
    CASE WHEN v.PROGRAMME LIKE 'BAC%' THEN 'Bachelor'
         WHEN v.PROGRAMME LIKE 'MAS%' THEN 'Mastere'
         ELSE 'BTS' END                                         AS "Cycle",
    v.AN_ETUDE                                                  AS "Année",
    CASE WHEN v.MODALITE = 'ALT' THEN 'Alternance'
         ELSE 'Initial' END                                     AS "Modalité",

    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2025 THEN v.VOL_EFF ELSE 0 END)  AS "Effectifs 2025",
    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2026 THEN v.VOL_EFF ELSE 0 END)  AS "Effectifs 2026",

    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2025 THEN v.VOL_NEW ELSE 0 END)  AS "Nouveaux inscrits 2025",
    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2026 THEN v.VOL_NEW ELSE 0 END)  AS "Nouveaux inscrits 2026",

    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2025
             THEN v.VOL_CLASS * CASE WHEN v.PROGRAMME LIKE 'BAC%' THEN 32
                                     WHEN v.PROGRAMME LIKE 'MAS%' THEN 26
                                     ELSE 30 END ELSE 0 END)                 AS "Places 2025",
    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2026
             THEN v.VOL_CLASS * CASE WHEN v.PROGRAMME LIKE 'BAC%' THEN 32
                                     WHEN v.PROGRAMME LIKE 'MAS%' THEN 26
                                     ELSE 30 END ELSE 0 END)                 AS "Places 2026",

    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2025 THEN v.CA ELSE 0 END)       AS "CA 2025",
    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2026 THEN v.CA ELSE 0 END)       AS "CA 2026",

    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2025
             THEN v.CA - v.COST_COMPLET ELSE 0 END)                          AS "EBITDA 2025",
    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2026
             THEN v.CA - v.COST_COMPLET ELSE 0 END)                          AS "EBITDA 2026",

    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2025
             THEN COALESCE(s.SPEND_ACQ, 0) ELSE 0 END)                       AS "Acquisition 2025",
    SUM(CASE WHEN CAST(v.EXERCICE AS INT) = 2026
             THEN COALESCE(s.SPEND_ACQ, 0) ELSE 0 END)                       AS "Acquisition 2026"
FROM    V_ALLOCATION AS v
LEFT JOIN azienda AS az
       ON  az.COD_AZIENDA = v.ENTITY
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
WHERE   v.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(v.EXERCICE AS INT) IN (2025, 2026)
GROUP BY COALESCE(az.DESC_AZIENDA0, v.ENTITY),
         v.PROGRAMME,
         CASE WHEN v.PROGRAMME LIKE 'BAC%' THEN 'Bachelor'
              WHEN v.PROGRAMME LIKE 'MAS%' THEN 'Mastere'
              ELSE 'BTS' END,
         v.AN_ETUDE,
         CASE WHEN v.MODALITE = 'ALT' THEN 'Alternance'
              ELSE 'Initial' END
