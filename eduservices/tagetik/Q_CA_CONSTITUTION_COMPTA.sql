-- =============================================================================
-- Q_CA_CONSTITUTION_COMPTA — DRILL-THROUGH de la tuile CA (côté COMPTA · preuve)
-- =============================================================================
-- « Ce que dit le grand livre. » Le CA par comptes de produits, par entité.
-- Comptes retenus : 706 / 7062 / 708 (les seuls comptes 70x présents dans le
-- dataset — vérifié). Même total que Q_CA_CONSTITUTION_CRM (écart 0,00 €).
--
-- POV : Tagetik injecte le filtre de la cellule cliquée (Exercice, et Marque si
-- le drill part d'une ligne marque).
-- Source : AW_002_000004_000001 (compta · grand livre, réel).
--
-- NB libellés : à ajuster au plan comptable du client si besoin — le mapping
-- des comptes est le seul point à confirmer côté client.
-- =============================================================================
SELECT
    EXERCICE                                   AS "Exercice",
    SUBSTR_BEFORE(ENTITY, '_')                 AS "Marque",
    ENTITY                                     AS "Campus",
    ACCOUNT                                    AS "Compte",
    CASE ACCOUNT
        WHEN '706'  THEN 'Prestations de services (scolarité)'
        WHEN '7062' THEN 'Frais de scolarité'
        WHEN '708'  THEN 'Produits des activités annexes'
        ELSE 'Autre produit'
    END                                        AS "Libellé",
    SUM(AMOUNT)                                AS "Montant"
FROM AW_002_000004_000001
WHERE ACCOUNT IN ('706', '7062', '708')
GROUP BY EXERCICE, SUBSTR_BEFORE(ENTITY, '_'), ENTITY, ACCOUNT
ORDER BY "Marque", "Campus", "Compte";
