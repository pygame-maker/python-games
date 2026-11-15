import math
import random
import pygame
from config import GRAVITY, MAX_FALL, TILE, WEAPONS


def rect_collides_tiles(grid, rect, solid_types=(1, 2)):
    x0 = max(0, rect.left // TILE)
    x1 = min(len(grid[0]) - 1, rect.right // TILE)
    y0 = max(0, rect.top // TILE)
    y1 = min(len(grid) - 1, rect.bottom // TILE)
    hits = []
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            t = grid[ty][tx]
            if t in solid_types:
                t_rect = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
                if rect.colliderect(t_rect):
                    hits.append((tx, ty, t, t_rect))
    return hits


def update_player(st, keys, jump_pressed, dash_pressed, hook_pressed, slam_pressed, dt, sounds, add_part, add_text):
    p = st["player"]
    lvl = st["level_data"]
    grid = lvl["grid"]

    if p["invuln"] > 0:
        p["invuln"] -= dt
    if p["dash_cd"] > 0:
        p["dash_cd"] -= dt
    if p["shoot_cd"] > 0:
        p["shoot_cd"] -= dt
    if p["coyote"] > 0:
        p["coyote"] -= dt
    if p["jump_buf"] > 0:
        p["jump_buf"] -= dt

    if jump_pressed:
        p["jump_buf"] = 0.14

    move_dir = (1 if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) else 0) - (1 if (keys[pygame.K_a] or keys[pygame.K_LEFT]) else 0)
    if move_dir != 0:
        p["facing"] = move_dir

    # Крюк-кошка (Grappling Hook на E или C)
    if hook_pressed:
        if p["hook"]:
            p["hook"] = None
        else:
            ang = -0.85 if p["facing"] > 0 else (-math.pi + 0.85)
            for dist in range(24, 185, 12):
                hx = p["x"] + 8 + math.cos(ang) * dist
                hy = p["y"] + 12 + math.sin(ang) * dist
                gx, gy = int(hx // TILE), int(hy // TILE)
                if 0 <= gy < len(grid) and 0 <= gx < len(grid[0]) and grid[gy][gx] in (1, 2):
                    p["hook"] = (hx, hy)
                    p["jumps_left"] = p["max_jumps"]
                    if "hook" in sounds:
                        sounds["hook"].play()
                    add_part(hx, hy, (0, 255, 220), 8, 90)
                    break

    # Рывок (Dash на Shift или X)
    if dash_pressed and p["dash_cd"] <= 0 and p["dash_timer"] <= 0:
        p["dash_timer"] = 0.16
        p["dash_cd"] = 0.70
        p["invuln"] = 0.25
        p["hook"] = None
        p["vx"] = p["facing"] * 450.0
        p["vy"] = 0.0
        st["shake"] = 3.0
        if "dash" in sounds:
            sounds["dash"].play()
        add_part(p["x"] + 8, p["y"] + 12, (0, 255, 210), 12, 110)

    # Удар сверху (Ground Slam на S/Вниз в воздухе)
    if slam_pressed and not p["on_ground"] and not p["slamming"]:
        p["slamming"] = True
        p["hook"] = None
        p["vx"] = 0.0
        p["vy"] = 620.0

    if p["hook"]:
        hx, hy = p["hook"]
        dx, dy = hx - (p["x"] + 8), hy - (p["y"] + 12)
        d = math.hypot(dx, dy)
        if d < 22:
            p["hook"] = None
            p["vy"] = -260.0
        else:
            p["vx"] = (dx / d) * 390.0
            p["vy"] = (dy / d) * 390.0
    elif p["dash_timer"] > 0:
        p["dash_timer"] -= dt
        if random.random() < 0.7:
            st["afterimages"].append({"x": p["x"], "y": p["y"], "facing": p["facing"], "life": 0.18})
    else:
        target_vx = move_dir * 185.0
        accel = 1400.0 if p["on_ground"] else 900.0
        if p["vx"] < target_vx:
            p["vx"] = min(target_vx, p["vx"] + accel * dt)
        elif p["vx"] > target_vx:
            p["vx"] = max(target_vx, p["vx"] - accel * dt)

        grav = GRAVITY * (0.35 if (p["wall_slide"] != 0 and p["vy"] > 0) else 1.0)
        p["vy"] = min(MAX_FALL, p["vy"] + grav * dt)

    if p["jump_buf"] > 0:
        if p["coyote"] > 0:
            p["vy"] = -345.0
            p["on_ground"] = False
            p["coyote"] = 0.0
            p["jump_buf"] = 0.0
            p["jumps_left"] = p["max_jumps"] - 1
            if "jump" in sounds:
                sounds["jump"].play()
            add_part(p["x"] + 8, p["y"] + 24, (180, 240, 255), 6, 70)
        elif p["wall_slide"] != 0:
            p["vx"] = -p["wall_slide"] * 240.0
            p["vy"] = -335.0
            p["facing"] = -p["wall_slide"]
            p["jump_buf"] = 0.0
            if "jump" in sounds:
                sounds["jump"].play()
            add_part(p["x"] + 8, p["y"] + 12, (0, 255, 200), 8, 80)
        elif p["jumps_left"] > 0:
            p["vy"] = -315.0
            p["jumps_left"] -= 1
            p["jump_buf"] = 0.0
            if "djump" in sounds:
                sounds["djump"].play()
            add_part(p["x"] + 8, p["y"] + 24, (0, 255, 200), 10, 95)

    rect = pygame.Rect(int(p["x"]), int(p["y"]), 16, 24)
    rect.x += int(round(p["vx"] * dt))
    p["wall_slide"] = 0
    for tx, ty, t_type, t_rect in rect_collides_tiles(grid, rect):
        if t_type == 2 and p["dash_timer"] > 0:
            grid[ty][tx] = 0
            st["shake"] = 5.0
            if "boom" in sounds:
                sounds["boom"].play()
            add_part(tx * TILE + 12, ty * TILE + 12, (230, 160, 60), 14, 140)
            continue

        if p["vx"] > 0:
            rect.right = t_rect.left
            if not p["on_ground"]:
                p["wall_slide"] = 1
        elif p["vx"] < 0:
            rect.left = t_rect.right
            if not p["on_ground"]:
                p["wall_slide"] = -1
        p["vx"] = 0.0
        p["hook"] = None

    p["on_ground"] = False
    rect.y += int(round(p["vy"] * dt))

    for tx, ty, t_type, t_rect in rect_collides_tiles(grid, rect):
        if t_type == 2 and p["slamming"]:
            grid[ty][tx] = 0
            st["shake"] = 6.0
            if "boom" in sounds:
                sounds["boom"].play()
            add_part(tx * TILE + 12, ty * TILE + 12, (230, 160, 60), 14, 140)
            continue

        if p["vy"] > 0:
            rect.bottom = t_rect.top
            p["on_ground"] = True
            p["coyote"] = 0.12
            p["jumps_left"] = p["max_jumps"]
            if p["slamming"]:
                p["slamming"] = False
                st["shake"] = 6.0
                if "boom" in sounds:
                    sounds["boom"].play()
                add_part(rect.centerx, rect.bottom, (255, 200, 80), 16, 160)
            p["vy"] = 0.0
        elif p["vy"] < 0:
            rect.top = t_rect.bottom
            p["vy"] = 0.0
            p["hook"] = None

    for mp in lvl["moving_plats"]:
        mp_rect = pygame.Rect(int(mp["x"]), int(mp["y"]), mp["w"], mp["h"])
        if p["vy"] >= 0 and rect.colliderect(mp_rect) and rect.bottom - p["vy"] * dt <= mp_rect.top + 8:
            rect.bottom = mp_rect.top
            rect.x += int(round(mp["vx"] * dt))
            p["on_ground"] = True
            p["coyote"] = 0.12
            p["jumps_left"] = p["max_jumps"]
            p["vy"] = 0.0

    for tx, ty, t_type, _ in rect_collides_tiles(grid, rect, solid_types=(3, 4)):
        if t_type == 4:
            p["vy"] = -510.0
            p["on_ground"] = False
            p["jumps_left"] = p["max_jumps"]
            if "djump" in sounds:
                sounds["djump"].play()
            add_part(tx * TILE + 12, ty * TILE + 12, (255, 60, 220), 12, 130)
        elif t_type == 3 and p["invuln"] <= 0:
            p["hp"] -= 15
            p["invuln"] = 0.8
            p["vy"] = -260.0
            st["shake"] = 6.0
            if "hit" in sounds:
                sounds["hit"].play()
            add_text(rect.centerx, rect.top - 8, "-15 ШИПЫ", (255, 60, 80))

    p["x"], p["y"] = float(rect.x), float(rect.y)

    if not p["on_ground"]:
        p["anim_frame"] = 3
    elif abs(p["vx"]) > 15:
        p["anim_t"] += dt * 12.0
        p["anim_frame"] = 1 + (int(p["anim_t"]) % 2)
    else:
        p["anim_frame"] = 0
def update_world_entities(st, dt, sounds, add_part, add_text):
    p = st["player"]
    lvl = st["level_data"]
    p_rect = pygame.Rect(int(p["x"]), int(p["y"]), 16, 24)

    for mp in lvl["moving_plats"]:
        mp["x"] += mp["vx"] * dt
        if mp["x"] <= mp["min_x"] or mp["x"] >= mp["max_x"]:
            mp["vx"] = -mp["vx"]

    for lsr in lvl["lasers"]:
        lsr["timer"] = (lsr["timer"] + dt) % 3.2
        lsr["active"] = lsr["timer"] < 1.5
        if lsr["active"] and p["invuln"] <= 0:
            l_rect = pygame.Rect(int(lsr["x"] - 3), int(lsr["y1"]), 6, int(lsr["y2"] - lsr["y1"]))
            if p_rect.colliderect(l_rect):
                p["hp"] -= 18
                p["invuln"] = 0.8
                st["shake"] = 6.0
                if "hit" in sounds:
                    sounds["hit"].play()
                add_text(p_rect.centerx, p_rect.top - 8, "-18 ЛАЗЕР", (255, 50, 90))

    mag_range = 110.0 if p["upgrades"]["magnet"] else 28.0
    for item in lvl["pickups"][:]:
        dx = p_rect.centerx - item["x"]
        dy = p_rect.centery - item["y"]
        dist = math.hypot(dx, dy)

        if item["kind"] == "coin" and dist < mag_range and dist > 1:
            item["x"] += (dx / dist) * 240.0 * dt
            item["y"] += (dy / dist) * 240.0 * dt

        if dist < 20:
            lvl["pickups"].remove(item)
            if item["kind"] == "coin":
                p["credits"] += 10
                st["score"] += 15
                if "coin" in sounds:
                    sounds["coin"].play()
            elif item["kind"] == "chest":
                locked = [w for w in WEAPONS if w not in p["weapons"]]
                if locked:
                    new_w = random.choice(locked)
                    p["weapons"].append(new_w)
                    p["cur_weapon"] = new_w
                    add_text(item["x"], item["y"] - 14, f"ИНСТРУМЕНТ: {WEAPONS[new_w]['name']}!", (255, 220, 60))
                else:
                    p["credits"] += 50
                    add_text(item["x"], item["y"] - 14, "+50 КРЕДИТОВ!", (255, 220, 60))
                if "buy" in sounds:
                    sounds["buy"].play()
                add_part(item["x"], item["y"], (255, 220, 60), 16, 130)
