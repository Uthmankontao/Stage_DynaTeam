import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
import networkx as nx
import tempfile
import os

# Configuration de la page Streamlit
st.set_page_config(page_title="Animation Rugby", layout="wide")
st.title("Animation des mouvements de rugby")

# Chargement des données
@st.cache_data
def load_data():
    # Remplacez ces chemins par des chemins accessibles ou utilisez st.file_uploader
    try:
        df = pd.read_csv("tracking GPS - pedagogie emergente.csv", low_memory=False)
        df_seq = pd.read_csv("event sequencage - pedagogie emergente.csv", sep=';')
        df_infos = pd.read_csv("informations - pedagogie emergente.csv", sep=';')
        return df, df_seq, df_infos
    except FileNotFoundError:
        # Créer des données de démonstration si les fichiers ne sont pas disponibles
        return create_demo_data()

def create_demo_data():
    # Création de données de démonstration pour tester l'application
    # DataFrame principal avec les positions
    times = np.linspace(0, 10, 100)
    players = list(range(1, 11))
    
    data = []
    for t in times:
        for p in players:
            team = 'Att' if p <= 5 else 'Def'
            # Simuler des mouvements aléatoires sur le terrain
            x = 20 + np.sin(t + p) * 10 + (5 if team == 'Att' else -5)
            y = p * 2 - 10 + np.cos(t) * 5
            data.append({
                'Time': t, 
                'Player': p, 
                'GPS': 'Player', 
                'X': x, 
                'Y': y, 
                'Possession': 1
            })
        # Ajouter le ballon
        carrier = np.random.choice([p for p in players if p <= 5])
        carrier_data = next(item for item in data if item['Time'] == t and item['Player'] == carrier)
        data.append({
            'Time': t, 
            'Player': carrier, 
            'GPS': 'Ball', 
            'X': carrier_data['X'], 
            'Y': carrier_data['Y'], 
            'Possession': 1
        })
    
    df = pd.DataFrame(data)
    
    # DataFrame de séquençage
    df_seq = pd.DataFrame([
        {'Possession': 1, 'Cote': 'DROITE', 'Start': 0, 'End': 10}
    ])
    
    # DataFrame d'informations sur les joueurs
    player_info = []
    for p in players:
        player_info.append({
            'ID': p,
            'Team': 'Att' if p <= 5 else 'Def',
            'Name': f'Player {p}'
        })
    df_infos = pd.DataFrame(player_info)
    
    return df, df_seq, df_infos

# Fonction pour dessiner un terrain de rugby
def draw_rugby_field(ax):
    # Dessiner le terrain (version simplifiée)
    ax.set_facecolor('#549D4B')  # Vert pour le gazon
    
    # Lignes du terrain
    ax.axhline(y=0, color='white', linewidth=2)  # Ligne médiane
    ax.axvline(x=0, color='white', linewidth=2)  # Ligne de but
    ax.axvline(x=22, color='white', linewidth=2)  # Ligne des 22m
    ax.axvline(x=-22, color='white', linewidth=2)  # Ligne des 22m
    
    # Ajouter d'autres éléments si nécessaire
    ax.set_aspect('equal')
    ax.axis('off')

# Charger les données
df, df_seq, df_infos = load_data()

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

# Choix de la possession
possessions = df['Possession'].unique()
selected_possession = st.sidebar.selectbox("Choisir une possession", possessions)

# Filtrer les données pour la possession sélectionnée
df_possession = df[(df['Possession'] == selected_possession) & (df['GPS'] != 'Ball')].copy()
df_possession_ball = df[(df['Possession'] == selected_possession) & (df['GPS'] == 'Ball')].copy()
df_possession['Carrier'] = False
df_seq_selected = df_seq[df_seq['Possession'] == selected_possession]

# Marquer les porteurs de balle
for _, row in df_possession_ball.iterrows():
    if row['Player'] in att_players:
        t, p = row['Time'], row['Player']
        df_possession.loc[(df_possession['Time'] == t) & (df_possession['Player'] == p), 'Carrier'] = True

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

# Temps disponibles
times = df_possession['Time'].unique()

if len(times) == 0:
    st.error("Aucune donnée disponible pour cette possession.")
