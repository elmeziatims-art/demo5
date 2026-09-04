-- Les 3 scenarios cote a cote : CA, effectif, EBITDA, marge (2027).
SELECT
    CASE m.VERSION WHEN 'V01' THEN 'Cadrage' WHEN 'V02' THEN 'Optimiste'
                   WHEN 'V03' THEN 'Prudent' END              AS "Scénario",
    SUM(m.CA)                                                 AS "CA 2027",
    SUM(m.EFFECTIF)                                           AS "Effectif",
    e.EBITDA                                                  AS "EBITDA",
    1.0 * e.EBITDA / NULLIF(SUM(m.CA),0)                            AS "Marge %"
FROM V_MOTEUR m
JOIN (
    SELECT VERSION,
        SUM(CASE WHEN ACCOUNT IN ('7062','706','708')            THEN AMOUNT
                 WHEN ACCOUNT LIKE '6%' AND ACCOUNT <> '6811'    THEN -AMOUNT ELSE 0 END) AS EBITDA
    FROM V_BUDGET WHERE EXERCICE='2027' GROUP BY VERSION
) e ON e.VERSION = m.VERSION
GROUP BY m.VERSION, e.EBITDA
ORDER BY m.VERSION;
