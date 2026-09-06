/* =============================================================================
   Q_D1_TABLEAU  —  DRILL-THROUGH sur une cellule d'EBITDA.
   "Pourquoi l'EBITDA a bouge" : le tableau, sept lignes.

     RANG      l'ordre de lecture
     EFFET     le libelle
     MONTANT   la contribution en euros
     PART_VAR  la part de la variation totale, vide sur les deux niveaux

   La requete herite du contexte de la cellule cliquee : l'entite et
   l'exercice. Elle vaut donc pour n'importe quelle cellule du cockpit, groupe,
   marque ou campus, sans qu'on ait rien a coder.

       AND a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
       AND a.EXERCICE IN (${$ANL_EXERCICE.code})

   Le premier resout un noeud en ses feuilles et une feuille en elle-meme,
   donc il couvre les trois niveaux. Si le drill passe deja une feuille seule,
   ${$Entity.code} suffit.

   L'annee precedente n'est PAS filtree par parametre : la jointure va la
   chercher toute seule sur EXERCICE - 1. C'est ce qui permet de cliquer sur
   2026 comme sur 2025 sans changer la requete.

   =============================================================================
   LA DECOMPOSITION, ET POURQUOI ELLE TOMBE JUSTE

     1  EBITDA N-1                le point de depart
     2  Effet effectifs           (EFF_N - EFF_P) x (CA/eleve_P - CVAR/eleve_P)
     3  Effet prix et mix         (CA/eleve_N - CA/eleve_P) x EFF_N
     4  Effet cout variable unit. -(CVAR/eleve_N - CVAR/eleve_P) x EFF_N
     5  Effet couts directs       -(CDIR_N - CDIR_P)
     6  Effet siege               -(CSIEGE_N - CSIEGE_P)
     7  EBITDA N                  le point d'arrivee

   La variation du CA et celle du cout variable sont chacune coupees en
   volume x unitaire. Les lignes 2 a 6 redonnent donc EXACTEMENT EBITDA N moins
   EBITDA N-1, sans residu et sans ligne "non alloue".

   Ne pas totaliser MONTANT : les rangs 1 et 7 sont des NIVEAUX, pas des
   effets. Un total vaudrait EBITDA N-1 + variation + EBITDA N.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    e.RANG,
    e.EFFET,

    CAST(ROUND(
        CASE e.RANG
            WHEN 1 THEN g.EBITDA_P
            WHEN 2 THEN g.E_VOL
            WHEN 3 THEN g.E_PRIX
            WHEN 4 THEN g.E_CVAR
            WHEN 5 THEN g.E_CDIR
            WHEN 6 THEN g.E_SIEGE
            ELSE        g.EBITDA_N
        END
    , 0) AS DECIMAL(18, 0))                                 AS MONTANT,

    CASE WHEN e.RANG IN (1, 7) THEN NULL ELSE
        CAST(ROUND(1.0 *
            CASE e.RANG
                WHEN 2 THEN g.E_VOL
                WHEN 3 THEN g.E_PRIX
                WHEN 4 THEN g.E_CVAR
                WHEN 5 THEN g.E_CDIR
                ELSE        g.E_SIEGE
            END / NULLIF(g.EBITDA_N - g.EBITDA_P, 0), 4)
        AS DECIMAL(9, 4)) END                               AS PART_VAR
FROM (
        SELECT
            SUM(x.EBITDA_P) AS EBITDA_P, SUM(x.EBITDA_N) AS EBITDA_N,
            SUM(x.E_VOL)    AS E_VOL,    SUM(x.E_PRIX)   AS E_PRIX,
            SUM(x.E_CVAR)   AS E_CVAR,   SUM(x.E_CDIR)   AS E_CDIR,
            SUM(x.E_SIEGE)  AS E_SIEGE
        FROM (
                SELECT
                    p.EBITDA AS EBITDA_P, n.EBITDA AS EBITDA_N,
                    (n.EFFECTIFS - p.EFFECTIFS)
                      * (1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)
                         - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0))         AS E_VOL,
                    (1.0 * n.CA / NULLIF(n.EFFECTIFS, 0)
                     - 1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS     AS E_PRIX,
                    -1 * (1.0 * n.COST_VAR / NULLIF(n.EFFECTIFS, 0)
                          - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS AS E_CVAR,
                    -1 * (n.COST_DIR   - p.COST_DIR)                          AS E_CDIR,
                    -1 * (n.COST_SIEGE - p.COST_SIEGE)                        AS E_SIEGE
                FROM (
                        SELECT  a.ENTITY, a.EXERCICE,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        WHERE   a.ENTITY   IN (${$Entity(HIERARCHY("EDU")).lowest})
                          AND   a.EXERCICE IN (${$ANL_EXERCICE.code})
                        GROUP BY a.ENTITY, a.EXERCICE
                     ) AS n
                INNER JOIN (
                        SELECT  a.ENTITY, a.EXERCICE,
                                SUM(a.CA)                          AS CA,
                                SUM(a.CA - a.COST_COMPLET)         AS EBITDA,
                                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                                SUM(a.COST_VARIABLE)               AS COST_VAR,
                                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
                        FROM    V_ALLOCATION AS a
                        WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                        GROUP BY a.ENTITY, a.EXERCICE
                     ) AS p
                       ON  p.ENTITY = n.ENTITY
                      AND  CAST(p.EXERCICE AS INT) = CAST(n.EXERCICE AS INT) - 1
             ) AS x
     ) AS g
CROSS JOIN (
        VALUES (1, 'EBITDA N-1'),
               (2, 'Effet effectifs'),
               (3, 'Effet prix et mix'),
               (4, 'Effet cout variable unitaire'),
               (5, 'Effet couts directs'),
               (6, 'Effet siege'),
               (7, 'EBITDA N')
     ) AS e(RANG, EFFET)
