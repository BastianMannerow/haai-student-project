import os
import random

import simpy
import tkinter as tk
from simulation import BastiACTR
from simulation.Middleman import Middleman
from simulation.Game import Game
from simulation.AgentConstruct import AgentConstruct
from simulation.AgentTypeReturner import AgentTypeReturner
import simulation.LevelBuilder as levelbuilder
import pyactr as actr


class Simulation:
    def __init__(self):
        self.agent_list = []
        self.root = tk.Tk()
        self.latency_factor_agent_actions = 1000  # in ms
        self.print_middleman = False
        self.middleman = Middleman(self, self.print_middleman)
        self.population_size = 2
        self.focus_position = (0, 2)
        self.agent_type_returner = AgentTypeReturner()
        self.actr_environment = actr.Environment(focus_position=self.focus_position)
        self.print_agent_actions = True

        # World configuration
        self.width = 9
        self.height = 9
        self.food_amount = 2
        self.wall_density = 10

    def agent_builder(self):
        """
        Builds all ACT-R agents
        """
        with open("gui/sprites/pokemon/pokemonNames.txt", 'r') as file:
            names = file.read().splitlines()

        original_names = names.copy()  # Keep a copy of the original list to avoid index errors with the sprites
        random.shuffle(names)

        agent_type = "Runner"

        for i in range(int(self.population_size)):
            name = names.pop()
            name_number = original_names.index(name) + 1
            agent = AgentConstruct(agent_type, self.actr_environment, None, self.middleman, name, name_number)
            self.agent_list.append(agent)

        for agent in self.agent_list:
            agent.set_agent_dictionary(self.agent_list)
            agent_id_list = list(agent.get_agent_dictionary())
            actr_construct, actr_agent, actr_adapter = self.agent_type_returner.return_agent_type(
                agent.actr_agent_type_name,
                self.actr_environment, agent_id_list)
            agent.set_actr_agent(actr_agent)
            agent.set_actr_adapter(actr_adapter)
            agent.set_simulation()
            agent.set_actr_construct(actr_construct)

    def run_simulation(self):
        """
        Entry point to the simulation. Setup, which enters the loop of step execution.
        """
        self.agent_builder()
        level_matrix = levelbuilder.build_level(self.height, self.width, self.agent_list, self.food_amount,
                                                self.wall_density)
        self.game_environment = Game(self.root, level_matrix)
        self.middleman.set_game_environment(self.game_environment)

        self.execute_step()
        self.root.mainloop()  # Allows GUI to run even while waiting for events

    def execute_step(self):
        """
        Execute an ACT-R specific step and triggers Adapter rules if needed.
        """
        self.schedule_agents_cognition()
        current_agent = self.agent_list[0]

        try:
            current_agent.simulation.step()
            # Synch timer
            event = current_agent.simulation.current_event
            current_agent.actr_time = current_agent.actr_time + event.time
            self.latency_factor_agent_actions = round(event.time * 1000)

            if (self.print_agent_actions):
                print(f"{current_agent.name}, {current_agent.actr_time}, {event[1]}, {event[2]}")
            key = BastiACTR.key_pressed(current_agent)
            # The agent decided to press a key, which will be executed by the middleman.
            if key:
                self.middleman.motor_input(key, current_agent)

            # The agent might be in a specific mental state, which requires Python intervention to override ACT-R.
            current_agent.actr_extension()
            self.root.after(self.latency_factor_agent_actions, lambda: self.execute_step())

        # Error handling due to a crashed ACT-R agent, to rescue the simulation.
        except simpy.core.EmptySchedule:
            if (self.print_agent_actions):
                print(f"{current_agent.name}, {current_agent.actr_time}, Oh no! Your agent has no production to fire :( Reset to initial goal!")
            current_agent.handle_empty_schedule()
            self.root.after_idle(lambda: self.execute_step())

    def schedule_agents_cognition(self):
        """
        Schedules the agents priority based on their time step inside their cognition. Basically rearranges the list.
        """
        if self.agent_list:
            for agent in self.agent_list:
                agent.update_stimulus()
            self.agent_list.sort(key=lambda agent: agent.actr_time)

    def notify_gui(self):
        """
        Notifies the gui to refresh.
        """
        if hasattr(self, 'gui'):
            self.gui.update()
