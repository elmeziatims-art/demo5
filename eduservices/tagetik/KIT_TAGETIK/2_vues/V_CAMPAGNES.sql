-- =============================================================================
-- VUE CAMPAGNES — moteur d'acquisition par campus  (corps CREATE OR REPLACE VIEW V_CAMPAGNES AS
SELECT ; SAP HANA)
-- Source : AW_002_000002_000001 (socle enrichi marketing)
-- Reproduit l'onglet 03_Campagnes : CPL, rendement (mesuré), part organique,
-- conversion lead->inscrit, et CAC MARGINAL (= coût du prochain inscrit).
--   rendement = LN(vol_actif/vol_ancien) / LN(budget_actif/budget_ancien)
--   CAC marginal = CPL / (rendement_acq × conversion)
-- Réf = exercice 2026 (atterrissage) ; mesure de tendance sur 2024.
-- Vérifié = Excel (MBway Paris 1475, Tunon Paris 2193, ...).
-- Brique intermédiaire : appelée par V_CAP (CAC marginal) et V_MOTEUR (rendement/part org/réf).
-- =============================================================================
SELECT
    m.SCENARIO, m.PERIODE, m.ENTITY,
    m.ORG_REF, m.PAID_REF, (m.ORG_REF + m.PAID_REF) AS LEAD_REF,
    m.SPEND_ACQ_REF, m.SPEND_BRAND_REF,
    m.PART_ORG, m.CPL, m.REND_ACQ, m.CONVERSION, m.REND_BRAND,
    m.CPL / NULLIF(m.REND_ACQ * m.CONVERSION, 0) AS CAC_MARGINAL
FROM (
    SELECT
        a.SCENARIO, a.PERIODE, a.ENTITY,
        a.ORG_26 AS ORG_REF, a.PAID_26 AS PAID_REF,
        a.SACQ_26 AS SPEND_ACQ_REF, a.SBR_26 AS SPEND_BRAND_REF,
        COALESCE(a.ORG_26 / NULLIF(a.ORG_26 + a.PAID_26, 0), 0)  AS PART_ORG,
        COALESCE(a.SACQ_26 / NULLIF(a.PAID_26, 0), 0)            AS CPL,
        COALESCE(a.NEW_26  / NULLIF(a.LEAD_26, 0), 0)            AS CONVERSION,
        CASE WHEN a.PAID_24 > 0 AND a.PAID_26 > 0 AND a.SACQ_24 > 0 AND a.SACQ_26 > 0 AND a.SACQ_26 <> a.SACQ_24
             THEN LN(a.PAID_26 / a.PAID_24) / LN(a.SACQ_26 / a.SACQ_24) ELSE 0.5 END AS REND_ACQ,
        CASE WHEN a.ORG_24 > 0 AND a.ORG_26 > 0 AND a.SBR_24 > 0 AND a.SBR_26 > 0 AND a.SBR_26 <> a.SBR_24
             THEN LN(a.ORG_26 / a.ORG_24) / LN(a.SBR_26 / a.SBR_24) ELSE 0.35 END AS REND_BRAND
    FROM (
        SELECT
            s.SCENARIO, s.PERIODE, s.ENTITY,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_LEAD_ORG   ELSE 0 END) AS ORG_26,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_LEAD_PAY   ELSE 0 END) AS PAID_26,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.DEPENSE_ACQ    ELSE 0 END) AS SACQ_26,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.DEPENSE_MARQUE ELSE 0 END) AS SBR_26,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_NEW        ELSE 0 END) AS NEW_26,
            SUM(CASE WHEN s.EXERCICE = '2026' THEN s.VOL_LEAD       ELSE 0 END) AS LEAD_26,
            SUM(CASE WHEN s.EXERCICE = '2024' THEN s.VOL_LEAD_ORG   ELSE 0 END) AS ORG_24,
            SUM(CASE WHEN s.EXERCICE = '2024' THEN s.VOL_LEAD_PAY   ELSE 0 END) AS PAID_24,
            SUM(CASE WHEN s.EXERCICE = '2024' THEN s.DEPENSE_ACQ    ELSE 0 END) AS SACQ_24,
            SUM(CASE WHEN s.EXERCICE = '2024' THEN s.DEPENSE_MARQUE ELSE 0 END) AS SBR_24
        FROM AW_002_000002_000001 s
        GROUP BY s.SCENARIO, s.PERIODE, s.ENTITY
    ) a
) m
