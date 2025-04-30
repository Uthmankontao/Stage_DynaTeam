# 📘 Notebook de base : Construction d'un graphe dynamique de passes avec données GPS

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# === 1. Chargement des données ===

# Remplacer par les chemins réels de vos fichiers
events_path = "event_sequencage_emergent.csv"
tracking_path = "tracking_emergent.csv"
infos_joueurs_path = "informations - pedagogie emergente.csv"

# Chargement
events = pd.read_csv(events_path, sep=';')
tracking = pd.read_csv(tracking_path)
infos_joueurs = pd.read_csv(infos_joueurs_path)

# Nettoyage des données GPS : conversion des colonnes
tracking = tracking[tracking['Player'] != 'Ball']
tracking['Player'] = pd.to_numeric(tracking['Player'], errors='coerce')
tracking = tracking.dropna(subset=['Player'])
tracking['Player'] = tracking['Player'].astype(int)

# Conversion des timecodes événements en secondes
events['Time_s'] = events['Position'] / 1000

# === 2. Filtrage des événements de passe ===

passes = events[(events['Passeur'].notna()) & (events['Receveur'].notna())].copy()
passes['Passeur'] = passes['Passeur'].astype(int)
passes['Receveur'] = passes['Receveur'].astype(int)

# === 3. Création du graphe dynamique de passes ===

G = nx.DiGraph()

# Fenêtre de tolérance pour matcher un timecode événement avec une ligne GPS
time_window = 0.2  # ±0.2 secondes

for _, row in passes.iterrows():
    t = row['Time_s']
    passeur = row['Passeur']
    receveur = row['Receveur']
    
    # Position du passeur
    pos_passeur = tracking[
        (tracking['Player'] == passeur) &
        (tracking['Time'].between(t - time_window, t + time_window))
    ][['X', 'Y']].mean()

    # Position du receveur
    pos_receveur = tracking[
        (tracking['Player'] == receveur) &
        (tracking['Time'].between(t - time_window, t + time_window))
    ][['X', 'Y']].mean()

    if not pos_passeur.isna().any() and not pos_receveur.isna().any():
        G.add_node(passeur, pos=(pos_passeur['X'], pos_passeur['Y']))
        G.add_node(receveur, pos=(pos_receveur['X'], pos_receveur['Y']))
        G.add_edge(passeur, receveur, time=t)

# === 4. Visualisation simple du graphe de passes ===

plt.figure(figsize=(8, 6))
pos = nx.get_node_attributes(G, 'pos')
nx.draw(G, pos, with_labels=True, node_size=500, node_color='skyblue', edge_color='gray')
plt.title("Graphe dynamique de passes (positions au moment des passes)")
plt.xlabel("X")
plt.ylabel("Y")
plt.grid(True)
plt.show()
