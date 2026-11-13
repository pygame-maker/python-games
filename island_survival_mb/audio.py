import pygame
import numpy as np

def _to_sound(wave, volume):
    """Преобразует одномерную волну в 2D стерео-массив для Pygame."""
    data = (wave * volume).astype(np.int16)
    stereo = np.column_stack((data, data))
    return pygame.sndarray.make_sound(stereo)

def generate_procedural_sounds():
    """Синтезирует звуковые эффекты через NumPy без внешних файлов."""
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    sr = 22050
    sounds = {}

    # 1. Удар по дереву
    t = np.linspace(0, 0.12, int(sr * 0.12), False)
    wave = np.sin(2 * np.pi * np.linspace(160, 50, len(t)) * t) * np.exp(-t * 25)
    sounds["chop"] = _to_sound(wave, 18000)

    # 2. Удар по камню
    t = np.linspace(0, 0.15, int(sr * 0.15), False)
    wave = (np.sin(2 * np.pi * 850 * t) * 0.5 + np.random.uniform(-0.5, 0.5, len(t))) * np.exp(-t * 30)
    sounds["mine"] = _to_sound(wave, 15000)

    # 3. Строительство / Крафт / Посадка
    t = np.linspace(0, 0.14, int(sr * 0.14), False)
    wave = np.sin(2 * np.pi * 420 * t) * np.exp(-t * 20)
    sounds["build"] = _to_sound(wave, 14000)

    # 4. Урон / Рык
    t = np.linspace(0, 0.25, int(sr * 0.25), False)
    wave = (np.sin(2 * np.pi * 95 * t) + np.random.uniform(-0.3, 0.3, len(t))) * np.exp(-t * 10)
    sounds["hit"] = _to_sound(wave, 18000)

    # 5. Сбор / Еда / Победа
    t = np.linspace(0, 0.12, int(sr * 0.12), False)
    wave = np.sin(2 * np.pi * np.linspace(350, 680, len(t)) * t) * np.exp(-t * 18)
    sounds["pickup"] = _to_sound(wave, 12000)

    # 6. Удар босса (тяжелый бас)
    t = np.linspace(0, 0.4, int(sr * 0.4), False)
    wave = np.sin(2 * np.pi * np.linspace(80, 30, len(t)) * t) * np.exp(-t * 6)
    sounds["boss_slam"] = _to_sound(wave, 24000)

    return sounds
