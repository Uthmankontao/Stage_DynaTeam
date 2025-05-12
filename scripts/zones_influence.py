import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from matplotlib.patches import Circle
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

# Fonction pour vérifier si une ligne de passe traverse une zone d'influence
def line_intersects_circle(line_start, line_end, circle_center, radius):
    """
    Vérifie si une ligne (passe) coupe un cercle (zone d'influence)
    
    :param line_start: Point de départ de la ligne (x1, y1)
    :param line_end: Point d'arrivée de la ligne (x2, y2)
    :param circle_center: Centre du cercle (x, y)
    :param radius: Rayon du cercle
    :return: True si la ligne coupe le cercle, False sinon
    """
    # Convertir en numpy arrays
    line_start = np.array(line_start)
    line_end = np.array(line_end)
    circle_center = np.array(circle_center)
    
    # Vecteur de la ligne
    d = line_end - line_start
    line_length = np.linalg.norm(d)
    
    # Direction normalisée
    d_normalized = d / line_length if line_length > 0 else np.array([0, 0])
    
    # Vecteur du point de départ au centre du cercle
    f = line_start - circle_center
    
    # Coefficients de l'équation quadratique
    a = np.dot(d_normalized, d_normalized)
    b = 2 * np.dot(f, d_normalized)
    c = np.dot(f, f) - radius**2
    
    discriminant = b**2 - 4 * a * c
    
    # Pas d'intersection
    if discriminant < 0:
        return False
    
    # Calculer les solutions
    discriminant = np.sqrt(discriminant)
    t1 = (-b - discriminant) / (2 * a)
    t2 = (-b + discriminant) / (2 * a)
    
    # Vérifier si l'intersection est sur le segment de ligne
    if (0 <= t1 <= line_length) or (0 <= t2 <= line_length):
        return True
    
    return False

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

# Ajouter les zones d'influence à la légende
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Attaquant'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Défenseur'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='white', markersize=8, label='Ballon'),
    Line2D([0], [0], color='orange', lw=2, label='Passes valides'),
    Line2D([0], [0], color='red', lw=2, linestyle='--', label='Passes bloquées'),
    Line2D([0], [0], color='white', lw=1, linestyle='--', label='Pression défensive'),
    plt.Circle((0, 0), 0.5, color='blue', alpha=0.2, label='Zone d\'influence')
]
ax.legend(handles=legend_elements, loc='upper left')

passes_lines, blocked_passes_lines, secondary_passes_lines, pressure_lines, influence_zones = [], [], [], [], []

