import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# Fonction principale pour afficher les graphes d'une possession entière
def main():
    # Charger les données de tracking et d'informations joueurs
    df = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/tracking GPS - pedagogie emergente.csv", low_memory=False)
    df_infos = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/informations - pedagogie emergente.csv", sep=';')
    # Demander à l'utilisateur le numéro de la possession à analyser
    sequence = int(input("donne un numéro de la possession : "))
    # Extraire les timestamps uniques pour cette possession (1 sur 10 pour alléger)
    timestamps = sorted(df[df["Possession"] == sequence]["Time"].unique()[::10])
    # Construire un graphe pour chaque timestamp sélectionné
    graphes = [construire_graphe(t, df, df_infos, sequence) for t in timestamps]
    print("Il y a", len(graphes), "graphes pour la possession", sequence)
    # Demander à l'utilisateur quel graphe il veut visualiser
    i = int(input("lequel veux tu voir ?  : "))
    G = graphes[i]
    afficher_graphe(G, timestamps[i])

# Fonction principale pour afficher le graphe à un instant précis
def main_2():
    # Charger les données de tracking et d'informations joueurs
    df = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/tracking GPS - pedagogie emergente.csv", low_memory=False)
    df_infos = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/informations - pedagogie emergente.csv", sep=';')
    # Demander à l'utilisateur la possession et le temps à visualiser
    sequence = int(input("donne le numéro de la possession : "))
    t = float(input("Quel temps (en secondes) veux-tu visualiser ? : "))
    # Construire et afficher le graphe pour ce temps
    G = construire_graphe(t, df, df_infos, sequence)
    afficher_graphe(G, t)

# Fonction pour afficher un graphe avec matplotlib
def afficher_graphe(G, t):
    print(f"Noeuds: {G.nodes(data=True)}")
    print(f"Arêtes: {G.edges(data=True)}")
    print(f"Graphe à t={t:.2f} : {len(G.nodes)} noeuds, {len(G.edges)} arêtes")
    # Position des noeuds (joueurs) sur le terrain
    pos = {n: (G.nodes[n]['x'], G.nodes[n]['y']) for n in G.nodes}
    # Couleur selon l'équipe
    color_map = ['red' if G.nodes[n]['team'] == 'Att' else 'blue' for n in G.nodes]

    plt.figure(figsize=(14, 8))
    # Afficher les joueurs
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=600, edgecolors='k')
    nx.draw_networkx_labels(G, pos, font_color='white', font_weight='bold')

    # Afficher les passes (arêtes vertes avec flèches)
    nx.draw_networkx_edges(G, pos, 
        edgelist=[(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'passe'],
        edge_color='green', arrows=True, arrowstyle='-|>', width=2)

    # Afficher les pressions défensives (arêtes grises en pointillé)
    edges_p = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'pression']
    nx.draw_networkx_edges(G, pos, edgelist=edges_p, style='dashed', edge_color='gray', arrows=False)
    # Afficher la distance sur les pressions
    labels_p = {(u, v): d['label'] for u, v, d in G.edges(data=True) if d['type'] == 'pression'}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_p, font_size=9)

    plt.title(f"Graphe dynamique à t = {t:.2f} s")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# Fonction pour construire le graphe à un instant t pour une possession donnée
def construire_graphe(t, df, df_infos, sequence):
    # Nettoyer les données : enlever colonne inutile et la balle
    df_clean = df.drop(columns="Unnamed: 0", errors="ignore")
    df_clean = df_clean[df_clean["GPS"] != "Ball"].copy()
    df_clean["Player"] = df_clean["Player"].fillna(0).astype(int)

    # Charger les événements de séquencage pour la possession
    df_seq = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/event sequencage - pedagogie emergente.csv", sep=';')
    df_seq = df_seq[df_seq["Possession"] == sequence]

    # Liste des joueurs attaquants et défenseurs
    att_players = df_infos[df_infos['Team'] == 'Att']['ID'].tolist()
    def_players = df_infos[df_infos['Team'] == 'Def']['ID'].tolist()

    # Trouver la frame la plus proche du temps t
    frame_cible = df_clean.iloc[(df_clean["Time"] - t).abs().argsort()[:1]]['Frame'].values[0]
    df_frame = df_clean[df_clean["Frame"] == frame_cible].copy()

    # Créer le graphe orienté
    G = nx.DiGraph()
    # Ajouter les joueurs comme noeuds avec leur position et équipe
    for _, row in df_frame.iterrows():
        pid = int(row["Player"])
        G.add_node(pid, team=row["Team"], x=row["X"], y=row["Y"])

    # Trouver le porteur de balle (le joueur le plus proche de la balle)
    df_ball = df[(df["GPS"] == "Ball") & (df["Frame"] == frame_cible)]
    carrier_id = None
    if not df_ball.empty:
        bx, by = df_ball[["X", "Y"]].values[0]
        df_att = df_frame[df_frame["Team"] == "Att"].copy()
        if not df_att.empty:
            dists = np.linalg.norm(df_att[["X", "Y"]].values - np.array([bx, by]), axis=1)
            carrier_id = int(df_att.iloc[dists.argmin()]["Player"])

    # Ajouter les passes possibles depuis le porteur de balle
    passes_possibles = []
    if carrier_id:
        x_c, y_c = G.nodes[carrier_id]['x'], G.nodes[carrier_id]['y']
        # Chercher le receveur réel dans le fichier de séquencage
        ligne = df_seq[df_seq["Position"] == frame_cible]
        receveur_reel = None
        if not ligne.empty:
            receveur_reel = ligne["Receveur"].dropna().astype(int).values[0] if ligne["Receveur"].notna().any() else None

        for pid in att_players:
            if pid != carrier_id and pid in G.nodes:
                x, y = G.nodes[pid]['x'], G.nodes[pid]['y']
                # Critère pour une passe possible : joueur devant et proche
                if x < x_c and np.linalg.norm([x - x_c, y - y_c]) < 15:
                    edge_type = 'passe'
                    # Marquer la passe réelle si c'est le bon receveur
                    if pid == receveur_reel:
                        G.add_edge(carrier_id, pid, type='passe', real=True)
                    else:
                        G.add_edge(carrier_id, pid, type='passe', real=False)

    # Ajouter les pressions défensives (défenseur proche d'un attaquant)
    for d in def_players:
        if d not in G.nodes:
            continue
        xd, yd = G.nodes[d]['x'], G.nodes[d]['y']
        for a in att_players:
            if a not in G.nodes:
                continue
            xa, ya = G.nodes[a]['x'], G.nodes[a]['y']
            dist = np.linalg.norm([xa - xd, ya - yd])
            # Critère : distance < 7 et attaquant devant le défenseur
            if dist < 7 and xa < xd:
                G.add_edge(d, a, type='pression', label=f"{dist:.1f}")

    return G

# Point d'entrée du script
if __name__ == "__main__":
    print("Quel mode ?")
    print("1. Afficher un graphe à un instant donné")
    print("2. Afficher un graphe pour une possession")
    choix = input("Entrez 1 ou 2 : ")
    if choix == "1":
        main_2()
    elif choix == "2":
        main()
    else:
        print("Choix invalide.")
