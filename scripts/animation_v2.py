import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
from tools.pitch import draw_rugby_field
from tools.gradient import calculate_gradient
from tools.fonctions_utiles import *


# Chargement des données
df_players = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/AGEN_PRESCRIPTIF.csv")
df_ball = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/AGEN_BALL_PRESCRIPTIF.csv")
df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/sequencage/agen_prescriptif.csv", sep=';')
df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/info_GPS/agen_prescriptif.csv", sep=';')

# Tri des df players et ball
df_players_sorted = df_players.sort_values(['Possession', 'GPS', 'Time']).copy()
df_ball_sorted = df_ball.sort_values(['Possession', 'Time']).copy()
 
# Filtrer les données pour une seule possession
df_possession_1 = df_players[(df_players['Possession'] == 1)].copy()
df_possession_1_ball = df_ball[(df_ball['Possession'] == 1)].copy()
df_seq_1 = df_seq[df_seq['Possession'] == 1].copy()

# Ajout des colonnes
df_possession_1['Carrier'] = False
df_possession_1['Player'] = 0
df_possession_1_ball['Player'] = 0
df_possession_1_ball['state'] = ''

# Correspondance GPS players
df_possession_1 = cores_GPS_player(df_possession_1, df_infos)
df_possession_1_ball = cores_GPS_player(df_possession_1_ball, df_infos)

# Mettre a jour l'état de la balle
df_possession_1_ball = maj_state(df_possession_1_ball, df_seq_1)

# Identifier les joueurs
att_players = df_infos[df_infos['Team'] == 'Att']['player'].tolist()
def_players = df_infos[df_infos['Team'] == 'Def']['player'].tolist()
def_players = list(map(lambda x: x + 10, def_players))
players = att_players + def_players
player_teams = {p: 'Att' if p in att_players else 'Def' for p in players}

# Calculer les gradients pour tous les joueurs
df_possession_1 = calculate_gradient(df_possession_1)

# Marquer les porteurs de balle
for _, row in df_possession_1_ball.iterrows():
    if row['Player'] in att_players:
        t, p = row['Time'], row['Player']
        df_possession_1.loc[(df_possession_1['Time'] == t) & (df_possession_1['Player'] == p), 'Carrier'] = True

times = df_possession_1['Time'].unique()

# Définition des couleurs pour la balle selon différents critères
BALL_COLORS = {
    'portée': 'white',
    'avc': 'gold',           # avant contacte
    'apc': 'purple',           # après contacte
    'pied' : 'cyan'
}

def determine_ball_color(ball_state):
    """Détermine la couleur de la balle selon son état"""
    if ball_state == 'portée':
        return BALL_COLORS['portée']
    elif ball_state == 'avc':
        return BALL_COLORS['avc']
    elif ball_state == 'apc':
        return BALL_COLORS['apc']
    elif ball_state == 'pied':  # Correction : 'pied' au lieu de 'Pied'
        return BALL_COLORS['pied']
    else:
        return BALL_COLORS['portée']

def point_in_ellipse(point, center, width, height, angle):
    """
    Vérifie si un point est à l'intérieur d'une ellipse
    
    Args:
        point: Point à tester (x, y)
        center: Centre de l'ellipse (x, y)
        width: Largeur de l'ellipse
        height: Hauteur de l'ellipse
        angle: Angle de rotation en radians
    
    Returns:
        bool: True si le point est dans l'ellipse
    """
    # Translater le point vers l'origine
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    
    # Appliquer la rotation inverse
    cos_angle = np.cos(-angle)
    sin_angle = np.sin(-angle)
    
    x_rot = dx * cos_angle - dy * sin_angle
    y_rot = dx * sin_angle + dy * cos_angle
    
    # Tester si le point est dans l'ellipse normalisée
    a = width / 2
    b = height / 2
    
    return (x_rot / a) ** 2 + (y_rot / b) ** 2 <= 1

# Graphique
fig, ax = plt.subplots(figsize=(12, 8))
draw_rugby_field(ax)
ax.set_xlim(-15, 50)
ax.set_ylim(-40, 10)
scatters = {p: ax.scatter([], [], s=100, color=('red' if p in att_players else 'blue')) for p in players}
ball_scatter = ax.scatter([], [], s=80, color='white', zorder=5, edgecolors='black', linewidth=2)
text_labels = []