# Configuration des zones d'influence des défenseurs
INFLUENCE_RADIUS = 3.5  # Rayon de la zone d'influence en mètres

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
    global passes_lines, blocked_passes_lines, secondary_passes_lines, pressure_lines, influence_zones, text_labels
    for line in passes_lines + blocked_passes_lines + secondary_passes_lines + pressure_lines:
        if line in ax.get_lines() or hasattr(line, 'remove'):
            line.remove()
    for zone in influence_zones:
        zone.remove()
    for txt in text_labels:
        txt.remove()
    passes_lines.clear()
    blocked_passes_lines.clear()
    secondary_passes_lines.clear()
    pressure_lines.clear()
    influence_zones.clear()
    text_labels.clear()
    
    frame_data = df_possession_1[df_possession_1['Time'] == t]
    ball_data = df_possession_1_ball[df_possession_1_ball['Time'] == t]
    if frame_data.empty:
        return []

    possession_id = int(frame_data['Possession'].iloc[0])
    cote = get_cote_for_possession(possession_id)

    player_pos = {}  # dictionnaire pour stocker les positions des joueurs
    for p in players:
        pdata = frame_data[frame_data['Player'] == p]
        if not pdata.empty:
            x, y = pdata[['X', 'Y']].values[0]
            scatters[p].set_offsets([[x, y]])
            player_pos[p] = (x, y)
            txt = ax.text(x, y + 0.8, str(p), fontsize=9, ha='center', color='white',
                          bbox=dict(facecolor='black', alpha=0.5, boxstyle='circle'))
            text_labels.append(txt)
        else:
            scatters[p].set_offsets(np.empty((0, 2)))

    if not ball_data.empty:
        bx, by = ball_data[['X', 'Y']].values[0]
        ball_scatter.set_offsets([[bx, by]])
    
    # Créer des zones d'influence pour les défenseurs
    defender_zones = {}
    for d in def_players:
        if d in player_pos:
            dpos = player_pos[d]
            # Créer un cercle représentant la zone d'influence
            circle = Circle(dpos, INFLUENCE_RADIUS, color='blue', alpha=0.2, fill=True)
            ax.add_patch(circle)
            influence_zones.append(circle)
            defender_zones[d] = (dpos, INFLUENCE_RADIUS)

    # Passes depuis porteur et identification des receveurs directs
    direct_receivers = []  # liste pour stocker les receveurs directs potentiels
    carrier = frame_data[frame_data['Carrier']]
    
    if not carrier.empty:
        cid = carrier['Player'].iloc[0]
        cpos = player_pos.get(cid)
        
        if cpos:  # vérifier que la position du porteur est disponible
            for p, pos in player_pos.items():
                if p != cid and player_teams[p] == 'Att':
                    dist = np.linalg.norm(np.array(cpos) - np.array(pos))
                    if dist < dynamic_threshold(cpos[0]) and is_backward_pass(cpos, pos, cote):
                        # Vérifier si la passe traverse une zone d'influence d'un défenseur
                        pass_blocked = False
                        for _, (def_pos, radius) in defender_zones.items():
                            if line_intersects_circle(cpos, pos, def_pos, radius):
                                pass_blocked = True
                                break
                        
                        if pass_blocked:
                            # Tracer les passes bloquées en rouge pointillé
                            arrow = ax.annotate("", 
                                     xy=(pos[0], pos[1]),           # pointe de la flèche
                                     xytext=(cpos[0], cpos[1]),     # base de la flèche
                                     arrowprops=dict(arrowstyle="->", color="red", 
                                                    lw=2, alpha=0.8, linestyle='--'))
                            blocked_passes_lines.append(arrow)
                        else:
                            # Tracer les passes directes valides
                            arrow = ax.annotate("", 
                                     xy=(pos[0], pos[1]),           # pointe de la flèche
                                     xytext=(cpos[0], cpos[1]),     # base de la flèche
                                     arrowprops=dict(arrowstyle="->", color="orange", 
                                                    lw=2, alpha=0.8))
                            passes_lines.append(arrow)
                            direct_receivers.append(p)  # Ajouter ce joueur comme receveur direct
                        
                        txt = ax.text((pos[0] + cpos[0])/2, (pos[1] + cpos[1])/2,
                              f"{dist:.1f}", fontsize=6, color='white')
                        text_labels.append(txt)

            # Tracer les passes secondaires à partir des receveurs directs
            for receiver in direct_receivers:
                receiver_pos = player_pos.get(receiver)
                
                for p, pos in player_pos.items():
                    if p != receiver and p != cid and player_teams[p] == 'Att':
                        dist = np.linalg.norm(np.array(receiver_pos) - np.array(pos))
                        if dist < dynamic_threshold(receiver_pos[0]) and is_backward_pass(receiver_pos, pos, cote):
                            # Vérifier si la passe secondaire traverse une zone d'influence d'un défenseur
                            pass_blocked = False
                            for _, (def_pos, radius) in defender_zones.items():
                                if line_intersects_circle(receiver_pos, pos, def_pos, radius):
                                    pass_blocked = True
                                    break
                            
                            if pass_blocked:
                                # Tracer les passes secondaires bloquées
                                arrow = ax.annotate("", 
                                         xy=(pos[0], pos[1]),            # pointe de la flèche
                                         xytext=(receiver_pos[0], receiver_pos[1]),  # base de la flèche
                                         arrowprops=dict(arrowstyle="->", color="red", 
                                                        lw=1.5, alpha=0.7, linestyle='--'))
                                blocked_passes_lines.append(arrow)
                            else:
                                # Tracer les passes secondaires valides
                                arrow = ax.annotate("", 
                                         xy=(pos[0], pos[1]),            # pointe de la flèche
                                         xytext=(receiver_pos[0], receiver_pos[1]),  # base de la flèche
                                         arrowprops=dict(arrowstyle="->", color="yellow", 
                                                        lw=1.5, alpha=0.7))
                                secondary_passes_lines.append(arrow)
                            
                            txt = ax.text((pos[0] + receiver_pos[0])/2, (pos[1] + receiver_pos[1])/2,
                                  f"{dist:.1f}", fontsize=6, color='white')
                            text_labels.append(txt)

    # Lien de pression valide uniquement si le défenseur est devant
    for d in def_players:
        if d not in player_pos:
            continue
        dpos = np.array(player_pos[d])
        for a in att_players:
            if a in player_pos:
                apos = np.array(player_pos[a])
                dist = np.linalg.norm(dpos - apos)
                if dist < 7 and is_pressure_valid(dpos, apos, cote):
                    line = ax.plot([dpos[0], apos[0]], [dpos[1], apos[1]],
                                   color='white', linestyle='--', linewidth=1, alpha=0.7)[0]
                    pressure_lines.append(line)
                    txt = ax.text((dpos[0] + apos[0])/2, (dpos[1] + apos[1])/2,
                                  f"{dist:.1f}", fontsize=6, color='white')
                    text_labels.append(txt)

    ax.set_title(f'Temps : {t:.2f}s – Côté : {cote}')
    return (list(scatters.values()) + [ball_scatter] + passes_lines + blocked_passes_lines + 
            secondary_passes_lines + pressure_lines + influence_zones + text_labels)

# Lancer l'animation
ani = FuncAnimation(fig, update, frames=times, init_func=init, interval=40, blit=True)
plt.tight_layout()
plt.show()
#ani.save("animation_rugby_avec_zones_influence.gif", writer="pillow", fps=15)
#print("Animation avec zones d'influence des défenseurs enregistrée.")