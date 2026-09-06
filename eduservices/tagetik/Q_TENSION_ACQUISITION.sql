/* =============================================================================
   Q_TENSION_ACQUISITION  —  SQL SERVER, a lancer telle quelle.
   Le tableau du graphe "Tension acquisition, base 100" : une ligne par
   exercice, les deux courbes en colonnes.

     EXERCICE  DEPENSES  INSCRITS  IND_DEPENSES  IND_INSCRITS  CAC  ECART_PT
       2024     358 819     1 092         100,0         100,0  329       0,0
       2025     394 702     1 159         110,0         106,1  341       3,9
       2026     434 174     1 229         121,0         112,5  353       8,5

   Les deux courbes partent de 100 en 2024. Quand celle des depenses monte plus
   vite que celle des inscrits, chaque inscrit coute de plus en plus cher :
   le recrutement s'achete au lieu de se gagner. ECART_PT mesure cet ecart en
   points d'indice, c'est la tension elle-meme.

   CAC est le cout d'acquisition par inscrit, en euros. Il dit la meme chose
   que l'ecart des deux courbes, mais dans l'unite du directeur de campus.

   L'annee de base est posee en dur a 2024, dans le bloc b. Pour la deplacer,
   changer la constante a cet endroit uniquement.

   Le perimetre passe par le parametre Tagetik, et il est ecrit QUATRE fois :
   deux fois pour les exercices courants, deux fois pour l'annee de base. Les
   quatre doivent porter la meme selection.

       AND a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})

   Les indices sont calcules APRES la somme du perimetre : un indice ne
   s'additionne pas, il ne peut donc pas etre re-agrege par une matrice. Pour
   une matrice, c'est Q_ACQUISITION_BASE100 qui expose les valeurs de
   reference sur chaque ligne et laisse le report diviser.

   Sources : V_ALLOCATION (inscrits) et AW_002_000002_000001 (DEPENSE_ACQ,
   identique au compte 6231 de la compta, verifie au centime sur les trois
   exercices).

   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    y.EXERCICE,

    CAST(ROUND(y.DEPENSES, 0) AS DECIMAL(18, 0))            AS DEPENSES,
    CAST(ROUND(y.INSCRITS, 0) AS DECIMAL(18, 0))            AS INSCRITS,

    CAST(ROUND(100.0 * y.DEPENSES / NULLIF(b.DEPENSES, 0), 1) AS DECIMAL(9, 1)) AS IND_DEPENSES,
    CAST(ROUND(100.0 * y.INSCRITS / NULLIF(b.INSCRITS, 0), 1) AS DECIMAL(9, 1)) AS IND_INSCRITS,

    CAST(ROUND(1.0 * y.DEPENSES / NULLIF(y.INSCRITS, 0), 0) AS DECIMAL(18, 0))  AS CAC,

    CAST(ROUND(100.0 * y.DEPENSES / NULLIF(b.DEPENSES, 0)
             - 100.0 * y.INSCRITS / NULLIF(b.INSCRITS, 0), 1) AS DECIMAL(9, 1)) AS ECART_PT
FROM (
        SELECT  v.EXERCICE,
                SUM(v.INSCRITS)                    AS INSCRITS,
                SUM(COALESCE(s.DEPENSES, 0))       AS DEPENSES
        FROM (
                SELECT  a.EXERCICE, a.ENTITY, SUM(a.VOL_NEW) AS INSCRITS
                FROM    V_ALLOCATION AS a
                WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                GROUP BY a.EXERCICE, a.ENTITY
             ) AS v
        LEFT JOIN (
                SELECT  z.EXERCICE, z.ENTITY, SUM(z.DEPENSE_ACQ) AS DEPENSES
                FROM    AW_002_000002_000001 AS z
                WHERE   z.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                GROUP BY z.EXERCICE, z.ENTITY
             ) AS s
               ON  s.ENTITY   = v.ENTITY
              AND  s.EXERCICE = v.EXERCICE
        GROUP BY v.EXERCICE
     ) AS y
CROSS JOIN (
        SELECT  SUM(v.INSCRITS)                    AS INSCRITS,
                SUM(COALESCE(s.DEPENSES, 0))       AS DEPENSES
        FROM (
                SELECT  a.ENTITY, SUM(a.VOL_NEW) AS INSCRITS
                FROM    V_ALLOCATION AS a
                WHERE   CAST(a.EXERCICE AS INT) = 2024
                  AND   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                GROUP BY a.ENTITY
             ) AS v
        LEFT JOIN (
                SELECT  z.ENTITY, SUM(z.DEPENSE_ACQ) AS DEPENSES
                FROM    AW_002_000002_000001 AS z
                WHERE   CAST(z.EXERCICE AS INT) = 2024
                  AND   z.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                GROUP BY z.ENTITY
             ) AS s
               ON  s.ENTITY = v.ENTITY
     ) AS b
