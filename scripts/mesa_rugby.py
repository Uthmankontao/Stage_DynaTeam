from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

# === Classe Joueur ===
class Joueur(Agent):
    def __init__(self, unique_id, model, team):
        super().__init__(unique_id, model)
        self.team = team

    def step(self):
        # Avancer ou reculer selon l'équipe
        x, y = self.pos
        if self.team == 'Att':
            new_y = min(y + 1, self.model.grid.height - 1)
            self.model.grid.move_agent(self, (x, new_y))
        else:
            new_y = max(y - 1, 0)
            self.model.grid.move_agent(self, (x, new_y))

    def advance(self):
        pass  # Pour SimultaneousActivation (nécessaire)

# === Classe du modèle ===
class RugbyModel(Model):
    def __init__(self, width=20, height=20):
        self.num_agents = 6
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)

        # Créer les attaquants
        for i in range(self.num_agents):
            agent = Joueur(i, self, 'Att')
            self.schedule.add(agent)
            self.grid.place_agent(agent, (i + 2, 1))  # Ligne du bas

        # Créer les défenseurs
        for i in range(self.num_agents):
            agent = Joueur(i + 100, self, 'Def')
            self.schedule.add(agent)
            self.grid.place_agent(agent, (i + 2, height - 2))  # Ligne du haut

    def step(self):
        self.schedule.step()

# === Fonction d’affichage ===
def agent_portrayal(agent):
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer": 0,
        "r": 0.8
    }

    if agent.team == "Att":
        portrayal["Color"] = "blue"
        portrayal["text"] = "A"
    else:
        portrayal["Color"] = "red"
        portrayal["text"] = "D"

    # Le premier attaquant a le ballon
    if agent.unique_id == 0:
        portrayal["text"] = "B"
        portrayal["Color"] = "green"
        portrayal["Layer"] = 1

    return portrayal

# === Interface ===
grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)
server = ModularServer(RugbyModel,
                       [grid],
                       "Modèle Rugby avec Mesa",
                       {"width": 20, "height": 20})

server.port = 8521
server.launch()
