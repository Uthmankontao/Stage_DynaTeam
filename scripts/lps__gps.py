import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from tools.fonctions_utiles import nettoyage_tracking, nettoyage_lps, load_fusion_files, get_dictionnaire
from video_basket import create_tracking_animation


def main():
    tracking_1_1_2_1 = "C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/basket/TRACKING/Equipe1_Vague1_Poss2_video_1.txt" # pour chaque possession
    # donner le chemin absolu du fichier
    tracking_df = pd.read_csv(tracking_1_1_2_1, names=['frame', 'player_id', 'x', 'y'], sep=",")
    tracking_df = nettoyage_tracking(tracking_df)

    liste_lps = load_fusion_files("C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/basket/LPS")
    lps_dict = get_dictionnaire(liste_lps)

    tracking_tenseur, delta_t, player_ids_valides = tenseur_tracking(tracking_df, lps_dict)
    results = lsap_gps_lps(tracking_tenseur, lps_dict, delta_t)
    N = len(lps_dict)
    P = len(player_ids_valides)
    assignation = resultat_lsap(results, lps_dict, N, P, player_ids_valides)
    for i in assignation:
        create_tracking_animation(
            tracking_df, lps_dict[i["lps_name"]], 
            t0=i["start_time"], player_id=i["player_id"], 
            output_filename=f"C:/Users/Ousmane Kontao/Desktop/Projet_Data/DATABASE/animation/tracking_animation_superpose_pour{i["player_id"]}.gif")
        

def tenseur_tracking(tracking_df, lps_dict):

    lps_keys = list(lps_dict.keys())
    N = len(lps_keys) # notre nombre de ligne de la matrice des coûts 

    tracking_times = tracking_df["time"].sort_index().unique()
    n_frames = len(tracking_times) # c'est ce qui va nous permettre de connaitre la longueur de la trajectoire
    # pour chaque joueur dans les gps

    delta_t = tracking_times[-1] - tracking_times[0]
    print(f"Cette vidéo dure {(delta_t):.2f} secondes")
    
    tracking_par_joueur = tracking_df.groupby("player_id")
    player_ids = tracking_df["player_id"].unique()
    for i in range(len(player_ids)):
        print(f"Joueur {i}: {len(tracking_par_joueur.get_group(i))} frames")

    player_ids_valides = []
    liste_des_trajectoires = []

    for pid in player_ids:
        trajectoire = tracking_par_joueur.get_group(pid).sort_values("time")
        trajectoire = trajectoire[["time", "x_norm", "y_norm"]].drop_duplicates("time")

        if len(trajectoire) < 0.75 * n_frames:
            continue
        trajectoire_interp = pd.DataFrame({"time" : tracking_times})
        trajectoire_interp = trajectoire_interp.merge(trajectoire, on="time", how="left")

        trajectoire_interp["x_norm"] = trajectoire_interp["x_norm"].interpolate(method="linear", limit_direction="both")
        trajectoire_interp["y_norm"] = trajectoire_interp["y_norm"].interpolate(method="linear", limit_direction="both")

        player_ids_valides.append(pid)
        liste_des_trajectoires.append(trajectoire_interp[["x_norm", "y_norm"]].values)

    tracking = np.stack(liste_des_trajectoires, axis=0)
    print(f"Nous avons desormais un tenseur de tracking de taille {tracking.shape}")

    return tracking, delta_t, player_ids_valides

def lsap_gps_lps(tracking, lps_dict, delta_t):

    results = {} # pour chaque couple (i, j) on aura -->  {'mean_dist' : distance_moyenne, 'start_time' : temps} 

    for i, (name, lps_df) in enumerate(lps_dict.items()):
        lps_times = lps_df["relative_time"].sort_values().unique()

        for t0 in lps_times:
            t_end =  t0 + delta_t
            fenetre_lps = lps_df[(lps_df["relative_time"] >= t0) & (lps_df["relative_time"]<= t_end)]

            if len(fenetre_lps) != tracking.shape[1]:
                continue
            trajectoire_lps = fenetre_lps[["x_norm", "y_norm"]].values

            matrice_distances = np.zeros((tracking.shape[0], 1))

            for j in range(tracking.shape[0]):
                distances = np.linalg.norm(tracking[j] - trajectoire_lps, axis=1)
                matrice_distances[j, 0] = distances.mean()

            # lsap pour affecter un seul joueur au lps
            row_ind, col_ind = linear_sum_assignment(matrice_distances)

            for j in row_ind:
                key = (i, j)
                new_cost = matrice_distances[j, 0]
                if key not in results or new_cost < results[key]["mean_dist"]:
                    results[key] = {"mean_dist" : new_cost, "start_time" : t0}
    return results


def resultat_lsap(results, lps_dict, N, P, player_ids):
    matrice_des_couts = np.full((N, P), np.inf)
    matrice_des_t0 = np.full((N, P), np.nan)

    for (i,j), values in results.items():
        matrice_des_couts[i, j] = values["mean_dist"]
        matrice_des_t0[i,j] = values["start_time"]

    row_ind, col_ind = linear_sum_assignment(matrice_des_couts)
    assignation = []

    for i,j in zip(row_ind, col_ind):
        cost = matrice_des_couts[i, j]
        t0 = matrice_des_t0[i, j]
        lps_name = list(lps_dict.keys())[i]
        player_id = player_ids[j]
        assignation.append({
            'lps_index': i,
            'lps_name': lps_name,
            'player_index': j,
            'player_id': player_id,
            'cost': cost,
            'start_time': t0
        })
    for a in assignation:
        print(f"LPS '{a['lps_name']}' → Joueur {a['player_id']} | coût = {a['cost']:.3f} | t0 = {a['start_time']:.2f}")
    return assignation

main()



