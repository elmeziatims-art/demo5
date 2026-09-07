/* =============================================================================
   V_MOTEUR_CAL  —  la vue de calibration du moteur d'acquisition.
   UNE LIGNE PAR CAMPUS. Elle restitue, le masque calcule.

   Elle alimente le bloc ①  « Calibration & effet d'un +Delta% », et elle est
   construite pour qu'on puisse BOUGER LE BUDGET D'ACQUISITION SANS LA
   RELANCER : le Delta est une saisie du masque, donc rien de ce qui en depend
   n'est ici.

   =============================================================================
   LA REGLE, ET ELLE EST STRICTE : AUCUN RAPPORT N'EST PRE-CALCULE

   Chaque taux de la feuille est expose sous forme de NUMERATEUR ET
   DENOMINATEUR, jamais sous forme de rapport. C'est ce qui fait qu'une ligne
   de marque ou de groupe reste juste : le masque somme les deux, puis divise.

       conversion         INSCRITS_N        /  LEAD_TOT_N
       CA par inscrit     CA_NEW_N          /  INSCRITS_N
       conso par eleve    COUT_CONSO_N      /  EFFECTIFS_N
       vacataire/classe   COUT_VACAT_N      /  CLASSES_N
       capacite moyenne   PLACES_N          /  CLASSES_N
       places libres      PLACES_N          -  EFFECTIFS_N

   C'etait le defaut du classeur : la conversion des lignes de marque et de
   groupe y etait ECRITE EN DUR. Sur le groupe, la moyenne des taux se trompait
   de 0,25 point contre la vraie somme sur somme -- elle donnait le meme poids
   a Tunon Lyon, 117 eleves, qu'a MBway Paris, 382.

   =============================================================================
   LA SEULE COLONNE QUI NE SE SOMME PAS : ELASTICITE

   Elle est calculee ici parce qu'elle ne peut pas l'etre ailleurs : c'est une
   REGRESSION sur trois points, et une regression des moindres carres est une
   agregation -- elle s'ecrit avec des SUM.

       pente = ( n·Σxy − Σx·Σy ) / ( n·Σx² − (Σx)² )
       x = LN(budget acquisition)   y = LN(leads payants)

   En T-SQL, LOG() est le logarithme neperien. Verifie identique a SLOPE
   d'Excel au dix-millieme sur les quatorze campus.

   ELLE VIT AU CAMPUS ET NE REMONTE PAS. Sur le groupe, les trois facons de
   l'agreger donnent trois nombres differents :

       regression sur les series agregees   0,4937
       moyenne simple des quatorze          0,5031
       moyenne ponderee par le budget       0,4881

   Le masque doit donc afficher un tiret sur les lignes de noeud, comme il le
   fait deja. Si l'on veut vraiment une elasticite de groupe, c'est la premiere
   des trois -- refaire la regression sur les series sommees -- et c'est une
   autre requete.

   =============================================================================
   LE COUT VARIABLE : PROJETE, ET NON PLUS SUPPOSE

   Le classeur portait « 300 EUR / eleve » sans source. Le chiffre visait juste
   -- le vrai est 363 -- mais il ne se defendait pas.

   La vue rend de quoi le calculer, et surtout de quoi le faire BASCULER TOUT
   SEUL selon le remplissage, ce qui est le coeur du sujet :

       tant qu'il reste des places   363 EUR/eleve   les consommables seuls
                                                     (604 achats d'etudes
                                                      + 6063 fournitures)
       s'il faut ouvrir une classe   750 EUR/eleve   + la quote-part du
                                                     vacataire de la classe
                                                     neuve (621 / classes,
                                                     rapporte a 30,3 places)

   Groupe 2026 : 135 classes, 4 088 places, 3 114 eleves, donc 974 PLACES
   LIBRES pour un remplissage de 76,2 %. Le geste a +8 % gagne 27 inscrits :
   ils tiennent tous dans les sieges libres, le vacataire est deja paye, le
   cout marginal est donc bien celui des consommables.

   LE COMPTE 6231 N'EST JAMAIS DANS CE COUT. C'est le budget d'acquisition, et
   il est deja soustrait comme « Delta budget ». L'inclure le compterait deux
   fois.

   =============================================================================
   ET LES ENSEIGNANTS PERMANENTS ?

   Ils sont dans la vue -- COUT_PERM_N, compte 6411, 3 841 070 EUR en 2026 --
   et ils sont alloues a l'HEURE, exactement comme les vacataires. Ils pesent
   meme 58,6 % du cout d'enseignement du reseau. Et pourtant ils ne sont pas
   dans le cout marginal, pour une raison qui n'a rien d'un oubli :

       un poste permanent est un ENGAGEMENT DE CAPACITE. Il est paye pareil
       que la salle contienne 24 ou 32 etudiants. Il ne varie pas avec
       l'eleve, il varie avec le NOMBRE DE POSTES -- c'est-a-dire par palier,
       et le palier suivant n'est pas une classe, c'est un campus.

   Le vacataire est la seule ressource enseignante que l'on achete a la
   classe : c'est pour cela qu'il est le seul a entrer dans le cout marginal,
   et seulement quand une classe doit ouvrir. Accessoirement, le 621 est du
   PERSONNEL EXTERIEUR : une facture, donc sans charges sociales 645 en plus,
   contrairement au 6411.

   Sur 20,6 MEUR de charges, 1,13 MEUR seulement -- 5,5 % -- bougent quand un
   eleve de plus s'assoit. Tout le reste est de la capacite deja engagee, et
   c'est precisement ce qui rend le geste d'acquisition aussi rentable tant
   qu'il reste des places.

   =============================================================================
   ET NON, ON NE S'ARRETE PAS AU CA

   Un DAF n'arbitre pas sur du chiffre d'affaires. « +205 651 EUR de CA » sans
   le cout en face est exactement le genre de nombre qui fait rejeter un
   modele. Maintenant que le cout se calcule au lieu de se supposer, la chaine
   peut aller jusqu'a l'EBITDA, qui est la seule grandeur sur laquelle on
   decide.
   ============================================================================= */
