-- =============================================================================
-- COPIE_SCENARIO_SIMULATION — le bac à sable du simulateur ouverture / fermeture
--
-- CE QUE CE SCRIPT FAIT, EXACTEMENT. Il n'ouvre PAS un nouveau dataset : il
-- écrit dans LES MÊMES trois cubes (AW_002_000001, 000002 et 000004), avec une
-- autre valeur dans la colonne SCENARIO. C'est un MEMBRE DE SCÉNARIO de plus,
-- pas un conteneur de plus.
--
-- Et c'est voulu : les deux jeux cohabitent alors ligne à ligne dans les mêmes
-- tables, donc UNE SEULE requête lit le cadrage et la simulation ensemble. Le
-- rapport « cadrage vs campus » côte à côte est gratuit. Un vrai dataset séparé
-- (nouvelles tables AW) imposerait des UNION entre tables et un jeu de vues
-- dupliqué ; il ne se justifie que pour isoler les droits ou le calendrier de
-- saisie des campus.
--
-- PRÉREQUIS RÉFÉRENTIEL, à faire AVANT de lancer ce script : créer le membre
-- '2027SIM_CAMPUS' dans la dimension Scénario, et l'ouvrir en écriture aux
-- campus dans le workflow. Sans le membre, le contrôle référentiel rejette les
-- lignes ; sans les droits, les campus voient le scénario sans pouvoir saisir.
--
-- CE QUI SE SAISIT ENSUITE, ET RIEN D'AUTRE : VOL_CLASS, dans le socle
-- AW_002_000002_000001, sur les lignes EXERCICE = '2026' du scénario de
-- simulation. C'est cette structure de classes que V_ALLOCATION reprend pour
-- 2027 (« VOL_CLASS structurel, figé sur le socle 2026 »). Un seul champ.
--
-- PRÉREQUIS, déjà posé : V_MOTEUR, V_BUDGET et V_ALLOCATION portent désormais le
-- SCENARIO sur toutes leurs jointures, fenêtres et poches. Sans cela un second
-- scénario multipliait les lignes du moteur et fusionnait les dénominateurs
-- d'allocation — silencieusement, sans aucune erreur, et le contrôle
-- d'enveloppe serait resté juste.
--
-- Rejouable : le DELETE en tête permet de repartir du cadrage à tout moment.
-- =============================================================================

-- ---------------------------------------------------------------- paramètres
--  Adapter ces deux valeurs, elles ne servent qu'ici.
--    source = le cadrage figé          cible = le bac à sable des campus
-- =============================================================================

-- ============================ 1. on repart d'une ardoise propre ==============
DELETE FROM AW_002_000002_000001 WHERE SCENARIO = '2027SIM_CAMPUS';
DELETE FROM AW_002_000004_000001 WHERE SCENARIO = '2027SIM_CAMPUS';
DELETE FROM AW_002_000001_000001 WHERE SCENARIO = '2027SIM_CAMPUS';

-- ============================ 2. le socle (volumes, tarifs, marketing) =======
--  Tous les exercices, 2024 à 2026 : le moteur a besoin des trois années pour
--  recalculer les élasticités (régression log-log de V_CAMPAGNES).
INSERT INTO AW_002_000002_000001
 (OID, SCENARIO, PERIODE, ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE,
  VOL_LEAD, VOL_CAND, VOL_ADMIS, VOL_NEW, VOL_REINS, VOL_EFF, VOL_EFF_INF, VOL_CLASS,
  REV_STUD, REV_FRAIS_INS, VOL_LEAD_ORG, VOL_LEAD_PAY, DEPENSE_ACQ, DEPENSE_MARQUE,
  USERUPD, DATEUPD, PROVENIENZA)
SELECT BINTOHEX(SYSUUID), '2027SIM_CAMPUS', s.PERIODE, s.ENTITY, s.PROGRAMME,
       s.AN_ETUDE, s.MODALITE, s.EXERCICE,
       s.VOL_LEAD, s.VOL_CAND, s.VOL_ADMIS, s.VOL_NEW, s.VOL_REINS, s.VOL_EFF,
       s.VOL_EFF_INF, s.VOL_CLASS, s.REV_STUD, s.REV_FRAIS_INS,
       s.VOL_LEAD_ORG, s.VOL_LEAD_PAY, s.DEPENSE_ACQ, s.DEPENSE_MARQUE,
       'SIMUL', CURRENT_TIMESTAMP, 'QDL'
