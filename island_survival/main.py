import os
import pickle
import pygame
import numpy as np

from config import SCREEN_W, SCREEN_H, WORLD_W, WORLD_H, GRID_SIZE, FPS, SAVE_FILE
from audio import generate_procedural_sounds
from world_gen import generate_island_data, create_sprites, create_light_mask
from entities import add_text, update_farms_and_bushes, update_enemies_and_boss
from ui import draw_hud

def init_world():
    seed = np.random.randint(0, 1000)
    tex_array, height_map = generate_island_data(WORLD_W, WORLD_H, seed)

    resources = []
    for _ in range(430):
        rx = np.random.randint(60, WORLD_W - 60)
        ry = np.random.randint(60, WORLD_H - 60)
        elev = height_map[rx, ry]
        if np.hypot(rx - WORLD_W // 2, ry - WORLD_H // 2) < 140:
            continue
        if 0.45 < elev < 0.66:
            if np.random.rand() < 0.78:
                resources.append({"type": "tree", "pos": [rx, ry], "hp": 4, "var": rx % 5})
            else:
                resources.append({"type": "bush", "pos": [rx, ry], "berries": True, "regrow": 0.0})
        elif 0.66 <= elev < 0.88:
            resources.append({"type": "rock", "pos": [rx, ry], "hp": 5, "var": ry % 5})

    return {
        "seed": seed,
        "tex_array": tex_array,
        "height_map": height_map,
        "resources": resources,
        "buildings": {},
        "enemies": [],
        "boss": {
            "pos": [WORLD_W // 2, WORLD_H // 2 - 120],
            "home": [WORLD_W // 2, WORLD_H // 2 - 120],
            "hp": 120,
            "max_hp": 120,
            "alive": True,
            "atk_cd": 0.0,
            "slam_timer": 0.0,
        },
        "player_pos": [WORLD_W // 2, WORLD_H // 2 + 180],
        "inv": {"wood": 15, "stone": 6, "food": 3, "seeds": 2, "boss_heart": 0},
        "gear": {"axe": False, "spear": False, "fire_sword": False, "torch_fuel": 0.0},
        "health": 100.0,
        "warmth": 100.0,
        "hunger": 100.0,
        "selected_slot": 0,
        "time_of_day": 0.25,
        "day_count": 1,
        "swing_timer": 0,
        "fish_cooldown": 0.0,
        "floating_texts": [],
        "game_over": False,
    }

def build_surfaces(state):
    island_surf = pygame.surfarray.make_surface(state["tex_array"])
    minimap_surf = pygame.transform.smoothscale(island_surf, (150, 150))
    sprites = create_sprites(state["seed"])
    return island_surf, minimap_surf, sprites

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Процедурный Остров: Выживание")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 15, bold=True)
    big_font = pygame.font.SysFont("Arial", 32, bold=True)

    sounds = generate_procedural_sounds()
    campfire_light = create_light_mask(185)
    torch_light = create_light_mask(135)
    player_light = create_light_mask(65)

    state = init_world()
    island_surf, minimap_surf, sprites = build_surfaces(state)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        px_world, py_world = state["player_pos"]

        near_bench = any(
            b["type"] == "bench" and np.hypot(px_world - (bx * GRID_SIZE + 16), py_world - (by * GRID_SIZE + 16)) < 65
            for (bx, by), b in state["buildings"].items()
        )
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # Сохранение (F5) и Загрузка (F9)
                if event.key == pygame.K_F5 and not state["game_over"]:
                    with open(SAVE_FILE, "wb") as f:
                        pickle.dump(state, f)
                    sounds["build"].play()
                    add_text(state, "ИГРА СОХРАНЕНА!", state["player_pos"], (100, 255, 180))
                elif event.key == pygame.K_F9 and os.path.exists(SAVE_FILE):
                    with open(SAVE_FILE, "rb") as f:
                        state = pickle.load(f)
                    island_surf, minimap_surf, sprites = build_surfaces(state)
                    sounds["build"].play()
                    add_text(state, "МИР ЗАГРУЖЕН!", state["player_pos"], (100, 220, 255))

                if state["game_over"] and event.key == pygame.K_r:
                    state = init_world()
                    island_surf, minimap_surf, sprites = build_surfaces(state)

                elif not state["game_over"]:
                    # Выбор слота 1-7
                    if pygame.K_1 <= event.key <= pygame.K_7:
                        state["selected_slot"] = event.key - pygame.K_1

                    # Крафт на верстаке (Z, X, C, V)
                    if near_bench:
                        if event.key == pygame.K_z and not state["gear"]["axe"] and state["inv"]["wood"] >= 4 and state["inv"]["stone"] >= 3:
                            state["inv"]["wood"] -= 4; state["inv"]["stone"] -= 3
                            state["gear"]["axe"] = True
                            sounds["build"].play()
                            add_text(state, "Скрафчен Каменный Топор!", state["player_pos"], (255, 230, 100))
                        elif event.key == pygame.K_x and not state["gear"]["spear"] and state["inv"]["wood"] >= 5 and state["inv"]["stone"] >= 2:
                            state["inv"]["wood"] -= 5; state["inv"]["stone"] -= 2
                            state["gear"]["spear"] = True
                            sounds["build"].play()
                            add_text(state, "Скрафчено Копье!", state["player_pos"], (255, 230, 100))
                        elif event.key == pygame.K_c and state["inv"]["wood"] >= 3:
                            state["inv"]["wood"] -= 3
                            state["gear"]["torch_fuel"] = 100.0
                            sounds["build"].play()
                            add_text(state, "Зажжен Ручной Факел!", state["player_pos"], (255, 180, 80))
                        elif event.key == pygame.K_v and not state["gear"]["fire_sword"] and state["inv"]["wood"] >= 10 and state["inv"]["stone"] >= 10 and state["inv"]["boss_heart"] >= 1:
                            state["inv"]["wood"] -= 10; state["inv"]["stone"] -= 10; state["inv"]["boss_heart"] -= 1
                            state["gear"]["fire_sword"] = True
                            sounds["pickup"].play()
                            add_text(state, "СОЗДАН ОГНЕННЫЙ МЕЧ!", state["player_pos"], (255, 120, 40))

                    # Поесть (E)
                    if event.key == pygame.K_e and state["inv"]["food"] > 0 and state["hunger"] < 98:
                        state["inv"]["food"] -= 1
                        state["hunger"] = min(100.0, state["hunger"] + 30.0)
                        state["health"] = min(100.0, state["health"] + 12.0)
                        sounds["pickup"].play()
                        add_text(state, "+30 Сытость", state["player_pos"], (120, 255, 120))

                    # Рыбалка (F)
                    if event.key == pygame.K_f and state["fish_cooldown"] <= 0:
                        near_water = any(
                            state["height_map"][int(np.clip(px_world + ox, 0, WORLD_W - 1)), int(np.clip(py_world + oy, 0, WORLD_H - 1))] < 0.36
                            for ox in [-25, 0, 25] for oy in [-25, 0, 25]
                        )
                        if near_water:
                            state["fish_cooldown"] = 2.5
                            if np.random.rand() < 0.75:
                                state["inv"]["food"] += 1
                                sounds["pickup"].play()
                                add_text(state, "+1 Рыба!", state["player_pos"], (100, 220, 255))
                            else:
                                add_text(state, "Сорвалась...", state["player_pos"], (200, 200, 200))
                        else:
                            add_text(state, "Подойдите к воде!", state["player_pos"], (255, 150, 100))
                        # Клики мыши
            if event.type == pygame.MOUSEBUTTONDOWN and not state["game_over"]:
                cam_x = int(np.clip(px_world - SCREEN_W // 2, 0, WORLD_W - SCREEN_W))
                cam_y = int(np.clip(py_world - SCREEN_H // 2, 0, WORLD_H - SCREEN_H))
                mx, my = pygame.mouse.get_pos()
                world_mx, world_my = mx + cam_x, my + cam_y
                gx, gy = world_mx // GRID_SIZE, world_my // GRID_SIZE
                dist_mouse = np.hypot(px_world - world_mx, py_world - world_my)

                # Сундук
                if dist_mouse < 80 and (gx, gy) in state["buildings"] and state["buildings"][(gx, gy)]["type"] == "chest":
                    chest_inv = state["buildings"][(gx, gy)]["items"]
                    if event.button == 1:
                        if state["inv"]["wood"] >= 5:
                            state["inv"]["wood"] -= 5; chest_inv["wood"] += 5
                            sounds["build"].play()
                            add_text(state, "В сундук: +5 Дерева", (world_mx, world_my), (230, 200, 100))
                        elif state["inv"]["stone"] >= 5:
                            state["inv"]["stone"] -= 5; chest_inv["stone"] += 5
                            sounds["build"].play()
                            add_text(state, "В сундук: +5 Камня", (world_mx, world_my), (200, 200, 210))
                    elif event.button == 3 and (chest_inv["wood"] > 0 or chest_inv["stone"] > 0):
                        state["inv"]["wood"] += chest_inv["wood"]
                        state["inv"]["stone"] += chest_inv["stone"]
                        add_text(state, f"Взято: {chest_inv['wood']}д, {chest_inv['stone']}к", (world_mx, world_my), (120, 255, 150))
                        chest_inv["wood"] = 0; chest_inv["stone"] = 0
                        sounds["pickup"].play()

                elif event.button == 1:
                    if state["selected_slot"] == 0:
                        state["swing_timer"] = 8
                        hit = False
                        atk_range = 72 if (state["gear"]["spear"] or state["gear"]["fire_sword"]) else 50
                        atk_dmg = 6 if state["gear"]["fire_sword"] else (2 if state["gear"]["spear"] else 1)

                        # 1. Атака Босса (Каменного Голема)
                        boss = state.get("boss")
                        if boss and boss["alive"]:
                            bx_w, by_w = boss["pos"]
                            if np.hypot(px_world - bx_w, py_world - by_w) < atk_range + 18:
                                boss["hp"] -= atk_dmg
                                sounds["mine"].play()
                                add_text(state, f"-{atk_dmg} HP Голему!", boss["pos"], (255, 150, 50))
                                if boss["hp"] <= 0:
                                    boss["alive"] = False
                                    state["inv"]["stone"] += 25
                                    state["inv"]["boss_heart"] += 1
                                    sounds["pickup"].play()
                                    add_text(state, "ГОЛЕМ ПОВЕРЖЕН! +Сердце Голема", state["player_pos"], (255, 220, 50))
                                hit = True

                        # 2. Атака ночных теней
                        if not hit:
                            for enemy in state["enemies"][:]:
                                ex_w, ey_w = enemy["pos"]
                                if np.hypot(px_world - ex_w, py_world - ey_w) < atk_range:
                                    enemy["hp"] -= atk_dmg
                                    ang = np.arctan2(ey_w - py_world, ex_w - px_world)
                                    enemy["pos"] = [ex_w + np.cos(ang) * 30, ey_w + np.sin(ang) * 30]
                                    sounds["hit"].play()
                                    add_text(state, f"-{atk_dmg} HP", enemy["pos"], (255, 90, 90))
                                    if enemy["hp"] <= 0:
                                        state["enemies"].remove(enemy)
                                        state["inv"]["food"] += 1
                                        add_text(state, "+1 Мясо", state["player_pos"], (255, 180, 100))
                                    hit = True
                                    break

                        # 3. Сбор урожая с грядки или подкидывание дров в костер
                        if not hit and (gx, gy) in state["buildings"]:
                            b = state["buildings"][(gx, gy)]
                            if b["type"] == "fire" and state["inv"]["wood"] >= 1:
                                state["inv"]["wood"] -= 1
                                b["fuel"] = min(100.0, b["fuel"] + 45.0)
                                sounds["build"].play()
                                add_text(state, "+Огонь", (world_mx, world_my), (255, 200, 80))
                                hit = True
                            elif b["type"] == "farm" and b["stage"] == 2:
                                b["stage"] = 0
                                b["growth"] = 0.0
                                state["inv"]["food"] += 3
                                state["inv"]["seeds"] += 1
                                sounds["pickup"].play()
                                add_text(state, "+3 Урожай, +1 Семена!", (world_mx, world_my), (255, 220, 80))
                                hit = True

                        # 4. Добыча деревьев, камней и кустов
                        if not hit:
                            gather_dmg = 2 if state["gear"]["axe"] else 1
                            for res in state["resources"][:]:
                                rx, ry = res["pos"]
                                if np.hypot(px_world - rx, py_world - ry) < 46:
                                    if res["type"] == "bush":
                                        if res["berries"]:
                                            res["berries"] = False
                                            res["regrow"] = 35.0
                                            state["inv"]["food"] += 1
                                            if np.random.rand() < 0.65:
                                                state["inv"]["seeds"] += 1
                                                add_text(state, "+1 Ягода, +1 Семена", res["pos"], (255, 130, 150))
                                            else:
                                                add_text(state, "+1 Ягода", res["pos"], (255, 100, 130))
                                            sounds["pickup"].play()
                                        break
                                    else:
                                        res["hp"] -= gather_dmg
                                        if res["type"] == "tree":
                                            sounds["chop"].play()
                                        else:
                                            sounds["mine"].play()
                                        if res["hp"] <= 0:
                                            if res["type"] == "tree":
                                                state["inv"]["wood"] += 3
                                                if np.random.rand() < 0.35:
                                                    state["inv"]["seeds"] += 1
                                                add_text(state, "+3 Дерево", res["pos"], (200, 160, 100))
                                            else:
                                                state["inv"]["stone"] += 2
                                                add_text(state, "+2 Камень", res["pos"], (180, 180, 190))
                                            state["resources"].remove(res)
                                        break

                    # Строительство (слоты 1-6 -> клавиши 2-7)
                    elif dist_mouse < 120 and (gx, gy) not in state["buildings"]:
                        slot = state["selected_slot"]
                        if slot == 1 and state["inv"]["wood"] >= 2:
                            state["inv"]["wood"] -= 2
                            state["buildings"][(gx, gy)] = {"type": "floor"}
                            sounds["build"].play()
                        elif slot == 2 and state["inv"]["wood"] >= 4:
                            state["inv"]["wood"] -= 4
                            state["buildings"][(gx, gy)] = {"type": "wall"}
                            sounds["build"].play()
                        elif slot == 3 and state["inv"]["wood"] >= 5 and state["inv"]["stone"] >= 3:
                            state["inv"]["wood"] -= 5; state["inv"]["stone"] -= 3
                            state["buildings"][(gx, gy)] = {"type": "fire", "fuel": 100.0}
                            sounds["build"].play()
                        elif slot == 4 and state["inv"]["wood"] >= 6 and state["inv"]["stone"] >= 4:
                            state["inv"]["wood"] -= 6; state["inv"]["stone"] -= 4
                            state["buildings"][(gx, gy)] = {"type": "bench"}
                            sounds["build"].play()
                        elif slot == 5 and state["inv"]["wood"] >= 8:
                            state["inv"]["wood"] -= 8
                            state["buildings"][(gx, gy)] = {"type": "chest", "items": {"wood": 0, "stone": 0}}
                            sounds["build"].play()
                        elif slot == 6 and state["inv"]["wood"] >= 3 and state["inv"]["seeds"] >= 1:
                            state["inv"]["wood"] -= 3; state["inv"]["seeds"] -= 1
                            state["buildings"][(gx, gy)] = {"type": "farm", "stage": 0, "growth": 0.0}
                            sounds["build"].play()

                        # --- ОБНОВЛЕНИЕ ЛОГИКИ ---
        if not state["game_over"]:
            old_time = state["time_of_day"]
            # Весь цикл суток = 900 секунд (10 мин день + 5 мин ночь)
            state["time_of_day"] = (state["time_of_day"] + dt / 900.0) % 1.0
            if state["time_of_day"] < old_time:
                state["day_count"] += 1

            # От 0.0 до 0.667 (600 сек / 10 мин) — день
            # От 0.667 до 1.0 (300 сек / 5 мин) — ночь
            t = state["time_of_day"]
            if t < 0.667:
                is_night = False
                darkness = 0
                # Плавные сумерки в последнюю минуту дня (от 0.60 до 0.667)
                if t > 0.60:
                    darkness = int(((t - 0.60) / 0.067) * 140)
            else:
                is_night = True
                # Плавный рассвет в последнюю минуту ночи (от 0.933 до 1.0)
                if t > 0.933:
                    darkness = int(228 - ((t - 0.933) / 0.067) * 228)
                else:
                    # Нарастание густой темноты в начале ночи
                    darkness = int(min(228, 140 + ((t - 0.667) / 0.05) * 88))

            if state["fish_cooldown"] > 0:
                state["fish_cooldown"] -= dt

            has_torch = state["gear"]["torch_fuel"] > 0 or state["gear"]["fire_sword"]
            if state["gear"]["torch_fuel"] > 0 and is_night:
                state["gear"]["torch_fuel"] = max(0.0, state["gear"]["torch_fuel"] - dt * 1.5)

            update_farms_and_bushes(state, dt)

            # Движение игрока
            keys = pygame.key.get_pressed()
            elev = state["height_map"][int(px_world), int(py_world)]
            speed = 1.5 if elev < 0.36 else 3.2
            dx = (keys[pygame.K_d] - keys[pygame.K_a]) * speed
            dy = (keys[pygame.K_s] - keys[pygame.K_w]) * speed

            for axis, delta in ((0, dx), (1, dy)):
                if delta != 0:
                    new_pos = list(state["player_pos"])
                    new_pos[axis] = np.clip(new_pos[axis] + delta, 12, WORLD_W - 12)
                    nx_p, ny_p = new_pos
                    pgx, pgy = int(nx_p) // GRID_SIZE, int(ny_p) // GRID_SIZE
                    if not ((pgx, pgy) in state["buildings"] and state["buildings"][(pgx, pgy)]["type"] == "wall"):
                        state["player_pos"] = new_pos

            px_world, py_world = state["player_pos"]

            # Костры и тепло
            near_fire = False
            active_fires = []
            for pos_key, b in list(state["buildings"].items()):
                if b["type"] == "fire":
                    b["fuel"] -= dt * 2.0
                    if b["fuel"] <= 0:
                        del state["buildings"][pos_key]
                    else:
                        kbx, kby = pos_key
                        fx, fy = kbx * GRID_SIZE + 16, kby * GRID_SIZE + 16
                        active_fires.append((fx, fy))
                        if np.hypot(px_world - fx, py_world - fy) < 135:
                            near_fire = True

            if near_fire or (has_torch and is_night):
                state["warmth"] = min(100.0, state["warmth"] + dt * 14.0)
            elif is_night:
                state["warmth"] = max(0.0, state["warmth"] - dt * 4.0)
            else:
                state["warmth"] = min(100.0, state["warmth"] + dt * 3.5)

            state["hunger"] = max(0.0, state["hunger"] - dt * 1.3)
            if state["warmth"] <= 0:
                state["health"] -= dt * 5.0
            if state["hunger"] <= 0:
                state["health"] -= dt * 3.5

            update_enemies_and_boss(state, dt, is_night, active_fires, sounds)

            if state["health"] <= 0:
                state["health"] = 0
                state["game_over"] = True
        else:
            darkness = 160
            is_night = True
            has_torch = False

        # --- ОТРИСОВКА ---
        cam_x = int(np.clip(px_world - SCREEN_W // 2, 0, WORLD_W - SCREEN_W))
        cam_y = int(np.clip(py_world - SCREEN_H // 2, 0, WORLD_H - SCREEN_H))
        mx, my = pygame.mouse.get_pos()
        world_mx, world_my = mx + cam_x, my + cam_y
        gx, gy = world_mx // GRID_SIZE, world_my // GRID_SIZE

        screen.blit(island_surf, (0, 0), (cam_x, cam_y, SCREEN_W, SCREEN_H))

        # Постройки и грядки
        for (bx, by), b in state["buildings"].items():
            sx, sy = bx * GRID_SIZE - cam_x, by * GRID_SIZE - cam_y
            if -GRID_SIZE < sx < SCREEN_W and -GRID_SIZE < sy < SCREEN_H:
                btype = b["type"]
                if btype in sprites:
                    screen.blit(sprites[btype], (sx, sy))
                elif btype == "farm":
                    screen.blit(sprites[f"farm_{b['stage']}"], (sx, sy))
                elif btype == "fire":
                    pygame.draw.circle(screen, (90, 90, 90), (sx + 16, sy + 16), 10)
                    flicker = np.random.randint(-2, 3)
                    pygame.draw.circle(screen, (255, 120, 20), (sx + 16, sy + 16), 7 + flicker)
                    pygame.draw.circle(screen, (255, 230, 80), (sx + 16, sy + 16), 4)

        # Сетка строительства (слоты 1-6)
        if 1 <= state["selected_slot"] <= 6 and not state["game_over"]:
            gsx, gsy = gx * GRID_SIZE - cam_x, gy * GRID_SIZE - cam_y
            can_build = np.hypot(px_world - world_mx, py_world - world_my) < 120 and (gx, gy) not in state["buildings"]
            pygame.draw.rect(screen, (100, 255, 100) if can_build else (255, 100, 100), (gsx, gsy, GRID_SIZE, GRID_SIZE), 2)

        # Ресурсы
        for res in state["resources"]:
            rx, ry = res["pos"]
            sx, sy = rx - cam_x, ry - cam_y
            if -50 < sx < SCREEN_W + 50 and -50 < sy < SCREEN_H + 50:
                if res["type"] == "rock":
                    screen.blit(sprites["rocks"][res["var"]], (sx - 16, sy - 16))
                elif res["type"] == "bush":
                    screen.blit(sprites["bush_full"] if res["berries"] else sprites["bush_empty"], (sx - 13, sy - 13))
                elif res["type"] == "tree":
                    pygame.draw.circle(screen, (25, 60, 25), (sx + 4, sy + 4), 14)

        # Босс (Древний Каменный Голем)
        boss = state.get("boss")
        if boss and boss["alive"]:
            bx_w, by_w = boss["pos"]
            bx, by = int(bx_w - cam_x), int(by_w - cam_y)
            screen.blit(sprites["boss"], (bx - 32, by - 32))
            if boss["slam_timer"] > 0:
                pygame.draw.circle(screen, (255, 100, 30), (bx, by), 48, 3)

        # Игрок
        px, py = int(px_world - cam_x), int(py_world - cam_y)
        pygame.draw.circle(screen, (220, 70, 50), (px, py), 8)
        pygame.draw.circle(screen, (255, 255, 255), (px, py), 8, 1)
        if state["gear"]["fire_sword"]:
            pygame.draw.circle(screen, (255, 100, 20), (px + 8, py - 4), 5)
        elif has_torch:
            pygame.draw.circle(screen, (255, 180, 40), (px + 7, py - 5), 4)
        if state["swing_timer"] > 0:
            rad = 55 if (state["gear"]["spear"] or state["gear"]["fire_sword"]) else 35
            col = (255, 140, 50) if state["gear"]["fire_sword"] else (255, 255, 200)
            pygame.draw.circle(screen, col, (px, py), rad, 2 if state["gear"]["fire_sword"] else 1)
            state["swing_timer"] -= 1

        # Кроны деревьев
        for res in state["resources"]:
            if res["type"] == "tree":
                rx, ry = res["pos"]
                sx, sy = rx - cam_x, ry - cam_y
                if -50 < sx < SCREEN_W + 50 and -50 < sy < SCREEN_H + 50:
                    screen.blit(sprites["trees"][res["var"]], (sx - 22, sy - 22))

        # Ночные тени
        for enemy in state["enemies"]:
            ex_w, ey_w = enemy["pos"]
            ex, ey = int(ex_w - cam_x), int(ey_w - cam_y)
            pygame.draw.circle(screen, (15, 10, 20), (ex, ey), 10)
            pygame.draw.circle(screen, (255, 40, 40), (ex - 3, ey - 2), 2)
            pygame.draw.circle(screen, (255, 40, 40), (ex + 3, ey - 2), 2)

        # Ночь и свет
        if darkness > 0:
            night_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            night_surf.fill((10, 15, 35, darkness))
            if has_torch:
                night_surf.blit(torch_light, (px - 135, py - 135), special_flags=pygame.BLEND_RGBA_SUB)
            else:
                night_surf.blit(player_light, (px - 65, py - 65), special_flags=pygame.BLEND_RGBA_SUB)
            for (bx, by), b in state["buildings"].items():
                if b["type"] == "fire":
                    fx, fy = bx * GRID_SIZE + 16 - cam_x, by * GRID_SIZE + 16 - cam_y
                    night_surf.blit(campfire_light, (fx - 185, fy - 185), special_flags=pygame.BLEND_RGBA_SUB)
            screen.blit(night_surf, (0, 0))

        # Всплывающий текст
        for ft in state["floating_texts"][:]:
            ftx, fty = ft["pos"]
            fty -= 20 * dt
            ft["pos"] = [ftx, fty]
            ft["timer"] -= dt
            if ft["timer"] <= 0:
                state["floating_texts"].remove(ft)
            else:
                screen.blit(font.render(ft["text"], True, ft["color"]), (ftx - cam_x - 20, fty - cam_y))

        draw_hud(screen, font, big_font, state, minimap_surf, is_night, near_bench)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

