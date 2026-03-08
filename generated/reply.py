python
编辑
1#Program start
2import pyautogui
3import time
4import pyperclip
5import ctypes
6
7def main():
8    try:
9        # 切换到英文输入法（模拟 Alt+Shift）
10        print("Switching to English input method...")
11        KEYEVENTF_KEYDOWN = 0x0000
12        KEYEVENTF_KEYUP = 0x0002
13        ctypes.windll.user32.keybd_event(0x12, 0, KEYEVENTF_KEYDOWN, 0)  # Alt down
14        time.sleep(0.1)
15        ctypes.windll.user32.keybd_event(0x10, 0, KEYEVENTF_KEYDOWN, 0)  # Shift down
16        time.sleep(0.1)
17        ctypes.windll.user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, 0)    # Shift up
18        time.sleep(0.1)
19        ctypes.windll.user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)    # Alt up
20        time.sleep(0.3)
21        
22        # 打开运行对话框
23        print("Opening Run dialog...")
24        pyautogui.hotkey('win', 'r')
25        time.sleep(0.5)
26        
27        # 输入 calc 并回车
28        print("Typing 'calc'...")
29        pyautogui.write('calc')
30        time.sleep(0.3)
31        pyautogui.press('enter')
32        time.sleep(2)  # 等待计算器启动
33        
34        # 输入计算表达式 123*456
35        print("Entering calculation: 123*456")
36        pyautogui.write('123')
37        time.sleep(0.3)
38        pyautogui.write('*')
39        time.sleep(0.3)
40        pyautogui.write('456')
41        time.sleep(0.3)
42        pyautogui.press('enter')
43        time.sleep(1)  # 等待计算结果显示
44        
45        print("Calculation completed.")
46        return {"success": True}
47    except Exception as e:
48        return {"success": False, "error": str(e)}
49
50if __name__ == "__main__":
51    result = main()
52    print(f"Execution result: {result}")
53#Program end