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
--
-- 2 subtilités indispensables :
--   1) SIGNE. La compta (AW_002_000004_000001) stocke TOUT en positif ; c'est
--      le FST qui applique les signes. Un SUM(AMOUNT) nu sur l'EBITDA renvoie
--      produits+charges (~41,8 M) au lieu du vrai EBITDA (3,29 M). On rétablit
--      le signe : comptes 7% = produit (+), le reste = charge (-).
--   2) LIBELLÉS. Jointures descriptives : conto (compte), azienda (entité),
--      ED_EXERCICE (exercice). Pas de libellé période (non demandé).
-- =============================================================================
SELECT d.ACCOUNT              AS "Compte",
       c.DESC_CONTO0          AS "Libellé compte",
       d.ENTITY               AS "Entité",
       a.DESC_AZIENDA0        AS "Libellé entité",
       d.EXERCICE             AS "Exercice",
       e.DESC0                AS "Libellé exercice",
       d.PERIOD               AS "Période",
       CASE WHEN d.ACCOUNT LIKE '7%' THEN d.AMOUNT ELSE -d.AMOUNT END AS "Montant"
FROM  AW_002_000004_000001 d
LEFT JOIN conto        c ON c.COD_CONTO   = d.ACCOUNT
LEFT JOIN azienda      a ON a.COD_AZIENDA = d.ENTITY
LEFT JOIN ED_EXERCICE  e ON e.COD         = d.EXERCICE
WHERE d.ENTITY   IN (${$Entity.code})
  AND d.EXERCICE IN (${$ANL_EXERCICE.code})
  AND d.ACCOUNT  IN (${$Account.code})
UNION ALL
SELECT 'Total','','','','','','',
       SUM(CASE WHEN ACCOUNT LIKE '7%' THEN AMOUNT ELSE -AMOUNT END)
FROM  AW_002_000004_000001
WHERE ENTITY   IN (${$Entity.code})
  AND EXERCICE IN (${$ANL_EXERCICE.code})
  AND ACCOUNT  IN (${$Account.code});


-- =============================================================================
-- DRILL 2 — COMMERCIAL : Leads, Inscrits, Dépenses acq -> détail funnel par classe
-- Source socle. Filtré par Entity + Exercice (le compte STA_* n'est pas requis :
-- on montre tout le funnel à la maille fine).
-- =============================================================================
-- Libellés dispo côté CRM : azienda (campus), ED_EXERCICE (exercice).
-- Programme / Année / Modalité restent en code (leurs tables de dim ne sont
-- pas encore câblées ; il suffira d'ajouter les LEFT JOIN quand tu me les donnes).
SELECT d.ENTITY   AS "Campus",   a.DESC_AZIENDA0 AS "Libellé campus",
       d.EXERCICE AS "Exercice", e.DESC0         AS "Libellé exercice",
       d.PROGRAMME AS "Programme", d.AN_ETUDE AS "Année", d.MODALITE AS "Modalité",
       SUM(d.VOL_LEAD)  AS "Leads",
       SUM(d.VOL_CAND)  AS "Candidatures",
       SUM(d.VOL_ADMIS) AS "Admis",
       SUM(d.VOL_NEW)   AS "Inscrits",
       SUM(d.VOL_EFF)   AS "Effectif",
       SUM(d.DEPENSE_ACQ) AS "Dépense acq."
FROM  AW_002_000002_000001 d
LEFT JOIN azienda     a ON a.COD_AZIENDA = d.ENTITY
LEFT JOIN ED_EXERCICE e ON e.COD         = d.EXERCICE
WHERE d.ENTITY   IN (${$Entity.code})
  AND d.EXERCICE IN (${$ANL_EXERCICE.code})
GROUP BY d.ENTITY, a.DESC_AZIENDA0, d.EXERCICE, e.DESC0, d.PROGRAMME, d.AN_ETUDE, d.MODALITE
ORDER BY d.PROGRAMME, d.AN_ETUDE, d.MODALITE;


-- =============================================================================
-- CÂBLAGE
--   Chiffre d'affaires · EBITDA (et blocs de charges)   -> DRILL 1 (Finance)
--   Leads · Inscrits · Dépenses acquisition             -> DRILL 2 (Commercial)
--   (CAC, Marge = membres calculés : on drille leurs composants, pas le ratio)
-- Astuce clé : sur un item FST, toujours ACCOUNT IN (${$Account.code}).
-- =============================================================================
