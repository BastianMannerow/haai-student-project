import tkinter as tk
from tkinter import font, filedialog
import random
from PIL import Image, ImageDraw, ImageFont, ImageTk

class StepLogWindow:
    """Öffnet ein eigenes Fenster mit einem scrollbaren Canvas-Grid zum Anzeigen der Step-Logs
       und bietet ein Eingabefeld zum JUMP‑en zu einer bestimmten Produktion und Export als PNG."""

    def __init__(self, master=None, tracer=None, simulation=None, title="Stepper Log"):
        self.tracer     = tracer
        self.simulation = simulation

        # Hauptfenster oder Toplevel
        self.window = tk.Toplevel(master) if master else tk.Tk()
        self.window.title(title)
        self.window.configure(bg="#2e1111")

        # Layout: links Listbox, rechts Canvas-Bereich mit Label-Canvas + Data-Canvas
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=0)
        self.window.grid_columnconfigure(1, weight=1)

        # Eingabe-Frame (JUMP + Download)
        self.input_frame = tk.Frame(self.window, bg="#2e1111")
        self.input_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5,10))
        self.input_frame.grid_columnconfigure(1, weight=1)

        tk.Label(self.input_frame, text="Produktion:", bg="#2e1111", fg="white")\
          .grid(row=0, column=0, padx=5)
        self.jump_entry = tk.Entry(self.input_frame)
        self.jump_entry.grid(row=0, column=1, padx=5, sticky="ew")
        tk.Button(self.input_frame, text="JUMP", command=self.on_jump)\
          .grid(row=0, column=2, padx=5)
        tk.Button(self.input_frame, text="Download PNG", command=self.on_download)\
          .grid(row=0, column=3, padx=5)

        # Agenten-Liste links
        self.listbox = tk.Listbox(self.window, width=20, bg="#2e1111", fg="white")
        self.listbox.grid(row=1, column=0, sticky="ns", padx=(5,0), pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_agent_select)

        # Plot-Frame rechts: Label-Canvas + Data-Canvas + Scrollbars
        self.plot_frame = tk.Frame(self.window, bg="#2e1111")
        self.plot_frame.grid(row=1, column=1, sticky="nsew", padx=(0,5), pady=5)
        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(1, weight=1)

        # Canvas für feste Zeilenlabels
        self.label_canvas = tk.Canvas(self.plot_frame, background="#2e1111", highlightthickness=0)
        # Canvas für scrollbare Daten
        self.data_canvas  = tk.Canvas(self.plot_frame, background="#2e1111")
        # Scrollbars
        self.vsb = tk.Scrollbar(self.plot_frame, orient="vertical", command=self._on_vertical_scroll)
        self.hsb = tk.Scrollbar(self.plot_frame, orient="horizontal", command=self.data_canvas.xview)

        # Verknüpfen
        self.label_canvas.configure(yscrollcommand=self.vsb.set)
        self.data_canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # Platzieren
        self.label_canvas.grid(row=0, column=0, sticky="ns")
        self.data_canvas .grid(row=0, column=1, sticky="nsew")
        self.vsb         .grid(row=0, column=2, sticky="ns")
        self.hsb         .grid(row=1, column=1, sticky="ew")

        # Auflösung
        self.screen_w = self.window.winfo_screenwidth()
        self.screen_h = self.window.winfo_screenheight()

        # Zellmaße: Breite so, dass 7 Blöcke passen
        self.cell_w    = max(self.screen_w // 7, 40)
        # Höhe mindestens so groß wie 1 Zeile Text
        self.base_cell_h = max(self.screen_h // 20, 40)

        # Font fürs Messen und Zeichnen
        self.font = font.nametofont("TkDefaultFont")

        # Farb‑Map (Pastelltöne)
        self.color_map = {}

        # Für den PNG‑Export
        self.pil_image = None

        # Redraw bei Resize
        self.data_canvas.bind('<Configure>', lambda e: self.redraw_current())

        # Initial
        self.current_agent = None
        self.refresh_agent_list()

    def _on_vertical_scroll(self, *args):
        # Beide Canvas gemeinsam vertikal scrollen
        self.label_canvas.yview(*args)
        self.data_canvas .yview(*args)

    def refresh_agent_list(self):
        names = sorted(self.tracer.known_agents) if self.tracer else []
        prev  = self.current_agent
        self.listbox.delete(0, tk.END)
        for n in names:
            self.listbox.insert(tk.END, n)
        if prev in names:
            i = names.index(prev)
            self.listbox.selection_set(i)
            self.current_agent = prev
        elif names:
            self.listbox.selection_set(0)
            self.current_agent = names[0]
        else:
            self.current_agent = None

    def on_agent_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        self.current_agent = self.listbox.get(sel[0])
        self.redraw_current()

    def redraw_current(self):
        if not self.current_agent:
            return
        self.show_agent_logs(self.current_agent)

    def show_agent_logs(self, agent_name: str):
        # Filtere Records
        recs = [r for r in self.tracer.records if r["agent_name"] == agent_name]
        if not recs:
            return

        types = sorted({r["type"] for r in recs})
        times = sorted({r["timestamp"] for r in recs})
        margin_y = 30

        # Maße für Typ‑Labels
        max_type_w = max((self.font.measure(str(t)) for t in types), default=0)
        line_h     = self.font.metrics("linespace")

        # Bestimme Zeilenhöhe nach Zeilenumbrüchen im Event‑Text
        event_texts = [str(r["event"]) for r in recs if r.get("event") is not None]
        max_lines   = max((t.count('\n')+1 for t in event_texts), default=1)
        cell_h      = max(self.base_cell_h, max_lines*line_h + 4)

        cols       = len(times)
        rows       = len(types)
        total_h    = margin_y + rows*cell_h + 20
        total_w    = cols*self.cell_w + 20
        label_w    = max_type_w + 20

        # Leere Canvases & SCROLLREGION
        self.label_canvas.delete("all")
        self.data_canvas .delete("all")
        self.label_canvas.config(scrollregion=(0,0,label_w, total_h))
        self.data_canvas .config(scrollregion=(0,0,total_w, total_h))

        # Neues PIL‑Bild (für Export)
        img  = Image.new("RGB", (label_w+total_w, total_h), "#2e1111")
        draw = ImageDraw.Draw(img)
        pil_font = ImageFont.load_default()

        # 1) Zeilen‑Labels (persistent, weiß)
        for i, t in enumerate(types):
            y = margin_y + i*cell_h + cell_h//2
            # Tk‑Canvas
            self.label_canvas.create_text(label_w//2, y,
                                          text=str(t), fill="white",
                                          font=self.font)
            # PIL
            draw.text((5, y - line_h//2), str(t), fill="white", font=pil_font)

        # 2) Zeit‑Labels oben
        for j, ts in enumerate(times):
            x = j*self.cell_w + self.cell_w//2
            # Tk‑Canvas
            self.data_canvas.create_text(x, margin_y//2,
                                        text=f"{ts:.2f}", fill="white",
                                        font=self.font)
            # PIL
            draw.text((label_w + x - self.font.measure(f"{ts:.2f}")//2, 5),
                      f"{ts:.2f}", fill="white", font=pil_font)

        # 3) Blöcke & Events
        for r in recs:
            i = types.index(r["type"])
            j = times.index(r["timestamp"])
            x1 = j*self.cell_w
            y1 = margin_y + i*cell_h
            x2 = x1 + self.cell_w
            y2 = y1 + cell_h

            typ = r["type"]
            if typ not in self.color_map:
                # helle Pastelltöne
                r_col = random.randint(180,255)
                g_col = random.randint(180,255)
                b_col = random.randint(180,255)
                self.color_map[typ] = f'#{r_col:02x}{g_col:02x}{b_col:02x}'
            fill = self.color_map[typ]

            # Tk‑Canvas
            self.data_canvas.create_rectangle(x1, y1, x2, y2,
                                              fill=fill, outline="white")
            evt = r.get("event")
            if evt is not None:
                self.data_canvas.create_text(x1 + self.cell_w/2,
                                             y1 + cell_h/2,
                                             text=str(evt), fill="black",
                                             font=self.font,
                                             width=self.cell_w-4)

            # PIL
            draw.rectangle([label_w + x1, y1, label_w + x2, y2],
                           fill=fill, outline="white")
            if evt is not None:
                # zentriert mehrzeilig
                lines = evt.split('\n')
                for k, line in enumerate(lines):
                    wy = y1 + k*line_h + 2
                    # horizontale Zentrierung
                    lw = draw.textlength(line, font=pil_font)
                    wx = label_w + x1 + (self.cell_w - lw)/2
                    draw.text((wx, wy), line, fill="black", font=pil_font)

        # Merke für Download
        self.pil_image = img

    def on_download(self):
        if not self.pil_image:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG files", "*.png")])
        if path:
            self.pil_image.save(path)

    def log(self, message: str = None):
        self.refresh_agent_list()
        if self.current_agent:
            self.redraw_current()

    def on_jump(self):
        prod_name = self.jump_entry.get().strip()
        if prod_name and self.simulation:
            self.simulation.start_jump(prod_name)
