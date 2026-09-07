/* =============================================================================
   Q_HYPOTHESES  —  les douze leviers du cadrage, les trois scenarios en colonnes.

   A QUOI CA SERT. Le masque ne doit plus porter un seul taux en dur. Il lit
   cette zone, restituee a droite dans des colonnes masquees, et un selecteur
   « Cadrage / Optimiste / Prudent » designe la colonne retenue par un
   INDEX/MATCH. Consequence : on bouge un taux dans Tagetik, on rafraichit, et
   les quarante nombres du classeur suivent. On bascule de scenario, pareil.

   LA FORME EST DELIBEREE : UNE LIGNE PAR LEVIER, TROIS COLONNES DE VALEURS.
   Une restitution « une ligne par levier ET par version » obligerait le masque
   a filtrer ; ici il n'a qu'a choisir une colonne. C'est ce qui rend le
   INDEX/MATCH trivial et le rapport lisible tel quel.

   ORDRE et FAMILLE ne sont pas dans le cube -- ce sont des attributs
   d'affichage. Ils viennent d'un bloc VALUES joint sur le code, comme dans
   Q_D2_SOCLE. Le cube ne stocke que ce qui se saisit : la valeur.

   PAS D'ORDER BY : le loader enveloppe la requete dans un SELECT COUNT(*), et
   un ORDER BY externe la casse. Le tri se fait sur la colonne ORDRE, cote
   rapport.

   SI LA TABLE D'HYPOTHESES PORTE D'AUTRES NOMS DE COLONNES, il n'y a que la
   clause FROM et les six references de h. a ajuster -- le reste est portable.

   HYP_PRICE_COEF n'est pas ici : il est au grain MARQUE et non versionne
   (VERSION = GEN), donc il ne rentre pas dans cette grille. C'est une autre
   restitution, si on en a besoin un jour.
   ============================================================================= */
SELECT
    d.ORDRE,
    d.FAMILLE,
    d.CODE,
    d.LIBELLE,
    SUM(CASE WHEN h.VERSION = 'V01' THEN h.AMOUNT ELSE 0 END)   AS "Cadrage",
    SUM(CASE WHEN h.VERSION = 'V02' THEN h.AMOUNT ELSE 0 END)   AS "Optimiste",
    SUM(CASE WHEN h.VERSION = 'V03' THEN h.AMOUNT ELSE 0 END)   AS "Prudent",
    d.UNITE,
    d.BRANCHE
FROM (
        VALUES
        ( 1, 'Croissance', 'HYP_ACQ_BUD',      'Variation du budget acquisition',          'taux', 'oui'),
        ( 2, 'Croissance', 'HYP_BRAND_BUD',    'Variation du budget de marque',            'taux', 'oui'),
        ( 3, 'Croissance', 'HYP_PRICE',        'Hausse tarifaire',                         'taux', 'oui'),
        ( 4, 'Croissance', 'HYP_CONV_LEAD',    'Gain conversion Lead vers Candidature',    'taux', 'socle'),
        ( 5, 'Croissance', 'HYP_CONV_ADM',     'Gain conversion Admis vers Inscrit',       'taux', 'socle'),
        ( 6, 'Croissance', 'HYP_PASSAGE',      'Amelioration du taux de passage',          'taux', 'socle'),
        ( 7, 'Couts',      'HYP_INFL_EXT',     'Inflation des charges externes',           'taux', 'oui'),
        ( 8, 'Couts',      'HYP_SALARY',       'Politique salariale',                      'taux', 'oui'),
        ( 9, 'Couts',      'HYP_FTE_PERM',     'Variation des effectifs permanents',       'taux', 'oui'),
        (10, 'Couts',      'HYP_PRODUCTIVITY', 'Effort de productivite',                   'taux', 'oui'),
        (11, 'Couts',      'HYP_STRUCT_COST',  'Variation des couts de structure',         'taux', 'oui'),
        (12, 'Constante',  'HYP_FEE',          'Frais de dossier par nouvel inscrit',      'euros','non')
     ) AS d (ORDRE, FAMILLE, CODE, LIBELLE, UNITE, BRANCHE)
LEFT JOIN AW_002_000001 AS h
       ON  h.ACCOUNT  = d.CODE
       AND h.ENTITY   = 'GRP'
       AND CAST(h.EXERCICE AS INT) = 2027
       AND h.VERSION IN ('V01', 'V02', 'V03')
GROUP BY d.ORDRE, d.FAMILLE, d.CODE, d.LIBELLE, d.UNITE, d.BRANCHE
