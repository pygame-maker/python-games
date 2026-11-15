import random
import pygame
from config import TILE


def generate_sector(sector_num):
    """Генерирует паркур-уровень без врагов: платформы, батуты, тайники, дата-кристаллы и портал."""
    w, h = 100 + min(40, sector_num * 8), 32
    # 0=пусто, 1=стена, 2=разрушаемый блок, 3=шипы, 4=батут
    grid = [[0 for _ in range(w)] for _ in range(h)]

    for x in range(w):
        grid[0][x] = 1
        grid[1][x] = 1
        grid[h - 1][x] = 1
        grid[h - 2][x] = 1
    for y in range(h):
        grid[y][0] = 1
        grid[y][1] = 1
        grid[y][w - 1] = 1
        grid[y][w - 2] = 1

    pickups = []
    moving_plats = []
    lasers = []
    terminals = []

    cur_x = 4
    floor_y = h - 5
    spawn_pos = (cur_x * TILE + 12, (floor_y - 2) * TILE)

    while cur_x < w - 18:
        sec_len = random.randint(10, 15)
        sec_type = random.choice(["parkour", "vertical", "moving", "secret", "trap"])
        next_floor_y = max(10, min(h - 4, floor_y + random.randint(-3, 3)))

        for x in range(cur_x, min(w - 14, cur_x + sec_len)):
            is_gap = (sec_type in ("parkour", "moving")) and (cur_x + 3 <= x <= cur_x + sec_len - 4) and (x % 5 in (2, 3))
            if not is_gap:
                for y in range(floor_y, h - 2):
                    grid[y][x] = 1
                if sec_type == "trap" and x % 5 == 0 and x > cur_x + 2:
                    grid[floor_y - 1][x] = 3
            else:
                if x % 5 == 2:
                    moving_plats.append(
                        {
                            "x": float(x * TILE),
                            "y": float((floor_y - 1) * TILE),
                            "w": TILE * 2,
                            "h": 10,
                            "vx": 55.0,
                            "vy": 0.0,
                            "min_x": float((x - 1) * TILE),
                            "max_x": float((x + 2) * TILE),
                        }
                    )

        # Верхние платформы для паркура и крюка-кошки
        plat_y = floor_y - random.randint(4, 6)
        plat_x0 = cur_x + 2
        plat_x1 = min(w - 15, cur_x + sec_len - 2)
        for px in range(plat_x0, plat_x1):
            grid[plat_y][px] = 1

        if sec_type == "vertical" and plat_x0 > 3:
            grid[floor_y - 1][plat_x0 - 1] = 4

        # Секретный тайник за треснувшей стеной (пробивается рывком или ударом сверху)
        if sec_type == "secret" and floor_y > 12:
            wall_x = cur_x + sec_len // 2
            for wy in range(floor_y - 4, floor_y):
                grid[wy][wall_x] = 2
            pickups.append({"x": float((wall_x + 2) * TILE), "y": float((floor_y - 2) * TILE), "kind": "chest"})

        if sec_type == "trap":
            lx = (cur_x + sec_len // 2) * TILE + 12
            lasers.append({"x": float(lx), "y1": float(2 * TILE), "y2": float(floor_y * TILE), "timer": random.uniform(0, 3.0)})

        # Дата-кристаллы на платформах
        for cx in range(plat_x0, plat_x1, 3):
            pickups.append({"x": float(cx * TILE + 12), "y": float((plat_y - 1) * TILE + 8), "kind": "coin"})

        cur_x += sec_len
        floor_y = next_floor_y

    # Финальная площадка с терминалом апгрейдов и порталом выхода
    end_x = w - 12
    end_y = h - 5
    for x in range(end_x - 3, w - 2):
        for y in range(end_y, h - 2):
            grid[y][x] = 1

    terminals.append({"x": float((end_x - 1) * TILE + 12), "y": float((end_y - 1) * TILE), "used": False})
    portal_pos = (float((end_x + 3) * TILE + 12), float((end_y - 1) * TILE))

    return {
        "w": w,
        "h": h,
        "grid": grid,
        "spawn": spawn_pos,
        "enemies": [],
        "pickups": pickups,
        "moving_plats": moving_plats,
        "lasers": lasers,
        "terminals": terminals,
        "boss": None,
        "portal": portal_pos,
    }
