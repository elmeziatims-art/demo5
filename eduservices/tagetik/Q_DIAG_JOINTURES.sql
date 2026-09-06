/* =============================================================================
   Q_DIAG_JOINTURES  —  a lancer AVANT de conclure quoi que ce soit.
   Repond a une seule question : pourquoi les colonnes N-1 sortent a zero.

   Une ligne par combinaison de cles reellement presente. On y lit trois choses.

   1. VERSION — combien V_ALLOCATION en produit-il par exercice ? S'il y en a
      deux ('ACT' cote socle, autre chose cote V_MOTEUR), le LEFT JOIN du
      cockpit qui exige p.VERSION = n.VERSION ne retrouve jamais son N-1, et
      INSCRITS_N1 comme SPEND_ACQ_N1 retombent a 0 par le COALESCE.
      VERSION_DU_N1 dit sous quelle version le N-1 existe reellement.

   2. NB_ACQ — pour combien de campus AW_002_000002_000001 renvoie-t-il une
      depense sur la meme cle. S'il vaut 0 alors que NB_ENTITY vaut 14, ce sont
      SCENARIO ou PERIODE qui ne correspondent pas entre les deux tables.

   3. N1_DISPO — l'exercice precedent existe-t-il dans le meme SCENARIO et la
      meme PERIODE. Sur le plus ancien exercice il vaut 0, c'est normal.

   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    v.SCENARIO,
    v.VERSION,
    v.PERIODE,
    v.EXERCICE,
    COUNT(DISTINCT v.ENTITY)                                    AS NB_ENTITY,
    SUM(CASE WHEN s.ENTITY IS NOT NULL THEN 1 ELSE 0 END)       AS NB_ACQ,
    SUM(COALESCE(s.SPEND_ACQ, 0))                               AS SPEND_ACQ_TOTAL,
    MAX(CASE WHEN n1.EXERCICE IS NOT NULL THEN 1 ELSE 0 END)    AS N1_DISPO,
    MAX(COALESCE(n1.VERSION, '(aucune)'))                       AS VERSION_DU_N1
FROM (
        SELECT DISTINCT a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
        FROM   V_ALLOCATION AS a
     ) AS v
LEFT JOIN (
        SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
        FROM    AW_002_000002_000001 AS z
        GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY
     ) AS s
       ON  s.SCENARIO = v.SCENARIO
      AND  s.PERIODE  = v.PERIODE
      AND  s.EXERCICE = v.EXERCICE
      AND  s.ENTITY   = v.ENTITY
LEFT JOIN (
        SELECT DISTINCT a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.ENTITY
        FROM   V_ALLOCATION AS a
     ) AS n1
       ON  n1.SCENARIO = v.SCENARIO
      AND  n1.PERIODE  = v.PERIODE
      AND  n1.ENTITY   = v.ENTITY
      AND  CAST(n1.EXERCICE AS INT) = CAST(v.EXERCICE AS INT) - 1
GROUP BY v.SCENARIO, v.VERSION, v.PERIODE, v.EXERCICE
