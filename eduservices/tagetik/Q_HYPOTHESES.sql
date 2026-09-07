/* =============================================================================
   Q_HYPOTHESES  —  les douze leviers du cadrage, les trois scenarios en colonnes.

   =============================================================================
   CORRECTION : LA PREMIERE VERSION VISAIT UNE TABLE QUI N'EXISTE PAS.

   J'avais ecrit AW_002_000001 en me fiant a la cartographie du depot -- qui est
   un document de CONCEPTION, pas un schema verifie. « Invalid object name » :
   c'etait merite. Cette version ne vise plus que la table dont on s'est deja
   servi avec succes, AW_002_000004_000001, et ne lit que quatre colonnes dont
   l'existence est prouvee par V_MOTEUR_CAL : ENTITY, ACCOUNT, EXERCICE, AMOUNT.

   PAS DE COLONNE VERSION, DONC. Le scenario est encode dans le CODE DU COMPTE :
   HYP_ACQ_BUD_V01, _V02, _V03. C'est moins elegant qu'une dimension Version,
   mais ca ne suppose rien sur le schema -- et le masque, lui, ne voit aucune
   difference : il continue de chercher la ligne HYP_ACQ_BUD et de choisir sa
   colonne.

   Le precedent existe deja dans le cube : TEC_PL et TEC_EBITDA y sont stockes
   sur GRP / 2027 exactement de cette facon. Les hypotheses sont des saisies,
   elles ont leur place la.

   =============================================================================
   SI VOUS VOULEZ LA VERSION PROPRE, une dimension Version plutot qu'un suffixe,
   il suffit de me dire ce que rend ceci :

       SELECT TABLE_NAME, COLUMN_NAME
       FROM   INFORMATION_SCHEMA.COLUMNS
       WHERE  TABLE_NAME LIKE 'AW[_]002%'

   Je reecris la requete sur le bon objet en trois minutes.

   =============================================================================
   LA FORME : UNE LIGNE PAR LEVIER, TROIS COLONNES DE VALEURS. Le masque n'a
   qu'a choisir une colonne -- c'est ce qui rend le INDEX/MATCH trivial. ORDRE,
   FAMILLE et LIBELLE ne sont pas dans le cube : ce sont des attributs
   d'affichage, ils viennent du bloc VALUES. Le cube ne stocke que la valeur.

   Pas d'ORDER BY : le loader enveloppe la requete dans un SELECT COUNT(*).
   ============================================================================= */
SELECT
    d.ORDRE,
    d.FAMILLE,
    d.CODE,
    d.LIBELLE,
    SUM(CASE WHEN h.ACCOUNT = d.CODE + '_V01' THEN h.AMOUNT ELSE 0 END)  AS "Cadrage",
    SUM(CASE WHEN h.ACCOUNT = d.CODE + '_V02' THEN h.AMOUNT ELSE 0 END)  AS "Optimiste",
    SUM(CASE WHEN h.ACCOUNT = d.CODE + '_V03' THEN h.AMOUNT ELSE 0 END)  AS "Prudent",
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
LEFT JOIN AW_002_000004_000001 AS h
       ON  h.ACCOUNT LIKE d.CODE + '[_]V0%'
       AND h.ENTITY  = 'GRP'
       AND CAST(h.EXERCICE AS INT) = 2027
GROUP BY d.ORDRE, d.FAMILLE, d.CODE, d.LIBELLE, d.UNITE, d.BRANCHE
