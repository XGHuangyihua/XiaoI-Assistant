#Program start
import pyautogui
import time
import pyperclip
import ctypes

def main():
    try:
        # 切换到英文输入法（模拟 Alt+Shift）
        print("Switching to English input method...")
        KEYEVENTF_KEYDOWN = 0x0000
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(0x12, 0, KEYEVENTF_KEYDOWN, 0)  # Alt down
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(0x10, 0, KEYEVENTF_KEYDOWN, 0)  # Shift down
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, 0)    # Shift up
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)    # Alt up
        time.sleep(0.3)
        
        # 打开运行对话框
        print("Opening Run dialog...")
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5)
        
        # 输入 calc 并回车
        print("Typing 'calc'...")
        pyautogui.write('calc')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(2)  # 等待计算器启动
        
        # 输入计算表达式 123*456
        print("Entering calculation: 123*456")
        pyautogui.write('123')
        time.sleep(0.3)
        pyautogui.write('*')
        time.sleep(0.3)
        pyautogui.write('456')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(1)  # 等待计算结果显示
        
        print("Calculation completed.")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = main()
    print(f"Execution result: {result}")
#Program end