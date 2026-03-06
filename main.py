"""
小i智能助手 - 主程序入口
"""

VERSION = "1.0.0"

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

# 从ui_main导入XiaoIWindow类
try:
    from ui_main import XiaoIWindow
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保 ui_main.py 文件中包含 XiaoIWindow 类")
    sys.exit(1)


def main():
    """主函数"""
    try:
        # 创建应用
        app = QApplication(sys.argv)

        # 设置字体（支持中文）
        font = QFont("Microsoft YaHei", 9)
        app.setFont(font)

        # 创建主窗口
        print("🚀 正在启动小i智能助手...")
        print(f"📋 版本: {VERSION}")
        window = XiaoIWindow()
        window.show()

        # 运行应用
        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
