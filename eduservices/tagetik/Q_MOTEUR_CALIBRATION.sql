/* =============================================================================
   Q_MOTEUR_CALIBRATION  —  ce qui rend l'onglet « Le moteur » vivant.

   UNE LIGNE PAR CAMPUS, QUATORZE LIGNES, TREIZE COLONNES. Elle rend tout ce
   que la feuille affiche AVANT le geste, et rien de ce qui vient apres.

   =============================================================================
   LA COUPURE : LA REQUETE CALIBRE, LE CLASSEUR APPLIQUE LE GESTE

   Le Delta de budget est une SAISIE. Les cinq dernieres colonnes de la feuille
   -- Delta budget, inscrits gagnes, CA gagne, EBITDA gagne, CAC marginal --
   dependent de cette saisie et doivent donc rester dans le classeur, sinon
   changer 8 % en 12 % obligerait a relancer la requete.

   La requete rend le MATERIAU DE CALIBRATION, qui lui ne depend d'aucune
   saisie :

       Campus · Marque
       Leads payants        2024 · 2025 · 2026
       Budget acquisition   2024 · 2025 · 2026
       Elasticite           la pente, calculee ici
       Conversion           inscrits / leads, exercice 2026
       CA par inscrit       exercice 2026
       Ecart de leads       un controle, voir plus bas

   Le classeur ne porte alors plus une seule valeur en dur.

   =============================================================================
   L'ELASTICITE EST CALCULEE EN SQL, ET C'EST LA MEME QUE CELLE D'EXCEL

   La feuille fait =SLOPE(LN(leads); LN(budget)) sur trois points. SLOPE est
   une regression des moindres carres, et une regression des moindres carres
   est une AGREGATION : elle s'ecrit avec des SUM, sans boucle et sans CTE.

       pente = ( n·Σ(xy) − Σx·Σy )  /  ( n·Σ(x²) − (Σx)² )
       avec  x = LN(budget)   et   y = LN(leads payants)

   En T-SQL, LOG() est le logarithme NEPERIEN -- c'est bien LN, pas log10.

   Verifie sur l'extrait, les quatorze campus : MBway Bordeaux 0,5385, ISCOM
   Paris 0,4421, Tunon Paris 0,4191. Identique a SLOPE au dix-millieme.

   On aurait pu se contenter de l'arc entre les deux bouts,
   LN(leads26/leads24) / LN(budget26/budget24). Sur cette donnee il donne
   EXACTEMENT le meme chiffre -- les series sont geometriques, donc les trois
   points en log sont parfaitement alignes. Mais sur de la vraie donnee ils
   divergeraient, et la regression est la seule des deux qui utilise le point
   du milieu. C'est donc elle qu'on garde.

   =============================================================================
   DEUX CORRECTIONS PAR RAPPORT A LA REQUETE ACTUELLE

   1. LE DENOMINATEUR DE LA CONVERSION. La requete actuelle ecrit

          SUM(VOL_NEW) / NULLIF(SUM(VOL_LEAD), 0)

      alors qu'elle expose, deux lignes plus haut, un LEAD_TOT construit comme
      VOL_LEAD_ORG + VOL_LEAD_PAY. Ce sont DEUX TOTAUX DE LEADS DIFFERENTS
      dans la meme ligne : sur les trois exercices, VOL_LEAD vaut 48 728 et
      ORG + PAY vaut 49 174. Quarante-trois lignes sur cent quatre-vingts sont
      en ecart.

      Sur 2026 les deux coincident a une unite pres, donc la conversion
      affichee aujourd'hui est juste. Mais une conversion 2024 ou 2025
      calculee sur VOL_LEAD serait fausse d'environ un pour cent, sans que
      rien ne le signale.

      Ici la conversion est calculee sur ORG + PAY, le meme total que celui
      dont le modele se sert. Et l'ecart est EXPOSE en derniere colonne :
      s'il n'est pas nul, c'est la source qu'il faut regarder.

   2. LES DIVISIONS SONT PROTEGEES. Chacune est prefixee de 1.0 * : en T-SQL,
      une division de deux entiers TRONQUE, et une conversion de 7,9 % devient
      0 %. Les colonnes sont peut-etre decimales aujourd'hui, elles peuvent
      cesser de l'etre demain.

   =============================================================================
   AUCUN RATIO N'EST PRE-AGREGE AU-DELA DU CAMPUS

   La conversion et le CA par inscrit sont calcules AU CAMPUS, apres somme des
   programmes. Ils ne se sommeront pas d'un campus a l'autre, et c'est normal :
   la ligne de marque du rapport est un SOUS-TOTAL DE LIGNES, pas une moyenne
   de taux. L'elasticite non plus ne se somme pas -- elle vit au campus, le
   moteur en a quatorze et pas cinq.

   =============================================================================
   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Exercices en dur comme le reste du modele. Pas de CTE, pas de ORDER BY,
   pas de ';'. Aucun parametre d'entite : c'est une requete de population, la
   matrice groupe sur MARQUE puis CAMPUS.
   ============================================================================= */
