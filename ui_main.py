"""
主界面 - 小i的图形界面
提示词模板从外部文件 deepseek_instructions.txt 动态加载
添加120秒总超时控制
"""

VERSION = "1.0.0"

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWebEngineWidgets import *
import sys
import os
import time
import pyperclip
from datetime import datetime

from screen_recognizer import ScreenRecognizer
from code_executor import CodeExecutor
from wifi_keyboard import WiFiKeyboard


class XiaoIWindow(QMainWindow):
    """小i主窗口"""

    def __init__(self):
        super().__init__()

        print(f"🔄 初始化版本: {VERSION}")
        print("🔄 初始化屏幕识别器...")
        self.recognizer = ScreenRecognizer("templates")

        print("🔄 初始化代码执行器...")
        self.code_executor = CodeExecutor(None, self.recognizer)

        # 初始化本地键盘控制器
        print("🔄 初始化键盘控制器...")
        self.esp32_kb = WiFiKeyboard()

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

    def setup_ui(self):
        """设置界面布局（通过主布局边距实现上下横条）"""
        self.setWindowTitle(f"助手小i v{VERSION}")
        self.setMinimumSize(800, 600)

        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))

        # 设置全局深色背景
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252525;
            }
            QGroupBox {
                color: #00b894;
                font-weight: bold;
                border: 2px solid #444444;
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
                color: #cccccc;
                font-size: 13px;
            }
            QTextEdit, QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444444;
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
        left_widget.setStyleSheet("#leftWidget { background-color: #252525; }")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        self.browser.setStyleSheet("border: none;")
        # 设置网页背景色为深色（需 Qt ≥5.13）
        self.browser.page().setBackgroundColor(QColor(37, 37, 37))
        left_layout.addWidget(self.browser)

        # ===== 右侧：控制面板（注意：整体边距也会影响右侧） =====
        right_widget = QWidget()
        right_widget.setMaximumWidth(500)
        right_widget.setMinimumWidth(400)
        right_widget.setStyleSheet(
            "background-color: #252525; border-left: 2px solid #444;"
        )

        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # 任务输入
        task_group = QGroupBox("📝 任务输入")
        task_group.setFixedHeight(150)
        task_layout = QVBoxLayout()
        task_layout.setContentsMargins(9, 9, 9, 9)
        self.task_input = QTextEdit()
        self.task_input.setPlaceholderText(
            "输入你想让电脑完成的任务... (Ctrl+Enter 发送)"
        )
        self.task_input.setText("打开计算器并计算 123*456")
        self.task_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.task_input.installEventFilter(self)
        task_layout.addWidget(self.task_input)
        task_group.setLayout(task_layout)
        right_layout.addWidget(task_group)

        # 操作控制
        btn_group = QGroupBox("🎮 操作控制")
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

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
        right_layout.addWidget(btn_group)

        # 执行日志
        log_group = QGroupBox("📋 执行日志")
        log_layout = QVBoxLayout()

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(300)
        self.log_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_area.setStyleSheet("""
            background-color: #1a1a1a;
            color: #00ff00;
            font-family: 'Consolas';
            font-size: 12px;
            border: 1px solid #444;
        """)
        log_layout.addWidget(self.log_area)

        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)

        main_layout.addWidget(left_widget, 7)
        main_layout.addWidget(right_widget, 3)

        self.log("=" * 60)
        self.log("🚀 小i智能助手已启动")
        self.log("⚡ 全自动模式：代码将自动执行（依赖 #Program start/end 标记）")
        self.log("=" * 60)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
        print(f"[{timestamp}] {message}")

    def load_prompt_template(self):
        template_path = os.path.join(
            os.path.dirname(__file__), "deepseek_instructions.txt"
        )
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
        self.stop_stable_check()
        self.global_timeout_timer = None

    # ---------- 发送任务 ----------
    def send_task_to_deepseek(self):
        self.stop_polling()
        self.stop_stable_check()
        self.stop_global_timeout()

        task = self.task_input.toPlainText().strip()
        if not task:
            self.log("❌ 请输入任务")
            return

        prompt = self.build_prompt(task)
        if prompt is None:
            return

        self.log(f"📝 任务: {task}")
        self.log("🔍 正在通过JS自动填写并发送...")

        escaped_prompt = (
            prompt.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )

        js_code = f"""
        (function() {{
            console.log('========== JS注入开始 ==========');
            console.log('Step 0: JS代码开始执行');
            
            var result = {{
                foundInput: false,
                insertedText: false,
                sentMessage: false,
                inputValue: '',
                error: null,
                debugLog: []
            }};
            
            function log(msg) {{
                console.log(msg);
                result.debugLog.push(msg);
            }}
            
            function waitForElement(selector, timeout) {{
                timeout = timeout || 10000;
                var start = Date.now();
                log('等待元素: ' + selector);
                while (Date.now() - start < timeout) {{
                    var el = document.querySelector(selector);
                    if (el) {{
                        log('找到元素: ' + selector);
                        return el;
                    }}
                }}
                log('未找到元素: ' + selector);
                return null;
            }}
            
            function sleep(ms) {{
                var start = Date.now();
                while (Date.now() - start < ms) {{ }}
            }}

            try {{
                log('Step 1: 查找输入框');
                
                // 1. 等待输入框出现 - 多种可能的选择器
                var selectors = [
                    'textarea[placeholder*="DeepSeek"]',
                    'textarea[placeholder*="发送消息"]',
                    'textarea[class*="ds-textarea"]',
                    'textarea'
                ];
                
                var inputBox = null;
                for (var i = 0; i < selectors.length; i++) {{
                    inputBox = document.querySelector(selectors[i]);
                    if (inputBox) {{
                        log('找到输入框，使用选择器: ' + selectors[i]);
                        break;
                    }}
                }}
                
                if (!inputBox) {{
                    result.error = '未找到输入框';
                    log('❌ 未找到输入框');
                    console.log('========== JS注入结束 (失败) ==========');
                    return result;
                }}
                result.foundInput = true;
                log('✅ 找到输入框');

                // 2. 聚焦并插入文本
                log('Step 2: 聚焦输入框');
                inputBox.focus();
                inputBox.select();
                inputBox.value = '';
                sleep(100);
                
                log('Step 3: 插入文本');
                // 尝试多种插入方式
                var insertSuccess = false;
                
                // 方式1: try execCommand
                try {{
                    var cmdResult = document.execCommand('insertText', false, '{escaped_prompt}');
                    log('execCommand 结果: ' + cmdResult);
                }} catch(e) {{
                    log('execCommand 错误: ' + e.message);
                }}
                
                // 方式2: 直接赋值
                inputBox.value = '{escaped_prompt}';
                inputBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
                inputBox.dispatchEvent(new Event('change', {{ bubbles: true }}));
                
                sleep(300);
                
                // 验证文本是否真的插入成功
                var currentValue = inputBox.value || '';
                log('输入框当前值长度: ' + currentValue.length);
                
                if (currentValue.length > 0) {{
                    result.insertedText = true;
                    result.inputValue = currentValue.substring(0, 100);
                    log('✅ 文本插入成功，长度: ' + currentValue.length);
                }} else {{
                    result.error = '文本插入失败，输入框为空';
                    log('❌ 文本插入失败');
                    console.log('========== JS注入结束 (失败) ==========');
                    return result;
                }}

                log('Step 4: 等待发送按钮');
                sleep(1500);

                log('Step 5: 发送消息');
                // 发送消息 - 使用回车键
                var enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true
                }});
                inputBox.dispatchEvent(enterEvent);
                log('已发送回车键事件');
                
                sleep(1000);
                
                // 验证发送：检查输入框是否被清空
                var afterSendValue = inputBox.value || '';
                log('发送后输入框长度: ' + afterSendValue.length);
                
                if (afterSendValue.length === 0 || afterSendValue !== result.inputValue) {{
                    result.sentMessage = true;
                    log('✅ 消息发送成功');
                }} else {{
                    result.error = '消息发送失败，输入框未被清空';
                    log('❌ 消息发送失败');
                }}
                
                log('========== JS注入结束 ==========');
                
                return {{ 
                    success: result.sentMessage, 
                    foundInput: result.foundInput,
                    insertedText: result.insertedText,
                    sentMessage: result.sentMessage,
                    inputValue: result.inputValue,
                    debugLog: result.debugLog,
                    error: result.error
                }};
            }} catch (error) {{
                log('❌ 异常: ' + error.message);
                console.log('========== JS注入结束 (异常) ==========');
                return {{ 
                    success: false, 
                    error: error.message,
                    foundInput: result.foundInput,
                    insertedText: result.insertedText,
                    sentMessage: result.sentMessage,
                    debugLog: result.debugLog
                }};
            }}
        }})();
        """

        def handle_js_result(result):
            # 输出详细的 JS 返回结果
            self.log("📊 JS注入状态报告:")
            
            fail_reason = "未知错误"  # 初始化变量
            js_success = False
            
            if result is None or result == "" or result == False:
                # JS 返回为空，但可能是 WebEngine 回调问题
                # 根据用户反馈，JS 实际已执行成功
                self.log("   ⚠️ 未收到JS返回值（WebEngine回调问题）")
                self.log("   ℹ️ 假设JS已执行成功，继续等待回复...")
                self.get_initial_message_count()
                self.start_global_timeout()
                self.start_polling()
                return
            
            if isinstance(result, dict):
                # 详细输出每一步的状态
                debug_log = result.get("debugLog", [])
                found = result.get("foundInput", False)
                inserted = result.get("insertedText", False)
                sent = result.get("sentMessage", False)
                success = result.get("success", False)
                error = result.get("error", "")
                input_val = result.get("inputValue", "")
                
                # 输出调试日志
                if debug_log:
                    self.log("   📝 执行步骤:")
                    for log_msg in debug_log[:10]:  # 只显示前10条
                        self.log(f"      {log_msg}")
                
                self.log(f"   🔍 找到输入框: {'✅ 是' if found else '❌ 否'}")
                self.log(f"   ✍️ 填入信息: {'✅ 是' if inserted else '❌ 否'}")
                if inserted and input_val:
                    self.log(f"   📝 输入内容: {input_val[:50]}...")
                self.log(f"   ⏎ 按下回车: {'✅ 是' if sent else '❌ 否'}")
                
                if error:
                    self.log(f"   ❌ 错误信息: {error}")
                
                # 综合判断
                if success and found and inserted and sent:
                    js_success = True
                else:
                    js_success = False
                    if not found:
                        fail_reason = "未找到DeepSeek输入框"
                    elif not inserted:
                        fail_reason = "文本未能填入输入框"
                    elif not sent:
                        fail_reason = "未能成功发送（按回车无效）"
                    else:
                        fail_reason = error or "未知错误"
            else:
                self.log(f"   ⚠️ 未知返回类型: {type(result)}")
                js_success = False
                fail_reason = "JS返回类型异常"
            
            if js_success:
                self.log("✅ JS注入流程全部成功")
                self.log("⏳ 正在等待DeepSeek回复...")
                self.get_initial_message_count()
                self.start_global_timeout()
                self.start_polling()
            else:
                self.log(f"⚠️ JS注入失败: {fail_reason}")
                self.log("🔄 尝试降级方案：屏幕模板匹配...")
                self.fallback_to_template_matching()

        self.browser.page().runJavaScript(js_code, handle_js_result)

    # ---------- 验证网页状态 ----------
    def verify_and_continue(self):
        """验证网页状态，判断 JS 是否发送成功"""
        verify_js = """
        (function() {
            var selectors = [
                'textarea[placeholder*="DeepSeek"]',
                'textarea[placeholder*="发送消息"]',
                'textarea[class*="ds-scroll-area"]',
                'textarea'
            ];
            
            var inputBox = null;
            for (var i = 0; i < selectors.length; i++) {
                inputBox = document.querySelector(selectors[i]);
                if (inputBox) break;
            }
            
            if (!inputBox) {
                return { success: false, error: "未找到输入框" };
            }
            
            var value = inputBox.value || "";
            
            // 检查是否已经有助手回复
            var messageSelectors = ['.ds-markdown', '[data-message-author="assistant"]', '.message-assistant'];
            var hasReply = false;
            for (var i = 0; i < messageSelectors.length; i++) {
                var msgs = document.querySelectorAll(messageSelectors[i]);
                if (msgs && msgs.length > 0) {
                    hasReply = true;
                    break;
                }
            }
            
            // 如果输入框被清空或有回复，说明发送成功
            var sent = (value.length === 0) || hasReply;
            
            return {
                success: sent,
                inputValue: value,
                inputEmpty: value.length === 0,
                hasReply: hasReply,
                error: sent ? null : "无法确认消息是否发送"
            };
        })();
        """
        
        def handle_verify(result):
            if isinstance(result, dict) and result.get("success", False):
                self.log("✅ JS注入成功（通过网页状态验证）")
                if result.get("hasReply"):
                    self.log("💬 检测到已有回复")
                self.log("⏳ 正在等待DeepSeek回复...")
                self.get_initial_message_count()
                self.start_global_timeout()
                self.start_polling()
            else:
                self.log("⚠️ JS注入可能失败，降级到模板匹配...")
                self.fallback_to_template_matching()
        
        self.browser.page().runJavaScript(verify_js, handle_verify)

    # ---------- 降级方案：屏幕模板匹配 ----------
    def fallback_to_template_matching(self):
        """JS注入失败时，使用屏幕模板匹配来查找并点击输入框"""
        try:
            self.log("🔍 正在通过屏幕模板匹配查找DeepSeek输入框...")
            
            # 查找输入框位置
            location = self.recognizer.find_deepseek_inputbox()
            
            if location:
                self.log(f"✅ 找到输入框，位置: {location['center']}")
                x, y = location['center']
                
                # 点击输入框聚焦
                self.log("🖱️ 点击输入框...")
                self.esp32_kb.mouse_click(x, y)
                time.sleep(0.5)
                
                # 构建提示词
                task = self.task_input.toPlainText().strip()
                prompt = self.build_prompt(task)
                
                if prompt:
                    # 粘贴提示词
                    self.log("📋 粘贴提示词...")
                    pyperclip.copy(prompt)
                    time.sleep(0.3)
                    self.esp32_kb.press_ctrl_v()
                    time.sleep(0.5)
                    
                    # 发送消息（按回车）
                    self.log("⏎ 发送消息...")
                    self.esp32_kb.press_enter()
                    
                    self.log("✅ 已通过模板匹配发送任务")
                    self.log("⏳ 正在等待DeepSeek回复...")
                    
                    self.get_initial_message_count()
                    self.start_global_timeout()
                    self.start_polling()
                    return
            
            self.log("❌ 模板匹配也未能找到输入框")
            self.log("💡 请确保：")
            self.log("   1. DeepSeek网页已打开")
            self.log("   2. templates文件夹中有input_box.jpeg模板")
            
        except Exception as e:
            self.log(f"❌ 降级方案失败: {e}")
            import traceback
            traceback.print_exc()

    # ---------- 轮询、稳定检测、提取等（原有逻辑不变）----------
    def get_initial_message_count(self):
        js = """
        (function() {
            const selectors = [
                '.ds-markdown',
                '[data-message-author="assistant"]',
                '.message-assistant',
                '.chat-message-assistant'
            ];
            for (let selector of selectors) {
                let elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    return elements.length;
                }
            }
            return 0;
        })();
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
        js = """
        (function() {
            const selectors = [
                '.ds-markdown',
                '[data-message-author="assistant"]',
                '.message-assistant',
                '.chat-message-assistant'
            ];
            for (let selector of selectors) {
                let elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    return elements.length;
                }
            }
            return 0;
        })();
        """

        def callback(current_count):
            elapsed = time.time() - self.polling_start_time
            if elapsed > self.polling_timeout:
                self.log("⏰ 轮询超时，尝试提取最后一条消息")
                self.stop_polling()
                self.extract_last_message()
                return

            if current_count > self.initial_count:
                self.log(
                    f"✅ 检测到新消息 (数量: {current_count} > {self.initial_count})"
                )
                self.stop_polling()
                self.start_content_stable_check()

        self.browser.page().runJavaScript(js, callback)

    def start_content_stable_check(self):
        self.log("📈 开始内容稳定检测...")
        self.stable_start_time = time.time()
        self.last_content_length = 0
        self.stable_check_count = 0
        self.get_current_content_length()
        if self.stable_timer is None:
            self.stable_timer = QTimer()
            self.stable_timer.timeout.connect(self.check_content_stability)
            self.stable_timer.start(self.stable_interval)

    def stop_stable_check(self):
        if self.stable_timer:
            self.stable_timer.stop()
            self.stable_timer = None
        self.stable_start_time = None
        self.last_content_length = 0
        self.stable_check_count = 0

    def get_current_content_length(self):
        js = """
        (function() {
            const selectors = [
                '.ds-markdown',
                '[data-message-author="assistant"]',
                '.message-assistant',
                '.chat-message-assistant'
            ];
            for (let selector of selectors) {
                let elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    let last = elements[elements.length - 1];
                    let text = last.innerText || last.textContent;
                    return text ? text.length : 0;
                }
            }
            return 0;
        })();
        """

        def callback(length):
            current_length = length
            elapsed = time.time() - self.stable_start_time
            if elapsed > self.stable_timeout:
                self.log(f"⏰ 稳定检测超时 ({self.stable_timeout}秒)，直接提取当前内容")
                self.stop_stable_check()
                self.extract_last_message()
                return

            if self.last_content_length == 0:
                self.last_content_length = current_length
                self.log(f"📏 初始内容长度: {current_length}")
                return

            if current_length == self.last_content_length:
                self.stable_check_count += 1
                self.log(
                    f"📏 内容长度稳定 ({current_length})，连续 {self.stable_check_count} 次"
                )
                if self.stable_check_count >= 2:
                    self.log("✅ 内容已稳定，准备提取")
                    self.stop_stable_check()
                    self.extract_last_message()
            else:
                self.stable_check_count = 0
                self.last_content_length = current_length
                self.log(f"📏 内容长度变化: {current_length}")

        self.browser.page().runJavaScript(js, callback)

    def check_content_stability(self):
        self.get_current_content_length()

    def extract_last_message(self):
        js = """
        (function() {
            const selectors = [
                '.ds-markdown',
                '[data-message-author="assistant"]',
                '.message-assistant',
                '.chat-message-assistant'
            ];
            for (let selector of selectors) {
                let elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    let last = elements[elements.length - 1];
                    return last.innerText || last.textContent;
                }
            }
            return '';
        })();
        """

        def handle_content(content):
            # 无论成功与否，停止总超时
            self.stop_global_timeout()

            if content and len(content.strip()) > 0:
                self.log(f"📥 成功提取到回复，长度: {len(content)} 字符")
                # 直接使用提取到的内容（可能包含代码块标记，但code_executor会处理）
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
        self.stop_stable_check()
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
