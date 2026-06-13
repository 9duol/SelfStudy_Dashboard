import tkinter as tk
from tkinter import messagebox, ttk
import time
import threading
import queue
import sounddevice as sd
from plyer import notification

from noise_detector import NoiseDetector
from config_loader import load_schedule
from settings_window import SettingsWindow
from activity_configurator import ActivityConfigurator
from splash_screen import SplashScreen  # 新增导入


class SchoolDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("自习课大屏幕看板")
        self.root.attributes('-fullscreen', True)
        # 默认浅色主题
        self.root.configure(bg="#ffffff")

        self.noise_detector = NoiseDetector()
        self.dark_mode = False  # 默认浅色（False 表示非深色）

        # 主题颜色（会随 dark_mode 切换）
        self.bg_color = "#ffffff"
        self.fg_color = "#222222"
        self.primary_color = "#0a84ff"  # 主要操作色（蓝）
        self.accent_color = "#00c853"  # 次要强调色（绿）
        self.warning_color = "#ffb300"  # 黄作为警示
        self.schedule = []
        # 构建界面并启动后台任务（在 __init__ 内执行）
        self.init_ui()
        self.apply_theme()

        self.update_time()

        self.noise_detector.start()
        self.update_noise_level()

        self.root.after(0, self.load_schedule_async)

        self.update_countdown()

        # 显示启动页面
        self.splash_screen = SplashScreen(root)
        self.splash_screen.show()

    def load_schedule_async(self):
        threading.Thread(target=self.load_schedule_and_update_ui).start()

    def load_schedule_and_update_ui(self):
        schedule = load_schedule()
        print(f"加载到的课程表: {schedule}")  # 调试信息
        self.root.after(0, self.update_schedule, schedule)

    def update_schedule(self, schedule):
        self.schedule = schedule
        self.update_countdown()

    def init_ui(self):
        # 顶部左侧标题
        self.title_label = tk.Label(self.root, text="自习看板", font=("微软雅黑", 18, "bold"))
        self.title_label.place(x=20, y=28)

        # 居中时间显示，较紧凑字体
        self.time_label = tk.Label(self.root, text="", font=("Times New Roman", 80, "bold"))
        self.time_label.pack(pady=20)

        self.reminder_label = tk.Label(self.root, text="当前活动：自习 请保持安静", font=("微软雅黑", 16))
        self.reminder_label.pack(pady=6)
        
        # 添加当前事件时间进度条
        self.progress_canvas = tk.Canvas(self.root, height=10, bg="#f0f0f0", highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 10, fill="#0a84ff", outline="")

        # 左下角操作按钮（设置/最小化），垂直排列在左下
        screen_h = self.root.winfo_screenheight()
        btn_left_x = 20
        # 按钮大小与间距
        btn_w, btn_h = 90, 36  # 缩小按钮宽度和高度
        gap = 12

        # 活动配置按钮
        self.activity_config_button = tk.Button(
            self.root, text="活动配置", font=("微软雅黑", 12), 
            command=self.open_activity_config,
            relief="flat")
        self.activity_config_button.place(x=btn_left_x, y=screen_h - (btn_h * 3 + gap * 2 + 20), width=btn_w, height=btn_h)

        self.settings_button = tk.Button(self.root, text="设置", font=("微软雅黑", 12), command=self.open_settings_window,
                                         relief="flat")
        self.settings_button.place(x=btn_left_x, y=screen_h - (btn_h * 2 + gap + 20), width=btn_w, height=btn_h)

        self.minimize_button = tk.Button(self.root, text="最小化", font=("微软雅黑", 12), command=self.minimize_window,
                                         relief="flat")
        self.minimize_button.place(x=btn_left_x, y=screen_h - (btn_h + 20), width=btn_w, height=btn_h)

        # 噪音显示与波形条放在左上区域
        self.noise_label = tk.Label(self.root, text="当前噪音：-- dB", font=("Segoe UI", 16, "bold"))
        self.noise_label.place(x=20, y=80)

        self.amplitude_bar = tk.Canvas(self.root, width=360, height=28, bg="#f5f5f5", highlightthickness=0)
        self.amplitude_bar.place(x=20, y=120)
        # 背景轨道
        self.amplitude_bar.create_rectangle(0, 0, 360, 28, fill="#f0f0f0", outline="", tags="bg")
        # 动态条（默认主色）
        self.amplitude_bar.create_rectangle(0, 0, 0, 28, fill=self.primary_color, outline="", tags="bar")
        # 警示标记（黄色区）
        warn_x = int(360 * 0.7)
        self.amplitude_bar.create_rectangle(warn_x, 0, warn_x + 4, 28, fill=self.warning_color, outline="")
        self.amplitude_bar.create_text(warn_x + 10, 14, text="⚠", font=("Segoe UI", 12), fill=self.fg_color, anchor="w")

        self.countdown_label = tk.Label(self.root, text="无活动", font=("微软雅黑", 16))
        self.countdown_label.place(x=20, y=160)

        self.time_label.pack_configure(anchor="center", pady=(self.root.winfo_screenheight() // 6, 10))
        self.reminder_label.pack_configure(anchor="center", pady=6)
        self.progress_canvas.pack_configure(anchor="center")
        
    def apply_theme(self):
        """将当前主题颜色应用到已有控件（浅色/深色切换共用）。"""
        bg = "#111111" if self.dark_mode else self.bg_color
        fg = "#ffffff" if self.dark_mode else self.fg_color
        primary = "#0a84ff" if not self.dark_mode else "#0a84ff"
        # 根窗口
        try:
            self.root.configure(bg=bg)
        except Exception:
            pass

        # 常用标签/按钮统一更新
        widgets = [
            getattr(self, 'title_label', None),
            getattr(self, 'time_label', None),
            getattr(self, 'reminder_label', None),
            getattr(self, 'noise_label', None),
            getattr(self, 'countdown_label', None),
            getattr(self, 'settings_button', None),
            getattr(self, 'minimize_button', None),
            getattr(self, 'activity_config_button', None),  # 添加活动配置按钮
        ]
        for w in widgets:
            if w is None:
                continue
            try:
                if isinstance(w, tk.Button):
                    w.configure(bg=primary, fg="#ffffff", activebackground=primary)
                else:
                    w.configure(bg=bg, fg=fg)
            except Exception:
                pass

        # amplitude bar 颜色
        try:
            self.amplitude_bar.itemconfig('bar', fill=self.primary_color if not self.dark_mode else '#00FFAA')
            self.amplitude_bar.configure(bg="#f5f5f5" if not self.dark_mode else "#000000")
        except Exception:
            pass
            
        # 进度条颜色
        try:
            progress_color = "#0a84ff" if not self.dark_mode else "#00FFAA"
            bg_color = "#f0f0f0" if not self.dark_mode else "#333333"
            self.progress_canvas.configure(bg=bg_color)
            self.progress_canvas.itemconfig(self.progress_rect, fill=progress_color)
        except Exception:
            pass
            
    def update_time(self):
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def update_noise_level(self):
        try:
            if not self.noise_detector.audio_queue.empty():
                audio_data = self.noise_detector.audio_queue.get_nowait()
                db_value = self.noise_detector.calculate_db(audio_data)
                if hasattr(self, 'last_db_value'):
                    db_value = 0.7 * self.last_db_value + 0.3 * db_value
                self.last_db_value = db_value
                self.update_amplitude_bar(db_value)
        except queue.Empty:
            pass
        self.root.after(50, self.update_noise_level)

    def update_amplitude_bar(self, db_value):
        norm = min(max((db_value - 10) / 60, 0), 1)
        r = int(255 * norm)
        g = int(255 * (1 - norm))
        color = f"#{r:02x}{g:02x}00"
        coords = self.amplitude_bar.coords("bar")
        current_width = coords[2] if coords else 0
        target_width = norm * 300
        easing_factor = 0.1
        new_width = current_width + (target_width - current_width) * easing_factor
        self.amplitude_bar.coords("bar", 0, 0, new_width, 40)
        self.amplitude_bar.itemconfig("bar", fill=color)

    def update_gui_display(self):
        if hasattr(self, 'last_db_value'):
            self.noise_label.config(text=f"当前噪音：{self.last_db_value:.1f} dB")
        self.root.after(1500, self.update_gui_display)

    def update_countdown(self):
        if not hasattr(self, 'schedule') or not self.schedule:
            self.countdown_label.config(text="无已载入的时间表")
            self.root.after(2000, self.update_countdown)
            return

        current_time = time.localtime()
        current_minutes = current_time.tm_hour * 60 + current_time.tm_min
        for i, (start, end, period_name) in enumerate(self.schedule, start=1):
            if start <= current_minutes <= end:
                remaining_minutes = end - current_minutes
                self.countdown_label.config(text=f"距离 {period_name} 结束还剩：{remaining_minutes} 分钟")
                
                # 更新进度条
                total_duration = end - start
                elapsed = current_minutes - start
                progress_ratio = elapsed / total_duration if total_duration > 0 else 0
                
                # 获取画布宽度并计算进度条长度
                canvas_width = self.progress_canvas.winfo_width()
                if canvas_width <= 1:  # 初始化时可能为1
                    canvas_width = 800  # 使用默认宽度
                    
                progress_width = int(canvas_width * progress_ratio)
                self.progress_canvas.coords(self.progress_rect, 0, 0, progress_width, 10)
                break
        else:
            self.countdown_label.config(text="无已载入的时间表")
            # 没有活动时清空进度条
            self.progress_canvas.coords(self.progress_rect, 0, 0, 0, 10)
            
            # 检查是否已过最后一个时间段，如果是则自动退出程序
            if self.schedule and current_minutes > max(end for start, end, name in self.schedule):
                self.auto_exit()

        self.root.after(2000, self.update_countdown)
    
    def auto_exit(self):
        """自动退出程序"""
        # 显示提示信息
        tk.messagebox.showinfo("自习结束", "所有自习时间段已结束，程序将自动退出。")
        
        # 5秒后退出程序
        self.root.after(5000, self.root.destroy)

    def open_settings_window(self):
        # 传递 self 以便 SettingsWindow 能访问和修改 dark_mode
        SettingsWindow(self.root, self.noise_detector, self.apply_theme)
        
    def open_activity_config(self):
        """打开活动配置窗口"""
        ActivityConfigurator(self.root)
        
    def minimize_window(self):
        self.root.iconify()
