import random
import time
import pygame


def play_sound_after_random_time(sound_file):
    # Инициализация микшера pygame
    pygame.mixer.init()

    random_time = 111
    print(f"Звук будет воспроизведен через {random_time} секунд.")

    time.sleep(random_time)

    # Загрузка и воспроизведение звука
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()

    # Ожидание завершения воспроизведения
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

    print("Звук воспроизведен.")


# Укажите путь к вашему звуковому файлу
sound_file = 'sou.mp3'

play_sound_after_random_time(sound_file)
