import pyactr as actr
from simulation.LübeckACTR import *


class Gengar:
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
        actr.chunktype("test", "state")
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
            "utility_noise"] = 20  # 0.0 = only base utility
        actr_agent.model_parameters["baselevel_learning"] = True

        # Goal Chunk Types
        goal_phases = self.goal_phases
        for phase in goal_phases:
            actr.chunktype(phase, "state")


        set_goal(actr_agent, self.initial_goal)


        actr.chunktype("moveplan", "goalname goalx goaly direction status")
        actr.chunktype("repairplan", "plan goalx goaly status direction")
        actr.chunktype("suspicion", "agent sus reason")
        actr.chunktype("press_key", "key")

        self.define_landmark_chunks(actr_agent)

        # Agent Model
        self.add_productions(actr_agent, goal_phases[0])
        return actr_agent

    def add_productions(self, actr_agent, phase):
        actr_agent.productionstring(name="load_environment", string=f"""
                            =g>
                                isa   {phase}
                                state {phase}Start
                        ==>
                            =g>
                                isa   {phase}
                                state {phase}Start
                        """)
        actr_agent.productionstring(name="move_generic", string="""
                    =g>
                        isa         moveplan
                        direction   =dir
                    ?manual>
                        state       free
                    ==>
                    +manual>
                        isa     _manual
                        cmd     'press_key'
                        key     =dir
                """)
        actr_agent.productionstring(name="start_repair", string="""
            =g>
                isa         repairplan
                plan        repair
                direction   =dir
                status      pending
            ?manual>
                state       free
        ==>
            +manual>
                isa     _manual
                cmd     'press_key'
                key     =dir
            =g>
                isa     repairplan
                status  in_progress
        """)

    #[(1, 2), (2, 15), (7, 8), (8, 1), (17, 2), (18, 16)]

    def define_landmark_chunks(self, actr_agent):
        actr.chunktype("landmark", "name x y")
        actr_agent.decmem.add(actr.chunkstring(string="""
                        isa     landmark
                        name    Uni
                        y       18
                        x       16
                    """))
        actr_agent.decmem.add(actr.chunkstring(string="""
                                isa     landmark
                                name    Uni
                                y       1
                                x       2
                            """))
        actr_agent.decmem.add(actr.chunkstring(string="""
                                isa     landmark
                                name    Uni
                                y       2
                                x       15
                            """))
        actr_agent.decmem.add(actr.chunkstring(string="""
                                isa     landmark
                                name    Uni
                                y       7
                                x       8
                            """))
        actr_agent.decmem.add(actr.chunkstring(string="""
                                isa     landmark
                                name    Uni
                                y       8
                                x       1
                            """))
        actr_agent.decmem.add(actr.chunkstring(string="""
                                isa     landmark
                                name    Uni
                                y       17
                                x       2
                            """))
