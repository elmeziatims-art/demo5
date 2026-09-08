/* =============================================================================
   Q_HYPOTHESES_BRUT  —  la table telle quelle, pour verifier a l'oeil.

   Elle a servi une fois et a tout appris : les vrais noms de colonnes
   (PARAMETRE, MEASURE, VERSION), l'absence de colonne EXERCICE, les codes
   reels des douze leviers -- et surtout que la table stocke des DEFORMATIONS,
   donc plusieurs lignes pour une meme cle.

   On la garde parce qu'elle sert a deux choses : verifier apres une saisie que
   la deformation est bien passee, et retrouver la valeur nette d'un levier
   sans passer par le rapport.
   ============================================================================= */
SELECT h.PARAMETRE, h.VERSION, COUNT(*) AS LIGNES, SUM(h.MEASURE) AS VALEUR_NETTE
FROM   AW_002_000001_000001 AS h
WHERE  h.PARAMETRE LIKE 'HYP%'
  AND  h.SCENARIO = '2027BUD_V1'
GROUP BY h.PARAMETRE, h.VERSION
