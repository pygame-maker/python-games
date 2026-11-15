import json
import math
import os
import random
import pygame

from config import BIOMES, FPS, HEIGHT, TILE, UPGRADES, WEAPONS, WIDTH
from entities import update_player, update_world_entities
from level_gen import generate_sector
from proc_gen import build_biome_assets, init_audio

SAVE_PATH = "cyber_platformer_save.json"


def create_new_state(sector=1, saved_player=None):
    lvl_data = generate_sector(sector)
    sx, sy = lvl_data["spawn"]
    player = {
        "x": float(sx),
        "y": float(sy),
        "vx": 0.0,
        "vy": 0.0,
        "facing": 1,
        "on_ground": False,
        "wall_slide": 0,
        "coyote": 0.0,
        "jump_buf": 0.0,
        "max_jumps": 1,
        "jumps_left": 1,
        "dash_cd": 0.0,
        "dash_timer": 0.0,
        "invuln": 0.0,
        "slamming": False,
        "hook": None,
        "hp": 100,
        "max_hp": 100,
        "credits": 0,
        "weapons": ["blaster"],
        "cur_weapon": "blaster",
        "shoot_cd": 0.0,
        "anim_t": 0.0,
        "anim_frame": 0,
        "upgrades": {
            "double_jump": False,
            "dash_dmg": False,
            "vampire": False,
            "magnet": False,
            "crit": False,
        },
    }

    if saved_player:
        player["max_hp"] = saved_player["max_hp"]
        player["hp"] = saved_player["max_hp"]
        player["credits"] = saved_player["credits"]
        player["weapons"] = list(saved_player["weapons"])
        player["cur_weapon"] = saved_player["cur_weapon"]
        player["upgrades"].update(saved_player["upgrades"])
        player["max_jumps"] = 2 if player["upgrades"]["double_jump"] else 1

    # Погодные частицы экрана
    weather = [
        {
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(0, HEIGHT),
            "spd": random.uniform(140, 260),
        }
        for _ in range(45)
    ]

    return {
        "sector": sector,
        "biome_idx": (sector - 1) % len(BIOMES),
        "level_data": lvl_data,
        "player": player,
        "bullets": [],
        "particles": [],
        "afterimages": [],
        "texts": [],
        "weather": weather,
        "score": saved_player.get("score", 0) if saved_player else 0,
        "shake": 0.0,
        "hitstop": 0.0,
        "shop_open": False,
        "shop_cursor": 0,
        "game_over": False,
    }


