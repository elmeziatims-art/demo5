-- =============================================================================
-- VUE CAP PROPOSÉ par campus  (corps SELECT ; SAP HANA)
-- Sources : AW_002_000002_000001 (socle) + AW_002_000004_000001 (compta, cpte 6231)
-- 3 indicateurs mesurés + 3 caps normalisés à moyenne 1 + CAP_RETENU (=1 par défaut)
-- + REJEU DU BUDGET D'ACQUISITION à somme nulle quand le cap bouge :
--     budget_rejoué = budget_réf × cap × [Σ budget_réf ÷ Σ(budget_réf × cap)]
--   (budget_réf par campus = dépense d'acquisition = compte 6231 ; enveloppe groupe constante)
-- =============================================================================
SELECT
    n.SCENARIO, n.PERIODE, n.ENTITY,
    n.CAC_MARGINAL, n.CROISS_LEADS, n.INTENSITE_MKT,
    n.CAP_EFF, n.CAP_MOM, n.CAP_POT, n.CAP_RETENU,
    n.BUDGET_ACQ_REF,
    n.BUDGET_ACQ_REF * n.CAP_RETENU
        * ( SUM(n.BUDGET_ACQ_REF) OVER (PARTITION BY n.SCENARIO, n.PERIODE)
            / NULLIF(SUM(n.BUDGET_ACQ_REF * n.CAP_RETENU) OVER (PARTITION BY n.SCENARIO, n.PERIODE), 0) )
        AS BUDGET_ACQ_REJOUE
FROM (
    SELECT
        r.SCENARIO, r.PERIODE, r.ENTITY,
        r.CAC_MARGINAL, r.CROISS_LEADS, r.INTENSITE_MKT, r.BUDGET_ACQ_REF,
        r.INV_CAC      / NULLIF(AVG(r.INV_CAC)      OVER (PARTITION BY r.SCENARIO, r.PERIODE), 0) AS CAP_EFF,
        r.CROISS_LEADS / NULLIF(AVG(r.CROISS_LEADS) OVER (PARTITION BY r.SCENARIO, r.PERIODE), 0) AS CAP_MOM,
        r.INV_INT      / NULLIF(AVG(r.INV_INT)      OVER (PARTITION BY r.SCENARIO, r.PERIODE), 0) AS CAP_POT,
        1 AS CAP_RETENU
    FROM (
        SELECT
            sagg.SCENARIO, sagg.PERIODE, sagg.ENTITY,
            sp.SPEND_2026                                   AS BUDGET_ACQ_REF,
            sp.SPEND_2026  / NULLIF(sagg.NEW_2026, 0)       AS CAC_MARGINAL,
            sagg.LEAD_2026 / NULLIF(sagg.LEAD_2024, 0) - 1  AS CROISS_LEADS,
            sp.SPEND_2026  / NULLIF(sagg.CA_2026, 0)        AS INTENSITE_MKT,
            sagg.NEW_2026  / NULLIF(sp.SPEND_2026, 0)       AS INV_CAC,
            sagg.CA_2026   / NULLIF(sp.SPEND_2026, 0)       AS INV_INT
        FROM (
            SELECT
                s.SCENARIO, s.PERIODE, s.ENTITY,
                SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_EFF * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS ELSE 0 END) AS CA_2026,
                SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_NEW  ELSE 0 END) AS NEW_2026,
                SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_LEAD ELSE 0 END) AS LEAD_2026,
                SUM(CASE WHEN s.EXERCICE = '2024' THEN s.VOL_LEAD ELSE 0 END) AS LEAD_2024
            FROM AW_002_000002_000001 s
            GROUP BY s.SCENARIO, s.PERIODE, s.ENTITY
        ) sagg
        LEFT JOIN (
            SELECT c.ENTITY, SUM(c.AMOUNT) AS SPEND_2026
            FROM AW_002_000004_000001 c
            WHERE c.ACCOUNT = '6231' AND c.EXERCICE = '2026'
            GROUP BY c.ENTITY
        ) sp ON sp.ENTITY = sagg.ENTITY
    ) r
) n
