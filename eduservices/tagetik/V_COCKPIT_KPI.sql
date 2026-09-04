-- =============================================================================
-- V_COCKPIT_KPI — le bandeau de tuiles du cockpit, une LIGNE par tuile.
--
-- Pourquoi une ligne par tuile plutot qu'une ligne large de 12 colonnes :
--   . chaque tuile pointe UNE cellule -> le masque Excel reste trivial
--   . ajouter un 7e KPI = une ligne de plus, aucune colonne a recabler
--   . la vue porte l'UNITE et le SENS, donc le format et la couleur se
--     pilotent par la donnee au lieu d'etre codes en dur dans la feuille
--
-- COLONNES
--   ORDRE            position de la tuile dans le bandeau
--   CODE             cle stable (utiliser pour les RECHERCHE, pas le libelle)
--   LIBELLE          intitule affiche
--   VALEUR           la valeur de la tuile
--   UNITE            MEUR | PCT | EUR | NB   -> quel format appliquer
--   VARIATION        l'ecart vs l'exercice precedent
--   TYPE_VARIATION   PCT (variation relative) | PT (points de marge)
--   SENS_FAVORABLE   +1 : une hausse est une bonne nouvelle
--                    -1 : une hausse est une mauvaise nouvelle (le CAC)
--   INFO             complement affiche sous la tuile (peut etre vide)
--
-- Le SENS_FAVORABLE est la colonne qui evite l'exception codee en dur :
-- la mise en forme conditionnelle teste VARIATION * SENS_FAVORABLE > 0,
-- et le CAC devient rouge a la hausse sans aucun cas particulier.
--
-- GRAIN : SCENARIO x VERSION x PERIODE x EXERCICE (niveau groupe).
-- Pour le meme bandeau par marque ou par campus : ajouter MARQUE (ou ENTITY)
-- au GROUP BY de "base", aux jointures de "duo", et au SELECT final.
-- =============================================================================
CREATE OR REPLACE VIEW V_COCKPIT_KPI AS
WITH base AS (
    SELECT
        c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE,
        SUM(c.CA)                                        AS CA,
        SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE)        AS EBITDA,   -- avant siege
        SUM(c.VOL_EFF)                                   AS EFF,
        SUM(c.PLACES)                                    AS PLACES,
        SUM(c.VOL_NEW)                                   AS INSCRITS
    FROM V_CAMPUS_CLASSE c
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE
),
acq AS (
    SELECT m.SCENARIO, m.PERIODE, m.EXERCICE, SUM(m.SPEND_ACQ) AS SPEND
    FROM V_MOTEUR_CAL m
    GROUP BY m.SCENARIO, m.PERIODE, m.EXERCICE
),
k AS (
    SELECT b.*, COALESCE(a.SPEND, 0) AS SPEND
    FROM base b
    LEFT JOIN acq a
      ON a.SCENARIO = b.SCENARIO AND a.PERIODE = b.PERIODE AND a.EXERCICE = b.EXERCICE
),
duo AS (                       -- l'exercice et son precedent, cote a cote
    SELECT
        n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE,
        n.CA, n.EBITDA, n.EFF, n.PLACES, n.INSCRITS, n.SPEND,
        p.CA       AS CA_P,     p.EBITDA AS EBITDA_P, p.EFF   AS EFF_P,
        p.PLACES   AS PLACES_P, p.INSCRITS AS INSCRITS_P, p.SPEND AS SPEND_P
    FROM k n
    LEFT JOIN k p
      ON  p.SCENARIO = n.SCENARIO
      AND p.VERSION  = n.VERSION
      AND p.PERIODE  = n.PERIODE
      AND p.EXERCICE = TO_VARCHAR(TO_INT(n.EXERCICE) - 1)
)
SELECT SCENARIO, VERSION, PERIODE, EXERCICE,
       1 AS ORDRE, 'CA' AS CODE, 'Chiffre d''affaires' AS LIBELLE,
       CA AS VALEUR, 'MEUR' AS UNITE,
       CA / NULLIF(CA_P, 0) - 1 AS VARIATION, 'PCT' AS TYPE_VARIATION,
       1 AS SENS_FAVORABLE, '' AS INFO
FROM duo
UNION ALL
SELECT SCENARIO, VERSION, PERIODE, EXERCICE,
       2, 'EBITDA', 'EBITDA',
       EBITDA, 'MEUR',
       EBITDA / NULLIF(EBITDA_P, 0) - 1, 'PCT',
       1, ''
FROM duo
UNION ALL
SELECT SCENARIO, VERSION, PERIODE, EXERCICE,
       3, 'MARGE', 'Marge EBITDA',
       EBITDA / NULLIF(CA, 0), 'PCT',
       (EBITDA / NULLIF(CA, 0) - EBITDA_P / NULLIF(CA_P, 0)) * 100, 'PT',
       1, 'vs ' || TO_VARCHAR(ROUND(100 * EBITDA_P / NULLIF(CA_P, 0), 1)) || ' %'
FROM duo
UNION ALL
SELECT SCENARIO, VERSION, PERIODE, EXERCICE,
       4, 'INSCRITS', 'Inscrits (nouveaux)',
       INSCRITS, 'NB',
       INSCRITS / NULLIF(INSCRITS_P, 0) - 1, 'PCT',
       1, TO_VARCHAR(INSCRITS - INSCRITS_P) || ' vs ' || TO_VARCHAR(TO_INT(EXERCICE) - 1)
FROM duo
UNION ALL
SELECT SCENARIO, VERSION, PERIODE, EXERCICE,
       5, 'CAC', 'Cout d''acquisition',
       SPEND / NULLIF(INSCRITS, 0), 'EUR',
       (SPEND / NULLIF(INSCRITS, 0)) / NULLIF(SPEND_P / NULLIF(INSCRITS_P, 0), 0) - 1, 'PCT',
       -1,                                        -- une hausse du CAC est defavorable
       'depense / inscrit'
FROM duo
UNION ALL
SELECT SCENARIO, VERSION, PERIODE, EXERCICE,
       6, 'REMPLISSAGE', 'Remplissage moyen',
       EFF / NULLIF(PLACES, 0), 'PCT',
       (EFF / NULLIF(PLACES, 0) - EFF_P / NULLIF(PLACES_P, 0)) * 100, 'PT',
       1, TO_VARCHAR(PLACES - EFF) || ' places libres'
FROM duo
;
