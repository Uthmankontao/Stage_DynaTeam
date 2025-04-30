<<<<<<< HEAD
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

# Load data
df = pd.read_csv('C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/tracking GPS - pedagogie emergente.csv')

# Filter data for possession = 1 and exclude the ball
df_possession_1 = df[(df['Possession'] == 1) & (df['GPS'] != 'Ball')]

# Filter data for possession = 1 for the ball
df_possession_1_ball = df[(df['Possession'] == 1) & (df['GPS'] == 'Ball')]

# Get unique players and remove player 16
players = df_possession_1['Player'].unique()
players = np.array([player for player in players if player != 16])

# Get team for each player (first occurrence)
player_teams = {}
for player in players:
    team = df_possession_1[df_possession_1['Player'] == player]['Team'].iloc[0]
    player_teams[player] = team

# Get the unique Time numbers and sort them
times = sorted(df_possession_1['Time'].unique())


# Create figure and set up the plot
fig, ax = plt.subplots(figsize=(10, 7))

# Draw a simplified field
ax.set_xlim(-10, 50)  # Adjust according to your dimensions
ax.set_ylim(-40, 10)
ax.set_title('Player Positions Over Time (Red = Att, Blue = Def, Green = Ball)')
ax.set_xlabel('X Position')
ax.set_ylabel('Y Position')

# Initialize scatter plots for each player
scatters = {}

# Create a scatter plot for each player with team-based colors (Att = red, Def = blue)
for player in players:
    team = player_teams[player]
    color = 'red' if team == 'Att' else 'blue'
    scatters[player] = ax.scatter([], [], s=100, label=f'P{int(player)}', color=color)

# Create a scatter plot for the ball (smaller green point)
ball_scatter = ax.scatter([], [], s=50, color='green', zorder=5)  # zorder ensures ball appears on top

# Create custom handles for the team colors and ball legend
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Att Team'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Def Team'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Ball')
]

# Add the team legend
team_legend = ax.legend(handles=legend_elements, loc='upper left')
ax.add_artist(team_legend)

# Create a separate legend for player numbers
player_handles = [plt.Line2D([0], [0], marker='o', color='w', 
                            markerfacecolor='red' if player_teams[player] == 'Att' else 'blue', 
                            markersize=8, label=f'P{int(player)}')
                 for player in players]
player_legend = ax.legend(handles=player_handles, loc='upper right', ncol=2)
ax.add_artist(player_legend)

ax.grid(True, linestyle='--', alpha=0.7)

def init():
    # Initialize the animation with empty data
    for player in players:
        scatters[player].set_offsets(np.empty((0, 2)))
    ball_scatter.set_offsets(np.empty((0, 2)))
    return list(scatters.values()) + [ball_scatter]

def update(time):
    frame_data = df_possession_1[df_possession_1['Time'] == time]
    
    for player in players:
        player_frame_data = frame_data[frame_data['Player'] == player]
        if not player_frame_data.empty:
            x = player_frame_data['X'].values[0]
            y = player_frame_data['Y'].values[0]
            scatters[player].set_offsets([[x, y]])
        else:
            scatters[player].set_offsets(np.empty((0, 2)))
    
    ball_frame_data = df_possession_1_ball[df_possession_1_ball['Time'] == time]
    if not ball_frame_data.empty:
        ball_x = ball_frame_data['X'].values[0]
        ball_y = ball_frame_data['Y'].values[0]
        ball_scatter.set_offsets([[ball_x, ball_y]])
    else:
        ball_scatter.set_offsets(np.empty((0, 2)))
    
    ax.set_title(f'Player Positions - Time: {time:.2f}s (Red = Att, Blue = Def, Green = Ball)')
    
    return list(scatters.values()) + [ball_scatter]


# Create animation with the correct time
ani = FuncAnimation(
    fig,
    update,
    frames=times,
    init_func=init,
    interval=10,  # Tu peux adapter cela pour coller au pas de temps réel
    blit=True,
    repeat=True
)


plt.tight_layout()
plt.show()

# If you want to save the animation as a video file:
=======
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

