-- =============================================================================
-- V_RECONCILIATION — vue "en ligne" pour la MATRICE de réconciliation CRM ‖ Compta
-- =============================================================================
-- Forme normalisée (ENTITY, ACCOUNT, EXERCICE, AMOUNT) : UNE mesure, le compte
-- porte le sens. -> matrice Tagetik avec des COMPTES en colonnes.
--
-- Le CRM est envoyé sur des COMPTES TECHNIQUES (classe 9), miroirs des produits :
--   9706  = CRM · CA initiale        (miroir du 706)
--   97062 = CRM · CA alternance      (miroir du 7062)
--   9708  = CRM · CA frais inscript. (miroir du 708)
--   9EFF  = CRM · Effectif           (STATISTIQUE, non monétaire)
-- La compta réelle reste sur 706 / 7062 / 708.
--
-- Dans Tagetik :
--   - dimension Compte : créer 9706/97062/9708 (monétaires) + 9EFF (statistique),
--     sous un noeud "CRM" ; 706/7062/708 sous le noeud "Produits".
--   - matrice : lignes = Entity (marque→campus), colonnes = comptes.
--   - Écart = membres calculés (FST) :  706-9706, 7062-97062, 708-9708, total.
-- Alignement vérifié au centime en 2026 (14 campus) : 706=9706, 7062=97062, 708=9708.
-- =============================================================================
CREATE OR ALTER VIEW V_RECONCILIATION AS
-- ===== COMPTA réelle (produits) =====
SELECT ENTITY, ACCOUNT, EXERCICE, SUM(AMOUNT) AS AMOUNT
FROM AW_002_000004_000001
WHERE ACCOUNT IN ('706','7062','708')
GROUP BY ENTITY, ACCOUNT, EXERCICE

UNION ALL
-- ===== CRM · CA initiale -> compte technique 9706 =====
SELECT ENTITY, '9706' AS ACCOUNT, EXERCICE,
       SUM(CASE WHEN MODALITE = 'INIT' THEN VOL_EFF * REV_STUD ELSE 0 END) AS AMOUNT
FROM AW_002_000002_000001
GROUP BY ENTITY, EXERCICE

UNION ALL
-- ===== CRM · CA alternance -> compte technique 97062 =====
SELECT ENTITY, '97062' AS ACCOUNT, EXERCICE,
       SUM(CASE WHEN MODALITE = 'ALT' THEN VOL_EFF * REV_STUD ELSE 0 END) AS AMOUNT
FROM AW_002_000002_000001
GROUP BY ENTITY, EXERCICE

UNION ALL
-- ===== CRM · CA frais d'inscription -> compte technique 9708 =====
SELECT ENTITY, '9708' AS ACCOUNT, EXERCICE,
       SUM(VOL_NEW * REV_FRAIS_INS) AS AMOUNT
FROM AW_002_000002_000001
GROUP BY ENTITY, EXERCICE

UNION ALL
-- ===== CRM · Effectif (statistique) -> compte technique 9EFF =====
SELECT ENTITY, '9EFF' AS ACCOUNT, EXERCICE,
       SUM(VOL_EFF) AS AMOUNT
FROM AW_002_000002_000001
GROUP BY ENTITY, EXERCICE;
