/* =============================================================================
   Q_D2_SOCLE  —  DRILL-THROUGH sur une cellule d'EBITDA, second drill.
   "DE QUOI CET EBITDA EST-IL FAIT" : le compte d'exploitation, poste par poste.

   SEIZE LIGNES, SIX COLONNES.

     Compte        LA CLE. Un vrai numero de compte pour quinze lignes, et le
                   code technique SIEGE pour la seizieme, qui est une
                   allocation et non une ecriture.
     Famille       Produits, Cout variable, Couts directs, Siege
     Poste         le libelle complet, pour le tableau
     Poste court   le libelle abrege, pour l'axe du graphe
     Montant 2025  contribution SIGNEE a l'EBITDA
     Montant 2026  idem

   =============================================================================
   CE QUI CHANGE : LE CHIFFRE D'AFFAIRES EST OUVERT EN TROIS COMPTES

   Il tenait sur une ligne, prise au socle CRM. Il en tient maintenant trois,
   lues sur les comptes de produit comme les douze comptes de charge :

       706    scolarite des etudiants en INITIAL
       7062   scolarite des ALTERNANTS
       708    frais d'inscription

   C'est possible depuis le realignement du 06/09 : les comptes de produit et
   le socle CRM disent desormais le meme montant, au centime, sur les trois
   exercices. Le tableau est donc un VRAI compte d'exploitation -- quinze
   lignes qui sont toutes de vraies ecritures, drillables plus loin -- au lieu
   d'un total de gestion pose au-dessus d'un detail de charges.

   Q_D3_CA_CRM et Q_D3_CA_COMPTA tiennent le rapprochement des deux chaines et
   montrent d'ou vient le montant, effectifs par prix.

   =============================================================================
   PAS DE COLONNE DE RANG

   L'ordre n'est pas l'affaire de la requete : le classeur va chercher chaque
   ligne par son Compte, avec une RECHERCHEV. Il fixe donc lui-meme la
   sequence, et la requete peut rendre ses lignes dans n'importe quel ordre --
   ce qui tombe bien, puisque le loader Tagetik interdit ORDER BY.

   C'est aussi pour cela que la ligne calculee porte un code : sans lui, elle
   serait introuvable par la recherche.

   LES MONTANTS SONT SIGNES : produits en positif, charges en negatif. Leur
   somme vaut exactement l'EBITDA.

   =============================================================================
   UNE STRUCTURE COMPTABLE STABLE, ET C'EST VOULU

   Le nombre de lignes ne depend pas de ce que la donnee contient. La liste des
   quinze comptes est ecrite dans un bloc VALUES joint en LEFT JOIN a la
   comptabilite : un compte sans mouvement rend zero, il ne disparait pas. Le
   706 par exemple est vide sur les campus Ipac, Pigier et Tunon, qui n'ont pas
   d'etudiants en initial -- la ligne reste, a zero. Seize lignes, toujours,
   quel que soit le noeud clique. Le jour ou un compte s'ajoute au plan, on
   l'ajoute a la liste et le compte passe a dix-sept, en connaissance de cause.

   =============================================================================
   DEUX SOURCES, ET C'EST L'INTERET DE CE DRILL

   1. LES QUINZE COMPTES sont lus tels quels sur le campus, dans
      AW_002_000004_000001. Ce sont de vraies ecritures.

   2. LE SIEGE n'est pas un compte du campus. Il est porte par GRP et
      redescendu par la cascade K1..K4 de V_ALLOCATION : la ligne est une
      ALLOCATION, pas une ecriture, et le libelle le dit.

   Verifie sur 2026 : 23 098 985 - 15 684 868 - 3 568 327 = 3 845 790.

   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Perimetre herite de la cellule cliquee, exercices en dur comme le cockpit.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    r.COMPTE                                    AS "Compte",
    r.FAMILLE                                   AS "Famille",
    r.POSTE                                     AS "Poste",
    r.COURT                                     AS "Poste court",
    r.SENS * SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2025 THEN d.AMOUNT ELSE 0 END)  AS "Montant 2025",
    r.SENS * SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2026 THEN d.AMOUNT ELSE 0 END)  AS "Montant 2026"
FROM (
        VALUES ('706',   'Produits',      'Scolarite des etudiants en initial', 'Scolarite initial',     1),
               ('7062',  'Produits',      'Scolarite des alternants',           'Scolarite alternance',  1),
               ('708',   'Produits',      'Frais d''inscription',               'Frais d''inscription',  1),
               ('621',   'Cout variable', 'Personnel exterieur (vacataires)',   'Vacataires',           -1),
               ('604',   'Cout variable', 'Achats d''etudes',                   'Achats d''etudes',     -1),
               ('6063',  'Cout variable', 'Fournitures',                        'Fournitures',          -1),
               ('6231',  'Cout variable', 'Publicite et acquisition',           'Acquisition',          -1),
               ('6411',  'Couts directs', 'Salaires des permanents',            'Salaires',             -1),
               ('6413',  'Couts directs', 'Primes',                             'Primes',               -1),
               ('645',   'Couts directs', 'Charges sociales',                   'Charges sociales',     -1),
               ('613',   'Couts directs', 'Loyers',                             'Loyers',               -1),
               ('615',   'Couts directs', 'Entretien',                          'Entretien',            -1),
               ('616',   'Couts directs', 'Assurances',                         'Assurances',           -1),
               ('625',   'Couts directs', 'Deplacements',                       'Deplacements',         -1),
               ('63511', 'Couts directs', 'Taxes',                              'Taxes',                -1)
     ) AS r(COMPTE, FAMILLE, POSTE, COURT, SENS)
LEFT JOIN AW_002_000004_000001 AS d
       ON  d.ACCOUNT = r.COMPTE
      AND  d.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
      AND  CAST(d.EXERCICE AS INT) IN (2025, 2026)
GROUP BY r.COMPTE, r.FAMILLE, r.POSTE, r.COURT, r.SENS

UNION ALL

SELECT
    'SIEGE'                                             AS "Compte",
    'Siege'                                             AS "Famille",
    'Siege redescendu (allocation, pas une ecriture)'   AS "Poste",
    'Siege'                                             AS "Poste court",
    -1 * SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2025 THEN a.COST_SIEGE ELSE 0 END),
    -1 * SUM(CASE WHEN CAST(a.EXERCICE AS INT) = 2026 THEN a.COST_SIEGE ELSE 0 END)
FROM    V_ALLOCATION AS a
WHERE   a.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
  AND   CAST(a.EXERCICE AS INT) IN (2025, 2026)
