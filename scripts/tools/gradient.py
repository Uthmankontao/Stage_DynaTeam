import pandas as pd
import numpy as np
# Fonction pour calculer le gradient (vitesse et direction)
def calculate_gradient(df):
    # Trier par joueur et temps pour s'assurer du bon calcul des différences
    df = df.sort_values(['Player', 'Time'])
    
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