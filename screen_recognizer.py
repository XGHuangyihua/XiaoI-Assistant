"""
屏幕识别器 - 识别屏幕上的元素
支持多尺度模板匹配，提高识别成功率
"""

import cv2
import numpy as np
import pyautogui
import os
import sys
from PIL import Image
import time


class ScreenRecognizer:
    """屏幕识别器"""

    def __init__(self, template_folder="templates"):
        self.template_folder = template_folder
        # 确保模板文件夹存在
        if not os.path.exists(template_folder):
            os.makedirs(template_folder)
            print(f"📁 创建模板文件夹: {template_folder}")

        # 缓存上次截图，用于调试
        self.last_screenshot = None
        self.debug_mode = True  # 调试模式开关

    def get_template_path(self, template_name):
        """
        获取模板文件路径，处理中文路径
        """
        # 方法1: 使用传入的文件名
        template_path = os.path.join(self.template_folder, template_name)

        if os.path.exists(template_path):
            return template_path

        # 方法2: 如果文件不存在，尝试查找类似文件
        print(f"🔍 正在查找模板文件: {template_name}")

        if os.path.exists(self.template_folder):
            # 列出文件夹中的所有图片
            image_files = []
            for file in os.listdir(self.template_folder):
                if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
                    image_files.append(file)
                    print(f"📁 找到图片: {file}")

            if not image_files:
                print("❌ templates文件夹中没有图片文件")
                return template_path

            # 如果传入的是中文名，尝试匹配
            if "发送" in template_name or "输入" in template_name:
                for file in image_files:
                    if "input" in file.lower() or "发送" in file or "输入" in file:
                        template_path = os.path.join(self.template_folder, file)
                        print(f"✅ 使用匹配的图片: {file}")
                        return template_path

            # 默认使用第一个图片
            first_image = image_files[0]
            template_path = os.path.join(self.template_folder, first_image)
            print(f"✅ 使用第一个图片: {first_image}")

        return template_path

    def load_image_safe(self, image_path):
        """
        安全地加载图片，支持中文路径和多种格式
        """
        if not os.path.exists(image_path):
            print(f"❌ 文件不存在: {image_path}")
            return None

        try:
            # 方法1: 使用OpenCV直接读取
            img = cv2.imread(image_path)
            if img is not None:
                if self.debug_mode:
                    print(f"✅ OpenCV读取成功: {os.path.basename(image_path)}")
                return img
        except Exception as e:
            if self.debug_mode:
                print(f"OpenCV读取失败: {e}")

        try:
            # 方法2: 使用PIL读取（更好地支持中文和特殊格式）
            from PIL import Image

            pil_image = Image.open(image_path)

            # 转换为RGB模式（如果需要）
            if pil_image.mode == "RGBA":
                # 创建白色背景
                rgb_image = Image.new("RGB", pil_image.size, (255, 255, 255))
                rgb_image.paste(pil_image, mask=pil_image.split()[3])
                pil_image = rgb_image
            elif pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # 转换为OpenCV格式
            img_array = np.array(pil_image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            if self.debug_mode:
                print(f"✅ PIL读取成功: {os.path.basename(image_path)}")
            return img_cv

        except Exception as e:
            print(f"PIL读取失败: {e}")

        return None

    def capture_screen(self):
        """截取整个屏幕"""
        try:
            # 使用pyautogui截图
            screenshot = pyautogui.screenshot()
            # 转换为OpenCV格式
            screen_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 缓存截图
            self.last_screenshot = screen_cv.copy()

            if self.debug_mode:
                h, w = screen_cv.shape[:2]
                print(f"📸 截图成功: {w} x {h}")

            return screen_cv
        except Exception as e:
            print(f"❌ 截图失败: {e}")
            return None

    def preprocess_image(self, img):
        """
        图像预处理，提高匹配成功率
        """
        if img is None:
            return None

        try:
            # 转换为灰度图
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()

            # 直方图均衡化，增强对比度
            gray = cv2.equalizeHist(gray)

            # 可选：高斯滤波去噪
            # gray = cv2.GaussianBlur(gray, (3, 3), 0)

            return gray
        except Exception as e:
            print(f"❌ 图像预处理失败: {e}")
            return None

    def find_template(self, template_name, confidence=0.3):
        """
        在屏幕上查找模板图片（增强版：多尺度匹配）

        参数:
            template_name: 模板文件名
            confidence: 匹配阈值（0-1），越低越容易匹配但也越容易误判

        返回:
            成功返回包含位置信息的字典，失败返回None
        """
        # 获取模板文件路径
        template_path = self.get_template_path(template_name)

        if not os.path.exists(template_path):
            print(f"❌ 模板文件不存在: {template_path}")
            print(f"💡 请将模板图片放入 {self.template_folder} 文件夹")
            return None

        # 读取模板图片
        template = self.load_image_safe(template_path)
        if template is None:
            print(f"❌ 无法读取模板图片")
            return None

        # 获取模板尺寸
        h, w = template.shape[:2]
        print(f"📏 模板原始尺寸: {w} x {h}")

        # 截取屏幕
        screen = self.capture_screen()
        if screen is None:
            return None

        # 图像预处理
        screen_gray = self.preprocess_image(screen)
        template_gray = self.preprocess_image(template)

        if screen_gray is None or template_gray is None:
            return None

        # 多尺度匹配（从大到小，优先匹配大尺寸）
        best_match = None
        best_val = -1
        scales = [1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5]

        print("🔄 正在进行多尺度匹配...")

        for scale in scales:
            # 缩放模板
            new_w = int(w * scale)
            new_h = int(h * scale)

            # 检查缩放后的模板是否超过屏幕尺寸
            if new_w > screen_gray.shape[1] or new_h > screen_gray.shape[0]:
                continue

            # 缩放模板
            resized_template = cv2.resize(template_gray, (new_w, new_h))

            # 模板匹配
            try:
                result = cv2.matchTemplate(
                    screen_gray, resized_template, cv2.TM_CCOEFF_NORMED
                )
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # 记录最佳匹配
                if max_val > best_val:
                    best_val = max_val
                    best_match = {
                        "scale": scale,
                        "confidence": max_val,
                        "top_left": max_loc,
                        "size": (new_w, new_h),
                    }

                # 打印高匹配度的结果
                if max_val > 0.2:
                    print(f"  缩放 {scale:.1f}: 匹配度 {max_val:.3f}")

            except Exception as e:
                print(f"  缩放 {scale:.1f} 匹配失败: {e}")
                continue

        # 检查是否找到足够好的匹配
        if best_match and best_val >= confidence:
            # 计算中心点
            top_left = best_match["top_left"]
            size = best_match["size"]
            center_x = top_left[0] + size[0] // 2
            center_y = top_left[1] + size[1] // 2

            print(f"\n✅ 找到目标位置!")
            print(f"  缩放比例: {best_match['scale']:.1f}")
            print(f"  匹配度: {best_val:.3f}")
            print(f"  中心坐标: ({center_x}, {center_y})")
            print(f"  区域: 左上({top_left[0]}, {top_left[1]}) 尺寸{size}")

            return {
                "top_left": top_left,
                "center": (center_x, center_y),
                "size": size,
                "scale": best_match["scale"],
                "confidence": best_val,
            }
        else:
            print(f"\n❌ 未找到足够匹配的目标")
            print(f"  最佳匹配度: {best_val:.3f}")
            print(f"  要求阈值: {confidence}")

            # 调试信息：保存截图
            if self.debug_mode and self.last_screenshot is not None:
                debug_path = os.path.join(self.template_folder, "last_screen.jpg")
                cv2.imwrite(debug_path, self.last_screenshot)
                print(f"📸 已保存当前屏幕截图: {debug_path}")

            return None

    def find_template_multi_angle(self, template_name, confidence=0.3):
        """
        多角度匹配（如果需要识别旋转的元素）
        """
        # TODO: 如果需要识别旋转的元素，可以实现这个功能
        pass

    def find_deepseek_inputbox(self):
        """专门查找DeepSeek输入框（尝试多种文件名）"""
        print("\n🔍 正在查找DeepSeek输入框...")

        # 尝试多个可能的文件名
        possible_names = [
            "input_box.jpeg",
            "input_box.jpg",
            "input_box.png",
            "发送输入框.jpeg",
            "发送输入框.jpg",
            "deepseek_input.jpeg",
            "deepseek_input.png",
            "input.png",
        ]

        # 尝试不同的匹配阈值（从低到高）
        thresholds = [0.15, 0.2, 0.25, 0.3]

        for name in possible_names:
            for thresh in thresholds:
                print(f"\n📝 尝试模板: {name} (阈值: {thresh})")
                result = self.find_template(name, confidence=thresh)
                if result:
                    print(f"✅ 成功找到DeepSeek输入框!")
                    return result
                # 短暂暂停，避免太快
                time.sleep(0.1)

        print("\n❌ 所有尝试均失败，未找到DeepSeek输入框")
        print("💡 建议:")
        print("   1. 确保DeepSeek网页已打开且输入框可见")
        print("   2. 重新截图输入框，保存为 input_box.jpeg")
        print("   3. 检查 templates 文件夹中是否有图片文件")
        return None

    def find_image_on_screen(self, image_path, confidence=0.3):
        """
        通用的图片查找方法
        """
        return self.find_template(os.path.basename(image_path), confidence)

    def find_template_in_region(self, template_name, region, confidence=0.3):
        """
        在指定区域内查找模板

        参数:
            template_name: 模板文件名
            region: 区域字典，包含 'top_left' 和 'size'
            confidence: 匹配阈值

        返回:
            成功返回包含位置信息的字典（相对于全屏的坐标），失败返回None
        """
        # 获取模板文件路径
        template_path = self.get_template_path(template_name)

        if not os.path.exists(template_path):
            print(f"❌ 模板文件不存在: {template_path}")
            return None

        # 读取模板图片
        template = self.load_image_safe(template_path)
        if template is None:
            print(f"❌ 无法读取模板图片")
            return None

        # 获取搜索区域
        rx, ry = region["top_left"]
        rw, rh = region["size"]

        # 截取屏幕
        screen = self.capture_screen()
        if screen is None:
            return None

        # 提取指定区域
        screen_h, screen_w = screen.shape[:2]
        rx = max(0, rx)
        ry = max(0, ry)
        rw = min(rw, screen_w - rx)
        rh = min(rh, screen_h - ry)

        screen_region = screen[ry : ry + rh, rx : rx + rw]

        if screen_region.size == 0:
            print(f"❌ 区域无效")
            return None

        # 图像预处理
        screen_gray = self.preprocess_image(screen_region)
        template_gray = self.preprocess_image(template)

        if screen_gray is None or template_gray is None:
            return None

        # 获取模板尺寸
        th, tw = template_gray.shape[:2]

        # 多尺度匹配（从大到小，优先匹配大尺寸）
        best_match = None
        best_val = -1
        scales = [1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5]

        for scale in scales:
            new_w = int(tw * scale)
            new_h = int(th * scale)

            if new_w > screen_region.shape[1] or new_h > screen_region.shape[0]:
                continue

            resized_template = cv2.resize(template_gray, (new_w, new_h))

            try:
                result = cv2.matchTemplate(
                    screen_gray, resized_template, cv2.TM_CCOEFF_NORMED
                )
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if max_val > best_val:
                    best_val = max_val
                    best_match = {
                        "scale": scale,
                        "confidence": max_val,
                        "top_left": max_loc,
                        "size": (new_w, new_h),
                    }

            except Exception as e:
                continue

        # 检查是否找到足够好的匹配
        if best_match and best_val >= confidence:
            # 计算相对于全屏的坐标
            rel_top_left = best_match["top_left"]
            rel_size = best_match["size"]
            center_x = rx + rel_top_left[0] + rel_size[0] // 2
            center_y = ry + rel_top_left[1] + rel_size[1] // 2

            print(f"✅ 区域内找到目标!")
            print(f"  匹配度: {best_val:.3f}")
            print(f"  区域坐标: ({center_x}, {center_y})")

            return {
                "top_left": (rx + rel_top_left[0], ry + rel_top_left[1]),
                "center": (center_x, center_y),
                "size": rel_size,
                "scale": best_match["scale"],
                "confidence": best_val,
            }
        else:
            print(f"❌ 区域内未找到匹配 (最佳: {best_val:.3f})")
            return None

    def get_screen_region(self, x, y, width, height):
        """
        获取屏幕指定区域
        """
        screen = self.capture_screen()
        if screen is None:
            return None

        h, w = screen.shape[:2]

        # 确保区域在屏幕范围内
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        width = min(width, w - x)
        height = min(height, h - y)

        region = screen[y : y + height, x : x + width]
        return region

    def save_template_from_screen(self, x, y, width, height, save_name):
        """
        从屏幕截取区域保存为模板
        """
        region = self.get_screen_region(x, y, width, height)
        if region is not None:
            save_path = os.path.join(self.template_folder, save_name)
            cv2.imwrite(save_path, region)
            print(f"✅ 模板已保存: {save_path}")
            return True
        return False

    def enable_debug(self, enable=True):
        """开启/关闭调试模式"""
        self.debug_mode = enable
        print(f"🔧 调试模式: {'开启' if enable else '关闭'}")

    def get_screen_text(self, region=None):
        """
        获取屏幕文字（预留OCR接口）
        目前返回模拟信息
        """
        return "当前屏幕：可以看到DeepSeek聊天界面"


# ========== 测试代码 ==========
if __name__ == "__main__":
    print("🔧 屏幕识别器测试")
    print("=" * 50)

    # 创建识别器
    recognizer = ScreenRecognizer("templates")

    # 开启调试模式
    recognizer.enable_debug(True)

    # 测试查找DeepSeek输入框
    print("\n📝 测试1: 查找DeepSeek输入框")
    location = recognizer.find_deepseek_inputbox()

    if location:
        print(f"\n✅ 测试通过!")
        print(f"   中心点: {location['center']}")
        print(f"   匹配度: {location['confidence']:.3f}")
    else:
        print(f"\n❌ 测试失败，未找到输入框")
        print("💡 请确保:")
        print("   1. DeepSeek网页已打开")
        print("   2. templates文件夹中有模板图片")
        print("   3. 模板图片名称正确")

    # 测试截图功能
    print("\n📝 测试2: 截图功能")
    screen = recognizer.capture_screen()
    if screen is not None:
        print("✅ 截图成功")
    else:
        print("❌ 截图失败")

    print("\n" + "=" * 50)
