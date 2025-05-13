import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def draw_rugby_field(ax):

    field_length = 35
    field_width = 35

    # Fond du terrain (vert)
    field_color = '#4c9b4c'
    ax.set_facecolor(field_color)
    
    try_zone_end = field_length
    
    # Dessin des quatre zones avec des opacités différentes
    # Zone BACK (0-20)
    back_rect = Rectangle((-10, -field_width/2 - 15), 15, field_width, 
                         facecolor=field_color, alpha=0.7, edgecolor='gray', linewidth=1)
    ax.add_patch(back_rect)
    ax.text(-2.5, -10, 'BACK', fontsize=14, color='gray', 
            ha='center', va='center', fontweight='bold')
    
    # Zone MIDDLE (20-40)
    middle_rect = Rectangle((5, -field_width/2 - 15), 17.5, field_width, 
                          facecolor=field_color, alpha=0.8, edgecolor='gray', linewidth=1)
    ax.add_patch(middle_rect)
    ax.text(13.75, -10, 'MIDDLE', fontsize=14, color='gray', 
            ha='center', va='center', fontweight='bold')
    
    # Zone FRONT (40-60)
    front_rect = Rectangle((22.5, -field_width/2 - 15), 17.5, field_width, 
                         facecolor=field_color, alpha=0.9, edgecolor='gray', linewidth=1)
    ax.add_patch(front_rect)
    ax.text(32, -10, 'FRONT', fontsize=14, color='gray', 
           ha='center', va='center', fontweight='bold')
    
    # Zone TRY
    try_zone = Rectangle((try_zone_end+5, -field_width/2 - 15), 5, field_width, 
                       facecolor='#3c8b3c', alpha=1.0, edgecolor='gray', linewidth=2)
    ax.add_patch(try_zone)
    ax.text(try_zone_end+7.5, -10, 'TRY', fontsize=14, color='gray', 
            ha='center', va='center', fontweight='bold')
    
    # Bordure du terrain
    field_border = Rectangle((-10, -field_width/2 - 15), field_length+15, field_width, 
                           fill=False, edgecolor='gray', linewidth=2)
    ax.add_patch(field_border)