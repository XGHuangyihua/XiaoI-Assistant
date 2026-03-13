import asyncio
import edge_tts
import os

async def speak():
    tts = edge_tts.Communicate("你好，世界", "zh-CN-XiaoxiaoNeural")
    await tts.save("output.mp3")
    print("音频文件已生成，正在播放...")
    os.startfile("output.mp3")  # 用系统默认播放器打开

asyncio.run(speak())