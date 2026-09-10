/* =============================================================================
   Q_RECONCILIATION_MARQUE  —  SQL SERVER, a lancer telle quelle.

   CE QU'ELLE REND. Une ligne par campus x exercice x version, sept colonnes :

     Entity        le code campus
     Marque        deduit du code, avant le souligne
     Exercice      2024 a 2027
     Version       ACT pour le reel, V01 / V02 / V03 pour le budget
     CA CRM        effectifs x tarif + nouveaux x frais d inscription
     CA Compta     comptes 706 + 7062 + 708
     Ecart         Compta moins CRM

   LES EN-TETES SONT SANS ACCENT, ET CE N'EST PAS UN OUBLI. Le masque
   RECONCILIATION_CRM_COMPTA repere ses colonnes par MATCH sur ce texte : si le
   loader mange un accent, le MATCH echoue et tout le masque tombe en #N/A.
   Ne pas les renommer.

   LE CRM CHANGE DE SOURCE SELON L'EXERCICE, et c'est normal : le reel vient du
   socle (volumes constates), le budget 2027 vient du moteur. Les deux mesurent
   la meme chose -- des effectifs multiplies par un tarif.

   CE QUE LA REQUETE VA MONTRER. Sur le reel, l'ecart est nul au centime, sur
   les trois exercices et les cinq marques. Sur 2027, le total reste nul mais
   les marques ne collent plus : jusqu'a +9 280 EUR sur Tunon et -7 128 EUR sur
   MBway en V01, +23 616 et -37 857 en V02. La cause est dans _CALC_PNL : le
   facteur de croissance applique aux comptes de produits est calcule au niveau
   GROUPE puis applique tel quel a chaque campus. La ventilation 2027 est donc
   celle de 2026.

   Pas de CTE, pas de ORDER BY, pas de ';' -- Tagetik enveloppe la requete dans
   un SELECT COUNT(*). Pas de crochets : guillemets doubles seulement.
   ============================================================================= */
SELECT
    x.ENTITY                                                          AS "Entity",
    CASE WHEN CHARINDEX('_', x.ENTITY) > 0
         THEN LEFT(x.ENTITY, CHARINDEX('_', x.ENTITY) - 1)
         ELSE x.ENTITY END                                            AS "Marque",
    x.EXERCICE                                                        AS "Exercice",
    x.VERSION                                                         AS "Version",
    CAST(ROUND(SUM(x.CA_CRM), 2) AS DECIMAL(18, 2))                   AS "CA CRM",
    CAST(ROUND(SUM(x.CA_CPT), 2) AS DECIMAL(18, 2))                   AS "CA Compta",
    CAST(ROUND(SUM(x.CA_CPT) - SUM(x.CA_CRM), 2) AS DECIMAL(18, 2))   AS "Ecart"
FROM (
        /* ----- CRM reel : le socle, volumes constates ----- */
        SELECT s.ENTITY, s.EXERCICE, 'ACT' AS VERSION,
               SUM(s.VOL_EFF * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) AS CA_CRM,
               CAST(0 AS DECIMAL(18, 2))                                 AS CA_CPT
        FROM   AW_002_000002_000001 AS s
        GROUP BY s.ENTITY, s.EXERCICE

        UNION ALL
        /* ----- CRM budget 2027 : le moteur ----- */
        SELECT b.ENTITY, b.EXERCICE, b.VERSION,
               SUM(b.CA), CAST(0 AS DECIMAL(18, 2))
        FROM   V_MOTEUR AS b
        GROUP BY b.ENTITY, b.EXERCICE, b.VERSION

        UNION ALL
        /* ----- Comptabilite : comptes de produits, reel et budget ----- */
        SELECT n.ENTITY, n.EXERCICE, n.VERSION,
               CAST(0 AS DECIMAL(18, 2)), SUM(n.AMOUNT)
        FROM   V_PNL AS n
        WHERE  n.ACCOUNT IN ('706', '7062', '708')
        GROUP BY n.ENTITY, n.EXERCICE, n.VERSION
     ) AS x
GROUP BY x.ENTITY, x.EXERCICE, x.VERSION