passes_lines, blocked_passes_lines, secondary_passes_lines, pressure_lines, influence_zones = [], [], [], [], []

# Configuration de base des zones d'influence
BASE_INFLUENCE_RADIUS = 1.5  # Rayon de base en mètres
MAX_SPEED_EFFECT = 2.0       # Effet max de la vitesse sur la taille
SPEED_SCALING = 0.5          # Facteur de mise à l'échelle pour la vitesse
OFFSET_SCALING = 0.4         # Facteur de mise à l'échelle pour le décalage du centre

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
    # Effacer les éléments existants
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
    cote = get_cote_for_possession(possession_id, df_seq_1)

    player_pos = {}  # dictionnaire pour stocker les positions des joueurs
    player_gradients = {}  # dictionnaire pour stocker les gradients des joueurs
    
    for p in players:
        pdata = frame_data[frame_data['Player'] == p]
        if not pdata.empty:
            x, y = pdata[['X', 'Y']].values[0]
            scatters[p].set_offsets([[x, y]])
            player_pos[p] = (x, y)
            
            # Récupérer les informations de gradient
            grad_magnitude = pdata['gradient_magnitude'].values[0]
            grad_angle = pdata['gradient_angle'].values[0]
            player_gradients[p] = (grad_magnitude, grad_angle)
            
            txt = ax.text(x, y + 0.8, str(p), fontsize=9, ha='center', color='white',
                          bbox=dict(facecolor='black', alpha=0.5, boxstyle='circle'))
            text_labels.append(txt)
        else:
            scatters[p].set_offsets(np.empty((0, 2)))
    
    ball_color = 'white'  # Couleur par défaut
    
    if not ball_data.empty:
        bx, by = ball_data[['X', 'Y']].values[0]
        # Correction : récupérer correctement l'état de la balle
        ball_state = ball_data['state'].iloc[0]  # Utiliser .iloc[0] pour récupérer la valeur
        ball_scatter.set_offsets([[bx, by]])
        
        # Déterminer la couleur de la balle selon la situation
        ball_color = determine_ball_color(ball_state)
        ball_scatter.set_color(ball_color)
    else:
        # Si pas de données de balle, cacher le scatter
        ball_scatter.set_offsets(np.empty((0, 2)))
    
    # Trouver le porteur de balle
    carrier = frame_data[frame_data['Carrier']]
    
    # Créer des zones d'influence elliptiques pour les défenseurs
    defender_zones = {}
    for d in def_players:
        if d in player_pos and d in player_gradients:
            dpos = player_pos[d]
            speed, angle = player_gradients[d]
            
            # Limiter la vitesse pour éviter des ellipses trop grandes
            speed = min(speed, 20)  
            
            # Calculer les dimensions de l'ellipse en fonction de la vitesse
            # Plus le joueur est rapide, plus l'ellipse est allongée dans la direction du mouvement
            width = BASE_INFLUENCE_RADIUS * (1 + SPEED_SCALING * min(speed, MAX_SPEED_EFFECT))
            height = BASE_INFLUENCE_RADIUS * (1 - 0.3 * min(speed, MAX_SPEED_EFFECT/2))  # Légèrement réduit perpendiculairement
            
            # Calculer le décalage du centre de l'ellipse dans la direction du mouvement
            offset_factor = OFFSET_SCALING * min(speed, MAX_SPEED_EFFECT)  # Le décalage augmente avec la vitesse
            offset_x = offset_factor * np.cos(angle)
            offset_y = offset_factor * np.sin(angle)
            
            # Calculer le centre décalé de l'ellipse (devant le joueur)
            ellipse_center = (dpos[0] + offset_x, dpos[1] + offset_y)
            
            # Créer l'ellipse avec l'orientation dans la direction du mouvement
            ellipse = Ellipse(ellipse_center, width=width, height=height, 
                             angle=np.degrees(angle), color='blue', alpha=0.2, fill=True)
            ax.add_patch(ellipse)
            influence_zones.append(ellipse)
            
            # Stocker les paramètres de l'ellipse pour l'intersection
            defender_zones[d] = (ellipse_center, width, height, angle)
            
            # Ajouter du texte pour la vitesse
            if speed > 0.5:  # Ne montrer que si la vitesse est significative
                txt = ax.text(dpos[0], dpos[1] - 1.2, f"{speed * 3.6:.1f} km/h", 
                             fontsize=7, ha='center', color='cyan')
                text_labels.append(txt)

    # Créer des zones d'influence elliptiques pour les attaquants
    stricker_zones = {}
    for d in att_players:
        if d in player_pos and d in player_gradients:
            dpos = player_pos[d]
            speed, angle = player_gradients[d]
            
            # Limiter la vitesse pour éviter des ellipses trop grandes
            speed = min(speed, 20)  
            
            # Calculer les dimensions de l'ellipse en fonction de la vitesse
            # Plus le joueur est rapide, plus l'ellipse est allongée dans la direction du mouvement
            width = BASE_INFLUENCE_RADIUS * (1 + SPEED_SCALING * min(speed, MAX_SPEED_EFFECT))
            height = BASE_INFLUENCE_RADIUS * (1 - 0.3 * min(speed, MAX_SPEED_EFFECT/2))  # Légèrement réduit perpendiculairement
            
            # Calculer le décalage du centre de l'ellipse dans la direction du mouvement
            offset_factor = OFFSET_SCALING * min(speed, MAX_SPEED_EFFECT)  # Le décalage augmente avec la vitesse
            offset_x = offset_factor * np.cos(angle)
            offset_y = offset_factor * np.sin(angle)
            
            # Calculer le centre décalé de l'ellipse (devant le joueur)
            ellipse_center = (dpos[0] + offset_x, dpos[1] + offset_y)
            
            # Créer l'ellipse avec l'orientation dans la direction du mouvement
            ellipse = Ellipse(ellipse_center, width=width, height=height, 
                             angle=np.degrees(angle), color='red', alpha=0.2, fill=True)
            ax.add_patch(ellipse)
            influence_zones.append(ellipse)
            
            # Stocker les paramètres de l'ellipse pour l'intersection
            stricker_zones[d] = (ellipse_center, width, height, angle)
            
            # Ajouter du texte pour la vitesse
            if speed > 0.5:  # Ne montrer que si la vitesse est significative
                txt = ax.text(dpos[0], dpos[1] - 1.2, f"{speed * 3.6:.1f} km/h", 
                             fontsize=7, ha='center', color='cyan')
                text_labels.append(txt)

    # Déterminer la couleur de la balle selon la situation
    ball_color = determine_ball_color(ball_state)
    ball_scatter.set_color(ball_color)

    # Passes depuis porteur et identification des receveurs directs
    direct_receivers = []  # liste pour stocker les receveurs directs potentiels
    
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
                        for _, (def_pos, width, height, angle) in defender_zones.items():
                            if line_intersects_ellipse(cpos, pos, def_pos, width, height, angle):
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
                            for _, (def_pos, width, height, angle) in defender_zones.items():
                                if line_intersects_ellipse(receiver_pos, pos, def_pos, width, height, angle):
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

    # Ajouter une légende pour les couleurs de la balle
    '''color_legend = [
        f"🟡 Portée (normal): {BALL_COLORS['in_hand']}",
        f"🔴 Sous pression: {BALL_COLORS['under_pressure']}",
        f"🟢 Jeu libre: {BALL_COLORS['free_play']}",
        f"🟠 Zone dangereuse: {BALL_COLORS['danger_zone']}",
        f"🟢 Opportunité: {BALL_COLORS['scoring_opportunity']}"
    ]'''
    legend_text = f"État balle: {ball_state if not ball_data.empty else 'N/A'} - Couleur: {ball_color}"
    txt = ax.text(0.02, 0.98, legend_text, transform=ax.transAxes, fontsize=10, 
                  verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    text_labels.append(txt)

    ax.set_title(f'Temps : {t:.2f}s – Côté : {cote}')
    return (list(scatters.values()) + [ball_scatter] + passes_lines + blocked_passes_lines + 
            secondary_passes_lines + pressure_lines + influence_zones + text_labels)

ani = FuncAnimation(fig, update, frames=times, init_func=init, interval=40, blit=True)
plt.tight_layout()
plt.show()