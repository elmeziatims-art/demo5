/* =============================================================================
   Q_G3_TENSION  —  SQL SERVER, a lancer telle quelle.
   TROIS COLONNES, TROIS LIGNES. Rien que ce que le graphe d'acquisition
   consomme.

     EXERCICE       la categorie de l'axe
     IND_DEPENSES   les deux courbes, base 100 sur le premier exercice
     IND_INSCRITS

   Les deux partent de 100 en 2024. Quand la courbe des depenses monte plus
   vite que celle des inscrits, chaque inscrit coute de plus en plus cher.

   Les indices sont calcules APRES la somme du perimetre : un indice ne
   s'additionne pas. Ne pas les faire re-agreger par une matrice.

   L'annee de base est posee en dur a 2024, dans le bloc b, seul endroit a
   changer pour la deplacer. La borne haute a 2026 est necessaire :
   V_ALLOCATION produit des lignes de budget 2027 sans depense d'acquisition en
   face, ce qui donnerait un indice inscrits a 370 et ecraserait le graphe.

   Le perimetre est ecrit QUATRE fois, deux pour les exercices courants et deux
   pour l'annee de base ; les quatre doivent porter la meme selection, sinon la
   base 100 est calculee sur un autre perimetre que les courbes.

   Pas de CTE, pas de ORDER BY, pas de ';'.
   Sources : V_ALLOCATION et AW_002_000002_000001.
   =============================================================================

   =============================================================================
   LES EN-TETES SONT EN CLAIR, entre crochets. Le drill-through affiche la
   sortie telle quelle a l'utilisateur : autant qu'il lise "CA par eleve N-1"
   plutot que CAE_P.

   Si le canal du loader ne conserve pas les accents -- c'est ce qui avait
   transforme "Activite" en "Activit?" sur des litteraux -- retirer simplement
   les accents dans les crochets. La requete ne change pas autrement.
   =============================================================================
   */
SELECT
    y.EXERCICE AS [Exercice],
    CAST(ROUND(100.0 * y.DEPENSES / NULLIF(b.DEPENSES, 0), 1) AS DECIMAL(9, 1)) AS [Dépenses d'acquisition base 100],
    CAST(ROUND(100.0 * y.INSCRITS / NULLIF(b.INSCRITS, 0), 1) AS DECIMAL(9, 1)) AS [Inscrits base 100]
FROM (
        SELECT  v.EXERCICE,
                SUM(v.INSCRITS)              AS INSCRITS,
                SUM(COALESCE(s.DEPENSES, 0)) AS DEPENSES
        FROM (
                SELECT  a.EXERCICE, a.ENTITY, SUM(a.VOL_NEW) AS INSCRITS
                FROM    V_ALLOCATION AS a
                WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                  AND   CAST(a.EXERCICE AS INT) BETWEEN 2024 AND 2026
                GROUP BY a.EXERCICE, a.ENTITY
             ) AS v
        LEFT JOIN (
                SELECT  z.EXERCICE, z.ENTITY, SUM(z.DEPENSE_ACQ) AS DEPENSES
                FROM    AW_002_000002_000001 AS z
                WHERE   z.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
                GROUP BY z.EXERCICE, z.ENTITY
             ) AS s
               ON  s.ENTITY = v.ENTITY AND s.EXERCICE = v.EXERCICE
        GROUP BY v.EXERCICE
     ) AS y
CROSS JOIN (
        SELECT  SUM(v.INSCRITS)              AS INSCRITS,
                SUM(COALESCE(s.DEPENSES, 0)) AS DEPENSES
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
