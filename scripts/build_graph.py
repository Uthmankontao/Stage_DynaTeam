import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# Fonction principale
# -----------------------------
def construire_graphe(t=316.84):
    # Chargement des données
    df = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/tracking GPS - pedagogie emergente.csv", low_memory=False)
    df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/event sequencage - pedagogie emergente.csv", sep=';')
    df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/informations - pedagogie emergente.csv", sep=';')

    df = df.drop(columns="Unnamed: 0", errors="ignore")
    df = df[df["GPS"] != "Ball"].copy()
    df["Player"] = df["Player"].fillna(0).astype(int)

    # Identification joueurs
    att_players = df_infos[df_infos['Team'] == 'Att']['ID'].tolist()
    def_players = df_infos[df_infos['Team'] == 'Def']['ID'].tolist()

    # Trouver la frame la plus proche de t
    frame_cible = df.iloc[(df["Time"] - t).abs().argsort()[:1]]['Frame'].values[0]
    df_frame = df[df["Frame"] == frame_cible].copy()

    # Création du graphe
    G = nx.DiGraph()

    # Ajout des nœuds
    for _, row in df_frame.iterrows():
        pid = int(row["Player"])
        G.add_node(pid, team=row["Team"], x=row["X"], y=row["Y"])

    # Identification du porteur de balle à cet instant
    df_ball = pd.read_csv("data_brute/tracking GPS - pedagogie emergente.csv", low_memory=False)
    df_ball = df_ball[(df_ball["GPS"] == "Ball") & (df_ball["Frame"] == frame_cible)]
    carrier_id = None
    if not df_ball.empty:
        bx, by = df_ball[["X", "Y"]].values[0]
        df_att = df_frame[df_frame["Team"] == "Att"].copy()
        dists = np.linalg.norm(df_att[["X", "Y"]].values - np.array([bx, by]), axis=1)
        carrier_id = df_att.iloc[dists.argmin()]["Player"]

    # Passe : arêtes orientées entre le porteur et ses coéquipiers derrière lui
    if carrier_id:
        x_c, y_c = G.nodes[carrier_id]['x'], G.nodes[carrier_id]['y']
        for pid in att_players:
            if pid != carrier_id and pid in G.nodes:
                x, y = G.nodes[pid]['x'], G.nodes[pid]['y']
                if x < x_c and np.linalg.norm([x - x_c, y - y_c]) < 15:
                    G.add_edge(carrier_id, pid, type='passe')

    # Pression : liens non orientés entre défenseur et attaquant s’ils sont en face (< 7m, devant)
    for d in def_players:
        if d not in G.nodes:
            continue
        xd, yd = G.nodes[d]['x'], G.nodes[d]['y']
        for a in att_players:
            if a not in G.nodes:
                continue
            xa, ya = G.nodes[a]['x'], G.nodes[a]['y']
            dist = np.linalg.norm([xa - xd, ya - yd])
            if dist < 7 and xa < xd:
                G.add_edge(d, a, type='pression', label=f"{dist:.1f}")

    # Affichage du graphe
    pos = {n: (G.nodes[n]['x'], G.nodes[n]['y']) for n in G.nodes}
    color_map = ['red' if G.nodes[n]['team'] == 'Att' else 'blue' for n in G.nodes]

    plt.figure(figsize=(14, 8))
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=600, edgecolors='k')
    nx.draw_networkx_labels(G, pos, font_color='white', font_weight='bold')

    # Arêtes passes
    nx.draw_networkx_edges(G, pos, edgelist=[(u,v) for u,v,d in G.edges(data=True) if d['type']=='passe'],
                           edge_color='green', arrows=True, arrowstyle='-|>', width=2)

    # Arêtes pression
    edges_p = [(u,v) for u,v,d in G.edges(data=True) if d['type']=='pression']
    nx.draw_networkx_edges(G, pos, edgelist=edges_p, style='dashed', edge_color='gray', arrows=False)
    labels_p = {(u,v): d['label'] for u,v,d in G.edges(data=True) if d['type']=='pression'}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_p, font_size=9)

    plt.title(f"Graphe dynamique à t = {t:.2f} s")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

    return G