FROM AW_002_000002_000001 s
WHERE s.SCENARIO = '2027BUD_V1';

-- ============================ 3. la comptabilité 2026 ========================
--  V_BUDGET projette 2027 en partant de cette compta : sans elle le scénario de
--  simulation n'aurait ni charges ni EBITDA.
INSERT INTO AW_002_000004_000001
 (OID, ENTITY, ACCOUNT, EXERCICE, SCENARIO, PERIOD, AMOUNT,
  USERUPD, DATEUPD, PROVENIENZA)
SELECT BINTOHEX(SYSUUID), c.ENTITY, c.ACCOUNT, c.EXERCICE, '2027SIM_CAMPUS',
       c.PERIOD, c.AMOUNT, 'SIMUL', CURRENT_TIMESTAMP, 'QDL'
FROM AW_002_000004_000001 c
WHERE c.SCENARIO = '2027BUD_V1';

-- ============================ 4. les hypothèses ==============================
--  Leviers de cadrage, clés d'allocation, coefficients de prix par marque.
--  On les recopie telles quelles : la simulation part EXACTEMENT du cadrage,
--  la seule chose qui bougera est le nombre de groupes.
INSERT INTO AW_002_000001_000001
 (OID, SCENARIO, PERIODE, ENTITY, VERSION, PARAMETRE, MEASURE, KEY_ALLOC,
  USERUPD, DATEUPD, PROVENIENZA)
SELECT BINTOHEX(SYSUUID), '2027SIM_CAMPUS', h.PERIODE, h.ENTITY, h.VERSION,
       h.PARAMETRE, h.MEASURE, h.KEY_ALLOC, 'SIMUL', CURRENT_TIMESTAMP, h.PROVENIENZA
FROM AW_002_000001_000001 h
WHERE h.SCENARIO = '2027BUD_V1';

-- ============================ 5. le contrôle =================================
--  Les deux scénarios doivent rendre EXACTEMENT le même budget tant qu'aucun
--  groupe n'a bougé. Si une seule de ces lignes n'affiche pas 0, une jointure
--  a encore perdu le scénario en route.
SELECT 'socle'      AS CUBE, COUNT(*) AS ECART FROM (
    SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, VOL_EFF, VOL_CLASS
    FROM AW_002_000002_000001 WHERE SCENARIO = '2027BUD_V1'
    EXCEPT
    SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, VOL_EFF, VOL_CLASS
    FROM AW_002_000002_000001 WHERE SCENARIO = '2027SIM_CAMPUS') X
UNION ALL
SELECT 'lignes moteur', ABS(
    (SELECT COUNT(*) FROM V_MOTEUR WHERE SCENARIO = '2027BUD_V1')
  - (SELECT COUNT(*) FROM V_MOTEUR WHERE SCENARIO = '2027SIM_CAMPUS'))
UNION ALL
SELECT 'CA 2027 V01', CAST(ROUND(ABS(
    (SELECT SUM(CA) FROM V_MOTEUR WHERE SCENARIO = '2027BUD_V1'     AND VERSION = 'V01')
  - (SELECT SUM(CA) FROM V_MOTEUR WHERE SCENARIO = '2027SIM_CAMPUS' AND VERSION = 'V01')), 2) AS INT)
UNION ALL
SELECT 'marge complete 2027 V01', CAST(ROUND(ABS(
    (SELECT SUM(MARGE_COMPLETE) FROM V_ALLOCATION
      WHERE SCENARIO = '2027BUD_V1'     AND EXERCICE = '2027' AND VERSION = 'V01')
  - (SELECT SUM(MARGE_COMPLETE) FROM V_ALLOCATION
      WHERE SCENARIO = '2027SIM_CAMPUS' AND EXERCICE = '2027' AND VERSION = 'V01')), 2) AS INT);
