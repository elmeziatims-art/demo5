/* =============================================================================
   Q_MARGE_MARQUE_2026  —  SQL SERVER, a lancer telle quelle.
   Le tableau du graphe "Marge EBITDA par marque" : une ligne par marque
   presente dans le perimetre, les trois exercices en colonnes.

     MARQUE   CA_2024  EBITDA_2024  MARGE_2024  ...  MARGE_2026  ECART_PT
     MBWAY    ...      ...          0,1653      ...  0,1817      +1,64
     ISCOM    ...      ...          0,1583      ...  0,1720      +1,37
     ...

   MARGE_* sort en FRACTION (0,1817) : formater la colonne en pourcentage dans
   Excel. ECART_PT est deja en POINTS de marge, c'est un ecart de taux, pas une
   variation relative -- ne pas le formater en pourcentage.

   Le perimetre passe par le parametre Tagetik :

       AND a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})

   Si l'on filtre sur une seule marque, la requete renvoie une seule ligne.
   Si l'on filtre sur trois campus de trois marques, elle en renvoie trois.
   Elle suit la selection sans rien coder en dur.

   La division est faite APRES la somme, a l'interieur de la requete : c'est ce
   qui permet de sortir MARGE directement. Une marge ne s'additionne pas, donc
   ne pas faire re-agreger ces colonnes par une matrice -- pour une matrice,
   c'est Q_MARGE_PAR_MARQUE qui expose CA et EBITDA separement.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    g.MARQUE,

    CAST(ROUND(g.CA_2024,     0) AS DECIMAL(18, 0))         AS CA_2024,
    CAST(ROUND(g.EBITDA_2024, 0) AS DECIMAL(18, 0))         AS EBITDA_2024,
    CAST(ROUND(1.0 * g.EBITDA_2024 / NULLIF(g.CA_2024, 0), 4) AS DECIMAL(9, 4)) AS MARGE_2024,

    CAST(ROUND(g.CA_2025,     0) AS DECIMAL(18, 0))         AS CA_2025,
    CAST(ROUND(g.EBITDA_2025, 0) AS DECIMAL(18, 0))         AS EBITDA_2025,
    CAST(ROUND(1.0 * g.EBITDA_2025 / NULLIF(g.CA_2025, 0), 4) AS DECIMAL(9, 4)) AS MARGE_2025,

    CAST(ROUND(g.CA_2026,     0) AS DECIMAL(18, 0))         AS CA_2026,
    CAST(ROUND(g.EBITDA_2026, 0) AS DECIMAL(18, 0))         AS EBITDA_2026,
    CAST(ROUND(1.0 * g.EBITDA_2026 / NULLIF(g.CA_2026, 0), 4) AS DECIMAL(9, 4)) AS MARGE_2026,

    CAST(ROUND(100.0 * (1.0 * g.EBITDA_2026 / NULLIF(g.CA_2026, 0)
                      - 1.0 * g.EBITDA_2024 / NULLIF(g.CA_2024, 0)), 2)
         AS DECIMAL(9, 2))                                  AS ECART_PT
FROM (
        SELECT
            a.MARQUE,
            SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2024 THEN a.CA ELSE 0 END) AS CA_2024,
            SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2025 THEN a.CA ELSE 0 END) AS CA_2025,
            SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2026 THEN a.CA ELSE 0 END) AS CA_2026,
            SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2024
                     THEN a.CA - a.COST_COMPLET ELSE 0 END)                    AS EBITDA_2024,
            SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2025
                     THEN a.CA - a.COST_COMPLET ELSE 0 END)                    AS EBITDA_2025,
            SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2026
                     THEN a.CA - a.COST_COMPLET ELSE 0 END)                    AS EBITDA_2026
        FROM    V_ALLOCATION AS a
        WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
        GROUP BY a.MARQUE
     ) AS g
