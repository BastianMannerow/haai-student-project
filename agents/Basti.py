import pyactr as actr


class Basti:
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
        self.goal_phases = ["test", "secondTest"]

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
            "utility_noise"] = 5  # 0.0 = only base utility, will be changed adaptevly
        actr_agent.model_parameters["baselevel_learning"] = True

        # Goal Chunk Types
        goal_phases = self.goal_phases
        for phase in goal_phases:
            actr.chunktype(phase, "state")

        actr.chunktype("impression", "positive")

        # Imaginal
        imaginal = actr_agent.set_goal(name="imaginal", delay=0)

        # Declarative Memory, initial mental models
        dd = {}
        for other_agent in self.other_agents_key_list:
            dd[actr.chunkstring(string=f"""
                isa mentalModelAgent{other_agent}
                reputation 5
                consistency True
                normConformity 0.5
            """)] = [0]

        actr_agent.set_decmem(dd)

        # Agent Model
        self.add_productions(actr_agent, goal_phases[0], goal_phases[1])
        self.add_visual_productions(actr_agent, goal_phases[0], goal_phases[1])
        return actr_agent

    def add_productions(self, actr_agent, phase, next_phase):
        actr_agent.productionstring(name=f"select_contribute", string=f"""
                =g>
                isa     {self.goal_phases[0]}
                state   {self.goal_phases[0]}Start
                ?manual>
                state   free
                ==>
                =g>
                isa     selectContribute
                state   retrieve
                +manual>
                isa     _manual
                cmd     'press_key'
                key     C""")

    def add_visual_productions(self, actr_agent, phase, next_phase):
        actr_agent.productionstring(name=f"move attention", string=f"""
                =g>
                isa     {self.goal_phases[0]}
                state   {self.goal_phases[0]}Start
                ?visual_location> 
                buffer full 
                =visual_location> 
                isa _visuallocation 
                ?visual> 
                buffer empty 
                state free
                ==>
                =g>
                isa     selectContribute
                state   retrieve
                ~visual_location> 
                +visual> 
                isa _visual 
                cmd move_attention 
                screen_pos =visual_location""")

        actr_agent.productionstring(name=f"encode first letter", string=f"""
                =g>
                isa     {self.goal_phases[0]}
                state   {self.goal_phases[0]}Start
                =visual> 
                isa _visual 
                value ~None
                ==>
                ~visual>
                =g>
                isa     selectContribute
                state   retrieve""")

        actr_agent.productionstring(name=f"find", string=f"""
                =g>
                isa     {self.goal_phases[0]}
                state   {self.goal_phases[0]}Start
                =visual> 
                isa _visual 
                value ~None
                ==>
                =g>
                isa     selectContribute
                state   retrieve
                ?visual_location>
                attended False 
                +visual_location> 
                isa _visuallocation 
                screen_x lowest 
                screen_y closest""")