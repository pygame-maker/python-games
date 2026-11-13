import pygame
import numpy as np
from config import SCREEN_W, SCREEN_H, WORLD_W, WORLD_H, GRID_SIZE

def draw_hud(screen, font, big_font, state, minimap_surf, is_night, near_bench):
    """Отрисовывает панель ресурсов, крафта, полоску босса и миникарту."""
    px_world, py_world = state["player_pos"]

    hud_h = 128 if near_bench else 104
    pygame.draw.rect(screen, (15, 18, 22, 220), (10, 10, 720, hud_h), border_radius=6)

    phase = f"ДЕНЬ {state['day_count']} (НОЧЬ)" if is_night else f"ДЕНЬ {state['day_count']}"
    s1 = f"{phase} | HP: {int(state['health'])}% | Тепло: {int(state['warmth'])}% | Сытость: {int(state['hunger'])}%  [F5: Сохр, F9: Загр]"
    s2 = f"Дерево: {state['inv']['wood']} | Камень: {state['inv']['stone']} | Еда: {state['inv']['food']} [E-есть, F-рыба] | Семена: {state['inv']['seeds']} | Факел: {int(state['gear']['torch_fuel'])}%"
    s3 = "1:Рука  2:Пол(2д)  3:Стена(4д)  4:Костер(5д,3к)  5:Верстак(6д,4к)  6:Сундук(8д)  7:Грядка(3д,1сем)"
    s4 = "Сундук: ЛКМ положить 5 рес. / ПКМ забрать | Грядка: ЛКМ собрать урожай (Слот 1)"

    screen.blit(font.render(s1, True, (255, 255, 255)), (20, 15))
    screen.blit(font.render(s2, True, (240, 210, 140)), (20, 38))
    screen.blit(font.render(s3, True, (170, 220, 180)), (20, 61))
    screen.blit(font.render(s4, True, (160, 185, 205)), (20, 82))

    if near_bench:
        craft_str = "ВЕРСТАК: [Z] Кам.Топор (4д,3к)   [X] Копье (5д,2к)   [C] Факел (3д)   [V] Огн.Меч (10д,10к,1 Сердце Голема)"
        screen.blit(font.render(craft_str, True, (255, 220, 90)), (20, 106))

    boss = state.get("boss")
    if boss and boss["alive"]:
        bx_w, by_w = boss["pos"]
        dist_boss = np.hypot(px_world - bx_w, py_world - by_w)
        if dist_boss < 320:
            bw = 400
            bx = SCREEN_W // 2 - bw // 2
            pygame.draw.rect(screen, (20, 20, 25), (bx - 4, SCREEN_H - 55, bw + 8, 34), border_radius=5)
            hp_ratio = max(0.0, boss["hp"] / boss["max_hp"])
            pygame.draw.rect(screen, (200, 45, 45), (bx, SCREEN_H - 51, int(bw * hp_ratio), 26), border_radius=4)
            b_txt = font.render(f"ДРЕВНИЙ КАМЕННЫЙ ГОЛЕМ: {boss['hp']} / {boss['max_hp']} HP", True, (255, 255, 255))
            screen.blit(b_txt, (SCREEN_W // 2 - b_txt.get_width() // 2, SCREEN_H - 46))

    mm_x, mm_y = SCREEN_W - 165, 15
    pygame.draw.rect(screen, (255, 255, 255), (mm_x - 2, mm_y - 2, 154, 154), 2)
    screen.blit(minimap_surf, (mm_x, mm_y))

    for (bx, by), b in state["buildings"].items():
        if b["type"] == "fire":
            pygame.draw.circle(screen, (255, 180, 0), (mm_x + int((bx * GRID_SIZE / WORLD_W) * 150), mm_y + int((by * GRID_SIZE / WORLD_H) * 150)), 3)

    if boss and boss["alive"]:
        bx_w, by_w = boss["pos"]
        pygame.draw.circle(screen, (200, 50, 255), (mm_x + int((bx_w / WORLD_W) * 150), mm_y + int((by_w / WORLD_H) * 150)), 4)

    pygame.draw.circle(screen, (255, 50, 50), (mm_x + int((px_world / WORLD_W) * 150), mm_y + int((py_world / WORLD_H) * 150)), 3)

    if state["game_over"]:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        screen.blit(overlay, (0, 0))
        t1 = big_font.render(f"ВЫ ПОГИБЛИ (Прожито дней: {state['day_count']})", True, (255, 80, 80))
        t2 = font.render("Нажмите [R] для нового острова или [F9] для загрузки сохранения", True, (255, 255, 255))
        screen.blit(t1, (SCREEN_W // 2 - t1.get_width() // 2, SCREEN_H // 2 - 30))
        screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, SCREEN_H // 2 + 15))
