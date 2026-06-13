import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from typing import List, Tuple


class ActivityConfigurator:
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title("活动配置")
        self.window.geometry("600x500")
        self.window.resizable(True, True)
        
        # 存储活动数据
        self.activities = []
        
        self.init_ui()
        self.load_activities()
        self.refresh_list()
    
    def init_ui(self):
        # 标题
        title_label = tk.Label(self.window, text="活动配置", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=10)
        
        # 活动列表框架
        list_frame = tk.LabelFrame(self.window, text="现有活动", font=("微软雅黑", 12))
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 活动列表
        self.activity_listbox = tk.Listbox(list_frame, font=("微软雅黑", 10), yscrollcommand=scrollbar.set)
        self.activity_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar.config(command=self.activity_listbox.yview)
        
        # 按钮框架
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        # 添加活动按钮
        add_button = tk.Button(button_frame, text="添加活动", font=("微软雅黑", 12), 
                              command=self.add_activity_dialog, width=10)
        add_button.pack(side=tk.LEFT, padx=5)
        
        # 编辑活动按钮
        edit_button = tk.Button(button_frame, text="编辑活动", font=("微软雅黑", 12), 
                               command=self.edit_activity_dialog, width=10)
        edit_button.pack(side=tk.LEFT, padx=5)
        
        # 删除活动按钮
        delete_button = tk.Button(button_frame, text="删除活动", font=("微软雅黑", 12), 
                                 command=self.delete_activity, width=10)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        save_button = tk.Button(button_frame, text="保存配置", font=("微软雅黑", 12), 
                               command=self.save_activities, bg="#0a84ff", fg="white", width=10)
        save_button.pack(side=tk.LEFT, padx=5)
        
        # 双击编辑
        self.activity_listbox.bind('<Double-Button-1>', lambda event: self.edit_activity_dialog())
    
    def load_activities(self):
        """从JSON文件加载活动配置"""
        try:
            if os.path.exists("schedule.json"):
                with open("schedule.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.activities = data.get("activities", [])
            else:
                # 默认活动
                self.activities = [
                    {"name": "晚修1", "start": 1140, "end": 1230},
                    {"name": "晚修2", "start": 1245, "end": 1310}
                ]
        except Exception as e:
            messagebox.showerror("错误", f"加载活动配置时出错: {str(e)}")
            self.activities = []
    
    def save_activities(self):
        """保存活动配置到JSON文件"""
        try:
            data = {"activities": self.activities}
            with open("schedule.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", "活动配置已保存")
        except PermissionError:
            messagebox.showerror("错误", "保存失败：没有权限写入文件，请以管理员身份运行程序或检查文件权限")
        except FileNotFoundError:
            messagebox.showerror("错误", "保存失败：找不到指定路径，请检查程序运行目录")
        except Exception as e:
            messagebox.showerror("错误", f"保存活动配置时出错: {str(e)}")
    
    def refresh_list(self):
        """刷新活动列表显示"""
        self.activity_listbox.delete(0, tk.END)
        for activity in self.activities:
            start_time = f"{activity['start'] // 60:02d}:{activity['start'] % 60:02d}"
            end_time = f"{activity['end'] // 60:02d}:{activity['end'] % 60:02d}"
            display_text = f"{activity['name']} ({start_time} - {end_time})"
            self.activity_listbox.insert(tk.END, display_text)
    
    def add_activity_dialog(self):
        """显示添加活动对话框"""
        dialog = ActivityDialog(self.window, "添加活动")
        self.window.wait_window(dialog.window)
        if dialog.result:
            self.activities.append(dialog.result)
            self.refresh_list()
    
    def edit_activity_dialog(self):
        """显示编辑活动对话框"""
        selection = self.activity_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个活动")
            return
        
        index = selection[0]
        activity = self.activities[index]
        dialog = ActivityDialog(self.window, "编辑活动", activity)
        self.window.wait_window(dialog.window)
        if dialog.result:
            self.activities[index] = dialog.result
            self.refresh_list()
    
    def delete_activity(self):
        """删除选中的活动"""
        selection = self.activity_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个活动")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的活动吗？"):
            index = selection[0]
            del self.activities[index]
            self.refresh_list()
            self.save_activities()


