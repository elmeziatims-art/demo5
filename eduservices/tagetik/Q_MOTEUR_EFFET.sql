-- =============================================================================
-- Q_MOTEUR_EFFET — la SORTIE du moteur par marque, depuis V_MOTEUR
-- Aligne la maille « marque » de l'Excel avec le calcul réel : on lit V_MOTEUR
-- (le moteur du cadrage, grain fin campus×programme×année×modalité) et on
-- l'agrège à la marque. Les chiffres sont donc EXACTEMENT ceux du cadrage.
--
-- L'EFFET d'un geste (+Δ% budget) = la DIFFÉRENCE entre deux états du moteur :
--   • soit entre versions (V01 cadrage vs V02 optimiste vs V03 prudent) ci-dessous,
--   • soit en rejouant le cadrage après avoir bougé le levier, puis en comparant.
-- On ne recalcule JAMAIS l'effet par une formule marginale à côté : c'est le
-- moteur per-cellule (mix, cohortes, prix par marque) qui fait foi.
--
-- Grain de sortie : VERSION × MARQUE. Filtrer / pivoter côté rapport.
-- =============================================================================
SELECT
    m.VERSION,
    m.MARQUE,
    SUM(m.NOUVEAUX)              AS "Nouveaux inscrits",
    SUM(m.EFFECTIF)             AS "Effectifs",
    SUM(m.CA)                  AS "CA 2027",
    1.0 * SUM(m.CA) / NULLIF(SUM(m.EFFECTIF),0) AS "CA / élève"
FROM V_MOTEUR m
GROUP BY m.VERSION, m.MARQUE
ORDER BY m.VERSION, m.MARQUE;

-- Variante « effet vs cadrage » (V01 en base, écart des autres versions) :
--   pivoter VERSION en colonnes côté rapport, puis membre calculé (Vxx − V01).