else:
    # Création de l'animation
    st.write("Génération de l'animation en cours...")
    
    fig, ax = plt.subplots(figsize=(10, 7))
    draw_rugby_field(ax)
    ax.set_xlim(-15, 50)
    ax.set_ylim(-40, 10)
    
    scatters = {p: ax.scatter([], [], s=100, color=('red' if p in att_players else 'blue')) for p in players}
    ball_scatter = ax.scatter([], [], s=50, color='white', zorder=5)
    
    # Légende
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Attaquants'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Défenseurs'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='white', markersize=8, label='Ballon')
    ]
    
    if show_passes:
        legend_elements.append(Line2D([0], [0], color='orange', lw=2, label='Passes possibles'))
    if show_pressure:
        legend_elements.append(Line2D([0], [0], color='white', lw=1, linestyle='--', label='Pression défensive'))
    
    ax.legend(handles=legend_elements, loc='upper left')
    
    passes_lines, pressure_lines, text_labels = [], [], []
    
    def init():
        for s in scatters.values():
            s.set_offsets(np.empty((0, 2)))
        ball_scatter.set_offsets(np.empty((0, 2)))
        return list(scatters.values()) + [ball_scatter]
    
    def update(t):
        global passes_lines, pressure_lines, text_labels
        for line in passes_lines + pressure_lines:
            line.remove() if line in ax.lines else None
        for txt in text_labels:
            txt.remove()
        passes_lines.clear()
        pressure_lines.clear()
        text_labels.clear()
    
        frame_data = df_possession[df_possession['Time'] == t]
        ball_data = df_possession_ball[df_possession_ball['Time'] == t]
        if frame_data.empty:
            return []
    
        possession_id = int(frame_data['Possession'].iloc[0])
        cote = get_cote_for_possession(possession_id)
    
        player_pos = {}
        for p in players:
            pdata = frame_data[frame_data['Player'] == p]
            if not pdata.empty:
                x, y = pdata[['X', 'Y']].values[0]
                scatters[p].set_offsets([[x, y]])
                player_pos[p] = (x, y)
                if show_player_ids:
                    txt = ax.text(x, y + 0.8, str(p), fontsize=9, ha='center', color='white',
                                  bbox=dict(facecolor='black', alpha=0.5, boxstyle='circle'))
                    text_labels.append(txt)
            else:
                scatters[p].set_offsets(np.empty((0, 2)))
    
        if not ball_data.empty:
            bx, by = ball_data[['X', 'Y']].values[0]
            ball_scatter.set_offsets([[bx, by]])
    
        # Passes en arrière depuis porteur
        if show_passes:
            carrier = frame_data[frame_data['Carrier']]
            if not carrier.empty:
                cid = carrier['Player'].iloc[0]
                cpos = player_pos.get(cid)
                if cpos:
                    for p, pos in player_pos.items():
                        if p != cid and player_teams[p] == 'Att':
                            dist = np.linalg.norm(np.array(cpos) - np.array(pos))
                            if dist < dynamic_threshold(cpos[0]) and is_backward_pass(cpos, pos, cote):
                                line = ax.plot([cpos[0], pos[0]], [cpos[1], pos[1]], color='orange', linewidth=2, alpha=0.8)[0]
                                passes_lines.append(line)
    
        # Liens de pression défensive
        if show_pressure:
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
                            if show_distances:
                                txt = ax.text((dpos[0] + apos[0])/2, (dpos[1] + apos[1])/2,
                                              f"{dist:.1f}", fontsize=8, color='white')
                                text_labels.append(txt)
    
        ax.set_title(f'Temps : {t:.2f}s – Côté : {cote}')
        return list(scatters.values()) + [ball_scatter] + passes_lines + pressure_lines + text_labels
    
    # Créer une animation et la sauvegarder en tant que GIF temporaire
    # Utiliser un sous-ensemble de temps pour accélérer la génération d'animation
    sample_indices = np.linspace(0, len(times)-1, min(50, len(times))).astype(int)
    sample_times = times[sample_indices]
    
    ani = FuncAnimation(fig, update, frames=sample_times, init_func=init, blit=True)
    
    # Utiliser un fichier temporaire pour stocker l'animation
    with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmpfile:
        ani.save(tmpfile.name, writer="pillow", fps=5)
        tmpfile_name = tmpfile.name
    
    # Afficher l'animation
    with open(tmpfile_name, "rb") as file:
        animation_bytes = file.read()
        st.image(animation_bytes, use_column_width=True)
    
    # Supprimer le fichier temporaire
    os.unlink(tmpfile_name)
    
    # Informations supplémentaires
    st.sidebar.info("""
    **Explications:**
    - Les points rouges représentent les attaquants
    - Les points bleus représentent les défenseurs
    - Le point blanc représente le ballon
    - Les lignes orange sont les passes possibles
    - Les lignes blanches pointillées indiquent la pression défensive
    """)

# Instructions pour l'utilisateur sur la façon de charger des données
st.sidebar.header("Fichiers requis")
st.sidebar.markdown("""
Pour utiliser cette application avec vos propres données, préparez les fichiers suivants dans le même répertoire que ce script:
- `tracking_gps.csv`: Données de suivi GPS des joueurs
- `event_sequencage.csv`: Séquençage des événements
- `informations.csv`: Informations sur les joueurs

Si ces fichiers ne sont pas trouvés, des données de démonstration seront utilisées.
""")