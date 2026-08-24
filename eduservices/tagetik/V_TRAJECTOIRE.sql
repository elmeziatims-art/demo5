-- =============================================================================
-- V_TRAJECTOIRE — trajectoire CA / EBITDA / Effectif 2024 -> 2027  (SAP HANA)
-- Source unique : V_PNL (réel 'ACT' 2024-2026 + budget V01/V02/V03 2027 + compte
--                 statistique 'EFFECTIF'). 1 ligne par EXERCICE.
--   • CA      = Σ comptes classe 7 (produits)
--   • EBITDA  = Σ7 − Σ6 + Σ6811   (on ré-ajoute la dotation aux amortissements
--               6811 : l'EBITDA est AVANT amortissements). Montants stockés positifs
--               (contrôle : 2026 -> CA 22 544 725, EBITDA 3 291 530).
--   • EFFECTIF= compte statistique 'EFFECTIF'
-- Le 2027 est pris sur la VERSION active (ici V01 = Cadrage) — paramétrable.
-- =============================================================================
CREATE OR REPLACE VIEW V_TRAJECTOIRE AS
SELECT
    p.EXERCICE,
    SUM(CASE WHEN p.ACCOUNT LIKE '7%' THEN p.AMOUNT ELSE 0 END)                       AS CA,
    SUM(CASE WHEN p.ACCOUNT LIKE '7%'  THEN  p.AMOUNT
             WHEN p.ACCOUNT =    '6811' THEN  0              -- amortissements EXCLUS (EBITDA)
             WHEN p.ACCOUNT LIKE '6%'   THEN -p.AMOUNT
             ELSE 0 END)                                                              AS EBITDA,
    SUM(CASE WHEN p.ACCOUNT = 'EFFECTIF' THEN p.AMOUNT ELSE 0 END)                    AS EFFECTIF
FROM V_PNL p
WHERE (p.EXERCICE IN ('2024','2025','2026') AND p.VERSION = 'ACT')
   OR (p.EXERCICE =  '2027'                 AND p.VERSION = 'V01')   -- scénario Cadrage
GROUP BY p.EXERCICE
ORDER BY p.EXERCICE;

-- Variante « live » multi-scénarios : remplacer la clause 2027 par
--   OR (p.EXERCICE = '2027' AND p.VERSION = :VERSION_ACTIVE)
-- pour piloter la trajectoire par le scénario choisi dans le masque.
