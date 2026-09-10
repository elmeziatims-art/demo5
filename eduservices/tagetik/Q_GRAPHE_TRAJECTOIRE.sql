/* =============================================================================
   Q_GRAPHE_TRAJECTOIRE  —  SQL SERVER, a lancer telle quelle.

   CE QU'ELLE REND. Trois lignes, une par exercice REEL, quatre colonnes :

     Exercice        2024, 2025, 2026
     CA              somme des comptes 70x
     EBITDA          CA moins les 6xx, hors 6811 (dotations)
     Marge EBITDA    EBITDA / CA, en FRACTION (0,1665) : formater en %

   Elle NE REND PAS 2027. C'est voulu : la ligne 2027 du graphe doit suivre la
   liste deroulante du masque, donc elle est en formules qui pointent Cadrage.
   Une requete qui figerait 2027 casserait la demo au premier changement de
   scenario.

   OU LA COLLER. Dans CAD_PIL, onglet Cadrage, en P6 -- les quatre colonnes
   tombent en P, Q, R, S, dans cet ordre. La cinquieme colonne du graphe,
   l'objectif (T), est une cellule elle aussi, pas une donnee de base.

   LA LIGNE 2027, a saisir une fois :
     P9 = 2027                 Q9 = =Cadrage!$D$12     R9 = =Cadrage!$D$13
     S9 = =Cadrage!$D$14       T6 a T9 = =Cadrage!$B$8

   LA DEFINITION D'EBITDA EST CELLE QUE CAD_PIL UTILISE DEJA. Controle : sur
   2026 la requete doit rendre 23 098 985 EUR de CA et 3 845 790 EUR d'EBITDA,
   soit exactement C12 et C13 du masque. Si l'ecart n'est pas nul, c'est le
   perimetre d'entites qui differe -- voir la note ci-dessous.

   PAS DE FILTRE D'ENTITE, ET C'EST DELIBERE. L'EBITDA du masque est APRES
   siege : il inclut l'entite GRP. Ajouter un filtre sur la hierarchie EDU
   exclurait GRP et ferait remonter l'EBITDA de 3,7 MEUR.

   PERIODE. La table de compta est annuelle (une ligne par entite x compte x
   exercice, PERIOD = 12). Si votre instance stocke du mensuel, decommenter le
   filtre sur PERIOD, sinon les montants sont multiplies par douze.

   ORDRE DES LIGNES. Tagetik enveloppe la requete dans un SELECT COUNT(*) :
   pas de CTE, pas de ORDER BY, pas de ';'. Le bloc VALUES fixe la sequence des
   exercices ; si l'affichage ne sort pas dans l'ordre, trier sur Exercice au
   niveau du rapport.

   LES EN-TETES SONT ENTRE GUILLEMETS DOUBLES -- Tagetik n'accepte pas les
   crochets, et pas d'apostrophe dans un alias (d'ou "CA" et non
   "Chiffre d'affaires"). Source : AW_002_000004_000001, la compta reelle,
   celle que V_PNL consomme pour la partie ACT.
   ============================================================================= */
SELECT
    e.EXERCICE                                                            AS "Exercice",
    CAST(ROUND(a.CA, 0) AS DECIMAL(18, 0))                                AS "CA",
    CAST(ROUND(a.CA - a.CHARGES, 0) AS DECIMAL(18, 0))                    AS "EBITDA",
    CAST(ROUND(1.0 * (a.CA - a.CHARGES) / NULLIF(a.CA, 0), 4)
         AS DECIMAL(9, 4))                                                AS "Marge EBITDA"
FROM (VALUES (2024), (2025), (2026)) AS e (EXERCICE)
OUTER APPLY (
        SELECT
            SUM(CASE WHEN LEFT(CAST(c.ACCOUNT AS VARCHAR(20)), 2) = '70'
                     THEN c.AMOUNT ELSE 0 END)                            AS CA,
            SUM(CASE WHEN LEFT(CAST(c.ACCOUNT AS VARCHAR(20)), 1) = '6'
                      AND LEFT(CAST(c.ACCOUNT AS VARCHAR(20)), 4) <> '6811'
                     THEN c.AMOUNT ELSE 0 END)                            AS CHARGES
        FROM   AW_002_000004_000001 AS c
        WHERE  c.SCENARIO = '2027BUD_V1'
          AND  CAST(c.EXERCICE AS INT) = e.EXERCICE
       /* AND  CAST(c.PERIOD AS VARCHAR(10)) = '12' */
     ) AS a
