"""
WiFi键盘控制器 - 使用 pyautogui 实现纯软件键鼠控制
无需ESP32硬件，直接通过系统API模拟键盘鼠标操作
"""

import pyautogui
import time
import sys
import pyperclip

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

import ctypes
from ctypes import wintypes


class WiFiKeyboard:
    """本地键盘鼠标控制器 - 使用 pyautogui"""

    def __init__(self, mdns_name=None):
        """
        初始化键盘控制器

        参数:
            mdns_name: 保留参数，用于兼容（忽略）
        """
        self.mdns_name = mdns_name
        self.connected = True
        self.ip = "本地模式"
        self.base_url = "pyautogui"
        self._original_ime = None
        print("[成功] 键盘控制器已初始化 (本地模式)")

    def test_connection(self):
        """测试连接（本地模式始终返回True）"""
        return True

    def discover_mdns(self, timeout=5):
        """mDNS发现（本地模式不需要）"""
        return None

    def discover_scan(self):
        """网络扫描（本地模式不需要）"""
        return None

    def connect(self):
        """连接（本地模式直接返回成功）"""
        self.connected = True
        return True

    def _update_last_success(self):
        """更新成功时间戳（本地模式不需要）"""
        pass

    def press_key(self, key):
        """
        按下一个键

        参数:
            key: 键名，如 "ENTER", "WIN_R", "CTRL_C"

        返回:
            bool: 是否成功
        """
        if not self.connected:
            print("[错误] 控制器未初始化")
            return False

        try:
            key_mapping = {
                "ENTER": "enter",
                "TAB": "tab",
                "SPACE": "space",
                "BACKSPACE": "backspace",
                "DELETE": "delete",
                "ESC": "esc",
                "WIN_R": "win+r",
                "WIN_D": "win+d",
                "WIN_E": "win+e",
                "CTRL_C": "ctrl+c",
                "CTRL_V": "ctrl+v",
                "CTRL_A": "ctrl+a",
                "CTRL_X": "ctrl+x",
                "CTRL_Z": "ctrl+z",
                "CTRL_S": "ctrl+s",
                "CTRL": "ctrl",
                "ALT": "alt",
                "SHIFT": "shift",
                "UP": "up",
                "DOWN": "down",
                "LEFT": "left",
                "RIGHT": "right",
                "F1": "f1",
                "F2": "f2",
                "F3": "f3",
                "F4": "f4",
                "F5": "f5",
                "F6": "f6",
                "F7": "f7",
                "F8": "f8",
                "F9": "f9",
                "F10": "f10",
                "F11": "f11",
                "F12": "f12",
            }

            key_lower = key.lower()
            pyauto_key = key_mapping.get(key.upper(), key_lower)

            pyautogui.press(pyauto_key)
            print(f"[按键] {key}")
            self._update_last_success()
            return True
        except Exception as e:
            print(f"[失败] 按键失败: {e}")
            return False

    def type_text(self, text):
        """
        输入文字
        - ASCII字符用 pyautogui.write()
        - 非ASCII字符用剪贴板粘贴
        """
        if not self.connected:
            print("[错误] 控制器未初始化")
            return False

        def is_ascii(s):
            return all(ord(c) < 128 for c in s)

        try:
            if is_ascii(text):
                pyautogui.write(text, interval=0.05)
                print(f"[输入] {text}")
            else:
                pyperclip.copy(text)
                print(f"[剪贴板] 已复制: {text[:30]}{'...' if len(text) > 30 else ''}")
                time.sleep(0.2)
                self.press_ctrl_v()

            return True
        except Exception as e:
            print(f"[错误] 输入失败: {e}")
            return False

    def release_all(self):
        """释放所有按键"""
        try:
            pyautogui.keyUp("ctrl")
            pyautogui.keyUp("alt")
            pyautogui.keyUp("shift")
            pyautogui.keyUp("win")
            return True
        except:
            return False

    def mouse_move(self, x, y):
        """移动鼠标到指定位置"""
        try:
            pyautogui.moveTo(x, y, duration=0.2)
            print(f"[鼠标移动] ({x}, {y})")
            return True
        except Exception as e:
            print(f"[失败] 鼠标移动失败: {e}")
            return False

    def mouse_click(self, x=None, y=None, button="left"):
        """点击鼠标"""
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button)
                print(f"[鼠标点击] ({x}, {y})")
            else:
                pyautogui.click(button=button)
                print(f"[鼠标点击] {button}")
            return True
        except Exception as e:
            print(f"[失败] 鼠标点击失败: {e}")
            return False

    def mouse_double_click(self, x=None, y=None, button="left"):
        """双击鼠标"""
        try:
            if x is not None and y is not None:
                pyautogui.doubleClick(x, y, button=button)
            else:
                pyautogui.doubleClick(button=button)
            print(f"[鼠标双击] ({x}, {y})")
            return True
        except Exception as e:
            print(f"[失败] 双击失败: {e}")
            return False

    def mouse_right_click(self, x=None, y=None):
        """右键点击"""
        return self.mouse_click(x, y, button="right")

    def scroll(self, clicks):
        """滚动鼠标滚轮"""
        try:
            pyautogui.scroll(clicks)
            print(f"[滚动] {clicks} 点击")
            return True
        except Exception as e:
            print(f"[失败] 滚动失败: {e}")
            return False

    def drag_to(self, x, y, button="left"):
        """拖拽鼠标"""
        try:
            pyautogui.dragTo(x, y, button=button)
            print(f"[拖拽] 到 ({x}, {y})")
            return True
        except Exception as e:
            print(f"[失败] 拖拽失败: {e}")
            return False

    def hotkey(self, *keys):
        """执行快捷键组合"""
        try:
            pyautogui.hotkey(*keys)
            print(f"[快捷键] {'+'.join(keys)}")
            return True
        except Exception as e:
            print(f"[失败] 快捷键失败: {e}")
            return False

    def press_enter(self):
        return self.press_key("ENTER")

    def press_tab(self):
        return self.press_key("TAB")

    def press_space(self):
        return self.press_key("SPACE")

    def press_backspace(self):
        return self.press_key("BACKSPACE")

    def press_delete(self):
        return self.press_key("DELETE")

    def press_esc(self):
        return self.press_key("ESC")

    def press_win_r(self):
        return self.press_key("WIN_R")

    def press_win_d(self):
        return self.press_key("WIN_D")

    def press_win_e(self):
        return self.press_key("WIN_E")

    def press_ctrl_c(self):
        return self.press_key("CTRL_C")

    def press_ctrl_v(self):
        return self.press_key("CTRL_V")

    def press_ctrl_a(self):
        return self.press_key("CTRL_A")

    def press_ctrl_x(self):
        return self.press_key("CTRL_X")

    def press_ctrl_z(self):
        return self.press_key("CTRL_Z")

    def press_ctrl_s(self):
        return self.press_key("CTRL_S")

    def press_alt_tab(self):
        return self.hotkey("alt", "tab")

    def press_alt_f4(self):
        return self.hotkey("alt", "f4")

    def press_f1(self):
        return self.press_key("F1")

    def press_f2(self):
        return self.press_key("F2")

    def press_f3(self):
        return self.press_key("F3")

    def press_f4(self):
        return self.press_key("F4")

    def press_f5(self):
        return self.press_key("F5")

    def press_up(self):
        return self.press_key("UP")

    def press_down(self):
        return self.press_key("DOWN")

    def press_left(self):
        return self.press_key("LEFT")

    def press_right(self):
        return self.press_key("RIGHT")

    def get_status(self):
        """获取连接状态"""
        return "[已连接] 本地模式 (pyautogui)"

    def close(self):
        """关闭连接"""
        self.release_all()
        self.connected = False


if __name__ == "__main__":
    print("=" * 50)
    print("本地键盘控制器测试")
    print("=" * 50)

    kb = WiFiKeyboard()

    if kb.connected:
        print(f"\n[成功] 初始化成功")

        print("\n[测试] 输入英文: hello")
        kb.type_text("hello")
        time.sleep(1)

        print("\n[测试] 输入中文: 春天的诗")
        kb.type_text("《春天的诗》")
        time.sleep(1)

        print("\n[测试] 打开运行对话框")
        kb.press_win_r()
        time.sleep(0.5)
        kb.type_text("notepad")
        kb.press_enter()
        time.sleep(1)

        print("\n[完成] 测试完成")
    else:
        print("\n[失败] 初始化失败")

    kb.close()
