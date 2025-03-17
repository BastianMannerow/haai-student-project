import pyactr as actr


class Hunter:
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
        self.actr_agent = actr.ACTRModel(environment=self.environ, motor_prepared=True, automatic_visual_search=True,
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
        actr_agent.visualBuffer("visual", "visual_location", actr_agent.decmem, finst=30)
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
        return actr_agent

    def add_productions(self, actr_agent, phase, next_phase):
        actr_agent.productionstring(name="initiate_search", string=f"""
            =g>
                isa     {self.goal_phases[0]}
                state   {self.goal_phases[0]}Start
            =visual_location>
                isa _visuallocation
            ==>
            =g>
                isa     {self.goal_phases[0]}
                state   {self.goal_phases[0]}Look
            +visual>
                isa _visual
                cmd     move_attention
                screen_pos =visual_location
        """)

        actr_agent.productionstring(name="store_stimulus", string=f"""
            =g>
            isa     {self.goal_phases[0]}
            state   {self.goal_phases[0]}Look
            =visual>
                isa         _visual
                value       =stimulus
                screen_pos  =pos
            =imaginal>
                buffer      empty
            ==>
            =g>
            isa     detect
            state   detectStart
            +imaginal>
                isa         stored_stimulus
                value       =stimulus
                screen_pos  =pos
            """)

        actr_agent.productionstring(name="detect_target", string=f"""
        =g>
            isa     detect
            state   detectStart
        =visual>
            isa         _visual
            value       =stimulus
            screen_pos  = new_pos
        ?imaginal>
            isa         stored_stimulus
            value       =stimulus
            screen_pos  = stored_pos
        ==>
        =g>
            isa     {self.goal_phases[0]}
            state   {self.goal_phases[0]}Start
        =imaginal>
            isa         target
            value       =stimulus
            screen_pos  = new_pos
        +manual>
            isa         _manual
            cmd         press_key
            key         M
        """)