CREATE OR ALTER VIEW V_MOTEUR_CAL AS
SELECT
    v.ENTITY,
    v.MARQUE,
    COALESCE(az.DESC_AZIENDA0, v.ENTITY)                            AS CAMPUS,

    /* ---- les series de calibration, trois exercices ---------------------- */
    SUM(CASE WHEN v.EXERCICE = 2024 THEN v.LEAD_PAY  END)           AS LEAD_PAY_2024,
    SUM(CASE WHEN v.EXERCICE = 2025 THEN v.LEAD_PAY  END)           AS LEAD_PAY_2025,
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.LEAD_PAY  END)           AS LEAD_PAY_2026,
    SUM(CASE WHEN v.EXERCICE = 2024 THEN v.SPEND_ACQ END)           AS SPEND_ACQ_2024,
    SUM(CASE WHEN v.EXERCICE = 2025 THEN v.SPEND_ACQ END)           AS SPEND_ACQ_2025,
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.SPEND_ACQ END)           AS SPEND_ACQ_2026,

    /* ---- la pente log-log, seule colonne non additive -------------------- */
    ( COUNT(*) * SUM(LOG(v.LEAD_PAY) * LOG(v.SPEND_ACQ))
      - SUM(LOG(v.LEAD_PAY)) * SUM(LOG(v.SPEND_ACQ)) )
    / NULLIF( COUNT(*) * SUM(LOG(v.SPEND_ACQ) * LOG(v.SPEND_ACQ))
              - SUM(LOG(v.SPEND_ACQ)) * SUM(LOG(v.SPEND_ACQ)), 0 )  AS ELASTICITE,

    /* ---- de quoi calculer la conversion et le CA par inscrit ------------- */
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.LEAD_TOT  END)           AS LEAD_TOT_N,
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.INSCRITS  END)           AS INSCRITS_N,
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.CA_NEW    END)           AS CA_NEW_N,

    /* ---- de quoi calculer le remplissage et le cout marginal ------------- */
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.EFFECTIFS END)           AS EFFECTIFS_N,
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.PLACES    END)           AS PLACES_N,
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.CLASSES   END)           AS CLASSES_N,
    SUM(CASE WHEN v.EXERCICE = 2026 THEN v.HEURES    END)           AS HEURES_N,
    MAX(k.COUT_CONSO)                                               AS COUT_CONSO_N,
    MAX(k.COUT_VACAT)                                               AS COUT_VACAT_N,
    MAX(k.COUT_PERM)                                                AS COUT_PERM_N,

    /* ---- controle : doit valoir zero ------------------------------------- */
    SUM(v.LEAD_TOT) - SUM(v.LEAD_BRUT)                              AS ECART_LEADS
