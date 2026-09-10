/* =============================================================================
   Q_D3_CA_CRM  —  DRILL-THROUGH sur le chiffre d'affaires, cote CRM.
   "D'OU VIENT CE CHIFFRE D'AFFAIRES" : la chaine des inducteurs.

   TROIS LIGNES, HUIT COLONNES.

     Compte         LA CLE. Le compte de produit auquel la ligne correspond,
                    pour se rapprocher de Q_D3_CA_COMPTA au meme grain.
     Poste          le libelle complet, pour le tableau
     Poste court    le libelle abrege, pour l'axe du graphe
     Unite comptee  ce que le volume compte : des effectifs, ou des entrants
     Volume 2025    additif
     Volume 2026    additif
     Montant 2025   additif
     Montant 2026   additif

   =============================================================================
   LA REGLE QUI GOUVERNE CETTE REQUETE : ELLE NE DIVISE PAS

   Le prix moyen ne sort pas d'ici, et c'est voulu. Une moyenne ne survit pas a
   une somme : additionner les prix moyens de quatorze campus ne donne pas le
   prix moyen du groupe. La requete rend donc le NUMERATEUR et le DENOMINATEUR
   -- le montant et le volume -- et le classeur divise APRES avoir somme. Le
   resultat est alors juste a tous les niveaux de la hierarchie, du campus au
   groupe, sans que la requete ait a savoir a quel niveau elle tourne.

   Meme discipline que Q_D1_SOCLE.

   =============================================================================
   LA CORRESPONDANCE AVEC LES COMPTES

       706    scolarite des etudiants en INITIAL   VOL_EFF x REV_STUD
       7062   scolarite des ALTERNANTS             VOL_EFF x REV_STUD
       708    frais d'inscription                  VOL_NEW x REV_FRAIS_INS

   Les frais d'inscription se paient une fois, a l'entree : leur volume est
   VOL_NEW, les nouveaux inscrits, pas l'effectif total. C'est pour cela que la
   colonne "Unite comptee" existe -- les trois lignes ne comptent pas la meme
   chose et on ne doit jamais additionner leurs volumes.

   =============================================================================
   CE QUE LE CLASSEUR EN FAIT

   Prix moyen        = Montant / Volume, apres somme
   Effet volume      = (Volume N - Volume N-1) x Prix moyen N-1
   Effet prix        = (Prix moyen N - Prix moyen N-1) x Volume N
   Effet volume + effet prix = variation du montant, EXACTEMENT.

   Pas de terme croise, pas de residu : le volume est valorise au prix de
   l'an dernier, le prix applique au volume de cette annee.

   L'effet prix porte aussi le MIX -- un campus qui bascule des initiaux vers
   des alternants voit son prix moyen bouger sans qu'aucun tarif ait change.
   Pour separer les deux il faudrait descendre au grain programme x annee
   d'etude ; a ce stade du drill, ce n'est pas la question posee.

   =============================================================================
   TROIS LIGNES, TOUJOURS

   Chaque branche de l'UNION est une agregation SANS GROUP BY : elle rend donc
   exactement une ligne, meme si le perimetre ne contient aucun etudiant en
   initial. C'est le cas des campus Ipac, Pigier et Tunon, ou le 706 sort a
   zero au lieu de disparaitre. Les COALESCE sont la pour cela : une somme sur
   zero ligne vaut NULL, pas 0.

   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Perimetre herite de la cellule cliquee, exercices en dur comme le cockpit.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    '706'                                       AS "Compte",
    'Scolarite des etudiants en initial'        AS "Poste",
    'Scolarite initial'                         AS "Poste court",
    'Effectifs'                                 AS "Unite comptee",
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_EFF ELSE 0 END), 0)                 AS "Volume 2025",
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_EFF ELSE 0 END), 0)                 AS "Volume 2026",
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0)    AS "Montant 2025",
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0)    AS "Montant 2026"
FROM    AW_002_000002_000001 AS s
WHERE   s.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(s.EXERCICE AS INT) IN (2025, 2026)
  AND   s.MODALITE = 'INIT'

UNION ALL

SELECT
    '7062',
    'Scolarite des alternants',
    'Scolarite alternance',
    'Effectifs',
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_EFF ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_EFF ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_EFF * s.REV_STUD ELSE 0 END), 0)
FROM    AW_002_000002_000001 AS s
WHERE   s.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(s.EXERCICE AS INT) IN (2025, 2026)
  AND   s.MODALITE = 'ALT'

UNION ALL

SELECT
    '708',
    'Frais d''inscription',
    'Frais d''inscription',
    'Nouveaux inscrits',
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_NEW ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_NEW ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2025 THEN s.VOL_NEW * s.REV_FRAIS_INS ELSE 0 END), 0),
    COALESCE(SUM(CASE WHEN CAST(s.EXERCICE AS INT) = 2026 THEN s.VOL_NEW * s.REV_FRAIS_INS ELSE 0 END), 0)
FROM    AW_002_000002_000001 AS s
WHERE   s.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(s.EXERCICE AS INT) IN (2025, 2026)
