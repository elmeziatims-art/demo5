-- =============================================================================
-- V_COCKPIT_MESURES — les mesures en COLONNES : la valeur ET sa croissance.
-- Grain : SCENARIO x VERSION x PERIODE x EXERCICE x MARQUE x ENTITY (campus).
--
-- -------------------------------------------------------------------------
-- LA REGLE A RETENIR : une VARIATION ne s'agrege pas.
-- -------------------------------------------------------------------------
-- La somme de deux marges n'est pas une marge ; la moyenne de deux CAC n'est
-- pas un CAC. Si la matrice totalise plusieurs campus, toute mesure du bloc ②
-- ou ③ devient FAUSSE.
--
-- D'ou la construction en trois blocs :
--   ① MESURES ADDITIVES ...... se somment a tous les niveaux. Chacune est
--                              livree en doublon N / N-1, donc une seule
--                              mesure choisie donne deja le chiffre et sa base
--                              de comparaison.
--   ② MESURES DERIVEES ....... justes AU GRAIN DE LA LIGNE (un campus).
--   ③ VARIATIONS ............. justes AU GRAIN DE LA LIGNE (un campus).
--
-- EN PRATIQUE :
--   . matrice au grain campus, sans totaux  -> pioche librement dans ①②③
--   . matrice avec totaux (marque, groupe)  -> ne prends que ①, et recompose :
--
--        Marge EBITDA        = EBITDA / CA
--        Croissance CA       = CA / CA_N1 - 1
--        Croissance EBITDA   = EBITDA / EBITDA_N1 - 1
--        Ecart de marge (pt) = (EBITDA/CA - EBITDA_N1/CA_N1) * 100
--        CAC                 = SPEND_ACQ / INSCRITS
--        Croissance CAC      = (SPEND_ACQ/INSCRITS) / (SPEND_ACQ_N1/INSCRITS_N1) - 1
--        Remplissage         = EFFECTIFS / PLACES
--
--   Ces six formules sont des cellules calculees a cote de la matrice, comme
--   tes SUMIFS. Elles restent justes a TOUS les niveaux, parce qu'elles
--   partent de mesures additives.
--
-- L'exercice de comparaison est deduit (EXERCICE - 1) : rien a saisir.
-- =============================================================================
WITH base AS (
    SELECT
        c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY,
        SUM(c.CA)                                   AS CA,
        SUM(c.CA - c.COST_COMPLET + c.COST_SIEGE)   AS EBITDA,      -- avant siege
        SUM(c.VOL_NEW)                              AS INSCRITS,
        SUM(c.VOL_EFF)                              AS EFFECTIFS,
        SUM(c.PLACES)                               AS PLACES
    FROM V_CAMPUS_CLASSE c
    GROUP BY c.SCENARIO, c.VERSION, c.PERIODE, c.EXERCICE, c.MARQUE, c.ENTITY
),
acq AS (
    SELECT m.SCENARIO, m.PERIODE, m.EXERCICE, m.ENTITY, SUM(m.SPEND_ACQ) AS SPEND_ACQ
    FROM V_MOTEUR_CAL m
    GROUP BY m.SCENARIO, m.PERIODE, m.EXERCICE, m.ENTITY
),
k AS (
    SELECT b.*, COALESCE(a.SPEND_ACQ, 0) AS SPEND_ACQ
    FROM base b
    LEFT JOIN acq a
      ON  a.SCENARIO = b.SCENARIO AND a.PERIODE = b.PERIODE
      AND a.EXERCICE = b.EXERCICE AND a.ENTITY  = b.ENTITY
)
SELECT
    -- ---------- dimensions ----------
    n.SCENARIO, n.VERSION, n.PERIODE, n.EXERCICE, n.MARQUE, n.ENTITY,

    -- ---------- ① MESURES ADDITIVES  (sommables a tous les niveaux) ----------
    n.CA                                          AS CA,
    p.CA                                          AS CA_N1,
    n.EBITDA                                      AS EBITDA,
    p.EBITDA                                      AS EBITDA_N1,
    n.INSCRITS                                    AS INSCRITS,
    p.INSCRITS                                    AS INSCRITS_N1,
    n.EFFECTIFS                                   AS EFFECTIFS,
    p.EFFECTIFS                                   AS EFFECTIFS_N1,
    n.PLACES                                      AS PLACES,
    p.PLACES                                      AS PLACES_N1,
    n.PLACES - n.EFFECTIFS                        AS PLACES_LIBRES,
    n.SPEND_ACQ                                   AS SPEND_ACQ,
    p.SPEND_ACQ                                   AS SPEND_ACQ_N1,

    -- ---------- ② MESURES DERIVEES  (justes au grain de la ligne) ----------
    1.0 * n.EBITDA / NULLIF(n.CA, 0)                 AS MARGE,
    1.0 * p.EBITDA / NULLIF(p.CA, 0)                 AS MARGE_N1,
    1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0)           AS CAC,
    1.0 * p.SPEND_ACQ / NULLIF(p.INSCRITS, 0)           AS CAC_N1,
    1.0 * n.EFFECTIFS / NULLIF(n.PLACES, 0)             AS REMPLISSAGE,
    1.0 * p.EFFECTIFS / NULLIF(p.PLACES, 0)             AS REMPLISSAGE_N1,

    -- ---------- ③ VARIATIONS  (justes au grain de la ligne) ----------
    1.0 * n.CA / NULLIF(p.CA, 0)       - 1       AS CA_VAR,
    1.0 * n.EBITDA / NULLIF(p.EBITDA, 0)   - 1       AS EBITDA_VAR,
    1.0 * n.INSCRITS / NULLIF(p.INSCRITS, 0) - 1       AS INSCRITS_VAR,
    1.0 * (1.0 * n.SPEND_ACQ / NULLIF(n.INSCRITS, 0)) / NULLIF(1.0 * p.SPEND_ACQ / NULLIF(p.INSCRITS, 0), 0) - 1
                                                  AS CAC_VAR,
    (1.0 * n.EBITDA / NULLIF(n.CA, 0)
       - 1.0 * p.EBITDA / NULLIF(p.CA, 0)) * 100        AS MARGE_VAR_PT,
    (1.0 * n.EFFECTIFS / NULLIF(n.PLACES, 0)
       - 1.0 * p.EFFECTIFS / NULLIF(p.PLACES, 0)) * 100 AS REMPLISSAGE_VAR_PT

FROM k n
LEFT JOIN k p
  ON  p.SCENARIO = n.SCENARIO
  AND p.VERSION  = n.VERSION
  AND p.PERIODE  = n.PERIODE
  AND p.ENTITY   = n.ENTITY
  AND CAST(p.EXERCICE AS INTEGER) = CAST(n.EXERCICE AS INTEGER) - 1

ORDER BY n.EXERCICE, n.MARQUE, n.ENTITY;
