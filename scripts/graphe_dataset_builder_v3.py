import os
import pandas as pd
import numpy as np
import networkx as nx
from tools.fonctions_utiles import *
from build_graphes_sp import construire_graphe

def main_1():
    """Génère le dataset de graphes en utilisant les fonctions de build_graph_v3"""
    
    # Chargement des données avec la même structure que build_graph_v3
    df_players = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/VANNES_PRESCRIPTIF.csv")
    df_ball = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/VANNES_BALL_PRESCRIPTIF.csv")
    df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/sequencage/vannes_prescriptif.csv", sep=';')
    df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/info_GPS/vannes_prescriptif.csv", sep=';')
    
    # Tri des données
    df_players_sorted = df_players.sort_values(['Possession', 'GPS', 'Time']).copy()
    df_ball_sorted = df_ball.sort_values(['Possession', 'Time']).copy()
    
    # Créer le dossier de sortie
    os.makedirs("graph_dataset", exist_ok=True)
    
    STEP = 5
    
    data = []  # Liste pour stocker les données des graphes
    
    # Parcours des possessions
    for possession_id in df_seq["Possession"].unique():
        print(f"Traitement de la possession {possession_id}")
        
        # Filtrer les données pour cette possession
        # Filtrer pour cette possession
        df_possession = df_players_sorted[df_players_sorted['Possession'] == possession_id].copy()
        df_ball_possession = df_ball_sorted[df_ball_sorted['Possession'] == possession_id].copy()
        df_seq_possession = df_seq[df_seq['Possession'] == possession_id].copy()
        
        if df_possession.empty:
            continue
            
        # Ajouter les colonnes nécessaires (comme dans build_graph_v3)
        df_possession['Carrier'] = False
        df_possession['Player'] = 0
        df_ball_possession['Player'] = 0

        # Correspondance GPS players
        df_possession = cores_GPS_player(df_possession, df_infos)
        df_ball_possession = cores_GPS_player(df_ball_possession, df_infos)
        
        # Obtenir les temps avec échantillonnage
        times = sorted(df_possession["Time"].unique())
        times = times[::STEP]
        
        # Générer les graphes pour chaque instant
        for t in times:
            try:
                # Utiliser directement la fonction construire_graphe de build_graph_v3
                G = construire_graphe(t, df_possession, df_ball_possession, df_infos, df_seq_possession)
                if G is None or len(G.nodes) == 0:
                    continue
                    
                # Sauvegarder le graphe
                fname = f"graph_dataset/pos_{possession_id}_t_{round(t,2)}.gexf"
                nx.write_gexf(G, fname)
                
                # Ajouter aux données
                data.append({
                    "file": fname,
                    "time": t,
                    "possession": possession_id,
                    "nodes_count": len(G.nodes),
                    "edges_count": len(G.edges),
                    "pass_edges": len([(u, v) for u, v, d in G.edges(data=True) if d["type"] == "passe"]),
                    "pressure_edges": len([(u, v) for u, v, d in G.edges(data=True) if d["type"] == "pression"])
                })
                
            except Exception as e:
                print(f"[!] Erreur pour possession {possession_id}, t={t} : {e}")
                continue
    
    # DataFrame final
    labels_df = pd.DataFrame(data)
    labels_df.to_csv("graph_dataset/graph.csv", index=False)
    
    print(f"\nDataset généré avec {len(labels_df)} graphes enregistrés.")
    print(f"Statistiques:")
    print(f"- Possessions traitées: {labels_df['possession'].nunique()}")
    print(f"- Nombre moyen de nœuds par graphe: {labels_df['nodes_count'].mean():.1f}")
    print(f"- Nombre moyen d'arêtes par graphe: {labels_df['edges_count'].mean():.1f}")

