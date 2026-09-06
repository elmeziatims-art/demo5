/* =============================================================================
   Q_BRIDGE_WATERFALL  —  SQL SERVER, forme enrobable par Tagetik.
   Le bridge EBITDA deja mis en forme pour un graphe en cascade : cinq lignes
   par campus, colonnes SOCLE / ANCRE / HAUSSE / BAISSE prêtes a empiler.

   Regles Tagetik : pas de CTE, pas de ORDER BY, pas de ';'.

   =============================================================================
   A LIRE AVANT DE BRANCHER LE GRAPHE
   =============================================================================

   SOCLE, ANCRE, HAUSSE et BAISSE ne sont PAS additives. Elles reposent sur un
   MIN et sur un test de signe, et ni l'un ni l'autre ne survit a une somme :

       SUM( MAX(x, 0) )  n'est pas  MAX( SUM(x), 0 )

   Ce n'est pas theorique. Sur 2025 -> 2026, l'effet prix vaut +26 EUR sur
   PIGIER_BOR et +35 EUR sur PIGIER_LYO, mais il est negatif sur les douze
   autres campus. Une somme des colonnes calculees ici donnerait au groupe une
   hausse de 61 EUR ET une baisse de 668 EUR sur la meme barre, alors que
   l'effet net vaut -607 EUR.

   D'ou deux usages, et un seul choix a faire :

   1. LA MATRICE MONTRE UN CAMPUS  ->  utiliser SOCLE / ANCRE / HAUSSE / BAISSE
      telles quelles. Elles sont exactes, il n'y a rien a calculer.

   2. LA MATRICE AGREGE (marque, groupe, ou toute selection de campus)
      ->  ignorer ces quatre colonnes et les reconstruire dans le report a
          partir du trio additif MONTANT / BASE / CUMUL, en quatre formules
          d'une ligne, appliquees APRES la somme :

          Ancre  = IF( RANG = 1 OU RANG = 5 ; MONTANT ; 0 )
          Hausse = IF( RANG = 1 OU RANG = 5 ; 0 ; MAX( MONTANT ; 0 ) )
          Baisse = IF( RANG = 1 OU RANG = 5 ; 0 ; MAX( -MONTANT ; 0 ) )
          Socle  = IF( RANG = 1 OU RANG = 5 ; 0 ; MIN( BASE ; CUMUL ) )

      MONTANT, BASE et CUMUL sont additives sur n'importe quel noeud : c'est
      le seul jeu de colonnes sur lequel on peut sommer sans se tromper.

   =============================================================================
   LES CINQ ETAPES

     1  EBITDA N-1     ancre de depart
     2  Activite       (EFF_N - EFF_P) x (CA/eleve_P - CVAR/eleve_P)
     3  Prix / mix     (CA/eleve_N - CA/eleve_P) x EFF_N
     4  Couts          cout variable unitaire + couts directs + siege
     5  EBITDA N       ancre d'arrivee

   La decomposition est exacte : 2 + 3 + 4 redonne exactement EBITDA_N moins
   EBITDA_P, sans residu, campus par campus. Pour ouvrir la barre "Couts" en
   ses trois composantes, prendre Q_BRIDGE_EBITDA et son axe a sept pas.

   Empilement du graphe : SOCLE en bas, invisible, puis ANCRE, HAUSSE et
   BAISSE dans trois series de couleurs differentes.

   Ne pas totaliser MONTANT : les rangs 1 et 5 sont des NIVEAUX, pas des
   effets. Filtrer EXERCICE = 2026 donne le bridge 2025 -> 2026.

   Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    r.SCENARIO,
    r.VERSION,
    r.PERIODE,
    r.EXERCICE,
    r.EXERCICE_N1,
    r.MARQUE,
    r.ENTITY,
    r.RANG,
    r.ETAPE,

    /* --- mise en forme du graphe : exacte au grain CAMPUS uniquement --- */
    CASE WHEN r.RANG IN (1, 5) THEN 0
         WHEN r.BASE < r.CUMUL THEN r.BASE
         ELSE r.CUMUL END                                   AS SOCLE,
    CASE WHEN r.RANG IN (1, 5) THEN r.MONTANT
         ELSE 0 END                                         AS ANCRE,
    CASE WHEN r.RANG IN (1, 5) THEN 0
         WHEN r.MONTANT > 0 THEN r.MONTANT
         ELSE 0 END                                         AS HAUSSE,
    CASE WHEN r.RANG IN (1, 5) THEN 0
         WHEN r.MONTANT < 0 THEN -1 * r.MONTANT
         ELSE 0 END                                         AS BAISSE,

    /* --- le trio additif : a sommer, puis a remettre en forme dans le report --- */
    r.MONTANT                                               AS MONTANT,
    r.BASE                                                  AS BASE,
    r.CUMUL                                                 AS CUMUL
FROM (
        SELECT
            b.SCENARIO, b.VERSION, b.PERIODE, b.EXERCICE, b.EXERCICE_N1,
            b.MARQUE, b.ENTITY, e.RANG, e.ETAPE,

            CASE e.RANG
                WHEN 1 THEN b.EBITDA_P
                WHEN 2 THEN b.E_VOL
                WHEN 3 THEN b.E_PRIX
                WHEN 4 THEN b.E_CVAR + b.E_CDIR + b.E_SIEGE
                ELSE        b.EBITDA_N
            END                                             AS MONTANT,

            CASE e.RANG
                WHEN 2 THEN b.EBITDA_P
                WHEN 3 THEN b.EBITDA_P + b.E_VOL
                WHEN 4 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX
                ELSE        0
            END                                             AS BASE,

            CASE e.RANG
                WHEN 1 THEN b.EBITDA_P
                WHEN 2 THEN b.EBITDA_P + b.E_VOL
                WHEN 3 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX
                ELSE        b.EBITDA_N
            END                                             AS CUMUL
        FROM (
                SELECT
                    n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE, n.MARQUE, n.ENTITY,
                    p.EXERCICE                              AS EXERCICE_N1,
                    p.EBITDA                                AS EBITDA_P,
                    n.EBITDA                                AS EBITDA_N,
                    (n.EFFECTIFS - p.EFFECTIFS)
                      * (1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)
                         - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0))         AS E_VOL,
                    (1.0 * n.CA / NULLIF(n.EFFECTIFS, 0)
                     - 1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS     AS E_PRIX,
                    -1 * (1.0 * n.COST_VAR / NULLIF(n.EFFECTIFS, 0)
                          - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS AS E_CVAR,
                    -1 * (n.COST_DIR - p.COST_DIR)                            AS E_CDIR,
                    -1 * (n.COST_SIEGE - p.COST_SIEGE)                        AS E_SIEGE
                FROM (
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
                     ) AS n
                INNER JOIN (
                        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
                     ) AS p
                       ON  p.SCENARIO = n.SCENARIO
                      AND  p.VERSION  = n.VERSION
                      AND  p.PERIODE  = n.PERIODE
                      AND  p.ENTITY   = n.ENTITY
                      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
             ) AS b
        CROSS JOIN (
                VALUES (1, 'EBITDA N-1'),
                       (2, 'Activite'),
                       (3, 'Prix / mix'),
                       (4, 'Couts'),
                       (5, 'EBITDA N')
             ) AS e(RANG, ETAPE)
     ) AS r
