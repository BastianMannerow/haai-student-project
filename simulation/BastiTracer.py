import sys
from io import StringIO

class BastiTracer:
    def __init__(self):
        self.captured_output = []
        # Wir behalten uns sys.__stdout__ vor, falls wir wirklich zur Konsole zurückschreiben wollen.
        self._original_stdout = sys.__stdout__

    def write(self, message):
        # Jede print-Ausgabe landet hier als 'message'
        self.captured_output.append(message)

        # Falls du dennoch direkt in der Konsole sehen willst, kannst du auskommentieren:
        # self._original_stdout.write(message)

    def flush(self):
        # Muss existieren, damit print(..., flush=True) nicht abstürzt
        pass

    def get_and_clear(self):
        """
        Hilfsfunktion, um alle bisher gesammelten Nachrichten
        zurückzugeben und internes Array zu leeren.
        """
        out = "".join(self.captured_output)
        self.captured_output.clear()
        return out
