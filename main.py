import tkinter as tk
from ui import SchoolDashboard, SplashScreen  # 导入启动页面
from shortcut import create_shortcut


if __name__ == "__main__":
    # 在程序运行前创建快捷方式（尝试，若失败会打印提示）
    create_shortcut()

    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口，等待启动页面完成

    # 启动主程序
    app = SchoolDashboard(root)

    # 启动GUI显示数值更新
    app.update_gui_display()

    root.mainloop()
