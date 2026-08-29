-- =============================================================================
-- DRILL-THROUGH paramétrés du COCKPIT (style Tagetik ${$Dim.code})
-- Paramètres = coordonnées de la cellule cliquée.
--   Entity  -> ${$Entity.code}           (standard)
--   Account -> ${$Account.code} / ${$Account(HIERARCHY("$")).code}  (item FST)
--   Exercice-> ${$ANL_EXERCICE.code}      (dimension analytique)
--   Période -> ${$Period.code}
--   (Programme ${$ANL_PROGRAMME.code}, Cycle ${$ANL_ANNEE_ETUDES_010.code}, Modalité ${$ANL_MODALITE.code})
-- =============================================================================


-- =============================================================================
-- DRILL 1 — FINANCE : CA, EBITDA (items FST) ET Dépenses acq / comptes directs.
-- Résout l'item FST -> comptes via VOCE_CONTO_ABBI ; sinon prend le compte direct.
-- Cible : CA · EBITDA · Dépenses acquisition.
-- =============================================================================
SELECT
    ENTITY                                   AS "Entité",
    ACCOUNT                                  AS "Compte",
    EXERCICE                                 AS "Exercice",
    PERIOD                                   AS "Période",
    AMOUNT                                   AS "Montant"
FROM  AW_002_000004_000001
WHERE ENTITY   = ${$Entity.code}
  AND EXERCICE = ${$ANL_EXERCICE.code}
  AND ACCOUNT IN (
        SELECT COD_CONTO FROM VOCE_CONTO_ABBI                              -- cas item FST (CA, EBITDA)
          WHERE COD_SCHEMA || '||' || COD_VOCE = ${$Account(HIERARCHY("$")).code}
        UNION
        SELECT ${$Account.code} FROM DUMMY WHERE ${$Account.code} <> ''    -- cas compte direct (6231)
      )
UNION ALL
SELECT 'Total', '', '', '', SUM(AMOUNT)
FROM  AW_002_000004_000001
WHERE ENTITY   = ${$Entity.code}
  AND EXERCICE = ${$ANL_EXERCICE.code}
  AND ACCOUNT IN (
        SELECT COD_CONTO FROM VOCE_CONTO_ABBI
          WHERE COD_SCHEMA || '||' || COD_VOCE = ${$Account(HIERARCHY("$")).code}
        UNION
        SELECT ${$Account.code} FROM DUMMY WHERE ${$Account.code} <> ''
      );


-- =============================================================================
-- DRILL 2 — COMMERCIAL : Leads, Inscrits (comptes STA_*, directs) -> détail socle.
-- Montre le funnel complet par classe (programme × année × modalité).
-- =============================================================================
SELECT
    ENTITY                                   AS "Campus",
    PROGRAMME                                AS "Programme",
    AN_ETUDE                                 AS "Année",
    MODALITE                                 AS "Modalité",
    SUM(VOL_LEAD)                            AS "Leads",
    SUM(VOL_CAND)                            AS "Candidatures",
    SUM(VOL_ADMIS)                           AS "Admis",
    SUM(VOL_NEW)                             AS "Inscrits",
    SUM(VOL_EFF)                             AS "Effectif",
    SUM(DEPENSE_ACQ)                         AS "Dépense acq."
FROM  AW_002_000002_000001
WHERE ENTITY   = ${$Entity.code}
  AND EXERCICE = ${$ANL_EXERCICE.code}
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE
ORDER BY PROGRAMME, AN_ETUDE, MODALITE;


-- =============================================================================
-- CÂBLAGE
--   Chiffre d'affaires · EBITDA · Dépenses acquisition   -> DRILL 1
--   Leads · Inscrits                                      -> DRILL 2
--   (CAC, Marge = membres calculés : on drille leurs composants, pas le ratio)
-- =============================================================================
