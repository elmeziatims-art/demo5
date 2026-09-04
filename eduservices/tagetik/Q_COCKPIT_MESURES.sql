-- Q_COCKPIT_MESURES — restitution rapide, grain campus, sans parametre.
-- Que des mesures ADDITIVES : le resultat reste juste quel que soit le niveau
-- sur lequel Tagetik filtre (campus, marque, noeud, groupe).
-- N-1 est une COLONNE, pas une ligne : un filtre sur EXERCICE = 2026 ne
-- l'emporte donc pas, la base de comparaison suit toujours.
SELECT
    n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE, n.MARQUE, n.ENTITY,
    n.CA,                                    COALESCE(p.CA, 0)         AS CA_N1,
    n.EBITDA,                                COALESCE(p.EBITDA, 0)     AS EBITDA_N1,
    n.INSCRITS,                              COALESCE(p.INSCRITS, 0)   AS INSCRITS_N1,
    n.EFFECTIFS,                             COALESCE(p.EFFECTIFS, 0)  AS EFFECTIFS_N1,
    n.PLACES,                                COALESCE(p.PLACES, 0)     AS PLACES_N1,
    n.PLACES - n.EFFECTIFS                                             AS PLACES_LIBRES,
    n.SPEND_ACQ,                             COALESCE(p.SPEND_ACQ, 0)  AS SPEND_ACQ_N1
FROM (
    SELECT c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY,
           SUM(c.CA)                                 AS CA,
           SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE) AS EBITDA,
           SUM(c.VOL_NEW)                            AS INSCRITS,
           SUM(c.VOL_EFF)                            AS EFFECTIFS,
           SUM(c.PLACES)                             AS PLACES,
           COALESCE(SUM(m.SPEND_ACQ), 0)             AS SPEND_ACQ
    FROM V_CAMPUS_CLASSE c
    LEFT JOIN V_MOTEUR_CAL m
           ON m.SCENARIO = c.SCENARIO AND m.PERIODE = c.PERIODE
          AND m.EXERCICE = c.EXERCICE AND m.ENTITY  = c.ENTITY
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY
) n
LEFT JOIN (
    SELECT c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.ENTITY,
           SUM(c.CA)                                 AS CA,
           SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE) AS EBITDA,
           SUM(c.VOL_NEW)                            AS INSCRITS,
           SUM(c.VOL_EFF)                            AS EFFECTIFS,
           SUM(c.PLACES)                             AS PLACES,
           COALESCE(SUM(m.SPEND_ACQ), 0)             AS SPEND_ACQ
    FROM V_CAMPUS_CLASSE c
    LEFT JOIN V_MOTEUR_CAL m
           ON m.SCENARIO = c.SCENARIO AND m.PERIODE = c.PERIODE
          AND m.EXERCICE = c.EXERCICE AND m.ENTITY  = c.ENTITY
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.ENTITY
) p
  ON  p.SCENARIO = n.SCENARIO AND p.VERSION = n.VERSION
  AND p.PERIODE  = n.PERIODE  AND p.ENTITY  = n.ENTITY
  AND p.EXERCICE = TO_VARCHAR(TO_INT(n.EXERCICE) - 1)
ORDER BY n.EXERCICE, n.MARQUE, n.ENTITY
;
