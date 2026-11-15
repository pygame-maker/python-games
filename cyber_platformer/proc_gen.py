import array
import math
import random
import pygame
from config import BIOMES, HEIGHT, TILE, WIDTH


def init_audio():
    sounds = {}
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        sr = 22050

        def synth(dur, f0, f1, vol=0.3, wave="square", decay=14.0):
            n = int(sr * dur)
            buf = array.array("h")
            phase = 0.0
            for i in range(n):
                t = i / sr
                f = f0 + (f1 - f0) * (i / n)
                phase += (2.0 * math.pi * f) / sr
                env = math.exp(-t * decay) * vol
                if wave == "square":
                    v = 1.0 if math.sin(phase) >= 0 else -1.0
                elif wave == "saw":
                    v = 2.0 * ((phase / (2.0 * math.pi)) % 1.0) - 1.0
                elif wave == "noise":
                    v = random.uniform(-1.0, 1.0)
                else:
                    v = math.sin(phase)
                buf.append(int(max(-32767, min(32767, v * env * 32767))))
            return pygame.mixer.Sound(buffer=buf)

        sounds["jump"] = synth(0.11, 210, 520, 0.22, "square", 16.0)
        sounds["djump"] = synth(0.13, 340, 760, 0.22, "sine", 14.0)
        sounds["dash"] = synth(0.15, 180, 620, 0.25, "saw", 12.0)
        sounds["shoot"] = synth(0.08, 820, 190, 0.22, "square", 24.0)
        sounds["rail"] = synth(0.22, 1200, 110, 0.30, "saw", 9.0)
        sounds["hit"] = synth(0.10, 180, 50, 0.30, "noise", 22.0)
        sounds["boom"] = synth(0.28, 130, 28, 0.38, "noise", 8.0)
        sounds["coin"] = synth(0.12, 660, 990, 0.20, "sine", 14.0)
        sounds["hook"] = synth(0.10, 400, 900, 0.20, "square", 18.0)
        sounds["buy"] = synth(0.20, 440, 880, 0.25, "square", 8.0)
    except Exception:
        pass
    return sounds
