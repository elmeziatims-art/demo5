-- =============================================================================
-- Q_RECONCILIATION_CA — CA CRM  À CÔTÉ DE  CA Compta  (une seule query, pas une vue)
-- =============================================================================
-- Le héros du cockpit : deux sources chargées séparément, un même total.
--   CA CRM    = socle,   Σ (effectifs × frais scolarité + nouveaux × frais inscription)
--   CA Compta = grand livre, Σ comptes de produits 706 / 7062 / 708
-- Jointure des deux datasets Tagetik par exercice.
--
-- RÉCONCILIATION (vérifiée sur données réelles) :
--   2026 -> écart 0 € (au centime, groupe / marque / campus)  <= exercice de référence
--   2024 -> écart -12 135 € | 2025 -> écart +28 466 €  (léger, historique)
-- Pour le BANDEAU du cockpit : filtrer EXERCICE = '2026' (dernier exercice clos,
-- réconcilié au centime). Les 3 lignes servent au contrôle.
-- =============================================================================
SELECT
    crm.EXERCICE                                  AS "Exercice",
    crm.CA_CRM                                     AS "CA CRM (socle)",
    cpt.CA_COMPTA                                  AS "CA Compta (706/7062/708)",
    cpt.CA_COMPTA - crm.CA_CRM                     AS "Écart"
FROM (
        SELECT EXERCICE,
               SUM(VOL_EFF * REV_STUD + VOL_NEW * REV_FRAIS_INS) AS CA_CRM
        FROM AW_002_000002_000001
        GROUP BY EXERCICE
     ) crm
INNER JOIN (
        SELECT EXERCICE,
               SUM(AMOUNT) AS CA_COMPTA
        FROM AW_002_000004_000001
        WHERE ACCOUNT IN ('706', '7062', '708')
        GROUP BY EXERCICE
     ) cpt
     ON cpt.EXERCICE = crm.EXERCICE
ORDER BY crm.EXERCICE;

-- Variante DRILL (réconciliation par marque/campus) : ajouter ENTITY aux deux
-- sous-requêtes et à la jointure (ON ... AND cpt.ENTITY = crm.ENTITY), puis
-- SUBSTR_BEFORE(ENTITY,'_') pour la marque. En 2026, écart 0 à chaque campus.
