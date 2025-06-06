import tkinter as tk
from tkinter import messagebox, ttk
import time
import threading
import sounddevice as sd
import numpy as np
from scipy.signal import lfilter
import queue
from plyer import notification  # 添加 plyer 模块用于发送系统通知
import configparser  # 添加 configparser 模块

# 噪音检测器类
class NoiseDetector:
    def __init__(self):
        self.sensitivity = 1.0
        self.audio_queue = queue.Queue()
        self.current_device = sd.default.device[0]  # 默认设备索引
        self.running = False
        self.noise_min_baseline = 0.0  # 最小基准线（静音环境）
        self.noise_max_baseline = 100.0  # 最大基准线（校准音频）

    def calculate_db(self, audio_data):
        # 确保音频数据在[-1, 1]范围内
        audio_data = np.clip(audio_data, -1.0, 1.0)

        # 计算RMS值
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < 1e-10:  # 防止取对数时出错
            rms = 1e-10

        # 计算分贝值
        db = 20 * np.log10(rms) + 94  # 假设麦克风的参考噪音为94 dB SPL

        # 加权约束在最小和最大基准线之间（修改范围：10-70 dB）
        adjusted_db = (db - self.noise_min_baseline) / (self.noise_max_baseline - self.noise_min_baseline) * 60 + 10
        adjusted_db = max(10, min(70, adjusted_db))  # 调整最大值到70
        return adjusted_db

    def calibrate_min_baseline(self):
        # 校准最小基准线（静音环境）
        print("正在校准最小基准线，请保持安静...")
        with sd.InputStream(device=self.current_device, channels=1, samplerate=44100) as stream:
            audio_data = stream.read(44100)[0]
            self.noise_min_baseline = self.calculate_db(audio_data[:, 0])
        print(f"最小基准线校准完成：{self.noise_min_baseline:.1f} dB")

    def calibrate_max_baseline(self):
        # 校准最大基准线（播放单频率嗡鸣音）
        print("正在校准最大基准线，请保持安静...")
        
        # 生成单频率嗡鸣音
        duration = 2  # 持续时间2秒
        frequency = 1000  # 频率为1000Hz
        samplerate = 44100
        t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * frequency * t)  # 振幅为0.5

        # 播放嗡鸣音
        def play_tone():
            sd.play(tone, samplerate)
            sd.wait()

        threading.Thread(target=play_tone, daemon=True).start()

        # 录制音频并校准
        with sd.InputStream(device=self.current_device, channels=1, samplerate=samplerate) as stream:
            audio_data = stream.read(samplerate)[0]
            self.noise_max_baseline = self.calculate_db(audio_data[:, 0])
        print(f"最大基准线校准完成：{self.noise_max_baseline:.1f} dB")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"音频流状态: {status}")
        # 直接将原始数据放入队列，减少处理延迟
        self.audio_queue.put(indata[:, 0])

    def start(self):
        self.running = True
        self.stream = sd.InputStream(
            device=self.current_device,
            channels=1,
            callback=self.audio_callback,
            samplerate=44100,  # 保持原来的采样率
            blocksize=1024  # 增加块大小，减少回调频率
        )
        self.stream.start()
        print("音频流已启动")

    def stop(self):
        self.running = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

