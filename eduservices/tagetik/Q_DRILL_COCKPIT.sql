-- =============================================================================
-- DRILL-THROUGH paramétrés du COCKPIT (style Tagetik ${$Dim.code})
-- Les ${$...} sont remplacés par les coordonnées de la cellule cliquée.
-- Adapte les NOMS de paramètres au nom technique de tes dimensions
-- (Entity, Account, Exercice, Period, Programme...).
-- =============================================================================


-- =============================================================================
-- DRILL A — cellule FINANCE (CA, EBITDA, un compte...) -> détail compta
-- Source : AW_002_000004_000001. Filtré par le POV de la cellule.
-- NB : si on clique un NŒUD (CA = Produits, EBITDA...), ${$Account.code} vaut le
--      nœud -> soit Tagetik passe les comptes feuilles, soit remplacer la ligne
--      "AND ACCOUNT = ${$Account.code}" par "AND ACCOUNT IN (706,7062,708)" etc.
-- =============================================================================
SELECT
    ENTITY                                   AS "Entité",
    ACCOUNT                                  AS "Compte",
    EXERCICE                                 AS "Exercice",
    PERIOD                                   AS "Période",
    AMOUNT                                   AS "Montant"
FROM  AW_002_000004_000001
WHERE ENTITY   = ${$Entity.code}
  AND ACCOUNT  = ${$Account.code}
  AND EXERCICE = ${$Exercice.code}
UNION ALL
SELECT 'Total', '', '', '', SUM(AMOUNT)
FROM  AW_002_000004_000001
WHERE ENTITY   = ${$Entity.code}
  AND ACCOUNT  = ${$Account.code}
  AND EXERCICE = ${$Exercice.code};


-- =============================================================================
-- DRILL B — cellule COMMERCIALE (Leads, Inscrits, CAC...) -> détail par classe
-- Source : AW_002_000002_000001 (socle). Filtré par le POV (Entity, Exercice).
-- Montre le funnel complet à la maille fine (programme × année × modalité).
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
  AND EXERCICE = ${$Exercice.code}
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE
ORDER BY PROGRAMME, AN_ETUDE, MODALITE;


-- =============================================================================
-- VARIANTE — détail transactionnel (écritures/factures) via map_dati_trasformati
-- Si tu veux le VRAI transactionnel (comme ton exemple invoice-level), le drill
-- vise la table d'import brute. Il faut le mapping des champs de TON import :
--   cod_mappatura / cod_import de l'import compta EDUSERVICES, et quel campoN =
--   Entity / Account / Exercice / Period / Montant.
-- Squelette (à compléter avec ton mapping) :
--
-- SELECT campo4 AS "Compte", campo5 AS "Libellé", campo9 AS "Pièce",
--        CAST(REPLACE(campo12,',','.') AS NUMERIC(20,2)) AS "Montant"
-- FROM   map_dati_trasformati
-- WHERE  cod_mappatura = '<xx>' AND cod_import = '<xxx>'
--   AND  campo3  = ${$Entity.code}
--   AND  campo15 = ${$Account.code}
--   AND  campo1  = ${$Exercice.code}
--   AND  campo2  = ${$Period.code}
-- ...
-- =============================================================================
