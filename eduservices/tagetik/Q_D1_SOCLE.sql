/* =============================================================================
   Q_D1_SOCLE  —  DRILL-THROUGH sur une cellule d'EBITDA.
   Quinze colonnes, une ligne par campus. Rien de plus.

   La requete envoie TOUS LES ELEMENTS DU CALCUL et rien d'autre : le classeur
   n'a plus une seule division a faire, il ne fait que multiplier et sommer.

     Campus
     Effectifs 2025                        Effectifs 2026
     Eleves gagnes
     CA par eleve 2025                     CA par eleve 2026
     Cout var. par eleve 2025              Cout var. par eleve 2026
     Marge sur cout var. par eleve 2025
     Couts directs 2025                    Couts directs 2026
     Siege 2025                            Siege 2026
     EBITDA 2025                           EBITDA 2026

   ALIAS ENTRE GUILLEMETS DOUBLES, pas entre crochets : c'est la forme que
   Tagetik accepte, celle deja utilisee dans Q_DRILL_COCKPIT avec des accents.

   =============================================================================
   CE QUE LE CLASSEUR EN FAIT, une multiplication par effet

     effet effectifs   =  Eleves gagnes x Marge sur cout var. par eleve 2025
     effet prix et mix = (CA/eleve 2026 - CA/eleve 2025) x Effectifs 2026
     effet cout var.   = -(Cout var./eleve 2026 - 2025) x Effectifs 2026
     effet couts dir.  = -(Couts directs 2026 - 2025)
     effet siege       = -(Siege 2026 - 2025)

   Sommes ligne a ligne puis totalises, ils redonnent exactement
   EBITDA 2026 - EBITDA 2025. La marge sur cout variable par eleve est le prix
   auquel un eleve de plus se valorise : ce qu'il rapporte moins ce qu'il coute
   directement. Les charges fixes qu'il faut ensuite absorber apparaissent en
   clair dans les deux dernieres lignes.

   SIX DECIMALES sur les quatre unitaires et sur la marge. Elles sont
   multipliees par des effectifs, donc l'arrondi se propage : a deux decimales
   le pont ne boucle plus a zero mais a 3,91 EUR sur le groupe. On transporte
   six decimales, le classeur en affiche deux.

   =============================================================================
   POURQUOI UNE LIGNE PAR CAMPUS

   Sur un noeud, agreger AVANT de calculer melangerait des campus a 7 123 EUR
   de CA par eleve et d'autres au-dela de 8 000 : un simple deplacement
   d'eleves entre campus, sans aucune hausse tarifaire, se lirait comme un
   effet prix. En gardant le grain campus, chaque eleve est valorise a la marge
   de SON campus. Sur une cellule de campus la question ne se pose pas.

   Le perimetre est herite de la cellule cliquee. Les exercices sont poses en
   dur, comme dans le cockpit ; pour les rendre parametrables, remplacer le
   2026 du bloc n par ${$ANL_EXERCICE.code} et retirer le filtre du bloc p, la
   jointure trouvant l'annee precedente sur EXERCICE - 1.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    COALESCE(az.DESC_AZIENDA0, n.ENTITY)                    AS "Campus",

    p.EFFECTIFS                                             AS "Effectifs 2025",
    n.EFFECTIFS                                             AS "Effectifs 2026",
    n.EFFECTIFS - p.EFFECTIFS                               AS "Élèves gagnés",

    CAST(1.0 * p.CA / NULLIF(p.EFFECTIFS, 0) AS DECIMAL(18, 6))
                                                            AS "CA par élève 2025",
    CAST(1.0 * n.CA / NULLIF(n.EFFECTIFS, 0) AS DECIMAL(18, 6))
                                                            AS "CA par élève 2026",
    CAST(1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0) AS DECIMAL(18, 6))
                                                            AS "Coût var. par élève 2025",
    CAST(1.0 * n.COST_VAR / NULLIF(n.EFFECTIFS, 0) AS DECIMAL(18, 6))
                                                            AS "Coût var. par élève 2026",
    CAST(1.0 * p.CA / NULLIF(p.EFFECTIFS, 0)
       - 1.0 * p.COST_VAR / NULLIF(p.EFFECTIFS, 0) AS DECIMAL(18, 6))
                                                            AS "Marge sur coût var. par élève 2025",

    p.COST_DIR                                              AS "Coûts directs 2025",
    n.COST_DIR                                              AS "Coûts directs 2026",
    p.COST_SIEGE                                            AS "Siège 2025",
    n.COST_SIEGE                                            AS "Siège 2026",

    p.CA - p.COST_VAR - p.COST_DIR - p.COST_SIEGE           AS "EBITDA 2025",
    n.CA - n.COST_VAR - n.COST_DIR - n.COST_SIEGE           AS "EBITDA 2026"
FROM (
        SELECT  a.ENTITY,
                SUM(a.CA)                          AS CA,
                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                SUM(a.COST_VARIABLE)               AS COST_VAR,
                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
        FROM    V_ALLOCATION AS a
        WHERE   CAST(a.EXERCICE AS INT) = 2026
          AND   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
        GROUP BY a.ENTITY
     ) AS n
INNER JOIN (
        SELECT  a.ENTITY,
                SUM(a.CA)                          AS CA,
                SUM(a.VOL_EFF)                     AS EFFECTIFS,
                SUM(a.COST_VARIABLE)               AS COST_VAR,
                SUM(a.COST_SIEGE)                  AS COST_SIEGE,
                SUM(a.COST_COMPLET - a.COST_VARIABLE - a.COST_SIEGE) AS COST_DIR
        FROM    V_ALLOCATION AS a
        WHERE   CAST(a.EXERCICE AS INT) = 2025
          AND   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
        GROUP BY a.ENTITY
     ) AS p
       ON  p.ENTITY = n.ENTITY
LEFT JOIN azienda AS az
       ON az.COD_AZIENDA = n.ENTITY
