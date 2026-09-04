-- Pont prix / volume / mix : decomposition de la variation de CA 2026 -> 2027, par version.
-- Volume = a prix 2026 ; Prix = a effectif 2026 ; Mix = interaction (residuel). Somme = delta CA.
CREATE OR ALTER VIEW V_BRIDGE_CA AS
WITH b26 AS (
    SELECT SUBSTR_BEFORE(ENTITY,'_') AS MARQUE, SUM(VOL_EFF) AS EFF,
        SUM(VOL_EFF*REV_STUD + VOL_NEW*REV_FRAIS_INS) AS CA
    FROM AW_002_000002_000001 WHERE EXERCICE='2026'
    GROUP BY SUBSTR_BEFORE(ENTITY,'_')
),
b27 AS ( SELECT MARQUE, VERSION, SUM(EFFECTIF) AS EFF, SUM(CA) AS CA FROM V_MOTEUR GROUP BY MARQUE, VERSION )
SELECT b27.VERSION,
    SUM(b26.CA)                                                                       AS CA_2026,
    SUM((1.0 * b26.CA / NULLIF(b26.EFF,0)) * (b27.EFF - b26.EFF))                              AS EFFET_VOLUME,
    SUM(b26.EFF * ((1.0 * b27.CA / NULLIF(b27.EFF,0)) - (1.0 * b26.CA / NULLIF(b26.EFF,0))))           AS EFFET_PRIX,
    SUM(((1.0 * b27.CA / NULLIF(b27.EFF,0)) - (1.0 * b26.CA / NULLIF(b26.EFF,0))) * (b27.EFF-b26.EFF)) AS EFFET_MIX,
    SUM(b27.CA)                                                                       AS CA_2027
FROM b26 JOIN b27 ON b27.MARQUE = b26.MARQUE
GROUP BY b27.VERSION;
