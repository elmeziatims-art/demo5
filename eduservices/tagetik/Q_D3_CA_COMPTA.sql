/* =============================================================================
   Q_D3_CA_COMPTA  —  DRILL-THROUGH sur le chiffre d'affaires, cote comptable.
   La meme somme, lue sur les comptes de produit.

   TROIS LIGNES, QUATRE COLONNES.

     Compte         LA CLE, la meme que dans Q_D3_CA_CRM
     Poste          le libelle du plan comptable quand il existe
     Montant 2025
     Montant 2026

   =============================================================================
   POURQUOI DEUX REQUETES POUR UN SEUL CHIFFRE

   Parce qu'elles ne passent pas par le meme chemin, et qu'un chiffre qui
   arrive deux fois par deux chemins differents est un chiffre verifie.

     Q_D3_CA_CRM      part des inducteurs : effectifs x droits de scolarite.
                      C'est la chaine du PILOTAGE -- on peut bouger un
                      effectif et voir le CA suivre.

     Q_D3_CA_COMPTA   lit les comptes 706, 7062 et 708 tels qu'ils sont poses.
                      C'est la chaine du CONSTAT.

   Les deux tombent au centime depuis le realignement du 06/09. L'ecart doit
   donc rester a zero ; s'il reapparait, c'est que le socle CRM a bouge sans
   que les comptes de produit suivent, et FIX_CA_COMPTA_2024_2025.sql les
   remet d'accord.

   =============================================================================
   TROIS LIGNES, TOUJOURS

   La liste des comptes est ecrite dans un bloc VALUES joint en LEFT JOIN a la
   comptabilite. Un compte sans mouvement rend zero, il ne disparait pas : le
   706 par exemple est vide sur les campus Ipac, Pigier et Tunon, qui n'ont pas
   d'etudiants en initial. La ligne reste, a zero, et le rapprochement se lit
   sans trou.

   LES MONTANTS SONT RENDUS EN POSITIF : ce sont des produits.

   Alias entre guillemets doubles, Tagetik n'accepte pas les crochets.
   Perimetre herite de la cellule cliquee, exercices en dur comme le cockpit.
   Pas de CTE, pas de ORDER BY, pas de ';'.
   ============================================================================= */
SELECT
    r.COMPTE                                    AS "Compte",
    COALESCE(c.DESC_CONTO0, r.POSTE)            AS "Poste",
    SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2025 THEN d.AMOUNT ELSE 0 END)  AS "Montant 2025",
    SUM(CASE WHEN CAST(d.EXERCICE AS INT) = 2026 THEN d.AMOUNT ELSE 0 END)  AS "Montant 2026"
FROM (
        VALUES ('706',  'Scolarite des etudiants en initial'),
               ('7062', 'Scolarite des alternants'),
               ('708',  'Frais d''inscription')
     ) AS r(COMPTE, POSTE)
LEFT JOIN AW_002_000004_000001 AS d
       ON  d.ACCOUNT = r.COMPTE
      AND  d.ENTITY IN (${$Entity(HIERARCHY("EDU")).lowest})
      AND  CAST(d.EXERCICE AS INT) IN (2025, 2026)
LEFT JOIN conto AS c
       ON  c.COD_CONTO = r.COMPTE
GROUP BY r.COMPTE, COALESCE(c.DESC_CONTO0, r.POSTE)
