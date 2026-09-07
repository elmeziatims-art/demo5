/* =============================================================================
   SEED_HYPOTHESES  —  ecrit les douze leviers x trois scenarios dans le cube.

   POURQUOI IL FAUT CE SCRIPT. Les taux du cadrage vivent aujourd'hui dans le
   classeur, en dur, cellules C22:E27 / C31:E35 / C39. Tant qu'ils y restent,
   aucune requete ne peut les rendre et le masque ne peut pas etre dynamique.
   On les remonte donc dans le cube, la ou ils auraient toujours du etre : ce
   sont des SAISIES, pas des constantes de feuille.

   VALEURS ABSOLUES, PAS DE DELTAS. Un script qui ecrit des valeurs absolues
   peut etre rejoue dix fois sans deriver. Un script qui ajoute, non.

   LES DEUX CASES VIDES DU CADRAGE SONT ECRITES A ZERO, explicitement :
   l'effort de productivite en Prudent, et la variation des couts de structure
   en Cadrage. Une case vide dans un classeur est une ambiguite ; un zero dans
   un cube est une decision.
   ============================================================================= */
MERGE AW_002_000001 AS c
USING (
        SELECT * FROM (
            VALUES
            ('HYP_ACQ_BUD',      'V01', 0.0800), ('HYP_ACQ_BUD',      'V02', 0.1500), ('HYP_ACQ_BUD',      'V03', -0.0500),
            ('HYP_BRAND_BUD',    'V01', 0.1000), ('HYP_BRAND_BUD',    'V02', 0.1500), ('HYP_BRAND_BUD',    'V03', -0.0500),
            ('HYP_PRICE',        'V01', 0.0029), ('HYP_PRICE',        'V02', 0.0350), ('HYP_PRICE',        'V03',  0.0200),
            ('HYP_CONV_LEAD',    'V01', 0.0100), ('HYP_CONV_LEAD',    'V02', 0.0300), ('HYP_CONV_LEAD',    'V03', -0.0100),
            ('HYP_CONV_ADM',     'V01', 0.0100), ('HYP_CONV_ADM',     'V02', 0.0250), ('HYP_CONV_ADM',     'V03', -0.0100),
            ('HYP_PASSAGE',      'V01', 0.0050), ('HYP_PASSAGE',      'V02', 0.0150), ('HYP_PASSAGE',      'V03', -0.0100),
            ('HYP_INFL_EXT',     'V01', 0.0200), ('HYP_INFL_EXT',     'V02', 0.0150), ('HYP_INFL_EXT',     'V03',  0.0300),
            ('HYP_SALARY',       'V01', 0.0250), ('HYP_SALARY',       'V02', 0.0200), ('HYP_SALARY',       'V03',  0.0300),
            ('HYP_FTE_PERM',     'V01', 0.0400), ('HYP_FTE_PERM',     'V02', 0.0300), ('HYP_FTE_PERM',     'V03',  0.0500),
            ('HYP_PRODUCTIVITY', 'V01', 0.0185), ('HYP_PRODUCTIVITY', 'V02', 0.0300), ('HYP_PRODUCTIVITY', 'V03',  0.0000),
            ('HYP_STRUCT_COST',  'V01', 0.0000), ('HYP_STRUCT_COST',  'V02',-0.0300), ('HYP_STRUCT_COST',  'V03',  0.0400),
            ('HYP_FEE',          'V01',90.0000), ('HYP_FEE',          'V02',90.0000), ('HYP_FEE',          'V03', 90.0000)
        ) AS v (ACCOUNT, VERSION, AMOUNT)
     ) AS s
   ON  c.ACCOUNT = s.ACCOUNT
   AND c.VERSION = s.VERSION
   AND c.ENTITY  = 'GRP'
   AND CAST(c.EXERCICE AS INT) = 2027
WHEN MATCHED THEN
     UPDATE SET c.AMOUNT = s.AMOUNT
WHEN NOT MATCHED BY TARGET THEN
     INSERT (ENTITY, ACCOUNT, EXERCICE, VERSION, SCENARIO, PERIOD, AMOUNT)
     VALUES ('GRP',  s.ACCOUNT, '2027', s.VERSION, '2027BUD_V1', '12', s.AMOUNT);

/* Controle : douze lignes par version, trente-six au total. */
SELECT h.VERSION, COUNT(*) AS LIGNES, SUM(h.AMOUNT) AS SOMME
FROM   AW_002_000001 AS h
WHERE  h.ENTITY = 'GRP' AND CAST(h.EXERCICE AS INT) = 2027 AND h.ACCOUNT LIKE 'HYP[_]%'
GROUP BY h.VERSION;