# 自习课大屏幕看板类
class SchoolDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("自习课大屏幕看板")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="black")  # 默认深色模式

        self.noise_detector = NoiseDetector()
        self.dark_mode = True  # 默认深色模式

        # 初始化UI组件
        self.init_ui()

        # 读取课程时间表
        self.schedule = []  # 初始化为空列表
        self.load_schedule_async()  # 异步加载课程时间表

        # 启动时间更新
        self.update_time()

        # 启动噪音检测
        self.noise_detector.start()
        self.update_noise_level()

        # 启动倒计时更新
        self.update_countdown()

    def load_schedule(self):
        import os
        config = configparser.ConfigParser()
        config_file = os.path.join(os.getcwd(), "schedule.ini")
        schedule = []

        try:
            config.read(config_file, encoding="utf-8")
            if "Schedule" in config:
                for key, value in config["Schedule"].items():
                    if key.startswith("period"):
                        # 清理注释部分，只保留数字
                        cleaned_value = value.split("#")[0].strip()
                        start, end = map(int, cleaned_value.split("-"))
                        schedule.append((start, end))
            else:
                print("未找到 [Schedule] 配置段，使用默认时间表")
        except Exception as e:
            print(f"读取课程时间表失败：{e}，使用默认时间表")

        # 如果配置文件不存在或读取失败，使用默认时间表
        if not schedule:
            schedule = [(1140, 1230), (1245, 1310)]  # 默认时间段：19:00-20:30 和 20:45-21:50

        return schedule

    # 异步加载课程时间表
    def load_schedule_async(self):
        threading.Thread(target=self.load_schedule_and_update_ui).start()

    def load_schedule_and_update_ui(self):
        schedule = self.load_schedule()
        self.root.after(0, self.update_schedule, schedule)

    def update_schedule(self, schedule):
        self.schedule = schedule
        self.update_countdown()  # 立即更新倒计时显示

    # 初始化UI组件
    def init_ui(self):
        # 程序标题文本框
        self.title_label = tk.Label(self.root, text="自习看板【专注模式】", font=("宋体", 24, "bold"), fg="white", bg="black")
        self.title_label.pack(pady=10, anchor="nw")
        self.title_label.place(x=20, y=20)

        # 时间标签
        self.time_label = tk.Label(self.root, text="", font=("Times New Roman", 128, "bold"), fg="white", bg="black")
        self.time_label.pack(pady=20)

        # 纪律提醒
        self.reminder_label = tk.Label(self.root, text="当前活动：自习 请保持安静", font=("宋体", 36), fg="white", bg="black")
        self.reminder_label.pack(pady=20)

        # 设置按钮
        self.settings_button = tk.Button(self.root, text="设置", font=("宋体", 14), command=self.open_settings_window, fg="white", bg="gray",
                                         relief="flat", highlightbackground="white", highlightthickness=2)
        self.settings_button.pack(pady=10)
        self.settings_button.configure(width=6, height=1)
        self.settings_button.place(x=20, y=self.root.winfo_screenheight() - 150)

        # 最小化按钮
        self.minimize_button = tk.Button(self.root, text="最小化", font=("宋体", 14), command=self.minimize_window, fg="white", bg="gray",
                                         relief="flat", highlightbackground="white", highlightthickness=2)
        self.minimize_button.pack(pady=10)
        self.minimize_button.configure(width=6, height=1)
        self.minimize_button.place(x=20, y=self.root.winfo_screenheight() - 100)

        # 噪音显示标签 (优化字体和动画效果)
        self.noise_label = tk.Label(self.root, text="当前噪音：-- dB", font=("Segoe UI", 28, "bold"), 
                               fg="#00FFAA", bg="black", relief="flat")
        self.noise_label.pack(pady=10)
        self.noise_label.place(x=20, y=80)

        # 重构音强波动条为渐变式仪表条
        self.amplitude_bar = tk.Canvas(self.root, width=300, height=40, bg="black", highlightthickness=0)
        self.amplitude_bar.pack(pady=10)
        self.amplitude_bar.place(x=380, y=89)
        
        # 创建分层渐变色块
        self.amplitude_bar.create_rectangle(0, 0, 300, 40, fill="#222222", outline="", tags="bg")
        self.amplitude_bar.create_rectangle(0, 0, 0, 40, fill="#00FFAA", outline="", tags="bar")
        # 添加警示区标记
        self.amplitude_bar.create_rectangle(185, 0, 190, 40, fill="#FF4444", outline="")
        self.amplitude_bar.create_text(220, 20, text="⚠️", font=("Segoe UI", 16), fill="white", anchor="w")

        # 倒计时标签
        self.countdown_label = tk.Label(self.root, text="无活动", font=("宋体", 24), fg="white", bg="black")
        self.countdown_label.pack(pady=10)
        self.countdown_label.place(x=20, y=140)

        # 调整组件位置
        self.time_label.pack_configure(anchor="center", pady=(self.root.winfo_screenheight() // 4, 10))
        self.reminder_label.pack_configure(anchor="center", pady=10)

    # 时间更新
    def update_time(self):
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    # 噪音检测更新
    def update_noise_level(self):
        try:
            if not self.noise_detector.audio_queue.empty():
                audio_data = self.noise_detector.audio_queue.get_nowait()
                db_value = self.noise_detector.calculate_db(audio_data)
                
                # 平滑噪音值变化（加权平均）
                if hasattr(self, 'last_db_value'):
                    db_value = 0.7 * self.last_db_value + 0.3 * db_value
                self.last_db_value = db_value
                
                # 更新波动条（100ms刷新率）
                self.update_amplitude_bar(db_value)
        except queue.Empty:
            pass
    
        # 每100ms刷新一次波动条
        self.root.after(100, self.update_noise_level)

    # 更新波动条
    def update_amplitude_bar(self, db_value):
        # 动态颜色过渡计算 (从绿色到红色)
        norm = min(max((db_value - 10) / 60, 0), 1)  # 原 (db_value-20)/40
        r = int(255 * norm)
        g = int(255 * (1 - norm))
        color = f"#{r:02x}{g:02x}00"
        
        # 改进平滑动画过渡（保持原有动画逻辑）
        current_width = self.amplitude_bar.coords("bar")[2]
        target_width = norm * 300
        
        # 使用指数衰减实现更平滑的过渡
        easing_factor = 0.1  # 衰减因子
        new_width = current_width + (target_width - current_width) * easing_factor
        
        self.amplitude_bar.coords("bar", 0, 0, new_width, 40)
        self.amplitude_bar.itemconfig("bar", fill=color)

    # 更新GUI显示数值（1s刷新率）
    def update_gui_display(self):
        if hasattr(self, 'last_db_value'):
            self.noise_label.config(text=f"当前噪音：{self.last_db_value:.1f} dB")
        
        # 每1000ms刷新一次GUI显示数值
        self.root.after(1000, self.update_gui_display)

    # 倒计时更新
    def update_countdown(self):
        current_time = time.localtime()
        current_minutes = current_time.tm_hour * 60 + current_time.tm_min

        # 遍历所有时间段
        for i, (start, end) in enumerate(self.schedule, start=1):
            if start <= current_minutes <= end:
                remaining_minutes = end - current_minutes
                self.countdown_label.config(text=f"距离时间段 {i} 结束还剩：{remaining_minutes} 分钟")
                break
        else:
            self.countdown_label.config(text="无活动")

        # 每2秒更新一次（原为每分钟更新一次）
        self.root.after(2000, self.update_countdown)

    # 打开设置窗口
    def open_settings_window(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("500x400")
        settings_window.configure(bg="black")

        # 录音设备选择
        devices = sd.query_devices()
        device_names = [f"{i}: {dev['name']}" for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        
        # 设备选择区域
        device_frame = tk.LabelFrame(settings_window, text="录音设备选择", font=("宋体", 12), fg="white", bg="black", bd=2, relief="groove")
        device_frame.pack(pady=10, fill="x", padx=20)
        
        device_label = tk.Label(device_frame, text="选择录音设备：", font=("宋体", 12), fg="white", bg="black")
        device_label.pack(pady=5)
        
        device_var = tk.StringVar()
        device_combo = ttk.Combobox(device_frame, textvariable=device_var, values=device_names)
        device_combo.pack(pady=5)
        default_device_index = self.noise_detector.current_device
        device_combo.set(device_names[default_device_index])

        # 灵敏度调节区域
        sensitivity_frame = tk.LabelFrame(settings_window, text="灵敏度调节", font=("宋体", 12), fg="white", bg="black", bd=2, relief="groove")
        sensitivity_frame.pack(pady=10, fill="x", padx=20)
        
        sensitivity_label = tk.Label(sensitivity_frame, text="检测灵敏度：", font=("宋体", 12), fg="white", bg="black")
        sensitivity_label.pack(pady=5)
        
        sensitivity_scale = ttk.Scale(sensitivity_frame, from_=0.5, to=2.0, orient="horizontal", length=200)
        sensitivity_scale.set(self.noise_detector.sensitivity)
        sensitivity_scale.pack(pady=5)

        # 校准按钮区域
        calibration_frame = tk.LabelFrame(settings_window, text="基准线校准", font=("宋体", 12), fg="white", bg="black", bd=2, relief="groove")
        calibration_frame.pack(pady=10, fill="x", padx=20)
        
        calibrate_min_button = tk.Button(calibration_frame, text="校准最小基准线", font=("宋体", 12),
                                         command=self.noise_detector.calibrate_min_baseline, fg="white", bg="gray",
                                         relief="flat", highlightbackground="white", highlightthickness=2)
        calibrate_min_button.pack(pady=5, side="left", padx=10)
        
        calibrate_max_button = tk.Button(calibration_frame, text="校准最大基准线", font=("宋体", 12),
                                         command=self.noise_detector.calibrate_max_baseline, fg="white", bg="gray",
                                         relief="flat", highlightbackground="white", highlightthickness=2)
        calibrate_max_button.pack(pady=5, side="left", padx=10)

        # 操作按钮区域
        operation_frame = tk.LabelFrame(settings_window, text="操作", font=("宋体", 12), fg="white", bg="black", bd=2, relief="groove")
        operation_frame.pack(pady=10, fill="x", padx=20)
        
        def save_settings():
            # 保存设备设置
            selected_device = int(device_var.get().split(':')[0])
            self.noise_detector.stop()
            self.noise_detector.current_device = selected_device
            self.noise_detector.sensitivity = sensitivity_scale.get()
            self.noise_detector.start()
            settings_window.destroy()

        save_button = tk.Button(operation_frame, text="保存", font=("宋体", 12), command=save_settings,
                              fg="white", bg="gray", relief="flat", highlightbackground="white", highlightthickness=2)
        save_button.pack(pady=5, side="left", padx=10)

        exit_button = tk.Button(operation_frame, text="退出程序", font=("宋体", 12), command=self.root.destroy,
                              fg="white", bg="gray", relief="flat", highlightbackground="white", highlightthickness=2)
        exit_button.pack(pady=5, side="left", padx=10)

        # 新增深浅色模式切换按钮
        def toggle_dark_mode():
            self.dark_mode = not self.dark_mode
            bg_color = "black" if self.dark_mode else "white"
            fg_color = "white" if self.dark_mode else "black"
            self.root.configure(bg=bg_color)
            self.title_label.configure(fg=fg_color, bg=bg_color)
            self.time_label.configure(fg=fg_color, bg=bg_color)
            self.reminder_label.configure(fg=fg_color, bg=bg_color)
            self.noise_label.configure(fg=fg_color, bg=bg_color)
            self.countdown_label.configure(fg=fg_color, bg=bg_color)
            self.settings_button.configure(fg=fg_color, bg="gray")
            self.minimize_button.configure(fg=fg_color, bg="gray")

        dark_mode_button = tk.Button(operation_frame, text="切换深浅色模式", font=("宋体", 12), command=toggle_dark_mode,
                                     fg="white", bg="gray", relief="flat", highlightbackground="white", highlightthickness=2)
        dark_mode_button.pack(pady=5, side="left", padx=10)

        # 新增 ISSUE/关于 按钮
        def open_about_window():
            about_window = tk.Toplevel(settings_window)
            about_window.title("ISSUE/关于")
            about_window.geometry("1200x800")
            about_window.configure(bg="black")

            # 创建滚动区域
            canvas = tk.Canvas(about_window, bg="black")
            scrollbar = tk.Scrollbar(about_window, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="black")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            about_text = """
            Dashboard @by1640L

            版本号：1.0.2（当前维护状态：已暂缓）
            本次更新时间：2025年6月4日

            1.新增了最小化窗口的逻辑判断功能，提升用户体验与稳定性。
            2.修复了课程表同步相关的问题，确保时间显示更加准确。
            3.优化了时钟对齐机制，现已与上层软件 Classisland 实现精准同步。

            本程序基于 MIT 开源协议 发布，您可以自由使用、修改和传播本项目，但需遵循相应的开源协议条款。

            相关链接
            上级软件：Classisland
            官方网站：https://classisland.tech/
            插件下载：本软件已成功上架 Classisland 插件广场，欢迎前往下载体验。
            项目仓库地址：
            https://github.com/lic06/Selfstudy_boards

            提交 ISSUE / 联系方式
            如果您在使用过程中遇到任何问题或有改进建议，欢迎通过以下方式反馈：

            1.GitHub Issues 页面提交：
            https://github.com/lic06/Selfstudy_boards/issues
            2.邮箱联系开发者：
            9duoliang@gmail.com
            3.线下联系开发者：2-506教室
            """

            # 标题部分
            title_label = tk.Label(scrollable_frame, text="关于/ISSUES", font=("宋体", 24, "bold"), fg="white", bg="black")
            title_label.pack(pady=20)

            # 正文部分
            about_label = tk.Label(scrollable_frame, text=about_text, font=("宋体", 14), fg="white", bg="black", justify="left")
            about_label.pack(pady=10, padx=20)

            # 关闭按钮
            close_button = tk.Button(about_window, text="关闭", font=("宋体", 14), command=about_window.destroy,
                                     fg="white", bg="gray", relief="flat", highlightbackground="white", highlightthickness=2)
            close_button.pack(pady=20)

        issue_button = tk.Button(operation_frame, text="ISSUE/关于", font=("宋体", 12), command=open_about_window,
                                 fg="white", bg="gray", relief="flat", highlightbackground="white", highlightthickness=2)
        issue_button.pack(pady=5, side="left", padx=10)

    # 最小化窗口
    def minimize_window(self):
        self.root.withdraw()  # 隐藏窗口
        print("窗口已隐藏，120秒后将自动恢复，如需退出请点击右下角的设置按钮，进入二级菜单退出。")
        
        # 发送系统通知
        notification.notify(
            title="自习看板",
            message="    窗口已隐藏，120秒后将自动恢复，如需退出请点击右下角的设置按钮，进入二级菜单退出。",
            app_name="自习看板",
            timeout=5  # 通知显示时间（秒）
        )
        
        self.root.after(120000, self.restore_window)  # 120秒后恢复窗口

    # 恢复窗口
    def restore_window(self):
        self.root.deiconify()  # 恢复窗口
        self.root.attributes('-fullscreen', True)  # 强制全屏
        print("窗口已恢复并强制全屏")

# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolDashboard(root)
    
    # 启动GUI显示数值更新
    app.update_gui_display()
    
    root.mainloop()