SELECT
    v.MARQUE                                                        AS "Marque",
    COALESCE(az.DESC_AZIENDA0, v.ENTITY)                            AS "Campus",

    SUM(CASE WHEN v.EXERCICE = 2024 THEN v.LEAD_PAY END)            AS "Leads payants 2024",
    SUM(CASE WHEN v.EXERCICE = 2025 THEN v.LEAD_PAY END)            AS "Leads payants 2025",
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.LEAD_PAY END)            AS "Leads payants 2026",

    SUM(CASE WHEN v.EXERCICE = 2024 THEN v.SPEND_ACQ END)           AS "Budget acquisition 2024",
    SUM(CASE WHEN v.EXERCICE = 2025 THEN v.SPEND_ACQ END)           AS "Budget acquisition 2025",
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.SPEND_ACQ END)           AS "Budget acquisition 2026",

    /* la pente des moindres carres sur les trois points, en log-log */
    ( COUNT(*) * SUM(LOG(v.LEAD_PAY) * LOG(v.SPEND_ACQ))
      - SUM(LOG(v.LEAD_PAY)) * SUM(LOG(v.SPEND_ACQ)) )
    / NULLIF( COUNT(*) * SUM(LOG(v.SPEND_ACQ) * LOG(v.SPEND_ACQ))
              - SUM(LOG(v.SPEND_ACQ)) * SUM(LOG(v.SPEND_ACQ)), 0 )  AS "Élasticité",

    1.0 * SUM(CASE WHEN v.EXERCICE = 2026 THEN v.INSCRITS END)
        / NULLIF(SUM(CASE WHEN v.EXERCICE = 2026 THEN v.LEAD_TOT END), 0)
                                                                    AS "Conversion 2026",
    1.0 * SUM(CASE WHEN v.EXERCICE = 2026 THEN v.CA_NEW END)
        / NULLIF(SUM(CASE WHEN v.EXERCICE = 2026 THEN v.INSCRITS END), 0)
                                                                    AS "CA par inscrit 2026",

    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.INSCRITS END)            AS "Nouveaux inscrits 2026",

    /* CONTROLE : doit valoir zero. S'il ne l'est pas, la source porte deux
       totaux de leads differents et la conversion des exercices passes est a
       verifier avant de s'en servir. */
    SUM(v.LEAD_TOT) - SUM(v.LEAD_BRUT)                              AS "Écart de leads (contrôle)"
FROM (
        SELECT  s.ENTITY,
                SUBSTR_BEFORE(s.ENTITY, '_')                AS MARQUE,
                CAST(s.EXERCICE AS INT)                     AS EXERCICE,
                SUM(s.VOL_LEAD_PAY)                         AS LEAD_PAY,
                SUM(s.VOL_LEAD_ORG) + SUM(s.VOL_LEAD_PAY)   AS LEAD_TOT,
                SUM(s.VOL_LEAD)                             AS LEAD_BRUT,
                SUM(s.DEPENSE_ACQ)                          AS SPEND_ACQ,
                SUM(s.VOL_NEW)                              AS INSCRITS,
                SUM(s.VOL_NEW * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) AS CA_NEW
        FROM    AW_002_000002_000001 AS s
        WHERE   CAST(s.EXERCICE AS INT) IN (2024, 2025, 2026)
        GROUP BY s.ENTITY, SUBSTR_BEFORE(s.ENTITY, '_'), CAST(s.EXERCICE AS INT)
        HAVING  SUM(s.VOL_LEAD_PAY) > 0 AND SUM(s.DEPENSE_ACQ) > 0
     ) AS v
LEFT JOIN azienda AS az
       ON  az.COD_AZIENDA = v.ENTITY
GROUP BY v.MARQUE, COALESCE(az.DESC_AZIENDA0, v.ENTITY)
