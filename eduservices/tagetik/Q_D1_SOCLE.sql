/* =============================================================================
   Q_D1_SOCLE  —  DRILL-THROUGH sur une cellule d'EBITDA.
   La requete envoie TOUS LES ELEMENTS DU CALCUL. Le classeur n'a plus qu'a
   multiplier et additionner : pas une seule division a faire cote Excel.

   Une ligne par CAMPUS du perimetre cliquee.

   =============================================================================
   LES VINGT-TROIS COLONNES, ET LEUR NATURE

   IDENTITE          ENTITY  LIBELLE  MARQUE  EXERCICE_P  EXERCICE_N

   VOLUMES           EFF_P  EFF_N  D_EFF                        additifs
   MONTANTS          CA_P CA_N  CVAR_P CVAR_N                   additifs
                     CDIR_P CDIR_N  SIEGE_P SIEGE_N             additifs
   RESULTATS         EBITDA_P  EBITDA_N  D_EBITDA               additifs

   UNITAIRES         CAE_P CAE_N      CA par eleve         PAR LIGNE SEULEMENT
                     CVE_P CVE_N      cout variable/eleve  PAR LIGNE SEULEMENT
                     MARGE_UNIT_P     CAE_P - CVE_P        PAR LIGNE SEULEMENT

   ATTENTION AUX CINQ DERNIERES. Ce sont des ratios : elles valent pour la
   ligne ou elles se trouvent et NE S'ADDITIONNENT PAS. Ne jamais les sommer,
   ne jamais les moyenner. Le classeur les utilise ligne a ligne, ce qui est
   leur seul emploi correct.

   =============================================================================
   CE QUE LE CLASSEUR EN FAIT, une multiplication par effet

     effet effectifs   =  D_EFF * MARGE_UNIT_P
     effet prix et mix = (CAE_N - CAE_P) * EFF_N
     effet cout var.   = -(CVE_N - CVE_P) * EFF_N
     effet couts dir.  = -(CDIR_N - CDIR_P)
     effet siege       = -(SIEGE_N - SIEGE_P)

   Sommes ligne a ligne puis totalises, les cinq effets redonnent D_EBITDA
   exactement. MARGE_UNIT_P est la marge sur cout variable par eleve de l'annee
   precedente : c'est a ce prix-la qu'un eleve de plus se valorise, pas au CA.

   =============================================================================
   POURQUOI UNE LIGNE PAR CAMPUS

   Sur un noeud, agreger AVANT de calculer melangerait des campus a 7 123 EUR
   de CA par eleve et d'autres au-dela de 8 000 : un simple deplacement
   d'eleves entre campus, sans aucune hausse tarifaire, se lirait comme un
   effet prix. En gardant le grain campus, chaque eleve est valorise a la marge
   de SON campus. Sur une cellule de campus la question ne se pose pas, il n'y
   a qu'une ligne.

   Contexte herite de la cellule cliquee. L'annee precedente n'est pas filtree
   par parametre : la jointure la trouve sur EXERCICE - 1.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    n.ENTITY,
    COALESCE(az.DESC_AZIENDA0, n.ENTITY)                    AS LIBELLE,
    n.MARQUE,
    p.EXERCICE                                              AS EXERCICE_P,
    n.EXERCICE                                              AS EXERCICE_N,

    p.EFFECTIFS                                             AS EFF_P,
    n.EFFECTIFS                                             AS EFF_N,
    n.EFFECTIFS - p.EFFECTIFS                               AS D_EFF,

    p.CA                                                    AS CA_P,
    n.CA                                                    AS CA_N,
    p.COST_VAR                                              AS CVAR_P,
    n.COST_VAR                                              AS CVAR_N,
    p.COST_DIR                                              AS CDIR_P,
    n.COST_DIR                                              AS CDIR_N,
    p.COST_SIEGE                                            AS SIEGE_P,
    n.COST_SIEGE                                            AS SIEGE_N,

    p.CA - p.COST_VAR - p.COST_DIR - p.COST_SIEGE           AS EBITDA_P,
    n.CA - n.COST_VAR - n.COST_DIR - n.COST_SIEGE           AS EBITDA_N,
    (n.CA - n.COST_VAR - n.COST_DIR - n.COST_SIEGE)
      - (p.CA - p.COST_VAR - p.COST_DIR - p.COST_SIEGE)     AS D_EBITDA,

    /* Les cinq unitaires : valables LIGNE A LIGNE, jamais sommables.
       SIX decimales et non deux. Elles sont multipliees par des effectifs, si
       bien qu'un arrondi au centime se propage : a deux decimales, le controle
       du pont ne tombe plus a zero mais a 3,91 EUR. A six, il tombe a un
       millieme d'euro. On affiche deux decimales dans le classeur, on en
       transporte six. */
    CAST(1.0 * p.CA / NULLIF(p.EFFECTIFS, 0) AS DECIMAL(18, 6))             AS CAE_P,
    CAST(1.0 * n.CA / NULLIF(n.EFFECTIFS, 0) AS DECIMAL(18, 6))             AS CAE_N,
    CAST(1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0) AS DECIMAL(18, 6))       AS CVE_P,
    CAST(1.0 * n.COST_VAR / NULLIF(n.EFFECTIFS, 0) AS DECIMAL(18, 6))       AS CVE_N,
    CAST(1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)
       - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0) AS DECIMAL(18, 6))       AS MARGE_UNIT_P
FROM (
        SELECT  a.ENTITY, a.MARQUE, a.EXERCICE,
                SUM(a.CA)                          AS CA,
                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                SUM(a.COST_VARIABLE)               AS COST_VAR,
                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY   IN (${$Entity(HIERARCHY("EDU")).lowest})
          AND   a.EXERCICE IN (${$ANL_EXERCICE.code})
        GROUP BY a.ENTITY, a.MARQUE, a.EXERCICE
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
LEFT JOIN azienda AS az
       ON az.COD_AZIENDA = n.ENTITY
