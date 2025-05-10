

class AgentConstruct:
    def __init__(self, actr_agent_type_name, actr_environment, simulation, middleman, name, name_number, los):

        # ACT-R specific settings
        self.pun = False # can be removed later
        self.realtime = False
        self.actr_agent = None
        self.actr_adapter = None
        self.actr_agent_type_name = actr_agent_type_name
        self.actr_environment = actr_environment
        self.simulation = simulation
        self.actr_construct = None
        self.name = name
        self.actr_time = 0
        self.middleman = middleman
        self.name_number = name_number
        self.visual_stimuli = []
        self.los = los

        self.triggers = [{'S': {'text': 'S', 'position': (1, 1)}}]
        self.stimuli = ['S']

    def set_actr_agent(self, actr_agent):
        self.actr_agent = actr_agent

    def set_actr_adapter(self, actr_adapter):
        self.actr_adapter = actr_adapter

    # Important for the agent to distinguish between himself and other agents.
    # It also contains social status associations for each agent.
    def set_agent_dictionary(self, agent_list):
        # Ensure the agent is at the beginning and receives the letter A
        agent_list = [self] + [agent for agent in agent_list if agent != self]

        # Helper function to generate letter codes (e.g., A, B, ..., Z, AA, AB, ...)
        def generate_letter_code(index):
            letters = []
            while index >= 0:
                letters.append(chr(65 + (index % 26)))  # 65 = ASCII-Wert von 'A'
                index = index // 26 - 1
            return ''.join(reversed(letters))

        # Create the dictionary with letters as keys and values as a dictionary containing the agent and social_status
        self.agent_dictionary = {
            generate_letter_code(i): {"agent": agent, "social_status": 1.0}
            for i, agent in enumerate(agent_list)
        }

    def get_agent_dictionary(self):
        return self.agent_dictionary

    # Fills the visual buffer with new stimuli, based on the environments condition.
    def update_stimulus(self):
        if self.middleman.experiment_environment:
            new_triggers, new_stimuli = self.middleman.get_agent_stimulus(self)
            """
            self.simulation._Simulation__env.triggers = new_triggers
            self.simulation._Simulation__env.stimuli = new_text
            # self.simulation._Simulation__env.trigger = new_triggers #  Seems to make problems.
            self.simulation._Simulation__env.stimulus = new_text
            """
            self.triggers = new_triggers
            self.stimuli = new_stimuli

            self.middleman.simulation.notify_gui()

    def set_actr_construct(self, actr_construct):
        self.actr_construct = actr_construct

    def set_simulation(self):
        self.simulation = None if self.actr_agent is None else self.actr_agent.simulation(
            realtime=self.realtime,
            environment_process=self.actr_environment.environment_process,
            stimuli=self.stimuli,
            triggers=self.triggers,
            times=0.1,
            gui=False,
            trace=False)

    def actr_extension(self):
        self.actr_adapter.extending_actr(self)

    # If the agents knowledge changes during the simulation, a new ACT-R simulation needs to be created. This doesn't
    # affect the agent itself, but rather resets the clock, which measures mental processes.
    def reset_simulation(self, default_goal=None):
        if not default_goal:
            default_goal = self.actr_construct.initial_goal
        first_goal = next(iter(self.actr_agent.goals.values()))  # The second one is imaginal
        first_goal.add(default_goal)
        new_simulation = self.actr_agent.simulation(
            realtime=self.realtime,
            environment_process=self.actr_environment.environment_process,
            stimuli=self.stimuli,
            triggers=self.triggers,
            times=0.1,
            gui=False,
            trace=False
        )

        self.simulation = new_simulation

    # An empty schedule would crash the whole simulation. Reset the agent instead, so he can reevaluate.
    def handle_empty_schedule(self):
        self.reset_simulation()
