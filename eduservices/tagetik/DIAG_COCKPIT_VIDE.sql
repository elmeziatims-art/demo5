/* =============================================================================
   DIAG_COCKPIT_VIDE  —  pourquoi Q_COCKPIT_COMPLET ne rend aucune ligne.

   A LANCER DANS SSMS, ETAPE PAR ETAPE. La PREMIERE etape qui rend 0 nomme le
   coupable ; les suivantes ne servent plus a rien.

   =============================================================================
   CE QUE LA STRUCTURE DE LA REQUETE PERMET DEJA D'ELIMINER

   L'ossature est :   FROM ( ... ) AS n   OUTER APPLY ( ... ) AS p

   OUTER APPLY ne SUPPRIME JAMAIS une ligne de n : quand le sous-ensemble p est
   vide, il rend NULL et la ligne reste. Le raccord N-1 est donc HORS DE CAUSE,
   et avec lui toute la moitie basse de la requete.

   Zero ligne en sortie => zero ligne dans n => zero ligne dans V_ALLOCATION.

   Le realignement du 06/09 est hors de cause lui aussi : il n'a touche que les
   comptes 706, 7062 et 708, et V_ALLOCATION ne lit que des comptes de charge.

   =============================================================================
   LES TROIS SEULS ENDROITS QUI PEUVENT ANNIHILER V_ALLOCATION

   Ce sont ses trois jointures fermantes. Une jointure interne dont le cote
   droit est vide ne rend pas des NULL : elle efface la ligne.

     1. JOIN sieg ON EXERCICE + VERSION      LE PLUS DANGEREUX
        Le pool siege est filtre sur ENTITY = 'GRP' et groupe par exercice.
        Il n'y a qu'UNE ligne par exercice pour TOUS les campus. Si GRP n'a
        aucune ecriture sur un exercice, l'exercice ENTIER disparait. Si GRP
        est vide partout, la vue est vide partout.

     2. JOIN cmp ON ENTITY + EXERCICE + VERSION
        Le pool de charges du campus. Un campus sans ecriture comptable
        disparait -- lui seul, pas les autres. Donne une vue partiellement
        vide, rarement totalement.

     3. CROSS JOIN k
        Les cles d'allocation. Le sous-select est un agregat sans GROUP BY :
        il rend TOUJOURS une ligne, meme sur zero donnee. Il ne peut donc pas
        vider la vue -- mais si K1..K4 reviennent NULL, tous les COST_*
        deviennent NULL, donc CA - COST_COMPLET est NULL et l'EBITDA aussi.
        Symptome different : des LIGNES QUI SORTENT AVEC DES CASES VIDES, pas
        une absence de lignes.

   Et une quatrieme cause, qui ne se voit pas dans le plan : si V_MOTEUR ou
   V_BUDGET n'existent plus ou sont en erreur, V_ALLOCATION est en erreur, et
   l'outil peut presenter cette erreur comme un resultat vide.
   ============================================================================= */

/* ---- ETAPE 1 : LA VUE REND-ELLE QUELQUE CHOSE ? -------------------------
   Le test le plus rapide. S'il rend 0, la requete du cockpit est innocente et
   tout se joue dans la vue : passer a l'etape 2.
   S'il rend des lignes, la vue va bien : sauter directement a l'etape 6.      */
SELECT  COUNT(*) AS LIGNES_TOTAL FROM V_ALLOCATION;

SELECT  EXERCICE, VERSION, COUNT(*) AS LIGNES, COUNT(DISTINCT ENTITY) AS CAMPUS
FROM    V_ALLOCATION
GROUP BY EXERCICE, VERSION
ORDER BY EXERCICE, VERSION;

/* ---- ETAPE 2 : LA SOURCE DES VOLUMES ------------------------------------
   Attendu : trois exercices, 60 lignes chacun, 14 campus.
   Si c'est vide, le probleme est en amont de tout le reste.                  */
SELECT  EXERCICE, COUNT(*) AS LIGNES, COUNT(DISTINCT ENTITY) AS CAMPUS
FROM    AW_002_000002_000001
GROUP BY EXERCICE
ORDER BY EXERCICE;

/* ---- ETAPE 3 : LE POOL SIEGE  <<<  PREMIER SUSPECT  --------------------
   Attendu : une ligne par exercice, avec un montant non nul.
   UN EXERCICE ABSENT ICI = CET EXERCICE ENTIEREMENT ABSENT DE LA VUE.        */
