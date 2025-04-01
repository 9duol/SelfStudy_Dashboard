import tkinter as tk
from tkinter import messagebox
import time
import threading
import pyaudio
import numpy as np

class SchoolDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("自习课大屏幕看板")
        self.root.attributes('-fullscreen', True)  # 全屏模式
        self.root.configure(bg="black")  # 设置背景为黑色

        # 时间标签
        self.time_label = tk.Label(root, text="", font=("Times New Rouma", 60), fg="white", bg="black")
        self.time_label.pack(pady=20)

        # 纪律提醒
        self.reminder_label = tk.Label(root, text="当前活动：自习 请保持安静", font=("宋体", 36), fg="white", bg="black")
        self.reminder_label.pack(pady=20)

        # 噪音分贝显示
        self.noise_label = tk.Label(root, text=" 0 dB", font=("宋体", 20), fg="white", bg="black")
        self.noise_label.pack(pady=20)

        # 设置按钮
        self.settings_button = tk.Button(root, text="设置", font=("宋体", 14), command=self.open_settings_window, fg="white", bg="gray", 
                                         relief="flat", highlightbackground="white", highlightthickness=2)
        self.settings_button.pack(pady=10)
        self.settings_button.configure(width=6, height=1)
        self.settings_button.place(x=20, y=root.winfo_screenheight() - 100)  # 调整到左下角

        # 退出按钮
        self.exit_button = tk.Button(root, text="退出", font=("宋体", 14), command=self.exit_program, fg="white", bg="gray", 
                                     relief="flat", highlightbackground="white", highlightthickness=2)
        self.exit_button.pack(pady=10)
        self.exit_button.configure(width=6, height=1)
        self.exit_button.place(x=20, y=root.winfo_screenheight() - 50)  # 调整到左下角，紧挨设置按钮下方

        # 调整组件位置到屏幕中间
        # 调整时间标签的位置到屏幕上方的四分之一处
        self.time_label.pack_configure(anchor="center", pady=(root.winfo_screenheight() // 4, 10))
        # 调整纪律提醒标签的位置到时间标签下方
        self.reminder_label.pack_configure(anchor="center", pady=10)
        # 调整噪音分贝显示标签的位置到纪律提醒标签下方
        self.noise_label.pack_configure(anchor="center", pady=10)

        # 启动时间更新线程
        self.update_time()

        # 启动噪音检测线程
        self.running = True
        self.noise_thread = threading.Thread(target=self.update_noise_level)
        self.noise_thread.start()

    def update_time(self):
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def open_settings_window(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x200")
        settings_window.configure(bg="black")

        sensitivity_label = tk.Label(settings_window, text="灵敏度调整", font=("宋体", 20), fg="white", bg="black")
        sensitivity_label.pack(pady=10)

        sensitivity_slider = tk.Scale(settings_window, from_=1, to=10, orient="horizontal", length=300, 
                                      font=("宋体", 14), fg="white", bg="black", 
                                      highlightbackground="black", troughcolor="gray")
        sensitivity_slider.set(self.sensitivity_slider.get() if hasattr(self, 'sensitivity_slider') else 5)
        sensitivity_slider.pack(pady=10)

        def save_settings():
            self.sensitivity_slider_value = sensitivity_slider.get()
            settings_window.destroy()

        save_button = tk.Button(settings_window, text="保存", font=("宋体", 14), command=save_settings, fg="white", bg="gray", 
                                relief="flat", highlightbackground="white", highlightthickness=2)
        save_button.pack(pady=10)

    def update_noise_level(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        while self.running:
            data = np.frombuffer(stream.read(1024, exception_on_overflow=False), dtype=np.int16)
            rms = np.sqrt(np.mean(np.square(data)))
            decibel = 20 * np.log10(rms + 1e-6)  # 防止log(0)

            # 根据灵敏度系数调整噪音显示
            sensitivity = getattr(self, 'sensitivity_slider_value', 5)  # 使用保存的灵敏度值
            adjusted_decibel = decibel * (sensitivity / 5)  # 灵敏度系数影响噪音值
            self.noise_label.config(text=f" {adjusted_decibel:.2f} dB")
            time.sleep(3)  # 调整刷新速度为每3秒
        stream.stop_stream()
        stream.close()
        p.terminate()

    def exit_program(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolDashboard(root)
    root.mainloop()
