-- =============================================================================
-- V_MOTEUR_CAL — calibration du moteur au grain CAMPUS × EXERCICE   (SAP HANA)
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
-- ── ATTRIBUTS CAMPUS (constants sur les années, rapatriés de V_CAMPAGNES) ────
--   REND_ACQ  = élasticité acquisition (régression log-log 3 ans)
--   REND_BRAND= élasticité marque      (régression log-log 3 ans)
--
-- NB : l'élasticité EST une régression sur 2024·2025·2026 ; elle n'a donc pas
--      de valeur « par année » — elle se répète, identique, sur chaque ligne
--      d'exercice du campus. Le join sur V_CAMPAGNES évite de redupliquer la
--      régression (definie une seule fois là-bas). CA_PAR_INSCRIT reste, lui,
--      annuel : c'est le vrai chiffre du campus, pas une moyenne groupe.
-- =============================================================================
SELECT
    y.SCENARIO, y.PERIODE, y.ENTITY, y.EXERCICE,
    y.LEAD_ORG,
    y.LEAD_PAY,
    y.LEAD_ORG + y.LEAD_PAY                              AS LEAD_TOT,
    y.SPEND_ACQ,
    y.SPEND_BRAND,
    y.INSCRITS,
    y.INSCRITS  / NULLIF(y.LEAD_TOT_RAW, 0)              AS CONVERSION,
    y.SPEND_ACQ / NULLIF(y.LEAD_PAY, 0)                  AS CPL,
    y.CA_NEW,
    y.CA_NEW    / NULLIF(y.INSCRITS, 0)                  AS CA_PAR_INSCRIT,
    c.REND_ACQ,
    c.REND_BRAND
FROM (
    SELECT
        s.SCENARIO, s.PERIODE, s.ENTITY, s.EXERCICE,
        SUM(s.VOL_LEAD_ORG)                                     AS LEAD_ORG,
        SUM(s.VOL_LEAD_PAY)                                     AS LEAD_PAY,
        SUM(s.VOL_LEAD)                                         AS LEAD_TOT_RAW,
        SUM(s.DEPENSE_ACQ)                                      AS SPEND_ACQ,
        SUM(s.DEPENSE_MARQUE)                                   AS SPEND_BRAND,
        SUM(s.VOL_NEW)                                          AS INSCRITS,
        SUM(s.VOL_NEW * s.REV_STUD + s.VOL_NEW * s.REV_FRAIS_INS) AS CA_NEW
    FROM AW_002_000002_000001 s
    GROUP BY s.SCENARIO, s.PERIODE, s.ENTITY, s.EXERCICE
) y
LEFT JOIN V_CAMPAGNES c
    ON  c.SCENARIO = y.SCENARIO
    AND c.PERIODE  = y.PERIODE
    AND c.ENTITY   = y.ENTITY
;
