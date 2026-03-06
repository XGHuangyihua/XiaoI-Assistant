# 小i智能助手 (XiaoI Assistant)

一个基于 DeepSeek AI 的桌面智能助手，能够自动执行各种电脑操作任务。

## 功能介绍

### 核心功能

1. **AI 任务执行**
   - 通过 DeepSeek AI 理解用户自然语言任务
   - 自动生成并执行 Python 代码完成指定任务
   - 支持 `#Program start` 和 `#Program end` 标记的代码提取

2. **屏幕识别**
   - 基于 OpenCV 的模板匹配技术
   - 多尺度匹配，提高识别准确率
   - 支持自定义模板图片 (`templates` 文件夹)

3. **键鼠控制**
   - 使用 pyautogui 实现自动化操作
   - 支持键盘按键、文本输入、鼠标点击/移动/滚动
   - 剪贴板输入，解决中文输入问题

4. **语音合成** (可选)
   - 支持 Microsoft Edge TTS 语音输出

### 应用场景

- 自动化打开应用程序
- 文件管理操作
- 数据录入与处理重复
- 性任务自动化

## 环境要求

- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.8 或更高版本
- **依赖**: 见 `requirements.txt`

## 安装步骤

### 1. 安装 Python

如果尚未安装 Python，请按以下步骤操作：

#### 方法一：官网下载（推荐）

1. 访问 Python 官网：https://www.python.org/downloads/
2. 下载最新版本的 Python (建议 3.10 或更高版本)
3. **重要**: 安装时勾选 `Add Python to PATH`
4. 点击 `Install Now` 完成安装

#### 方法二：Microsoft Store

1. 打开 Microsoft Store
2. 搜索 "Python"
3. 安装 Python 3.x 版本

#### 验证安装

打开命令提示符 (Win + R，输入 `cmd`)，输入：

```bash
python --version
```

应显示 Python 版本号，例如 `Python 3.10.x`

### 2. 克隆或下载项目

```bash
git clone https://github.com/你的用户名/xiao-i-assistant.git
cd xiao-i-assistant
```

或者直接下载 ZIP 压缩包并解压。

### 3. 创建虚拟环境（推荐）

```bash
python -m venv venv
```

激活虚拟环境：

```bash
# Windows
venv\Scripts\activate
```

激活成功后，命令行前会显示 `(venv)`。

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

如果安装失败，尝试：

```bash
# 升级 pip
python -m pip install --upgrade pip

# 单独安装每个依赖
pip install PySide6
pip install requests
pip install pyautogui
# ... 等等
```

### 5. 安装 WebEngine 依赖 (PySide6)

PySide6 WebEngine 需要额外的运行时支持：

```bash
# Windows
pip install PySide6-Addons
```

## 使用方法

### 1. 启动程序

在项目目录下运行：

```bash
python main.py
```

或：

```bash
python ui_main.py
```

### 2. 主界面说明

程序启动后，您将看到主界面：

- **左侧**: DeepSeek 网页聊天界面
- **右侧**: 控制面板

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   DeepSeek 聊天界面                                 │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│  📝 任务输入                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ 输入你想让电脑完成的任务...                  │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [🚀 发送任务到DeepSeek]                            │
│                                                     │
│  📋 执行日志                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ [12:30:15] 小i智能助手已启动                │   │
│  │ [12:30:20] 任务: 打开计算器                 │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 3. 使用流程

1. 在 **任务输入框** 中输入您想让电脑完成的任务
2. 点击 **发送任务到DeepSeek** 按钮（或按 Ctrl+Enter）
3. 程序会自动：
   - 将任务发送给 DeepSeek AI
   - 等待 AI 生成代码
   - 提取代码（通过 `#Program start` 和 `#Program end` 标记）
   - 自动执行代码

### 4. 代码格式要求

确保 DeepSeek 返回的代码包含以下标记：

```python
#Program start
# 你的代码
#Program end
```

代码必须导入必要的模块：

```python
import pyautogui
import time
import pyperclip
import ctypes
```

### 5. 示例任务

- "打开计算器并计算 123*456"
- "打开记事本并输入 Hello World"
- "打开浏览器访问百度"
- "新建一个文件夹并命名为 test"

## 项目结构

```
XiaoI_Project/
├── main.py                 # 主程序入口
├── ui_main.py             # 主界面
├── screen_recognizer.py   # 屏幕识别器
├── code_executor.py       # 代码执行器
├── wifi_keyboard.py       # 键鼠控制器
├── requirements.txt       # Python 依赖
├── templates/             # 模板图片目录
│   └── input_box.jpeg     # 输入框模板
├── generated/             # 生成的代码目录
│   ├── act.py            # 执行的代码
│   └── reply.py          # AI 原始回复
├── deepseek_instructions.txt  # AI 提示词模板
└── README.md             # 本文件
```

## 常见问题

### 1. 导入错误

**问题**: `ImportError: No module named 'PySide6'`

**解决**:
```bash
pip install PySide6 PySide6-Addons PySide6-WebEngine
```

### 2. 截图失败

**问题**: 屏幕识别器无法截图

**解决**: 确保程序有屏幕截图权限，在系统设置中允许。

### 3. 代码执行无响应

**问题**: 自动生成的代码没有执行

**解决**: 
- 检查 `#Program start` 和 `#Program end` 标记是否正确
- 查看日志区域的错误信息
- 手动运行 `generated/act.py` 查看具体错误

### 4. 中文输入问题

代码中使用剪贴板方式输入中文：
```python
pyperclip.copy('中文文本')
pyautogui.hotkey('ctrl', 'v')
```

### 5. 程序被截断问题

如果 AI 返回的代码被截断，程序会自动尝试修复缺失的括号。

## 注意事项

1. **自动化操作期间请勿移动鼠标或按键**
2. **任务执行时不要切换窗口**
3. **确保 DeepSeek 网页正常加载**
4. **如遇问题，查看日志区域的详细错误信息**

## 技术栈

- **GUI**: PySide6 (Qt for Python)
- **浏览器**: PySide6 WebEngine (基于 Chromium)
- **AI**: DeepSeek Chat
- **图像识别**: OpenCV, NumPy
- **自动化**: pyautogui, pyperclip
- **语音**: edge-tts

## 许可证

MIT License - Copyright (c) 2026

## 贡献

欢迎提交 Issue 和 Pull Request！
