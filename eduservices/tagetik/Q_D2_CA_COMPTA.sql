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
   L'ECART, ET COMMENT ON LE REGLE

        exercice     compta 7*        socle CRM        ecart
        2024        20 552 827       20 567 210      -14 383   -0,070 %
        2025        21 775 820       21 758 770      +17 050   +0,078 %
        2026        23 098 985       23 098 985            0    0,000 %

   2026 tombe au centime parce que l'exercice est construit depuis le socle.
   2024 et 2025 portent un estime etabli separement, et l'ecart qu'ils laissent
   n'est pas une erreur de correspondance de comptes : le rapport entre les
   deux sources est CONSTANT a l'interieur d'un campus, d'un compte de produit
   a l'autre. ISCOM Toulouse par exemple : 1,00772 sur le 706, 1,00919 sur le
   7062, 1,00770 sur le 708. Des volumes ou des prix differents feraient bouger
   ce rapport d'un compte a l'autre ; il ne bouge pas. C'est donc un
   coefficient applique campus par campus, signe dans les deux sens -- MBway
   Paris -0,45 %, Tunon Paris +0,92 %, les deux Pigier a zero. Un bruit.

   FIX_CA_COMPTA_2024_2025.sql le supprime : un UPDATE de 70 lignes qui
   recalcule les comptes de produit depuis le CRM, sans aucun montant en dur.
   Apres passage, les trois exercices tombent a zero.

   Cela ne change RIEN au cockpit ni aux drills. V_ALLOCATION ne lit jamais les
   comptes de produit : le chiffre d'affaires du modele vient du socle CRM.
   Seul ce rapprochement bouge.

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
