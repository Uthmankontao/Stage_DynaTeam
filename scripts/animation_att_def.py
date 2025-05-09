import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from build_graph import construire_graphe
import networkx as nx
from pitch import draw_rugby_field


# Chargement des données
df = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/tracking GPS - pedagogie emergente.csv", low_memory=False)
df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/event sequencage - pedagogie emergente.csv", sep=';')
df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/informations - pedagogie emergente.csv", sep=';')

# Identifier les joueurs
att_players = df_infos[df_infos['Team'] == 'Att']['ID'].tolist()
def_players = df_infos[df_infos['Team'] == 'Def']['ID'].tolist()
players = att_players + def_players
player_teams = {p: 'Att' if p in att_players else 'Def' for p in players}

# Filtrer les données pour une seule possession (ex. : 1)
df_possession_1 = df[(df['Possession'] == 1) & (df['GPS'] != 'Ball')].copy()
df_possession_1_ball = df[(df['Possession'] == 1) & (df['GPS'] == 'Ball')].copy()
df_possession_1['Carrier'] = False
df_seq_1 = df_seq[df_seq['Possession'] == 1]

# Marquer les porteurs de balle
for _, row in df_possession_1_ball.iterrows():
    if row['Player'] in att_players:
        t, p = row['Time'], row['Player']
        df_possession_1.loc[(df_possession_1['Time'] == t) & (df_possession_1['Player'] == p), 'Carrier'] = True

# Fonctions utiles
def dynamic_threshold(x):
    return max(8, 18 - 0.2 * x)

def is_backward_pass(cpos, pos, cote):
    return pos[0] > cpos[0] if cote == "DROITE" else pos[0] < cpos[0]

def is_pressure_valid(dpos, apos, cote):
    return dpos[0] < apos[0] if cote == "DROITE" else dpos[0] > apos[0]

def get_cote_for_possession(possession_id):
    row = df_seq[df_seq["Possession"] == possession_id]
    if not row.empty:
        return row["Cote"].iloc[0]
    return "DROITE"

# Time
times = df_possession_1['Time'].unique()

# Graphique
fig, ax = plt.subplots(figsize=(12, 8))
draw_rugby_field(ax)
ax.set_xlim(-15, 50)
ax.set_ylim(-40, 10)
scatters = {p: ax.scatter([], [], s=100, color=('red' if p in att_players else 'blue')) for p in players}
ball_scatter = ax.scatter([], [], s=50, color='white', zorder=5)
text_labels = []

"""legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Att'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Def'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Ballon'),
    Line2D([0], [0], color='orange', lw=2, label='Passes possibles'),
    Line2D([0], [0], color='white', lw=1, linestyle='--', label='Pression défensive')
]"""
#ax.legend(handles=legend_elements, loc='upper left')

passes_lines, pressure_lines = [], []

def init():
    """
    Initialise les positions des joueurs et du ballon pour l'animation.
    Vide les lignes de passes et de pression.
    """
    for s in scatters.values():
        s.set_offsets(np.empty((0, 2)))
    ball_scatter.set_offsets(np.empty((0, 2)))
    return list(scatters.values()) + [ball_scatter]

