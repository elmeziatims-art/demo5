-- =============================================================================
-- Q_BRIDGE_RECONCILIATION_CA — LE PONT qui explique l'écart CRM vs Compta
-- =============================================================================
-- Cible du hyperlink sur la cellule « Écart » du bandeau réconciliation.
-- Décompose l'écart CA CRM (contractuel) -> CA Compta (reconnu) et le NOMME.
--
-- Fait vérifié sur données réelles : l'écart est à ~100 % sur la SCOLARITÉ
-- (comptes 706+7062) ; les frais d'inscription (708) tiennent au centime.
-- La raison = RATTACHEMENT de la scolarité à l'exercice :
--   le CRM compte la scolarité contractuelle pleine sur l'année d'inscription ;
--   la compta ne reconnaît que la quote-part courue (année académique sept->août),
--   le reste est différé en PRODUITS CONSTATÉS D'AVANCE (compte 487).
--   Écart = variation des PCA -> change de signe et s'annule (0 en 2026).
--
-- 2024 : rattachement -12 297 | 2025 : +28 428 | 2026 : 0
-- =============================================================================
SELECT
    crm.EXERCICE                                   AS "Exercice",
    crm.CA_CRM                                      AS "CA CRM (contractuel)",
    cpt.CA_CPT_SCOL - crm.CA_CRM_SCOL               AS "Rattachement scolarité (Δ PCA, cpte 487)",
    cpt.CA_CPT_FRAIS - crm.CA_CRM_FRAIS             AS "Divers frais d'inscription (708)",
    cpt.CA_CPT                                      AS "CA Compta (reconnu)",
    cpt.CA_CPT - crm.CA_CRM                         AS "Écart total"
FROM (
        SELECT EXERCICE,
               SUM(VOL_EFF * REV_STUD)                          AS CA_CRM_SCOL,
               SUM(VOL_NEW * REV_FRAIS_INS)                     AS CA_CRM_FRAIS,
               SUM(VOL_EFF * REV_STUD + VOL_NEW * REV_FRAIS_INS) AS CA_CRM
        FROM AW_002_000002_000001
        GROUP BY EXERCICE
     ) crm
INNER JOIN (
        SELECT EXERCICE,
               SUM(CASE WHEN ACCOUNT IN ('706','7062') THEN AMOUNT ELSE 0 END) AS CA_CPT_SCOL,
               SUM(CASE WHEN ACCOUNT = '708'           THEN AMOUNT ELSE 0 END) AS CA_CPT_FRAIS,
               SUM(AMOUNT)                                                     AS CA_CPT
        FROM AW_002_000004_000001
        WHERE ACCOUNT IN ('706','7062','708')
        GROUP BY EXERCICE
     ) cpt
     ON cpt.EXERCICE = crm.EXERCICE
ORDER BY crm.EXERCICE;

-- Variante DRILL par marque/campus : ajouter ENTITY aux deux sous-requêtes et à
-- la jointure. On voit alors QUELS campus portent le rattachement (les plus en
-- croissance d'effectifs -> plus de scolarité différée).
