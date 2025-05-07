import random

from simulation import LübeckACTR

class BeedrillAdapter:
    """
    A basic agent, which serves as a demonstrator.

    Attributes:
        agent_construct (str): Nothing
    """

    def __init__(self, agent_construct):
        """
        Args:
            agent_construct: nothing at the moment
        """
        self.agent_construct = agent_construct
        self.move_time = random.uniform(3.0, 10.0)

    # Extending ACT-R
    def extending_actr(self, agent_construct):
        """
        Functionality, which extends ACT-R
        In pyactr, ACT-R functionality and regular arithmetic or logical functions are strictly divided.
        The reason for that is a clearer understanding of the agents' behaviour.
        This method will supervise the internal state of the agent.

        Args:
            agent_construct (AgentConstruct): Parent of the SocialAgent
        """

        agent_list = agent_construct.middleman.simulation.agent_list
        other_agent = [agent for agent in agent_list if agent is not agent_construct][0]

        r, c = agent_construct.middleman.experiment_environment.find_agent(other_agent)
        rr, cc = agent_construct.middleman.experiment_environment.find_agent(agent_construct)

        if (r, c) == (rr, cc):
            raise ValueError("AWWWWWWWWWWWWW IT HURTS")

        if c > cc:
            print("SUCCESS!")

        agent_construct.actr_time = agent_construct.actr_time + other_agent.actr_time
        if other_agent.actr_time > self.move_time:
            agent_construct.middleman.motor_input("W", agent_construct)