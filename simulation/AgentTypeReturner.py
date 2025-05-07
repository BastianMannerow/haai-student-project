from agents.Beedrill import Beedrill
from agents.BeedrillAdapter import BeedrillAdapter
from agents.Charmander import Charmander
from agents.CharmanderAdapter import CharmanderAdapter
from agents.Dakrai import Dakrai
from agents.DakraiAdapter import DakraiAdapter
from agents.Deoxis import Deoxis
from agents.DeoxisAdapter import DeoxisAdapter
from agents.Mew import Mew
from agents.MewAdapter import MewAdapter
from agents.Pinsir import Pinsir
from agents.PinsirAdapter import PinsirAdapter
from agents.Victreebel import Victreebel
from agents.VictreebelAdapter import VictreebelAdapter


# Only to avoid overloading the simulation. Returns the Agent object needed.
class AgentTypeReturner:
    def __init__(self):
        pass

    # Create an agent object based on the type
    def return_agent_type(self, name, actr_environment, agent_id_list):
        if name == "Human":
            return None

        elif name == "Mew":
            runner = Mew(actr_environment)
            return runner, runner.build_agent(agent_id_list), MewAdapter(actr_environment)

        elif name == "Beedrill":
            runner = Beedrill(actr_environment)
            return runner, runner.build_agent(agent_id_list), BeedrillAdapter(actr_environment)

        elif name == "Charmander":
            runner = Charmander(actr_environment)
            return runner, runner.build_agent(agent_id_list), CharmanderAdapter(actr_environment)

        elif name == "Dakrai":
            runner = Dakrai(actr_environment)
            return runner, runner.build_agent(agent_id_list), DakraiAdapter(actr_environment)

        elif name == "Deoxis":
            runner = Deoxis(actr_environment)
            return runner, runner.build_agent(agent_id_list), DeoxisAdapter(actr_environment)

        elif name == "Pinsir":
            runner = Pinsir(actr_environment)
            return runner, runner.build_agent(agent_id_list), PinsirAdapter(actr_environment)

        elif name == "Victreebel":
            runner = Victreebel(actr_environment)
            return runner, runner.build_agent(agent_id_list), VictreebelAdapter(actr_environment)


        else:
            raise ValueError(f"Unknown Agent .py Type: {name}")