import tkinter as tk
from tkinter import ttk
import sounddevice as sd
# 导入关于窗口
from about_window import AboutWindow


class SettingsWindow:
    def __init__(self, root, noise_detector, apply_theme_callback):
        self.root = root
        self.noise_detector = noise_detector
        self.apply_theme_callback = apply_theme_callback
        self.dark_mode = False

        self.window = tk.Toplevel(self.root)
        self.window.title("设置")
        self.window.geometry("500x600")
        self.window.configure(bg="#111111" if self.dark_mode else "#ffffff")
        self.window.resizable(False, False)

        self.init_ui()

    def init_ui(self):
        # 标题
        title_label = tk.Label(self.window, text="设置", font=("微软雅黑", 18, "bold"),
                               fg="#ffffff" if self.dark_mode else "#222222",
                               bg="#111111" if self.dark_mode else "#ffffff")
        title_label.pack(pady=10)

        # 创建退出按钮并放置在右上角
        exit_button = tk.Button(self.window, text="退出程序", font=("微软雅黑", 14, "bold"), 
                               command=self.root.destroy,
                               fg="#ffffff", bg="#ff3b30", relief="flat",
                               width=10, height=1)
        exit_button.place(relx=1.0, x=-10, y=10, anchor="ne")

        # 创建笔记本控件（选项卡）
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 设备设置选项卡
        self.create_device_tab(notebook)
        
        # 应用设置选项卡
        self.create_application_tab(notebook)
        
        # 关于选项卡
        self.create_about_tab(notebook)

    def create_device_tab(self, notebook):
        """创建设备设置选项卡"""
        device_frame = tk.Frame(notebook, bg="#111111" if self.dark_mode else "#ffffff")
        notebook.add(device_frame, text="设备设置")
        
        # 录音设备选择
        device_label = tk.Label(device_frame, text="录音设备：", font=("微软雅黑", 12),
                               fg="#ffffff" if self.dark_mode else "#222222",
                               bg="#111111" if self.dark_mode else "#ffffff")
        device_label.pack(pady=(20, 5), anchor="w", padx=20)
        
        devices = sd.query_devices()
        device_names = [f"{i}: {dev['name']}" for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        
        self.device_var = tk.StringVar()
        device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, values=device_names, width=50)
        device_combo.pack(pady=5, padx=20, fill="x")
        default_device_index = self.noise_detector.current_device or 0
        if device_names:
            device_combo.set(device_names[default_device_index])
        
        # 灵敏度调节
        sensitivity_label = tk.Label(device_frame, text="检测灵敏度：", font=("微软雅黑", 12),
                                    fg="#ffffff" if self.dark_mode else "#222222",
                                    bg="#111111" if self.dark_mode else "#ffffff")
        sensitivity_label.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.sensitivity_scale = ttk.Scale(device_frame, from_=0.5, to=2.0, orient="horizontal", length=300)
        self.sensitivity_scale.set(self.noise_detector.sensitivity)
        self.sensitivity_scale.pack(pady=5, padx=20, fill="x")
        
        # 灵敏度值显示
        self.sensitivity_value = tk.Label(device_frame, text=f"当前值: {self.noise_detector.sensitivity:.2f}", 
                                         font=("微软雅黑", 10),
                                         fg="#ffffff" if self.dark_mode else "#666666",
                                         bg="#111111" if self.dark_mode else "#ffffff")
        self.sensitivity_value.pack(pady=5, anchor="w", padx=20)
        
        # 绑定灵敏度调节事件
        self.sensitivity_scale.configure(command=self.update_sensitivity_display)
        
        # 基准线校准
        calibration_label = tk.Label(device_frame, text="基准线校准：", font=("微软雅黑", 12),
                                    fg="#ffffff" if self.dark_mode else "#222222",
                                    bg="#111111" if self.dark_mode else "#ffffff")
        calibration_label.pack(pady=(20, 5), anchor="w", padx=20)
        
        calibrate_frame = tk.Frame(device_frame, bg="#111111" if self.dark_mode else "#ffffff")
        calibrate_frame.pack(pady=5, fill="x", padx=20)
        
        calibrate_min_button = tk.Button(calibrate_frame, text="校准最小基准线", font=("微软雅黑", 10),
                                         command=self.noise_detector.calibrate_min_baseline,
                                         fg="#ffffff", bg="#555555", relief="flat")
        calibrate_min_button.pack(side="left", padx=(0, 10))
        
        calibrate_max_button = tk.Button(calibrate_frame, text="校准最大基准线", font=("微软雅黑", 10),
                                         command=self.noise_detector.calibrate_max_baseline,
                                         fg="#ffffff", bg="#555555", relief="flat")
        calibrate_max_button.pack(side="left")

    def create_application_tab(self, notebook):
        """创建应用设置选项卡"""
        app_frame = tk.Frame(notebook, bg="#111111" if self.dark_mode else "#ffffff")
        notebook.add(app_frame, text="应用设置")
        
        # 主题设置
        theme_label = tk.Label(app_frame, text="主题设置：", font=("微软雅黑", 12),
                              fg="#ffffff" if self.dark_mode else "#222222",
                              bg="#111111" if self.dark_mode else "#ffffff")
        theme_label.pack(pady=(20, 10), anchor="w", padx=20)
        
        theme_frame = tk.Frame(app_frame, bg="#111111" if self.dark_mode else "#ffffff")
        theme_frame.pack(pady=5, fill="x", padx=20)
        
        dark_mode_button = tk.Button(theme_frame, text="切换深浅色模式", font=("微软雅黑", 10), 
                                    command=self.toggle_dark_mode,
                                    fg="#ffffff", bg="#555555", relief="flat")
        dark_mode_button.pack(side="left")
        
        # 刷新主程序
        refresh_label = tk.Label(app_frame, text="界面操作：", font=("微软雅黑", 12),
                                fg="#ffffff" if self.dark_mode else "#222222",
                                bg="#111111" if self.dark_mode else "#ffffff")
        refresh_label.pack(pady=(20, 10), anchor="w", padx=20)
        
        refresh_frame = tk.Frame(app_frame, bg="#111111" if self.dark_mode else "#ffffff")
        refresh_frame.pack(pady=5, fill="x", padx=20)
        
        refresh_button = tk.Button(refresh_frame, text="刷新主程序", font=("微软雅黑", 10), 
                                  command=self.refresh_main_ui,
                                  fg="#ffffff", bg="#ff9500", relief="flat")
        refresh_button.pack(side="left", padx=(0, 10))
        
        # 保存设置
        save_label = tk.Label(app_frame, text="保存设置：", font=("微软雅黑", 12),
                             fg="#ffffff" if self.dark_mode else "#222222",
                             bg="#111111" if self.dark_mode else "#ffffff")
        save_label.pack(pady=(20, 10), anchor="w", padx=20)
        
        save_frame = tk.Frame(app_frame, bg="#111111" if self.dark_mode else "#ffffff")
        save_frame.pack(pady=5, fill="x", padx=20)
        
        save_button = tk.Button(save_frame, text="保存当前设置", font=("微软雅黑", 10), 
                               command=self.save_settings,
                               fg="#ffffff", bg="#0a84ff", relief="flat")
        save_button.pack(side="left", padx=(0, 10))

    def create_about_tab(self, notebook):
        """创建关于选项卡"""
        about_frame = tk.Frame(notebook, bg="#111111" if self.dark_mode else "#ffffff")
        notebook.add(about_frame, text="关于")
        
        # 关于信息
        info_frame = tk.Frame(about_frame, bg="#111111" if self.dark_mode else "#ffffff")
        info_frame.pack(pady=20, fill="both", expand=True)
        
        app_name = tk.Label(info_frame, text="自习看板程序", font=("微软雅黑", 16, "bold"),
                           fg="#ffffff" if self.dark_mode else "#222222",
                           bg="#111111" if self.dark_mode else "#ffffff")
        app_name.pack(pady=(20, 5))
        
        version = tk.Label(info_frame, text="版本: 1.1.0", font=("微软雅黑", 10),
                          fg="#ffffff" if self.dark_mode else "#666666",
                          bg="#111111" if self.dark_mode else "#ffffff")
        version.pack(pady=5)
        
        description = tk.Label(info_frame, text="专注自习室管理的看板系统", font=("微软雅黑", 10),
                              fg="#ffffff" if self.dark_mode else "#444444",
                              bg="#111111" if self.dark_mode else "#ffffff")
        description.pack(pady=5)
        
        # 按钮区域
        button_frame = tk.Frame(info_frame, bg="#111111" if self.dark_mode else "#ffffff")
        button_frame.pack(pady=30)
        
        about_button = tk.Button(button_frame, text="查看详细信息", font=("微软雅黑", 10), 
                                command=self.open_about,
                                fg="#ffffff", bg="#34c759", relief="flat")
        about_button.pack(side="left", padx=10)
        
        check_update_button = tk.Button(button_frame, text="检查更新", font=("微软雅黑", 10), 
                                       command=self.check_updates,
                                       fg="#ffffff", bg="#555555", relief="flat")
        check_update_button.pack(side="left", padx=10)

    def update_sensitivity_display(self, value):
        """更新灵敏度显示"""
        self.sensitivity_value.config(text=f"当前值: {float(value):.2f}")

    def refresh_main_ui(self):
        """强制刷新主程序UI"""
        # 重新应用主题
        self.apply_theme_callback()
        
        # 重新加载课程表
        if hasattr(self.root, 'load_schedule_async'):
            self.root.load_schedule_async()
        elif hasattr(self.root, 'app') and hasattr(self.root.app, 'load_schedule_async'):
            self.root.app.load_schedule_async()
        else:
            # 直接调用UI中的加载方法
            self.root.load_schedule_and_update_ui()
        
        # 更新窗口标题
        self.root.title("自习课大屏幕看板")
        
        # 强制更新所有组件
        self.root.update_idletasks()
        self.root.update()
        
        # 显示提示信息
        tk.messagebox.showinfo("刷新完成", "主程序UI已刷新完成")

    def open_about(self):
        """打开关于窗口"""
        AboutWindow(self.root)
        
    def check_updates(self):
        """检查更新"""
        # 使用关于窗口进行检查更新
        AboutWindow.check_for_updates_standalone(self.root)

    def save_settings(self):
        try:
            selected_device = int(self.device_var.get().split(':')[0])
        except Exception:
            selected_device = self.noise_detector.current_device or 0
        self.noise_detector.stop()
        self.noise_detector.current_device = selected_device
        self.noise_detector.sensitivity = self.sensitivity_scale.get()
        self.noise_detector.start()

        # 应用主题更改
        self.apply_theme_callback()

        tk.messagebox.showinfo("保存成功", "设置已保存")
        self.window.destroy()

    def toggle_dark_mode(self):
        # 更新主程序的 dark_mode 状态
        self.root.dark_mode = not self.root.dark_mode
        # 调用主程序的主题应用回调
        self.apply_theme_callback()

        # 更新设置窗口背景颜色
        self.window.configure(bg="#111111" if self.root.dark_mode else "#ffffff")

        # 重新初始化 UI 以更新颜色
        for widget in self.window.winfo_children():
            widget.destroy()
        self.init_ui()