def update(t):
    """
    Met à jour les positions des joueurs et le ballon pour chaque frame de l'animation.
    Affiche les passes possibles et la pression défensive.
    
    :param t: Temps actuel de l'animation.
    :return: Liste des objets à mettre à jour dans l'animation.
    """
    # Effacer les lignes de passes et de pression existantes
    global passes_lines, pressure_lines, text_labels # pour accéder aux listes globales
    for line in passes_lines + pressure_lines:
        line.remove()
    for txt in text_labels:
        txt.remove()
    passes_lines.clear()
    pressure_lines.clear()
    text_labels.clear()
    frame_data = df_possession_1[df_possession_1['Time'] == t]
    ball_data = df_possession_1_ball[df_possession_1_ball['Time'] == t]
    if frame_data.empty:
        return []

    possession_id = int(frame_data['Possession'].iloc[0])
    cote = get_cote_for_possession(possession_id)

    player_pos = {} # dictionnaire pour stocker les positions des joueurs
    for p in players: # on parcourt tous les joueurs
        # On récupère les données du joueur pour le temps t
        pdata = frame_data[frame_data['Player'] == p] # données du joueur p
        # On vérifie si le joueur est présent dans les données
        if not pdata.empty: # si le joueur est présent
            # On récupère les coordonnées X et Y du joueur
            x, y = pdata[['X', 'Y']].values[0] # coordonnées du joueur p
            # On met à jour la position du joueur dans le dictionnaire
            scatters[p].set_offsets([[x, y]]) # on met à jour la position du scatter plot
            # On ajoute le joueur au dictionnaire player_pos
            player_pos[p] = (x, y) # on ajoute le joueur au dictionnaire player_pos
            # On vérifie si le joueur est porteur de balle
            txt = ax.text(x, y + 0.8, str(p), fontsize=9, ha='center', color='white',
                          bbox=dict(facecolor='black', alpha=0.5, boxstyle='circle'))
            text_labels.append(txt)
        else: # si le joueur n'est pas présent, on vide le scatter plot
            # On vide le scatter plot du joueur p
            scatters[p].set_offsets(np.empty((0, 2))) # on vide le scatter plot du joueur p
            # On vide la position du joueur p dans le dictionnaire player_pos

    if not ball_data.empty:
        bx, by = ball_data[['X', 'Y']].values[0]
        ball_scatter.set_offsets([[bx, by]])

    # Passes en arrière depuis porteur
    carrier = frame_data[frame_data['Carrier']] # on récupère le porteur de balle
    # On vérifie si le porteur de balle est présent
    if not carrier.empty:# si le porteur de balle est présent
        # On récupère l'identifiant du porteur de balle
        cid = carrier['Player'].iloc[0] # identifiant du porteur de balle 
        # On vérifie si le porteur de balle est présent dans les données
        cpos = player_pos.get(cid) # position du porteur de balle
        for p, pos in player_pos.items(): # on parcourt tous les joueurs
            # On vérifie si le joueur est différent du porteur de balle
            if p != cid and player_teams[p] == 'Att': # si le joueur est un attaquant
                # On vérifie si le joueur est présent dans les données
                dist = np.linalg.norm(np.array(cpos) - np.array(pos)) # distance entre le porteur de balle et le joueur
                # On vérifie si la distance est inférieure au seuil dynamique
                if dist < dynamic_threshold(cpos[0]) and is_backward_pass(cpos, pos, cote):
                    # On dessine la ligne de passe
                    # On dessine la ligne de passe entre le porteur de balle et le joueur
                    line = ax.plot([cpos[0], pos[0]], [cpos[1], pos[1]], color='orange', linewidth=2, alpha=0.8)[0] 
                    # On ajoute la ligne de passe à la liste des lignes de passes
                    passes_lines.append(line) 

    # Lien de pression valide uniquement si le défenseur est devant
    for d in def_players: # on parcourt tous les défenseurs
        # On vérifie si le défenseur est présent dans les données
        if d not in player_pos:
            continue
        # On récupère la position du défenseur
        # On vérifie si le défenseur est présent dans les données
        dpos = np.array(player_pos[d])
        for a in att_players:
            if a in player_pos: # si le joueur est un attaquant
                # On récupère la position de l'attaquant
                apos = np.array(player_pos[a])
                # On vérifie si la distance entre le défenseur et l'attaquant est inférieure au seuil
                dist = np.linalg.norm(dpos - apos)
                if dist < 7 and is_pressure_valid(dpos, apos, cote):
                    # On dessine la ligne de pression entre le défenseur et l'attaquant
                    line = ax.plot([dpos[0], apos[0]], [dpos[1], apos[1]],
                                   color='white', linestyle='--', linewidth=1, alpha=0.7)[0]
                    pressure_lines.append(line)
                    txt = ax.text((dpos[0] + apos[0])/2, (dpos[1] + apos[1])/2,
                                  f"{dist:.1f}", fontsize=6, color='white')
                    text_labels.append(txt) # on ajoute le texte à la liste des textes

    ax.set_title(f'Temps : {t:.2f}s – Côté : {cote}')
    return list(scatters.values()) + [ball_scatter] + passes_lines + pressure_lines + text_labels

# Lancer l’animation
#ani = FuncAnimation(fig, update, frames=times, init_func=init, interval=40, blit=True)
#ani.save("animation_rugby.gif", writer="pillow", fps=15)
#print("Animation avec filtre de pression cohérent enregistrée.")


