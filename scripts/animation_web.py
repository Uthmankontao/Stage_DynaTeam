import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import os
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse

# Configuration de la page Streamlit
st.set_page_config(page_title="Animation Rugby Dynamique", layout="wide")
st.title("Animation Dynamique des Mouvements de Rugby")

# Charger les données
try:
    df = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/tracking GPS - pedagogie emergente.csv", low_memory=False)
    df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/event sequencage - pedagogie emergente.csv", sep=';')
    df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/informations - pedagogie emergente.csv", sep=';')
except Exception as e:
    st.error(f"Erreur de chargement des données : {e}")
    st.stop()

# Vérifier que les données sont chargées correctement
if df.empty or df_seq.empty or df_infos.empty:
    st.error("Les fichiers de données sont vides.")
    st.stop()

# Identifier les joueurs
att_players = df_infos[df_infos['Team'] == 'Att']['ID'].tolist()
def_players = df_infos[df_infos['Team'] == 'Def']['ID'].tolist()
players = att_players + def_players
player_teams = {p: 'Att' if p in att_players else 'Def' for p in players}

# Interface utilisateur pour sélectionner les options
st.sidebar.header("Options d'affichage")

# Options pour choisir ce qu'on veut afficher
show_passes = st.sidebar.checkbox("Afficher les passes possibles", value=True)
show_pressure = st.sidebar.checkbox("Afficher la pression défensive", value=True)
show_distances = st.sidebar.checkbox("Afficher les distances", value=True)
show_player_ids = st.sidebar.checkbox("Afficher les IDs des joueurs", value=True)
show_influence_zones = st.sidebar.checkbox("Afficher les zones d'influence", value=True)
show_player_speeds = st.sidebar.checkbox("Afficher les vitesses des joueurs", value=True)

# Sélectionner la possession
possessions = df['Possession'].unique()
selected_possession = st.sidebar.selectbox("Choisir une possession", possessions)

# Configuration de l'animation
df_possession = df[(df['Possession'] == selected_possession) & (df['GPS'] != 'Ball')].copy()
df_possession_ball = df[(df['Possession'] == selected_possession) & (df['GPS'] == 'Ball')].copy()
df_possession['Carrier'] = False

# Marquer les porteurs de balle
for _, row in df_possession_ball.iterrows():
    if row['Player'] in att_players:
        t, p = row['Time'], row['Player']
        df_possession.loc[(df_possession['Time'] == t) & (df_possession['Player'] == p), 'Carrier'] = True

def draw_rugby_field(ax):
    # Dessiner le terrain (version simplifiée)
    ax.set_facecolor('#549D4B')  # Vert pour le gazon
    
    # Lignes du terrain
    ax.axhline(y=0, color='white', linewidth=2)  # Ligne médiane
    ax.axvline(x=0, color='white', linewidth=2)  # Ligne de but
    ax.axvline(x=22, color='white', linewidth=2)  # Ligne des 22m
    ax.axvline(x=-22, color='white', linewidth=2)  # Ligne des 22m
    
    ax.set_aspect('equal')
    ax.axis('off')

# Préparation de l'animation
times = df_possession['Time'].unique()

# Fonction pour créer l'animation et l'enregistrer en GIF
def create_rugby_animation():
    # Vérifier qu'il y a des frames
    if len(times) == 0:
        st.error("Aucune donnée disponible pour cette possession.")
        return None
    
    # Créer la figure et le terrain
    fig, ax = plt.subplots(figsize=(12, 8))
    draw_rugby_field(ax)
    ax.set_xlim(-15, 50)
    ax.set_ylim(-40, 10)
    
    # Préparation des scatter plots
    scatters = {p: ax.scatter([], [], s=100, color=('red' if p in att_players else 'blue')) for p in players}
    ball_scatter = ax.scatter([], [], s=50, color='white', zorder=5)
    
    # Variables pour stocker les éléments dynamiques
    passes_lines, blocked_passes_lines, secondary_passes_lines = [], [], []
    pressure_lines, influence_zones, text_labels = [], [], []
    
    def init():
        for s in scatters.values():
            s.set_offsets(np.empty((0, 2)))
        ball_scatter.set_offsets(np.empty((0, 2)))
        return list(scatters.values()) + [ball_scatter]
    
    def update(frame_index):
        # Vérifier que l'index est valide
        if frame_index < 0 or frame_index >= len(times):
            return []
        
        t = times[frame_index]
        
        # Effacer les éléments existants
        for line in passes_lines + blocked_passes_lines + secondary_passes_lines + pressure_lines:
            line.remove() if line in ax.lines else None
        for zone in influence_zones:
            zone.remove() if isinstance(zone, Ellipse) else None
        for txt in text_labels:
            txt.remove()
        
        passes_lines.clear()
        blocked_passes_lines.clear()
        secondary_passes_lines.clear()
        pressure_lines.clear()
        influence_zones.clear()
        text_labels.clear()
        
        frame_data = df_possession[df_possession['Time'] == t]
        ball_data = df_possession_ball[df_possession_ball['Time'] == t]
        
        if frame_data.empty:
            return []
        
        cote = 'DROITE'  # Côté fixe pour la démonstration
        
        player_pos = {}
        player_gradients = {}
        
        # Récupérer les positions et gradients des joueurs
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
                
                # Afficher les IDs des joueurs
                if show_player_ids:
                    txt = ax.text(x, y + 0.8, str(p), fontsize=9, ha='center', color='white',
                                  bbox=dict(facecolor='black', alpha=0.5, boxstyle='circle'))
                    text_labels.append(txt)
                
                # Afficher les vitesses des joueurs
                if show_player_speeds and grad_magnitude > 0.5:
                    txt = ax.text(x, y - 1.2, f"{grad_magnitude * 3.6:.1f} km/h", 
                                  fontsize=7, ha='center', color='cyan')
                    text_labels.append(txt)
            else:
                scatters[p].set_offsets(np.empty((0, 2)))
        
        # Ballon
        if not ball_data.empty:
            bx, by = ball_data[['X', 'Y']].values[0]
            ball_scatter.set_offsets([[bx, by]])
        
        ax.set_title(f'Temps : {t:.2f}s – Côté : {cote}')
        return (list(scatters.values()) + [ball_scatter])
    
    # Enregistrer l'animation en GIF
    output_path = 'rugby_animation.gif'
    
    try:
        # Créer l'animation
        ani = FuncAnimation(fig, update, frames=len(times), init_func=init, blit=True)
        
        # Écrire le GIF
        ani.save(output_path, writer=PillowWriter)
        
        # Fermer la figure pour libérer la mémoire
        plt.close(fig)
        
        return output_path
    
    except Exception as e:
        st.error(f"Erreur lors de la création de l'animation : {e}")
        plt.close(fig)
        return None

# Bouton pour générer l'animation
if st.button('Générer l\'animation'):
    # Créer et afficher l'animation
    animation_path = create_rugby_animation()
    
    # Afficher le GIF
    if animation_path:
        st.image(animation_path)
    else:
        st.error("Impossible de générer l'animation.")

# Instructions et explications
st.sidebar.info("""
**Explications de l'animation :**
- Points rouges : Attaquants
- Points bleus : Défenseurs
- Point blanc : Ballon
- Sélectionnez une possession et générez l'animation
""")