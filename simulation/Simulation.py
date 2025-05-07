import random

import simpy
import tkinter as tk
from simulation import LübeckACTR
from simulation.Middleman import Middleman
from simulation.Game import Game
from simulation.AgentConstruct import AgentConstruct
from simulation.AgentTypeReturner import AgentTypeReturner
import simulation.LevelBuilder as levelbuilder
import pyactr as actr


class Simulation:
    """
    Creates all objects and coordinates time

    Attributes:
        focus_position (tuple): Initial focus position of the agents eyes
        print_middleman (bool): Logging translation between environment and agents
        width (int): Amount of cells in the world
        height (int): Amount of cells in the world
        food_amount (int): How many food sources will occur in the world
        wall_density (float): In %, the density of walls for world generation
        speed_factor (float): In %, the speed of the simulation. 100 is real time cognition of the agents
        print_agent_actions (bool): If False, turn off all agents internal logging simultaniously
        agent_type_config (dict): .py Class name of your agent, amount and if you want to display their logs

        global_sim_time (float): Used for synchronising the gui with the cognition time
        agent_list (list): All agents participating in the simulation
        root (Tkinter()): GUI of the simulation
        agent_type_returner (AgentTypeReturner): Returns the actr agent and its Adapter
        actr_environment (pyactr.Environment()): Environment in which the visual stimuli will appear
        middleman (Middleman): Translates changes between the environment and the agents
    """

    def __init__(self):
        # Configuration
        self.level_type = "Perception & Action 1"
        self.focus_position = (0, 2)
        self.print_middleman = False
        self.width = 5
        self.height = 5
        self.food_amount = 3
        self.wall_density = 0
        self.speed_factor = 50
        self.print_agent_actions = True
        self.agent_type_config = {
            "Mew": {"count": 1, "pokedex_id": 151, "print_agent_actions": True}
            #"Charmander": {"count": 1, "pokedex_id": 4, "print_agent_actions": False},
            #"Victreebel": {"count": 1, "pokedex_id": 71, "print_agent_actions": False}
            #"Pinsir": {"count": 1, "pokedex_id": 127, "print_agent_actions": False}
            #"Deoxis": {"count": 1, "pokedex_id": 386, "print_agent_actions": False}
            #"Dakrai": {"count": 1, "pokedex_id": 491, "print_agent_actions": False}
        }

        # Critical
        self.global_sim_time = 0
        self.agent_list = []
        self.root = tk.Tk()
        self.agent_type_returner = AgentTypeReturner()
        self.actr_environment = actr.Environment(focus_position=self.focus_position)
        self.middleman = Middleman(self, self.print_middleman)

    def agent_builder(self):
        """
        Creates all agent objects with its components.
        """
        with open("gui/sprites/pokemon/pokemonNames.txt", 'r') as file:
            names = file.read().splitlines()
        original_names = names.copy()
        random.shuffle(names)

        # Creates agent constructs, which hold all information of one agent.
        for agent_type, config in self.agent_type_config.items():
            count = config["count"]
            print_actions = config.get("print_agent_actions", self.print_agent_actions)
            pokedex_id = config.get("pokedex_id")

            for i in range(count):
                if pokedex_id is not None:
                    name_number = pokedex_id
                    name = original_names[name_number - 1]
                else:
                    name = names.pop()
                    name_number = original_names.index(name) + 1

                agent = AgentConstruct(agent_type, self.actr_environment, None, self.middleman, name, name_number)
                agent.actr_time = 0
                agent.print_agent_actions = print_actions
                self.agent_list.append(agent)

        # Adding more information to the construct, so that one agent is able to distinguish other agents.
        for agent in self.agent_list:
            agent.set_agent_dictionary(self.agent_list)
            agent_id_list = list(agent.get_agent_dictionary())
            actr_construct, actr_agent, actr_adapter = self.agent_type_returner.return_agent_type(
                agent.actr_agent_type_name, self.actr_environment, agent_id_list
            )
            agent.set_actr_agent(actr_agent)
            agent.set_actr_adapter(actr_adapter)
            agent.set_simulation()
            agent.set_actr_construct(actr_construct)

    def run_simulation(self):
        """
        Initialises the simulation (building agents, middleman and game, then entering execution loop and start gui)
        """
        self.agent_builder()
        level_matrix = levelbuilder.build_level(
            self.height, self.width, self.agent_list, self.food_amount, self.wall_density, self.level_type
        )
        self.game_environment = Game(self.root, level_matrix)
        self.middleman.set_game_environment(self.game_environment)
        self.execute_step()
        self.root.mainloop()

    def execute_step(self):
        """
        Schedules the agents based on their cognition time. Allows the cognitive fastest agent to step.
        """

        # Refresh agents visual stimuli, to keep their buffers up to date. Can't be moved to other method,
        # because deadlocks could arise.
        for agent in self.agent_list:
            agent.update_stimulus()

        # Scheduling
        self.agent_list.sort(key=lambda agent: agent.actr_time)
        next_agent = self.agent_list[0]
        delay = next_agent.actr_time - self.global_sim_time
        factor = 100 / self.speed_factor
        delay_ms = round(delay * factor * 1000)
        if delay_ms < 1:
            delay_ms = 1

        # Execution
        self.root.after(delay_ms, lambda: self.execute_agent_step(next_agent))

    def execute_agent_step(self, agent):
        """
        Executes a cognitive step. Also handles errors like empty schedules (by reset) or inactivity (by removal).

        Args:
            agent (AgentConstruct): the cognitive active agent
        """
        try:
            agent.simulation.step()
            event = agent.simulation.current_event

            # Measuring cognitive time. Removal after ten cognitive deadlocks
            if event.time > 0 or self.level_type is not None:
                agent.no_increase_count = 0
            else:
                agent.no_increase_count = getattr(agent, "no_increase_count", 0) + 1

            if agent.no_increase_count >= 10:
                print(f"{agent.name} removed due to 10 consecutive steps with no actr_time increase.")
                if agent in self.agent_list:
                    self.agent_list.remove(agent)
                self.game_environment.remove_agent_from_game(agent)
            else:
                # Refresh time for the agent and the global simulation
                agent.actr_time += event.time
                self.global_sim_time = agent.actr_time

                # Further execution
                agent.actr_extension()
                if getattr(agent, "print_agent_actions", self.print_agent_actions):
                    print(f"{agent.name}, {agent.actr_time}, {event[1]}, {event[2]}")
                key = LübeckACTR.key_pressed(agent)
                if key:
                    self.middleman.motor_input(key, agent)

            # Return recursively
            self.execute_step()

        # Error handling
        except (simpy.core.EmptySchedule, AttributeError, IndexError, RuntimeError) as e:
            if "has terminated" in str(e):
                print(
                    f"{agent.name}, {agent.actr_time}, Oh no! Your agent's simulation process has terminated. Resetting to initial goal!")
            else:
                print(
                    f"{agent.name}, {agent.actr_time}, Oh no! Your agent has no production to fire :( Reset to initial goal!")
            agent.handle_empty_schedule()
            self.root.after_idle(lambda: self.execute_step())

    def notify_gui(self):
        """
        Causes gui to refresh
        """
        if hasattr(self, 'gui'):
            self.gui.update()
