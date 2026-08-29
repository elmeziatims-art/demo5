-- =============================================================================
-- DRILL-THROUGH du COCKPIT (style Tagetik) — VERSION QUI MARCHE
-- =============================================================================
-- Clé : ${$Account.code} sur un item FST renvoie la LISTE des comptes ->
--       on l'entoure de IN ( ... ). Idem pour les autres dimensions.
-- Paramètres : Entity, Account (item FST), Exercice = ${$ANL_EXERCICE.code}.
-- =============================================================================


-- =============================================================================
-- DRILL 1 — FINANCE : CA, EBITDA, blocs de charges -> détail compta
-- Marche pour tous les items FST (le IN(...) reçoit leurs comptes).
-- =============================================================================
SELECT ACCOUNT AS "Compte", ENTITY AS "Entité", EXERCICE AS "Exercice",
       PERIOD AS "Période", AMOUNT AS "Montant"
FROM  AW_002_000004_000001
WHERE ENTITY   IN (${$Entity.code})
  AND EXERCICE IN (${$ANL_EXERCICE.code})
  AND ACCOUNT  IN (${$Account.code})
UNION ALL
SELECT 'Total','','','', SUM(AMOUNT)
FROM  AW_002_000004_000001
WHERE ENTITY   IN (${$Entity.code})
  AND EXERCICE IN (${$ANL_EXERCICE.code})
  AND ACCOUNT  IN (${$Account.code});


-- =============================================================================
-- DRILL 2 — COMMERCIAL : Leads, Inscrits, Dépenses acq -> détail funnel par classe
-- Source socle. Filtré par Entity + Exercice (le compte STA_* n'est pas requis :
-- on montre tout le funnel à la maille fine).
-- =============================================================================
SELECT ENTITY AS "Campus", PROGRAMME AS "Programme", AN_ETUDE AS "Année", MODALITE AS "Modalité",
       SUM(VOL_LEAD)  AS "Leads",
       SUM(VOL_CAND)  AS "Candidatures",
       SUM(VOL_ADMIS) AS "Admis",
       SUM(VOL_NEW)   AS "Inscrits",
       SUM(VOL_EFF)   AS "Effectif",
       SUM(DEPENSE_ACQ) AS "Dépense acq."
FROM  AW_002_000002_000001
WHERE ENTITY   IN (${$Entity.code})
  AND EXERCICE IN (${$ANL_EXERCICE.code})
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE
ORDER BY PROGRAMME, AN_ETUDE, MODALITE;


-- =============================================================================
-- CÂBLAGE
--   Chiffre d'affaires · EBITDA (et blocs de charges)   -> DRILL 1 (Finance)
--   Leads · Inscrits · Dépenses acquisition             -> DRILL 2 (Commercial)
--   (CAC, Marge = membres calculés : on drille leurs composants, pas le ratio)
-- Astuce clé : sur un item FST, toujours ACCOUNT IN (${$Account.code}).
-- =============================================================================
