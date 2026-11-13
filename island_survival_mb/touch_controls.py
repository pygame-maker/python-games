import pygame
import numpy as np

class TouchUI:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h

        # Виртуальный джойстик (левый нижний угол)
        self.joy_center = (110, screen_h - 110)
        self.joy_radius = 65
        self.knob_pos = list(self.joy_center)
        self.joy_active = False
        self.move_vec = (0.0, 0.0)
        self.last_dir = (0.0, -1.0)  # Направление взгляда для строительства

        # Кнопки действий (правый нижний угол)
        self.buttons = {
            "action": {"rect": pygame.Rect(screen_w - 115, screen_h - 115, 90, 90), "label": "УДАР / БИТЬ", "color": (200, 65, 55)},
            "build":  {"rect": pygame.Rect(screen_w - 215, screen_h - 105, 80, 80), "label": "СТРОИТЬ", "color": (65, 145, 75)},
            "slot":   {"rect": pygame.Rect(screen_w - 215, screen_h - 195, 80, 75), "label": "СЛОТ", "color": (70, 110, 160)},
            "eat":    {"rect": pygame.Rect(screen_w - 110, screen_h - 205, 80, 75), "label": "ЕСТЬ", "color": (180, 130, 45)},
            "fish":   {"rect": pygame.Rect(screen_w - 110, screen_h - 290, 80, 70), "label": "РЫБА", "color": (50, 130, 175)},
            "craft":  {"rect": pygame.Rect(screen_w - 215, screen_h - 280, 80, 70), "label": "КРАФТ", "color": (150, 90, 170)},
        }

    def handle_touch(self, event, screen):
        """Обрабатывает нажатия и свайпы по экрану планшета."""
        sw_real, sh_real = screen.get_size()
        scale_x = self.sw / sw_real
        scale_y = self.sh / sh_real

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            tx, ty = mx * scale_x, my * scale_y

            # Проверка касания в зоне джойстика
            jx, jy = self.joy_center
            if np.hypot(tx - jx, ty - jy) < self.joy_radius * 1.6:
                self.joy_active = True
                self._update_joystick(tx, ty)
                return None

            # Проверка нажатия кнопок
            for name, btn in self.buttons.items():
                if btn["rect"].collidepoint(tx, ty):
                    return name

        elif event.type == pygame.MOUSEMOTION and self.joy_active:
            mx, my = event.pos
            self._update_joystick(mx * scale_x, my * scale_y)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.joy_active:
                self.joy_active = False
                self.knob_pos = list(self.joy_center)
                self.move_vec = (0.0, 0.0)

        return None

    def _update_joystick(self, tx, ty):
        jx, jy = self.joy_center
        dx, dy = tx - jx, ty - jy
        dist = np.hypot(dx, dy)
        if dist > 0:
            nx, ny = dx / dist, dy / dist
            self.last_dir = (nx, ny)
            clamped = min(dist, self.joy_radius)
            self.knob_pos = [jx + nx * clamped, jy + ny * clamped]
            power = clamped / self.joy_radius
            self.move_vec = (nx * power, ny * power)

    def draw(self, screen, font, near_bench):
        """Рисует полупрозрачный джойстик и кнопки поверх игры."""
        ui_surf = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)

        # Джойстик
        jx, jy = self.joy_center
        pygame.draw.circle(ui_surf, (255, 255, 255, 55), (jx, jy), self.joy_radius)
        pygame.draw.circle(ui_surf, (255, 255, 255, 110), (jx, jy), self.joy_radius, 2)
        kx, ky = int(self.knob_pos[0]), int(self.knob_pos[1])
        pygame.draw.circle(ui_surf, (255, 255, 255, 160), (kx, ky), 26)

        # Кнопки
        for name, btn in self.buttons.items():
            if name == "craft" and not near_bench:
                continue
            r = btn["rect"]
            r_col, g_col, b_col = btn["color"]
            pygame.draw.rect(ui_surf, (r_col, g_col, b_col, 150), r, border_radius=14)
            pygame.draw.rect(ui_surf, (255, 255, 255, 180), r, 2, border_radius=14)
            lbl = font.render(btn["label"], True, (255, 255, 255))
            ui_surf.blit(lbl, (r.centerx - lbl.get_width() // 2, r.centery - lbl.get_height() // 2))

        screen.blit(ui_surf, (0, 0))
