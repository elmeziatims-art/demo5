/* =============================================================================
   Q_PORTEFEUILLE_CLASSES  —  le portefeuille au grain de la CLASSE.
   Marque x campus x programme x annee d'etude x modalite.

   Requete de POPULATION, pas de drill : elle n'a pas de parametre d'entite et
   rend tout le perimetre. C'est la matrice Tagetik qui filtre, replie et
   deplie sur ses propres axes.

   SOIXANTE LIGNES, VINGT COLONNES. Cinq de dimension avec leurs codes, deux
   libelles, et douze mesures -- six par exercice, en colonnes cote a cote.

   =============================================================================
   LES CODES SONT LA, ET C'EST LE POINT QUI COMPTE POUR UNE MATRICE

   MARQUE et ENTITY sont rendus en CODE, a cote de leurs libelles. C'est ce qui
   permet a la matrice de se raccrocher a la hierarchie : grouper, filtrer et
   descendre sur un noeud se fait sur le code, jamais sur le libelle. Une
   requete qui ne rendrait que "MBway Paris" donnerait un tableau qui s'affiche
   mais ne se pilote pas.

   Les libelles viennent de azienda quand ils existent, et retombent sur le
   code sinon -- c'est le cas si un noeud de marque n'est pas porte comme une
   entite dans la dimension.

   =============================================================================
   AUCUN RATIO. QUE DU MATERIAU.

   Ni remplissage, ni CAC, ni marge en pourcentage. Un rapport ne survit pas a
   une somme : le remplissage de trois classes n'est pas la somme de leurs
   remplissages. La requete rend les numerateurs et les denominateurs, la
   matrice divise APRES avoir somme :

       remplissage  = Effectifs / Places
       CAC          = Acquisition / Nouveaux inscrits
       marge EBITDA = EBITDA / CA

   C'est ce qui rend la matrice juste a TOUS ses niveaux de repli -- classe,
   campus, marque, groupe -- sans que la requete ait a savoir ou elle est
   depliee. Les douze colonnes chiffrees sont additives, sans exception.

   =============================================================================
   DEUX PIEGES DU GRAIN FIN, FERMES ET VERIFIES SUR LA DONNEE

   1. L'ACQUISITION. La sous-requete est groupee au MEME grain que
      V_ALLOCATION. Groupee par campus -- comme elle l'est dans le cockpit --
      le total du campus se serait repete sur chacune de ses lignes et
      l'acquisition aurait ete comptee jusqu'a six fois au repli.
      DEPENSE_ACQ est portee ligne par ligne dans le CRM, et seulement par les
      ANNEES D'ENTREE : B1, BTS1, M1. Elle vaut zero ailleurs, ce qui est
      exact -- on depense pour recruter des entrants, pas pour une B3.
      Controle 2026 : 23 lignes servies sur 60, total 434 174, soit le compte
      6231 au centime.

   2. LES PLACES. VOL_CLASS x capacite. Un meme couple campus x programme x
      annee present dans les deux modalites aurait compte ses classes deux
      fois. Zero cas dans la donnee : une classe est d'une modalite ou de
      l'autre. Remplissage 2026 verifie a 76,2 %.

   =============================================================================
   PAS DE REGRESSION : LES REPLIS REDONNENT LES CHIFFRES CONNUS

   Somme des 60 lignes, exercice 2026 :

       CA                23 098 985      la ligne du cockpit
       EBITDA             3 845 790      la cellule d'ou partent les drills
       Effectifs              3 114
       Nouveaux inscrits      1 229
       Places                 4 088
       Acquisition          434 174      le compte 6231

   Et le repli par campus redonne exactement les quatorze lignes du cockpit --
   verifie a l'ecart nul sur les cinq mesures et les quatorze campus.

   =============================================================================
   LITTERAUX EN ASCII, ET C'EST OBLIGATOIRE. 'Mastere', 'Alternance' : les
   chaines ecrites dans la requete ne survivent pas au canal du loader si elles
   portent un accent, elles ressortent en 'Mast?re'. Les ALIAS de colonnes, eux,
   transitent autrement et gardent les leurs.

   Aucune apostrophe dans un alias, meme entre guillemets doubles.
   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Exercices en dur comme le cockpit. Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    v.MARQUE                                                    AS "Marque",
    COALESCE(mq.DESC_AZIENDA0, v.MARQUE)                        AS "Libellé marque",
    v.ENTITY                                                    AS "Campus",
    COALESCE(az.DESC_AZIENDA0, v.ENTITY)                        AS "Libellé campus",
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
LEFT JOIN azienda AS mq
       ON  mq.COD_AZIENDA = v.MARQUE
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
WHERE   CAST(v.EXERCICE AS INT) IN (2025, 2026)
GROUP BY v.MARQUE,
         COALESCE(mq.DESC_AZIENDA0, v.MARQUE),
         v.ENTITY,
         COALESCE(az.DESC_AZIENDA0, v.ENTITY),
         v.PROGRAMME,
         CASE WHEN v.PROGRAMME LIKE 'BAC%' THEN 'Bachelor'
              WHEN v.PROGRAMME LIKE 'MAS%' THEN 'Mastere'
              ELSE 'BTS' END,
         v.AN_ETUDE,
         CASE WHEN v.MODALITE = 'ALT' THEN 'Alternance'
              ELSE 'Initial' END
