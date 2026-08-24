-- =============================================================================
-- V_TRAJECTOIRE — trajectoire historique CA / EBITDA / Effectif 2024 -> 2026 (SAP HANA)
-- Source : V_PNL (réel 'ACT'). 1 ligne par EXERCICE.
--   • CA      = Σ comptes classe 7 (produits)
--   • EBITDA  = Σ7 − Σ6 (hors 6811 : amortissements exclus de l'EBITDA)
--   • EFFECTIF= compte statistique 'EFFECTIF'
--   Contrôle : 2026 -> CA 22 544 725, EBITDA 3 291 530, Effectif 3036.
-- NB : le 2027 n'est PAS dans la vue — il est ajouté en formule LIVE dans l'Excel
--      (à partir du moteur), en complément de cette restitution, pour un effet
--      instantané quand on bouge les leviers.
-- =============================================================================
CREATE OR REPLACE VIEW V_TRAJECTOIRE AS
SELECT
    p.EXERCICE,
    SUM(CASE WHEN p.ACCOUNT LIKE '7%' THEN p.AMOUNT ELSE 0 END)                    AS CA,
    SUM(CASE WHEN p.ACCOUNT LIKE '7%'  THEN  p.AMOUNT
             WHEN p.ACCOUNT =    '6811' THEN  0              -- amortissements exclus
             WHEN p.ACCOUNT LIKE '6%'   THEN -p.AMOUNT
             ELSE 0 END)                                                           AS EBITDA,
    SUM(CASE WHEN p.ACCOUNT = 'EFFECTIF' THEN p.AMOUNT ELSE 0 END)                 AS EFFECTIF
FROM V_PNL p
WHERE p.VERSION = 'ACT'
  AND p.EXERCICE IN ('2024','2025','2026')
GROUP BY p.EXERCICE
ORDER BY p.EXERCICE;
