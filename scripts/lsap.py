import pandas as pd
import numpy as np
from numpy.linalg import norm
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
from glob import glob # pour trouver les fichiers de tracking
import multiprocessing # pour le traitement parallèle
from functools import partial # pour faciliter l'utilisation de la fonction avec des arguments partiels
#import ffmpeg

from pyproj import Transformer

def loader_lps(file_path, separator='\t', header=0):
    """
    Charge un fichier de données (CSV ou TXT)
    
    Parameters:
    -----------
    file_path : str
        Chemin vers le fichier
    separator : str
        Séparateur utilisé dans le fichier ('\t' pour tab, ',' pour virgule, ' ' pour espace, etc.)
    header : int or None
        Ligne à utiliser comme en-têtes (0 = première ligne, None = pas d'en-tête)
    """
    try:
        # Essayer de détecter automatiquement le format
        return pd.read_csv(file_path, sep=separator, header=header)
    except:
        # Si ça échoue, essayer avec d'autres séparateurs communs
        separators = ['\t', ',', ';', ' ', '|']
        for sep in separators:
            try:
                return pd.read_csv(file_path, sep=sep, header=header)
            except:
                continue
        raise ValueError(f"Impossible de lire le fichier {file_path}. Format non reconnu.")
    
def loader_tracking(file_path, separator='\t', header=None):
    """
    Charge un fichier de données (CSV ou TXT) et nomme les colonnes frame, player, x, y
    
    Parameters:
    -----------
    file_path : str
        Chemin vers le fichier
    separator : str
        Séparateur utilisé dans le fichier ('\t' pour tab, ',' pour virgule, ' ' pour espace, etc.)
    header : int or None
        Ligne à utiliser comme en-têtes (None = pas d'en-tête par défaut)
    """
    # Noms des colonnes prédéfinis
    column_names = ['frame', 'player', 'x', 'y']
    
    try:
        # Essayer de détecter automatiquement le format
        df = pd.read_csv(file_path, sep=separator, header=header, names=column_names)
        return df
    except:
        # Si ça échoue, essayer avec d'autres séparateurs communs
        separators = ['\t', ',', ';', ' ', '|']
        for sep in separators:
            try:
                df = pd.read_csv(file_path, sep=sep, header=header, names=column_names)
                return df
            except:
                continue
        raise ValueError(f"Impossible de lire le fichier {file_path}. Format non reconnu.")
    
def lps_sample(df):
    df_sample = df.copy()
    df_sample = df_sample[::2]
    return df_sample

def tracking_sample(df):
    """
    Échantillonne le DataFrame en gardant une frame sur 5
    """
    df_sample = df.copy()
    
    # Obtenir les frames uniques et les trier
    unique_frames = sorted(df_sample['frame'].unique())
    
    # Prendre une frame sur 5 (indices 0, 5, 10, 15, ...)
    selected_frames = unique_frames[::5]
    
    # Filtrer le DataFrame pour ne garder que les frames sélectionnées
    df_sample = df_sample[df_sample['frame'].isin(selected_frames)]
    
    return df_sample

def load_sample_clear_lps(file_path):

    df = loader_lps(file_path)
    
    df = lps_sample(df)

    columns_to_drop = ["lat_brute", "long_brute", "hdop", "vitesse_fusion", "battery"]
    df = df.drop(columns=columns_to_drop, errors='ignore')

    transformer = Transformer.from_crs("epsg:4326", "epsg:2154", always_xy=True)
    df['x'], df['y'] = transformer.transform(df['longitude_fusion'].values, df['latitude_fusion'].values)
    df['x_norm'] = df['x'] - df['x'].mean()
    df['y_norm'] = df['y'] - df['y'].mean()
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    start_time = df['datetime'].iloc[0]
    df['relative_time'] = (df['datetime'] - start_time).dt.total_seconds()
    df = df.dropna(subset=["latitude_fusion", "longitude_fusion"])
    df = df.reset_index(drop=True)

    return df

