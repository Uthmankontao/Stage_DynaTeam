import os
import pandas as pd
import numpy as np
import networkx as nx
from test_graph import construire_graphe

# Chargement des différents fichiers de données :
# - df : données de tracking GPS (positions des joueurs à chaque instant)
# - df_seq : séquences d'événements (début/fin de possession, résultat, etc.)
# - df_infos : informations additionnelles sur les joueurs/équipes
df = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/tracking GPS - pedagogie emergente.csv", low_memory=False)
df_seq = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/event sequencage - pedagogie emergente.csv", sep=';')
df_infos = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/data_brute/informations - pedagogie emergente.csv", sep=';')

# Création du dossier de sortie pour stocker les graphes générés
os.makedirs("graph_dataset", exist_ok=True)

# Définition du pas d'échantillonnage temporel (ex : 1 graphe toutes les 10 frames)
STEP = 10

data = [] # Liste pour stocker les informations sur chaque graphe généré

# Parcours de chaque possession unique dans le fichier de séquencage
for possession_id in df_seq["Possession"].unique():
    # Filtrage des données de tracking pour la possession courante
    df_pos = df[df["Possession"] == possession_id]
    if df_pos.empty:
        continue  # On passe si aucune donnée de tracking pour cette possession

    # Récupération des instants de temps uniques pour cette possession, échantillonnés selon STEP
    times = sorted(df_pos["Time"].unique())
    times = times[::STEP]

    # Recherche du résultat de la possession (ex : essai, perte de balle, etc.)
    result_row = df_seq[(df_seq["Possession"] == possession_id) & (df_seq["Resultat"].notna())]
    if not result_row.empty:
        result = result_row["Resultat"].values[-1].strip().lower()
        label = 1 if result == "essai" else 0  # Label binaire : 1 si essai, 0 sinon
    else:
        continue  # On passe si pas de résultat renseigné

    df_seq_pos = df_seq[df_seq["Possession"] == possession_id]

    # Pour chaque instant t sélectionné dans la possession
    for t in times:
        try:
            # Construction du graphe à l'instant t pour la possession courante
            G = construire_graphe(t, df, df_infos, possession_id)
            if G is None or len(G.nodes) == 0:
                continue  # On passe si le graphe est vide

            # Sauvegarde du graphe au format GEXF (lisible par Gephi, NetworkX, etc.)
            fname = f"graph_dataset/pos_{possession_id}_t_{round(t,2)}.gexf"
            nx.write_gexf(G, fname)

            # Vérification de la présence d'une passe réelle dans le graphe (attribut "real" sur les arêtes de type "passe")
            has_real_pass = any(d.get("real") == True for u, v, d in G.edges(data=True) if d["type"] == "passe")

            # Ajout des informations du graphe à la liste data
            data.append({
                "file": fname,                # Chemin du fichier graphe
                "time": t,                    # Instant de temps
                "possession": possession_id,  # Identifiant de la possession
                "label": label,               # Label binaire (essai ou non)
                "has_real_pass": int(has_real_pass)  # Indicateur de passe réelle
            })
        except Exception as e:
            print(f"[!] Erreur pour possession {possession_id}, t={t} : {e}")
            continue

# Création d'un DataFrame récapitulatif de tous les graphes générés
labels_df = pd.DataFrame(data)
labels_df.to_csv("graph_dataset/graph_labels.csv", index=False)  # Sauvegarde des métadonnées des graphes
print("Dataset généré avec", len(labels_df), "graphes enregistrés.")
