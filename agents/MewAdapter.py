from simulation import LübeckACTR
import pyactr as actr

class MewAdapter:
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

    # Extending ACT-R
    def extending_actr(self):
        """
        Functionality, which extends ACT-R
        In pyactr, ACT-R functionality and regular arithmetic or logical functions are strictly divided.
        The reason for that is a clearer understanding of the agents' behaviour.
        This method will supervise the internal state of the agent.
        """
        #actr_agent = self.agent_construct.actr_agent
        #LübeckACTR.set_imaginal(actr_agent, actr.chunkstring(
        #            string=f"isa test state testtest"), 2)
        #LübeckACTR.get_imaginal(actr_agent, actr.chunkstring(self.agent_construct.actr_agent, 2))