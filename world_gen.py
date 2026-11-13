import pygame
import numpy as np
from noise import pnoise2
from config import WORLD_W, WORLD_H, GRID_SIZE

def generate_island_data(width, height, seed):
    """Генерирует массив текстуры острова с биомами и карту высот."""
    scale = 7.5
    height_map = np.zeros((width, height), dtype=np.float32)
    cx, cy = width / 2.0, height / 2.0
    max_dist = np.sqrt(cx**2 + cy**2)

    for x in range(0, width, 2):
        for y in range(0, height, 2):
            nx = (x / width) * scale
            ny = (y / height) * scale
            n = pnoise2(nx, ny, octaves=6, persistence=0.5, lacunarity=2.0, base=seed) + 0.5
            dist = np.sqrt((x - cx)**2 + (y - cy)**2) / max_dist
            mask = 1.0 - (dist ** 2.4) * 1.35
            val = np.clip(n * mask + 0.22, 0.0, 1.0)
            height_map[x:x+2, y:y+2] = val

    light = np.zeros((width, height), dtype=np.float32)
    light[:-1, :-1] = height_map[:-1, :-1] - height_map[1:, 1:]
    relief = np.where(height_map > 0.36, 22.0, 5.0)
    light = np.clip(light * relief + 0.85, 0.45, 1.25)

    tex = np.zeros((width, height, 3), dtype=np.uint8)
    tex[height_map < 0.28] = (20, 60, 120)                                 # Глубокая вода
    tex[(height_map >= 0.28) & (height_map < 0.36)] = (40, 110, 160)       # Мелководье
    tex[(height_map >= 0.36) & (height_map < 0.42)] = (210, 190, 130)      # Песок
    tex[(height_map >= 0.42) & (height_map < 0.68)] = (55, 120, 45)        # Трава
    tex[height_map >= 0.68] = (105, 105, 110)                              # Скалы

    grain = np.random.uniform(-14, 14, (width, height, 1))
    final_tex = np.clip((tex + grain) * light[:, :, np.newaxis], 0, 255).astype(np.uint8)
    return final_tex, height_map

def create_sprites(seed):
    """Создает процедурные текстуры для деревьев, камней, построек и босса."""
    sprites = {"trees": [], "rocks": []}

    # Деревья
    for i in range(5):
        surf = pygame.Surface((44, 44), pygame.SRCALPHA)
        for x in range(44):
            for y in range(44):
                dist = np.hypot(x - 22, y - 22)
                n = pnoise2(x * 0.15, y * 0.15, octaves=3, base=seed + i)
                if dist + n * 8 < 16:
                    shade = int(n * 45)
                    light = 20 if (x + y) < 44 else -15
                    surf.set_at((x, y), (
                        np.clip(35 + shade + light, 15, 80),
                        np.clip(105 + shade + light, 50, 160),
                        np.clip(30 + shade + light, 10, 70),
                        255
                    ))
        sprites["trees"].append(surf)

    # Камни
    for i in range(5):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        for x in range(32):
            for y in range(32):
                dist = np.hypot(x - 16, y - 16)
                n = pnoise2(x * 0.2, y * 0.2, octaves=4, base=seed + 10 + i)
                if dist + n * 6 < 12:
                    crack = -35 if abs(n) < 0.04 else 0
                    light = 15 if (x + y) < 32 else -15
                    val = np.clip(115 + int(n * 50) + light + crack, 40, 180)
                    surf.set_at((x, y), (val, val, val + 5, 255))
        sprites["rocks"].append(surf)

    # Ягодные кусты
    for key, has_berries in (("bush_full", True), ("bush_empty", False)):
        surf = pygame.Surface((26, 26), pygame.SRCALPHA)
        for x in range(26):
            for y in range(26):
                if np.hypot(x - 13, y - 13) + pnoise2(x * 0.25, y * 0.25, base=77) * 4 < 10:
                    surf.set_at((x, y), (30, 100, 35, 255))
        if has_berries:
            for bx, by in ((9, 10), (16, 9), (12, 16), (17, 15)):
                pygame.draw.circle(surf, (220, 40, 60), (bx, by), 2)
        sprites[key] = surf

    # Деревянные постройки (Пол, Стена, Верстак, Сундук)
    for key, base, border in (
        ("floor", (145, 95, 50), None),
        ("wall", (105, 65, 30), (55, 30, 10)),
        ("bench", (160, 110, 55), (210, 180, 90)),
        ("chest", (130, 80, 35), (230, 190, 60)),
    ):
        r_base, g_base, b_base = base
        surf = pygame.Surface((GRID_SIZE, GRID_SIZE))
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                n = pnoise2(x * 0.1, y * 0.35, octaves=3, base=12)
                seam = -25 if (y % 8 == 0) else 0
                surf.set_at((x, y), (
                    np.clip(r_base + int(n * 25) + seam, 20, 230),
                    np.clip(g_base + int(n * 20) + seam, 20, 200),
                    np.clip(b_base + int(n * 15) + seam, 10, 160)
                ))
        if border:
            pygame.draw.rect(surf, border, (0, 0, GRID_SIZE, GRID_SIZE), 3)
        if key == "bench":
            pygame.draw.rect(surf, (180, 180, 190), (8, 8, 16, 6))
        elif key == "chest":
            pygame.draw.rect(surf, (240, 200, 50), (13, 12, 6, 8))
        sprites[key] = surf

    # Грядки (0 - пустая, 1 - росток, 2 - созревший урожай)
    for stage in (0, 1, 2):
        surf = pygame.Surface((GRID_SIZE, GRID_SIZE))
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                n = pnoise2(x * 0.25, y * 0.25, base=99)
                furrow = -20 if (y % 6 < 2) else 10
                surf.set_at((x, y), (
                    np.clip(75 + int(n * 20) + furrow, 30, 120),
                    np.clip(50 + int(n * 15) + furrow, 20, 90),
                    30
                ))
        if stage == 1:
            for gx in (10, 22):
                for gy in (10, 22):
                    pygame.draw.circle(surf, (70, 170, 60), (gx, gy), 3)
        elif stage == 2:
            for gx in (10, 22):
                for gy in (10, 22):
                    pygame.draw.circle(surf, (235, 190, 40), (gx, gy), 5)
                    pygame.draw.circle(surf, (80, 160, 50), (gx, gy - 3), 2)
        sprites[f"farm_{stage}"] = surf

    # Процедурный спрайт Босса (Древний Каменный Голем)
    boss_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    for x in range(64):
        for y in range(64):
            dist = np.hypot(x - 32, y - 32)
            n = pnoise2(x * 0.14, y * 0.14, octaves=4, base=seed + 55)
            if dist + n * 10 < 24:
                rune = 60 if abs(n) < 0.035 else 0
                val = np.clip(85 + int(n * 45), 35, 140)
                boss_surf.set_at((x, y), (np.clip(val + rune * 2, 0, 255), np.clip(val + rune, 0, 255), val, 255))
    pygame.draw.circle(boss_surf, (255, 80, 20), (24, 26), 4)
    pygame.draw.circle(boss_surf, (255, 80, 20), (40, 26), 4)
    sprites["boss"] = boss_surf

    return sprites

def create_light_mask(radius):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for x in range(radius * 2):
        for y in range(radius * 2):
            dist = np.hypot(x - radius, y - radius)
            if dist < radius:
                alpha = int(255 * (1 - (dist / radius) ** 1.5))
                surf.set_at((x, y), (255, 220, 150, alpha))
    return surf
