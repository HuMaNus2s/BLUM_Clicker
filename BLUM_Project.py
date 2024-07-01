import pygame
import pygame_menu
import pyautogui
import cv2
import numpy as np
from PIL import Image
from threading import Thread, Event
import mss
import pygetwindow as gw
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import keyboard

# Глобальные переменные
target_image = None
target_image_cv2 = None
clicker_running = False
stop_event = Event()
thread_clicker = None
thread_updater = None
window = None
FRAMES = 144  # Установим FPS на уровне 144

# Создаем Pygame окно и устанавливаем режим
pygame.init()
pygame.display.set_caption('Clicker')
surface = pygame.display.set_mode((900, 712))
clock = pygame.time.Clock()

# Функция захвата изображения из определенного окна
def capture_window(window):
    with mss.mss() as sct:
        monitor = {"top": window.top, "left": window.left, "width": window.width, "height": window.height}
        img = sct.grab(monitor)
        img = np.array(img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

# Функция обновления изображения в окне
def update_image(window):
    while not stop_event.is_set():
        frame = capture_window(window)
        
        # Если целевое изображение установлено, выполняем шаблонное сопоставление
        if target_image_cv2 is not None:
            # Масштабируем изображение для улучшения поиска
            for scale in np.linspace(0.5, 1.5, 20)[::-1]:
                resized = cv2.resize(target_image_cv2, None, fx=scale, fy=scale)
                res = cv2.matchTemplate(frame, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                # Пороговое значение для обнаружения
                threshold = 0.8
                if max_val >= threshold:
                    h, w = resized.shape[:2]
                    top_left = max_loc
                    bottom_right = (top_left[0] + w, top_left[1] + h)

                    # Рисуем прямоугольник вокруг обнаруженного шаблона
                    cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                    break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = img.resize((402, 712))  # Масштабируем изображение для вывода
        img_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
        
        # Отрисовка на скрытой поверхности
        surface.blit(img_surface, (0, 0))
        
        # Обновление экрана
        pygame.display.update()

        # Ограничение FPS
        clock.tick(FRAMES)

# Основная функция обработки и нажатия
def main(window):
    global clicker_running
    while not stop_event.is_set():
        if clicker_running:
            frame = capture_window(window)

            # Если целевое изображение установлено, выполняем шаблонное сопоставление
            if target_image_cv2 is not None:
                for scale in np.linspace(0.5, 1.5, 20)[::-1]:
                    resized = cv2.resize(target_image_cv2, None, fx=scale, fy=scale)
                    res = cv2.matchTemplate(frame, resized, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)

                    # Пороговое значение для обнаружения
                    threshold = 0.8
                    if max_val >= threshold:
                        h, w = resized.shape[:2]
                        top_left = max_loc
                        center_x = top_left[0] + w // 2
                        center_y = top_left[1] + h // 2

                        # Нажимаем на центр обнаруженного шаблона
                        pyautogui.click(window.left + center_x, window.top + center_y)
                        break
        
        # Задержка для предотвращения слишком частого нажатия
        time.sleep(1 / FRAMES)  # Обновление каждые ~16.67 миллисекунд

# Функция выбора окна
def choose_window():
    global window, thread_updater
    window_title = "TelegramDesktop"  # Или имя окна вашего Web3 приложения
    matching_windows = [w for w in gw.getWindowsWithTitle(window_title) if w.title == window_title]
    if matching_windows:
        window = matching_windows[0]
        if thread_updater:
            stop_event.set()
            thread_updater.join()
            stop_event.clear()
        thread_updater = Thread(target=update_image, args=(window,))
        thread_updater.start()
    else:
        messagebox.showerror("Ошибка", f"Не удалось найти окно с названием {window_title}.")

# Функция выбора целевого изображения
def choose_target():
    global target_image, target_image_cv2
    target_file = filedialog.askopenfilename(title="Выберите целевое изображение", filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if target_file:
        target_image = Image.open(target_file)
        target_image_cv2 = cv2.cvtColor(np.array(target_image), cv2.COLOR_RGB2BGR)
        target_image = target_image.resize((200, 200), Image.ANTIALIAS)
        target_image = target_image.convert('RGB')

# Функция для запуска программы
def start_program():
    global thread_clicker, stop_event, clicker_running
    if window and target_image_cv2 is not None:
        stop_event.clear()
        thread_clicker = Thread(target=main, args=(window,))
        thread_clicker.start()
        clicker_running = True
        print("Программа запущена")
    else:
        messagebox.showerror("Ошибка", "Выберите целевое изображение перед запуском программы!")
        clicker_running = False

# Функция для остановки программы
def stop_program():
    global thread_clicker, stop_event, clicker_running
    stop_event.set()
    if thread_clicker:
        thread_clicker.join()
        print("Программа остановлена")
        thread_clicker = None
        clicker_running = False

    # Очистка экрана
    surface.fill((0, 0, 0))
    pygame.display.update()

# Функция для переключения кликера
def toggle_clicker():
    global clicker_running
    clicker_running = not clicker_running
    
    if clicker_running:
        start_program()
        status = "Запущен"
        print(f"Status: {status}")
    else:
        stop_program()
        status = "Остановлен"
        print(f"Status: {status}")

# Назначение горячих клавиш
keyboard.add_hotkey('shift+s', toggle_clicker)

# Создание GUI с использованием pygame-menu
def create_menu():
    global clicker_running, stop_event, thread_clicker, thread_updater, window

    try:
        menu = pygame_menu.Menu('', 900, 712, theme=pygame_menu.themes.THEME_DARK)
    except Exception as e:
        print(f"Exception occurred: {e}")
        raise

    # Добавление пунктов меню справа
    menu.add.button('Выбрать целевое изображение', choose_target).translate(200, 100)
    menu.add.button('Запустить программу', start_program).translate(200, 110)
    menu.add.button('Остановить программу', stop_program).translate(200, 120)
    menu.add.button('Выход', pygame_menu.events.EXIT).translate(200, 130)

    # Автоматический выбор окна "Telegram Desktop"
    choose_window()

    menu.mainloop(surface)

# Запуск главного меню
if __name__ == '__main__':
    create_menu()
