import json
import math
import os
import random
import pygame

from config import BIOMES, FPS, HEIGHT, TILE, UPGRADES, WEAPONS, WIDTH
from entities import update_player, update_world_entities
from level_gen import generate_sector
from proc_gen import build_biome_assets, init_audio
from touch_ui import TouchController

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

    weather = [
        {"x": random.uniform(0, WIDTH), "y": random.uniform(0, HEIGHT), "spd": random.uniform(140, 260)}
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


class VirtualKeys:
    """Объединяет физическую клавиатуру и сенсорные кнопки для entities.py."""

    def __init__(self, kb_keys, touch):
        self.kb = kb_keys
        self.touch = touch

    def __getitem__(self, key):
        if self.kb[key]:
            return True
        if key in (pygame.K_a, pygame.K_LEFT) and self.touch.held["left"]:
            return True
        if key in (pygame.K_d, pygame.K_RIGHT) and self.touch.held["right"]:
            return True
        if key in (pygame.K_s, pygame.K_DOWN) and self.touch.held["down"]:
            return True
        return False


def main():
    pygame.init()
    # На планшете автоматически откроется на весь экран с масштабированием
    flags = pygame.SCALED | (pygame.FULLSCREEN if "ANDROID_ROOT" in os.environ else 0)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    pygame.display.set_caption("CYBER RUNNER // TOUCH")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 13, bold=True)
    big_font = pygame.font.SysFont("monospace", 22, bold=True)

    sounds = init_audio()
    saved = load_progress()
    st = create_new_state(saved["sector"] if saved else 1, saved)
    assets = build_biome_assets(st["biome_idx"])
    touch = TouchController()

    def add_part(x, y, col, count=8, spd=120.0):
        for _ in range(count):
            ang = random.uniform(0, 6.28318)
            v = random.uniform(spd * 0.25, spd)
            st["particles"].append(
                {"x": float(x), "y": float(y), "vx": math.cos(ang) * v, "vy": math.sin(ang) * v, "life": random.uniform(0.16, 0.38), "col": col}
            )

    def add_text(x, y, txt, col):
        st["texts"].append({"x": float(x), "y": float(y), "txt": txt, "col": col, "life": 0.9})

    def buy_upgrade(idx):
        p = st["player"]
        upg = UPGRADES[idx]
        uid = upg["id"]
        if not p["upgrades"].get(uid, False) and p["credits"] >= upg["cost"]:
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
            touch.handle_event(event)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if st["shop_open"]:
                        st["shop_open"] = False
                    else:
                        running = False
                elif st["game_over"] and event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                    st = create_new_state(1, None)
                    assets = build_biome_assets(st["biome_idx"])
                elif st["shop_open"]:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        st["shop_cursor"] = (st["shop_cursor"] - 1) % len(UPGRADES)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        st["shop_cursor"] = (st["shop_cursor"] + 1) % len(UPGRADES)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                        buy_upgrade(st["shop_cursor"])
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
                    elif event.key == pygame.K_f:
                        if any(math.hypot(p["x"] - t["x"], p["y"] - t["y"]) < 40 for t in lvl["terminals"]):
                            st["shop_open"] = True

        touch.update()
        taps = touch.consume_taps()

        near_terminal = any(math.hypot(p["x"] - t["x"], p["y"] - t["y"]) < 42 for t in lvl["terminals"])

        # Обработка касаний в меню проигрыша и магазине апгрейдов
        if st["game_over"] and taps:
            st = create_new_state(1, None)
            assets = build_biome_assets(st["biome_idx"])
        elif st["shop_open"]:
            close_rect = pygame.Rect(WIDTH // 2 - 70, HEIGHT - 46, 140, 30)
            for tx_p, ty_p in taps:
                if close_rect.collidepoint(tx_p, ty_p):
                    st["shop_open"] = False
                for idx in range(len(UPGRADES)):
                    row_rect = pygame.Rect(130, 88 + idx * 34, 380, 28)
                    if row_rect.collidepoint(tx_p, ty_p):
                        st["shop_cursor"] = idx
                        buy_upgrade(idx)
        else:
            if touch.just_pressed["jump"]:
                jump_pressed = True
            if touch.just_pressed["dash"]:
                dash_pressed = True
            if touch.just_pressed["hook"]:
                hook_pressed = True
            if touch.just_pressed["down"]:
                slam_pressed = True
            if touch.just_pressed["wep"]:
                idx = (p["weapons"].index(p["cur_weapon"]) + 1) % len(p["weapons"])
                p["cur_weapon"] = p["weapons"][idx]
            if touch.just_pressed["shop"] and near_terminal:
                st["shop_open"] = True
        if not st["game_over"] and not st["shop_open"]:
            if st["hitstop"] > 0:
                st["hitstop"] -= dt
            else:
                kb_keys = pygame.key.get_pressed()
                vkeys = VirtualKeys(kb_keys, touch)
                update_player(st, vkeys, jump_pressed, dash_pressed, hook_pressed, slam_pressed, dt, sounds, add_part, add_text)
                update_world_entities(st, dt, sounds, add_part, add_text)

                if (kb_keys[pygame.K_z] or kb_keys[pygame.K_j] or kb_keys[pygame.K_RETURN] or touch.held["fire"]) and p["shoot_cd"] <= 0:
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

                if lvl["portal"]:
                    px_p, py_p = lvl["portal"]
                    if math.hypot(p["x"] + 8 - px_p, p["y"] + 12 - py_p) < 28:
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
        cam_x = int(max(0, min(lvl["w"] * TILE - WIDTH, p["x"] - WIDTH // 2 + ox)))
        cam_y = int(max(0, min(lvl["h"] * TILE - HEIGHT, p["y"] - HEIGHT // 2 + oy)))

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
            if near_terminal:
                hint = font.render("ТЕРМИНАЛ [MOD]", True, (0, 255, 200))
                screen.blit(hint, (tsx - hint.get_width() // 2, tsy - 32))

        for item in lvl["pickups"]:
            ix, iy = int(item["x"] - cam_x), int(item["y"] - cam_y)
            if item["kind"] == "coin":
                pygame.draw.circle(screen, (255, 220, 50), (ix, iy), 4)
            else:
                pygame.draw.rect(screen, (255, 190, 40), (ix - 8, iy - 6, 16, 12), 2)

        if lvl["portal"]:
            port_x, port_y = lvl["portal"]
            ptx, pty = int(port_x - cam_x), int(port_y - cam_y)
            pygame.draw.circle(screen, (0, 255, 170), (ptx, pty), 16, 2)

        if p["hook"]:
            hook_x, hook_y = p["hook"]
            pygame.draw.line(screen, (0, 255, 220), (int(p["x"] + 8 - cam_x), int(p["y"] + 12 - cam_y)), (int(hook_x - cam_x), int(hook_y - cam_y)), 2)

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
        screen.blit(font.render(f"КР:{p['credits']} | {w_name}", True, (255, 220, 80)), (16, 43))

        rx0, ry0 = WIDTH - 118, 8
        pygame.draw.rect(screen, (10, 14, 22), (rx0, ry0, 110, 32))
        pygame.draw.rect(screen, (0, 190, 210), (rx0, ry0, 110, 32), 1)
        px_r = rx0 + int((p["x"] / (lvl["w"] * TILE)) * 106)
        py_r = ry0 + int((p["y"] / (lvl["h"] * TILE)) * 28)
        pygame.draw.circle(screen, (0, 255, 200), (px_r, py_r), 2)
        if lvl["portal"]:
            port_x, port_y = lvl["portal"]
            bx_r = rx0 + int((port_x / (lvl["w"] * TILE)) * 106)
            by_r = ry0 + int((port_y / (lvl["h"] * TILE)) * 28)
            pygame.draw.circle(screen, (0, 255, 140), (bx_r, by_r), 3)

        if not st["shop_open"] and not st["game_over"]:
            touch.draw(screen, font, near_terminal)

        if st["shop_open"]:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((8, 12, 20, 220))
            screen.blit(ov, (0, 0))
            title = big_font.render("ТЕРМИНАЛ МОДУЛЕЙ (НАЖМИТЕ ДЛЯ ПОКУПКИ)", True, (0, 255, 210))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 36))
            for idx, upg in enumerate(UPGRADES):
                y_pos = 92 + idx * 34
                sel = idx == st["shop_cursor"]
                owned = p["upgrades"].get(upg["id"], False)
                col = (0, 255, 180) if sel else (160, 200, 220)
                status = "[УСТАНОВЛЕНО]" if owned else f"[{upg['cost']} КР]"
                line = font.render(f"{'> ' if sel else '  '}{upg['name']}  {status}", True, col)
                screen.blit(line, (140, y_pos))

            close_rect = pygame.Rect(WIDTH // 2 - 70, HEIGHT - 46, 140, 30)
            pygame.draw.rect(screen, (255, 60, 90), close_rect, 2, border_radius=6)
            cl_txt = font.render("[ ЗАКРЫТЬ ]", True, (255, 120, 140))
            screen.blit(cl_txt, (close_rect.centerx - cl_txt.get_width() // 2, close_rect.centery - cl_txt.get_height() // 2))

        if st["game_over"]:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((18, 6, 12, 200))
            screen.blit(ov, (0, 0))
            t1 = big_font.render("СИСТЕМА ОТКЛЮЧЕНА", True, (255, 60, 85))
            t2 = font.render(f"СЕКТОР: {st['sector']} | СЧЕТ: {st['score']} | НАЖМИТЕ НА ЭКРАН", True, (220, 240, 255))
            screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 25))
            screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 12))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
