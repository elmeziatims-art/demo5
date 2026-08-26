-- Tendance historique : leads, CA, depenses, CAC par exercice x marque (Socle CRM)
CREATE OR REPLACE VIEW V_TENDANCE AS
SELECT EXERCICE, SUBSTR_BEFORE(ENTITY,'_') AS MARQUE,
    SUM(VOL_LEAD)                                       AS LEADS,
    SUM(VOL_NEW)                                        AS INSCRITS,
    SUM(VOL_EFF*REV_STUD + VOL_NEW*REV_FRAIS_INS)       AS CA,
    SUM(DEPENSE_ACQ)                                    AS DEPENSE_ACQ,
    SUM(DEPENSE_MARQUE)                                 AS DEPENSE_MARQUE,
    SUM(DEPENSE_ACQ) / NULLIF(SUM(VOL_NEW),0)           AS CAC
FROM AW_002_000002_000001
GROUP BY EXERCICE, SUBSTR_BEFORE(ENTITY,'_');
