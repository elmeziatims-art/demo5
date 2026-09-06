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
   L'ECART, ET POURQUOI ON LE GARDE

        exercice     compta 7*        socle CRM        ecart
        2024        20 552 827       20 567 210      -14 383   -0,07 %
        2025        21 775 820       21 758 770      +17 050   +0,08 %
        2026        23 098 985       23 098 985            0    0,00 %

   Cette table n'est pas un grand livre cloture : elle porte l'ESTIME. Un ecart
   de sept centiemes de pour cent entre un estime et un modele pilote par les
   inducteurs du CRM n'est donc pas une anomalie, c'est le fonctionnement
   normal des deux chaines. On ne le corrige pas.

   Que 2026 tombe exactement au centime se lit sans peine : l'exercice est
   construit depuis le socle, donc aligne par construction. Les deux exercices
   passes portent un estime etabli separement.

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
