import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os
import random
from simulation.Food import Food
from simulation.Wall import Wall
from simulation.AgentConstruct import AgentConstruct

class MatrixWorldGUI:
    def __init__(self, world, root):
        self.world = world
        self.root = root
        self.root.title("Social Simulation")
        self.root.configure(bg='black')
        self.root.state('zoomed')  # Maximiert das Fenster

        # Initialer Zoomfaktor
        self.zoom_factor = 1.0

        # Bildschirmabmessungen und Info-Panel definieren
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        info_frame_width = screen_width // 5

        # Erstellen eines Containers für Canvas und Steuerungsbuttons (linker Bereich)
        self.canvas_frame = tk.Frame(self.root, bg="black")
        self.canvas_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Haupt-Canvas für das Spielfeld
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Steuerungs-Frame unten im linken Bereich
        self.control_frame = tk.Frame(self.canvas_frame, bg="#333333")
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Hinzufügen der Steuerungsbuttons
        btn_pan_left = tk.Button(self.control_frame, text="←", command=lambda: self.canvas.xview_scroll(-3, "units"))
        btn_pan_left.pack(side=tk.LEFT, padx=5, pady=5)

        btn_pan_right = tk.Button(self.control_frame, text="→", command=lambda: self.canvas.xview_scroll(3, "units"))
        btn_pan_right.pack(side=tk.LEFT, padx=5, pady=5)

        btn_pan_up = tk.Button(self.control_frame, text="↑", command=lambda: self.canvas.yview_scroll(-3, "units"))
        btn_pan_up.pack(side=tk.LEFT, padx=5, pady=5)

        btn_pan_down = tk.Button(self.control_frame, text="↓", command=lambda: self.canvas.yview_scroll(3, "units"))
        btn_pan_down.pack(side=tk.LEFT, padx=5, pady=5)

        btn_zoom_in = tk.Button(self.control_frame, text="Zoom In", command=self.zoom_in)
        btn_zoom_in.pack(side=tk.LEFT, padx=5, pady=5)

        btn_zoom_out = tk.Button(self.control_frame, text="Zoom Out", command=self.zoom_out)
        btn_zoom_out.pack(side=tk.LEFT, padx=5, pady=5)

        # Info-Panel (rechter Bereich)
        self.info_frame = tk.Frame(self.root, width=info_frame_width, bg='#171717')
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_frame.pack_propagate(False)  # Verhindert automatisches Anpassen der Größe

        # Unterframe für Agentenbild und Namen
        self.agent_info_frame = tk.Frame(self.info_frame, bg='#171717')
        self.agent_info_frame.pack(padx=10, pady=20)

        self.agent_image_label = tk.Label(self.agent_info_frame, bg='#171717')
        self.agent_image_label.pack()

        self.agent_name_label = tk.Label(
            self.agent_info_frame, fg="white", bg='#171717',
            font=("Helvetica", 16, "bold")
        )
        self.agent_name_label.pack(pady=10)

        # Titel und Container für visuelle Stimuli
        self.visual_stimuli_title = tk.Label(
            self.info_frame, text="Visual Stimuli", fg="white", bg='#171717',
            font=("Helvetica", 14)
        )
        self.visual_stimuli_frame = tk.Frame(self.info_frame, bg='#171717')

        # Dynamische Berechnung der Zellgröße anhand der verfügbaren Fläche
        canvas_width = screen_width - info_frame_width
        grid_cols = len(self.world.level_matrix[0])
        grid_rows = len(self.world.level_matrix)
        self.cell_size = min(canvas_width / grid_cols, screen_height / grid_rows) * self.zoom_factor
        self.image_height = int(self.cell_size * 2.5)

        # Caches für Bilder und Animationen
        self.agent_images = {}  # Für aktuelle Frame-Indizes
        self.agent_gifs = {}    # Für animierte GIF-Frames
        self.food_images = {}   # Für Food-Bilder

        # Laden der Umgebungsbilder (z. B. Gras, Baum) in passender Größe
        self.environment_images = {
            "grass": self.load_environment_image("gui/sprites/environment/grass.png"),
            "tree": self.load_environment_image("gui/sprites/environment/tree.png")
        }

        # Wähle initial einen zufälligen Agenten aus dem Spielfeld
        self.selected_agent = random.choice(
            [agent for row in self.world.level_matrix for cell in row for agent in cell if isinstance(agent, AgentConstruct)]
        )
        self.update_info_panel(self.selected_agent)

        # Scrollbars (unsichtbar, width=0)
        self.h_scroll = tk.Scrollbar(self.canvas, orient=tk.HORIZONTAL, command=self.canvas.xview, width=0)
        self.v_scroll = tk.Scrollbar(self.canvas, orient=tk.VERTICAL, command=self.canvas.yview, width=0)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        # Tastenbindungen für das Verschieben (Pan) des Canvas
        self.root.bind("<Left>", lambda event: self.canvas.xview_scroll(-3, "units"))
        self.root.bind("<Right>", lambda event: self.canvas.xview_scroll(3, "units"))
        self.root.bind("<Up>", lambda event: self.canvas.yview_scroll(-3, "units"))
        self.root.bind("<Down>", lambda event: self.canvas.yview_scroll(3, "units"))

        # Tastatureingaben für Zoom
        self.root.bind("<plus>", lambda event: self.zoom_in())
        self.root.bind("<KP_Add>", lambda event: self.zoom_in())
        self.root.bind("<minus>", lambda event: self.zoom_out())
        self.root.bind("<KP_Subtract>", lambda event: self.zoom_out())

        # Mausklicks zum Auswählen von Objekten (Agent, Food, Wall)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Bei Fenstergrößenänderung: Neuberechnung der Zellgröße
        self.root.bind("<Configure>", self.on_resize)

        # Periodische Aktualisierung der visuellen Stimuli (alle 1000 ms)
        self.schedule_visual_stimuli_update()

    def on_resize(self, event):
        # Neue Fensterabmessungen abrufen
        new_width = self.root.winfo_width()
        new_height = self.root.winfo_height()
        info_frame_width = new_width // 5
        canvas_width = new_width - info_frame_width

        grid_cols = len(self.world.level_matrix[0])
        grid_rows = len(self.world.level_matrix)
        new_cell_size = min(canvas_width / grid_cols, new_height / grid_rows) * self.zoom_factor

        if abs(new_cell_size - self.cell_size) > 1:
            self.cell_size = new_cell_size
            self.image_height = int(self.cell_size * 2.5)
            # Umgebungsbilder neu laden
            self.environment_images = {
                "grass": self.load_environment_image("gui/sprites/environment/grass.png"),
                "tree": self.load_environment_image("gui/sprites/environment/tree.png")
            }
            # Caches leeren, damit Food- und Agentenbilder neu skaliert werden
            self.food_images.clear()
            self.agent_gifs.clear()
            self.agent_images.clear()
            self.draw_grid()

    def zoom_in(self):
        self.zoom_factor *= 1.1
        self.update_zoom()

    def zoom_out(self):
        self.zoom_factor *= 0.9
        self.update_zoom()

    def update_zoom(self):
        new_width = self.root.winfo_width()
        new_height = self.root.winfo_height()
        info_frame_width = new_width // 5
        canvas_width = new_width - info_frame_width

        grid_cols = len(self.world.level_matrix[0])
        grid_rows = len(self.world.level_matrix)
        new_cell_size = min(canvas_width / grid_cols, new_height / grid_rows) * self.zoom_factor
        self.cell_size = new_cell_size
        self.image_height = int(self.cell_size * 2.5)
        self.environment_images = {
            "grass": self.load_environment_image("gui/sprites/environment/grass.png"),
            "tree": self.load_environment_image("gui/sprites/environment/tree.png")
        }
        self.food_images.clear()
        self.agent_gifs.clear()
        self.agent_images.clear()
        self.draw_grid()

    def load_environment_image(self, path):
        """
        Lädt ein Umgebungsbild und skaliert es exakt auf die Zellengröße,
        sodass keine schwarzen Lücken entstehen.
        """
        image = Image.open(path)
        # Skalierung ohne Beibehaltung des Seitenverhältnisses,
        # sodass das Bild die gesamte Zelle ausfüllt
        image = image.resize((int(self.cell_size), int(self.cell_size)), Image.LANCZOS)
        return ImageTk.PhotoImage(image)

    def get_random_food_image(self):
        """
        Wählt ein zufälliges Food-Bild aus dem Verzeichnis, skaliert es so, dass es maximal in die Zelle passt,
        und gibt das PhotoImage sowie den Pfad zurück.
        """
        food_dir = "gui/sprites/food"
        food_files = [f for f in os.listdir(food_dir) if f.endswith('.png')]
        random_food_file = random.choice(food_files)
        image_path = os.path.join(food_dir, random_food_file)
        image = Image.open(image_path)
        image.thumbnail((self.cell_size, self.cell_size), Image.LANCZOS)
        return ImageTk.PhotoImage(image), image_path

    def draw_grid(self):
        """
        Zeichnet das Spielfeld im Canvas. Dabei wird das Raster zentriert, falls es kleiner als der Canvas ist.
        Es werden Umgebung, Wände, Food und animierte Agenten gezeichnet.
        """
        self.canvas.delete("all")
        # Aktuelle Canvas-Größe ermitteln
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        grid_cols = len(self.world.level_matrix[0])
        grid_rows = len(self.world.level_matrix)
        grid_width = grid_cols * self.cell_size
        grid_height = grid_rows * self.cell_size

        # Berechne Offsets, um das Raster zu zentrieren (falls es kleiner als der Canvas ist)
        self.offset_x = max((canvas_width - grid_width) / 2, 0)
        self.offset_y = max((canvas_height - grid_height) / 2, 0)

        for r, row in enumerate(self.world.level_matrix):
            for c, cell in enumerate(row):
                x1 = self.offset_x + c * self.cell_size
                y1 = self.offset_y + r * self.cell_size
                # Basisumgebung (Gras) zeichnen
                self.canvas.create_image(x1, y1, anchor=tk.NW, image=self.environment_images["grass"])
                # Zeichne Baum, falls eine Wand vorhanden ist, oder Food, falls vorhanden
                if any(isinstance(obj, Wall) for obj in cell):
                    self.canvas.create_image(x1, y1, anchor=tk.NW, image=self.environment_images["tree"])
                elif any(isinstance(obj, Food) for obj in cell):
                    food_obj = next(obj for obj in cell if isinstance(obj, Food))
                    self.draw_food(food_obj, x1, y1)
                # Zeichne animierte Agenten
                for obj in cell:
                    if isinstance(obj, AgentConstruct):
                        self.draw_agent(obj, x1, y1)

        # Rotes Overlay um den ausgewählten Agenten bzw. das ausgewählte Feld zeichnen
        self.draw_red_overlay()
        # Aktualisiert die Scrollregion des Canvas
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def draw_red_overlay(self):
        """
        Zeichnet ein halbtransparentes rotes Overlay.
        Für Agenten wird ein größerer Bereich (mehrere Zellen) markiert,
        während bei Food oder Wall nur die jeweilige Zelle hervorgehoben wird.
        """
        if not self.selected_agent:
            return

        agent_x, agent_y = self.find_agent_position(self.selected_agent)
        if agent_x is None or agent_y is None:
            return

        overlay_color = "#2e1111"
        # Unterscheide, ob Food/Wall oder Agent ausgewählt wurde
        if isinstance(self.selected_agent, (Food, Wall)):
            x1 = self.offset_x + agent_x * self.cell_size
            y1 = self.offset_y + agent_y * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            for i in range(10):  # Simuliere Transparenz
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=overlay_color, outline="", stipple="gray50")
        else:
            grid_cols = len(self.world.level_matrix[0])
            grid_rows = len(self.world.level_matrix)
            overlay_range = min(2, grid_cols // 2, grid_rows // 2)
            for dx in range(-overlay_range, overlay_range + 1):
                for dy in range(-overlay_range, overlay_range + 1):
                    x = agent_x + dx
                    y = agent_y + dy
                    if 0 <= x < grid_cols and 0 <= y < grid_rows:
                        x1 = self.offset_x + x * self.cell_size
                        y1 = self.offset_y + y * self.cell_size
                        x2 = x1 + self.cell_size
                        y2 = y1 + self.cell_size
                        for i in range(10):
                            self.canvas.create_rectangle(x1, y1, x2, y2, fill=overlay_color, outline="", stipple="gray50")

    def find_agent_position(self, agent):
        """
        Findet und gibt die (Spalte, Zeile)-Position des übergebenen Objekts in der Level-Matrix zurück.
        """
        for r, row in enumerate(self.world.level_matrix):
            for c, cell in enumerate(row):
                if agent in cell:
                    return c, r
        return None, None

    def draw_food(self, food, x, y):
        """
        Zeichnet ein Food-Objekt mittig in der Zelle (auf der Grastextur).
        """
        if food not in self.food_images:
            self.food_images[food], food.image_path = self.get_random_food_image()
        center_x = x + self.cell_size / 2
        center_y = y + self.cell_size / 2
        self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=self.food_images[food])

    def draw_agent(self, agent, x, y):
        """
        Zeichnet einen animierten Agenten mittig in der Zelle.
        Die Agentengrafik nimmt 80% der Zellgröße (Gras) ein.
        """
        gif_path = f"gui/sprites/pokemon/gif/{agent.name_number}.gif"
        agent_size = int(self.cell_size * 0.8)  # 80% der Zellgröße
        if gif_path not in self.agent_gifs:
            image = Image.open(gif_path)
            frames = [ImageTk.PhotoImage(self.resize_image_keep_aspect(frame, agent_size, agent_size), master=self.root)
                      for frame in ImageSequence.Iterator(image)]
            self.agent_gifs[gif_path] = frames
            self.agent_images[gif_path] = 0
        frames = self.agent_gifs[gif_path]
        frame_index = self.agent_images[gif_path]
        center_x = x + self.cell_size / 2
        center_y = y + self.cell_size / 2
        self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=frames[frame_index])
        self.agent_images[gif_path] = (frame_index + 1) % len(frames)

    def resize_image_keep_aspect(self, image, max_width, max_height):
        """
        Skaliert ein Bild so, dass es in max_width und max_height passt, ohne das Seitenverhältnis zu verändern.
        """
        original_width, original_height = image.size
        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        return image.resize((new_width, new_height), Image.LANCZOS)

    def update_info_panel(self, obj):
        """
        Aktualisiert das Informationspanel (rechter Bereich) mit Details zum ausgewählten Objekt (Agent, Food oder Wall).
        Dabei werden alte Widgets entfernt und neue hinzugefügt.
        """
        for widget in self.visual_stimuli_frame.winfo_children():
            widget.destroy()
        for widget in self.info_frame.winfo_children():
            if widget not in {self.agent_info_frame, self.visual_stimuli_frame, self.visual_stimuli_title}:
                widget.destroy()

        if isinstance(obj, AgentConstruct):
            png_path = f"gui/sprites/pokemon/png/{obj.name_number}.png"
            image = Image.open(png_path)
            image.thumbnail((self.image_height, self.image_height), Image.LANCZOS)
            agent_image = ImageTk.PhotoImage(image)
            self.agent_image_label.config(image=agent_image)
            self.agent_image_label.image = agent_image
            self.agent_name_label.config(text=obj.name)
            self.visual_stimuli_title.pack(padx=10, pady=10)
            self.visual_stimuli_frame.pack(padx=10, pady=10)
            visual_stimuli = obj.visual_stimuli
            self.draw_matrix(visual_stimuli)

        elif isinstance(obj, Food):
            food_image = self.food_images[obj]
            self.agent_image_label.config(image=food_image)
            self.agent_image_label.image = food_image
            self.agent_name_label.config(text="Food")
            self.visual_stimuli_title.pack_forget()
            self.visual_stimuli_frame.pack_forget()
            self.saturation_label = tk.Label(
                self.info_frame, text=f"Saturation: {obj.get_saturation()}",
                fg="white", bg='#171717', font=("Helvetica", 12), anchor='center'
            )
            self.saturation_label.pack(anchor='center')
            self.amount_label = tk.Label(
                self.info_frame, text=f"Amount: {obj.get_amount()}",
                fg="white", bg='#171717', font=("Helvetica", 12), anchor='center'
            )
            self.amount_label.pack(anchor='center')
            self.regrowth_label = tk.Label(
                self.info_frame, text=f"Time till regrowth: {obj.get_time_till_regrowth()}",
                fg="white", bg='#171717', font=("Helvetica", 12), anchor='center'
            )
            self.regrowth_label.pack(anchor='center')

        elif isinstance(obj, Wall):
            png_path = "gui/sprites/environment/tree.png"
            image = Image.open(png_path)
            image.thumbnail((self.image_height, self.image_height), Image.LANCZOS)
            wall_image = ImageTk.PhotoImage(image)
            self.agent_image_label.config(image=wall_image)
            self.agent_image_label.image = wall_image
            self.agent_name_label.config(text="Wall")
            self.visual_stimuli_title.pack_forget()
            self.visual_stimuli_frame.pack_forget()
            self.description_label = tk.Label(
                self.info_frame, text="A wall, which prevents the agent's movement.",
                fg="white", bg='#171717', font=("Helvetica", 12), anchor='center'
            )
            self.description_label.pack(anchor='center')

    def on_canvas_click(self, event):
        """
        Behandelt Mausklicks im Canvas, um ein Objekt auszuwählen.
        Berücksichtigt den Offset, falls das Raster zentriert dargestellt wird.
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if hasattr(self, "offset_x") and hasattr(self, "offset_y"):
            x -= self.offset_x
            y -= self.offset_y
        r, c = int(y // self.cell_size), int(x // self.cell_size)
        if r < len(self.world.level_matrix) and c < len(self.world.level_matrix[0]):
            for obj in self.world.level_matrix[r][c]:
                if isinstance(obj, (AgentConstruct, Food, Wall)):
                    self.selected_agent = obj
                    self.update_info_panel(self.selected_agent)
                    break

    def update(self):
        """
        Aktualisiert das Spielfeld und sorgt dafür, dass Animationen (z. B. animierte GIFs) flüssig laufen.
        Diese Methode wird alle 50 ms erneut aufgerufen.
        """
        self.draw_grid()
        self.root.update_idletasks()
        self.root.update()
        self.root.after(50, self.update)

    def draw_matrix(self, matrix):
        """
        Zeichnet eine einfache Darstellung der übergebenen visuellen Stimuli-Matrix.
        Jede Zelle wird als Label dargestellt.
        """
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                cell_text = val if val else " "
                cell_label = tk.Label(
                    self.visual_stimuli_frame, text=cell_text, fg="white", bg='#171717',
                    relief='solid', borderwidth=1, width=4, height=2,
                    highlightbackground="white", highlightcolor="white", highlightthickness=1
                )
                cell_label.grid(row=i, column=j, padx=1, pady=1)

    def schedule_visual_stimuli_update(self):
        """
        Aktualisiert periodisch die visuellen Stimuli im Info-Panel.
        Gleichzeitig werden die Details von Food oder Wall aktualisiert, sofern ausgewählt.
        """
        self.update_info_panel(self.selected_agent)
        self.root.after(1000, self.schedule_visual_stimuli_update)
        if isinstance(self.selected_agent, Food):
            self.saturation_label.config(text=f"Saturation: {self.selected_agent.get_saturation()}")
            self.amount_label.config(text=f"Amount: {self.selected_agent.get_amount()}")
            self.regrowth_label.config(text=f"Time till regrowth: {self.selected_agent.get_time_till_regrowth()}")
        elif isinstance(self.selected_agent, Wall):
            self.description_label.config(text="A wall, which prevents the agent's movement.")
