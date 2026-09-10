/* =============================================================================
   Q_D2_CA_COMPTA  —  le controle de rapprochement du second drill.
   Une ligne, deux colonnes : le chiffre d'affaires tel que la table dite
   "compta" le porte, comptes 706, 7062 et 708.

   =============================================================================
   LA CORRESPONDANCE ENTRE LES DEUX SOURCES

       706    scolarite des etudiants en INITIAL     VOL_EFF x REV_STUD
       7062   scolarite des ALTERNANTS               VOL_EFF x REV_STUD
       708    frais d'inscription                    VOL_NEW x REV_FRAIS_INS

   Verifiee sur les soixante-dix lignes de 2026, sans une seule exception.

   =============================================================================
   LES DEUX SOURCES SONT ALIGNEES  (UPDATE passe le 06/09)

        exercice     compta 7*        socle CRM        ecart
        2024        20 567 210       20 567 210            0
        2025        21 758 770       21 758 770            0
        2026        23 098 985       23 098 985            0

   Il y avait un ecart sur les deux exercices passes : -14 383 en 2024,
   +17 050 en 2025, soit sept a huit centiemes de pour cent. Ce n'etait pas une
   erreur de correspondance de comptes -- le rapport entre les deux sources
   etait CONSTANT a l'interieur d'un campus, d'un compte de produit a l'autre
   (ISCOM Toulouse : 1,00772 sur le 706, 1,00919 sur le 7062, 1,00770 sur le
   708), alors que des volumes ou des prix differents l'auraient fait bouger.
   C'etait un coefficient pose campus par campus quand l'estime des exercices
   passes a ete etabli, signe dans les deux sens et nul sur les deux Pigier.

   FIX_CA_COMPTA_2024_2025.sql l'a supprime : 70 lignes recalculees depuis le
   CRM, aucun montant en dur. Les trois exercices tombent desormais au centime,
   et ce controle doit rendre zero. S'il rend autre chose un jour, c'est que le
   socle a bouge sans que les comptes de produit suivent : relancer le script.

   L'EBITDA n'a pas bouge d'un centime -- V_ALLOCATION ne lit jamais les
   comptes de produit, le chiffre d'affaires du modele vient du socle CRM.

   =============================================================================
   POURQUOI LE MODELE PREND LE CRM

     1. LE GRAIN. Le socle porte 180 lignes -- campus x programme x annee
        d'etude x modalite -- la table de gestion 105, au grain campus x compte.
        Sans le CRM, aucune marge par programme ni par classe n'est calculable,
        et c'est tout l'objet du modele.

     2. LE PILOTAGE. Le CRM donne le CA comme un PRODUIT d'inducteurs,
        effectifs x droits de scolarite. On peut donc bouger les effectifs et
        voir le CA suivre. Un montant deja pose est un constat : il ne se
        simule pas.

   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    'Chiffre d''affaires en gestion (706 + 7062 + 708)'       AS "Contrôle",
    SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2025 THEN d.AMOUNT ELSE 0 END) AS "Montant 2025",
    SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2026 THEN d.AMOUNT ELSE 0 END) AS "Montant 2026"
FROM    AW_002_000004_000001 AS d
WHERE   d.ACCOUNT IN ('706', '7062', '708')
  AND   d.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(d.EXERCICE AS INT) IN (2025, 2026)
