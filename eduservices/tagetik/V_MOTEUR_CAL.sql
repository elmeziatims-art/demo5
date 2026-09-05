-- =============================================================================
-- V_MOTEUR_CAL — calibration du moteur au grain CAMPUS × EXERCICE   (SQL Server / T-SQL)
-- Source : AW_002_000002_000001 (socle enrichi marketing).
--
-- Objet : donner en UNE vue tout ce qu'affichent les onglets Excel « Le moteur »
-- et « Budget de marque » — avec EXERCICE comme VRAIE dimension (contrairement à
-- V_CAMPAGNES, qui replie les années en interne et ne sort que les réfs 2026).
--
-- Grain de sortie : SCENARIO × PERIODE × ENTITY × EXERCICE.
--   → dans une matrice Tagetik : ENTITY (groupé par marque) en lignes,
--     EXERCICE (2024·2025·2026) en colonnes, mesures = les séries ci-dessous.
--
-- ── SÉRIES ANNUELLES (varient par EXERCICE) ─────────────────────────────────
--   LEAD_ORG · LEAD_PAY · LEAD_TOT · SPEND_ACQ (6231) · SPEND_BRAND (6236)
--   INSCRITS (VOL_NEW) · CONVERSION (inscrits/leads) · CPL (spend acq/lead payé)
--   CA_NEW · CA_PAR_INSCRIT (= CA du nouvel inscrit)
--
-- ── ÉLASTICITÉ : PAS dans la vue, calculée sur la MATRICE ────────────────────
--   Volontairement, la vue ne sort PAS le rendement. L'élasticité se calcule
--   en colonne/membre calculé Tagetik, directement à partir des membres EXERCICE
--   (elle reste ainsi transparente et cliquable, comme la formule Excel) :
--
--     • version 2 points (log-log) — identique au 3 points si la série est
--       log-linéaire (c'est le cas ici) :
--         ELAST_ACQ   = LN(LEAD_PAY[2026]  / LEAD_PAY[2024])
--                     / LN(SPEND_ACQ[2026] / SPEND_ACQ[2024])
--         ELAST_BRAND = LN(LEAD_ORG[2026]   / LEAD_ORG[2024])
--                     / LN(SPEND_BRAND[2026]/ SPEND_BRAND[2024])
--
--     • version 3 points (régression = SLOPE, plus robuste au bruit) : poser
--       x_a = LN(SPEND_ACQ[a]), y_a = LN(LEAD_PAY[a]) pour a ∈ {2024,25,26},
--       xbar = (x24+x25+x26)/3, ybar = (y24+y25+y26)/3, puis
--         ELAST_ACQ = Σ(x_a-xbar)(y_a-ybar) / Σ(x_a-xbar)²
--       (idem marque avec SPEND_BRAND / LEAD_ORG). C'est exactement le calcul
--        de V_CAMPAGNES.REND_ACQ, mais posé sur la matrice.
-- =============================================================================
CREATE OR ALTER VIEW V_MOTEUR_CAL AS
SELECT
    s.SCENARIO, s.PERIODE, s.ENTITY, s.EXERCICE,
    SUM(s.VOL_LEAD_ORG)                                       AS LEAD_ORG,
    SUM(s.VOL_LEAD_PAY)                                       AS LEAD_PAY,
    SUM(s.VOL_LEAD_ORG) + SUM(s.VOL_LEAD_PAY)                 AS LEAD_TOT,
    SUM(s.DEPENSE_ACQ)                                        AS SPEND_ACQ,
    SUM(s.DEPENSE_MARQUE)                                     AS SPEND_BRAND,
    SUM(s.VOL_NEW)                                            AS INSCRITS,
    1.0 * SUM(s.VOL_NEW) / NULLIF(SUM(s.VOL_LEAD), 0)            AS CONVERSION,
    1.0 * SUM(s.DEPENSE_ACQ) / NULLIF(SUM(s.VOL_LEAD_PAY), 0)       AS CPL,
    SUM(s.VOL_NEW * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) AS CA_NEW,
    1.0 * SUM(s.VOL_NEW * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) / NULLIF(SUM(s.VOL_NEW), 0)                           AS CA_PAR_INSCRIT
FROM AW_002_000002_000001 s
GROUP BY s.SCENARIO, s.PERIODE, s.ENTITY, s.EXERCICE
;
