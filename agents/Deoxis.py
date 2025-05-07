import pyactr as actr


class Deoxis:
    """
    A basic agent, which serves as a demonstrator.

    Attributes:
        this_agent_key (str): Self identification from AgentConstruct agent_dictionary
        other_agents_key_list (list): Identification from AgentConstruct agent_dictionary for other agents but self
        environ (Environment): pyactr environment
        actr_agent (ACTRModel): pyactr agent
        goal_phases (list): All goal states, which are independent of each other. Makes code more readable
        initial_goal (Chunk): If the agent crashes, it will start again with this goal
    """

    def __init__(self, environ):
        """
        Args:
            environ: pyactr environment (can be overwritten later)
        """
        self.this_agent_key = None
        self.other_agents_key_list = None

        self.environ = environ
        self.actr_agent = actr.ACTRModel(environment=self.environ, motor_prepared=True, automatic_visual_search=False,
                                         subsymbolic=True)
        self.goal_phases = ["test"]

        self.initial_goal = actr.chunkstring(string=f"""
            isa     {self.goal_phases[0]}
            state   {self.goal_phases[0]}Start
        """)

    # Building the agent
    def build_agent(self, agent_list):
        """
        Builds an ACT-R agent

        Args:
            agent_list (list): Strings from the AgentConstruct dictionary to identify other agents

        Returns:
            pyactr.ACTRAgent: The final actr_agent object from pyactr
        """
        self.this_agent_key = agent_list[0]
        self.other_agents_key_list = agent_list[1:]

        # ACT-R configuration for this agent
        actr_agent = self.actr_agent
        actr_agent.model_parameters[
            "utility_noise"] = 5  # 0.0 = only base utility
        actr_agent.model_parameters["baselevel_learning"] = False

        # Goal Chunk Types
        goal_phases = self.goal_phases
        for phase in goal_phases:
            actr.chunktype(phase, "state")

        # Agent Model
        self.add_productions(actr_agent, goal_phases[0])
        return actr_agent

    def add_productions(self, actr_agent, phase):
        actr_agent.productionstring(name=f"happy easteregg", string=f"""
                =g>
                isa     {phase}
                state   {phase}Start
                ==>
                =g>
                isa     {phase}
                state   {phase}Start""")