def build_biome_assets(biome_idx):
    b = BIOMES[biome_idx % len(BIOMES)]
    assets = {}

    # 1. Тайл платформы с неоновой кромкой и фактурой
    tile = pygame.Surface((TILE, TILE)).convert()
    tile.fill(b["tile_main"])
    pygame.draw.rect(tile, b["tile_edge"], (0, 0, TILE, 3))
    pygame.draw.rect(tile, (12, 16, 24), (0, 3, TILE, TILE - 3), 1)
    pygame.draw.line(tile, b["tile_edge"], (4, 8), (10, 8), 1)
    assets["tile"] = tile

    # 2. Разрушаемый блок
    cracked = pygame.Surface((TILE, TILE)).convert()
    cracked.fill((55, 45, 38))
    pygame.draw.rect(cracked, (220, 150, 50), (0, 0, TILE, TILE), 2)
    pygame.draw.line(cracked, (25, 20, 15), (4, 4), (20, 20), 2)
    pygame.draw.line(cracked, (25, 20, 15), (20, 5), (6, 18), 2)
    assets["cracked"] = cracked

    # 3. Батут (Jump Pad)
    pad = pygame.Surface((TILE, TILE), pygame.SRCALPHA).convert_alpha()
    pygame.draw.rect(pad, (40, 45, 60), (2, TILE - 6, TILE - 4, 6))
    pygame.draw.rect(pad, (255, 60, 220), (4, TILE - 10, TILE - 8, 4))
    assets["pad"] = pad

    # 4. Шипы
    spike = pygame.Surface((TILE, TILE), pygame.SRCALPHA).convert_alpha()
    for sx in (0, 8, 16):
        pygame.draw.polygon(spike, (255, 55, 75), [(sx, TILE), (sx + 4, TILE - 12), (sx + 8, TILE)])
        pygame.draw.polygon(spike, (255, 190, 200), [(sx + 2, TILE), (sx + 4, TILE - 10), (sx + 5, TILE)])
    assets["spike"] = spike

    # 5. Многослойный параллакс-фон города/комплекса
    bg = pygame.Surface((WIDTH, HEIGHT)).convert()
    for y in range(HEIGHT):
        t = y / HEIGHT
        col = [int(b["bg_top"][i] * (1 - t) + b["bg_bot"][i] * t) for i in range(3)]
        pygame.draw.line(bg, col, (0, y), (WIDTH, y))

    rng = random.Random(100 + biome_idx)
    for _ in range(18):
        bw = rng.randint(28, 68)
        bh = rng.randint(80, 230)
        bx = rng.randint(-20, WIDTH)
        by = HEIGHT - bh
        pygame.draw.rect(bg, (10, 14, 22), (bx, by, bw, bh))
        for wy in range(by + 10, HEIGHT - 10, 14):
            for wx in range(bx + 6, bx + bw - 8, 10):
                if rng.random() < 0.35:
                    pygame.draw.rect(bg, b["tile_edge"], (wx, wy, 4, 6))
    assets["bg"] = bg

    # 6. Кадры анимации игрока (стоя, бег 1, бег 2, прыжок)
    assets["player"] = []
    for frame in range(4):
        p = pygame.Surface((20, 28), pygame.SRCALPHA).convert_alpha()
        # Плащ/шарф
        scarf_y = 9 + (1 if frame in (1, 3) else 0)
        pygame.draw.polygon(p, (255, 50, 110), [(6, scarf_y), (0, scarf_y + 3), (5, scarf_y + 6)])
        # Тело и броня
        pygame.draw.rect(p, (30, 42, 62), (5, 8, 10, 13), border_radius=3)
        pygame.draw.rect(p, (0, 245, 210), (5, 8, 10, 13), 1, border_radius=3)
        # Голова и визор
        pygame.draw.rect(p, (25, 32, 48), (5, 1, 10, 8), border_radius=2)
        pygame.draw.rect(p, (0, 255, 220), (9, 3, 6, 3))
        # Ноги (анимация шага)
        if frame == 1:
            pygame.draw.line(p, (0, 220, 190), (7, 21), (4, 27), 2)
            pygame.draw.line(p, (0, 220, 190), (12, 21), (15, 26), 2)
        elif frame == 2:
            pygame.draw.line(p, (0, 220, 190), (7, 21), (13, 27), 2)
            pygame.draw.line(p, (0, 220, 190), (12, 21), (6, 26), 2)
        elif frame == 3:
            pygame.draw.line(p, (0, 220, 190), (7, 21), (5, 25), 2)
            pygame.draw.line(p, (0, 220, 190), (12, 21), (14, 24), 2)
        else:
            pygame.draw.line(p, (0, 220, 190), (7, 21), (7, 27), 2)
            pygame.draw.line(p, (0, 220, 190), (12, 21), (12, 27), 2)
        assets["player"].append(p)

    # 7. Враги: Кибер-паук, Летающий дрон, Турель и Босс
    spider = pygame.Surface((24, 18), pygame.SRCALPHA).convert_alpha()
    pygame.draw.ellipse(spider, (50, 20, 30), (4, 4, 16, 10))
    pygame.draw.ellipse(spider, (255, 60, 90), (4, 4, 16, 10), 2)
    pygame.draw.circle(spider, (255, 230, 50), (15, 8), 2)
    for lx in (5, 11, 17):
        pygame.draw.line(spider, (255, 60, 90), (lx, 13), (lx - 2, 17), 2)
    assets["spider"] = spider

    flyer = pygame.Surface((24, 24), pygame.SRCALPHA).convert_alpha()
    pygame.draw.circle(flyer, (180, 50, 255), (12, 12), 8, 2)
    pygame.draw.circle(flyer, (255, 80, 120), (12, 12), 4)
    pygame.draw.line(flyer, (120, 240, 255), (2, 7), (22, 7), 2)
    assets["flyer"] = flyer

    boss = pygame.Surface((56, 56), pygame.SRCALPHA).convert_alpha()
    pygame.draw.circle(boss, (255, 50, 80, 50), (28, 28), 27)
    pygame.draw.polygon(boss, (38, 16, 26), [(28, 4), (52, 28), (28, 52), (4, 28)])
    pygame.draw.polygon(boss, (255, 70, 95), [(28, 4), (52, 28), (28, 52), (4, 28)], 3)
    pygame.draw.circle(boss, (255, 220, 60), (28, 28), 9)
    assets["boss"] = boss

    return assets
