-- =============================================================================
-- Q_RECONCILIATION_DETAIL — Matrice de réconciliation CRM ‖ Compta (2026)
-- =============================================================================
-- Une seule matrice : par marque/campus, le CRM et la Compta côte à côte,
-- découpés de la MÊME façon (initiale / alternance / frais), + écart par ligne.
-- -> si un écart apparaît, on voit direct CHEZ QUI (marque, campus, composante).
--
-- Alignement vérifié au centime en 2026 (14 campus, écart 0) :
--   CRM initial (MODALITE=INIT)  = compte 706
--   CRM alternance (MODALITE=ALT)= compte 7062
--   CRM frais (VOL_NEW×frais)    = compte 708
--
-- Dimension-keyed (Marque, Campus) -> multidim Tagetik (roule vers marque/groupe).
-- Drill d'une ligne -> le transactionnel : côté CRM le détail classe (socle),
-- côté Compta les écritures (Q_CA_CONSTITUTION_CRM / Q_CA_CONSTITUTION_COMPTA).
-- =============================================================================
SELECT
    crm.MARQUE                                                     AS "Marque",
    crm.CAMPUS                                                     AS "Campus",
    crm.EFFECTIF                                                   AS "Effectif",
    crm.CA_INIT                                                    AS "CRM · CA initial",
    crm.CA_ALT                                                     AS "CRM · CA alternance",
    crm.CA_FRAIS                                                   AS "CRM · CA frais insc.",
    cpt.C706                                                       AS "Compta · Initial (706)",
    cpt.C7062                                                      AS "Compta · Alternance (7062)",
    cpt.C708                                                       AS "Compta · Frais dossier (708)",
    (cpt.C706 + cpt.C7062 + cpt.C708)
      - (crm.CA_INIT + crm.CA_ALT + crm.CA_FRAIS)                  AS "Écart"
FROM (
        SELECT SUBSTR_BEFORE(ENTITY,'_') AS MARQUE,
               ENTITY                    AS CAMPUS,
               SUM(VOL_EFF)                                                       AS EFFECTIF,
               SUM(CASE WHEN MODALITE = 'INIT' THEN VOL_EFF * REV_STUD ELSE 0 END) AS CA_INIT,
               SUM(CASE WHEN MODALITE = 'ALT'  THEN VOL_EFF * REV_STUD ELSE 0 END) AS CA_ALT,
               SUM(VOL_NEW * REV_FRAIS_INS)                                        AS CA_FRAIS
        FROM AW_002_000002_000001
        WHERE EXERCICE = '2026'
        GROUP BY SUBSTR_BEFORE(ENTITY,'_'), ENTITY
     ) crm
LEFT JOIN (
        SELECT ENTITY,
               SUM(CASE WHEN ACCOUNT = '706'  THEN AMOUNT ELSE 0 END) AS C706,
               SUM(CASE WHEN ACCOUNT = '7062' THEN AMOUNT ELSE 0 END) AS C7062,
               SUM(CASE WHEN ACCOUNT = '708'  THEN AMOUNT ELSE 0 END) AS C708
        FROM AW_002_000004_000001
        WHERE EXERCICE = '2026'
          AND ACCOUNT IN ('706', '7062', '708')
        GROUP BY ENTITY
     ) cpt
     ON cpt.ENTITY = crm.CAMPUS
ORDER BY crm.MARQUE, crm.CAMPUS;
