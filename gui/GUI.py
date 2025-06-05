import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os
import random
from simulation.Food import Food
from simulation.Wall import Wall
from simulation.Location import Location
from simulation.Water import Water
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

        # Canvas‐Container (linke Hälfte)
        self.canvas_frame = tk.Frame(self.root, bg="black")
        self.canvas_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Haupt‐Canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Steuerungs‐Frame mit Pan‐ und Zoom‐Buttons
        self.control_frame = tk.Frame(self.canvas_frame, bg="#333333")
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

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

        # Info‐Panel (rechte Hälfte)
        self.info_frame = tk.Frame(self.root, width=info_frame_width, bg='#171717')
        self.info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_frame.pack_propagate(False)

        # Agenten‐Info innerhalb des Info‐Panels
        self.agent_info_frame = tk.Frame(self.info_frame, bg='#171717')
        self.agent_info_frame.pack(padx=10, pady=20)

        self.agent_image_label = tk.Label(self.agent_info_frame, bg='#171717')
        self.agent_image_label.pack()

        self.agent_name_label = tk.Label(
            self.agent_info_frame, fg="white", bg='#171717',
            font=("Helvetica", 16, "bold")
        )
        self.agent_name_label.pack(pady=10)

        # Titel und Container für Visual Stimuli (unten im Info‐Panel)
        self.visual_stimuli_title = tk.Label(
            self.info_frame, text="Visual Stimuli", fg="white", bg='#171717',
            font=("Helvetica", 14)
        )
        self.visual_stimuli_frame = tk.Frame(self.info_frame, bg='#171717')

        # Zellgröße berechnen
        canvas_width = screen_width - info_frame_width
        grid_cols = len(self.world.level_matrix[0])
        grid_rows = len(self.world.level_matrix)
        self.cell_size = min(canvas_width / grid_cols, screen_height / grid_rows) * self.zoom_factor
        self.image_height = int(self.cell_size * 2.5)

        # Caches für bereits geladene Bilder/Animationen
        self.agent_images = {}    # Gif‐Frame‐Index pro Datei
        self.agent_gifs = {}      # Liste der PhotoImage‐Frames pro GIF
        self.food_images = {}     # Skalierte Food‐Bilder pro Food‐Instanz

        # Umgebungsbilder: Gras, Baum (Wall), Wasser
        self.environment_images = {
            "grass": self.load_environment_image("gui/sprites/environment/grass.png"),
            "tree":  self.load_environment_image("gui/sprites/environment/tree.png"),
            "water": self.load_environment_image("gui/sprites/environment/water.png"),
        }

        # Location‐Bilder (feste Namen in genau dieser Reihenfolge)
        # Dateipfade: "gui/sprites/environment/MUK.png", "gui/sprites/environment/BlauerEngel.png" usw.
        self.location_images = {}
        location_types = ["MUK", "BlauerEngel", "Holstentor", "Hauptbahnhof", "Dräger", "Uni"]
        for name in location_types:
            path = f"gui/sprites/environment/{name}.png"
            self.location_images[name] = self.load_environment_image(path)

        # 1) Jedes Location‐Objekt in world.level_matrix in der Reihenfolge, wie sie auftauchen,
        #    einer der sechs Location‐Typen zuordnen.
        self.location_mapping = {}
        idx = 0
        for row in self.world.level_matrix:
            for cell in row:
                for obj in cell:
                    if isinstance(obj, Location) and obj not in self.location_mapping:
                        # Wenn mehr Locations als Typen existieren, nehmen wir zyklisch den letzten
                        if idx < len(location_types):
                            self.location_mapping[obj] = location_types[idx]
                        else:
                            self.location_mapping[obj] = location_types[-1]
                        idx += 1

        # 2) Einen zufälligen Agenten auswählen (falls vorhanden) und Info‐Panel initialisieren
        all_agents = [
            agent for row in self.world.level_matrix
            for cell in row
            for agent in cell
            if isinstance(agent, AgentConstruct)
        ]
        if all_agents:
            self.selected_agent = random.choice(all_agents)
            self.update_info_panel(self.selected_agent)
        else:
            self.selected_agent = None

        # Unsichtbare Scrollbars einrichten (Screenshot‐Pan)
        self.h_scroll = tk.Scrollbar(self.canvas, orient=tk.HORIZONTAL, command=self.canvas.xview, width=0)
        self.v_scroll = tk.Scrollbar(self.canvas, orient=tk.VERTICAL, command=self.canvas.yview, width=0)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        # Tasten für Pan
        self.root.bind("<Left>",  lambda event: self.canvas.xview_scroll(-3, "units"))
        self.root.bind("<Right>", lambda event: self.canvas.xview_scroll(3, "units"))
        self.root.bind("<Up>",    lambda event: self.canvas.yview_scroll(-3, "units"))
        self.root.bind("<Down>",  lambda event: self.canvas.yview_scroll(3, "units"))

        # Tasten für Zoom
        self.root.bind("<plus>",      lambda event: self.zoom_in())
        self.root.bind("<KP_Add>",    lambda event: self.zoom_in())
        self.root.bind("<minus>",     lambda event: self.zoom_out())
        self.root.bind("<KP_Subtract>", lambda event: self.zoom_out())

        # Klicks im Canvas → Auswählen
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Wenn Fenstergröße sich ändert → Größe/Zellen neu berechnen
        self.root.bind("<Configure>", self.on_resize)

        # Periodische Updates (Visual Stimuli, Info‐Panel)
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
            self.environment_images["grass"] = self.load_environment_image("gui/sprites/environment/grass.png")
            self.environment_images["tree"]  = self.load_environment_image("gui/sprites/environment/tree.png")
            self.environment_images["water"] = self.load_environment_image("gui/sprites/environment/water.png")

            # Location‐Bilder neu laden
            for name in self.location_images:
                path = f"gui/sprites/environment/{name}.png"
                self.location_images[name] = self.load_environment_image(path)

            # Food‐ und Agenten‐Caches leeren, damit sie neu skaliert werden
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

        # Umgebungsbilder neu laden
        self.environment_images["grass"] = self.load_environment_image("gui/sprites/environment/grass.png")
        self.environment_images["tree"]  = self.load_environment_image("gui/sprites/environment/tree.png")
        self.environment_images["water"] = self.load_environment_image("gui/sprites/environment/water.png")

        # Location‐Bilder neu laden
        for name in self.location_images:
            path = f"gui/sprites/environment/{name}.png"
            self.location_images[name] = self.load_environment_image(path)

        # Caches leeren
        self.food_images.clear()
        self.agent_gifs.clear()
        self.agent_images.clear()
        self.draw_grid()

    def load_environment_image(self, path):
        """
        Lädt ein Umgebungsbild (Gras, Baum, Wasser oder Location) von dem angegebenen Pfad
        und skaliert es exakt auf die Zellengröße (self.cell_size × self.cell_size).
        """
        image = Image.open(path)
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
        Zeichnet das gesamte Spielfeld: Zellen‐Raster zentriert, dann
        Umgebung (Gras), Wall (Baum), Water, Location (+Overlay bei damaged),
        Food und schließlich animierte Agenten.
        """
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        grid_cols = len(self.world.level_matrix[0])
        grid_rows = len(self.world.level_matrix)
        grid_width = grid_cols * self.cell_size
        grid_height = grid_rows * self.cell_size

        # Offset zum Zentrieren
        self.offset_x = max((canvas_width - grid_width) / 2, 0)
        self.offset_y = max((canvas_height - grid_height) / 2, 0)

        for r, row in enumerate(self.world.level_matrix):
            for c, cell in enumerate(row):
                x1 = self.offset_x + c * self.cell_size
                y1 = self.offset_y + r * self.cell_size

                # 1) Gras‐Textur in den Hintergrund
                self.canvas.create_image(x1, y1, anchor=tk.NW, image=self.environment_images["grass"])

                # 2) Wall? → Baum‐Bild
                if any(isinstance(obj, Wall) for obj in cell):
                    self.canvas.create_image(x1, y1, anchor=tk.NW, image=self.environment_images["tree"])

                # 3) Sonst: Water? → Wasser‐Bild
                elif any(isinstance(obj, Water) for obj in cell):
                    self.canvas.create_image(x1, y1, anchor=tk.NW, image=self.environment_images["water"])

                # 4) Sonst: Location? → passendes Location‐Bild + ggf. rotes Overlay
                elif any(isinstance(obj, Location) for obj in cell):
                    location_obj = next(obj for obj in cell if isinstance(obj, Location))
                    loc_name = self.location_mapping.get(location_obj, None)
                    if loc_name and loc_name in self.location_images:
                        self.canvas.create_image(x1, y1, anchor=tk.NW, image=self.location_images[loc_name])

                    # Overlay bei damaged == True
                    if getattr(location_obj, "damaged", False):
                        x2 = x1 + self.cell_size
                        y2 = y1 + self.cell_size
                        overlay_color = "#ff0000"
                        # 50% Transparenz simulieren
                        for _ in range(10):
                            self.canvas.create_rectangle(
                                x1, y1, x2, y2,
                                fill=overlay_color, outline="", stipple="gray50"
                            )

                # 5) Sonst: Food? → Food‐Sprite mittig
                elif any(isinstance(obj, Food) for obj in cell):
                    food_obj = next(obj for obj in cell if isinstance(obj, Food))
                    self.draw_food(food_obj, x1, y1)

                # 6) Zum Schluss: Agenten (animierte GIFs) auf die Zelle legen
                for obj in cell:
                    if isinstance(obj, AgentConstruct):
                        self.draw_agent(obj, x1, y1)

        # Rotes Overlay um das ausgewählte Objekt (Agent oder anderes) zeichnen
        self.draw_red_overlay()

        # Scrollregion anpassen
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def draw_red_overlay(self):
        """
        Zeichnet ein halbtransparentes rotes Overlay:
        - Wenn ein Agent ausgewählt ist, werden alle Zellen innerhalb seiner Sichtweite (agent.los)
          markiert.
        - Wenn ein anderes Objekt ausgewählt ist (Food, Wall, Water, Location),
          dann wird nur die jeweilige Zelle markiert.
        """
        if not self.selected_agent:
            return

        col, row = self.find_agent_position(self.selected_agent)
        if col is None or row is None:
            return

        overlay_color = "#2e1111"

        # Wenn ausgewähltes Objekt ein Agent ist, nutzen wir agent.los statt einer festen 2
        if isinstance(self.selected_agent, AgentConstruct):
            los_range = getattr(self.selected_agent, "los", 0)
            # Lässt uns nicht über das Spielfeld hinauszeichnen
            grid_cols = len(self.world.level_matrix[0])
            grid_rows = len(self.world.level_matrix)

            for dx in range(-los_range, los_range + 1):
                for dy in range(-los_range, los_range + 1):
                    x = col + dx
                    y = row + dy
                    if 0 <= x < grid_cols and 0 <= y < grid_rows:
                        x1 = self.offset_x + x * self.cell_size
                        y1 = self.offset_y + y * self.cell_size
                        x2 = x1 + self.cell_size
                        y2 = y1 + self.cell_size
                        for _ in range(10):  # ≈50% Transparenz
                            self.canvas.create_rectangle(
                                x1, y1, x2, y2,
                                fill=overlay_color,
                                outline="",
                                stipple="gray50"
                            )
        else:
            # Wenn ausgewähltes Objekt kein Agent ist (Food, Wall, Water, Location),
            # dann nur die jeweilige Zelle hervorheben
            x1 = self.offset_x + col * self.cell_size
            y1 = self.offset_y + row * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            for _ in range(10):
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=overlay_color,
                    outline="",
                    stipple="gray50"
                )


    def find_agent_position(self, agent):
        """
        Gibt (Spalte, Zeile) zurück, in welcher sich das gegebene Objekt befindet.
        """
        for r, row in enumerate(self.world.level_matrix):
            for c, cell in enumerate(row):
                if agent in cell:
                    return c, r
        return None, None

    def draw_food(self, food, x, y):
        """
        Zeichnet ein Food‐Objekt mittig in der Zelle.
        """
        if food not in self.food_images:
            self.food_images[food], food.image_path = self.get_random_food_image()
        cx = x + self.cell_size / 2
        cy = y + self.cell_size / 2
        self.canvas.create_image(cx, cy, anchor=tk.CENTER, image=self.food_images[food])

    def draw_agent(self, agent, x, y):
        """
        Zeichnet den animierten Agenten‐GIF mittig in der Zelle.
        Die GIF‐Frames werden skaliert auf 80% der Zellgröße.
        """
        gif_path = f"gui/sprites/pokemon/gif/{agent.name_number}.gif"
        agent_size = int(self.cell_size * 0.8)

        if gif_path not in self.agent_gifs:
            image = Image.open(gif_path)
            frames = [
                ImageTk.PhotoImage(
                    self.resize_image_keep_aspect(frame, agent_size, agent_size),
                    master=self.root
                )
                for frame in ImageSequence.Iterator(image)
            ]
            self.agent_gifs[gif_path] = frames
            self.agent_images[gif_path] = 0

        frames = self.agent_gifs[gif_path]
        idx = self.agent_images[gif_path]
        cx = x + self.cell_size / 2
        cy = y + self.cell_size / 2
        self.canvas.create_image(cx, cy, anchor=tk.CENTER, image=frames[idx])
        self.agent_images[gif_path] = (idx + 1) % len(frames)

    def resize_image_keep_aspect(self, image, max_width, max_height):
        """
        Skaliert ein PIL‐Image so, dass es innerhalb von (max_width × max_height)
        bleibt, ohne das Seitenverhältnis zu verändern.
        """
        original_width, original_height = image.size
        ratio = min(max_width / original_width, max_height / original_height)
        new_w = int(original_width * ratio)
        new_h = int(original_height * ratio)
        return image.resize((new_w, new_h), Image.LANCZOS)

    def update_info_panel(self, obj):
        """
        Zeigt im rechten Info‐Panel Details zum ausgewählten Objekt an:
        Agent, Food, Wall, Water oder Location.
        """
        # 1) Visual Stimuli‐Frame leeren
        for widget in self.visual_stimuli_frame.winfo_children():
            widget.destroy()
        # 2) Alle Widgets im info_frame löschen, außer agent_info_frame, visual_stimuli_frame & Titel
        for widget in self.info_frame.winfo_children():
            if widget not in {self.agent_info_frame, self.visual_stimuli_frame, self.visual_stimuli_title}:
                widget.destroy()

        if isinstance(obj, AgentConstruct):
            # Agent anzeigen
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
            # Food anzeigen
            food_image = self.food_images.get(obj)
            if food_image:
                self.agent_image_label.config(image=food_image)
                self.agent_image_label.image = food_image
            self.agent_name_label.config(text="Food")
            self.visual_stimuli_title.pack_forget()
            self.visual_stimuli_frame.pack_forget()

            self.saturation_label = tk.Label(
                self.info_frame,
                text=f"Saturation: {obj.get_saturation()}",
                fg="white", bg='#171717',
                font=("Helvetica", 12), anchor='center'
            )
            self.saturation_label.pack(anchor='center')

            self.amount_label = tk.Label(
                self.info_frame,
                text=f"Amount: {obj.get_amount()}",
                fg="white", bg='#171717',
                font=("Helvetica", 12), anchor='center'
            )
            self.amount_label.pack(anchor='center')

            self.regrowth_label = tk.Label(
                self.info_frame,
                text=f"Time till regrowth: {obj.get_time_till_regrowth()}",
                fg="white", bg='#171717',
                font=("Helvetica", 12), anchor='center'
            )
            self.regrowth_label.pack(anchor='center')

        elif isinstance(obj, Wall):
            # Wall anzeigen
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
                self.info_frame,
                text="A wall, which prevents the agent's movement.",
                fg="white", bg='#171717',
                font=("Helvetica", 12), anchor='center'
            )
            self.description_label.pack(anchor='center')

        elif isinstance(obj, Water):
            # Water anzeigen
            png_path = "gui/sprites/environment/water.png"
            image = Image.open(png_path)
            image.thumbnail((self.image_height, self.image_height), Image.LANCZOS)
            water_image = ImageTk.PhotoImage(image)
            self.agent_image_label.config(image=water_image)
            self.agent_image_label.image = water_image
            self.agent_name_label.config(text="Water")
            self.visual_stimuli_title.pack_forget()
            self.visual_stimuli_frame.pack_forget()

            self.water_label = tk.Label(
                self.info_frame,
                text="Water, which works like a wall.",
                fg="white", bg='#171717',
                font=("Helvetica", 12), anchor='center'
            )
            self.water_label.pack(anchor='center')

        elif isinstance(obj, Location):
            # Location‐Info anzeigen (Name, Status)
            loc_name = self.location_mapping.get(obj, "Unknown")
            png_path = f"gui/sprites/environment/{loc_name}.png"
            if os.path.exists(png_path):
                image = Image.open(png_path)
                image.thumbnail((self.image_height, self.image_height), Image.LANCZOS)
                loc_image = ImageTk.PhotoImage(image)
                self.agent_image_label.config(image=loc_image)
                self.agent_image_label.image = loc_image

            self.agent_name_label.config(text=f"Location: {loc_name}")
            self.visual_stimuli_title.pack_forget()
            self.visual_stimuli_frame.pack_forget()

            damaged_flag = getattr(obj, "damaged", False)
            status_text = "Damaged" if damaged_flag else "Intact"
            self.location_status_label = tk.Label(
                self.info_frame,
                text=f"Status: {status_text}",
                fg="white", bg='#171717',
                font=("Helvetica", 12), anchor='center'
            )
            self.location_status_label.pack(anchor='center')

    def on_canvas_click(self, event):
        """
        Mausklick im Canvas → wählt das oberste Objekt in der angeklickten Zelle aus.
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if hasattr(self, "offset_x") and hasattr(self, "offset_y"):
            x -= self.offset_x
            y -= self.offset_y
        r, c = int(y // self.cell_size), int(x // self.cell_size)
        if 0 <= r < len(self.world.level_matrix) and 0 <= c < len(self.world.level_matrix[0]):
            for obj in self.world.level_matrix[r][c]:
                if isinstance(obj, (AgentConstruct, Food, Wall, Water, Location)):
                    self.selected_agent = obj
                    self.update_info_panel(self.selected_agent)
                    break

    def update(self):
        """
        Zeichnet das Spielfeld neu und sorgt dafür, dass Agenten‐GIFs animiert bleiben.
        Wird alle 50 ms erneut aufgerufen.
        """
        self.draw_grid()
        self.root.update_idletasks()
        self.root.update()
        self.root.after(50, self.update)

    def draw_matrix(self, matrix):
        """
        Zeichnet die Visual Stimuli‐Matrix (z. B. für Agenten‐Info) im Info‐Panel.
        """
        for widget in self.visual_stimuli_frame.winfo_children():
            widget.destroy()

        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                cell_text = val if val else " "
                cell_label = tk.Label(
                    self.visual_stimuli_frame,
                    text=cell_text, fg="white", bg='#171717',
                    relief='solid', borderwidth=1, width=4, height=2,
                    highlightbackground="white", highlightcolor="white", highlightthickness=1
                )
                cell_label.grid(row=i, column=j, padx=1, pady=1)

    def schedule_visual_stimuli_update(self):
        """
        Aktualisiert Info‐Panel bzw. Status‐Labels (Food, Location) alle 1000 ms.
        """
        if self.selected_agent is not None:
            self.update_info_panel(self.selected_agent)
            if isinstance(self.selected_agent, Food):
                self.saturation_label.config(text=f"Saturation: {self.selected_agent.get_saturation()}")
                self.amount_label.config(text=f"Amount: {self.selected_agent.get_amount()}")
                self.regrowth_label.config(text=f"Time till regrowth: {self.selected_agent.get_time_till_regrowth()}")
            elif isinstance(self.selected_agent, Location):
                damaged_flag = getattr(self.selected_agent, "damaged", False)
                status_text = "Damaged" if damaged_flag else "Intact"
                self.location_status_label.config(text=f"Status: {status_text}")

        self.root.after(1000, self.schedule_visual_stimuli_update)
