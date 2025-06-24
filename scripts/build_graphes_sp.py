import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from tools.fonctions_utiles import *
from tools.gradient import *

def main():
    """Mode principal : sélectionner une possession et un instant"""
    # Chargement des données (même structure que le premier fichier)
    df_players = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/AGEN_EMERGENT.csv")
    df_ball = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/AGEN_BALL_EMERGENT.csv")
    df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/sequencage/agen_emergent.csv", sep=';')
    df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/info_GPS/agen_emergent.csv", sep=';')
    
    # Tri des données
    df_players_sorted = df_players.sort_values(['Possession', 'GPS', 'Time']).copy()
    df_ball_sorted = df_ball.sort_values(['Possession', 'Time']).copy()
    
    # Sélection de la possession
    possession = int(input("Donnez un numéro de possession : "))
    
    # Filtrer pour cette possession
    df_possession = df_players_sorted[df_players_sorted['Possession'] == possession].copy()
    df_ball_possession = df_ball_sorted[df_ball_sorted['Possession'] == possession].copy()
    df_seq_possession = df_seq[df_seq['Possession'] == possession].copy()
    
    if df_possession.empty:
        print(f"Aucune donnée trouvée pour la possession {possession}")
        return
    
    # Ajouter les colonnes nécessaires
    df_possession['Carrier'] = False
    df_possession['Player'] = 0
    df_ball_possession['Player'] = 0
    
    # Correspondance GPS players
    df_possession = cores_GPS_player(df_possession, df_infos)
    df_ball_possession = cores_GPS_player(df_ball_possession, df_infos)
    
    # Récupérer les temps disponibles (échantillonnage)
    timestamps = sorted(df_possession["Time"].unique())  # Prendre 1 frame sur 5
    
    print(f"Il y a {len(timestamps)} instants disponibles pour la possession {possession}")
    i = int(input("Lequel voulez-vous voir (0 à {}) ? : ".format(len(timestamps)-1)))
    
    if 0 <= i < len(timestamps):
        t = timestamps[i]
        G = construire_graphe(t, df_possession, df_ball_possession, df_infos, df_seq_possession)
        afficher_graphe(G, t, possession)
    else:
        print("Index invalide")

def line_intersects_ellipse(p1, p2, ellipse_center, width, height, angle):
    """
    Vérifie si une ligne intersecte avec une ellipse
    Fonction simplifiée pour déterminer si une passe traverse une zone d'influence
    """
    # Calculer le point milieu de la ligne
    mid_point = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    
    # Vérifier si le point milieu est dans l'ellipse (approximation simple)
    dx = mid_point[0] - ellipse_center[0]
    dy = mid_point[1] - ellipse_center[1]
    
    # Rotation inverse
    cos_angle = np.cos(-angle)
    sin_angle = np.sin(-angle)
    
    x_rot = dx * cos_angle - dy * sin_angle
    y_rot = dx * sin_angle + dy * cos_angle
    
    # Test ellipse
    a = width / 2
    b = height / 2
    
    return (x_rot / a) ** 2 + (y_rot / b) ** 2 <= 1

