"""
主界面 - 小i的图形界面
提示词模板从外部文件 deepseek_instructions.txt 动态加载
添加120秒总超时控制
"""

VERSION = "1.2.0"

import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-features=LocalNetworkAccess"

import pyautogui
import pyperclip

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
from PySide6.QtWebEngineCore import QWebEnginePage
import sys
import time
import json
from datetime import datetime

from screen_recognizer import ScreenRecognizer
from code_executor import CodeExecutor
from wifi_keyboard import WiFiKeyboard


MODEL_CONFIGS = {
    "DeepSeek": {
        "url": "https://chat.deepseek.com",
        "template": "deepseek_instructions.txt",
        "input_selectors": [
            "textarea[placeholder*='DeepSeek']",
            "textarea[placeholder*='发送消息']",
            "textarea[class*='ds-scroll-area']",
            "textarea",
        ],
        "message_selectors": [
            ".ds-markdown",
            '[data-message-author="assistant"]',
            ".message-assistant",
            ".chat-message-assistant",
        ],
    },
    "千问": {
        "url": "https://www.qianwen.com/",
        "template": "deepseek_instructions.txt",
        "input_selectors": [
            "div[role='textbox'][data-placeholder='向千问提问']",
            "[data-slate-editor='true'][contenteditable='true']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
        ],
        "message_selectors": [
            "#qk-markdown-react",
            ".qk-markdown",
            ".message-item",
            ".chat-message",
            "div[class]",
        ],
    },
}


