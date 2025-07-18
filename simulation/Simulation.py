import random
import simpy
import tkinter as tk
from gui.Stepper import StepLogWindow
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
        los (int): How far is the line of sight for the agent. 0 = Infinite
        stepper (bool): If True, run simulation by pressing SPACE step by step
        agent_type_config (dict): .py Class name of your agent, amount and if you want to display their logs

        global_sim_time (float): Used for synchronising the gui with the cognition time
        agent_list (list): All agents participating in the simulation
        root (Tkinter()): GUI of the simulation
        agent_type_returner (AgentTypeReturner): Returns the actr agent and its Adapter
        actr_environment (pyactr.Environment()): Environment in which the visual stimuli will appear
        middleman (Middleman): Translates changes between the environment and the agents
    """

    def __init__(self, interceptor):
        # Configuration
        self.level_type = "Agent Project"
        self.focus_position = (0, 2)
        self.print_middleman = False
        self.width = 16
        self.height = 16
        self.food_amount = 3
        self.wall_density = 0
        self.speed_factor = 50
        self.print_agent_actions = True
        self.los = 3
        self.stepper = True
        self.agent_type_config = {
            "Imposter": {"count": 1, "pokedex_id": 647, "print_agent_actions": False},
            "Chatot": {"count": 1, "pokedex_id": 441, "print_agent_actions": True},  # Tom
            #"Hoothoot": {"count": 1, "pokedex_id": 163, "print_agent_actions": True},  # Christoh
            #"Charmander": {"count": 1, "pokedex_id": 4, "print_agent_actions": True},  # Yannik
            #"Gengar": {"count": 1, "pokedex_id": 94, "print_agent_actions": True}  # Pascal
        }

        # Critical state
        self.global_sim_time = 0
        self.agent_list = []
        self.interceptor = interceptor

        # Agent & ACT-R environment setup (für agent_builder)
        self.agent_type_returner = AgentTypeReturner()
        self.actr_environment = actr.Environment(focus_position=self.focus_position)
        self.middleman = Middleman(self, self.print_middleman)

        # GUI setup
        self.root = tk.Tk()
        if self.stepper:
            self.root.bind("<space>", lambda e: self.step_once())
            self.log_window = StepLogWindow(
                master=self.root,
                tracer=self.interceptor,
                simulation=self
            )

        # Jump-State
        self.jumping = False
        self.jump_target = None

    def agent_builder(self):
        """Creates all agent objects with its components."""
        with open("gui/sprites/pokemon/pokemonNames.txt", 'r') as file:
            names = file.read().splitlines()
        original_names = names.copy()
        random.shuffle(names)

        for agent_type, config in self.agent_type_config.items():
            count = config["count"]
            print_actions = config.get("print_agent_actions", self.print_agent_actions)
            pokedex_id = config.get("pokedex_id")

            for _ in range(count):
                if pokedex_id is not None:
                    name_number = pokedex_id
                    name = original_names[name_number - 1]
                else:
                    name = names.pop()
                    name_number = original_names.index(name) + 1

                agent = AgentConstruct(
                    agent_type,
                    self.actr_environment,
                    None,
                    self.middleman,
                    name,
                    name_number,
                    self.los
                )
                agent.actr_time = 0
                agent.print_agent_actions = print_actions
                self.agent_list.append(agent)

        for agent in self.agent_list:
            agent.set_agent_dictionary(self.agent_list)
            ids = list(agent.get_agent_dictionary())
            actr_construct, actr_agent, actr_adapter = (
                AgentTypeReturner()
                .return_agent_type(
                    agent.actr_agent_type_name,
                    self.actr_environment,
                    ids
                )
            )
            agent.set_actr_agent(actr_agent)
            agent.set_actr_adapter(actr_adapter)
            agent.set_simulation()
            agent.set_actr_construct(actr_construct)

    def run_simulation(self):
        self.agent_builder()
        level_matrix = levelbuilder.build_level(
            self.height,
            self.width,
            self.agent_list,
            self.food_amount,
            self.wall_density,
            self.level_type
        )
        self.game_environment = Game(self.root, level_matrix)
        self.middleman.set_game_environment(self.game_environment)
        if not self.stepper:
            self.execute_step()

        self.root.mainloop()

    def execute_step(self):
        """Schedules agents based on cognition time (non-stepper mode)."""
        if self.stepper:
            return

        for agent in self.agent_list:
            agent.update_stimulus()

        LübeckACTR.fix_pyactr()
        self.agent_list.sort(key=lambda a: a.actr_time)
        next_agent = self.agent_list[0]
        delay = next_agent.actr_time - self.global_sim_time
        factor = 100 / self.speed_factor
        ms = max(1, round(delay * factor * 1000))
        self.root.after(ms, lambda: self.execute_agent_step(next_agent))

    def execute_agent_step(self, agent):
        """Executes a cognitive step and handles errors."""
        try:
            agent.simulation.step()
            event = agent.simulation.current_event

            if event.time > 0 or self.level_type is not None:
                agent.no_increase_count = 0
            else:
                agent.no_increase_count = getattr(agent, "no_increase_count", 0) + 1

            if agent.no_increase_count >= 10:
                print(f"{agent.name} removed due to inactivity.")
                self.agent_list.remove(agent)
                self.game_environment.remove_agent_from_game(agent)
            else:
                agent.actr_time += event.time
                self.global_sim_time = agent.actr_time
                agent.actr_extension()
                if agent.print_agent_actions:
                    print(f"{agent.name}, {agent.actr_time}, {event}")
                key = LübeckACTR.key_pressed(agent)
                if key:
                    self.middleman.motor_input(key, agent)

            self.execute_step()

        except (simpy.core.EmptySchedule, AttributeError, IndexError, RuntimeError) as e:
            print(f"Error in {agent.name}: {e}")
            agent.handle_empty_schedule()
            self.root.after_idle(lambda: self.execute_step())

    def step_once(self):
        """Performs exactly one cognitive step (stepper mode)."""
        for agent in self.agent_list:
            agent.update_stimulus()

        LübeckACTR.fix_pyactr()
        self.agent_list.sort(key=lambda a: a.actr_time)
        na = self.agent_list[0]
        try:
            na.simulation.step()
            event = na.simulation.current_event
            if event.time > 0:
                na.no_increase_count = 0
            else:
                na.no_increase_count = getattr(na, "no_increase_count", 0) + 1

            if na.no_increase_count >= 10:
                print(f"{na.name} removed due to inactivity.")
                self.agent_list.remove(na)
                self.game_environment.remove_agent_from_game(na)
            else:
                na.actr_time += event.time
                self.global_sim_time = na.actr_time
                na.actr_extension()
                if na.print_agent_actions:
                    print(f"{na.name}, {na.actr_time}, {event}")
                key = LübeckACTR.key_pressed(na)
                if key:
                    self.middleman.motor_input(key, na)
                self.interceptor.trace(na, event)
                self.log_window.log()

        except (simpy.core.EmptySchedule, AttributeError, IndexError, RuntimeError) as e:
            print(f"Error in step_once for {na.name}: {e}")
            na.handle_empty_schedule()
        finally:
            self.notify_gui()

    def start_jump(self, production_name: str):
        """Starts jumping until the specified production fires (only in stepper mode)."""
        if not self.stepper:
            # Jump only available when stepper is active
            return
        self.jumping = True
        self.jump_target = f"RULE FIRED: {production_name}"
        self._jump_step()

    def _jump_step(self):
        if not getattr(self, 'jumping', False):
            return
        before = len(self.interceptor.records)
        self.step_once()
        for r in self.interceptor.records[before:]:
            if r.get('type') == 'PROCEDURAL' and str(r.get('event')) == self.jump_target:
                self.jumping = False
                print(f"✅ Jump completed to {self.jump_target}")
                return
        self.root.after(1, self._jump_step)

    def notify_gui(self):
        """Refreshes GUI elements."""
        if hasattr(self, 'log_window'):
            self.log_window.window.update_idletasks()
            self.log_window.window.update()
