import pygame
from config import HEIGHT, WIDTH


class TouchController:
    def __init__(self):
        self.fingers = {}  # finger_id -> (x, y)
        self.mouse_down = False
        self.mouse_pos = (0, 0)

        # Координаты кнопок под разрешение 640x360 (удобно для больших пальцев)
        self.buttons = {
            "left": {"rect": pygame.Rect(14, HEIGHT - 66, 54, 52), "label": "<", "col": (0, 210, 230)},
            "right": {"rect": pygame.Rect(76, HEIGHT - 66, 54, 52), "label": ">", "col": (0, 210, 230)},
            "down": {"rect": pygame.Rect(45, HEIGHT - 124, 54, 48), "label": "v", "col": (255, 190, 60)},
            "jump": {"rect": pygame.Rect(WIDTH - 68, HEIGHT - 68, 54, 54), "label": "JMP", "col": (0, 255, 170)},
            "dash": {"rect": pygame.Rect(WIDTH - 130, HEIGHT - 68, 54, 54), "label": "DSH", "col": (0, 230, 255)},
            "hook": {"rect": pygame.Rect(WIDTH - 68, HEIGHT - 130, 54, 54), "label": "HOK", "col": (255, 90, 220)},
            "fire": {"rect": pygame.Rect(WIDTH - 130, HEIGHT - 130, 54, 54), "label": "FIR", "col": (255, 210, 60)},
            "wep": {"rect": pygame.Rect(268, 8, 54, 26), "label": "WEP", "col": (180, 230, 255)},
            "shop": {"rect": pygame.Rect(330, 8, 54, 26), "label": "MOD", "col": (0, 255, 190)},
        }

        self.held = {k: False for k in self.buttons}
        self.just_pressed = {k: False for k in self.buttons}
        self.tap_points = []  # Точки одиночных нажатий для меню и магазина

    def handle_event(self, event):
        if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
            px = int(event.x * WIDTH)
            py = int(event.y * HEIGHT)
            self.fingers[event.finger_id] = (px, py)
            if event.type == pygame.FINGERDOWN:
                self.tap_points.append((px, py))
        elif event.type == pygame.FINGERUP:
            self.fingers.pop(event.finger_id, None)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            self.mouse_pos = event.pos
            self.tap_points.append(event.pos)
        elif event.type == pygame.MOUSEMOTION and self.mouse_down:
            self.mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

    def update(self):
        active_pts = list(self.fingers.values())
        if self.mouse_down:
            active_pts.append(self.mouse_pos)

        for k, btn in self.buttons.items():
            # Расширяем зону попадания пальцем на 4 пикселя для комфорта
            hit_rect = btn["rect"].inflate(8, 8)
            now_held = any(hit_rect.collidepoint(pt) for pt in active_pts)
            self.just_pressed[k] = now_held and not self.held[k]
            self.held[k] = now_held

    def consume_taps(self):
        taps = list(self.tap_points)
        self.tap_points.clear()
        return taps

    def draw(self, screen, font, near_terminal=False):
        for k, btn in self.buttons.items():
            if k == "shop" and not near_terminal:
                continue

            r = btn["rect"]
            is_active = self.held[k]
            col = btn["col"]

            # Полупрозрачная подложка кнопки
            surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            alpha = 110 if is_active else 45
            surf.fill((col[0], col[1], col[2], alpha))
            screen.blit(surf, (r.x, r.y))

            pygame.draw.rect(screen, col, r, 2 if is_active else 1, border_radius=8)
            lbl = font.render(btn["label"], True, (255, 255, 255) if is_active else col)
            screen.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))