def main_2():
    """Génère le dataset de graphes en utilisant les fonctions de build_graph_v3"""
    
    # Chargement des données avec la même structure que build_graph_v3
    df_players = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/VANNES_PRESCRIPTIF.csv")
    df_ball = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/export/VANNES_BALL_PRESCRIPTIF.csv")
    df_seq = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/sequencage/vannes_prescriptif.csv", sep=';')
    df_infos = pd.read_csv("C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/data_v2/data/info_GPS/vannes_prescriptif.csv", sep=';')
    
    # Tri des données
    df_players_sorted = df_players.sort_values(['Possession', 'GPS', 'Time']).copy()
    df_ball_sorted = df_ball.sort_values(['Possession', 'Time']).copy()
    
    # Créer le dossier de sortie
    os.makedirs("graph_dataset_Events", exist_ok=True)
    
    data = []  # Liste pour stocker les données des graphes
    
    # Parcours des possessions
    for possession_id in df_seq["Possession"].unique():
        print(f"Traitement de la possession {possession_id}")
        
        # Filtrer les données pour cette possession
        # Filtrer pour cette possession
        df_possession = df_players_sorted[df_players_sorted['Possession'] == possession_id].copy()
        df_ball_possession = df_ball_sorted[df_ball_sorted['Possession'] == possession_id].copy()
        df_seq_possession = df_seq[df_seq['Possession'] == possession_id].copy()
        
        if df_possession.empty:
            continue
            
        # Ajouter les colonnes nécessaires (comme dans build_graph_v3)
        df_possession['Carrier'] = False
        df_possession['Player'] = 0
        df_ball_possession['Player'] = 0

        # Correspondance GPS players
        df_possession = cores_GPS_player(df_possession, df_infos)
        df_ball_possession = cores_GPS_player(df_ball_possession, df_infos)

        positions = df_seq_possession[df_seq_possession['Passeur'].notna()]['Position'].unique()
        
        df_possession = df_possession[df_possession['Position'].isin(positions)]
        # Obtenir les temps avec échantillonnage
        times = sorted(df_possession["Time"].unique())
        
        # Générer les graphes pour chaque instant
        for t in times:
            try:
                # Utiliser directement la fonction construire_graphe de build_graph_v3
                G = construire_graphe(t, df_possession, df_ball_possession, df_infos, df_seq_possession)
                if G is None or len(G.nodes) == 0:
                    continue
                    
                # Sauvegarder le graphe
                fname = f"graph_dataset_Events/Events_pos_{possession_id}_t_{round(t,2)}.gexf"
                nx.write_gexf(G, fname)
                
                # Ajouter aux données
                data.append({
                    "file": fname,
                    "time": t,
                    "possession": possession_id,
                    "nodes_count": len(G.nodes),
                    "edges_count": len(G.edges),
                    "pass_edges": len([(u, v) for u, v, d in G.edges(data=True) if d["type"] == "passe"]),
                    "pressure_edges": len([(u, v) for u, v, d in G.edges(data=True) if d["type"] == "pression"])
                })
                
            except Exception as e:
                print(f"[!] Erreur pour possession {possession_id}, t={t} : {e}")
                continue
    
    # DataFrame final
    Events_df = pd.DataFrame(data)
    Events_df.to_csv("graph_dataset_Events/graph_Events.csv", index=False)
    
    print(f"\nDataset généré avec {len(Events_df)} graphes enregistrés.")
    print(f"Statistiques:")
    print(f"- Possessions traitées: {Events_df['possession'].nunique()}")
    print(f"- Nombre moyen de nœuds par graphe: {Events_df['nodes_count'].mean():.1f}")
    print(f"- Nombre moyen d'arêtes par graphe: {Events_df['edges_count'].mean():.1f}")


if __name__ == "__main__":
    print("Choisissez la version à exécuter :")
    print("1 - main() : Génération avec échantillonnage temporel (STEP=10)")
    print("2 - main_2() : Génération pour tous les temps disponibles")
    
    while True:
        try:
            choice = input("Votre choix (1 ou 2) : ").strip()
            if choice == "1":
                print("Exécution de main()...")
                main_1()
                break
            elif choice == "2":
                print("Exécution de main_2()...")
                main_2()
                break
            else:
                print("Choix invalide. Veuillez entrer 1 ou 2.")
        except KeyboardInterrupt:
            print("\nOpération annulée.")
            break