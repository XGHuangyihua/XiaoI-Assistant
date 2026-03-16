#Program start
import pyautogui
import time
import pyperclip
import sys

def main():
    # 初始化：尝试切换到英文键盘布局
    try:
        import win32api
        win32api.LoadKeyboardLayout('00000409', 1)
        time.sleep(0.3)
        print("Keyboard layout switched to English.")
    except ImportError:
        print("pywin32 not installed, skipping keyboard layout switch.")
    except Exception as e:
        print(f"Failed to switch keyboard layout: {e}")

    try:
        # 步骤1: 打开运行对话框
        print("Opening Run dialog...")
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5)

        # 步骤2: 输入 calc 并回车打开计算器
        print("Typing 'calc' to open Calculator...")
        pyautogui.write('calc')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(2.0)  # 等待计算器完全启动

        # 步骤3: 输入计算表达式 123*456
        # 注意：标准计算器通常支持直接输入表达式并回车计算
        print("Inputting calculation: 123*456")
        pyautogui.write('123*456')
        time.sleep(0.5)
        
        # 步骤4: 按回车键执行计算
        print("Pressing Enter to calculate...")
        pyautogui.press('enter')
        time.sleep(1.0)

        print("Calculation command sent successfully.")
        return {"success": True}

    except Exception as e:
        print(f"An error occurred: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = main()
    print(f"Execution result: {result}")
#Program end