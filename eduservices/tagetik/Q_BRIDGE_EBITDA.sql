/* =============================================================================
   Q_BRIDGE_EBITDA  —  SQL SERVER, forme enrobable par Tagetik.
   Le tableau EXACT qui est derriere le graphe "Bridge EBITDA N-1 -> N".

   Une ligne par CAMPUS x EFFET (7 effets), donc 7 x 14 = 98 lignes par
   exercice. ENTITY ne contient que des elements finaux, MARQUE est portee sur
   chaque ligne : la matrice se filtre sur la marque et Tagetik somme.

   Regles Tagetik : pas de CTE, pas de ORDER BY, pas de ';'.

   --------------------------------------------------------------------------
   LES SEPT LIGNES, dans l'ordre RANG

     1  EBITDA N-1                 le point de depart
     2  Effet effectifs            (EFF_N - EFF_P) x (CA/eleve_P - CVAR/eleve_P)
     3  Effet prix et mix          (CA/eleve_N - CA/eleve_P) x EFF_N
     4  Effet cout variable unitaire  -(CVAR/eleve_N - CVAR/eleve_P) x EFF_N
     5  Effet couts directs        -(CDIR_N - CDIR_P)
     6  Effet siege                -(CSIEGE_N - CSIEGE_P)
     7  EBITDA N                   le point d'arrivee

   La decomposition est EXACTE par construction : la variation de CA et celle
   du cout variable sont chacune coupees en volume x unitaire, et 2+3+4+5+6
   redonne exactement EBITDA_N - EBITDA_P. Aucun residu, aucun "non alloue".

   --------------------------------------------------------------------------
   TROIS MESURES, TOUTES ADDITIVES

     MONTANT   la hauteur de la barre (positive ou negative)
     BASE      le bas de la barre flottante   (cumul avant l'effet)
     CUMUL     le haut de la barre flottante  (cumul apres l'effet)

   Les trois s'additionnent sur n'importe quel noeud d'entite. NE PAS calculer
   ici le socle invisible du graphe : il vaut MIN(BASE, CUMUL) et le MIN n'est
   pas additif. Le report le calcule APRES la somme :

       socle invisible = MIN( SUM(BASE) ; SUM(CUMUL) )
       hauteur tracee  = ABS( SUM(MONTANT) )

   Ne pas totaliser la colonne MONTANT : les rangs 1 et 7 sont des NIVEAUX,
   pas des effets. Un total vaudrait EBITDA_P + delta + EBITDA_N.

   --------------------------------------------------------------------------
   Filtrer EXERCICE = 2026 donne le bridge 2025 -> 2026. La requete produit
   tous les exercices qui ont un N-1 disponible.
   Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    b.SCENARIO,
    b.VERSION,
    b.PERIODE,
    b.EXERCICE,
    b.EXERCICE_N1,
    b.MARQUE,
    b.ENTITY,
    e.RANG,
    e.EFFET,

    CASE e.RANG
        WHEN 1 THEN b.EBITDA_P
        WHEN 2 THEN b.E_VOL
        WHEN 3 THEN b.E_PRIX
        WHEN 4 THEN b.E_CVAR
        WHEN 5 THEN b.E_CDIR
        WHEN 6 THEN b.E_SIEGE
        ELSE        b.EBITDA_N
    END                                                     AS MONTANT,

    CASE e.RANG
        WHEN 1 THEN 0
        WHEN 2 THEN b.EBITDA_P
        WHEN 3 THEN b.EBITDA_P + b.E_VOL
        WHEN 4 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX
        WHEN 5 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX + b.E_CVAR
        WHEN 6 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX + b.E_CVAR + b.E_CDIR
        ELSE        0
    END                                                     AS BASE,

    CASE e.RANG
        WHEN 1 THEN b.EBITDA_P
        WHEN 2 THEN b.EBITDA_P + b.E_VOL
        WHEN 3 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX
        WHEN 4 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX + b.E_CVAR
        WHEN 5 THEN b.EBITDA_P + b.E_VOL + b.E_PRIX + b.E_CVAR + b.E_CDIR
        ELSE        b.EBITDA_N
    END                                                     AS CUMUL
FROM (
        SELECT
            n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE, n.MARQUE, n.ENTITY,
            p.EXERCICE                                      AS EXERCICE_N1,
            p.EBITDA                                        AS EBITDA_P,
            n.EBITDA                                        AS EBITDA_N,

            /* 2. effet effectifs : le volume gagne, valorise a la marge sur
                  cout variable de l'annee precedente */
            (n.EFFECTIFS - p.EFFECTIFS)
              * (1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)
                 - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0))            AS E_VOL,

            /* 3. effet prix et mix : ce que rapporte un eleve en plus ou en moins */
            (1.0 * n.CA / NULLIF(n.EFFECTIFS, 0)
             - 1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS        AS E_PRIX,

            /* 4. effet cout variable unitaire */
            -1 * (1.0 * n.COST_VAR / NULLIF(n.EFFECTIFS, 0)
                  - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0)) * n.EFFECTIFS AS E_CVAR,

            /* 5. couts directs : permanents et structure du campus, en bloc */
            -1 * (n.COST_DIR - p.COST_DIR)                               AS E_CDIR,

            /* 6. siege redescendu */
            -1 * (n.COST_SIEGE - p.COST_SIEGE)                           AS E_SIEGE
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
        VALUES (1, '1. EBITDA N-1'),
               (2, '2. Effet effectifs'),
               (3, '3. Effet prix et mix'),
               (4, '4. Effet cout variable unitaire'),
               (5, '5. Effet couts directs'),
               (6, '6. Effet siege'),
               (7, '7. EBITDA N')
     ) AS e(RANG, EFFET)
