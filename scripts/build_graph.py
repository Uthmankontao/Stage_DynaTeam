import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
#import os 
edges_file = "../data/racing_emergent/edges_racing_emergent_possession_1.csv"
vertices_file = "../data/racing_emergent/vertices_racing_emergent_possession_1.csv"

def load_possession_graph(edges_path, vertices_path):
    """Construit un graphe dirigé à partir de fichiers edges et vertices."""
    edges_df = pd.read_csv(edges_path)
    vertices_df = pd.read_csv(vertices_path)
    G = nx.DiGraph()

    for _, row in vertices_df.iterrows():
        node = row["Vertex rank"]
        G.add_node(node,
                   relative_position=tuple(row["Relative position"]),
                   absolute_position=row["Absolute position"],
                   start_time=row["Start time label"],
                   end_time=row["End time label"],
                   leaf=row["Leaf"])

    for _, row in edges_df.iterrows():
        origin, destination = eval(row["Origin-Destination"])
        label = row["Change label"]
        G.add_edge(origin, destination, label=label)
        
    return G


G = load_possession_graph(edges_file, vertices_file)
for _ in G:
    print(G.nodes[_])


plt.figure(figsize=(14, 7))
pos = nx.spring_layout(G, seed=42)
node_labels = {n: f"{n}/n{G.nodes[n]['absolute_position']}" for n in G.nodes()}
edge_labels = nx.get_edge_attributes(G, 'label')

nx.draw(G, pos, with_labels=True, labels=node_labels, node_color='lightcoral', node_size=1000, font_size=8)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
plt.title("Graphe de possession Racing (pédagogie émergente)")
plt.axis('off')
plt.tight_layout()
plt.show()
