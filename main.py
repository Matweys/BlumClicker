import time
import cv2
import keyboard
import mss
import numpy as np
import pygetwindow as gw
import win32api
import win32con
import pyautogui  # Добавим импорт pyautogui
import threading  # Добавим импорт threading


class Logger:
    def __init__(self, prefix=None):
        self.prefix = prefix

    def log(self, data: str):
        if self.prefix:
            print(f"{self.prefix} {data}")
        else:
            print(data)


logger = Logger("[Script]")


def hex_to_hsv(hex_color):
    hex_color = hex_color.lstrip('#')
    h_len = len(hex_color)
    rgb = tuple(int(hex_color[i:i + h_len // 3], 16) for i in range(0, h_len, h_len // 3))

    rgb_normalized = np.array([[rgb]], dtype=np.uint8)
    hsv = cv2.cvtColor(rgb_normalized, cv2.COLOR_RGB2HSV)
    return hsv[0][0]


def click_at(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)


def click_button_periodically(x, y, interval_min=35, interval_max=60):
    def click():
        while True:
            time.sleep(np.random.randint(interval_min, interval_max))
            pyautogui.click(x, y)
            logger.log(f'Clicked at: {x}, {y}')

    thread = threading.Thread(target=click, daemon=True)
    thread.start()


def click_color_areas(window_title, target_colors_hex):
    windows = gw.getWindowsWithTitle(window_title)
    if not windows:
        print(f"No window found with title: {window_title}")
        return

    window = windows[0]

    window.activate()

    target_hsvs = [hex_to_hsv(color) for color in target_colors_hex]

    with mss.mss() as sct:
        running = False

        def toggle_script():
            nonlocal running
            running = not running
            logger.log(f'Script running: {running}')
        time.sleep(1)
        keyboard.add_hotkey('z', toggle_script)

        # Запустим периодическое нажатие кнопки
        click_button_periodically(1043, 821)

        while True:
            if running:
                monitor = {
                    "top": window.top,
                    "left": window.left,
                    "width": window.width,
                    "height": window.height
                }
                img = np.array(sct.grab(monitor))

                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

                for target_hsv in target_hsvs:
                    lower_bound = np.array([max(0, target_hsv[0] - 5), 50, 50])
                    upper_bound = np.array([min(179, target_hsv[0] + 5), 255, 255])

                    mask = cv2.inRange(hsv, lower_bound, upper_bound)

                    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                    for contour in contours:
                        if cv2.contourArea(contour) < 500:
                            continue

                        M = cv2.moments(contour)
                        if M["m00"] == 0:
                            continue
                        cX = int(M["m10"] / M["m00"]) + monitor["left"]
                        cY = int(M["m01"] / M["m00"]) + monitor["top"]

                        click_offset_y = 0
                        click_at(cX, cY + click_offset_y)
                        logger.log(f'Нажал: {cX} {cY + click_offset_y}')
                pass
            else:
                pass


if __name__ == "__main__":
    logger.log('После запуска мини игры, нажмите клавишу "ё" на клавиатуре, раскладка клавиатуры должна быть EN, по окончанию мини игры, нажмите еще раз "ё" что бы отключить скрипт. Повторяйте действия нужное количество раз')
    target_colors_hex = ["#c5d900", "#7eff22"]
    click_color_areas("TelegramDesktop", target_colors_hex)
