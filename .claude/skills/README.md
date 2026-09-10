# Skills du projet

## cfo-executive-dataviz

Charte et methode pour les livrables Excel de la demo EDUSERVICES : cockpits
CFO, reporting de gestion, dataviz financiere.

Installe le 06/09/2026 depuis le paquet fourni par Saad. Contenu inchange par
rapport a l'original, seule cette note a ete ajoutee autour.

Il se charge tout seul au demarrage d'une session sur ce repo. On peut aussi
l'appeler explicitement :

    /cfo-executive-dataviz

Le controle qualite se lance a la main sur n'importe quel classeur :

    python3 .claude/skills/cfo-executive-dataviz/scripts/quality_gate.py <fichier.xlsx>

Il verifie les erreurs de formule, les valeurs en cache, le mode de calcul, les
liens externes, les feuilles masquees et la presence d'une couche de controle.
