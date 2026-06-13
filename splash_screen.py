import tkinter as tk
import time
import threading
import os
import json
import configparser

class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.splash = tk.Toplevel(root)
        self.splash.title("启动中...")
        self.splash.geometry("600x400")
        self.splash.configure(bg="#2c3e50")
        self.splash.overrideredirect(True)  # 去掉窗口边框

        # 居中显示
        self.center_window()
        
        # 创建UI元素
        self.create_widgets()
        
        # 启动信息 - 已细化为更真实的加载步骤
        self.messages = [
            "正在加载配置文件...",
            "正在检查 schedule.json...",
            "正在解析课程表配置...",
            "正在初始化组件...",
            "正在启动音频检测模块...",
            "正在加载课程表...",
            "启动完成，正在进入主界面..."
        ]
        self.current_message_index = 0
        self.current_progress = 0
        self.target_progress = 0

    def center_window(self):
        """将启动窗口居中显示"""
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.splash.winfo_screenheight() // 2) - (400 // 2)
        self.splash.geometry(f"600x400+{x}+{y}")

    def create_widgets(self):
        """创建启动界面的UI元素"""
        # 程序标题
        title_frame = tk.Frame(self.splash, bg="#2c3e50")
        title_frame.pack(expand=True, fill="both", pady=(50, 0))
        
        title_label = tk.Label(
            title_frame, 
            text="自习课大屏幕看板", 
            font=("微软雅黑", 28, "bold"), 
            bg="#2c3e50", 
            fg="#ecf0f1"
        )
        title_label.pack(pady=(0, 10))
        
        # 版本号
        version_label = tk.Label(
            title_frame, 
            text="版本号：v1.1.0", 
            font=("微软雅黑", 14), 
            bg="#2c3e50", 
            fg="#bdc3c7"
        )
        version_label.pack()
        
        # 进度条容器
        progress_container = tk.Frame(self.splash, bg="#2c3e50")
        progress_container.pack(pady=(30, 20))
        
        # 进度条
        self.progress_canvas = tk.Canvas(
            progress_container, 
            width=400, 
            height=10, 
            bg="#34495e", 
            highlightthickness=0
        )
        self.progress_canvas.pack()
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, 10, 
            fill="#3498db", 
            outline=""
        )
        
        # 状态信息显示
        self.status_frame = tk.Frame(self.splash, bg="#2c3e50")
        self.status_frame.pack(fill="x", padx=50)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="正在准备启动...",
            font=("微软雅黑", 12),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        self.status_label.pack()
        
        # 控制台输出区域
        console_frame = tk.LabelFrame(
            self.splash, 
            text="启动日志", 
            font=("微软雅黑", 10),
            bg="#2c3e50",
            fg="#ecf0f1",
            padx=10,
            pady=10
        )
        console_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        self.console_text = tk.Text(
            console_frame,
            font=("Consolas", 9),
            bg="#34495e",
            fg="#ecf0f1",
            height=6,
            state="disabled"
        )
        self.console_text.pack(fill="both", expand=True)
        
        # 滚动条
        console_scrollbar = tk.Scrollbar(self.console_text)
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_text.config(yscrollcommand=console_scrollbar.set)
        console_scrollbar.config(command=self.console_text.yview)

    def log_message(self, message):
        """向控制台输出信息"""
        self.console_text.config(state="normal")
        self.console_text.insert("end", f"> {message}\n")
        self.console_text.config(state="disabled")
        self.console_text.see("end")

    def load_config_process(self):
        """真实加载配置文件的过程"""
        # 步骤1: 检查 schedule.json
        self.update_status(0, "正在检查配置文件...")
        self.log_message("检查 schedule.json 文件")
        time.sleep(0.5)
        
        json_file = "schedule.json"
        if os.path.exists(json_file):
            self.log_message(f"找到配置文件: {json_file}")
            self.update_status(15, "正在读取 schedule.json...")
            
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    activities = data.get("activities", [])
                    self.log_message(f"成功加载 {len(activities)} 个活动配置")
                    time.sleep(0.5)
            except json.JSONDecodeError as e:
                self.log_message(f"JSON格式错误: {e}")
                time.sleep(0.5)
            except Exception as e:
                self.log_message(f"读取JSON课程时间表失败: {e}")
                time.sleep(0.5)
        else:
            self.log_message("未找到 schedule.json，将尝试加载INI配置文件")
            time.sleep(0.5)
            
            # 步骤2: 检查 schedule.ini
            ini_file = "schedule.ini"
            self.update_status(20, "正在检查 schedule.ini...")
            if os.path.exists(ini_file):
                self.log_message(f"找到配置文件: {ini_file}")
                try:
                    config = configparser.ConfigParser()
                    config.read(ini_file, encoding='utf-8')
                    if 'Schedule' in config:
                        count = len([key for key in config['Schedule'].keys() if key.startswith('period')])
                        self.log_message(f"成功加载 {count} 个时段配置")
                    time.sleep(0.5)
                except Exception as e:
                    self.log_message(f"读取INI课程时间表失败: {e}")
                    time.sleep(0.5)
            else:
                self.log_message("未找到 schedule.ini，将使用默认配置")
                time.sleep(0.5)
        
        # 步骤3: 初始化其他组件
        self.update_status(40, "正在初始化组件...")
        self.log_message("初始化界面组件")
        time.sleep(0.3)
        
        self.update_status(60, "正在启动音频检测模块...")
        self.log_message("启动音频检测模块")
        time.sleep(0.3)
        
        self.update_status(80, "正在加载课程表...")
        self.log_message("加载课程表数据")
        time.sleep(0.3)
        
        # 步骤4: 完成启动
        self.update_status(100, "启动完成，正在进入主界面...")
        self.log_message("启动完成")
        time.sleep(0.5)
        
        # 完成启动
        self.status_label.config(text="启动完成！")
        self.splash.after(500, self.close)

    def update_status(self, progress, message):
        """更新状态和进度"""
        self.target_progress = progress
        self.status_label.config(text=message)
        self.log_message(message)
        self.update_progress_smooth()
        
        # 如果进度达到100%，则关闭启动屏幕
        if progress >= 100:
            self.splash.after(500, self.close)

    def update_progress_smooth(self):
        """平滑更新进度条"""
        if self.current_progress < self.target_progress:
            self.current_progress += 1
            progress_width = (self.current_progress / 100) * 400
            self.progress_canvas.coords(self.progress_fill, 0, 0, progress_width, 10)
            self.splash.after(10, self.update_progress_smooth)

    def update_progress(self):
        """启动配置加载流程，在后台线程执行"""
        # 使用线程避免阻塞UI
        threading.Thread(target=self.load_config_process, daemon=True).start()

    def show(self):
        """显示启动页面并开始动画"""
        self.update_progress()

    def close(self):
        """关闭启动页面并显示主窗口"""
        self.splash.destroy()
        self.root.deiconify()