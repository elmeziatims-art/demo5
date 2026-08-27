-- =============================================================================
-- V_COCKPIT — alimentation du cockpit, forme "en ligne" (FST-ready, maille fine)
-- =============================================================================
-- Rien n'est pré-calculé ici. On sort la donnée BRUTE au grain le plus fin, et
-- c'est TON FST qui calcule CA, EBITDA, Marge. Le cockpit lit des membres :
--   CA      = noeud Produits (FST)
--   EBITDA  = FST 010
--   Marge % = EBITDA / CA           (membre calculé Tagetik)
--   CAC     = compte 6231 / STAT_INSC (membre calculé Tagetik)
--
-- Deux familles dans la même dimension Compte :
--   FINANCE    : les comptes P&L réels (dont 6231 = dépense acquisition)
--                -> le FST remonte CA / EBITDA / marge.
--   COMMERCIAL : comptes STATISTIQUES (non monétaires) à créer, hors hiérarchie
--                P&L : STAT_LEAD, STAT_CAND, STAT_ADMIS, STAT_INSC, STAT_EFF.
--
-- Maille la plus fine par source :
--   FINANCE    = ENTITY × ACCOUNT × EXERCICE × PERIOD
--   COMMERCIAL = ENTITY × PROGRAMME × AN_ETUDE × MODALITE × EXERCICE × PERIOD
--   (les dimensions non applicables au financier = membre générique 'GEN')
-- Réel/atterrissage : VERSION = 'ACT', EXERCICE 2024-2026.
-- =============================================================================
CREATE OR REPLACE VIEW V_COCKPIT AS
-- ===== FINANCE : tous les comptes P&L réels (le FST calcule CA, EBITDA, marge) =====
SELECT
    ENTITY,
    'GEN'                        AS PROGRAMME,
    'GEN'                        AS AN_ETUDE,
    'GEN'                        AS MODALITE,
    ACCOUNT,
    EXERCICE,
    CAST(PERIOD AS VARCHAR(10))  AS PERIOD,
    'ACT'                        AS VERSION,
    SUM(AMOUNT)                  AS AMOUNT
FROM AW_002_000004_000001
GROUP BY ENTITY, ACCOUNT, EXERCICE, CAST(PERIOD AS VARCHAR(10))

UNION ALL   -- ===== COMMERCIAL : leads (statistique) =====
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STAT_LEAD', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_LEAD)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL   -- candidatures
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STAT_CAND', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_CAND)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL   -- admis
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STAT_ADMIS', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_ADMIS)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL   -- inscrits (nouveaux)
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STAT_INSC', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_NEW)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10))

UNION ALL   -- effectif
SELECT ENTITY, PROGRAMME, AN_ETUDE, MODALITE, 'STAT_EFF', EXERCICE,
       CAST(PERIODE AS VARCHAR(10)), 'ACT', SUM(VOL_EFF)
FROM AW_002_000002_000001
GROUP BY ENTITY, PROGRAMME, AN_ETUDE, MODALITE, EXERCICE, CAST(PERIODE AS VARCHAR(10));
