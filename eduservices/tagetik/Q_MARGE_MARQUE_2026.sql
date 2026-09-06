/* =============================================================================
   Q_MARGE_MARQUE_2026  —  SQL SERVER, a lancer telle quelle.
   Le tableau du graphe "Marge EBITDA par marque", avec un AXE QUI S'ADAPTE
   AU NOEUD CHOISI.

     le perimetre couvre PLUSIEURS marques  ->  une ligne par MARQUE
     le perimetre couvre UNE SEULE marque    ->  une ligne par CAMPUS

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
   L'ORDRE DES COLONNES EST CELUI DU GRAPHE

   Les quatre premieres colonnes sont LIBELLE puis les trois marges, dans
   l'ordre chronologique. Un graphe se branche donc directement sur la zone de
   restitution, sans colonne de relais dans le classeur : la categorie est la
   colonne 1, les trois series les colonnes 2, 3 et 4, contigues.

   Tout le detail -- niveau, code, chiffre d'affaires et EBITDA de chaque
   exercice -- vient APRES, disponible pour l'audit mais hors du chemin du
   graphe.

   =============================================================================
   COMMENT L'AXE SE CHOISIT

   Une premiere version testait le code du noeud, avec 'ALL' IN (...code).
   Elle ne marche pas : la substitution ne renvoie pas seulement le noeud
   selectionne, donc le test etait toujours vrai et l'axe restait bloque sur la
   marque. On ne devine plus la semantique du parametre : le niveau se DEDUIT
   DE LA DONNEE.

       le perimetre contient plus d'une marque  ->  axe MARQUE
       il n'en contient qu'une                  ->  axe CAMPUS

   C'est exactement le comportement voulu, et il ne depend d'aucun code en dur :

       ALL              5 marques  ->  cinq barres, une par enseigne
       MBWAY            1 marque   ->  quatre barres, les campus MBway
       un seul campus   1 marque   ->  une barre
       deux enseignes   2 marques  ->  deux barres

   Un seul parametre en tout, le perimetre, ecrit deux fois : une fois pour
   compter les marques, une fois pour agreger. Les deux doivent porter la meme
   selection.

          AND a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})

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
    /* 1 a 4 : le graphe. Categorie, puis les trois series, contigues. */
    COALESCE(az.DESC_AZIENDA0, m.LIB, g.CODE)               AS LIBELLE,
    CAST(ROUND(1.0 * g.EBITDA_2024 / NULLIF(g.CA_2024, 0), 4) AS DECIMAL(9, 4)) AS MARGE_2024,
    CAST(ROUND(1.0 * g.EBITDA_2025 / NULLIF(g.CA_2025, 0), 4) AS DECIMAL(9, 4)) AS MARGE_2025,
    CAST(ROUND(1.0 * g.EBITDA_2026 / NULLIF(g.CA_2026, 0), 4) AS DECIMAL(9, 4)) AS MARGE_2026,

    /* 5 et au-dela : le detail, pour l'audit et pour le tableau */
    CAST(ROUND(100.0 * (1.0 * g.EBITDA_2026 / NULLIF(g.CA_2026, 0)
                      - 1.0 * g.EBITDA_2024 / NULLIF(g.CA_2024, 0)), 2)
         AS DECIMAL(9, 2))                                  AS ECART_PT,
    g.NIVEAU,
    g.CODE,
    CAST(ROUND(g.CA_2024,     0) AS DECIMAL(18, 0))         AS CA_2024,
    CAST(ROUND(g.EBITDA_2024, 0) AS DECIMAL(18, 0))         AS EBITDA_2024,
    CAST(ROUND(g.CA_2025,     0) AS DECIMAL(18, 0))         AS CA_2025,
    CAST(ROUND(g.EBITDA_2025, 0) AS DECIMAL(18, 0))         AS EBITDA_2025,
    CAST(ROUND(g.CA_2026,     0) AS DECIMAL(18, 0))         AS CA_2026,
    CAST(ROUND(g.EBITDA_2026, 0) AS DECIMAL(18, 0))         AS EBITDA_2026
FROM (
        SELECT
            CASE WHEN f.PLUSIEURS = 1 THEN 'MARQUE' ELSE 'CAMPUS' END             AS NIVEAU,
            CASE WHEN f.PLUSIEURS = 1 THEN a.MARQUE ELSE a.ENTITY END             AS CODE,
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
