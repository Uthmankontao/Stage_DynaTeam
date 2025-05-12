def update(t):
    """
    Met à jour les positions des joueurs et le ballon pour chaque frame de l'animation.
    Affiche les passes possibles et la pression défensive.
    
    :param t: Temps actuel de l'animation.
    :return: Liste des objets à mettre à jour dans l'animation.
    """
    # Effacer les éléments existants
    global passes_lines, blocked_passes_lines, secondary_passes_lines, pressure_lines, influence_zones, text_labels
    for line in passes_lines + blocked_passes_lines + secondary_passes_lines + pressure_lines:
        if line in ax.get_lines() or hasattr(line, 'remove'):
            line.remove()
    for zone in influence_zones:
        zone.remove()
    for txt in text_labels:
        txt.remove()
    passes_lines.clear()
    blocked_passes_lines.clear()
    secondary_passes_lines.clear()
    pressure_lines.clear()
    influence_zones.clear()
    text_labels.clear()
    
    frame_data = df_possession_1[df_possession_1['Time'] == t]
    ball_data = df_possession_1_ball[df_possession_1_ball['Time'] == t]
    if frame_data.empty:
        return []

    possession_id = int(frame_data['Possession'].iloc[0])
    cote = get_cote_for_possession(possession_id, df_seq_1)

    player_pos = {}  # dictionnaire pour stocker les positions des joueurs
    player_gradients = {}  # dictionnaire pour stocker les gradients des joueurs
    
    for p in players:
        pdata = frame_data[frame_data['Player'] == p]
        if not pdata.empty:
            x, y = pdata[['X', 'Y']].values[0]
            scatters[p].set_offsets([[x, y]])
            player_pos[p] = (x, y)
            
            # Récupérer les informations de gradient
            grad_magnitude = pdata['gradient_magnitude'].values[0]
            grad_angle = pdata['gradient_angle'].values[0]
            player_gradients[p] = (grad_magnitude, grad_angle)
            
            txt = ax.text(x, y + 0.8, str(p), fontsize=9, ha='center', color='white',
                          bbox=dict(facecolor='black', alpha=0.5, boxstyle='circle'))
            text_labels.append(txt)
        else:
            scatters[p].set_offsets(np.empty((0, 2)))

    if not ball_data.empty:
        bx, by = ball_data[['X', 'Y']].values[0]
        ball_scatter.set_offsets([[bx, by]])
    
    # Créer des zones d'influence elliptiques pour les défenseurs
    defender_zones = {}
    for d in def_players:
        if d in player_pos and d in player_gradients:
            dpos = player_pos[d]
            speed, angle = player_gradients[d]
            
            # Limiter la vitesse pour éviter des ellipses trop grandes
            speed = min(speed, 20)  
            
            # Calculer les dimensions de l'ellipse en fonction de la vitesse
            # Plus le joueur est rapide, plus l'ellipse est allongée dans la direction du mouvement
            width = BASE_INFLUENCE_RADIUS * (1 + SPEED_SCALING * min(speed, MAX_SPEED_EFFECT))
            height = BASE_INFLUENCE_RADIUS * (1 - 0.3 * min(speed, MAX_SPEED_EFFECT/2))  # Légèrement réduit perpendiculairement
            
            # Calculer le décalage du centre de l'ellipse dans la direction du mouvement
            offset_factor = OFFSET_SCALING * min(speed, MAX_SPEED_EFFECT)  # Le décalage augmente avec la vitesse
            offset_x = offset_factor * np.cos(angle)
            offset_y = offset_factor * np.sin(angle)
            
            # Calculer le centre décalé de l'ellipse (devant le joueur)
            ellipse_center = (dpos[0] + offset_x, dpos[1] + offset_y)
            
            # Créer l'ellipse avec l'orientation dans la direction du mouvement
            ellipse = Ellipse(ellipse_center, width=width, height=height, 
                             angle=np.degrees(angle), color='blue', alpha=0.2, fill=True)
            ax.add_patch(ellipse)
            influence_zones.append(ellipse)
            
            # Stocker les paramètres de l'ellipse pour l'intersection
            defender_zones[d] = (ellipse_center, width, height, angle)
            
            # Ajouter du texte pour la vitesse
            if speed > 0.5:  # Ne montrer que si la vitesse est significative
                txt = ax.text(dpos[0], dpos[1] - 1.2, f"{speed * 3.6:.1f} km/h", 
                             fontsize=7, ha='center', color='cyan')
                text_labels.append(txt)

    # Créer des zones d'influence elliptiques pour les attaquants
    stricker_zones = {}
    for d in att_players:
        if d in player_pos and d in player_gradients:
            dpos = player_pos[d]
            speed, angle = player_gradients[d]
            
            # Limiter la vitesse pour éviter des ellipses trop grandes
            speed = min(speed, 20)  
            
            # Calculer les dimensions de l'ellipse en fonction de la vitesse
            # Plus le joueur est rapide, plus l'ellipse est allongée dans la direction du mouvement
            width = BASE_INFLUENCE_RADIUS * (1 + SPEED_SCALING * min(speed, MAX_SPEED_EFFECT))
            height = BASE_INFLUENCE_RADIUS * (1 - 0.3 * min(speed, MAX_SPEED_EFFECT/2))  # Légèrement réduit perpendiculairement
            
            # Calculer le décalage du centre de l'ellipse dans la direction du mouvement
            offset_factor = OFFSET_SCALING * min(speed, MAX_SPEED_EFFECT)  # Le décalage augmente avec la vitesse
            offset_x = offset_factor * np.cos(angle)
            offset_y = offset_factor * np.sin(angle)
            
            # Calculer le centre décalé de l'ellipse (devant le joueur)
            ellipse_center = (dpos[0] + offset_x, dpos[1] + offset_y)
            
            # Créer l'ellipse avec l'orientation dans la direction du mouvement
            ellipse = Ellipse(ellipse_center, width=width, height=height, 
                             angle=np.degrees(angle), color='red', alpha=0.2, fill=True)
            ax.add_patch(ellipse)
            influence_zones.append(ellipse)
            
            # Stocker les paramètres de l'ellipse pour l'intersection
            stricker_zones[d] = (ellipse_center, width, height, angle)
            
            # Ajouter du texte pour la vitesse
            if speed > 0.5:  # Ne montrer que si la vitesse est significative
                txt = ax.text(dpos[0], dpos[1] - 1.2, f"{speed * 3.6:.1f} km/h", 
                             fontsize=7, ha='center', color='cyan')
                text_labels.append(txt)

    # Passes depuis porteur et identification des receveurs directs
    direct_receivers = []  # liste pour stocker les receveurs directs potentiels
    carrier = frame_data[frame_data['Carrier']]
    
    if not carrier.empty:
        cid = carrier['Player'].iloc[0]
        cpos = player_pos.get(cid)
        
        if cpos:  # vérifier que la position du porteur est disponible
            for p, pos in player_pos.items():
                if p != cid and player_teams[p] == 'Att':
                    dist = np.linalg.norm(np.array(cpos) - np.array(pos))
                    if dist < dynamic_threshold(cpos[0]) and is_backward_pass(cpos, pos, cote):
                        # Vérifier si la passe traverse une zone d'influence d'un défenseur
                        pass_blocked = False
                        for _, (def_pos, width, height, angle) in defender_zones.items():
                            if line_intersects_ellipse(cpos, pos, def_pos, width, height, angle):
                                pass_blocked = True
                                break
                        
                        if pass_blocked:
                            # Tracer les passes bloquées en rouge pointillé
                            arrow = ax.annotate("", 
                                     xy=(pos[0], pos[1]),           # pointe de la flèche
                                     xytext=(cpos[0], cpos[1]),     # base de la flèche
                                     arrowprops=dict(arrowstyle="->", color="red", 
                                                    lw=2, alpha=0.8, linestyle='--'))
                            blocked_passes_lines.append(arrow)
                        else:
                            # Tracer les passes directes valides
                            arrow = ax.annotate("", 
                                     xy=(pos[0], pos[1]),           # pointe de la flèche
                                     xytext=(cpos[0], cpos[1]),     # base de la flèche
                                     arrowprops=dict(arrowstyle="->", color="orange", 
                                                    lw=2, alpha=0.8))
                            passes_lines.append(arrow)
                            direct_receivers.append(p)  # Ajouter ce joueur comme receveur direct
                        
                        txt = ax.text((pos[0] + cpos[0])/2, (pos[1] + cpos[1])/2,
                              f"{dist:.1f}", fontsize=6, color='white')
                        text_labels.append(txt)

            # Tracer les passes secondaires à partir des receveurs directs
            for receiver in direct_receivers:
                receiver_pos = player_pos.get(receiver)
                
                for p, pos in player_pos.items():
                    if p != receiver and p != cid and player_teams[p] == 'Att':
                        dist = np.linalg.norm(np.array(receiver_pos) - np.array(pos))
                        if dist < dynamic_threshold(receiver_pos[0]) and is_backward_pass(receiver_pos, pos, cote):
                            # Vérifier si la passe secondaire traverse une zone d'influence d'un défenseur
                            pass_blocked = False
                            for _, (def_pos, width, height, angle) in defender_zones.items():
                                if line_intersects_ellipse(receiver_pos, pos, def_pos, width, height, angle):
                                    pass_blocked = True
                                    break
                            
                            if pass_blocked:
                                # Tracer les passes secondaires bloquées
                                arrow = ax.annotate("", 
                                         xy=(pos[0], pos[1]),            # pointe de la flèche
                                         xytext=(receiver_pos[0], receiver_pos[1]),  # base de la flèche
                                         arrowprops=dict(arrowstyle="->", color="red", 
                                                        lw=1.5, alpha=0.7, linestyle='--'))
                                blocked_passes_lines.append(arrow)
                            else:
                                # Tracer les passes secondaires valides
                                arrow = ax.annotate("", 
                                         xy=(pos[0], pos[1]),            # pointe de la flèche
                                         xytext=(receiver_pos[0], receiver_pos[1]),  # base de la flèche
                                         arrowprops=dict(arrowstyle="->", color="yellow", 
                                                        lw=1.5, alpha=0.7))
                                secondary_passes_lines.append(arrow)
                            
                            txt = ax.text((pos[0] + receiver_pos[0])/2, (pos[1] + receiver_pos[1])/2,
                                  f"{dist:.1f}", fontsize=6, color='white')
                            text_labels.append(txt)

    # Lien de pression valide uniquement si le défenseur est devant
    for d in def_players:
        if d not in player_pos:
            continue
        dpos = np.array(player_pos[d])
        for a in att_players:
            if a in player_pos:
                apos = np.array(player_pos[a])
                dist = np.linalg.norm(dpos - apos)
                if dist < 7 and is_pressure_valid(dpos, apos, cote):
                    line = ax.plot([dpos[0], apos[0]], [dpos[1], apos[1]],
                                   color='white', linestyle='--', linewidth=1, alpha=0.7)[0]
                    pressure_lines.append(line)
                    txt = ax.text((dpos[0] + apos[0])/2, (dpos[1] + apos[1])/2,
                                  f"{dist:.1f}", fontsize=6, color='white')
                    text_labels.append(txt)

    ax.set_title(f'Temps : {t:.2f}s – Côté : {cote}')
    return (list(scatters.values()) + [ball_scatter] + passes_lines + blocked_passes_lines + 
            secondary_passes_lines + pressure_lines + influence_zones + text_labels)