SELECT  EXERCICE,
        COUNT(*)                                                        AS ECRITURES_GRP,
        SUM(CASE WHEN ACCOUNT IN ('6414','6226','626','6281','6331','6333')
                 THEN AMOUNT ELSE 0 END)                                AS HOLDING_TOT,
        SUM(CASE WHEN ACCOUNT = '6236' THEN AMOUNT ELSE 0 END)          AS MARQUE_TOT
FROM    AW_002_000004_000001
WHERE   ENTITY = 'GRP'
GROUP BY EXERCICE
ORDER BY EXERCICE;

/* ---- ETAPE 4 : LES POOLS CAMPUS  <<<  SECOND SUSPECT  ------------------
   Rend la liste des campus qui ont des volumes mais AUCUNE ecriture
   comptable. Chacun de ceux-la est efface de la vue par la jointure interne.
   Attendu : AUCUNE LIGNE.                                                    */
SELECT  DISTINCT v.ENTITY, v.EXERCICE
FROM    AW_002_000002_000001 AS v
WHERE   NOT EXISTS (SELECT 1 FROM AW_002_000004_000001 AS d
                    WHERE d.ENTITY = v.ENTITY AND d.EXERCICE = v.EXERCICE)
ORDER BY v.EXERCICE, v.ENTITY;

/* ---- ETAPE 5 : LES CLES D'ALLOCATION ------------------------------------
   Attendu : quatre valeurs non nulles parmi REV_CA / VOL_EFF / VOL_CLASS.
   Des NULL ici ne VIDENT PAS la vue : ils vident les COUTS, donc l'EBITDA.
   Symptome : des lignes qui sortent, mais EBITDA a blanc.                    */
SELECT  PARAMETRE, KEY_ALLOC, DATEUPD
FROM    AW_002_000001_000001
WHERE   PARAMETRE IN ('ALLOC_GRP_HOLDING','ALLOC_BRAND_CAMP',
                      'ALLOC_CAMP_CLASS','ALLOC_GRP_MARQUE')
ORDER BY PARAMETRE, DATEUPD DESC;

/* ---- ETAPE 6 : LA REQUETE DU COCKPIT, NIVEAU PAR NIVEAU -----------------
   A ne faire que si l'etape 1 a rendu des lignes. On remonte le meme escalier
   que la requete : si 6a rend des lignes et 6b zero, c'est la jointure
   d'acquisition qui casse ; si 6b rend des lignes, c'est que la requete
   complete va bien et que le vide vient de l'outil, pas du SQL.              */

-- 6a : l'agregat de base, sans rien d'autre
SELECT  COUNT(*) AS NIVEAU_6A
FROM (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                SUM(a.CA) AS CA
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
     ) AS v;

-- 6b : le meme, avec la jointure sur la depense d'acquisition
SELECT  COUNT(*) AS NIVEAU_6B
FROM (
        SELECT  a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY,
                SUM(a.CA) AS CA
        FROM    V_ALLOCATION AS a
        GROUP BY a.SCENARIO, a.VERSION, a.PERIODE, a.EXERCICE, a.MARQUE, a.ENTITY
     ) AS v
LEFT JOIN (
        SELECT  z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY,
                SUM(z.DEPENSE_ACQ) AS SPEND_ACQ
        FROM    AW_002_000002_000001 AS z
        GROUP BY z.SCENARIO, z.PERIODE, z.EXERCICE, z.ENTITY
     ) AS s
       ON  s.SCENARIO = v.SCENARIO AND s.PERIODE  = v.PERIODE
      AND  s.EXERCICE = v.EXERCICE AND s.ENTITY   = v.ENTITY;

/* ---- ETAPE 7 : SI TOUT CE QUI PRECEDE REND DES LIGNES -------------------
   Alors le SQL va bien et le vide vient du contexte d'execution. Deux causes
   classiques, dans cet ordre :

     - la requete tourne dans le loader Tagetik sur une base ou un schema qui
       n'est pas celui de SSMS. Prefixer V_ALLOCATION du schema (dbo.) et
       relancer.
     - l'outil a presente une ERREUR comme un resultat vide. Relancer la meme
       requete dans SSMS : l'erreur, elle, s'affiche.
   ============================================================================= */