def load_sample_clear_tracking(file_path):

    df = loader_tracking(file_path)

    df = tracking_sample(df)

    # Supprimer d'éventuelles lignes d'en-tête dupliquées (par ex. "x" dans la colonne x)
    df = df[~df["x"].isin(["x", "X"])]
    df = df[~df["y"].isin(["y", "Y"])]
    
    # Supprimer les NaNs sur x/y
    df = df.dropna(subset=["x", "y"]).reset_index(drop=True)

    # Conversion des colonnes aux bons types
    df["x"] = df["x"].astype(float)
    df["y"] = df["y"].astype(float)
    df["player_id"] = df["player_id"].astype(int)
    df["frame"] = df["frame"].astype(int)

    # Ajout du temps
    df["time"] = df["frame"] / 25

    # Normalisation par joueur
    df["x_norm"] = df.groupby("player_id")["x"].transform(lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0)
    df["y_norm"] = df.groupby("player_id")["y"].transform(lambda y: (y - y.mean()) / y.std() if y.std() > 0 else 0)

    return df

import os
import pandas as pd
from pyproj import Transformer

def process_lps_directory(directory_path, file_extension=None):
    """
    Applique la fonction load_sample_clear_lps à tous les fichiers d'un répertoire
    et stocke les résultats dans un dictionnaire.
    
    Args:
        directory_path (str): Chemin vers le répertoire contenant les fichiers
        file_extension (str, optional): Extension des fichiers à traiter (ex: '.csv', '.txt')
                                      Si None, traite tous les fichiers
    
    Returns:
        dict: Dictionnaire avec les noms de fichiers comme clés et les DataFrames comme valeurs
    """
    
    # Dictionnaire pour stocker les résultats
    results = {}
    
    # Vérifier que le répertoire existe
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Le répertoire '{directory_path}' n'existe pas.")
    
    # Parcourir tous les fichiers du répertoire
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        # Vérifier que c'est un fichier (pas un dossier)
        if os.path.isfile(file_path):
            # Filtrer par extension si spécifiée
            if file_extension is None or filename.endswith(file_extension):
                try:
                    # Appliquer la fonction de traitement
                    processed_df = load_sample_clear_lps(file_path)
                    
                    # Stocker dans le dictionnaire (utiliser le nom du fichier sans extension comme clé)
                    file_key = os.path.splitext(filename)[0]
                    results[file_key] = processed_df
                    
                    print(f"✓ Fichier traité avec succès: {filename}")
                    
                except Exception as e:
                    print(f"✗ Erreur lors du traitement de {filename}: {str(e)}")
                    continue
    
    print(f"\n📊 Traitement terminé: {len(results)} fichier(s) traité(s) avec succès")
    return results


# Exemple d'utilisation:
# results_dict = process_lps_directory("/chemin/vers/repertoire", file_extension=".csv")
# 
# # Accéder aux données d'un fichier spécifique:
# # df_fichier1 = results_dict["nom_fichier_sans_extension"]


INPUT_LPS_DIRECTORY = "C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/basket/LPS"

dict_lps = process_lps_directory(INPUT_LPS_DIRECTORY, '.csv')

def get_time(dict_lps):
    """
    Renvoie le temps total d'un fichier lps
    """

def distance(traking_df, lps_df, j, delta, t):
    """
    Renvoie la moyenne des distance du joueur i par rapport au joueur dans lps_df tout au long de delta à partir de t.
    """

def lsap(cost_matrix):
    """
    Renvoie le LSAP de la matrice.
    """

def tracking_matcher(tracking_df, dim, delta, dict_lps, t):
    dict = {}
    cost_matrix = np.zeros(dim)
    for t in range(t - delta):
        for i in range(dim[0]):
            lps_df = dict_lps[i]
            for j in range(dim[1]):
                cost_matrix[i,j] = distance(tracking_df, lps_df, j, delta, dict_lps, t)
        dict[t] = lsap(cost_matrix)
    return dict
    


def main(file_path, dict_lps):
    tracking_df = load_sample_clear_tracking(file_path)
    dim = (7,7)
    delta = len(tracking_df['frame'].unique())/7
    t = get_time(dict_lps)
    res = tracking_matcher(tracking_df, dim, delta, dict_lps, t)
    return min(res)
    