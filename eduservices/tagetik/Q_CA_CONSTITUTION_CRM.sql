-- =============================================================================
-- Q_CA_CONSTITUTION_CRM — DRILL-THROUGH de la tuile CA (côté CRM · pilotage)
-- =============================================================================
-- « Combien d'étudiants, à quel prix. » Le CA reconstruit à partir des volumes
-- et des tarifs, jusqu'à la classe (campus × programme × année × modalité).
--
-- Réconciliation VÉRIFIÉE sur données réelles (2026) : la somme "CA total" de
-- cette query = celle de Q_CA_CONSTITUTION_COMPTA, au groupe ET à chaque marque
-- (écart 0,00 €). Les deux drills tombent donc toujours sur le même total.
--
-- POV : Tagetik injecte le filtre de la cellule cliquée (Exercice, et Marque si
-- le drill part d'une ligne marque). Colonnes de dimension laissées visibles
-- pour que le drill-through se filtre correctement.
-- Source : AW_002_000002_000001 (socle CRM).
-- =============================================================================
SELECT
    EXERCICE                                              AS "Exercice",
    SUBSTR_BEFORE(ENTITY, '_')                            AS "Marque",
    ENTITY                                                AS "Campus",
    PROGRAMME                                             AS "Programme",
    AN_ETUDE                                              AS "Année d'étude",
    MODALITE                                              AS "Modalité",
    SUM(VOL_EFF)                                          AS "Effectifs",
    SUM(VOL_EFF * REV_STUD)
        / NULLIF(SUM(VOL_EFF), 0)                         AS "Tarif moyen",
    SUM(VOL_EFF * REV_STUD)                               AS "CA scolarité",
    SUM(VOL_NEW)                                          AS "Nouveaux inscrits",
    SUM(VOL_NEW * REV_FRAIS_INS)                          AS "CA frais d'inscription",
    SUM(VOL_EFF * REV_STUD + VOL_NEW * REV_FRAIS_INS)     AS "CA total"
FROM AW_002_000002_000001
GROUP BY EXERCICE, SUBSTR_BEFORE(ENTITY, '_'), ENTITY, PROGRAMME, AN_ETUDE, MODALITE
ORDER BY "Marque", "Campus", "Programme", "Année d'étude", "Modalité";
