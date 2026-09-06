/* =============================================================================
   Q_D2_CA_COMPTA  —  le controle de reconciliation du second drill.
   Une ligne, deux colonnes : le chiffre d'affaires tel que la COMPTABILITE le
   porte, comptes 706, 7062 et 708.

   A quoi ca sert. Le drill affiche un chiffre d'affaires venu du socle CRM, et
   la question tombe toujours : pourquoi pas la compta ? Cette requete met les
   deux cote a cote dans le classeur et laisse le rapprochement se voir.

   Mesure sur le perimetre complet :

        exercice     compta 7*        socle CRM        ecart
        2024        20 552 827       20 567 210      -14 383   -0,07 %
        2025        21 775 820       21 758 770      +17 050   +0,08 %
        2026        23 098 985       23 098 985            0    0,00 %

   Les deux disent la meme chose. Le modele prend le CRM pour deux raisons qui
   n'ont rien a voir avec l'exactitude :

     1. LE GRAIN. Le socle porte 180 lignes -- campus x programme x annee
        d'etude x modalite -- la compta 105, au grain campus x compte. Sans le
        CRM, aucune marge par programme ni par classe n'est calculable, et
        c'est tout l'objet du modele.

     2. LE PILOTAGE. Le CRM donne le CA comme un PRODUIT d'inducteurs,
        effectifs x droits de scolarite. On peut donc bouger les effectifs et
        voir le CA suivre. Un montant comptable est un constat : il ne se
        simule pas.

   L'ecart nul sur 2026 et non nul sur 2024-2025 se lit sans peine : 2026 a ete
   construit depuis le socle puis comptabilise, tandis que les deux exercices
   passes sont du realise, ou des annulations et des decalages d'encaissement
   creent quelques milliers d'euros de difference. C'est une lecture, pas une
   certitude, et elle vaut d'etre confirmee cote metier.

   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    'Chiffre d''affaires en comptabilité (706 + 7062 + 708)'  AS "Contrôle",
    SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2025 THEN d.AMOUNT ELSE 0 END) AS "Montant 2025",
    SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2026 THEN d.AMOUNT ELSE 0 END) AS "Montant 2026"
FROM    AW_002_000004_000001 AS d
WHERE   d.ACCOUNT IN ('706', '7062', '708')
  AND   d.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(d.EXERCICE AS INT) IN (2025, 2026)
