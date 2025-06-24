import pandas as pd
import numpy as np



def dynamic_threshold(x):
    return max(8, 18 - 0.2 * x)

def is_backward_pass(cpos, pos, cote):
    return pos[0] < cpos[0] if cote == "DROITE" else pos[0] > cpos[0]

def is_pressure_valid(dpos, apos, cote):
    return dpos[0] > apos[0] if cote == "DROITE" else dpos[0] < apos[0]

def get_cote_for_possession(possession_id, df_seq):
    row = df_seq[df_seq["Possession"] == possession_id]
    if not row.empty:
        return row["Cote"].iloc[0]
    return "DROITE"

def cores_GPS_player(df_players, df_infos):
    # Create a dictionary mapping GPS values to PLAYER values
    dict_gps_to_player = {}
    for _, row in df_infos.iterrows():
        if row['Team'] == 'Att':
            dict_gps_to_player[row['GPS']] = row['player']
        else:
            dict_gps_to_player[row['GPS']] = row['player'] + 10
    
    # Create a new column 'Player' in df_players based on the GPS values
    player_list = []
    for _, row in df_players.iterrows():
        gps_value = row['GPS']
        # Check if the GPS value is NaN
        if pd.isna(gps_value):
            player_list.append("0")  # Valeur par défaut
        else:
            # Try to get the player, use a default if not found
            player_list.append(dict_gps_to_player.get(gps_value, "0"))
    
    # Assigner la liste à la colonne Player
    df_players['Player'] = player_list
    
    return df_players


def line_intersects_ellipse(line_start, line_end, ellipse_center, width, height, angle):
    """
    Vérifie si une ligne (passe) coupe une ellipse (zone d'influence)
    
    :param line_start: Point de départ de la ligne (x1, y1)
    :param line_end: Point d'arrivée de la ligne (x2, y2)
    :param ellipse_center: Centre de l'ellipse (x, y)
    :param width: Largeur de l'ellipse
    :param height: Hauteur de l'ellipse
    :param angle: Angle de rotation de l'ellipse en radians
    :return: True si la ligne coupe l'ellipse, False sinon
    """
    # Convertir en numpy arrays
    line_start = np.array(line_start)
    line_end = np.array(line_end)
    ellipse_center = np.array(ellipse_center)
    
    # Vérifier si la ligne a une longueur nulle
    line_vector = line_end - line_start
    line_length = np.linalg.norm(line_vector)
    
    # Si la ligne a une longueur nulle, vérifier si le point est dans l'ellipse
    if line_length < 1e-10:  # Tolérance numérique
        # Transformer le point dans le repère de l'ellipse
        cos_angle = np.cos(-angle)
        sin_angle = np.sin(-angle)
        
        # Translation pour centrer l'ellipse à l'origine
        point_translated = line_start - ellipse_center
        
        # Rotation pour aligner l'ellipse avec les axes
        point_rotated = np.array([
            point_translated[0] * cos_angle - point_translated[1] * sin_angle,
            point_translated[0] * sin_angle + point_translated[1] * cos_angle
        ])
        
        # Vérifier si le point est dans l'ellipse
        normalized_x = point_rotated[0] / (width/2)
        normalized_y = point_rotated[1] / (height/2)
        return (normalized_x**2 + normalized_y**2) <= 1
    
    # Transformer la ligne dans le repère de l'ellipse (sans rotation)
    cos_angle = np.cos(-angle)
    sin_angle = np.sin(-angle)
    
    # Translation pour centrer l'ellipse à l'origine
    ls_translated = line_start - ellipse_center
    le_translated = line_end - ellipse_center
    
    # Rotation pour aligner l'ellipse avec les axes
    ls_rotated = np.array([
        ls_translated[0] * cos_angle - ls_translated[1] * sin_angle,
        ls_translated[0] * sin_angle + ls_translated[1] * cos_angle
    ])
    le_rotated = np.array([
        le_translated[0] * cos_angle - le_translated[1] * sin_angle,
        le_translated[0] * sin_angle + le_translated[1] * cos_angle
    ])
    
    # Mise à l'échelle pour transformer l'ellipse en cercle
    ls_scaled = np.array([ls_rotated[0] / (width/2), ls_rotated[1] / (height/2)])
    le_scaled = np.array([le_rotated[0] / (width/2), le_rotated[1] / (height/2)])
    
    # Vecteur de la ligne dans l'espace transformé
    d = le_scaled - ls_scaled
    d_magnitude = np.linalg.norm(d)
    
    # Normalisation sécurisée
    if d_magnitude < 1e-10:  # Tolérance numérique
        # Si les points sont identiques après transformation, vérifier si le point est dans le cercle unité
        return np.linalg.norm(ls_scaled) <= 1
    
    d_normalized = d / d_magnitude
    
    # Coefficients de l'équation quadratique pour l'intersection ligne-cercle
    a = np.dot(d_normalized, d_normalized)  # Devrait être 1 puisque d_normalized est normalisé
    b = 2 * np.dot(ls_scaled, d_normalized)
    c = np.dot(ls_scaled, ls_scaled) - 1
    
    discriminant = b**2 - 4 * a * c
    
    # Pas d'intersection
    if discriminant < 0:
        return False
    
    # Calculer les solutions
    sqrt_discriminant = np.sqrt(discriminant)
    
    # Protection contre la division par zéro (même si a devrait être ~1)
    if abs(a) < 1e-10:
        return False
    
    t1 = (-b - sqrt_discriminant) / (2 * a)
    t2 = (-b + sqrt_discriminant) / (2 * a)
    
    # Vérifier si l'intersection est sur le segment de ligne
    # Les valeurs t sont dans l'espace normalisé, donc on compare avec d_magnitude
    if (0 <= t1 <= d_magnitude) or (0 <= t2 <= d_magnitude):
        return True
    
    return False

def maj_state(df_ball, df_seq):
    """
    Version simplifiée qui se concentre sur les événements principaux
    """
    import pandas as pd
    
    df_ball_updated = df_ball.copy()
    
    # Initialiser la colonne state si elle n'existe pas
    if 'state' not in df_ball_updated.columns:
        df_ball_updated['state'] = 'portée'
    
    positions = sorted(df_seq['Position'].unique())
    
    for i in range(len(positions)):
        # Récupérer la ligne correspondant à cette position
        row = df_seq[df_seq['Position'] == positions[i]].iloc[0]
        
        # Déterminer l'état selon vos critères
        if pd.notna(row['Passeur']) and (pd.isna(row['Contact']) or row['Contact'] == ''):
            state = 'avc'
        elif pd.notna(row['Passeur']) and row['Contact'] == 'contact':
            state = 'apc'
        elif pd.notna(row['Resultat']) and row['Resultat'] == 'jeu au pied':
            state = 'pied'  # Correction : 'pied' en minuscules
        else:
            state = 'portée'
        
        # Déterminer la plage de positions à mettre à jour
        if i < len(positions) - 1:
            # Positions entre la position actuelle et la suivante
            start_pos = positions[i]
            end_pos = positions[i + 1]
            mask = (df_ball_updated['Position'] >= start_pos) & (df_ball_updated['Position'] < end_pos)
        else:
            # Dernière position - appliquer jusqu'à la fin
            start_pos = positions[i]
            mask = df_ball_updated['Position'] >= start_pos
        
        # Appliquer l'état à toutes les positions dans cette plage
        df_ball_updated.loc[mask, 'state'] = state
    
    return df_ball_updated