FROM (
        SELECT  s.ENTITY,
                LEFT(s.ENTITY, CHARINDEX('_', s.ENTITY + '_') - 1)  AS MARQUE,
                CAST(s.EXERCICE AS INT)                             AS EXERCICE,
                SUM(s.VOL_LEAD_PAY)                                 AS LEAD_PAY,
                SUM(s.VOL_LEAD_ORG) + SUM(s.VOL_LEAD_PAY)           AS LEAD_TOT,
                SUM(s.VOL_LEAD)                                     AS LEAD_BRUT,
                SUM(s.DEPENSE_ACQ)                                  AS SPEND_ACQ,
                SUM(s.VOL_NEW)                                      AS INSCRITS,
                SUM(s.VOL_EFF)                                      AS EFFECTIFS,
                SUM(s.VOL_CLASS)                                    AS CLASSES,
                SUM(s.VOL_CLASS * CASE WHEN s.PROGRAMME LIKE 'BAC%' THEN 32
                                       WHEN s.PROGRAMME LIKE 'MAS%' THEN 26
                                       ELSE 30 END)                 AS PLACES,
                /* les heures d'enseignement : c'est la cle d'allocation du 621 et du
                   6411, et le denominateur du tarif horaire. Meme maquette pedagogique
                   que le classeur, onglet « Integration & controles ». */
                SUM(s.VOL_CLASS * CASE WHEN s.PROGRAMME LIKE 'BAC%' AND s.MODALITE = 'INIT' THEN 600
                                       WHEN s.PROGRAMME LIKE 'BAC%'                         THEN 480
                                       WHEN s.PROGRAMME LIKE 'MAS%' AND s.MODALITE = 'INIT' THEN 520
                                       WHEN s.PROGRAMME LIKE 'MAS%'                         THEN 420
                                       WHEN s.MODALITE = 'INIT'                             THEN 1000
                                       ELSE 700 END)                AS HEURES,
                SUM(s.VOL_NEW * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) AS CA_NEW
        FROM    AW_002_000002_000001 AS s
        WHERE   CAST(s.EXERCICE AS INT) IN (2024, 2025, 2026)
        GROUP BY s.ENTITY, LEFT(s.ENTITY, CHARINDEX('_', s.ENTITY + '_') - 1),
                 CAST(s.EXERCICE AS INT)
        HAVING  SUM(s.VOL_LEAD_PAY) > 0 AND SUM(s.DEPENSE_ACQ) > 0
     ) AS v
LEFT JOIN azienda AS az
       ON  az.COD_AZIENDA = v.ENTITY
LEFT JOIN (
        /* Les deux poches de cout variable, separees parce qu'elles ne se
           comportent pas pareil : les consommables suivent l'ELEVE, le
           vacataire suit la CLASSE. Le compte 6231 est volontairement absent :
           c'est le budget d'acquisition, deja soustrait comme Delta budget. */
        SELECT  d.ENTITY,
                SUM(CASE WHEN d.ACCOUNT IN ('604', '6063') THEN d.AMOUNT ELSE 0 END) AS COUT_CONSO,
                SUM(CASE WHEN d.ACCOUNT = '621'            THEN d.AMOUNT ELSE 0 END) AS COUT_VACAT,
                SUM(CASE WHEN d.ACCOUNT = '6411'           THEN d.AMOUNT ELSE 0 END) AS COUT_PERM
        FROM    AW_002_000004_000001 AS d
        WHERE   CAST(d.EXERCICE AS INT) = 2026
        GROUP BY d.ENTITY
     ) AS k
       ON  k.ENTITY = v.ENTITY
GROUP BY v.ENTITY, v.MARQUE, COALESCE(az.DESC_AZIENDA0, v.ENTITY);