# Load data
df = pd.read_csv('C:/Users/Rémi/Documents/stage/stage_Dynateam/Stage_DynaTeam/data/donnees_brute/Etude 4.3. rugby/data/tracking GPS - pedagogie emergente.csv')

# Filter data for possession = 1 and exclude the ball
df_possession_1 = df[(df['Possession'] == 1) & (df['GPS'] != 'Ball')]

# Filter data for possession = 1 for the ball
df_possession_1_ball = df[(df['Possession'] == 1) & (df['GPS'] == 'Ball')]

# Get unique players and remove player 16
players = df_possession_1['Player'].unique()
players = np.array([player for player in players if player != 16])

# Get team for each player (first occurrence)
player_teams = {}
for player in players:
    team = df_possession_1[df_possession_1['Player'] == player]['Team'].iloc[0]
    player_teams[player] = team

# Get the unique Time numbers and sort them
times = sorted(df_possession_1['Time'].unique())


# Create figure and set up the plot
fig, ax = plt.subplots(figsize=(10, 7))

# Draw a simplified field
ax.set_xlim(-10, 50)  # Adjust according to your dimensions
ax.set_ylim(-40, 10)
ax.set_title('Player Positions Over Time (Red = Att, Blue = Def, Green = Ball)')
ax.set_xlabel('X Position')
ax.set_ylabel('Y Position')

# Initialize scatter plots for each player
scatters = {}

# Create a scatter plot for each player with team-based colors (Att = red, Def = blue)
for player in players:
    team = player_teams[player]
    color = 'red' if team == 'Att' else 'blue'
    scatters[player] = ax.scatter([], [], s=100, label=f'P{int(player)}', color=color)

# Create a scatter plot for the ball (smaller green point)
ball_scatter = ax.scatter([], [], s=50, color='green', zorder=5)  # zorder ensures ball appears on top

# Create custom handles for the team colors and ball legend
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Att Team'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Def Team'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=8, label='Ball')
]

# Add the team legend
team_legend = ax.legend(handles=legend_elements, loc='upper left')
ax.add_artist(team_legend)

# Create a separate legend for player numbers
player_handles = [plt.Line2D([0], [0], marker='o', color='w', 
                            markerfacecolor='red' if player_teams[player] == 'Att' else 'blue', 
                            markersize=8, label=f'P{int(player)}')
                 for player in players]
player_legend = ax.legend(handles=player_handles, loc='upper right', ncol=2)
ax.add_artist(player_legend)

ax.grid(True, linestyle='--', alpha=0.7)

def init():
    # Initialize the animation with empty data
    for player in players:
        scatters[player].set_offsets(np.empty((0, 2)))
    ball_scatter.set_offsets(np.empty((0, 2)))
    return list(scatters.values()) + [ball_scatter]

def update(time):
    frame_data = df_possession_1[df_possession_1['Time'] == time]
    
    for player in players:
        player_frame_data = frame_data[frame_data['Player'] == player]
        if not player_frame_data.empty:
            x = player_frame_data['X'].values[0]
            y = player_frame_data['Y'].values[0]
            scatters[player].set_offsets([[x, y]])
        else:
            scatters[player].set_offsets(np.empty((0, 2)))
    
    ball_frame_data = df_possession_1_ball[df_possession_1_ball['Time'] == time]
    if not ball_frame_data.empty:
        ball_x = ball_frame_data['X'].values[0]
        ball_y = ball_frame_data['Y'].values[0]
        ball_scatter.set_offsets([[ball_x, ball_y]])
    else:
        ball_scatter.set_offsets(np.empty((0, 2)))
    
    ax.set_title(f'Player Positions - Time: {time:.2f}s (Red = Att, Blue = Def, Green = Ball)')
    
    return list(scatters.values()) + [ball_scatter]


# Create animation with the correct time
ani = FuncAnimation(
    fig,
    update,
    frames=times,
    init_func=init,
    interval=10,  # Tu peux adapter cela pour coller au pas de temps réel
    blit=True,
    repeat=True
)


plt.tight_layout()
plt.show()

# If you want to save the animation as a video file:
>>>>>>> 7a8c9535ac269acfd3585b3f7f3fecdca98a0af4
# ani.save('player_movement.mp4', writer='ffmpeg', fps=10)