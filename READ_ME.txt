----- "SEQUENCES" : l'ensemble des passes effectuées ainsi que les début et fin de possession -----

Chaque ligne est un événement (passe, réception, fin de possession)
	"Position" est la colonne qui contient le timecode de l'événement (en ms)
	L'événement est une passe quand "Passeur" contient l'identifiant d'un joueur
	L'événement est une réception quand "Receveur" contient l'identifiant d'un joueur
	L'événément est une fin de possession quand "Resultat" contient un résultat de possession, parmi :
      - "essai"
      - "ballon perdu"
      - "defenseur" (= passe au pied qui fini dans les mains d'un défenseur)
      - "touche" (= passe au pied qui termine en dehors du terrain, après un rebond)
      = les deux premiers sont les principaux, les suivants servent à savoir où est le ballon à la fin
	Les autres colonnes contiennent des informations supplémentaires :
      - "Condition" = pédagogie dans laquelle a joué l'équipe (émergent ou prescriptif)		
      - "Possession" = un identifiant unique de la possession (au sein d'une "Expe")
      - "Serie" = différentes phases de l'expérimentation (pre-test, intervention, post-test)
      - "Defense" = scénario de jeu, c'est à dire un positionnement donné des défenseurs parmi les 5 possibles
      - "Cote" = lancement de jeu vers la droite ou vers la gauche (= éventuellement à inverser dans un cas)
      - "Contact" = indique lorsqu'une passe a été réalisée 'après contact' (= un défenseur touche l'attaquant)
      - "Pied" = indique lorsqu'une passe a été effectuée au pied, en diagonale ou vers l'avant
      - "Sortie" = quand le résultat est "touche", ça indique à quel endroit le ballon est sorti





----- "INFOS" : contient les informations sur les joueurs (équipe, numéro de maillot, n° de boitier GPS) -----

=> Ce fichier permet d'associer les données de séquençage (où les joueurs sont identifiés par un numéro unique) et les données GPS (où les joueurs sont identifiés par le numéro de leur balise GPS)





----- "GPS_clean" contient les données spatio-temporelles des joueurs et du ballon -----

"X";"Y" -> la coordonnées GPS
"Position" -> le timecode
"GPS" -> la balise GPS

"Expe" -> nom de l'équipe
"Possession" -> un identifiant unique de la possession (au sein d'une "Expe")
"Condition" -> pédagogie dans laquelle a joué l'équipe (émergent ou prescriptif)
"Serie" -> différentes phases de l'expérimentation (pre-test, intervention, post-test)
"Defense" -> scénario de jeu, c'est à dire un positionnement donné des défenseurs parmi les 5 possibles
"Cote" -> lancement de jeu vers la droite ou vers la gauche (= éventuellement à inverser dans un cas)
"Team" -> équipe du joueur (attaque ou défense)

Attention : 
- une équipe est un combo unique Expe x Condition, car ce ne sont pas les mêmes joueurs qui ont effectué les 2 pédagogies (chaque joueur = une seule pédagogie)
- lancement de jeu à droite et à gauche ne se font pas sur le même terrain





----- "GPS_raw" : ce sont les fichiers GPS de chaque joueur, dans la version brute -----

"Expe"_Export for "Player" "GPS" DeviceID.csv

où Expe/Player/GPS correspondent aux variables retrouvées dans les autres fichiers

pour les expe "racing" et "toulouse" les données ont été récoltées en 2 sessions, il y a donc un "_e" ou un "_p" à la fin du nom du fichier pour signifier s'il sagit de la partie "EMERGENT" ou "PRESCRIPTIF" (correspondant aux 2 valeurs possibles de la variable "Condition" dans les autres fichiers)





----- "GPS_V2" : une nouvelle version des fichiers GPS, qui inclue + de data et + d'infos -----
Il y a "+ de data" car on a les données de plus d'équipes, et "+ d'infos" :
- "Time" correspond au temps de jeu de la possession
- "Position" correspond au temps du fichier de séquençage 
- "Event" correspond à l'évènement du ballon (e.g., passe, en vol, reception et course) 
- "Passe" correspond au nombre de passe effectué au l'instant T.
=> Ces données nécessite un léger traitement pour être exactement "clean" comme les données V1