def save_progress(st):
    p = st["player"]
    data = {
        "sector": st["sector"],
        "score": st["score"],
        "max_hp": p["max_hp"],
        "credits": p["credits"],
        "weapons": p["weapons"],
        "cur_weapon": p["cur_weapon"],
        "upgrades": p["upgrades"],
    }
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def load_progress():
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    pygame.display.set_caption("CYBER RUNNER 100 // PLATFORMER")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 13, bold=True)
    big_font = pygame.font.SysFont("monospace", 24, bold=True)

    sounds = init_audio()
    saved = load_progress()
    st = create_new_state(saved["sector"] if saved else 1, saved)
    assets = build_biome_assets(st["biome_idx"])

    def add_part(x, y, col, count=8, spd=120.0):
        for _ in range(count):
            ang = random.uniform(0, 6.28318)
            v = random.uniform(spd * 0.25, spd)
            st["particles"].append(
                {
                    "x": float(x),
                    "y": float(y),
                    "vx": math.cos(ang) * v,
                    "vy": math.sin(ang) * v,
                    "life": random.uniform(0.16, 0.38),
                    "col": col,
                }
            )

    def add_text(x, y, txt, col):
        st["texts"].append({"x": float(x), "y": float(y), "txt": txt, "col": col, "life": 0.9})

    running = True
    while running:
        dt = min(0.05, clock.tick(FPS) / 1000.0)
        p = st["player"]
        lvl = st["level_data"]

        jump_pressed = False
        dash_pressed = False
        hook_pressed = False
        slam_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if st["shop_open"]:
                        st["shop_open"] = False
                    else:
                        running = False

                elif st["game_over"]:
                    if event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                        st = create_new_state(1, None)
                        assets = build_biome_assets(st["biome_idx"])

                elif st["shop_open"]:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        st["shop_cursor"] = (st["shop_cursor"] - 1) % len(UPGRADES)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        st["shop_cursor"] = (st["shop_cursor"] + 1) % len(UPGRADES)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                        upg = UPGRADES[st["shop_cursor"]]
                        uid = upg["id"]
                        already = p["upgrades"].get(uid, False)
                        if not already and p["credits"] >= upg["cost"]:
                            p["credits"] -= upg["cost"]
                            if uid == "max_hp":
                                p["max_hp"] += 25
                                p["hp"] = p["max_hp"]
                            else:
                                p["upgrades"][uid] = True
                                if uid == "double_jump":
                                    p["max_jumps"] = 2
                            if "buy" in sounds:
                                sounds["buy"].play()
                            add_text(p["x"], p["y"] - 16, f"УСТАНОВЛЕНО: {upg['name']}", (0, 255, 180))
                    elif event.key in (pygame.K_f, pygame.K_TAB):
                        st["shop_open"] = False

                else:
                    if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                        jump_pressed = True
                    elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_x):
                        dash_pressed = True
                    elif event.key in (pygame.K_e, pygame.K_c):
                        hook_pressed = True
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        slam_pressed = True
                    elif event.key == pygame.K_q:
                        idx = (p["weapons"].index(p["cur_weapon"]) + 1) % len(p["weapons"])
                        p["cur_weapon"] = p["weapons"][idx]
                    elif pygame.K_1 <= event.key <= pygame.K_4:
                        w_idx = event.key - pygame.K_1
                        if w_idx < len(p["weapons"]):
                            p["cur_weapon"] = p["weapons"][w_idx]
                    elif event.key == pygame.K_f:
                        # Взаимодействие с терминалом апгрейдов
                        for term in lvl["terminals"]:
                            if math.hypot(p["x"] - term["x"], p["y"] - term["y"]) < 36:
                                st["shop_open"] = True
                                break
        if not st["game_over"] and not st["shop_open"]:
            if st["hitstop"] > 0:
                st["hitstop"] -= dt
            else:
                keys = pygame.key.get_pressed()
                update_player(st, keys, jump_pressed, dash_pressed, hook_pressed, slam_pressed, dt, sounds, add_part, add_text)
                update_world_entities(st, dt, sounds, add_part, add_text)

                if (keys[pygame.K_z] or keys[pygame.K_j] or keys[pygame.K_RETURN]) and p["shoot_cd"] <= 0:
                    w_info = WEAPONS[p["cur_weapon"]]
                    p["shoot_cd"] = w_info["cd"]
                    base_ang = 0.0 if p["facing"] > 0 else math.pi
                    for _ in range(w_info["count"]):
                        ang = base_ang + random.uniform(-w_info["spread"], w_info["spread"])
                        st["bullets"].append(
                            {
                                "x": p["x"] + (16 if p["facing"] > 0 else 0),
                                "y": p["y"] + 11,
                                "vx": math.cos(ang) * w_info["spd"],
                                "vy": math.sin(ang) * w_info["spd"],
                                "dmg": w_info["dmg"],
                                "enemy": False,
                                "col": w_info["col"],
                            }
                        )
                    snd_key = "rail" if p["cur_weapon"] == "railgun" else "shoot"
                    if snd_key in sounds:
                        sounds[snd_key].play()

                grid = lvl["grid"]
                for b in st["bullets"][:]:
                    b["x"] += b["vx"] * dt
                    b["y"] += b["vy"] * dt
                    gx, gy = int(b["x"] // TILE), int(b["y"] // TILE)
                    if gx < 0 or gy < 0 or gx >= lvl["w"] or gy >= lvl["h"] or grid[gy][gx] in (1, 2):
                        if 0 <= gy < lvl["h"] and 0 <= gx < lvl["w"] and grid[gy][gx] == 2 and b["dmg"] >= 4:
                            grid[gy][gx] = 0
                            st["shake"] = 5.0
                            add_part(gx * TILE + 12, gy * TILE + 12, (230, 160, 60), 12, 130)
                        add_part(b["x"], b["y"], b["col"], 4, 65)
                        st["bullets"].remove(b)
                        continue

                    if b["enemy"]:
                        p_rect = pygame.Rect(int(p["x"]), int(p["y"]), 16, 24)
                        if p["invuln"] <= 0 and p_rect.collidepoint(int(b["x"]), int(b["y"])):
                            p["hp"] -= b["dmg"]
                            p["invuln"] = 0.65
                            st["shake"] = 5.0
                            if "hit" in sounds:
                                sounds["hit"].play()
                            add_text(p_rect.centerx, p_rect.top - 8, f"-{b['dmg']}", (255, 60, 80))
                            st["bullets"].remove(b)
                    else:
                        hit_any = False
                        for e in lvl["enemies"]:
                            e_rect = pygame.Rect(int(e["x"]), int(e["y"]), 24, 20)
                            if e_rect.collidepoint(int(b["x"]), int(b["y"])):
                                is_crit = p["upgrades"]["crit"] and random.random() < 0.25
                                dmg = int(b["dmg"] * (2.5 if is_crit else 1.0))
                                e["hp"] -= dmg
                                if is_crit:
                                    st["hitstop"] = 0.03
                                    add_text(e["x"], e["y"] - 10, f"{dmg} CRIT!", (255, 230, 60))
                                else:
                                    add_text(e["x"], e["y"] - 8, f"-{dmg}", b["col"])
                                add_part(b["x"], b["y"], b["col"], 5, 80)
                                hit_any = True
                                break

                        boss = lvl["boss"]
                        if not hit_any and boss and boss["alive"]:
                            b_rect = pygame.Rect(int(boss["x"]), int(boss["y"]), 56, 56)
                            if b_rect.collidepoint(int(b["x"]), int(b["y"])):
                                boss["hp"] -= b["dmg"]
                                add_part(b["x"], b["y"], b["col"], 6, 95)
                                hit_any = True

                        if hit_any and b in st["bullets"]:
                            st["bullets"].remove(b)

                if lvl["portal"]:
                    px_p, py_p = lvl["portal"]
                    if math.hypot(p["x"] + 8 - px_p, p["y"] + 12 - py_p) < 26:
                        st["sector"] += 1
                        save_progress(st)
                        st = create_new_state(st["sector"], load_progress())
                        assets = build_biome_assets(st["biome_idx"])
                        if "buy" in sounds:
                            sounds["buy"].play()

                if p["hp"] <= 0:
                    p["hp"] = 0
                    st["game_over"] = True

        if st["shake"] > 0:
            st["shake"] = max(0.0, st["shake"] - 28.0 * dt)

        for pt in st["particles"][:]:
            pt["x"] += pt["vx"] * dt
            pt["y"] += pt["vy"] * dt
            pt["life"] -= dt
            if pt["life"] <= 0:
                st["particles"].remove(pt)

        for af in st["afterimages"][:]:
            af["life"] -= dt
            if af["life"] <= 0:
                st["afterimages"].remove(af)

        for tx in st["texts"][:]:
            tx["y"] -= 24.0 * dt
            tx["life"] -= dt
            if tx["life"] <= 0:
                st["texts"].remove(tx)

        w_type = BIOMES[st["biome_idx"]]["weather"]
        for w_pt in st["weather"]:
            w_pt["y"] += w_pt["spd"] * dt * (0.4 if w_type in ("snow", "spores") else 1.2)
            w_pt["x"] -= (35.0 if w_type == "rain" else -15.0) * dt
            if w_pt["y"] > HEIGHT:
                w_pt["y"] = 0
                w_pt["x"] = random.uniform(0, WIDTH)
        ox = random.uniform(-st["shake"], st["shake"]) if st["shake"] > 0 else 0
        oy = random.uniform(-st["shake"], st["shake"]) if st["shake"] > 0 else 0
        max_cx = lvl["w"] * TILE - WIDTH
        max_cy = lvl["h"] * TILE - HEIGHT
        cam_x = int(max(0, min(max_cx, p["x"] - WIDTH // 2 + ox)))
        cam_y = int(max(0, min(max_cy, p["y"] - HEIGHT // 2 + oy)))

        screen.blit(assets["bg"], (0, 0))

        w_col = (80, 180, 255) if w_type == "rain" else ((120, 255, 110) if w_type == "spores" else ((220, 240, 255) if w_type == "snow" else (255, 130, 50)))
        for w_pt in st["weather"]:
            if w_type == "rain":
                pygame.draw.line(screen, w_col, (int(w_pt["x"]), int(w_pt["y"])), (int(w_pt["x"] - 2), int(w_pt["y"] + 7)), 1)
            else:
                pygame.draw.rect(screen, w_col, (int(w_pt["x"]), int(w_pt["y"]), 2, 2))

        tx0 = max(0, cam_x // TILE)
        tx1 = min(lvl["w"] - 1, (cam_x + WIDTH) // TILE + 1)
        ty0 = max(0, cam_y // TILE)
        ty1 = min(lvl["h"] - 1, (cam_y + HEIGHT) // TILE + 1)
        grid = lvl["grid"]
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                t = grid[ty][tx]
                if t == 1:
                    screen.blit(assets["tile"], (tx * TILE - cam_x, ty * TILE - cam_y))
                elif t == 2:
                    screen.blit(assets["cracked"], (tx * TILE - cam_x, ty * TILE - cam_y))
                elif t == 3:
                    screen.blit(assets["spike"], (tx * TILE - cam_x, ty * TILE - cam_y))
                elif t == 4:
                    screen.blit(assets["pad"], (tx * TILE - cam_x, ty * TILE - cam_y))

        for mp in lvl["moving_plats"]:
            pygame.draw.rect(screen, (0, 220, 255), (int(mp["x"] - cam_x), int(mp["y"] - cam_y), mp["w"], mp["h"]))

        for lsr in lvl["lasers"]:
            lx = int(lsr["x"] - cam_x)
            if lsr.get("active"):
                pygame.draw.line(screen, (255, 40, 80), (lx, int(lsr["y1"] - cam_y)), (lx, int(lsr["y2"] - cam_y)), 4)
            else:
                pygame.draw.line(screen, (80, 30, 40), (lx, int(lsr["y1"] - cam_y)), (lx, int(lsr["y2"] - cam_y)), 1)

        for term in lvl["terminals"]:
            tsx, tsy = int(term["x"] - cam_x), int(term["y"] - cam_y)
            pygame.draw.rect(screen, (0, 210, 255), (tsx - 8, tsy - 16, 16, 16), 2)
            if math.hypot(p["x"] - term["x"], p["y"] - term["y"]) < 36:
                hint = font.render("[F] МОДУЛИ", True, (0, 255, 200))
                screen.blit(hint, (tsx - hint.get_width() // 2, tsy - 32))

        for item in lvl["pickups"]:
            ix, iy = int(item["x"] - cam_x), int(item["y"] - cam_y)
            if item["kind"] == "coin":
                pygame.draw.circle(screen, (255, 220, 50), (ix, iy), 4)
            else:
                pygame.draw.rect(screen, (255, 190, 40), (ix - 8, iy - 6, 16, 12), 2)

        if lvl["portal"]:
            ptx, pty = int(lvl["portal"][0] - cam_x), int(lvl["portal"][1] - cam_y)
            pygame.draw.circle(screen, (0, 255, 170), (ptx, pty), 16, 2)

        if p["hook"]:
            pygame.draw.line(screen, (0, 255, 220), (int(p["x"] + 8 - cam_x), int(p["y"] + 12 - cam_y)), (int(p["hook"][0] - cam_x), int(p["hook"][1] - cam_y)), 2)

        for af in st["afterimages"]:
            spr = assets["player"][0]
            if af["facing"] < 0:
                spr = pygame.transform.flip(spr, True, False)
            spr_copy = spr.copy()
            spr_copy.set_alpha(90)
            screen.blit(spr_copy, (int(af["x"] - 2 - cam_x), int(af["y"] - 4 - cam_y)))

        if p["invuln"] <= 0 or int(p["invuln"] * 20) % 2 == 0:
            spr = assets["player"][p["anim_frame"]]
            if p["facing"] < 0:
                spr = pygame.transform.flip(spr, True, False)
            screen.blit(spr, (int(p["x"] - 2 - cam_x), int(p["y"] - 4 - cam_y)))

        for e in lvl["enemies"]:
            espr = assets["spider"] if e["type"] == "spider" else assets["flyer"]
            screen.blit(espr, (int(e["x"] - cam_x), int(e["y"] - cam_y)))

        boss = lvl["boss"]
        if boss and boss["alive"]:
            bsx, bsy = int(boss["x"] - cam_x), int(boss["y"] - cam_y)
            screen.blit(assets["boss"], (bsx, bsy))
            pygame.draw.rect(screen, (50, 15, 20), (bsx, bsy - 10, 56, 5))
            pygame.draw.rect(screen, (255, 60, 80), (bsx, bsy - 10, int(56 * (boss["hp"] / boss["max_hp"])), 5))

        for b in st["bullets"]:
            pygame.draw.circle(screen, b["col"], (int(b["x"] - cam_x), int(b["y"] - cam_y)), 3)

        for pt in st["particles"]:
            pygame.draw.rect(screen, pt["col"], (int(pt["x"] - cam_x), int(pt["y"] - cam_y), 2, 2))

        for tx in st["texts"]:
            lbl = font.render(tx["txt"], True, tx["col"])
            screen.blit(lbl, (int(tx["x"] - cam_x - lbl.get_width() // 2), int(tx["y"] - cam_y)))

        pygame.draw.rect(screen, (10, 14, 22), (8, 8, 250, 54))
        pygame.draw.rect(screen, (0, 190, 210), (8, 8, 250, 54), 1)
        hp_w = int(230 * (p["hp"] / p["max_hp"]))
        pygame.draw.rect(screen, (45, 18, 24), (16, 15, 230, 9))
        pygame.draw.rect(screen, (0, 255, 170), (16, 15, hp_w, 9))

        w_name = WEAPONS[p["cur_weapon"]]["name"]
        screen.blit(font.render(f"СЕКТОР {st['sector']}: {BIOMES[st['biome_idx']]['name']}", True, (180, 240, 255)), (16, 28))
        screen.blit(font.render(f"КР:{p['credits']} | {w_name} [Q]", True, (255, 220, 80)), (16, 43))

        rx0, ry0 = WIDTH - 118, 8
        pygame.draw.rect(screen, (10, 14, 22), (rx0, ry0, 110, 32))
        pygame.draw.rect(screen, (0, 190, 210), (rx0, ry0, 110, 32), 1)
        px_r = rx0 + int((p["x"] / (lvl["w"] * TILE)) * 106)
        py_r = ry0 + int((p["y"] / (lvl["h"] * TILE)) * 28)
        pygame.draw.circle(screen, (0, 255, 200), (px_r, py_r), 2)
        if boss and boss["alive"]:
            bx_r = rx0 + int((boss["x"] / (lvl["w"] * TILE)) * 106)
            by_r = ry0 + int((boss["y"] / (lvl["h"] * TILE)) * 28)
            pygame.draw.circle(screen, (255, 60, 80), (bx_r, by_r), 3)

        if st["shop_open"]:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((8, 12, 20, 210))
            screen.blit(ov, (0, 0))
            title = big_font.render("ТЕРМИНАЛ КИБЕР-МОДУЛЕЙ [W/S, ENTER, F-ВЫХОД]", True, (0, 255, 210))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 42))
            for idx, upg in enumerate(UPGRADES):
                y_pos = 95 + idx * 34
                sel = idx == st["shop_cursor"]
                owned = p["upgrades"].get(upg["id"], False)
                col = (0, 255, 180) if sel else (160, 200, 220)
                status = "[УСТАНОВЛЕНО]" if owned else f"[{upg['cost']} КР]"
                line = font.render(f"{'> ' if sel else '  '}{upg['name']}  {status}", True, col)
                screen.blit(line, (150, y_pos))

        if st["game_over"]:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((18, 6, 12, 200))
            screen.blit(ov, (0, 0))
            t1 = big_font.render("СИСТЕМА ОТКЛЮЧЕНА", True, (255, 60, 85))
            t2 = font.render(f"СЕКТОР: {st['sector']} | СЧЕТ: {st['score']} | [SPACE / R] - ЗАНОВО", True, (220, 240, 255))
            screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 25))
            screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 12))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
