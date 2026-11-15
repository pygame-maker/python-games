WIDTH, HEIGHT = 640, 360
FPS = 60
TILE = 24
GRAVITY = 980.0
MAX_FALL = 520.0

BIOMES = [
    {
        "name": "НЕОНОВЫЙ СЕКТОР",
        "bg_top": (8, 12, 24),
        "bg_bot": (18, 28, 48),
        "tile_main": (24, 34, 52),
        "tile_edge": (0, 230, 210),
        "weather": "rain",
    },
    {
        "name": "ТОКСИЧНЫЕ СТОКИ",
        "bg_top": (10, 20, 14),
        "bg_bot": (22, 42, 26),
        "tile_main": (28, 44, 32),
        "tile_edge": (80, 255, 90),
        "weather": "spores",
    },
    {
        "name": "КРИО-СЕРВЕРЫ",
        "bg_top": (10, 18, 32),
        "bg_bot": (26, 46, 72),
        "tile_main": (34, 56, 84),
        "tile_edge": (130, 220, 255),
        "weather": "snow",
    },
    {
        "name": "ЯДРО РЕАКТОРА",
        "bg_top": (26, 10, 12),
        "bg_bot": (52, 18, 22),
        "tile_main": (48, 24, 28),
        "tile_edge": (255, 95, 45),
        "weather": "embers",
    },
]

WEAPONS = {
    "blaster": {"name": "Импульс-пистолет", "cd": 0.22, "dmg": 2, "spd": 440, "spread": 0.03, "count": 1, "col": (0, 255, 220)},
    "shotgun": {"name": "Плазма-дробовик", "cd": 0.55, "dmg": 2, "spd": 390, "spread": 0.24, "count": 4, "col": (255, 190, 50)},
    "railgun": {"name": "Рельсотрон", "cd": 0.75, "dmg": 7, "spd": 680, "spread": 0.0, "count": 1, "col": (255, 70, 180)},
    "smg": {"name": "Кибер-ПП", "cd": 0.09, "dmg": 1, "spd": 460, "spread": 0.12, "count": 1, "col": (110, 255, 120)},
}

UPGRADES = [
    {"id": "max_hp", "name": "+25 Макс. Броня", "cost": 40},
    {"id": "double_jump", "name": "Двойной прыжок", "cost": 60},
    {"id": "dash_dmg", "name": "Энерго-рывок (урон)", "cost": 55},
    {"id": "vampire", "name": "Вампиризм (+2 HP за килл)", "cost": 75},
    {"id": "magnet", "name": "Магнит кредитов", "cost": 35},
    {"id": "crit", "name": "+15% Крит. урон (x2.5)", "cost": 50},
]
