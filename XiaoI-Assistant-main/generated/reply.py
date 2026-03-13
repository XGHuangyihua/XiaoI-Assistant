python
复制
下载
#Program start
import pyautogui
import time
import pyperclip
import ctypes

def main():
    try:
        # 切换到英文输入法（模拟 Alt+Shift）
        KEYEVENTF_KEYDOWN = 0x0000
        KEYEVENTF_KEYUP = 0x0002
        print("切换到英文输入法...")
        ctypes.windll.user32.keybd_event(0x12, 0, KEYEVENTF_KEYDOWN, 0)  # Alt down
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(0x10, 0, KEYEVENTF_KEYDOWN, 0)  # Shift down
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, 0)    # Shift up
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)    # Alt up
        time.sleep(0.3)
        
        print("打开运行对话框...")
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5)
        
        print("输入 %temp% 打开临时文件夹...")
        pyautogui.write('%temp%')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(2)
        
        print("按 Ctrl+A 全选文件...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        print("按 Delete 键删除文件...")
        pyautogui.press('delete')
        time.sleep(0.5)
        
        print("确认删除（如果有确认对话框）...")
        pyautogui.press('enter')
        time.sleep(2)
        
        print("关闭文件资源管理器...")
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.5)
        
        print("再次打开运行对话框...")
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5)
        
        print("输入 temp 打开另一个临时文件夹...")
        pyautogui.write('temp')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(2)
        
        print("按 Ctrl+A 全选文件...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        print("按 Delete 键删除文件...")
        pyautogui.press('delete')
        time.sleep(0.5)
        
        print("确认删除（如果有确认对话框）...")
        pyautogui.press('enter')
        time.sleep(2)
        
        print("关闭文件资源管理器...")
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.5)
        
        print("OpenCL缓存清理完成！")
        return {"success": True, "message": "OpenCL缓存清理完成"}
        
    except Exception as e:
        error_msg = f"执行出错: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

if __name__ == "__main__":
    result = main()
    print(f"执行结果: {result}")
#Program end