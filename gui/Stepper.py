import tkinter as tk
import random
from tkinter import font

class StepLogWindow:
    """Öffnet ein eigenes Fenster mit einem scrollbaren Canvas-Grid zum Anzeigen der Step-Logs
       und bietet ein Eingabefeld zum JUMPen zu einer bestimmten Produktion."""

    def __init__(self, master=None, tracer=None, simulation=None, title="Stepper Log"):
        self.tracer = tracer
        self.simulation = simulation
        self.window = tk.Toplevel(master) if master else tk.Tk()
        self.window.title(title)
        self.window.configure(bg="#2e1111")

        # Rahmen-Layout mit Grid: 2 Spalten, Input oben, Listbox links, Canvas rechts
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=0)  # Listbox-Spalte bleibt passend
        self.window.grid_columnconfigure(1, weight=1)  # Canvas-Spalte füllt Rest

        # Eingabe für JUMP
        self.input_frame = tk.Frame(self.window, bg="#2e1111")
        self.input_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5,10))
        self.input_frame.grid_columnconfigure(1, weight=1)

        tk.Label(self.input_frame, text="Produktion:", bg="#2e1111", fg="white")\
          .grid(row=0, column=0, padx=5)
        self.jump_entry = tk.Entry(self.input_frame)
        self.jump_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.jump_button = tk.Button(self.input_frame, text="JUMP", command=self.on_jump)
        self.jump_button.grid(row=0, column=2, padx=5)

        # Liste der Agents links
        self.listbox = tk.Listbox(self.window, width=20, bg="#2e1111", fg="white")
        self.listbox.grid(row=1, column=0, sticky="ns", padx=(5,0), pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_agent_select)

        # Frame für Canvas+Scrollbars
        self.plot_frame = tk.Frame(self.window, bg="#2e1111")
        self.plot_frame.grid(row=1, column=1, sticky="nsew", padx=(0,5), pady=5)
        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(0, weight=1)

        # Canvas für das Grid
        self.canvas = tk.Canvas(self.plot_frame, background="#2e1111")
        self.vsb = tk.Scrollbar(self.plot_frame, orient="vertical", command=self.canvas.yview)
        self.hsb = tk.Scrollbar(self.plot_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        # Font für Canvas-Text dynamisch anpassen
        default_font = font.nametofont("TkDefaultFont")
        default_size = default_font.cget("size")
        self.font = default_font

        # Farbzuordnung für Event-Typen
        self.color_map = {}

        # Dynamisches Nachzeichnen bei Resize
        self.canvas.bind('<Configure>', lambda e: self.redraw_current())

        # Initial befüllen
        self.current_agent = None
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
        self.current_agent = self.listbox.get(sel[0])
        self.redraw_current()

    def redraw_current(self):
        """Zeichnet den aktuellen Agent neu, z.B. bei Resize oder Auswahl."""
        if not self.current_agent:
            return
        self.show_agent_logs(self.current_agent)

    def show_agent_logs(self, agent_name: str):
        """Zeigt den kompletten Verlauf für den ausgewählten Agent im Canvas-Grid an."""
        self.canvas.delete("all")
        recs = [r for r in self.tracer.records if r["agent_name"] == agent_name]
        if not recs:
            return
        types = sorted({r["type"] for r in recs})
        times = sorted({r["timestamp"] for r in recs})
        # Dynamische Zellgrößen basierend auf Canvas-Größe
        w = max(self.canvas.winfo_width() - 120, 200)
        h = max(self.canvas.winfo_height() - 60, 200)
        cell_w = w / max(len(times), 1)
        cell_h = h / max(len(types), 1)
        margin_x, margin_y = 100, 30

        row_index = {t: i for i, t in enumerate(types)}
        col_index = {ts: j for j, ts in enumerate(times)}

        # Typ-Achse
        for t, i in row_index.items():
            y = margin_y + i * cell_h + cell_h / 2
            self.canvas.create_text(5, y, anchor="w", text=str(t), fill="white", font=self.font)

        # Zeit-Achse
        header_y = margin_y / 2
        for ts, j in col_index.items():
            x = margin_x + j * cell_w + cell_w / 2
            self.canvas.create_text(x, header_y, anchor="s", text=f"{ts:.2f}", fill="white", font=self.font)

        # Blöcke zeichnen
        for r in recs:
            i = row_index[r["type"]]
            j = col_index[r["timestamp"]]
            x1 = margin_x + j * cell_w
            y1 = margin_y + i * cell_h
            x2, y2 = x1 + cell_w, y1 + cell_h
            typ = r["type"]
            if typ not in self.color_map:
                self.color_map[typ] = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            color = self.color_map[typ]
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="white")
            evt = r.get("event")
            if evt is not None:
                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2,
                                        text=str(evt), fill="black", width=cell_w - 4, font=self.font)

        total_w = margin_x + len(times) * cell_w + 20
        total_h = margin_y + len(types) * cell_h + 20
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))

    def log(self, message: str = None):
        """Nach jedem Step: Liste und Log-Ansicht aktualisieren."""
        self.refresh_agent_list()
        if self.listbox.size() > 0:
            sel = self.listbox.curselection() or (0,)
            self.listbox.selection_set(sel)
            self.current_agent = self.listbox.get(sel[0])
            self.redraw_current()

    def on_jump(self):
        """Callback für den JUMP-Button."""
        prod_name = self.jump_entry.get().strip()
        if prod_name and self.simulation:
            self.simulation.start_jump(prod_name)