class XiaoIWindow(QMainWindow):
    """小i主窗口"""

    def __init__(self):
        super().__init__()

        print("🔄 初始化屏幕识别器...")
        self.recognizer = ScreenRecognizer("templates")

        print("🔄 初始化代码执行器...")
        self.code_executor = CodeExecutor(None, self.recognizer)

        # 初始化本地键盘控制器
        print("🔄 初始化键盘控制器...")
        self.esp32_kb = WiFiKeyboard()

        # 当前选择的模型
        self.current_model = "DeepSeek"

        self.setup_ui()

        # 轮询相关变量
        self.polling_timer = None
        self.polling_start_time = None
        self.initial_count = 0
        self.polling_timeout = 30
        self.polling_interval = 3000

        # 内容稳定检测相关变量
        self.stable_timer = None
        self.stable_start_time = None
        self.last_content_length = 0
        self.stable_check_count = 0
        self.stable_timeout = 120
        self.stable_interval = 3000

        # 总超时控制（120秒）
        self.global_timeout_timer = None
        self.global_timeout_seconds = 120

        # Program end 标记检测
        self.program_end_timer = None
        self.program_end_start_time = None

    def setup_ui(self):
        """设置界面布局（通过主布局边距实现上下横条）"""
        self.setWindowTitle(f"助手小i v{VERSION}")
        self.setMinimumSize(800, 600)

        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))

        # 设置全局浅色背景
        self.setStyleSheet("""
            QMainWindow {
                background-color: #edeef0;
            }
            QGroupBox {
                color: #333333;
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QTextEdit, QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas;
                font-size: 12px;
            }
            QTextEdit:focus, QLineEdit:focus {
                border: 2px solid #00b894;
            }
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00ce9a;
            }
            QPushButton:pressed {
                background-color: #008b74;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        # 关键修改：设置上下边距为3px，左右边距为0，使整个中央区域上下留出3px背景色横条
        main_layout.setContentsMargins(0, 3, 0, 3)
        main_layout.setSpacing(0)

        # ===== 左侧：DeepSeek网页（直接放入，无需额外容器） =====
        left_widget = QWidget()
        left_widget.setObjectName("leftWidget")
        left_widget.setStyleSheet("#leftWidget { background-color: #edeef0; }")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(MODEL_CONFIGS["DeepSeek"]["url"]))
        self.browser.setStyleSheet("border: none;")
        self.browser.page().setBackgroundColor(QColor(255, 255, 255))
        left_layout.addWidget(self.browser)

        # ===== 右侧：控制面板（注意：整体边距也会影响右侧） =====
        right_widget = QWidget()
        right_widget.setMaximumWidth(500)
        right_widget.setMinimumWidth(400)
        right_widget.setStyleSheet("background-color: #edeef0;")

        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # 任务输入
        task_group = QGroupBox("📝 任务输入")
        task_group.setFixedHeight(150)
        task_layout = QVBoxLayout()
        task_layout.setContentsMargins(9, 9, 9, 9)
        self.task_input = QTextEdit()
        self.task_input.setStyleSheet(
            "background-color: #ffffff; color: #333333; border: 1px solid #cccccc; border-radius: 4px; padding: 8px; font-family: Consolas; font-size: 12px;"
        )
        self.task_input.setPlaceholderText(
            "输入你想让电脑完成的任务... (Ctrl+Enter 发送)"
        )
        self.task_input.setText("打开计算器并计算 123*456")
        self.task_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.task_input.installEventFilter(self)
        task_layout.addWidget(self.task_input)
        task_group.setLayout(task_layout)

        # 操作控制
        btn_group = QGroupBox("🎮 操作控制")
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        # 模型选择
        model_select_layout = QHBoxLayout()
        model_select_label = QLabel("选择模型:")
        model_select_label.setStyleSheet("color: #333333; font-size: 13px;")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["DeepSeek", "千问"])
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QComboBox QAbstractItemView {
                color: #333333;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #888888;
                margin-right: 5px;
            }
        """)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_select_layout.addWidget(model_select_label)
        model_select_layout.addWidget(self.model_combo)
        model_select_layout.addStretch()
        btn_layout.addLayout(model_select_layout)

        self.send_btn = QPushButton("🚀 发送任务到DeepSeek")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 12px;
                border: 2px solid #FFFFFF;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #00ce9a;
                border: 2px solid #FFFF00;
            }
        """)
        self.send_btn.clicked.connect(self.send_task_to_deepseek)
        btn_layout.addWidget(self.send_btn)

        btn_group.setLayout(btn_layout)

        # 执行日志
        log_group = QGroupBox("📋 执行日志")
        log_layout = QVBoxLayout()

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(300)
        self.log_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.log_area.setStyleSheet("""
            background-color: #ffffff;
            color: #333333;
            font-family: 'Consolas';
            font-size: 12px;
            border: 1px solid #ccc;
        """)
        log_layout.addWidget(self.log_area)

        log_group.setLayout(log_layout)

        # 添加到右侧布局（顺序：日志、任务输入、操作控制）
        right_layout.addWidget(log_group)
        right_layout.addWidget(task_group)
        right_layout.addWidget(btn_group)

        main_layout.addWidget(left_widget, 7)
        main_layout.addWidget(right_widget, 3)

        self.log("=" * 60)
        self.log(f"🚀 小i智能助手已启动 v{VERSION}")
        self.log("⚡ 全自动模式：代码将自动执行（依赖 #Program start/end 标记）")
        self.log("=" * 60)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
        print(f"[{timestamp}] {message}")

    def on_model_changed(self, model):
        self.current_model = model
        config = MODEL_CONFIGS[model]
        self.browser.setUrl(QUrl(config["url"]))
        self.send_btn.setText(f"🚀 发送任务到{model}")
        self.log(f"🔄 已切换到 {model}，正在加载页面...")

    def load_prompt_template(self):
        config = MODEL_CONFIGS[self.current_model]
        template_file = config["template"]
        template_path = os.path.join(os.path.dirname(__file__), template_file)
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.log(f"📄 已加载提示词模板: {template_path}")
                return content
        except FileNotFoundError:
            self.log(f"❌ 错误：提示词文件 {template_path} 不存在，请检查文件")
            return None
        except Exception as e:
            self.log(f"❌ 读取提示词文件失败: {e}")
            return None

    def build_prompt(self, task):
        template = self.load_prompt_template()
        if template is None:
            return None
        return template.replace("{task}", task)

    # ---------- 总超时控制 ----------
    def start_global_timeout(self):
        """启动120秒总超时定时器"""
        self.stop_global_timeout()  # 先停止可能存在的旧定时器
        self.global_timeout_timer = QTimer()
        self.global_timeout_timer.setSingleShot(True)
        self.global_timeout_timer.timeout.connect(self.on_global_timeout)
        self.global_timeout_timer.start(self.global_timeout_seconds * 1000)
        self.log(f"⏱️ 启动总超时定时器（{self.global_timeout_seconds}秒）")

    def stop_global_timeout(self):
        """停止总超时定时器"""
        if self.global_timeout_timer:
            self.global_timeout_timer.stop()
            self.global_timeout_timer = None

    def on_global_timeout(self):
        """总超时触发时的处理"""
        self.log(
            f"❌ 超时：{self.global_timeout_seconds}秒内未获取到完整的代码（未检测到 #Program start 和 #Program end）"
        )
        self.stop_polling()
        self.stop_program_end_check()
        self.global_timeout_timer = None

    # ---------- 发送任务 ----------
    def send_task_to_deepseek(self):
        self.stop_polling()
        self.stop_program_end_check()
        self.stop_global_timeout()

        task = self.task_input.toPlainText().strip()
        if not task:
            self.log("❌ 请输入任务")
            return

        prompt = self.build_prompt(task)
        if prompt is None:
            return

        self.current_prompt = prompt
        self.log(f"📝 任务: {task}")

        # 千问和 DeepSeek 分开处理
        if self.current_model == "千问":
            self.send_task_qianwen(prompt)
        else:
            self.send_task_deepseek_js(prompt)

    # 千问: JS 注入 + pyautogui 发送
    def send_task_qianwen_js(self, prompt):
        config = MODEL_CONFIGS[self.current_model]
        selectors_js = [s.replace("'", "\\'") for s in config["input_selectors"]]

        self.log(f"🔍 正在通过JS自动填写并发送到{self.current_model}...")

        escaped_prompt = (
            prompt.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

        js_code = f"""
        (function() {{
            console.log('🔍 开始自动填写...');
            
            function waitForElement(selector, timeout) {{
                timeout = timeout || 10000;
                var start = Date.now();
                while (Date.now() - start < timeout) {{
                    var el = document.querySelector(selector);
                    if (el) return el;
                }}
                return null;
            }}

            try {{
                var inputBox = waitForElement('{selectors_js[0]}') 
                            || waitForElement('{selectors_js[1]}')
                            || waitForElement('{selectors_js[2]}')
                            || document.querySelector('{selectors_js[3]}');
                if (!inputBox) throw new Error('未找到输入框');
                console.log('✅ 找到输入框');

                inputBox.focus();
                
                inputBox.innerText = '{escaped_prompt}';
                inputBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
                inputBox.dispatchEvent(new Event('change', {{ bubbles: true }}));
                console.log('✅ 已插入文本');
                
                return {{ success: true }};
            }} catch (error) {{
                console.error('❌ 错误:', error.message);
                return {{ success: false, error: error.message }};
            }}
        }})();
        """

        def handle_js_result(result):
            self.log(f"📊 JS返回结果: {result}")
            time.sleep(0.5)
            pyautogui.press("enter")
            self.log(f"✅ 已发送任务到{self.current_model}")
            self.log("⏳ 正在等待回复...")

            self.get_initial_message_count()
            self.start_global_timeout()
            self.start_polling()

        self.browser.page().runJavaScript(js_code, handle_js_result)

    # DeepSeek: JS 注入
    def send_task_deepseek_js(self, prompt):
        config = MODEL_CONFIGS[self.current_model]
        selectors_js = [s.replace("'", "\\'") for s in config["input_selectors"]]

        self.log(f"🔍 正在通过JS自动填写并发送到{self.current_model}...")

        escaped_prompt = (
            prompt.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

        js_code = f"""
        (function() {{
            console.log('🔍 开始自动填写...');
            
            function waitForElement(selector, timeout) {{
                timeout = timeout || 10000;
                var start = Date.now();
                while (Date.now() - start < timeout) {{
                    var el = document.querySelector(selector);
                    if (el) return el;
                }}
                return null;
            }}

            try {{
                var inputBox = waitForElement('{selectors_js[0]}') 
                            || waitForElement('{selectors_js[1]}')
                            || waitForElement('{selectors_js[2]}')
                            || document.querySelector('{selectors_js[3]}');
                if (!inputBox) throw new Error('未找到输入框');
                console.log('✅ 找到输入框');

                inputBox.focus();
                inputBox.select();
                
                try {{
                    document.execCommand('insertText', false, '{escaped_prompt}');
                }} catch(e) {{
                    inputBox.value = '{escaped_prompt}';
                    inputBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputBox.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                console.log('✅ 已插入文本');

                var start = Date.now();
                while (Date.now() - start < 1000) {{}}

                var enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true
                }});
                inputBox.dispatchEvent(enterEvent);
                console.log('✅ 已按回车发送');
                
                return {{ success: true }};
            }} catch (error) {{
                console.error('❌ 错误:', error.message);
                return {{ success: false, error: error.message }};
            }}
        }})();
        """

        def handle_js_result(result):
            self.log(f"📊 JS返回结果: {result}")
            self.log(f"✅ 已发送任务到{self.current_model}")
            self.log("⏳ 正在等待回复...")

            self.get_initial_message_count()
            self.start_global_timeout()
            self.start_polling()

        self.browser.page().runJavaScript(js_code, handle_js_result)

    # 千问: 模板匹配 + pyautogui
    def send_task_qianwen(self, prompt):
        self.log("=" * 40)
        self.log("🚀 开始发送任务到千问")
        self.log("=" * 40)

        # 千问生成回复较慢，增加轮询超时
        original_timeout = self.polling_timeout
        self.polling_timeout = 60

        # ========== 步骤1: 全屏模板匹配直接找输入框 ==========
        self.log("📋 步骤1: 全屏模板匹配查找输入框...")
        input_thresholds = [0.15, 0.2, 0.25, 0.3]
        input_box = None

        for thresh in input_thresholds:
            self.log(f"  🔍 尝试阈值 {thresh}...")
            input_box = self.recognizer.find_template(
                "qianwen_input_box.jpeg", confidence=thresh
            )
            if input_box and "center" in input_box:
                self.log(
                    f"  ✅ 找到输入框! 位置: ({input_box['center'][0]}, {input_box['center'][1]}), 匹配度: {input_box['confidence']:.3f}"
                )
                break
            time.sleep(0.1)

        if not input_box or "center" not in input_box:
            self.log("❌ 步骤1失败: 未找到输入框")
            self.log("❌ 任务中止 - 无法定位输入框")
            return

        # 验证输入框匹配度
        if input_box["confidence"] < 0.4:
            self.log(
                f"❌ 步骤1失败: 输入框匹配度过低 ({input_box['confidence']:.3f} < 0.4)"
            )
            self.log("❌ 任务中止 - 输入框定位不准确")
            return

        # 鼠标移动到输入框中心
        input_cx, input_cy = input_box["center"]
        self.log(f"  🖱️  鼠标移动到输入框中心 ({input_cx}, {input_cy})...")
        pyautogui.moveTo(input_cx, input_cy)
        self.log("  ✅ 已移动到输入框中心")
        time.sleep(0.5)

        # ========== 步骤2: 连续点击三次激活输入框 ==========
        self.log(f"📋 步骤2: 连续点击三次激活输入框 ({input_cx}, {input_cy})...")
        pyautogui.click(input_cx, input_cy)
        time.sleep(0.2)
        pyautogui.click(input_cx, input_cy)
        time.sleep(0.2)
        pyautogui.click(input_cx, input_cy)
        self.log("  ✅ 已连续点击三次")
        time.sleep(0.5)

        # ========== 步骤3: 复制内容到剪贴板 ==========
        self.log("📋 步骤3: 复制内容到剪贴板...")
        pyperclip.copy(prompt)
        self.log(f"  ✅ 已复制 ({len(prompt)} 字符)")
        time.sleep(0.3)

        # ========== 步骤4: 粘贴内容 ==========
        self.log("📋 步骤4: 粘贴内容...")
        pyautogui.hotkey("ctrl", "v")
        self.log("  ✅ 已粘贴内容")
        time.sleep(0.3)

        # ========== 步骤5: 发送消息 ==========
        self.log("📋 步骤5: 发送消息...")
        pyautogui.press("enter")
        self.log("  ✅ 已按回车发送")

        self.log("=" * 40)
        self.log(f"✅ 任务发送完成到 {self.current_model}")
        self.log("⏳ 正在等待回复...")
        self.log("=" * 40)

        self.get_initial_message_count()
        self.start_global_timeout()
        self.start_polling()

        # 恢复默认轮询超时
        self.polling_timeout = original_timeout

    # ---------- 轮询、稳定检测、提取等 ----------
    def get_initial_message_count(self):
        config = MODEL_CONFIGS[self.current_model]
        msg_selectors = config["message_selectors"]
        msg_selectors_js = "[" + ",".join([f"'{s}'" for s in msg_selectors]) + "]"

        js = f"""
        (function() {{
            const selectors = {msg_selectors_js};
            for (let selector of selectors) {{
                let elements = document.querySelectorAll(selector);
                if (elements.length > 0) {{
                    return elements.length;
                }}
            }}
            return 0;
        }})();
        """

        def callback(count):
            self.initial_count = count
            self.log(f"📊 当前助手消息数量: {count}")

        self.browser.page().runJavaScript(js, callback)

    def start_polling(self):
        self.polling_start_time = time.time()
        if self.polling_timer is None:
            self.polling_timer = QTimer()
            self.polling_timer.timeout.connect(self.check_new_message)
            self.polling_timer.setSingleShot(False)
            self.polling_timer.start(self.polling_interval)
            self.log(
                f"⏱️ 开始轮询新消息 (间隔{self.polling_interval // 1000}秒，超时{self.polling_timeout}秒)"
            )

    def stop_polling(self):
        if self.polling_timer:
            self.polling_timer.stop()
            self.polling_timer = None
            self.polling_start_time = None

    def check_new_message(self):
        config = MODEL_CONFIGS[self.current_model]
        msg_selectors = config["message_selectors"]
        msg_selectors_js = "[" + ",".join([f"'{s}'" for s in msg_selectors]) + "]"

        js = f"""
        (function() {{
            try {{
                const selectors = {msg_selectors_js};
                for (let selector of selectors) {{
                    let elements = document.querySelectorAll(selector);
                    if (elements && elements.length > 0) {{
                        let last = elements[elements.length - 1];
                        let text = '';
                        if (last.innerText) text = last.innerText;
                        else if (last.textContent) text = last.textContent;
                        else text = '';
                        return JSON.stringify({{
                            count: elements.length,
                            content: text,
                            selector: selector
                        }});
                    }}
                }}
                return JSON.stringify({{count: 0, content: '', selector: 'none'}});
            }} catch(e) {{
                return JSON.stringify({{error: e.message, count: 0, content: ''}});
            }}
        }})();
        """

        def callback(result):
            if self.polling_start_time is None:
                return

            if not isinstance(result, str):
                self.log(f"⚠️ 轮询返回异常: {type(result)} - {str(result)[:100]}")
                return

            try:
                data = json.loads(result)
            except:
                self.log(f"⚠️ JSON解析失败: {result[:100]}")
                return

            if "error" in data:
                self.log(f"⚠️ JS错误: {data['error']}")
                return

            current_count = data.get("count", 0)
            content = data.get("content", "")
            elapsed = time.time() - self.polling_start_time

            if elapsed > self.polling_timeout:
                self.log("⏰ 轮询超时，尝试提取最后一条消息")
                self.stop_polling()
                self.extract_last_message()
                return

            if "#Program end" in content:
                self.log("✅ 检测到 #Program end 标记，回复已完成")
                self.stop_polling()
                self.extract_last_message()
                return

            if current_count > self.initial_count:
                self.log(
                    f"✅ 检测到新消息 (数量: {current_count} > {self.initial_count})"
                )
                self.log("⏳ 等待 #Program end 标记...")

        self.browser.page().runJavaScript(js, callback)

    def start_program_end_check(self):
        self.log("🔍 开始检测 #Program end 标记...")
        self.program_end_start_time = time.time()
        self.check_program_end_marker()

    def stop_program_end_check(self):
        if self.program_end_timer:
            self.program_end_timer.stop()
            self.program_end_timer = None
        self.program_end_start_time = None

    def check_program_end_marker(self):
        config = MODEL_CONFIGS[self.current_model]
        msg_selectors = config["message_selectors"]
        msg_selectors_js = "[" + ",".join([f"'{s}'" for s in msg_selectors]) + "]"

        js = f"""
        (function() {{
            const selectors = {msg_selectors_js};
            for (let selector of selectors) {{
                let elements = document.querySelectorAll(selector);
                if (elements.length > 0) {{
                    let last = elements[elements.length - 1];
                    let text = last.innerText || last.textContent || '';
                    return text;
                }}
            }}
            return '';
        }})();
        """

        def callback(content):
            if self.program_end_start_time is None:
                return

            elapsed = time.time() - self.program_end_start_time
            if elapsed > self.stable_timeout:
                self.log(
                    f"⏰ 检测超时（{self.stable_timeout}秒），未找到 #Program end 标记"
                )
                self.stop_program_end_check()
                self.extract_last_message()
                return

            if content and "#Program end" in content:
                self.log("✅ 检测到 #Program end 标记，回复已完成")
                self.stop_program_end_check()
                self.extract_last_message()
            else:
                self.log("⏳ 等待 #Program end 标记...")
                if (
                    not hasattr(self, "program_end_timer")
                    or self.program_end_timer is None
                ):
                    self.program_end_timer = QTimer()
                    self.program_end_timer.timeout.connect(
                        self.check_program_end_marker
                    )
                    self.program_end_timer.start(self.stable_interval)

        self.browser.page().runJavaScript(js, callback)

    def extract_last_message(self):
        config = MODEL_CONFIGS[self.current_model]
        msg_selectors = config["message_selectors"]
        msg_selectors_js = "[" + ",".join([f"'{s}'" for s in msg_selectors]) + "]"

        js = f"""
        (function() {{
            const selectors = {msg_selectors_js};
            for (let selector of selectors) {{
                let elements = document.querySelectorAll(selector);
                if (elements.length > 0) {{
                    let last = elements[elements.length - 1];
                    return last.innerText || last.textContent;
                }}
            }}
            return '';
        }})();
        """

        def handle_content(content):
            # 无论成功与否，停止总超时
            self.stop_global_timeout()

            if content and len(content.strip()) > 0:
                self.log(f"📥 成功提取到回复，长度: {len(content)} 字符")

                if self.current_model == "千问":
                    result = self.code_executor.process_qianwen_reply(content)
                else:
                    result = self.code_executor.process_deepseek_reply(content)

                if result and result.get("success"):
                    if result.get("act_file"):
                        self.log(f"📁 代码已保存: {result['act_file']}")
                        self.log("⚡ 正在自动执行代码...")
                        self.execute_act_file(result["act_file"])
                    else:
                        self.log("⚠️ 代码提取成功但保存失败")
                else:
                    error_msg = (
                        result.get("error", "未知错误") if result else "处理失败"
                    )
                    self.log(f"❌ 处理失败: {error_msg}")
                    if result and result.get("reply_file"):
                        self.log(f"📁 原始回复已保存: {result['reply_file']}")
            else:
                self.log("❌ 提取到的内容为空")

        self.browser.page().runJavaScript(js, handle_content)

    def execute_act_file(self, act_file, timeout=60):
        """执行 act.py 文件（与原来相同）"""
        try:
            self.log("🚀 正在自动执行生成的代码...")
            self.log(f"📁 执行文件: {act_file}")
            self.log(f"⏱️ 超时设置: {timeout}秒")

            if not os.path.exists(act_file):
                self.log(f"❌ 文件不存在: {act_file}")
                return False

            import subprocess
            import sys
            import threading
            import queue

            python_exe = sys.executable
            output_queue = queue.Queue()

            def run_subprocess():
                try:
                    if sys.platform == "win32":
                        process = subprocess.Popen(
                            [python_exe, act_file],
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            bufsize=1,
                        )
                    else:
                        process = subprocess.Popen(
                            [python_exe, act_file],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            bufsize=1,
                        )

                    try:
                        stdout, stderr = process.communicate(timeout=timeout)
                        output_queue.put(
                            ("success", stdout, stderr, process.returncode)
                        )
                    except subprocess.TimeoutExpired:
                        process.kill()
                        output_queue.put(("timeout", "", "", -1))
                except Exception as e:
                    output_queue.put(("error", "", str(e), -1))

            if sys.platform == "win32":
                thread = threading.Thread(target=run_subprocess)
                thread.start()
                self.log("✅ 已在新窗口中启动执行")
                self.log("ℹ️ 请查看新打开的窗口查看执行结果")

                thread.join(timeout + 5)

                if thread.is_alive():
                    self.log(f"⚠️ 执行超时（{timeout}秒），已强制终止")
                    return False

                try:
                    status, stdout, stderr, returncode = output_queue.get_nowait()
                    if status == "timeout":
                        self.log(f"⏰ 执行超时（{timeout}秒）")
                        return False
                    elif status == "error":
                        self.log(f"❌ 执行出错: {stderr}")
                        return False
                    else:
                        if stdout:
                            self.log(f"📤 执行输出:\n{stdout}")
                        if stderr:
                            self.log(f"⚠️ 执行错误:\n{stderr}")
                        if returncode == 0:
                            self.log("✅ 代码执行成功完成")
                            return True
                        else:
                            self.log(f"❌ 代码执行失败，返回码: {returncode}")
                            return False
                except queue.Empty:
                    self.log("⏳ 代码正在执行中...")
                    return True
            else:
                run_subprocess()
                return True

        except Exception as e:
            self.log(f"❌ 执行失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def eventFilter(self, obj, event):
        if obj == self.task_input and event.type() == QEvent.Type.KeyPress:
            if (
                event.key() == Qt.Key.Key_Return
                and event.modifiers() == Qt.KeyboardModifier.ControlModifier
            ):
                self.send_task_to_deepseek()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self.stop_polling()
        self.stop_program_end_check()
        self.stop_global_timeout()
        self.log("🔄 正在关闭程序...")
        event.accept()


def main():
    try:
        app = QApplication(sys.argv)
        font = QFont("Microsoft YaHei", 9)
        app.setFont(font)
        window = XiaoIWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"❌ 程序启动失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
