-- =============================================================================
-- VUE CAMPAGNES — moteur d'acquisition par campus  (SAP HANA)
-- Source : AW_002_000002_000001 (socle enrichi marketing)
-- Sort : CPL, rendement (élasticité), part organique, conversion lead->inscrit,
--        CAC MARGINAL (= coût du prochain inscrit). Grain = ENTITY (campus).
--
-- RENDEMENT = régression log-log sur 3 ans (2024·2025·2026) :
--   élasticité = pente de ln(volume) sur ln(budget) = SLOPE(LN(vol);LN(budget)).
--   (= exactement la formule de l'Excel « Le moteur ». Sur 2 points seulement,
--    ça se réduit à LN(v26/v24)/LN(b26/b24) ; la régression 3 ans est plus
--    robuste au bruit et reste identique quand 2025 est sur la droite.)
--   CAC marginal = CPL / (rendement_acq × conversion).
-- Réf (niveaux) = exercice 2026. Brique appelée par V_CAP et V_MOTEUR.
-- =============================================================================
SELECT
    m.SCENARIO, m.PERIODE, m.ENTITY,
    m.ORG_REF, m.PAID_REF, (m.ORG_REF + m.PAID_REF) AS LEAD_REF,
    m.SPEND_ACQ_REF, m.SPEND_BRAND_REF,
    m.PART_ORG, m.CPL, m.REND_ACQ, m.CONVERSION, m.REND_BRAND,
    m.CPL / NULLIF(m.REND_ACQ * m.CONVERSION, 0) AS CAC_MARGINAL
FROM (
    SELECT
        g.SCENARIO, g.PERIODE, g.ENTITY,
        g.ORG_26 AS ORG_REF, g.PAID_26 AS PAID_REF,
        g.SACQ_26 AS SPEND_ACQ_REF, g.SBR_26 AS SPEND_BRAND_REF,
        COALESCE(g.ORG_26 / NULLIF(g.ORG_26 + g.PAID_26, 0), 0) AS PART_ORG,
        COALESCE(g.SACQ_26 / NULLIF(g.PAID_26, 0), 0)          AS CPL,
        COALESCE(g.NEW_26  / NULLIF(g.LEAD_26, 0), 0)          AS CONVERSION,
        -- élasticité acquisition = pente régression ln(paid) sur ln(spend acq), 3 ans
        CASE WHEN g.DEN_A > 0 THEN g.NUM_A / g.DEN_A ELSE 0.5  END AS REND_ACQ,
        -- élasticité marque = pente régression ln(org) sur ln(spend marque), 3 ans
        CASE WHEN g.DEN_B > 0 THEN g.NUM_B / g.DEN_B ELSE 0.35 END AS REND_BRAND
    FROM (
        SELECT l.*,
            (l.LSA24-l.MA)*(l.LPA24-l.MPA) + (l.LSA25-l.MA)*(l.LPA25-l.MPA) + (l.LSA26-l.MA)*(l.LPA26-l.MPA) AS NUM_A,
            (l.LSA24-l.MA)*(l.LSA24-l.MA) + (l.LSA25-l.MA)*(l.LSA25-l.MA) + (l.LSA26-l.MA)*(l.LSA26-l.MA)   AS DEN_A,
            (l.LSB24-l.MB)*(l.LOA24-l.MOA) + (l.LSB25-l.MB)*(l.LOA25-l.MOA) + (l.LSB26-l.MB)*(l.LOA26-l.MOA) AS NUM_B,
            (l.LSB24-l.MB)*(l.LSB24-l.MB) + (l.LSB25-l.MB)*(l.LSB25-l.MB) + (l.LSB26-l.MB)*(l.LSB26-l.MB)   AS DEN_B
        FROM (
            SELECT a.*,
                LN(a.SACQ_24) AS LSA24, LN(a.SACQ_25) AS LSA25, LN(a.SACQ_26) AS LSA26,
                LN(a.PAID_24) AS LPA24, LN(a.PAID_25) AS LPA25, LN(a.PAID_26) AS LPA26,
                LN(a.SBR_24)  AS LSB24, LN(a.SBR_25)  AS LSB25, LN(a.SBR_26)  AS LSB26,
                LN(a.ORG_24)  AS LOA24, LN(a.ORG_25)  AS LOA25, LN(a.ORG_26)  AS LOA26,
                (LN(a.SACQ_24)+LN(a.SACQ_25)+LN(a.SACQ_26))/3 AS MA,
                (LN(a.PAID_24)+LN(a.PAID_25)+LN(a.PAID_26))/3 AS MPA,
                (LN(a.SBR_24) +LN(a.SBR_25) +LN(a.SBR_26))/3  AS MB,
                (LN(a.ORG_24) +LN(a.ORG_25) +LN(a.ORG_26))/3  AS MOA
            FROM (
                SELECT s.SCENARIO, s.PERIODE, s.ENTITY,
                    SUM(CASE WHEN s.EXERCICE='2026' THEN s.VOL_LEAD_ORG   ELSE 0 END) AS ORG_26,
                    SUM(CASE WHEN s.EXERCICE='2026' THEN s.VOL_LEAD_PAY   ELSE 0 END) AS PAID_26,
                    SUM(CASE WHEN s.EXERCICE='2026' THEN s.DEPENSE_ACQ    ELSE 0 END) AS SACQ_26,
                    SUM(CASE WHEN s.EXERCICE='2026' THEN s.DEPENSE_MARQUE ELSE 0 END) AS SBR_26,
                    SUM(CASE WHEN s.EXERCICE='2026' THEN s.VOL_NEW        ELSE 0 END) AS NEW_26,
                    SUM(CASE WHEN s.EXERCICE='2026' THEN s.VOL_LEAD       ELSE 0 END) AS LEAD_26,
                    SUM(CASE WHEN s.EXERCICE='2025' THEN s.VOL_LEAD_ORG   ELSE 0 END) AS ORG_25,
                    SUM(CASE WHEN s.EXERCICE='2025' THEN s.VOL_LEAD_PAY   ELSE 0 END) AS PAID_25,
                    SUM(CASE WHEN s.EXERCICE='2025' THEN s.DEPENSE_ACQ    ELSE 0 END) AS SACQ_25,
                    SUM(CASE WHEN s.EXERCICE='2025' THEN s.DEPENSE_MARQUE ELSE 0 END) AS SBR_25,
                    SUM(CASE WHEN s.EXERCICE='2024' THEN s.VOL_LEAD_ORG   ELSE 0 END) AS ORG_24,
                    SUM(CASE WHEN s.EXERCICE='2024' THEN s.VOL_LEAD_PAY   ELSE 0 END) AS PAID_24,
                    SUM(CASE WHEN s.EXERCICE='2024' THEN s.DEPENSE_ACQ    ELSE 0 END) AS SACQ_24,
                    SUM(CASE WHEN s.EXERCICE='2024' THEN s.DEPENSE_MARQUE ELSE 0 END) AS SBR_24
                FROM AW_002_000002_000001 s
                GROUP BY s.SCENARIO, s.PERIODE, s.ENTITY
            ) a
        ) l
    ) g
) m
