import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
import pitch

# Charge les données
df = pd.read_csv('C:/Users/Ousmane Kontao/Desktop/Projet_Data🏀/data_brute/tracking GPS - pedagogie emergente.csv', low_memory=False)

# Filter data for possession = 1 and exclude the ball.
df_possession_1 = df[(df['Possession'] == 1) & (df['GPS'] != 'Ball')].copy()

# Filter data for possession = 1 for the ball.
df_possession_1_ball = df[(df['Possession'] == 1) & (df['GPS'] == 'Ball')].copy()

# Ajoute une colonne 'Carrier' et l'initialise à False.
df_possession_1['Carrier'] = False  

# La liste des numéros des joueurs, d'abord les attaquants, puis les defenseurs et enfin tout le monde.
att_players = [1, 2, 3, 4, 5, 6]
def_players = [10, 11, 12, 13, 14, 15]
players = [1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15]

# Met à jour la colonne 'Carrier'.
for i in df_possession_1_ball.iterrows():
    row = i[1]
    if row['Player'] in att_players:
        time = row['Time']
        player = row['Player']
        df_possession_1.loc[(df_possession_1['Time'] == time) & (df_possession_1['Player'] == player), 'Carrier'] = True

# On créer un dictionnaire qui associe chaque joueur a son équipe.
player_teams = {}
for player in players:
    team = 'Att' if player <= 6 else 'Def'
    player_teams[player] = team

# On récupère les toutes les valeurs uniques de la colonne 'Time'.
times = df_possession_1['Time'].unique()

# Création de la figure.
fig, ax = plt.subplots(figsize=(12, 8))

# Dessiner le terrain
pitch.draw_rugby_field(ax)

ax.set_xlim(-15, 50)
ax.set_ylim(-40, 10)
ax.set_title('Graphe dynamique des joueurs et des possibilités de passes.')

# On crée un dictionnaire vide scatters qui va stocker les objets scatter plot pour chaque joueur.
scatters = {}

# Parcourt la liste des joueurs et pour chaque joueur, récupère son équipe à partie de player_teams,
# attribue la couleur rouge pour les attaquants ('Att') et bleue pour les défenseurs ('Def'),
# crée un scatter plot vide ([], [] pour les coordonnées x et y) et enfin,
# stocke ce scatter plot dans le dictionnaire avec le numéro du joueur comme clé.

for player in players:
    team = player_teams[player]
    color = 'red' if team == 'Att' else 'blue'
    scatters[player] = ax.scatter([], [], s=100, color=color)

# On crée un scatter_plot vide pour le ballon.
ball_scatter = ax.scatter([], [], s=50, color='green', zorder=5)

# On crée la légende, on se sert de Line2D pour personnaliser les éléments.
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Att'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Def'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Ballon'),
    Line2D([0], [0], color='orange', lw=2, label='Passes possibles')
]

# Ajout de la légende.
team_legend = ax.legend(handles=legend_elements, loc='upper left')
ax.add_artist(team_legend)

# Calcul de la distance euclidienne
def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# Fonction qui déterine si un joueur est a porté de passe
def player_in_range(p1, p2):
    return distance(p1, p2) < 15 and p1[0] > p2[0]

# Liste pour stocker les lignes de passes
passes_lines = []

def init():
    # Initialise l'animation.
    for player in players:
        scatters[player].set_offsets(np.empty((0, 2)))
    ball_scatter.set_offsets(np.empty((0, 2)))
    
    # Effacer toutes les lignes de passes existantes.
    global passes_lines
    while passes_lines:
        line = passes_lines.pop()
        if line in ax.get_lines():
            line.remove()
    
    return list(scatters.values()) + [ball_scatter]

def update(time):
    frame_data = df_possession_1[df_possession_1['Time'] == time]
    
    # Effacer toutes les lignes de passes existantes
    global passes_lines
    while passes_lines:
        line = passes_lines.pop()
        if line in ax.get_lines():
            line.remove()
    
    # On met a jour les positions des joueurs.
    player_positions = {}
    for player in players:
        player_frame_data = frame_data[frame_data['Player'] == player]
        if not player_frame_data.empty:
            x = player_frame_data['X'].values[0]
            y = player_frame_data['Y'].values[0]
            player_positions[player] = (x, y)
            scatters[player].set_offsets([[x, y]])
        else:
            scatters[player].set_offsets(np.empty((0, 2)))
    
    # On met a jour les positions du ballon.
    ball_frame_data = df_possession_1_ball[df_possession_1_ball['Time'] == time]
    if not ball_frame_data.empty:
        ball_x = ball_frame_data['X'].values[0]
        ball_y = ball_frame_data['Y'].values[0]
        ball_scatter.set_offsets([[ball_x, ball_y]])
    else:
        ball_scatter.set_offsets(np.empty((0, 2)))
    
    # Trouve le porteur de balle a cet instant.
    carrier_data = frame_data[frame_data['Carrier'] == True]
    
    if not carrier_data.empty:
        carrier_player = carrier_data['Player'].iloc[0]
        carrier_team = player_teams[carrier_player]
        
        if carrier_player in player_positions:
            carrier_pos = player_positions[carrier_player]
            
            # On trouve les coéquipiers qui sont a porté.
            for player, pos in player_positions.items():
                if player != carrier_player and player_teams[player] == carrier_team:
                    if player_in_range(carrier_pos, pos):
                        # On déssine un vecteur entre les deux.
                        line = ax.plot([carrier_pos[0], pos[0]], [carrier_pos[1], pos[1]], 
                                      color='orange', linewidth=2, alpha=0.7, zorder=1)[0]
                        passes_lines.append(line)
    
    ax.set_title(f'Player Positions - Time: {time:.2f}s (Red = Att, Blue = Def, Green = Ball)')
    
    return list(scatters.values()) + [ball_scatter] + passes_lines

# Création de l'animation
ani = FuncAnimation(
    fig,
    update,
    frames=times,
    init_func=init,
    interval=10,
    blit=True,
    repeat=True
)

plt.tight_layout()
plt.show()

