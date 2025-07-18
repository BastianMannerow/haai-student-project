from agents.Beedrill import Beedrill
from agents.BeedrillAdapter import BeedrillAdapter
from agents.Dakrai import Dakrai
from agents.DakraiAdapter import DakraiAdapter
from agents.Deoxis import Deoxis
from agents.DeoxisAdapter import DeoxisAdapter
from agents.Imposter import Imposter
from agents.ImposterAdapter import ImposterAdapter
from agents.Mew import Mew
from agents.MewAdapter import MewAdapter
from agents.Pinsir import Pinsir
from agents.PinsirAdapter import PinsirAdapter
from agents.Victreebel import Victreebel
from agents.VictreebelAdapter import VictreebelAdapter
from agents.CharmanderProj import Charmander
from agents.CharmanderProjAdapter import CharmanderAdapter
from agents.Chatot import Chatot
from agents.ChatotAdapter import ChatotAdapter
from agents.Gengar import Gengar
from agents.GengarAdapter import GengarAdapter
from agents.Hoothoot import Hoothoot
from agents.HoothootAdapter import HoothootAdapter


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

        elif name == "Imposter":
            runner = Imposter(actr_environment)
            return runner, runner.build_agent(agent_id_list), ImposterAdapter(actr_environment)

        elif name == "Charmander":
            runner = Charmander(actr_environment)
            return runner, runner.build_agent(agent_id_list), CharmanderAdapter(actr_environment)

        elif name == "Chatot":
            runner = Chatot(actr_environment)
            return runner, runner.build_agent(agent_id_list), ChatotAdapter(actr_environment)
        elif name == "Gengar":
            runner = Gengar(actr_environment)
            return runner, runner.build_agent(agent_id_list), GengarAdapter(actr_environment, runner)

        elif name == "Hoothoot":
            runner = Hoothoot(actr_environment)
            return runner, runner.build_agent(agent_id_list), HoothootAdapter(actr_environment)

        else:
            raise ValueError(f"Unknown Agent .py Type: {name}")