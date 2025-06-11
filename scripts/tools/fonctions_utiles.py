import pandas as pd
import numpy as np
from pyproj import Transformer
import os
from glob import glob
def lps_sample(df):
    df = df.copy()
    df = df[::2]# c'est tout ce qu'il fallait mettre pour échantillonner tous les 2 frames
    return df

def nettoyage_lps(df):
    columns_to_drop = ["lat_brute", "long_brute", "hdop", "vitesse_fusion", "battery"]
    df = df.drop(columns=columns_to_drop, errors='ignore')
    df = lps_sample(df)
    transformer = Transformer.from_crs("epsg:4326", "epsg:2154", always_xy=True)
    df['x'], df['y'] = transformer.transform(df['longitude_fusion'].values, df['latitude_fusion'].values)
    # normalisation centrée réduite
    df['x_norm'] = (df['x'] - df['x'].mean()) / df['x'].std()
    df['y_norm'] = (df['y'] - df['y'].mean()) / df['y'].std()
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    start_time = df['datetime'].iloc[0]
    df['relative_time'] = (df['datetime'] - start_time).dt.total_seconds()
    df = df.dropna(subset=["latitude_fusion", "longitude_fusion"])
    df = df.reset_index(drop=True)
    return df
def tracking_sample(df):
    """
    Échantillonne le DataFrame en gardant une frame sur 5
    """
    df = df.copy()
    unique_frames = sorted(df['frame'].unique())
    selected_frames = unique_frames[::5]
    df = df[df['frame'].isin(selected_frames)]
    return df

def nettoyage_tracking(df):
    df = df.dropna(subset=["x", "y"])
    df = df.reset_index(drop=True)
    df = tracking_sample(df)
    df["time"] = df["frame"] / 25
    df["x"] = df["x"].astype(float)
    df["y"] = df["y"].astype(float)
    df["player_id"] = df["player_id"].astype(int)
    df["frame"] = df["frame"].astype(int)

    df["x_norm"] = df.groupby("player_id")["x"].transform(lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0)
    df["y_norm"] = df.groupby("player_id")["y"].transform(lambda y: (y - y.mean()) / y.std() if y.std() > 0 else 0)
    return df


def load_fusion_files(folder_path):
    fusion_files = glob(os.path.join(folder_path, "*_fusion.csv"))
    dataframes = []
    for file in fusion_files:
        df = pd.read_csv(file, sep=';')
        dataframes.append(df)
    return dataframes

def get_dictionnaire(liste_lps):
    for i in range(len(liste_lps)):
        liste_lps[i] = nettoyage_lps(liste_lps[i])
    lps_dict = {i: df for i, df in enumerate(liste_lps)}
    return lps_dict

def tenseur_tracking(tracking_df):

    tracking_times = tracking_df["time"].sort_index().unique()
    n_frames = len(tracking_times) # c'est ce qui va nous permettre de connaitre la longueur de la trajectoire
    # pour chaque joueur dans les gps
    delta_t = tracking_times[-1] - tracking_times[0]
    print(f"Cette vidéo dure {(delta_t):.2f} secondes")
    
    tracking_par_joueur = tracking_df.groupby("player_id")
    player_ids = tracking_df["player_id"].unique()
    for i in range(len(player_ids)):
        print(f"Joueur {i}: {len(tracking_par_joueur.get_group(i))} frames")

    player_ids_valides = []
    liste_des_trajectoires = []

    for pid in player_ids:
        trajectoire = tracking_par_joueur.get_group(pid).sort_values("time")
        trajectoire = trajectoire[["time", "x_norm", "y_norm"]].drop_duplicates("time")

        if len(trajectoire) < 0.75 * n_frames:
            continue
        trajectoire_interp = pd.DataFrame({"time" : tracking_times})
        trajectoire_interp = trajectoire_interp.merge(trajectoire, on="time", how="left")

        trajectoire_interp["x_norm"] = trajectoire_interp["x_norm"].interpolate(method="linear", limit_direction="both")
        trajectoire_interp["y_norm"] = trajectoire_interp["y_norm"].interpolate(method="linear", limit_direction="both")

        player_ids_valides.append(pid)
        liste_des_trajectoires.append(trajectoire_interp[["x_norm", "y_norm"]].values)

    tracking = np.stack(liste_des_trajectoires, axis=0)
    print(f"Nous avons desormais un tenseur de tracking de taille {tracking.shape}")

    return tracking, player_ids_valides, delta_t, n_frames
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