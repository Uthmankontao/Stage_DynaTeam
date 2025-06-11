import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_tracking_animation(df_tracking, df_lps, t0, player_id=None, output_filename='tracking_animation.gif', base_datetime=None):
    """
    Crée une animation GIF avec superposition des données tracking et LPS :
    - Graphique unique : Positions de tous les joueurs (tracking) + trajectoires tracking + trajectoire LPS superposée
    
    Parameters:
    -----------
    df_tracking : pandas.DataFrame
        DataFrame contenant les données de tracking avec colonnes :
        frame, player_id, x, y, time, x_norm, y_norm
    df_lps : pandas.DataFrame
        DataFrame LPS avec colonnes :
        timestamp, latitude_fusion, longitude_fusion, x, y, x_norm, y_norm, datetime, relative_time
    t0 : datetime, str, int, ou float
        Temps de départ de la vidéo LPS
        - Si datetime/str : temps absolu
        - Si int/float : secondes depuis base_datetime (ou depuis une référence)
    player_id : int, optional
        ID du joueur à suivre individuellement (par défaut le premier)
    output_filename : str
        Nom du fichier GIF de sortie
    base_datetime : datetime ou str, optional
        Temps de référence si t0 est un nombre (par défaut: premier timestamp des données LPS)
    """
    
    # Convertir t0 en datetime si c'est une string ou un nombre
    if isinstance(t0, str):
        t0 = pd.to_datetime(t0)
    elif isinstance(t0, (int, float)):
        # Si t0 est un nombre (secondes), utiliser une référence de base
        if base_datetime is None:
            # Utiliser le premier timestamp des données LPS comme référence
            if not df_lps.empty and 'datetime' in df_lps.columns:
                base_time = pd.to_datetime(df_lps['datetime'].iloc[0])
            else:
                # Référence par défaut basée sur vos données
                base_time = pd.to_datetime('2023-12-13 14:35:13')
        else:
            base_time = pd.to_datetime(base_datetime)
        
        t0 = base_time + timedelta(seconds=t0)
    
    # Préparer les données de tracking
    df_tracking = df_tracking.copy()
    df_lps = df_lps.copy()
    
    # Préparer les données LPS
    df_lps['datetime'] = pd.to_datetime(df_lps['datetime'])
    
    # Trouver le point de départ dans df_lps correspondant à t0
    if isinstance(t0, (pd.Timestamp, datetime)):
        # Trouver l'index le plus proche de t0 dans df_lps
        time_diffs = abs(df_lps['datetime'] - t0)
        lps_start_idx = time_diffs.idxmin()
    else:
        # t0 est un temps relatif
        if 'relative_time' in df_lps.columns:
            time_diffs = abs(df_lps['relative_time'] - t0)
            lps_start_idx = time_diffs.idxmin()
        else:
            lps_start_idx = 0
    
    print(f"Point de départ LPS trouvé à l'index: {lps_start_idx}")
    print(f"Temps de départ LPS: {df_lps.iloc[lps_start_idx]['datetime']}")
    
    # Calculer la durée maximale de la vidéo tracking
    max_tracking_time = df_tracking['time'].max()
    print(f"Durée maximale du tracking: {max_tracking_time:.1f} secondes")
    
    # Filtrer les données LPS pour ne prendre que la durée équivalente au tracking
    lps_filtered = df_lps.iloc[lps_start_idx:].copy()
    if 'relative_time' in lps_filtered.columns:
        lps_start_time = lps_filtered.iloc[0]['relative_time']
        lps_filtered = lps_filtered[
            lps_filtered['relative_time'] <= (lps_start_time + max_tracking_time)
        ]
    else:
        # Calculer le temps relatif basé sur datetime
        lps_start_datetime = lps_filtered.iloc[0]['datetime']
        lps_filtered['temp_relative'] = (lps_filtered['datetime'] - lps_start_datetime).dt.total_seconds()
        lps_filtered = lps_filtered[lps_filtered['temp_relative'] <= max_tracking_time]
    
    print(f"Données LPS filtrées: {len(lps_filtered)} points")
    
    # Obtenir les frames uniques pour l'animation
    unique_frames = sorted(df_tracking['frame'].unique())
    
    # Si pas de player_id spécifié, prendre le premier joueur disponible
    if player_id is None:
        player_id = df_tracking['player_id'].iloc[0]
    
    # Configuration de la figure avec style sombre - Un seul graphique large
    plt.style.use('dark_background')
    fig, ax = plt.subplots(1, 1, figsize=(18, 12), facecolor='black')
    fig.suptitle('Animation: Joueur Tracking Spécifique + LPS', 
                fontsize=20, color='white', y=0.96)
    
    # Utiliser les coordonnées normalisées pour une meilleure visualisation
    coord_x = 'x_norm'
    coord_y = 'y_norm'
    
    # Calculer les limites globales (tracking + LPS)
    all_x = list(df_tracking[coord_x]) + (list(lps_filtered[coord_x]) if not lps_filtered.empty else [])
    all_y = list(df_tracking[coord_y]) + (list(lps_filtered[coord_y]) if not lps_filtered.empty else [])
    
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    
    # Ajouter une marge
    x_margin = (x_max - x_min) * 0.15
    y_margin = (y_max - y_min) * 0.15
    
    # Configuration du graphique unique - Style sombre élégant
    ax.set_xlim(x_min - x_margin, x_max + x_margin)
    ax.set_ylim(y_min - y_margin, y_max + y_margin)
    ax.set_xlabel('X', color='white', fontsize=14, fontweight='bold')
    ax.set_ylabel('Y', color='white', fontsize=14, fontweight='bold')
    ax.set_title(f'Joueur {player_id}: Tracking + LPS', 
                color='white', fontsize=16, pad=25)
    ax.grid(True, alpha=0.2, color='gray', linestyle='--', linewidth=0.8)
    ax.set_facecolor('black')
    ax.tick_params(colors='white', labelsize=11)
    
    # Styliser les bordures
    for spine in ax.spines.values():
        spine.set_color('white')
        spine.set_linewidth(1.5)
    
    # Créer une palette de couleurs vibrantes pour le fond noir
    unique_players = sorted(df_tracking['player_id'].unique())
    # Utiliser des couleurs vives qui ressortent sur fond noir
    bright_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', 
                    '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43',
                    '#FD79A8', '#FDCB6E', '#A29BFE', '#74B9FF', '#81ECEC',
                    '#E17055', '#00B894', '#E84393', '#FDFF00', '#FF3838']
    
    # Si plus de joueurs que de couleurs prédéfinies, compléter avec tab20
    if len(unique_players) > len(bright_colors):
        extra_colors = plt.cm.tab20(np.linspace(0, 1, len(unique_players) - len(bright_colors)))
        colors = bright_colors + [f"#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}" for c in extra_colors[:,:3]]
    else:
        colors = [bright_colors[i % len(bright_colors)] for i in range(len(unique_players))]
    
    player_colors = dict(zip(unique_players, colors))
    
    # Initialiser les objets graphiques
    tracking_scatters = {}
    tracking_texts = {}
    tracking_trails = {}  # Pour la trajectoire du joueur spécifique
    
    # Trajectoire LPS avec style distinctif (cyan/turquoise)
    lps_line, = ax.plot([], [], color="#FF0000", alpha=0.9, linewidth=5, 
                    label=f'LPS Joueur {player_id}', linestyle='-',
                    zorder=3)
    lps_point = ax.scatter([], [], c="#FF0000", s=350, 
                        zorder=7, edgecolors='white', linewidth=3, marker='D')
    
    # Trajectoire complète LPS en arrière-plan (fantôme)
    if not lps_filtered.empty:
        ax.plot(lps_filtered[coord_x], lps_filtered[coord_y], 
            color="#FF0000", alpha=0.15, linewidth=2, linestyle=':', 
            zorder=1)
    
    # Initialiser la trajectoire de tracking pour le joueur spécifié seulement
    tracking_trail_line, = ax.plot([], [], color=player_colors[player_id], alpha=0.7, 
                                linewidth=3.5, linestyle='-', zorder=2)
    
    # Créer une légende organisée et simplifiée
    legend_elements = []
    
    # Ajouter LPS en premier (élément principal)
    legend_elements.append(plt.Line2D([0], [0], color='#00FFFF', linewidth=4, 
                                    label=f'LPS Trajectoire'))
    
    # Ajouter seulement le joueur tracking suivi
    legend_elements.append(plt.Line2D([0], [0], color=player_colors[player_id], 
                                    linewidth=3.5, label=f'🏃 Tracking Joueur {player_id}'))
    
    # Ajouter les autres joueurs tracking (positions seulement, sans trajectoires)
    for pid in unique_players:
        if pid != player_id:
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=player_colors[pid], markersize=8,
                                            linestyle='None', label=f'● Joueur {pid}'))
    
    # Créer la légende avec un style amélioré
    legend = ax.legend(handles=legend_elements, loc='upper left', 
                    bbox_to_anchor=(1.02, 1), fancybox=True, shadow=True,
                    facecolor='black', edgecolor='white', 
                    labelcolor='white', fontsize=11, framealpha=0.9)
    
    legend.get_frame().set_linewidth(2)
    
    # Ajuster la mise en page pour faire de la place à la légende
    plt.subplots_adjust(right=0.8)
    
    # Texte pour afficher les informations - Style amélioré
    info_text = fig.text(0.02, 0.02, '', ha='left', fontsize=11, 
                        color='white', weight='bold',
                        bbox=dict(boxstyle="round,pad=0.5", facecolor='black', 
                                alpha=0.8, edgecolor='white'))
    
    # Zone d'information en haut à gauche
    stats_text = fig.text(0.02, 0.85, '', ha='left', va='top', fontsize=10, 
                        color='white',
                        bbox=dict(boxstyle="round,pad=0.4", facecolor='black', 
                                alpha=0.7, edgecolor='gray'))
    
    def animate(frame_idx):
        if frame_idx >= len(unique_frames):
            return (list(tracking_scatters.values()) + list(tracking_texts.values()) + 
                [tracking_trail_line, lps_line, lps_point, info_text, stats_text])
            
        current_frame = unique_frames[frame_idx]
        
        # Données pour le frame actuel (tous les joueurs tracking)
        current_data = df_tracking[df_tracking['frame'] == current_frame]
        
        # Nettoyer les anciens objets tracking
        for scatter in tracking_scatters.values():
            scatter.remove()
        for text in tracking_texts.values():
            text.remove()
        tracking_scatters.clear()
        tracking_texts.clear()
        
        if len(current_data) > 0:
            current_time = current_data['time'].iloc[0]
            
            # Mettre à jour la trajectoire de tracking pour le joueur spécifié seulement
            player_history = df_tracking[
                (df_tracking['player_id'] == player_id) & 
                (df_tracking['time'] <= current_time)
            ].sort_values('time')
            
            if len(player_history) > 1:
                tracking_trail_line.set_data(
                    player_history[coord_x].values,
                    player_history[coord_y].values
                )
            else:
                tracking_trail_line.set_data([], [])
            
            # Créer les scatter plots pour chaque joueur avec leurs numéros
            for _, player_data in current_data.iterrows():
                pid = player_data['player_id']
                x_pos = player_data[coord_x]
                y_pos = player_data[coord_y]
                
                # Taille spéciale pour le joueur suivi
                size = 400 if pid == player_id else 280
                alpha = 1.0 if pid == player_id else 0.85
                edge_width = 4 if pid == player_id else 2
                
                # Scatter plot pour le joueur avec effet de glow
                scatter = ax.scatter(x_pos, y_pos, 
                                c=[player_colors[pid]], 
                                s=size, alpha=alpha, 
                                edgecolors='white', linewidth=edge_width,
                                zorder=5)
                tracking_scatters[pid] = scatter
                
                # Texte avec le numéro du joueur - Style amélioré
                text_size = 15 if pid == player_id else 12
                text_weight = 'bold'
                text = ax.text(x_pos, y_pos, str(pid), 
                            ha='center', va='center', 
                            fontsize=text_size, fontweight=text_weight,
                            color='black', zorder=6,
                            bbox=dict(boxstyle="circle,pad=0.15", 
                                    facecolor='white', alpha=0.95,
                                    edgecolor='black' if pid == player_id else 'gray'))
                tracking_texts[pid] = text
            
            # Trouver les données LPS correspondantes jusqu'à ce temps
            if 'relative_time' in lps_filtered.columns:
                lps_start_relative = lps_filtered.iloc[0]['relative_time']
                target_time = lps_start_relative + current_time
                lps_until_now = lps_filtered[lps_filtered['relative_time'] <= target_time]
            else:
                # Utiliser temp_relative calculé plus tôt
                lps_until_now = lps_filtered[lps_filtered['temp_relative'] <= current_time]
            
            if len(lps_until_now) > 0:
                # Mettre à jour la trajectoire LPS
                lps_line.set_data(
                    lps_until_now[coord_x].values,
                    lps_until_now[coord_y].values
                )
                
                # Position actuelle dans LPS
                current_lps_pos = lps_until_now.iloc[-1]
                lps_point.set_offsets([[
                    current_lps_pos[coord_x],
                    current_lps_pos[coord_y]
                ]])
                
                # Affichage du temps et des informations
                if isinstance(t0, (pd.Timestamp, datetime)):
                    actual_time = t0 + timedelta(seconds=current_time)
                    time_display = actual_time.strftime("%H:%M:%S")
                else:
                    total_time = t0 + current_time
                    time_display = f"{total_time:.1f}s"
                
                # Calculer la distance parcourue en LPS
                if len(lps_until_now) > 1:
                    distances = np.sqrt(np.diff(lps_until_now[coord_x])**2 + np.diff(lps_until_now[coord_y])**2)
                    total_distance = np.sum(distances)
                    avg_speed = total_distance / current_time if current_time > 0 else 0
                else:
                    total_distance = 0
                    avg_speed = 0
                
                info_text.set_text(f'Frame: {current_frame} | Temps: {time_display} | '
                                f'Temps relatif: {current_time:.1f}s | Points LPS: {len(lps_until_now)}')
                
                stats_text.set_text(f'Joueur Tracking suivi: {player_id}\n'
                                f'Distance LPS: {total_distance:.1f}m\n'
                                f'Vitesse moy. LPS: {avg_speed:.1f}m/s\n'
                                f'Joueurs visibles: {len(current_data)}\n'
                                f'Trajectoire tracking: {"Oui" if len(player_history) > 1 else "Non"}')
            else:
                # Pas encore de données LPS
                lps_line.set_data([], [])
                lps_point.set_offsets(np.empty((0, 2)))
                info_text.set_text(f'Frame: {current_frame} | Temps relatif: {current_time:.1f}s | '
                                f'En attente des données LPS...')
                stats_text.set_text(f'Joueur Tracking suivi: {player_id}\n'
                                f'Joueurs visibles: {len(current_data)}\n'
                                f'Trajectoire tracking: {"Oui" if len(player_history) > 1 else "Non"}\n'
                                f'Synchronisation en cours...')
        
        return (list(tracking_scatters.values()) + list(tracking_texts.values()) + 
            [tracking_trail_line, lps_line, lps_point, info_text, stats_text])
    
    # Créer l'animation
    total_frames = len(unique_frames)
    target_duration = 18  # secondes (un peu plus long pour apprécier les trajectoires)
    interval = max(90, int((target_duration * 1000) / total_frames))  # millisecondes
    
    print(f"Création de l'animation avec trajectoire spécifique...")
    print(f"- {total_frames} frames")
    print(f"- Intervalle: {interval}ms par frame")
    print(f"- Durée estimée: {(total_frames * interval) / 1000:.1f} secondes")
    print(f"- Joueur Tracking suivi: {player_id}")
    print(f"- Nombre total de joueurs tracking: {df_tracking['player_id'].nunique()}")
    print(f"- Temps de synchronisation t0: {t0}")
    print(f"- Fonctionnalités: Positions tous joueurs + Trajectoire tracking joueur {player_id} + Trajectoire LPS")
    
    anim = animation.FuncAnimation(
        fig, animate, frames=total_frames,
        interval=interval, blit=False, repeat=True
    )
    
    # Sauvegarder en GIF
    print(f"Sauvegarde de l'animation: {output_filename}")
    try:
        anim.save(output_filename, writer='pillow', fps=1000/interval, dpi=120)
        print(f"Animation avec trajectoire spécifique sauvegardée avec succès: {output_filename}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        # Essayer avec imagemagick si pillow échoue
        try:
            anim.save(output_filename, writer='imagemagick', fps=1000/interval, dpi=120)
            print(f"Animation sauvegardée avec imagemagick: {output_filename}")
        except Exception as e2:
            print(f"Erreur avec imagemagick aussi: {e2}")
    
    plt.tight_layout()
    return anim


# Appel de la fonction
"""create_tracking_animation(
    tracking_df, lps_dict[0], 
    t0=4992.60, player_id=1, 
    output_filename="../../DATABASE/animation/tracking_animation_superpose.gif"
)"""