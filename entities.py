import numpy as np
from config import WORLD_W, WORLD_H, GRID_SIZE

def add_text(state, text, pos, color=(255, 255, 255)):
    state["floating_texts"].append({"text": text, "pos": list(pos), "timer": 1.3, "color": color})

def update_farms_and_bushes(state, dt):
    """Обновляет рост ягод и урожая на грядках."""
    for res in state["resources"]:
        if res["type"] == "bush" and not res["berries"]:
            res["regrow"] -= dt
            if res["regrow"] <= 0:
                res["berries"] = True

    for b in state["buildings"].values():
        if b["type"] == "farm" and b["stage"] < 2:
            b["growth"] += dt
            if b["growth"] >= 20.0:
                b["stage"] += 1
                b["growth"] = 0.0

def update_enemies_and_boss(state, dt, is_night, active_fires, sounds):
    """ИИ ночных теней и Древнего Каменного Голема."""
    px, py = state["player_pos"]

    # 1. Ночные тени-волки
    if is_night and len(state["enemies"]) < 3 + state["day_count"] and np.random.rand() < 0.015:
        ang = np.random.uniform(0, np.pi * 2)
        ex = np.clip(px + np.cos(ang) * 430, 30, WORLD_W - 30)
        ey = np.clip(py + np.sin(ang) * 430, 30, WORLD_H - 30)
        if state["height_map"][int(ex), int(ey)] >= 0.36:
            state["enemies"].append({"pos": [ex, ey], "hp": 3, "atk_cd": 0.0})

    for enemy in state["enemies"][:]:
        if not is_night:
            state["enemies"].remove(enemy)
            continue
        if enemy["atk_cd"] > 0:
            enemy["atk_cd"] -= dt

        ex, ey = enemy["pos"]
        scared = False
        for fx, fy in active_fires:
            if np.hypot(ex - fx, ey - fy) < 145:
                scared = True
                ang = np.arctan2(ey - fy, ex - fx)
                enemy["pos"] = [ex + np.cos(ang) * 2.5, ey + np.sin(ang) * 2.5]
                break

        if not scared:
            dist_p = np.hypot(px - ex, py - ey)
            if dist_p > 16:
                ang = np.arctan2(py - ey, px - ex)
                nx = ex + np.cos(ang) * 2.1
                ny = ey + np.sin(ang) * 2.1
                egx, egy = int(nx) // GRID_SIZE, int(ny) // GRID_SIZE
                if not ((egx, egy) in state["buildings"] and state["buildings"][(egx, egy)]["type"] == "wall"):
                    enemy["pos"] = [nx, ny]
            elif enemy["atk_cd"] <= 0:
                state["health"] -= 12.0
                enemy["atk_cd"] = 1.2
                sounds["hit"].play()
                add_text(state, "-12 HP!", state["player_pos"], (255, 60, 60))

    # 2. Босс острова — Древний Каменный Голем
    boss = state.get("boss")
    if boss and boss["alive"]:
        if boss["atk_cd"] > 0:
            boss["atk_cd"] -= dt
        if boss["slam_timer"] > 0:
            boss["slam_timer"] -= dt

        bx, by = boss["pos"]
        hx, hy = boss["home"]
        dist_home = np.hypot(bx - hx, by - hy)
        dist_player = np.hypot(px - bx, py - by)

        target = state["player_pos"] if (dist_player < 240 and dist_home < 420) else boss["home"]
        tx, ty = target
        dist_target = np.hypot(tx - bx, ty - by)

        if dist_target > 24:
            ang = np.arctan2(ty - by, tx - bx)
            nbx = bx + np.cos(ang) * 1.45
            nby = by + np.sin(ang) * 1.45
            boss["pos"] = [nbx, nby]
            bgx, bgy = int(nbx) // GRID_SIZE, int(nby) // GRID_SIZE
            if (bgx, bgy) in state["buildings"] and state["buildings"][(bgx, bgy)]["type"] == "wall":
                del state["buildings"][(bgx, bgy)]
                sounds["boss_slam"].play()

        if dist_player < 42 and boss["atk_cd"] <= 0:
            boss["atk_cd"] = 2.0
            boss["slam_timer"] = 0.35
            state["health"] -= 24.0
            sounds["boss_slam"].play()
            add_text(state, "-24 HP (УДАР ГОЛЕМА)!", state["player_pos"], (255, 50, 50))
