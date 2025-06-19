import datetime

class BastiTracer:
    def __init__(self):
        # Hier speichern wir alle Log-Einträge
        # Jeder Eintrag ist ein Dict mit keys: timestamp, type, event, agent_name
        self.records = []
        # Damit wir neue Agents erkennen
        self.known_agents = set()

    def trace(self, agent, event):
        """
        Legt einen Log-Eintrag an:
        - timestamp: der aktuelle Simulationszeitpunkt (agent.actr_time)
        - type: der Agenten-Typ (agent.actr_agent_type_name)
        - event: die aktuelle Event-Beschreibung aus ACT-R
        - agent_name: agent.name (falls du mehrere Instanzen desselben Typs differenzieren willst)
        Außerdem wird, falls dieser Agent noch unbekannt ist, zuerst ein 'agent_added'-Eintrag erzeugt.
        """
        ts = agent.actr_time
        name = agent.name

        # Neuer Agent?
        if name not in self.known_agents:
            self.known_agents.add(name)
            self.records.append({
                "timestamp": ts,
                "type": "agent_added",
                "event": None,
                "agent_name": name
            })

        # Den eigentlichen Schritt loggen
        self.records.append({
            "timestamp": ts,
            "type": event[1],
            "event": event[2],
            "agent_name": name
        })

    def get_logs(self):
        """Gibt die gesammelten Log-Einträge zurück."""
        return self.records
