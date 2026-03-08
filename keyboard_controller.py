"""
键盘控制器 - 负责与ESP32通信
"""
import serial
import serial.tools.list_ports
import time

class ESP32Keyboard:
    """ESP32键盘控制器"""
    
    def __init__(self):
        self.serial = None
        self.connected = False
        self.port_name = None
        self.port_description = None
        self.connect()
    
    def find_esp32_port(self):
        """
        自动查找ESP32连接的串口
        返回: (端口号, 端口描述) 或 (None, None)
        """
        ports = serial.tools.list_ports.comports()
        print("\n🔍 正在扫描可用串口...")
        
        for port in ports:
            print(f"  发现端口: {port.device} - {port.description}")
            
            # 常见的ESP32串口描述关键词
            keywords = ['USB', 'CH340', 'CH341', 'CP210', 'ESP32', 
                       'Serial', 'UART', 'COM', 'Arduino']
            
            # 检查端口描述是否包含关键词
            for keyword in keywords:
                if keyword.lower() in port.description.lower():
                    print(f"  ✅ 找到疑似ESP32端口: {port.device} ({port.description})")
                    return port.device, port.description
            
            # 在Windows上，ESP32通常是COM3-COM10
            if port.device.startswith('COM') and port.device[3:].isdigit():
                com_num = int(port.device[3:])
                if 3 <= com_num <= 10:
                    print(f"  🤔 可能是ESP32端口: {port.device}")
                    return port.device, port.description
        
        return None, None
    
    def connect(self):
        """连接到ESP32"""
        port, description = self.find_esp32_port()
        
        if not port:
            print("❌ 未找到ESP32设备")
            print("💡 请检查:")
            print("   1. ESP32是否正确连接")
            print("   2. 是否安装了CH340/CP210驱动")
            print("   3. 设备管理器中是否识别到串口")
            return False
        
        print(f"\n🔌 尝试连接: {port} ({description})")
        
        # 尝试不同的波特率
        baud_rates = [115200, 9600, 57600, 38400]
        
        for baud in baud_rates:
            try:
                print(f"  尝试波特率: {baud}")
                self.serial = serial.Serial(
                    port=port,
                    baudrate=baud,
                    timeout=2,
                    write_timeout=2
                )
                
                # 等待ESP32复位
                time.sleep(2.5)
                
                # 清空缓冲区
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                
                # 发送测试命令
                print("  发送测试命令...")
                self.serial.write(b"RELEASE\n")
                self.serial.flush()
                
                # 等待响应
                time.sleep(0.5)
                
                # 读取响应
                response = ""
                start_time = time.time()
                while time.time() - start_time < 2:
                    if self.serial.in_waiting > 0:
                        response_line = self.serial.readline().decode().strip()
                        if response_line:
                            response += response_line + "\n"
                            print(f"  收到响应: {response_line}")
                
                if response:
                    self.connected = True
                    self.port_name = port
                    self.port_description = description
                    print(f"\n✅ ESP32连接成功!")
                    print(f"  端口: {port}")
                    print(f"  描述: {description}")
                    print(f"  波特率: {baud}")
                    print(f"  响应: {response.strip()}")
                    
                    # 清空缓冲区准备后续通信
                    self.serial.reset_input_buffer()
                    return True
                else:
                    print(f"  ⚠️ 无响应，关闭连接")
                    self.serial.close()
                    
            except serial.SerialException as e:
                print(f"  ❌ 串口错误: {e}")
                if self.serial:
                    self.serial.close()
            except Exception as e:
                print(f"  ❌ 其他错误: {e}")
                if self.serial:
                    self.serial.close()
        
        print("\n❌ 所有连接尝试失败")
        return False
    
    def send_command(self, command, wait_response=True):
        """
        发送命令到ESP32
        
        参数:
            command: 要发送的命令字符串
            wait_response: 是否等待响应
        
        返回:
            bool: 是否成功
        """
        if not self.connected or not self.serial:
            print("❌ ESP32未连接")
            return False
        
        try:
            # 清空输入缓冲区，丢弃所有旧数据
            self.serial.reset_input_buffer()
            time.sleep(0.1)
            
            # 发送命令
            print(f"📤 发送: {command}")
            self.serial.write(f"{command}\n".encode())
            self.serial.flush()
            
            if wait_response:
                # 等待ESP32处理
                time.sleep(0.3)
                
                # 读取所有响应
                responses = []
                start_time = time.time()
                while time.time() - start_time < 2:  # 最多等待2秒
                    if self.serial.in_waiting > 0:
                        response = self.serial.readline().decode().strip()
                        if response:
                            responses.append(response)
                            print(f"📥 ESP32: {response}")
                    else:
                        time.sleep(0.1)
                
                return len(responses) > 0
            else:
                return True
            
        except serial.SerialTimeoutException:
            print("❌ 发送超时")
            return False
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False
    
    def send_with_retry(self, command, max_retries=3):
        """
        带重试的命令发送
        
        参数:
            command: 命令字符串
            max_retries: 最大重试次数
        
        返回:
            bool: 是否成功
        """
        for attempt in range(max_retries):
            if self.send_command(command):
                return True
            print(f"⚠️ 发送失败，重试 {attempt + 1}/{max_retries}")
            time.sleep(0.5)
        
        print(f"❌ 发送失败，已重试 {max_retries} 次")
        return False
    
    def press_key(self, key):
        """
        按下一个键
        
        参数:
            key: 键名，如 "ENTER", "CTRL_C", "WIN_R" 等
        
        返回:
            bool: 是否成功
        """
        # 完整的键名映射表
        key_map = {
            # 基础按键
            'enter': 'ENTER',
            'return': 'ENTER',
            'tab': 'TAB',
            'space': 'SPACE',
            'backspace': 'BACKSPACE',
            'delete': 'DELETE',
            'esc': 'ESC',
            'escape': 'ESC',
            
            # 修饰键
            'ctrl': 'CTRL',
            'alt': 'ALT',
            'shift': 'SHIFT',
            'win': 'WIN',
            'windows': 'WIN',
            
            # Win组合键 - 关键修复部分
            'win_r': 'WIN_R',      # 小写形式
            'win+r': 'WIN_R',       # 带加号形式
            'win r': 'WIN_R',       # 带空格形式
            'win_R': 'WIN_R',       # 混合大小写
            'WIN_R': 'WIN_R',       # 全大写形式（DeepSeek用的就是这个）
            
            'win_d': 'WIN_D',
            'win+d': 'WIN_D',
            'win d': 'WIN_D',
            'WIN_D': 'WIN_D',
            
            'win_e': 'WIN_E',
            'win+e': 'WIN_E',
            'win e': 'WIN_E',
            'WIN_E': 'WIN_E',
            
            # Alt组合键
            'alt_tab': 'ALT_TAB',
            'alt+tab': 'ALT_TAB',
            'alt tab': 'ALT_TAB',
            'ALT_TAB': 'ALT_TAB',
            
            'alt_f4': 'ALT_F4',
            'alt+f4': 'ALT_F4',
            'alt f4': 'ALT_F4',
            'ALT_F4': 'ALT_F4',
            
            # Ctrl组合键
            'ctrl_c': 'CTRL_C',
            'ctrl+c': 'CTRL_C',
            'ctrl c': 'CTRL_C',
            'CTRL_C': 'CTRL_C',
            
            'ctrl_v': 'CTRL_V',
            'ctrl+v': 'CTRL_V',
            'ctrl v': 'CTRL_V',
            'CTRL_V': 'CTRL_V',
            
            'ctrl_a': 'CTRL_A',
            'ctrl+a': 'CTRL_A',
            'ctrl a': 'CTRL_A',
            'CTRL_A': 'CTRL_A',
            
            'ctrl_x': 'CTRL_X',
            'ctrl+x': 'CTRL_X',
            'ctrl x': 'CTRL_X',
            'CTRL_X': 'CTRL_X',
            
            'ctrl_z': 'CTRL_Z',
            'ctrl+z': 'CTRL_Z',
            'ctrl z': 'CTRL_Z',
            'CTRL_Z': 'CTRL_Z',
            
            'ctrl_s': 'CTRL_S',
            'ctrl+s': 'CTRL_S',
            'ctrl s': 'CTRL_S',
            'CTRL_S': 'CTRL_S',
            
            'ctrl_f': 'CTRL_F',
            'ctrl+f': 'CTRL_F',
            'ctrl f': 'CTRL_F',
            'CTRL_F': 'CTRL_F',
        }
        
        # 记录原始键名用于调试
        original_key = key
        
        # 统一转为小写用于查找映射
        key_lower = key.lower()
        
        # 查找映射
        if key_lower in key_map:
            mapped_key = key_map[key_lower]
            print(f"🔑 按键映射: {original_key} -> {mapped_key}")
            return self.send_with_retry(f"PRESS {mapped_key}")
        
        # 如果没有映射，直接使用原键名（转为大写）
        key_upper = key.upper()
        print(f"🔑 按键: {key_upper} (无映射)")
        return self.send_with_retry(f"PRESS {key_upper}")
    
    def type_text(self, text):
        """
        输入文字
        
        参数:
            text: 要输入的文字
        
        返回:
            bool: 是否成功
        """
        if not text:
            return False
        
        # 处理特殊字符
        text = text.replace('"', '\\"')
        
        # 对于较长的文本，可能需要分段发送
        max_length = 50  # 每段最大长度
        if len(text) <= max_length:
            return self.send_with_retry(f'TYPE "{text}"')
        else:
            # 分段输入
            success = True
            for i in range(0, len(text), max_length):
                segment = text[i:i+max_length]
                if not self.send_with_retry(f'TYPE "{segment}"'):
                    success = False
                time.sleep(0.1)  # 短暂停顿
            return success
    
    # ========== 常用快捷键 ==========
    
    def press_enter(self):
        """按回车键"""
        return self.press_key("ENTER")
    
    def press_tab(self):
        """按Tab键"""
        return self.press_key("TAB")
    
    def press_space(self):
        """按空格键"""
        return self.press_key("SPACE")
    
    def press_backspace(self):
        """按退格键"""
        return self.press_key("BACKSPACE")
    
    def press_delete(self):
        """按删除键"""
        return self.press_key("DELETE")
    
    def press_esc(self):
        """按ESC键"""
        return self.press_key("ESC")
    
    def press_ctrl_c(self):
        """复制 (Ctrl+C)"""
        return self.press_key("CTRL_C")
    
    def press_ctrl_v(self):
        """粘贴 (Ctrl+V)"""
        return self.press_key("CTRL_V")
    
    def press_ctrl_x(self):
        """剪切 (Ctrl+X)"""
        return self.press_key("CTRL_X")
    
    def press_ctrl_a(self):
        """全选 (Ctrl+A)"""
        return self.press_key("CTRL_A")
    
    def press_ctrl_z(self):
        """撤销 (Ctrl+Z)"""
        return self.press_key("CTRL_Z")
    
    def press_ctrl_y(self):
        """重做 (Ctrl+Y)"""
        return self.press_key("CTRL_Y")
    
    def press_ctrl_s(self):
        """保存 (Ctrl+S)"""
        return self.press_key("CTRL_S")
    
    def press_ctrl_f(self):
        """查找 (Ctrl+F)"""
        return self.press_key("CTRL_F")
    
    def press_win_r(self):
        """打开运行对话框 (Win+R)"""
        return self.press_key("WIN_R")
    
    def press_win_d(self):
        """显示桌面 (Win+D)"""
        return self.press_key("WIN_D")
    
    def press_win_e(self):
        """打开资源管理器 (Win+E)"""
        return self.press_key("WIN_E")
    
    def press_alt_tab(self):
        """切换窗口 (Alt+Tab)"""
        return self.press_key("ALT_TAB")
    
    def press_alt_f4(self):
        """关闭当前窗口 (Alt+F4)"""
        return self.press_key("ALT_F4")
    
    def press_f1(self):
        """F1键"""
        return self.press_key("F1")
    
    def press_f2(self):
        """F2键"""
        return self.press_key("F2")
    
    def press_f3(self):
        """F3键"""
        return self.press_key("F3")
    
    def press_f4(self):
        """F4键"""
        return self.press_key("F4")
    
    def press_f5(self):
        """F5键"""
        return self.press_key("F5")
    
    # ========== 方向键 ==========
    
    def press_up(self):
        """上方向键"""
        return self.press_key("UP")
    
    def press_down(self):
        """下方向键"""
        return self.press_key("DOWN")
    
    def press_left(self):
        """左方向键"""
        return self.press_key("LEFT")
    
    def press_right(self):
        """右方向键"""
        return self.press_key("RIGHT")
    
    # ========== 鼠标操作 ==========
    
    def mouse_click(self, button='left'):
        """
        鼠标点击
        
        参数:
            button: 'left', 'right', 'middle'
        """
        btn_map = {'left': 1, 'right': 2, 'middle': 3}
        return self.send_with_retry(f"MOUSE_CLICK {btn_map.get(button, 1)}")
    
    def mouse_double_click(self):
        """鼠标双击"""
        return self.send_with_retry("MOUSE_DOUBLE_CLICK")
    
    def release_all(self):
        """释放所有按键"""
        return self.send_with_retry("RELEASE")
    
    # ========== 工具方法 ==========
    
    def test_connection(self):
        """测试连接状态"""
        if not self.connected or not self.serial:
            return False
        
        # 发送ping命令
        return self.send_command("RELEASE")
    
    def get_status_text(self):
        """获取状态文本（用于UI显示）"""
        if self.connected and self.port_name:
            return f"✅ 已连接 ({self.port_name})"
        else:
            return "❌ 未连接"
    
    def get_port_info(self):
        """获取端口信息"""
        if self.connected and self.port_name:
            return {
                'port': self.port_name,
                'description': self.port_description,
                'connected': True
            }
        else:
            return {
                'port': None,
                'description': None,
                'connected': False
            }
    
    def list_available_ports(self):
        """列出所有可用串口"""
        ports = serial.tools.list_ports.comports()
        result = []
        for port in ports:
            result.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return result
    
    def close(self):
        """关闭串口连接"""
        if self.serial:
            try:
                print("🔄 正在关闭ESP32连接...")
                self.release_all()  # 释放所有按键
                time.sleep(0.1)
                self.serial.close()
                print("✅ ESP32连接已关闭")
            except Exception as e:
                print(f"⚠️ 关闭连接时出错: {e}")
            finally:
                self.serial = None
                self.connected = False
                self.port_name = None
                self.port_description = None
    
    def __del__(self):
        """析构函数"""
        self.close()


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("🔧 ESP32键盘控制器测试")
    print("=" * 50)
    
    # 创建控制器
    kb = ESP32Keyboard()
    
    if kb.connected:
        print("\n✅ 连接成功，开始测试...")
        
        # 测试各种格式的Win+R
        print("\n📝 测试各种格式的Win+R:")
        print("1. press_key('WIN_R')")
        kb.press_key('WIN_R')
        time.sleep(2)
        
        print("\n2. press_key('win_r')")
        kb.press_key('win_r')
        time.sleep(2)
        
        print("\n3. press_key('win+r')")
        kb.press_key('win+r')
        time.sleep(2)
        
        print("\n4. press_win_r()")
        kb.press_win_r()
        time.sleep(2)
        
        print("\n✅ 测试完成")
    else:
        print("\n❌ 连接失败，请检查ESP32")
    
    # 关闭连接
    kb.close()