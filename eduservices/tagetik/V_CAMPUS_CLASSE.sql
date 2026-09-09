/* =============================================================================
   V_CAMPUS_CLASSE  —  SQL SERVER (T-SQL)
   La vue qui alimente le cockpit directeur de campus et le drill.
   Wrapper mince sur V_ALLOCATION + capacite / remplissage / contribution /
   point mort. Une seule vue a lire.

   Grain : SCENARIO x VERSION x PERIODE x EXERCICE x ENTITY x MARQUE
           x PROGRAMME x AN_ETUDE x MODALITE      (= une classe-cohorte)

   Capacite par cycle (parametrable) : BAC 32 · MAS 26 · BTS 30.
   Elle est calculee UNE fois dans la sous-requete, puis reutilisee : en T-SQL
   on ne peut pas referencer un alias du meme SELECT.

   POOL_ODIR     = la poche 604+6063 du CAMPUS, reprise telle quelle de
                   V_ALLOCATION : divisee par l'effectif du campus elle donne le
                   cout marginal d'un eleve de plus, hors 6231.

   CONTRIBUTION  = CA - COST_VARIABLE
                   (couts EVITABLES si on ferme : vacataires + achats directs ;
                    les permanents et la structure, eux, restent)
   POINT_MORT    = cout complet d'UNE classe / marge variable par eleve
                   = combien d'eleves il faut pour couvrir le cout complet charge

   Toutes les divisions sont prefixees de 1.0 : en T-SQL, INT / INT tronque,
   et le remplissage comme le point mort reviendraient a 0 sans aucune erreur.
   ============================================================================= */
CREATE OR ALTER VIEW V_CAMPUS_CLASSE AS
SELECT
    x.SCENARIO, x.VERSION, x.PERIODE, x.EXERCICE,
    x.ENTITY, x.MARQUE, x.PROGRAMME, x.AN_ETUDE, x.MODALITE,
    x.VOL_EFF,
    x.VOL_CLASS,
    x.VOL_NEW,
    x.CA,
    x.CAPACITE,
    x.VOL_CLASS * x.CAPACITE                                        AS PLACES,
    1.0 * x.VOL_EFF / NULLIF(x.VOL_CLASS * x.CAPACITE, 0)           AS REMPLISSAGE,
    x.COST_VARIABLE,
    x.CA - x.COST_VARIABLE                                          AS CONTRIBUTION,
    x.COST_COMPLET,
    x.MARGE_COMPLETE,
    x.COST_SIEGE,
    -- Detail des postes, ajoute pour V_SIMULATION_CLASSES (ouverture / fermeture
    -- de groupe) : il faut savoir CE QUI PART avec le groupe et CE QUI RESTE.
    -- Ajout en fin de vue, donc sans effet sur les lecteurs existants.
    x.COST_VAC, x.COST_PERM, x.COST_ODIR, x.COST_STRUCT,
    x.COST_MARQUE, x.COST_HOLDING, x.POOL_ODIR,
    (1.0 * x.COST_COMPLET / NULLIF(x.VOL_CLASS, 0))
      / NULLIF(1.0 * (x.CA - x.COST_VARIABLE) / NULLIF(x.VOL_EFF, 0), 0)
                                                                    AS POINT_MORT
FROM (
    SELECT  a.*,
            CASE WHEN a.PROGRAMME LIKE 'BAC%' THEN 32
                 WHEN a.PROGRAMME LIKE 'MAS%' THEN 26
                 ELSE 30 END                                        AS CAPACITE
    FROM    V_ALLOCATION AS a
) AS x;