def construire_graphe(t, df_players, df_ball, df_infos, df_seq):
    """
    Construit un graphe NetworkX à partir des données à un instant t
    
    Args:
        t: temps cible
        df_players: DataFrame des joueurs
        df_ball: DataFrame de la balle
        df_infos: DataFrame des informations joueurs
        df_seq: DataFrame de séquençage
    
    Returns:
        NetworkX DiGraph
    """
    # Identifier les équipes
    att_players = df_infos[df_infos['Team'] == 'Att']['player'].tolist()
    def_players = df_infos[df_infos['Team'] == 'Def']['player'].tolist()
    def_players = list(map(lambda x: x + 10, def_players))  # Ajuster les IDs défense
    
    # Trouver le frame le plus proche du temps cible
    frame_data = df_players[df_players['Time'] == t]
    
    if frame_data.empty:
        # Si pas de données exactes, prendre le temps le plus proche
        times_available = df_players['Time'].unique()
        closest_time = times_available[np.argmin(np.abs(times_available - t))]
        frame_data = df_players[df_players['Time'] == closest_time]
        t = closest_time
    
    # Créer le graphe dirigé
    G = nx.DiGraph()
    
    # Récupérer la position de la balle
    ball_position = None
    ball_data = df_ball[df_ball['Time'] == t]
    if not ball_data.empty:
        ball_position = (ball_data['X'].iloc[0], ball_data['Y'].iloc[0])
    
    # Ajouter les nœuds (joueurs)
    player_positions = {}
    for _, row in frame_data.iterrows():
        player_id = int(row['Player'])
        team = 'Att' if player_id in att_players else 'Def'
        
        # Calculer la distance à la balle
        distance_to_ball = None
        if ball_position is not None:
            player_pos = (row['X'], row['Y'])
            distance_to_ball = np.linalg.norm(np.array(player_pos) - np.array(ball_position))
        
        # Calculer le gradient du joueur
        gradient_x, gradient_y, vitesse = calculate_player_gradient(player_id, t, df_players)
        
        G.add_node(player_id, 
                  team=team, 
                  x=row['X'], 
                  y=row['Y'], 
                  distance_to_ball=distance_to_ball,
                  gradient_x=gradient_x,
                  gradient_y=gradient_y,
                  vitesse=vitesse)
        player_positions[player_id] = (row['X'], row['Y'])
    
    # Trouver le porteur de balle
    ball_data = df_ball[df_ball['Time'] == t]
    carrier_id = None
    
    if not ball_data.empty:
        bx, by = ball_data[['X', 'Y']].values[0]
        # Trouver le joueur attaquant le plus proche de la balle
        min_dist = float('inf')
        for player_id in att_players:
            if player_id in player_positions:
                px, py = player_positions[player_id]
                dist = np.linalg.norm([px - bx, py - by])
                if dist < min_dist:
                    min_dist = dist
                    carrier_id = player_id
    
    # Obtenir le côté de jeu pour cette possession
    possession_id = frame_data['Possession'].iloc[0] if not frame_data.empty else 1
    cote = get_cote_for_possession(possession_id, df_seq)
    
    # Créer des zones d'influence simplifiées pour les défenseurs
    BASE_INFLUENCE_RADIUS = 1.5
    defender_zones = {}
    for def_id in def_players:
        if def_id in player_positions:
            def_pos = player_positions[def_id]
            # Zone d'influence circulaire simplifiée pour le graphe
            defender_zones[def_id] = (def_pos, BASE_INFLUENCE_RADIUS * 2, BASE_INFLUENCE_RADIUS * 2, 0)
    
    # Liste pour stocker les receveurs directs (pour les sous-passes)
    direct_receivers = []
    
    # Ajouter les arêtes de passes directes possibles
    if carrier_id and carrier_id in player_positions:
        carrier_pos = player_positions[carrier_id]
        
        for player_id in att_players:
            if player_id != carrier_id and player_id in player_positions:
                receiver_pos = player_positions[player_id]
                distance = np.linalg.norm(np.array(carrier_pos) - np.array(receiver_pos))
                
                # Vérifier si c'est une passe vers l'arrière et dans la distance acceptable
                if distance < dynamic_threshold(carrier_pos[0]) and is_backward_pass(carrier_pos, receiver_pos, cote):
                    # Vérifier si la passe traverse une zone d'influence d'un défenseur
                    pass_blocked = False
                    for _, (def_pos, width, height, angle) in defender_zones.items():
                        if line_intersects_ellipse(carrier_pos, receiver_pos, def_pos, width, height, angle):
                            pass_blocked = True
                            break
                    
                    if pass_blocked:
                        # Passe bloquée
                        G.add_edge(carrier_id, player_id, type='passe_bloquee', distance=distance)
                    else:
                        # Passe directe valide
                        G.add_edge(carrier_id, player_id, type='passe', distance=distance)
                        direct_receivers.append(player_id)  # Ajouter aux receveurs directs
    
    # Ajouter les arêtes de sous-passes (passes secondaires)
    for receiver_id in direct_receivers:
        if receiver_id in player_positions:
            receiver_pos = player_positions[receiver_id]
            
            for player_id in att_players:
                if player_id != receiver_id and player_id != carrier_id and player_id in player_positions:
                    secondary_receiver_pos = player_positions[player_id]
                    distance = np.linalg.norm(np.array(receiver_pos) - np.array(secondary_receiver_pos))
                    
                    # Vérifier si c'est une sous-passe valide
                    if distance < dynamic_threshold(receiver_pos[0]) and is_backward_pass(receiver_pos, secondary_receiver_pos, cote):
                        # Vérifier si la sous-passe traverse une zone d'influence d'un défenseur
                        pass_blocked = False
                        for _, (def_pos, width, height, angle) in defender_zones.items():
                            if line_intersects_ellipse(receiver_pos, secondary_receiver_pos, def_pos, width, height, angle):
                                pass_blocked = True
                                break
                        
                        if pass_blocked:
                            # Sous-passe bloquée
                            G.add_edge(receiver_id, player_id, type='sous_passe_bloquee', distance=distance)
                        else:
                            # Sous-passe valide
                            G.add_edge(receiver_id, player_id, type='sous_passe', distance=distance)
    
    # Ajouter les arêtes de pression défensive
    for def_id in def_players:
        if def_id not in player_positions:
            continue
        def_pos = player_positions[def_id]
        
        for att_id in att_players:
            if att_id not in player_positions:
                continue
            att_pos = player_positions[att_id]
            distance = np.linalg.norm(np.array(def_pos) - np.array(att_pos))
            
            # Vérifier si le défenseur exerce une pression valide
            if distance < 7 and is_pressure_valid(def_pos, att_pos, cote):
                G.add_edge(def_id, att_id, type='pression', distance=distance, label=f"{distance:.1f}")
    
    return G

