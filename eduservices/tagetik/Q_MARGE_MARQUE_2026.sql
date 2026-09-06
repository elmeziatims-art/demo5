/* =============================================================================
   Q_MARGE_MARQUE_2026  —  SQL SERVER, a lancer telle quelle.
   Le tableau du graphe "Marge EBITDA par marque", avec un AXE QUI S'ADAPTE
   AU NOEUD CHOISI.

     noeud selectionne = ALL   ->  une ligne par MARQUE   (5 barres)
     noeud selectionne = autre ->  une ligne par CAMPUS   (les feuilles du noeud)

   On choisit ALL, le graphe compare les cinq enseignes. On descend sur MBWAY,
   le meme graphe compare les quatre campus MBway. Un seul objet de report,
   deux lectures, aucune bascule a faire a la main.

   La colonne NIVEAU dit lequel des deux axes a ete servi : elle sert a piloter
   le titre du graphe ("par marque" ou "par campus") sans deuxieme requete.

   =============================================================================
   LES LIBELLES

   L'axe du graphe affiche la DESCRIPTION, pas le code : "MBway Paris" et non
   MBWAY_PAR. Elle vient de la table azienda, comme dans le drill, par la meme
   jointure  az.COD_AZIENDA = le code retenu. Comme le regroupement est fait
   AVANT, une seule jointure sert les deux niveaux : elle attrape le campus
   quand on est descendu, le noeud de marque quand on est sur ALL.

   Si les noeuds de marque ne portent pas ces codes dans azienda, un petit
   mapping VALUES prend le relais, et en dernier recours c'est le code brut qui
   s'affiche. L'axe n'est donc jamais vide, quoi qu'il arrive.

   CODE reste disponible a cote de LIBELLE, pour trier ou pour retrouver une
   ligne sans ambiguite.

   =============================================================================
   LES DEUX PARAMETRES

   1. LE PERIMETRE, comme d'habitude, sur les feuilles :

          AND a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})

   2. LE CODE DU NOEUD, qui sert uniquement de bascule d'axe. Il n'est ecrit
      qu'UNE fois, dans le CROSS JOIN, et il en sort un simple 0 ou 1 :

          CASE WHEN 'ALL' IN (${$Entity(HIERARCHY("EDU")).code}) THEN 1 ELSE 0 END

      La constante 'ALL' est le seul endroit a changer si la racine de la
      hierarchie EDU porte un autre code chez vous (EDU, GRP...). Le IN
      fonctionne aussi bien si le parametre renvoie une valeur unique qu'une
      liste, donc rien a adapter selon le mode de selection.

   =============================================================================
   LECTURE DES COLONNES

   MARGE_* sort en FRACTION (0,1825) : formater en pourcentage dans Excel.
   ECART_PT est deja en POINTS de marge, c'est un ecart de taux et pas une
   variation relative -- ne pas le formater en pourcentage.

   La division est faite APRES la somme, a l'interieur de la requete : c'est ce
   qui permet de sortir MARGE directement. Une marge ne s'additionne pas, donc
   ne pas faire re-agreger ces colonnes par une matrice -- pour une matrice,
   c'est Q_MARGE_PAR_MARQUE qui expose CA et EBITDA separement.

   Pas de CTE, pas de ORDER BY, pas de ';'.  Source : V_ALLOCATION.
   ============================================================================= */
SELECT
    g.NIVEAU,
    g.CODE,
    COALESCE(az.DESC_AZIENDA0, m.LIB, g.CODE)               AS LIBELLE,

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
            CASE WHEN f.RACINE = 1 THEN 'MARQUE' ELSE 'CAMPUS' END             AS NIVEAU,
            CASE WHEN f.RACINE = 1 THEN a.MARQUE ELSE a.ENTITY END             AS CODE,
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
                SELECT CASE WHEN 'ALL' IN (${$Entity(HIERARCHY("EDU")).code})
                            THEN 1 ELSE 0 END                                  AS RACINE
             ) AS f
        WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
        GROUP BY f.RACINE,
                 CASE WHEN f.RACINE = 1 THEN a.MARQUE ELSE a.ENTITY END
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
