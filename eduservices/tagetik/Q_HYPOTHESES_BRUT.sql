/* =============================================================================
   Q_HYPOTHESES_BRUT  —  trois lignes, a lancer UNE FOIS, pour lever les
   dernieres incertitudes de nommage.

   Elle ne sert pas au rapport. Elle sert a repondre a trois questions que je ne
   peux pas trancher depuis mes exports, et sur lesquelles je ne veux plus
   deviner :

     - comment s'appelle la colonne qui porte le scenario ? VERSION ?
     - quelles sont les valeurs exactes ? V01/V02/V03, ou autre chose ?
     - quels sont les codes reels des douze leviers, et sur quelle ENTITY ?

   Une fois la sortie sous les yeux, Q_HYPOTHESES est juste ou se corrige en
   deux lignes.
   ============================================================================= */
SELECT TOP 60 *
FROM   AW_002_000001_000001 AS h
WHERE  h.ACCOUNT LIKE 'HYP%'