def afficher_graphe(G, t, possession):
    """
    Affiche le graphe avec matplotlib
    
    Args:
        G: graphe NetworkX
        t: temps
        possession: numéro de possession
    """
    print(f"Graphe à t={t:.2f}s, possession {possession} : {len(G.nodes)} nœuds, {len(G.edges)} arêtes")
    
    # Compter les différents types d'arêtes
    edge_counts = {}
    for _, _, data in G.edges(data=True):
        edge_type = data['type']
        edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1
    
    print(f"Types d'arêtes: {edge_counts}")
    
    # Afficher les informations des nœuds avec distance à la balle et gradient
    print("\nInformations des joueurs :")
    for node in sorted(G.nodes()):
        node_data = G.nodes[node]
        team = node_data['team']
        distance = node_data.get('distance_to_ball')
        vitesse = node_data.get('vitesse', 0)
        gradient_x = node_data.get('gradient_x', 0)
        gradient_y = node_data.get('gradient_y', 0)
        
        info_str = f"  Joueur {node} ({team}) - Position: ({node_data['x']:.1f}, {node_data['y']:.1f})"
        if distance is not None:
            info_str += f" - Distance balle: {distance:.1f}m"
        else:
            info_str += " - Distance balle: N/A"
        info_str += f" - Vitesse: {vitesse:.1f}m/s - Gradient: ({gradient_x:.1f}, {gradient_y:.1f})"
        print(info_str)
    
    print(f"\nArêtes: {list(G.edges(data=True))}")
    
    # Positions des nœuds basées sur les coordonnées réelles
    pos = {n: (G.nodes[n]['x'], G.nodes[n]['y']) for n in G.nodes}
    
    # Couleurs des nœuds selon l'équipe
    color_map = ['red' if G.nodes[n]['team'] == 'Att' else 'blue' for n in G.nodes]
    
    # Créer la figure
    plt.figure(figsize=(16, 10))
    
    # Dessiner les nœuds
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=600, edgecolors='k')
    
    # Dessiner les labels des joueurs avec distance à la balle et vitesse
    labels = {}
    for node in G.nodes():
        distance_to_ball = G.nodes[node].get('distance_to_ball')
        vitesse = G.nodes[node].get('vitesse', 0)
        
        label_parts = [str(node)]
        if distance_to_ball is not None:
            label_parts.append(f"({distance_to_ball:.1f}m)")
        label_parts.append(f"v:{vitesse:.1f}")
        
        labels[node] = "\n".join(label_parts)
    
    nx.draw_networkx_labels(G, pos, labels=labels, font_color='white', font_weight='bold', font_size=8)
    
    # Dessiner les vecteurs de vitesse (gradients) pour chaque joueur
    for node in G.nodes():
        node_data = G.nodes[node]
        gradient_x = node_data.get('gradient_x', 0)
        gradient_y = node_data.get('gradient_y', 0)
        vitesse = node_data.get('vitesse', 0)
        
        if vitesse > 0.5:  # Afficher seulement si la vitesse est significative
            x, y = pos[node]
            # Normaliser et ajuster la longueur du vecteur pour l'affichage
            scale = min(3.0, vitesse * 0.3)  # Ajuster l'échelle selon vos besoins
            dx = gradient_x / vitesse * scale if vitesse > 0 else 0
            dy = gradient_y / vitesse * scale if vitesse > 0 else 0
            
            color = 'darkred' if node_data['team'] == 'Att' else 'darkblue'
            plt.arrow(x, y, dx, dy, head_width=0.3, head_length=0.2, 
                     fc=color, ec=color, alpha=0.8, linewidth=2)
    
    # Dessiner les arêtes de passes directes (vertes)
    pass_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'passe']
    if pass_edges:
        nx.draw_networkx_edges(G, pos, 
            edgelist=pass_edges,
            edge_color='green', arrows=True, arrowstyle='-|>', width=2, alpha=0.8)
    
    # Dessiner les arêtes de passes bloquées (rouges pointillées)
    blocked_pass_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'passe_bloquee']
    if blocked_pass_edges:
        nx.draw_networkx_edges(G, pos, 
            edgelist=blocked_pass_edges,
            edge_color='red', arrows=True, arrowstyle='-|>', width=2, alpha=0.8, style='dashed')
    
    # Dessiner les arêtes de sous-passes (jaunes)
    secondary_pass_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'sous_passe']
    if secondary_pass_edges:
        nx.draw_networkx_edges(G, pos, 
            edgelist=secondary_pass_edges,
            edge_color='yellow', arrows=True, arrowstyle='-|>', width=1.5, alpha=0.7)
    
    # Dessiner les arêtes de sous-passes bloquées (orange pointillées)
    blocked_secondary_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'sous_passe_bloquee']
    if blocked_secondary_edges:
        nx.draw_networkx_edges(G, pos, 
            edgelist=blocked_secondary_edges,
            edge_color='orange', arrows=True, arrowstyle='-|>', width=1.5, alpha=0.7, style='dashed')
    
    # Dessiner les arêtes de pression (grises, pointillées)
    pressure_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'pression']
    if pressure_edges:
        nx.draw_networkx_edges(G, pos, 
            edgelist=pressure_edges, 
            style='dashed', edge_color='gray', arrows=False, width=1.5, alpha=0.7)
        
        # Ajouter les labels de distance pour la pression
        pressure_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True) if d['type'] == 'pression'}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=pressure_labels, font_size=8)
    
    # Ajouter les labels de distance pour les passes directes
    pass_labels = {(u, v): f"{d['distance']:.1f}m" for u, v, d in G.edges(data=True) if d['type'] == 'passe'}
    if pass_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=pass_labels, font_size=8, font_color='darkgreen')
    
    # Ajouter les labels de distance pour les sous-passes
    secondary_labels = {(u, v): f"{d['distance']:.1f}m" for u, v, d in G.edges(data=True) if d['type'] == 'sous_passe'}
    if secondary_labels:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=secondary_labels, font_size=7, font_color='orange')
    
    plt.title(f"Graphe rugby - Possession {possession} à t = {t:.2f}s\n"
              f"Rouge: Attaque, Bleu: Défense\n" 
              f"Vert: Passes directes, Jaune: Sous-passes, Rouge/Orange pointillé: Passes bloquées\n"
              f"Lignes grises: Pression défensive\n"
              f"Flèches colorées: Vecteurs vitesse des joueurs\n"
              f"Chiffres sous les joueurs: Distance à la balle (m) et vitesse (m/s)")
    plt.axis('equal')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

main()