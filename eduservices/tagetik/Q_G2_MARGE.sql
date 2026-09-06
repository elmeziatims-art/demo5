/* =============================================================================
   Q_G2_MARGE  —  SQL SERVER, a lancer telle quelle.
   QUATRE COLONNES. Rien que ce que le graphe de marge consomme.

     LIBELLE       la categorie de l'axe
     MARGE_2024    les trois series, dans l'ordre chronologique
     MARGE_2025
     MARGE_2026

   Les marges sortent en FRACTION (0,1825) : formater l'axe en pourcentage.

   L'AXE SUIT LE NOEUD CHOISI. Le CROSS JOIN compte les marques du perimetre :
   plusieurs, la requete rend une ligne par marque ; une seule, elle rend une
   ligne par campus. Cinq barres a la racine, quatre sur MBway, deux sur Tunon,
   sans rien coder en dur.

   Le libelle vient de la table azienda, comme dans le drill. Si les noeuds de
   marque n'y portent pas ces codes, le mapping VALUES prend le relais, et en
   dernier recours c'est le code brut qui s'affiche : l'axe n'est jamais vide.

   La division est faite APRES la somme du perimetre : une marge ne
   s'additionne pas. Ne pas faire re-agreger cette colonne par une matrice.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
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
    COALESCE(az.DESC_AZIENDA0, m.LIB, g.CODE)               AS [Marque ou campus],
    CAST(ROUND(1.0 * g.EBITDA_2024 / NULLIF(g.CA_2024, 0), 4) AS DECIMAL(9, 4)) AS [Marge EBITDA 2024],
    CAST(ROUND(1.0 * g.EBITDA_2025 / NULLIF(g.CA_2025, 0), 4) AS DECIMAL(9, 4)) AS [Marge EBITDA 2025],
    CAST(ROUND(1.0 * g.EBITDA_2026 / NULLIF(g.CA_2026, 0), 4) AS DECIMAL(9, 4)) AS [Marge EBITDA 2026]
FROM (
        SELECT
            CASE WHEN f.PLUSIEURS = 1 THEN a.MARQUE ELSE a.ENTITY END          AS CODE,
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
        CROSS JOIN (
                SELECT CASE WHEN COUNT(DISTINCT z.MARQUE) > 1 THEN 1 ELSE 0 END AS PLUSIEURS
                FROM   V_ALLOCATION AS z
                WHERE  z.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
             ) AS f
        WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
        GROUP BY f.PLUSIEURS,
                 CASE WHEN f.PLUSIEURS = 1 THEN a.MARQUE ELSE a.ENTITY END
     ) AS g
LEFT JOIN azienda AS az
       ON az.COD_AZIENDA = g.CODE
LEFT JOIN (
        VALUES ('MBWAY',  'MBway'),
               ('ISCOM',  'ISCOM'),
               ('IPAC',   'Ipac Bachelor Factory'),
               ('PIGIER', 'Pigier'),
               ('TUNON',  'Tunon')
     ) AS m(COD, LIB)
       ON m.COD = g.CODE
