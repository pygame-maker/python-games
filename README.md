# 🏝️ Procedural Island Survival

A top-down 2D survival sandbox game written in pure Python. **The core feature of this project:** there are zero external image, texture, or audio files—the entire island landscape, biomes, bump-mapped shadows, sprites, UI, and even sound effects are mathematically synthesized at runtime.

Designed as a lightweight, self-contained game for both desktop PCs and a custom **Orange Pi Zero 3 Cyberdeck**.

---

## ✨ Key Features

* **100% Procedural Graphics:** A seamless island with distinct biomes (deep water, shallows, sandy beaches, grass, and rocky peaks) generated via Perlin noise with real-time relief shading (Bump Mapping).
* **Procedural Audio Synthesizer:** All sound effects (chopping wood, mining stone, building, harvesting, and enemy growls) are generated from scratch using `NumPy` waveforms and played via `Pygame`.
* **Day/Night Cycle & Survival:** A full cycle featuring a 10-minute day and a 5-minute night with dynamic lighting. At night, body temperature drops and forest shadows emerge from the darkness—stay near campfires or carry a torch to survive.
* **Base Building & Farming:** Construct wooden floors, walls, campfires, workbenches, storage chests, and farm plots to grow crops from harvested seeds.
* **Crafting & Island Boss:** Craft a stone axe, spear, and hand torch. Venture to the center of the island to defeat the **Ancient Stone Golem**, claim its *Golem Heart*, and forge the **Fire Sword**.
* **Save & Load System:** Instantly save and restore the entire procedural world state to a single file.

---

## 🛠️ Installation & Running

### Desktop (Windows / Linux / macOS)

1. Clone the repository:
   ```bash
   git clone https://github.com
   cd YOUR_REPO_NAME
   ```
2. Install the required libraries:
   ```bash
   pip install pygame numpy noise
   ```
3. Run the game:
   ```bash
   python main.py
   ```

### Orange Pi Zero 3 / Raspberry Pi (Armbian / Debian)

On ARM single-board computers, installing `pygame` and `numpy` via system packages is recommended for fast setup:
```bash
sudo apt update
sudo apt install python3-pygame python3-numpy python3-pip -y
pip3 install noise --break-system-packages
python3 main.py
```

---

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **W A S D** | Move character |
| **1 — 7** | Select hotbar slot (1: Hand/Weapon, 2: Floor, 3: Wall, 4: Campfire, 5: Workbench, 6: Chest, 7: Farm Plot) |
| **Left Click** | Attack, gather resources, harvest crops, build, or deposit +5 items into a chest |
| **Right Click** | Withdraw all items from a chest |
| **E** | Eat food (restores hunger and health) |
| **F** | Go fishing (must stand near the water's edge) |
| **Z / X / C / V** | Craft at a Workbench (Stone Axe / Spear / Hand Torch / Fire Sword) |
| **F5 / F9** | Quick Save / Quick Load world state |
| **R** | Generate a new island after death |

---

## 📂 Project Structure

* `main.py` — Main game loop, input handling, survival logic, and rendering pipeline.
* `config.py` — Screen resolution, world dimensions, and game balance settings.
* `world_gen.py` — Heightmap, biome coloring, and procedural sprite generator.
* `entities.py` — Crop growth timers, night shadow AI, and Ancient Golem boss logic.
* `audio.py` — Procedural `NumPy` sound wave synthesizer.
* `ui.py` — HUD rendering, boss health bar, and live minimap.
