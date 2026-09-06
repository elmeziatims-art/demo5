/* =============================================================================
   FIX_CA_COMPTA_2024_2025  —  aligner le chiffre d'affaires de gestion sur le
   socle CRM pour les deux exercices passes.

   A LANCER DANS SSMS, PAS DANS LE LOADER TAGETIK. Ce fichier contient un
   UPDATE et des ';' : c'est un script de maintenance, pas une requete de
   restitution.

   =============================================================================
   CE QU'ON CORRIGE, ET POURQUOI L'ECART EXISTE

   2026 tombe au centime sur les quatorze campus. 2024 et 2025 non :

        exercice     compta 7*        socle CRM        ecart
        2024        20 552 827       20 567 210      -14 383   -0,070 %
        2025        21 775 820       21 758 770      +17 050   +0,078 %
        2026        23 098 985       23 098 985            0    0,000 %

   L'ecart n'est pas une erreur de correspondance de comptes. Le rapport entre
   les deux sources est CONSTANT a l'interieur d'un campus, d'un compte de
   produit a l'autre -- ISCOM Toulouse par exemple : 1,00772 sur le 706,
   1,00919 sur le 7062, 1,00770 sur le 708. Si les volumes ou les prix
   differaient, le rapport bougerait d'un compte a l'autre. Il ne bouge pas :
   c'est donc un COEFFICIENT applique campus par campus au moment ou l'estime
   des exercices passes a ete etabli, pas une divergence de fond.

   Il est aussi SIGNE de façon differente d'un campus a l'autre -- MBway Paris
   -0,45 %, Tunon Paris +0,92 % -- et les deux Pigier sont a zero. Un bruit,
   au sens propre.

   =============================================================================
   CE QUE LA CORRECTION NE CHANGE PAS

   RIEN dans le cockpit, rien dans les drills, rien dans l'EBITDA. V_ALLOCATION
   ne lit jamais les comptes de produit : le chiffre d'affaires du modele vient
   du socle CRM, effectifs x droits de scolarite. Les comptes 706, 7062 et 708
   ne servent qu'au rapprochement du second drill.

   La seule chose qui change est donc ce rapprochement : il passera a zero sur
   les trois exercices au lieu de zero sur le seul 2026.

   =============================================================================
   LA CORRESPONDANCE APPLIQUEE

       706    scolarite des etudiants en INITIAL     SUM(VOL_EFF x REV_STUD)
       7062   scolarite des ALTERNANTS               SUM(VOL_EFF x REV_STUD)
       708    frais d'inscription                    SUM(VOL_NEW x REV_FRAIS_INS)

   Verifiee sur les soixante-dix lignes de 2026, sans une seule exception.

   PORTEE : 70 lignes -- 35 par exercice, sur 2024 et 2025. Les 35 lignes de
   2026 sont deja exactes et l'UPDATE les recrit a l'identique. 2027 n'a pas de
   socle CRM, la jointure ne le touche donc pas.

   Les montants ne sont PAS ecrits en dur : ils sont recalcules depuis le CRM.
   Le script reste donc juste si le socle bouge, et peut se relancer.
   ============================================================================= */

/* ---------- 1. AVANT : l'ecart, exercice par exercice ---------------------- */
SELECT  d.EXERCICE,
        SUM(d.AMOUNT)                       AS COMPTA,
        MAX(x.TOTAL_CRM)                    AS SOCLE_CRM,
        SUM(d.AMOUNT) - MAX(x.TOTAL_CRM)    AS ECART
FROM    AW_002_000004_000001 AS d
CROSS APPLY (
        SELECT  SUM(s.VOL_EFF * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) AS TOTAL_CRM
        FROM    AW_002_000002_000001 AS s
        WHERE   s.EXERCICE = d.EXERCICE
          AND   s.SCENARIO = d.SCENARIO
     ) AS x
WHERE   d.ACCOUNT IN ('706', '7062', '708')
GROUP BY d.EXERCICE
ORDER BY d.EXERCICE;

