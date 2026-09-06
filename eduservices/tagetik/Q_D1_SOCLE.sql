/* =============================================================================
   Q_D1_SOCLE  —  DRILL-THROUGH sur une cellule d'EBITDA, version "socle".
   La requete ne renvoie que de la MATIERE ADDITIVE. Excel fait le reste.

   Une ligne par CAMPUS du perimetre cliquee, onze colonnes, toutes sommables :

     ENTITY     le campus
     EFF_P   EFF_N      effectifs, annee precedente et annee courante
     CA_P    CA_N       chiffre d'affaires
     CVAR_P  CVAR_N     cout variable
     CDIR_P  CDIR_N     couts directs, permanents et structure du campus
     SIEGE_P SIEGE_N    siege redescendu

   Aucun ratio, aucun test de signe, aucune division : rien qui puisse se
   fausser en s'agregeant. Tout le calcul d'effets se fait dans le classeur.

   =============================================================================
   POURQUOI UNE LIGNE PAR CAMPUS, ET PAS UN SEUL TOTAL

   On pourrait ne renvoyer qu'une ligne agregee et calculer les effets dessus.
   Le total retomberait juste, mais la REPARTITION entre effets changerait : le
   CA par eleve du groupe melange des campus a 7 123 EUR et d'autres a plus de
   8 000, si bien qu'un simple deplacement d'eleves entre campus, sans aucune
   hausse tarifaire, se lirait comme un effet prix.

   Sur le groupe 2025 -> 2026 l'ecart est de 1 515 EUR sur l'effet effectifs et
   1 946 EUR sur l'effet prix. Peu de chose, mais c'est de la mecanique, pas du
   metier. En gardant le grain campus, chaque eleve est valorise a la marge de
   SON campus.

   Sur une cellule de campus, les deux methodes donnent evidemment le meme
   resultat : il n'y a qu'une ligne.

   =============================================================================
   CE QUE LE CLASSEUR CALCULE ENSUITE, ligne a ligne puis somme

     effet effectifs   = (EFF_N - EFF_P) x (CA_P/EFF_P - CVAR_P/EFF_P)
     effet prix et mix = (CA_N/EFF_N - CA_P/EFF_P) x EFF_N
     effet cout var.   = -(CVAR_N/EFF_N - CVAR_P/EFF_P) x EFF_N
     effet couts dir.  = -(CDIR_N - CDIR_P)
     effet siege       = -(SIEGE_N - SIEGE_P)

     EBITDA_P = CA_P - CVAR_P - CDIR_P - SIEGE_P
     EBITDA_N = CA_N - CVAR_N - CDIR_N - SIEGE_N

   Les cinq effets sommes redonnent EBITDA_N - EBITDA_P exactement, campus par
   campus comme au total.

   Contexte herite de la cellule cliquee. L'annee precedente n'est pas filtree
   par parametre : la jointure la trouve sur EXERCICE - 1.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    n.ENTITY,
    p.EFFECTIFS  AS EFF_P,   n.EFFECTIFS  AS EFF_N,
    p.CA         AS CA_P,    n.CA         AS CA_N,
    p.COST_VAR   AS CVAR_P,  n.COST_VAR   AS CVAR_N,
    p.COST_DIR   AS CDIR_P,  n.COST_DIR   AS CDIR_N,
    p.COST_SIEGE AS SIEGE_P, n.COST_SIEGE AS SIEGE_N
FROM (
        SELECT  a.ENTITY, a.EXERCICE,
                SUM(a.CA)                          AS CA,
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
