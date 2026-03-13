"""
代码执行器 - 安全执行DeepSeek生成的代码
使用pyautogui进行键鼠控制
"""

import ast
import traceback
import sys
import os
import re
from datetime import datetime


class CodeExecutor:
    """代码执行器"""

    def __init__(self, keyboard, recognizer):
        self.keyboard = keyboard
        self.recognizer = recognizer
        self.allowed_modules = {
            "time",
            "datetime",
            "math",
            "random",
            "pyautogui",
            "cv2",
            "numpy",
            "PIL",
        }

        # 设置输出目录
        try:
            self.output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "generated"
            )
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                print(f"📁 创建输出目录: {self.output_dir}")
            else:
                print(f"📁 输出目录: {self.output_dir}")
        except Exception as e:
            print(f"❌ 创建输出目录失败: {e}")
            self.output_dir = os.path.join(os.path.expanduser("~"), "xiao_i_generated")
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            print(f"📁 使用备用目录: {self.output_dir}")

        # 保存最后执行的完整代码
        self.last_full_code = None
        self.last_output_file = None

    def check_code_safety(self, code):
        """检查代码安全性"""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ["os", "sys", "subprocess", "platform"]:
                            return False, f"禁止导入危险模块: {alias.name}"
                if isinstance(node, ast.ImportFrom):
                    if node.module in ["os", "sys", "subprocess", "platform"]:
                        return False, f"禁止导入危险模块: {node.module}"
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ["open", "remove", "system", "popen"]:
                            return False, f"禁止调用: {node.func.attr}"
            return True, "安全检查通过"
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        except Exception as e:
            return False, f"安全检查失败: {e}"

    def clean_code(self, code):
        """
        清理提取的代码，将单独成行的 ''' 或 \"\"\" 后面加上空格，避免程序被截断
        修复：如果一行只有三个引号，在后面加三个空格
        """
        if not code:
            return code

        try:
            lines = code.split("\n")
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped in ['"""', "'''"]:
                    if line.endswith('"""'):
                        cleaned_lines.append('"""   ')
                    elif line.endswith("'''"):
                        cleaned_lines.append("'''   ")
                    else:
                        cleaned_lines.append(line + "   ")
                    print(f"🔧 修复单独的三引号行: {line} -> {cleaned_lines[-1]}")
                else:
                    cleaned_lines.append(line)
            return "\n".join(cleaned_lines)
        except Exception as e:
            print(f"⚠️ 清理代码时出错: {e}")
            return code

    def fix_truncated_code(self, code):
        """
        修复截断的代码 - 补全缺失的闭合括号和语句
        """
        if not code:
            return code

        code = code.strip()
        open_braces = code.count("{") - code.count("}")
        open_brackets = code.count("[") - code.count("]")
        open_parens = code.count("(") - code.count(")")

        lines = code.split("\n")
        fixed_lines = []
        for line in lines:
            fixed_lines.append(line)

        for _ in range(open_braces):
            fixed_lines.append("}")
        for _ in range(open_brackets):
            fixed_lines.append("]")
        for _ in range(open_parens):
            fixed_lines.append(")")

        if "try:" in code and "except" not in code:
            fixed_lines.append("    except Exception as e:")
            fixed_lines.append('        return {"success": False, "error": str(e)}')

        if "def main():" in code and "__name__" not in code:
            fixed_lines.append("")
            fixed_lines.append('if __name__ == "__main__":')
            fixed_lines.append("    result = main()")
            fixed_lines.append('    print(f"执行结果: {result}")')

        return "\n".join(fixed_lines)

    def extract_code_from_deepseek_reply(self, reply):
        """
        从DeepSeek回复中提取代码
        仅依赖 #Program start 和 #Program end 标记
        """
        if not reply:
            return None

        try:
            lines = reply.splitlines()
            start_idx = -1
            end_idx = -1

            # 查找第一个 #Program start（忽略前导空白）
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("#Program start"):
                    start_idx = i
                    break

            if start_idx == -1:
                print("❌ 未找到 #Program start 标记")
                return None

            # 在 start_idx 之后查找第一个 #Program end
            for i in range(start_idx + 1, len(lines)):
                stripped = lines[i].strip()
                if stripped.startswith("#Program end"):
                    end_idx = i
                    break

            if end_idx == -1:
                print("❌ 未找到 #Program end 标记")
                return None

            # 提取从 start_idx 到 end_idx 的所有行（包含标记行）
            extracted_lines = lines[start_idx:end_idx + 1]
            extracted_code = "\n".join(extracted_lines)

            print(f"✅ 通过标记提取到代码，长度: {len(extracted_code)} 字符")

            # 后续清理和修复（可选）
            cleaned_code = self.clean_code(extracted_code)
            cleaned_code = self.fix_truncated_code(cleaned_code)
            return cleaned_code

        except Exception as e:
            print(f"❌ 提取代码时出错: {e}")
            traceback.print_exc()
            return None

    def save_reply_and_code(self, reply, extracted_code):
        """
        保存原始回复和提取的代码
        始终保存为固定的文件名：reply.py 和 act.py
        """
        reply_file = os.path.join(self.output_dir, "reply.py")
        act_file = os.path.join(self.output_dir, "act.py")
        results = {
            "reply_saved": False,
            "act_saved": False,
            "reply_file": reply_file,
            "act_file": act_file,
        }

        # 保存原始回复
        try:
            if os.path.exists(reply_file):
                os.remove(reply_file)
                print(f"🗑️ 删除旧文件: {reply_file}")
            with open(reply_file, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"📄 原始回复已保存: {reply_file}")
            results["reply_saved"] = True
        except Exception as e:
            print(f"❌ 保存原始回复失败: {e}")
            results["reply_error"] = str(e)

        # 保存提取的代码
        try:
            if os.path.exists(act_file):
                os.remove(act_file)
                print(f"🗑️ 删除旧文件: {act_file}")
            with open(act_file, "w", encoding="utf-8") as f:
                f.write(extracted_code)
            print(f"📄 执行代码已保存: {act_file}")
            results["act_saved"] = True
            self.last_full_code = extracted_code
            self.last_output_file = act_file
        except Exception as e:
            print(f"❌ 保存执行代码失败: {e}")
            results["act_error"] = str(e)

        return results

    def process_deepseek_reply(self, reply):
        """
        处理DeepSeek回复：提取代码并保存文件
        返回: {'success': bool, 'reply_file': str, 'act_file': str, 'error': str}
        """
        try:
            print("\n" + "=" * 60)
            print("📥 收到DeepSeek回复:")
            print("-" * 30)
            print(reply[:300] + ("..." if len(reply) > 300 else ""))
            print("-" * 30)
            print(f"📏 回复总长度: {len(reply)} 字符")

            # 提取代码（仅基于标记）
            extracted_code = self.extract_code_from_deepseek_reply(reply)

            if not extracted_code:
                print("❌ 未找到代码标记")
                save_result = self.save_reply_and_code(reply, "# 未找到代码")
                return {
                    "success": False,
                    "error": "未找到 #Program start 或 #Program end 标记",
                    "reply_file": save_result.get("reply_file"),
                    "act_file": save_result.get("act_file"),
                }

            print("\n📝 提取的代码:")
            print("-" * 30)
            print(extracted_code[:300] + ("..." if len(extracted_code) > 300 else ""))
            print("-" * 30)
            print(f"📏 代码长度: {len(extracted_code)} 字符")

            # 安全检查
            safe, message = self.check_code_safety(extracted_code)
            if not safe:
                print(f"❌ 安全检查失败: {message}")
                save_result = self.save_reply_and_code(reply, extracted_code)
                return {
                    "success": False,
                    "error": message,
                    "reply_file": save_result.get("reply_file"),
                    "act_file": save_result.get("act_file"),
                }

            print(f"✅ 安全检查通过")

            # 保存文件
            save_result = self.save_reply_and_code(reply, extracted_code)

            return {
                "success": True,
                "reply_file": save_result.get("reply_file"),
                "act_file": save_result.get("act_file"),
                "error": None,
            }

        except Exception as e:
            print(f"❌ 处理回复时发生严重错误: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": f"处理错误: {str(e)}",
                "reply_file": None,
                "act_file": None,
            }

    def get_last_full_code(self):
        return self.last_full_code

    def get_last_output_file(self):
        return self.last_output_file

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")