import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


df = pd.read_csv("../data/agen_emergent/edges_agen_emergent_possession_1.csv")  
print(df.head())

G = nx.DiGraph()

for _, row in df.iterrows():
    origin, dest = eval(row["Origin-Destination"])
    label = row["Change label"]
    G.add_edge(origin, dest, label=label)


plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)  # positions pour tous les noeuds
edges_labels = nx.get_edge_attributes(G, 'label')

nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=700, font_size=10, font_weight="bold", arrows=True)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edges_labels, font_color='red', font_size=8)
plt.title("Graphe des des changements de labels")
plt.axis('off')
plt.tight_layout()
plt.show()