class ActivityDialog:
    def __init__(self, parent, title, activity=None):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("350x400")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        self.result = None
        self.activity = activity
        
        self.init_ui()
        if activity:
            self.populate_fields(activity)
        
        # 居中显示
        self.window.geometry("+%d+%d" % (parent.winfo_rootx()+50, parent.winfo_rooty()+50))
    
    def init_ui(self):
        # 活动名称
        name_frame = tk.Frame(self.window)
        name_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(name_frame, text="活动名称:", font=("微软雅黑", 10)).pack(anchor="w")
        self.name_entry = tk.Entry(name_frame, font=("微软雅黑", 10))
        self.name_entry.pack(fill="x", pady=(5, 0))
        
        # 开始时间
        start_frame = tk.Frame(self.window)
        start_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(start_frame, text="开始时间 (HH:MM):", font=("微软雅黑", 10)).pack(anchor="w")
        
        time_frame = tk.Frame(start_frame)
        time_frame.pack(fill="x", pady=(5, 0))
        
        self.start_hour = tk.Spinbox(time_frame, from_=0, to=23, width=5, font=("微软雅黑", 10))
        self.start_hour.pack(side=tk.LEFT)
        tk.Label(time_frame, text=":", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.start_minute = tk.Spinbox(time_frame, from_=0, to=59, width=5, font=("微软雅黑", 10))
        self.start_minute.pack(side=tk.LEFT)
        
        # 结束时间
        end_frame = tk.Frame(self.window)
        end_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(end_frame, text="结束时间 (HH:MM):", font=("微软雅黑", 10)).pack(anchor="w")
        
        time_frame2 = tk.Frame(end_frame)
        time_frame2.pack(fill="x", pady=(5, 0))
        
        self.end_hour = tk.Spinbox(time_frame2, from_=0, to=23, width=5, font=("微软雅黑", 10))
        self.end_hour.pack(side=tk.LEFT)
        tk.Label(time_frame2, text=":", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.end_minute = tk.Spinbox(time_frame2, from_=0, to=59, width=5, font=("微软雅黑", 10))
        self.end_minute.pack(side=tk.LEFT)
        
        # 按钮
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20, fill="x", padx=20)
        
        ok_button = tk.Button(button_frame, text="确定", font=("微软雅黑", 10), 
                             command=self.ok, width=10)
        ok_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = tk.Button(button_frame, text="取消", font=("微软雅黑", 10), 
                                 command=self.cancel, width=10)
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def populate_fields(self, activity):
        """填充编辑字段"""
        self.name_entry.insert(0, activity["name"])
        self.start_hour.delete(0, tk.END)
        self.start_hour.insert(0, f"{activity['start'] // 60:02d}")
        self.start_minute.delete(0, tk.END)
        self.start_minute.insert(0, f"{activity['start'] % 60:02d}")
        self.end_hour.delete(0, tk.END)
        self.end_hour.insert(0, f"{activity['end'] // 60:02d}")
        self.end_minute.delete(0, tk.END)
        self.end_minute.insert(0, f"{activity['end'] % 60:02d}")
    
    def ok(self):
        """确认按钮处理"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入活动名称")
            return
        
        try:
            start_h = int(self.start_hour.get())
            start_m = int(self.start_minute.get())
            end_h = int(self.end_hour.get())
            end_m = int(self.end_minute.get())
            
            if not (0 <= start_h <= 23 and 0 <= start_m <= 59):
                messagebox.showwarning("警告", "开始时间格式不正确")
                return
            
            if not (0 <= end_h <= 23 and 0 <= end_m <= 59):
                messagebox.showwarning("警告", "结束时间格式不正确")
                return
            
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            
            if start_minutes >= end_minutes:
                messagebox.showwarning("警告", "结束时间必须晚于开始时间")
                return
            
            self.result = {
                "name": name,
                "start": start_minutes,
                "end": end_minutes
            }
            self.window.destroy()
        except ValueError:
            messagebox.showwarning("警告", "时间格式不正确")
    
    def cancel(self):
        """取消按钮处理"""
        self.window.destroy()