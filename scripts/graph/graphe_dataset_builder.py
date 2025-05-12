import os
import pandas as pd
import numpy as np
import networkx as nx
from test_graph import construire_graphe


df = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data🏀/data_brute/tracking GPS - pedagogie emergente.csv", low_memory=False)
df_seq = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data🏀/data_brute/event sequencage - pedagogie emergente.csv", sep=';')
df_infos = pd.read_csv("C:/Users/Ousmane Kontao/Desktop/Projet_Data🏀/data_brute/informations - pedagogie emergente.csv", sep=';')

os.makedirs("graph_dataset", exist_ok=True)

# Seuils pour l'échantillonnage temporel (ex: 5 frames/sec si tracking à 50Hz)
STEP = 10

data = [] # Liste pour stocker les données des graphes

# Parcours des possessions
for possession_id in df_seq["Possession"].unique():
    df_pos = df[df["Possession"] == possession_id]
    if df_pos.empty:
        continue
    times = sorted(df_pos["Time"].unique())
    times = times[::STEP]

    result_row = df_seq[(df_seq["Possession"] == possession_id) & (df_seq["Resultat"].notna())]
    if not result_row.empty:
        result = result_row["Resultat"].values[-1].strip().lower()
        label = 1 if result == "essai" else 0
    else:
        continue

    df_seq_pos = df_seq[df_seq["Possession"] == possession_id]

    for t in times:
        try:
            G = construire_graphe(t, df, df_infos, possession_id)
            if G is None or len(G.nodes) == 0:
                continue
            fname = f"graph_dataset/pos_{possession_id}_t_{round(t,2)}.gexf"
            nx.write_gexf(G, fname)
            has_real_pass = any(d.get("real") == True for u, v, d in G.edges(data=True) if d["type"] == "passe")
            data.append({
                "file": fname,
                "time": t,
                "possession": possession_id,
                "label": label,
                "has_real_pass": int(has_real_pass)
            })
        except Exception as e:
            print(f"[!] Erreur pour possession {possession_id}, t={t} : {e}")
            continue

# DataFrame final
labels_df = pd.DataFrame(data)
labels_df.to_csv("graph_dataset/graph_labels.csv", index=False)
print("Dataset généré avec", len(labels_df), "graphes enregistrés.")
