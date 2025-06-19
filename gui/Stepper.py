import tkinter as tk
import random

class StepLogWindow:
    """Öffnet ein eigenes Fenster mit einem scrollbaren Canvas-Grid zum Anzeigen der Step-Logs."""

    def __init__(self, master=None, tracer=None, title="Stepper Log", width=60, height=20):
        self.tracer = tracer
        self.window = tk.Toplevel(master) if master else tk.Tk()
        self.window.title(title)
        self.window.configure(bg="#2e1111")
        self.window.geometry(f"{width * 8}x{height * 16}")

        # Liste der Agents links
        self.listbox = tk.Listbox(self.window, width=20, bg="#2e1111", fg="white")
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", self.on_agent_select)

        # Frame für Canvas+Scrollbars
        self.plot_frame = tk.Frame(self.window, bg="#2e1111")
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas für das Grid
        self.canvas = tk.Canvas(self.plot_frame, background="#2e1111")
        # Scrollbars
        self.vsb = tk.Scrollbar(self.plot_frame, orient="vertical", command=self.canvas.yview)
        self.hsb = tk.Scrollbar(self.plot_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # grid-Aufbau
        self.plot_frame.columnconfigure(0, weight=1)
        self.plot_frame.rowconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        # Farbzuordnung für Event-Typen
        self.color_map = {}

        # initial befüllen
        self.refresh_agent_list()

    def refresh_agent_list(self):
        """Füllt die Listbox mit allen bisher im Tracer bekannten Agenten."""
        self.listbox.delete(0, tk.END)
        if not self.tracer:
            return
        for name in sorted(self.tracer.known_agents):
            self.listbox.insert(tk.END, name)

    def on_agent_select(self, event):
        """Wird aufgerufen, wenn der User in der Listbox einen Agent anklickt."""
        sel = self.listbox.curselection()
        if not sel:
            return
        agent_name = self.listbox.get(sel[0])
        self.show_agent_logs(agent_name)

    def show_agent_logs(self, agent_name: str):
        """Zeigt den kompletten Verlauf für den ausgewählten Agent im Canvas-Grid an."""
        self.canvas.delete("all")

        recs = [r for r in self.tracer.records if r["agent_name"] == agent_name]
        types = sorted({r["type"] for r in recs})
        times = sorted({r["timestamp"] for r in recs})
        row_index = {t:i for i,t in enumerate(types)}
        col_index = {ts:i for i,ts in enumerate(times)}

        # Zellengröße & Abstände
        cell_w = 100
        cell_h = 50
        margin_x = 100
        margin_y = 30

        # Typ-Achse (links)
        for t,i in row_index.items():
            y = margin_y + i*cell_h + cell_h/2
            self.canvas.create_text(5, y, anchor="w", text=str(t), fill="white")

        # Zeit-Achse (oben), jetzt tiefer bei margin_y/2
        header_y = margin_y / 2
        for ts,j in col_index.items():
            x = margin_x + j*cell_w + cell_w/2
            self.canvas.create_text(x, header_y, anchor="s", text=f"{ts:.2f}", fill="white")

        # Blöcke zeichnen
        for r in recs:
            i = row_index[r["type"]]
            j = col_index[r["timestamp"]]
            x1 = margin_x + j*cell_w
            y1 = margin_y + i*cell_h
            x2 = x1 + cell_w
            y2 = y1 + cell_h

            typ = r["type"]
            if typ not in self.color_map:
                self.color_map[typ] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            color = self.color_map[typ]

            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="white")
            evt = r["event"]
            if evt is not None:
                self.canvas.create_text(
                    (x1+x2)/2, (y1+y2)/2,
                    text=str(evt),
                    fill="black",
                    width=cell_w-4
                )

        # Scroll-Region einstellen
        total_w = margin_x + len(times)*cell_w + 20
        total_h = margin_y + len(types)*cell_h + 20
        self.canvas.config(scrollregion=(0,0,total_w,total_h))

    def log(self, message: str = None):
        """
        Wird nach jedem step_once() aufgerufen.
        1. Listbox auffrischen (neue Agents)
        2. Falls noch keine Auswahl, ersten Agenten auswählen
        3. Verlauf des aktuell Gewählten anzeigen.
        """
        self.refresh_agent_list()
        if self.listbox.size() > 0:
            sel = self.listbox.curselection()
            if not sel:
                self.listbox.selection_set(0)
                sel = (0,)
            agent_name = self.listbox.get(sel[0])
            self.show_agent_logs(agent_name)
