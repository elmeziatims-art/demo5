/* =============================================================================
   Q_HYPOTHESES  —  les douze leviers du cadrage, les trois scenarios en colonnes.

   A QUOI CA SERT. Le masque ne porte plus un seul taux en dur. Il lit cette
   zone, collee en AD..AJ de l'onglet « Le moteur », et un selecteur
   « Cadrage / Optimiste / Prudent » designe la colonne retenue par un
   INDEX/MATCH a deux entrees -- la ligne par le code, la colonne par le
   scenario. On bouge un taux dans Tagetik, on rafraichit, tout suit.

   =============================================================================
   LE PIEGE DE CETTE TABLE, ET IL EST SERIEUX : ELLE STOCKE DES DEFORMATIONS.

   PROVENIENZA vaut INPUT_DEFORM. Une meme cle (PARAMETRE, VERSION) peut donc
   porter PLUSIEURS lignes -- les saisies successives -- et la valeur du levier
   est LEUR SOMME, pas la derniere, pas la plus grande.

       HYP_PRICE        V01    0,0200  puis  -0,0171   =  0,0029
       HYP_PRODUCTIVITY V01    0,0100  puis  +0,0085   =  0,0185
       HYP_ACQ_BUD      V01    0,0800  puis  +0,0100  puis  -0,0100  =  0,0800
       HYP_BRAND_BUD    V02    0,2000  puis  -0,0500   =  0,1500

   Un MAX, un TOP 1 ou un « dernier OID » rendrait 0,0200 sur la hausse
   tarifaire au lieu de 0,0029 -- soit sept fois trop, sans aucune erreur a
   l'ecran. C'est pour ca que la requete somme, et qu'il ne faut pas la
   « simplifier ».

   Verifie sur les douze leviers et les trois versions : la somme redonne
   exactement les valeurs du classeur de cadrage.

   =============================================================================
   LES NOMS REELS, CONSTATES DANS LA TABLE

     le compte      PARAMETRE   (et non ACCOUNT)
     la valeur      MEASURE     (et non AMOUNT)
     le scenario    VERSION     V01 / V02 / V03   -- et GEN pour le non versionne
     l'annee        IL N'Y A PAS DE COLONNE EXERCICE : c'est SCENARIO qui la
                    porte, '2027BUD_V1'. Filtrer sur EXERCICE echouerait.

   HYP_PRICE_COEF n'est pas dans cette grille : il est au grain MARQUE
   (ENTITY = MBWAY_REF, ISCOM_REF...) et en VERSION GEN, donc non versionne.
   C'est une autre restitution, si on en a besoin un jour.

   Pas d'ORDER BY : le loader enveloppe la requete dans un SELECT COUNT(*). Le
   tri se fait sur la colonne ORDRE, cote rapport.
   ============================================================================= */
SELECT
    d.ORDRE,
    d.FAMILLE,
    d.CODE,
    d.LIBELLE,
    SUM(CASE WHEN h.VERSION = 'V01' THEN h.MEASURE ELSE 0 END)  AS "Cadrage",
    SUM(CASE WHEN h.VERSION = 'V02' THEN h.MEASURE ELSE 0 END)  AS "Optimiste",
    SUM(CASE WHEN h.VERSION = 'V03' THEN h.MEASURE ELSE 0 END)  AS "Prudent",
    d.UNITE,
    d.BRANCHE
FROM (
        VALUES
        ( 1, 'Croissance', 'HYP_ACQ_BUD',       'Variation du budget acquisition',        'taux',  'oui'),
        ( 2, 'Croissance', 'HYP_BRAND_BUD',     'Variation du budget de marque',          'taux',  'oui'),
        ( 3, 'Croissance', 'HYP_PRICE',         'Hausse tarifaire',                       'taux',  'oui'),
        ( 4, 'Croissance', 'HYP_CNV_LEAD_CAND', 'Gain conversion Lead vers Candidature',  'taux',  'socle'),
        ( 5, 'Croissance', 'HYP_CNV_ADM_INS',   'Gain conversion Admis vers Inscrit',     'taux',  'socle'),
        ( 6, 'Croissance', 'HYP_PASS_RATE',     'Amelioration du taux de passage',        'taux',  'socle'),
        ( 7, 'Couts',      'HYP_INFL_EXT',      'Inflation des charges externes',         'taux',  'oui'),
        ( 8, 'Couts',      'HYP_SALARY',        'Politique salariale',                    'taux',  'oui'),
        ( 9, 'Couts',      'HYP_FTE_PERM',      'Variation des effectifs permanents',     'taux',  'oui'),
        (10, 'Couts',      'HYP_PRODUCTIVITY',  'Effort de productivite',                 'taux',  'oui'),
        (11, 'Couts',      'HYP_STRUCT_COST',   'Variation des couts de structure',       'taux',  'oui'),
        (12, 'Constante',  'HYP_FILE_FEE',      'Frais de dossier par nouvel inscrit',    'euros', 'non')
     ) AS d (ORDRE, FAMILLE, CODE, LIBELLE, UNITE, BRANCHE)
LEFT JOIN AW_002_000001_000001 AS h
       ON  h.PARAMETRE = d.CODE
       AND h.ENTITY    = 'GRP'
       AND h.SCENARIO  = '2027BUD_V1'
       AND h.PERIODE   = '12'
GROUP BY d.ORDRE, d.FAMILLE, d.CODE, d.LIBELLE, d.UNITE, d.BRANCHE
