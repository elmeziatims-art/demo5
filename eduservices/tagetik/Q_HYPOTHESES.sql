/* =============================================================================
   Q_HYPOTHESES  —  les douze leviers du cadrage, les trois scenarios en colonnes.

   A QUOI CA SERT. Le masque ne porte plus un seul taux en dur. Il lit cette
   zone, collee en AD..AJ de l'onglet « Le moteur », et un selecteur
   « Cadrage / Optimiste / Prudent » designe la colonne retenue par un
   INDEX/MATCH a deux entrees -- la ligne par le code, la colonne par le
   scenario. On bouge un taux dans Tagetik, on rafraichit, et les quarante
   nombres du classeur suivent.

   =============================================================================
   CE QUI A ETE CORRIGE

   J'avais ecrit AW_002_000001 : il manquait le second segment. C'est
   AW_002_000001_000001, et les taux y sont deja -- il n'y a donc RIEN a
   alimenter. Le script de seed que j'avais joint ne servait a rien : supprime.

   =============================================================================
   DEUX POINTS DE NOMMAGE QUE JE N'AI PAS PU VERIFIER, ET QUI SE CORRIGENT EN
   DEUX LIGNES SI JE ME TROMPE

     1. la colonne du scenario -- j'ecris h.VERSION, avec V01 / V02 / V03 ;
     2. les codes des leviers -- je les reprends de votre cartographie, et
        l'entite GRP.

   Si l'un des deux est faux, la requete ne renvoie pas d'erreur : elle rend
   douze lignes a ZERO. C'est le symptome a reconnaitre. Q_HYPOTHESES_BRUT.sql
   donne les vrais noms d'un coup.

   =============================================================================
   LA FORME : UNE LIGNE PAR LEVIER, TROIS COLONNES DE VALEURS. Le masque n'a
   qu'a choisir une colonne. ORDRE, FAMILLE et LIBELLE ne sont pas dans le cube
   -- ce sont des attributs d'affichage, ils viennent du bloc VALUES. Le cube ne
   stocke que la valeur.

   Pas d'ORDER BY : le loader enveloppe la requete dans un SELECT COUNT(*). Le
   tri se fait sur la colonne ORDRE, cote rapport.
   ============================================================================= */
SELECT
    d.ORDRE,
    d.FAMILLE,
    d.CODE,
    d.LIBELLE,
    SUM(CASE WHEN h.VERSION = 'V01' THEN h.AMOUNT ELSE 0 END)  AS "Cadrage",
    SUM(CASE WHEN h.VERSION = 'V02' THEN h.AMOUNT ELSE 0 END)  AS "Optimiste",
    SUM(CASE WHEN h.VERSION = 'V03' THEN h.AMOUNT ELSE 0 END)  AS "Prudent",
    d.UNITE,
    d.BRANCHE
FROM (
        VALUES
        ( 1, 'Croissance', 'HYP_ACQ_BUD',      'Variation du budget acquisition',        'taux',  'oui'),
        ( 2, 'Croissance', 'HYP_BRAND_BUD',    'Variation du budget de marque',          'taux',  'oui'),
        ( 3, 'Croissance', 'HYP_PRICE',        'Hausse tarifaire',                       'taux',  'oui'),
        ( 4, 'Croissance', 'HYP_CONV_LEAD',    'Gain conversion Lead vers Candidature',  'taux',  'socle'),
        ( 5, 'Croissance', 'HYP_CONV_ADM',     'Gain conversion Admis vers Inscrit',     'taux',  'socle'),
        ( 6, 'Croissance', 'HYP_PASSAGE',      'Amelioration du taux de passage',        'taux',  'socle'),
        ( 7, 'Couts',      'HYP_INFL_EXT',     'Inflation des charges externes',         'taux',  'oui'),
        ( 8, 'Couts',      'HYP_SALARY',       'Politique salariale',                    'taux',  'oui'),
        ( 9, 'Couts',      'HYP_FTE_PERM',     'Variation des effectifs permanents',     'taux',  'oui'),
        (10, 'Couts',      'HYP_PRODUCTIVITY', 'Effort de productivite',                 'taux',  'oui'),
        (11, 'Couts',      'HYP_STRUCT_COST',  'Variation des couts de structure',       'taux',  'oui'),
        (12, 'Constante',  'HYP_FEE',          'Frais de dossier par nouvel inscrit',    'euros', 'non')
     ) AS d (ORDRE, FAMILLE, CODE, LIBELLE, UNITE, BRANCHE)
LEFT JOIN AW_002_000001_000001 AS h
       ON  h.ACCOUNT = d.CODE
       AND h.ENTITY  = 'GRP'
       AND CAST(h.EXERCICE AS INT) = 2027
GROUP BY d.ORDRE, d.FAMILLE, d.CODE, d.LIBELLE, d.UNITE, d.BRANCHE
