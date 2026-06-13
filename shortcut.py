import os
import sys


def create_shortcut():
    """在桌面创建指向当前脚本的快捷方式（Windows）。如果已存在则跳过。"""
    try:
        import win32com.client
    except Exception:
        print("pywin32 未安装，无法创建快捷方式")
        return

    current_file_path = os.path.abspath(sys.argv[0])
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    shortcut_path = os.path.join(desktop_path, "自习看板.lnk")

    if not os.path.exists(shortcut_path):
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = current_file_path
        shortcut.WorkingDirectory = os.path.dirname(current_file_path)
        shortcut.IconLocation = current_file_path
        shortcut.save()
        print("快捷方式已创建")
    else:
        print("快捷方式已存在，跳过创建")
