import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

def main():
    df = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/data_brute/tracking GPS - pedagogie emergente.csv", low_memory=False)
    df_infos = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/data_brute/informations - pedagogie emergente.csv", sep=';')
    sequence = int(input("donne un numéro de la possession : "))
    timestamps = sorted(df[df["Possession"] == sequence]["Time"].unique()[::10])
    graphes = [construire_graphe(t, df, df_infos) for t in timestamps]
    print("Il y a", len(graphes), "graphes pour la possession", sequence)
    i = int(input("lequel veux tu voir ?  : "))
    G = graphes[i]
    afficher_graphe(graphes[i], timestamps[i])

def main_2():
    df = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/data_brute/tracking GPS - pedagogie emergente.csv", low_memory=False)
    df_infos = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/data_brute/informations - pedagogie emergente.csv", sep=';')
    t = float(input("Quel temps (en secondes) veux-tu visualiser ? : "))
    G = construire_graphe(t, df, df_infos)
    afficher_graphe(G, t)

def afficher_graphe(G, t):
    print(f"Noeuds: {G.nodes(data=True)}")
    print(f"Arêtes: {G.edges(data=True)}")
    print(f"Graphe à t={t:.2f} : {len(G.nodes)} noeuds, {len(G.edges)} arêtes")
    pos = {n: (G.nodes[n]['x'], G.nodes[n]['y']) for n in G.nodes}
    color_map = ['red' if G.nodes[n]['team'] == 'Att' else 'blue' for n in G.nodes]

    plt.figure(figsize=(14, 8))
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=600, edgecolors='k')
    nx.draw_networkx_labels(G, pos, font_color='white', font_weight='bold')

    nx.draw_networkx_edges(G, pos, 
        edgelist=[(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'passe'],
        edge_color='green', arrows=True, arrowstyle='-|>', width=2)

    edges_p = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'pression']
    nx.draw_networkx_edges(G, pos, edgelist=edges_p, style='dashed', edge_color='gray', arrows=False)
    labels_p = {(u, v): d['label'] for u, v, d in G.edges(data=True) if d['type'] == 'pression'}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_p, font_size=9)

    plt.title(f"Graphe dynamique à t = {t:.2f} s")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def construire_graphe(t, df, df_infos):
    df = df.drop(columns="Unnamed: 0", errors="ignore")
    df = df[df["GPS"] != "Ball"].copy()
    df["Player"] = df["Player"].fillna(0).astype(int)

    att_players = df_infos[df_infos['Team'] == 'Att']['ID'].tolist()
    def_players = df_infos[df_infos['Team'] == 'Def']['ID'].tolist()

    frame_cible = df.iloc[(df["Time"] - t).abs().argsort()[:1]]['Frame'].values[0]
    df_frame = df[df["Frame"] == frame_cible].copy()

    G = nx.DiGraph()
    for _, row in df_frame.iterrows():
        pid = int(row["Player"])
        G.add_node(pid, team=row["Team"], x=row["X"], y=row["Y"])

    df_ball = df[(df["GPS"] == "Ball") & (df["Frame"] == frame_cible)]
    carrier_id = None
    if not df_ball.empty:
        bx, by = df_ball[["X", "Y"]].values[0]
        df_att = df_frame[df_frame["Team"] == "Att"].copy()
        dists = np.linalg.norm(df_att[["X", "Y"]].values - np.array([bx, by]), axis=1)
        carrier_id = df_att.iloc[dists.argmin()]["Player"]

    if carrier_id:
        x_c, y_c = G.nodes[carrier_id]['x'], G.nodes[carrier_id]['y']
        for pid in att_players:
            if pid != carrier_id and pid in G.nodes:
                x, y = G.nodes[pid]['x'], G.nodes[pid]['y']
                if x < x_c and np.linalg.norm([x - x_c, y - y_c]) < 15:
                    G.add_edge(carrier_id, pid, type='passe')

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
    return G



if __name__ == "__main__":
    print("Quel mode veux-tu utiliser ?")
    print("1. Afficher un graphe à un instant donné")
    print("2. Afficher un graphe pour une possession")
    choix = input("Entrez 1 ou 2 : ")
    if choix == "1":
        main_2()
    elif choix == "2":
        main()
    else:
        print("Choix invalide.")


    