def lsap_process(lps_dict, tracking):
    """
    Calcule une matrice de coût [N fichiers LPS, P joueurs tracking]
    avec distance moyenne minimale sur toutes les fenêtres glissantes.
    """
    lps_keys = list(lps_dict.keys())
    N = len(lps_keys)

    tracking_times = tracking['time'].sort_values().unique()
    delta_t = tracking_times[-1] - tracking_times[0]
    n_frames = len(tracking_times)

    # Préparer les trajectoires des joueurs du tracking
    tracking_grouped = tracking.groupby('player_id')
    player_ids = tracking['player_id'].unique()

    valid_player_ids = []
    traj_list = []

    for pid in player_ids:
        traj = tracking_grouped.get_group(pid).sort_values('time')
        if len(traj) == n_frames:
            valid_player_ids.append(pid)
            traj_list.append(traj[['x_norm', 'y_norm']].values)  # (T, 2)

    P = len(valid_player_ids)
    tracking_tensor = np.stack(traj_list, axis=0)  # (P, T, 2)

    cost_matrix = np.full((N, P), np.inf)

    for i, (name, lps_df) in enumerate(lps_dict.items()):
        lps_times = lps_df['relative_time'].sort_values().unique()

        for t0 in lps_times:
            t_end = t0 + delta_t
            lps_window = lps_df[(lps_df['relative_time'] >= t0) & (lps_df['relative_time'] <= t_end)]

            if len(lps_window) != n_frames:
                continue

            lps_traj = lps_window[['x_norm', 'y_norm']].values  # (T, 2)

            for j in range(P):
                dists = np.linalg.norm(tracking_tensor[j] - lps_traj, axis=1)
                mean_dist = dists.mean()

                # Mettre à jour si c’est meilleur
                if mean_dist < cost_matrix[i, j]:
                    cost_matrix[i, j] = mean_dist

    return cost_matrix, lps_keys, valid_player_ids
