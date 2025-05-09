import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from build_graph import construire_graphe
import networkx as nx
from pitch import draw_rugby_field


# Chargement des données
df = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/tracking GPS - pedagogie emergente.csv", low_memory=False)
df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/event sequencage - pedagogie emergente.csv", sep=';')
df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/informations - pedagogie emergente.csv", sep=';')

# Identifier les joueurs
att_players = df_infos[df_infos['Team'] == 'Att']['ID'].tolist()
def_players = df_infos[df_infos['Team'] == 'Def']['ID'].tolist()
players = att_players + def_players
player_teams = {p: 'Att' if p in att_players else 'Def' for p in players}

# Filtrer les données pour une seule possession (ex. : 1)
df_possession_1 = df[(df['Possession'] == 1) & (df['GPS'] != 'Ball')].copy()
df_possession_1_ball = df[(df['Possession'] == 1) & (df['GPS'] == 'Ball')].copy()
df_possession_1['Carrier'] = False
df_seq_1 = df_seq[df_seq['Possession'] == 1]

# Marquer les porteurs de balle
for _, row in df_possession_1_ball.iterrows():
    if row['Player'] in att_players:
        t, p = row['Time'], row['Player']
        df_possession_1.loc[(df_possession_1['Time'] == t) & (df_possession_1['Player'] == p), 'Carrier'] = True

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

# Time
times = df_possession_1['Time'].unique()

# Graphique
fig, ax = plt.subplots(figsize=(12, 8))
draw_rugby_field(ax)
ax.set_xlim(-15, 50)
ax.set_ylim(-40, 10)
scatters = {p: ax.scatter([], [], s=100, color=('red' if p in att_players else 'blue')) for p in players}
ball_scatter = ax.scatter([], [], s=50, color='white', zorder=5)
text_labels = []

"""legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Att'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Def'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Ballon'),
    Line2D([0], [0], color='orange', lw=2, label='Passes possibles'),
    Line2D([0], [0], color='white', lw=1, linestyle='--', label='Pression défensive')
]"""
#ax.legend(handles=legend_elements, loc='upper left')

passes_lines, pressure_lines = [], []

def init():
    for s in scatters.values():
        s.set_offsets(np.empty((0, 2)))
    ball_scatter.set_offsets(np.empty((0, 2)))
    return list(scatters.values()) + [ball_scatter]

def update(t):
    global passes_lines, pressure_lines, text_labels
    for line in passes_lines + pressure_lines:
        line.remove()
    for txt in text_labels:
        txt.remove()
    passes_lines.clear()
    pressure_lines.clear()
    text_labels.clear()

    frame_data = df_possession_1[df_possession_1['Time'] == t]
    ball_data = df_possession_1_ball[df_possession_1_ball['Time'] == t]
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
            txt = ax.text(x, y + 0.8, str(p), fontsize=9, ha='center', color='white',
                          bbox=dict(facecolor='black', alpha=0.5, boxstyle='circle'))
            text_labels.append(txt)
        else:
            scatters[p].set_offsets(np.empty((0, 2)))

    if not ball_data.empty:
        bx, by = ball_data[['X', 'Y']].values[0]
        ball_scatter.set_offsets([[bx, by]])

    # Passes en arrière depuis porteur
    carrier = frame_data[frame_data['Carrier']]
    if not carrier.empty:
        cid = carrier['Player'].iloc[0]
        cpos = player_pos.get(cid)
        for p, pos in player_pos.items():
            if p != cid and player_teams[p] == 'Att':
                dist = np.linalg.norm(np.array(cpos) - np.array(pos))
                if dist < dynamic_threshold(cpos[0]) and is_backward_pass(cpos, pos, cote):
                    line = ax.plot([cpos[0], pos[0]], [cpos[1], pos[1]], color='orange', linewidth=2, alpha=0.8)[0]
                    passes_lines.append(line)

    # Lien de pression valide uniquement si le défenseur est devant
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
                    txt = ax.text((dpos[0] + apos[0])/2, (dpos[1] + apos[1])/2,
                                  f"{dist:.1f}", fontsize=8, color='white')
                    text_labels.append(txt)

    ax.set_title(f'Temps : {t:.2f}s – Côté : {cote}')
    return list(scatters.values()) + [ball_scatter] + passes_lines + pressure_lines + text_labels

# Lancer l’animation
ani = FuncAnimation(fig, update, frames=times, init_func=init, interval=40, blit=True)
ani.save("animation_rugby.gif", writer="pillow", fps=15)
print("Animation avec filtre de pression cohérent enregistrée.")

"""t = df['Time'].unique()[600]

G = construire_graphe(t)

if G is not None:
    print("Nœuds :", G.nodes(data=True))
    print("Arêtes :", G.edges(data=True))
else:
    print("Aucun graphe généré à cet instant.")

pos = {n: (d['x'], d['y']) for n, d in G.nodes(data=True)}
colors = ['red' if d['team'] == 'Att' else 'blue' for n, d in G.nodes(data=True)]
edge_colors = ['green' if d['type'] == 'passe' else 'gray' for u, v, d in G.edges(data=True)]

plt.figure(figsize=(12, 8))
nx.draw(G, pos, with_labels=True, node_color=colors, edge_color=edge_colors, node_size=500, font_color='white')
plt.title(f"Graphe dynamique à t = {t}s")
plt.show()"""