/* ---------- 2. LA CORRECTION ---------------------------------------------- */
/* Une seule instruction. La jointure interne fait le tri toute seule : un
   couple campus x compte absent du CRM n'est pas touche, et 2027, qui n'a pas
   de socle, sort de la jointure. */
UPDATE  d
SET     d.AMOUNT = x.MONTANT
FROM    AW_002_000004_000001 AS d
JOIN (
        SELECT  s.SCENARIO,
                s.EXERCICE,
                s.ENTITY,
                CASE WHEN s.MODALITE = 'ALT' THEN '7062' ELSE '706' END AS ACCOUNT,
                SUM(s.VOL_EFF * s.REV_STUD)                             AS MONTANT
        FROM    AW_002_000002_000001 AS s
        GROUP BY s.SCENARIO, s.EXERCICE, s.ENTITY,
                 CASE WHEN s.MODALITE = 'ALT' THEN '7062' ELSE '706' END

        UNION ALL

        SELECT  s.SCENARIO,
                s.EXERCICE,
                s.ENTITY,
                '708',
                SUM(s.VOL_NEW * s.REV_FRAIS_INS)
        FROM    AW_002_000002_000001 AS s
        GROUP BY s.SCENARIO, s.EXERCICE, s.ENTITY
     ) AS x
   ON  x.SCENARIO = d.SCENARIO
  AND  x.EXERCICE = d.EXERCICE
  AND  x.ENTITY   = d.ENTITY
  AND  x.ACCOUNT  = d.ACCOUNT
WHERE   d.ACCOUNT IN ('706', '7062', '708');

/* ---------- 3. APRES : les trois exercices doivent afficher zero ----------- */
SELECT  d.EXERCICE,
        SUM(d.AMOUNT)                       AS COMPTA,
        MAX(x.TOTAL_CRM)                    AS SOCLE_CRM,
        SUM(d.AMOUNT) - MAX(x.TOTAL_CRM)    AS ECART
FROM    AW_002_000004_000001 AS d
CROSS APPLY (
        SELECT  SUM(s.VOL_EFF * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) AS TOTAL_CRM
        FROM    AW_002_000002_000001 AS s
        WHERE   s.EXERCICE = d.EXERCICE
          AND   s.SCENARIO = d.SCENARIO
     ) AS x
WHERE   d.ACCOUNT IN ('706', '7062', '708')
GROUP BY d.EXERCICE
ORDER BY d.EXERCICE;

/* ---------- 4. LE CONTROLE FIN : campus par campus, doit rendre 0 ligne ---- */
SELECT  d.EXERCICE, d.ENTITY, d.ACCOUNT, d.AMOUNT AS COMPTA, x.MONTANT AS SOCLE_CRM,
        d.AMOUNT - x.MONTANT AS ECART
FROM    AW_002_000004_000001 AS d
JOIN (
        SELECT  s.SCENARIO, s.EXERCICE, s.ENTITY,
                CASE WHEN s.MODALITE = 'ALT' THEN '7062' ELSE '706' END AS ACCOUNT,
                SUM(s.VOL_EFF * s.REV_STUD) AS MONTANT
        FROM    AW_002_000002_000001 AS s
        GROUP BY s.SCENARIO, s.EXERCICE, s.ENTITY,
                 CASE WHEN s.MODALITE = 'ALT' THEN '7062' ELSE '706' END
        UNION ALL
        SELECT  s.SCENARIO, s.EXERCICE, s.ENTITY, '708',
                SUM(s.VOL_NEW * s.REV_FRAIS_INS)
        FROM    AW_002_000002_000001 AS s
        GROUP BY s.SCENARIO, s.EXERCICE, s.ENTITY
     ) AS x
   ON  x.SCENARIO = d.SCENARIO AND x.EXERCICE = d.EXERCICE
  AND  x.ENTITY   = d.ENTITY   AND x.ACCOUNT  = d.ACCOUNT
WHERE   d.ACCOUNT IN ('706', '7062', '708')
  AND   ABS(d.AMOUNT - x.MONTANT) > 0.005
ORDER BY d.EXERCICE, d.ENTITY, d.ACCOUNT;
