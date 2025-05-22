Ce script Python permet de visualiser dynamiquement les interactions entre joueurs lors d'une possession de balle à partir de données de tracking GPS.

Fonctionnement général :
------------------------
1. Chargement des données :
   - Les données de tracking des joueurs et de la balle sont chargées depuis un fichier CSV.
   - Les informations sur les joueurs (équipe, ID, etc.) sont également chargées.

2. Modes d'utilisation :
   - Mode 1 : Visualiser le graphe à un instant précis d'une possession.
   - Mode 2 : Visualiser l'évolution du graphe tout au long d'une possession (un graphe toutes les 10 frames environ).

3. Construction du graphe :
   - À chaque instant, un graphe orienté est construit :
     - Les joueurs sont ajoutés comme nœuds, avec leur position et leur équipe.
     - Le porteur de balle est identifié (joueur attaquant le plus proche de la balle).
     - Les passes possibles sont ajoutées comme arêtes vertes (avec flèche) depuis le porteur de balle vers les coéquipiers proches et devant lui.
     - Les pressions défensives sont ajoutées comme arêtes grises en pointillé entre défenseurs et attaquants proches.

4. Visualisation :
   - Les graphes sont affichés avec matplotlib :
     - Les joueurs attaquants sont en rouge, les défenseurs en bleu.
     - Les passes sont en vert, les pressions en gris pointillé.
     - Les distances des pressions sont affichées sur les arêtes correspondantes.

Utilisation :
-------------
- Lancer le script.
- Choisir le mode (1 ou 2).
- Saisir le numéro de la possession à analyser.
- Selon le mode, saisir l'instant à visualiser ou choisir parmi les graphes générés.

Remarques :
-----------
- Les fichiers CSV doivent être présents aux chemins indiqués dans le script.
- Le script utilise les bibliothèques pandas, numpy, networkx et matplotlib.



Générateur de Dataset de Graphes à partir de Données GPS Sportives
Ce script Python permet de transformer des données brutes de tracking GPS et d’événements sportifs en une série de graphes (au format GEXF) pour chaque possession de balle, à différents instants du match. Il génère également un fichier CSV récapitulant les métadonnées de chaque graphe.

Fonctionnement général
Chargement des données

df : positions GPS des joueurs à chaque instant.
df_seq : séquences d’événements (début/fin de possession, résultat, etc.).
df_infos : informations sur les joueurs (équipe, ID...).
Création du dossier de sortie
Les graphes générés sont stockés dans le dossier graph_dataset.

Boucle sur chaque possession
Pour chaque possession unique :

On filtre les données GPS correspondantes.
On récupère les instants de temps (tous les 10 frames par défaut).
On cherche le résultat de la possession (essai ou non).
Génération des graphes
Pour chaque instant t sélectionné :

On construit un graphe représentant la situation de jeu à cet instant (voir fonction construire_graphe).
On sauvegarde le graphe au format .gexf.
On vérifie s’il y a une passe réelle dans le graphe.
On ajoute les informations du graphe à la liste des métadonnées.
Export des métadonnées
À la fin, toutes les informations sont sauvegardées dans graph_labels.csv.

À quoi sert chaque fichier généré ?
Fichiers .gexf : chaque fichier représente un graphe à un instant donné d’une possession (peut être visualisé avec Gephi ou NetworkX).
graph_labels.csv : contient pour chaque graphe :
le chemin du fichier,
l’instant de temps,
l’ID de la possession,
le label (1 = essai, 0 = autre),
la présence d’une passe réelle.
Fonction clé : construire_graphe
Cette fonction crée un graphe orienté où :

Les nœuds sont les joueurs (avec position et équipe).
Les arêtes représentent les passes possibles, les passes réelles, et les pressions défensives.
Utilisation
Place les fichiers CSV bruts dans le dossier attendu.
Lance le script graphe_dataset_builder.py.
Les graphes et le fichier de labels seront générés dans le dossier graph_dataset.



Ce fichier est un graphe au format GEXF (Graph Exchange XML Format), généré par NetworkX. Il représente un réseau de joueurs (nœuds) et leurs interactions (arêtes) dans un contexte de données, probablement lié à un match ou une simulation sportive.

## Structure du fichier

- **Nodes (nœuds)** : Chaque nœud représente un joueur, identifié par un `id` et un `label`. Les attributs associés à chaque joueur sont :
  - `team` : l'équipe du joueur (`Att` pour attaquant, `Def` pour défenseur)
  - `x`, `y` : coordonnées spatiales du joueur

- **Edges (arêtes)** : Chaque arête représente une interaction entre deux joueurs :
  - `type` : le type d'interaction (`pression` ou `passe`)
  - `label` : valeur associée à l'interaction (ex : intensité de la pression)
  - Attribut `real` (pour les passes) : indique si la passe est réelle (`true` ou `false`)

## Utilisation

Ce fichier peut être ouvert avec des outils de visualisation de graphes compatibles GEXF (Gephi, NetworkX, etc.) pour analyser les relations et positions des joueurs.

## Exemple d'interprétation

- Les nœuds avec `team="Att"` sont les attaquants, ceux avec `team="Def"` sont les défenseurs.
- Les arêtes de type `pression` indiquent une pression exercée par un défenseur sur un attaquant, avec une intensité (`label`).
- Les arêtes de type `passe` indiquent une tentative de passe entre joueurs, avec un attribut `real` pour préciser si la passe a été réalisée.

## Génération

Auteur : Ousmane Kontao