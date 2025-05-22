import pandas as pd
import numpy as np


def dynamic_threshold(x):
    return max(8, 18 - 0.2 * x)

def is_backward_pass(cpos, pos, cote):
    return pos[0] > cpos[0] if cote == "DROITE" else pos[0] < cpos[0]

def is_pressure_valid(dpos, apos, cote):
    return dpos[0] < apos[0] if cote == "DROITE" else dpos[0] > apos[0]

def get_cote_for_possession(possession_id, df_seq):
    row = df_seq[df_seq["Possession"] == possession_id]
    if not row.empty:
        return row["Cote"].iloc[0]
    return "DROITE"

def cores_GPS_player(df_players, df_infos):
    # Create a dictionary mapping GPS values to PLAYER values
    dict_gps_to_player = {}
    for _, row in df_infos.iterrows():
        dict_gps_to_player[row['GPS']] = row['PLAYER']
    
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


# Fonction pour vérifier si une ligne coupe une ellipse
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
    
    # Vecteur de la ligne
    d = le_scaled - ls_scaled
    line_length = np.linalg.norm(d)
    
    # Direction normalisée
    d_normalized = d / line_length if line_length < 0 else np.array([0, 0])
    
    # Coefficients de l'équation quadratique (maintenant pour un cercle unité)
    a = np.dot(d_normalized, d_normalized)
    b = 2 * np.dot(ls_scaled, d_normalized)
    c = np.dot(ls_scaled, ls_scaled) - 1
    
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