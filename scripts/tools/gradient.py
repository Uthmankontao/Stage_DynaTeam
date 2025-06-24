import pandas as pd
import numpy as np
# Fonction pour calculer le gradient (vitesse et direction)
def calculate_gradient(df):
    # Trier par joueur et temps pour s'assurer du bon calcul des différences
    #df = df.sort_values(['Player', 'Time'])
    
    # Grouper par joueur pour éviter les calculs entre différents joueurs
    result = pd.DataFrame()
    for player, group in df.groupby('Player'):
        # Créer des copies des coordonnées décalées d'une ligne
        group['X_prev'] = group['X'].shift(1)
        group['Y_prev'] = group['Y'].shift(1)
        group['Time_prev'] = group['Time'].shift(1)
        
        # Calculer les différences (gradient)
        group['gradient_X'] = group['X'] - group['X_prev']
        group['gradient_Y'] = group['Y'] - group['Y_prev']
        group['time_diff'] = group['Time'] - group['Time_prev']
        
        # Éviter la division par zéro
        group['time_diff'] = group['time_diff'].replace(0, 0.02)
        
        # Calculer la magnitude du gradient (vitesse en m/s)
        group['gradient_magnitude'] = np.sqrt(group['gradient_X']**2 + group['gradient_Y']**2) / group['time_diff']
        
        # Calculer l'angle du déplacement en radians
        group['gradient_angle'] = np.arctan2(group['gradient_Y'], group['gradient_X'])
        
        # La première ligne de chaque joueur aura des NaN
        group = group.fillna(0)
        result = pd.concat([result, group])
    
    return result

def calculate_player_gradient(player_id, t, df_players, window=0.1):
    """
    Calcule le gradient (vitesse) d'un joueur à un instant donné
    
    Args:
        player_id: ID du joueur
        t: temps cible
        df_players: DataFrame des joueurs
        window: fenêtre temporelle pour le calcul du gradient (en secondes)
    
    Returns:
        tuple: (gradient_x, gradient_y, vitesse_magnitude)
    """
    # Filtrer les données pour ce joueur
    player_data = df_players[df_players['Player'] == player_id].sort_values('Time')
    
    if len(player_data) < 2:
        return 0, 0, 0
    
    # Trouver les points avant et après le temps cible dans une fenêtre
    before_data = player_data[player_data['Time'] <= t]
    after_data = player_data[player_data['Time'] >= t]
    
    if len(before_data) == 0 or len(after_data) == 0:
        return 0, 0, 0
    
    # Prendre les points les plus proches dans la fenêtre
    t_before = before_data['Time'].iloc[-1]
    t_after = after_data['Time'].iloc[0]
    
    # Si on est exactement sur un point, essayer d'utiliser les points adjacents
    if t_before == t_after:
        if len(before_data) > 1:
            t_before = before_data['Time'].iloc[-2]
        elif len(after_data) > 1:
            t_after = after_data['Time'].iloc[1]
        else:
            return 0, 0, 0
    
    # Vérifier que les points sont dans la fenêtre temporelle
    if abs(t_before - t) > window or abs(t_after - t) > window:
        # Élargir la recherche si nécessaire
        window_extended = min(1.0, abs(t_after - t_before))
        if abs(t_before - t) > window_extended or abs(t_after - t) > window_extended:
            return 0, 0, 0
    
    # Récupérer les positions
    pos_before = before_data[before_data['Time'] == t_before][['X', 'Y']].iloc[-1]
    pos_after = after_data[after_data['Time'] == t_after][['X', 'Y']].iloc[0]
    
    # Calculer le gradient (vitesse)
    dt = t_after - t_before
    if dt == 0:
        return 0, 0, 0
    
    gradient_x = (pos_after['X'] - pos_before['X']) / dt
    gradient_y = (pos_after['Y'] - pos_before['Y']) / dt
    vitesse_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
    
    return gradient_x, gradient_y, vitesse_magnitude