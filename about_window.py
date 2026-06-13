import tkinter as tk
from tkinter import ttk, scrolledtext
import urllib.request
import urllib.error
import ssl
import json
import webbrowser
import os
from typing import Optional
import time
from tkinter import messagebox
import threading

# 导入更新模块
try:
    from updater import Updater
    UPDATER_AVAILABLE = True
except ImportError:
    UPDATER_AVAILABLE = False
    print("提示：未找到更新模块")

# 尝试导入markdown库，如果没有安装则使用简单处理
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("提示：未安装markdown库，将使用简单格式处理。如需完整Markdown支持，请运行 'pip install markdown'")


class AboutWindow:
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title("关于自习看板")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # 当前版本号
        self.current_version = "1.1.0"
        
        # 初始化更新器
        if UPDATER_AVAILABLE:
            self.updater = Updater(self.current_version)
        else:
            self.updater = None
        
        # 用于跟踪上次检查更新的时间和点击次数
        self.last_check_time = 0
        self.check_click_count = 0
        self.repo_url = "https://github.com/lic06/Selfstudy_boards"
        
        self.init_ui()
        self.load_readme()
    
    def init_ui(self):
        # 创建主框架
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题标签
        title_label = tk.Label(main_frame, text="自习课大屏幕看板", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 版本信息
        version_frame = tk.Frame(main_frame)
        version_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.version_label = tk.Label(version_frame, text=f"当前版本: v{self.current_version}", font=("微软雅黑", 10))
        self.version_label.pack(side=tk.LEFT)
        
        self.update_button = tk.Button(version_frame, text="检查更新", command=self.check_for_updates)
        self.update_button.pack(side=tk.RIGHT)
        
        # 创建文本显示区域
        text_frame = tk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动文本框
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            state=tk.DISABLED
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # 创建状态栏
        self.status_bar = tk.Label(
            main_frame,
            text="就绪",
            font=("微软雅黑", 9),
            anchor=tk.W,
            relief=tk.SUNKEN
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 更新信息框架（初始隐藏）
        self.update_frame = tk.Frame(main_frame)
        self.update_frame.pack(fill=tk.X, pady=(10, 0))
        self.update_frame.pack_forget()
        
        update_label = tk.Label(self.update_frame, text="发现新版本!", font=("微软雅黑", 12, "bold"), fg="red")
        update_label.pack(side=tk.LEFT)
        
        self.download_button = tk.Button(self.update_frame, text="前往下载", command=self.open_release_page)
        self.download_button.pack(side=tk.RIGHT)
        
        self.latest_version_label = tk.Label(self.update_frame, text="", font=("微软雅黑", 10))
        self.latest_version_label.pack(side=tk.RIGHT, padx=(0, 10))
    
    def load_readme(self):
        """加载README文件"""
        # 首先尝试从GitHub获取README
        github_content = self.fetch_github_readme()
        if github_content:
            self.display_content(github_content)
            self.status_bar.config(text="已加载: GitHub在线文档")
            return
        
        # 如果GitHub获取失败，尝试本地文件
        readme_files = [
            "README.md",
            "readme.md",
            "README.markdown",
            "readme.markdown",
            "README.txt",
            "readme.txt",
            "README"
        ]
        
        readme_path = None
        for filename in readme_files:
            path = os.path.join(os.getcwd(), filename)
            if os.path.exists(path):
                readme_path = path
                break
        
        if readme_path:
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.display_content(content)
                self.status_bar.config(text=f"已加载: {os.path.basename(readme_path)} (本地文件)")
            except Exception as e:
                self.display_error(f"无法读取 README 文件: {str(e)}")
                self.status_bar.config(text="加载失败")
        else:
            self.display_error("未找到 README 文件")
            self.status_bar.config(text="文件未找到")
    
    def fetch_github_readme(self):
        """从GitHub获取README文件"""
        try:
            # GitHub README URL
            url = "https://raw.githubusercontent.com/9duol/SelfStudy_Dashboard/main/README.md"
            
            # 创建请求对象
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # 创建SSL上下文
            context = ssl.create_default_context()
            
            # 发送请求，设置5秒超时
            response = urllib.request.urlopen(request, context=context, timeout=5)
            content = response.read().decode('utf-8')
            return content
        except urllib.error.URLError as e:
            print(f"无法从GitHub获取README: {e}")
            return None
        except ssl.SSLError as e:
            print(f"SSL错误: {e}")
            return None
        except Exception as e:
            print(f"获取GitHub README时发生未知错误: {e}")
            return None
    
    def display_content(self, content: str):
        """显示README内容"""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        
        # 根据是否可用markdown库选择处理方式
        if MARKDOWN_AVAILABLE:
            try:
                # 转换Markdown为HTML，然后简化处理
                html = markdown.markdown(content)
                processed_content = self.simple_html_to_text(html)
            except Exception as e:
                # 如果Markdown处理失败，回退到简单处理
                processed_content = self.simple_markdown_to_text(content)
        else:
            # 如果没有markdown库，使用简单处理
            processed_content = self.simple_markdown_to_text(content)
        
        self.text_area.insert(tk.END, processed_content)
        self.text_area.config(state=tk.DISABLED)
    
    def display_error(self, error_msg: str):
        """显示错误信息"""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, error_msg)
        self.text_area.config(state=tk.DISABLED)
    
    def simple_html_to_text(self, html: str) -> str:
        """简单的HTML转文本处理"""
        import re
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', html)
        # 处理一些特殊字符
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        return text
    
    def simple_markdown_to_text(self, content: str) -> str:
        """简单的Markdown转文本处理"""
        import re
        # 处理标题
        content = re.sub(r'^# (.+)$', r'【\1】\n', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'● \1\n', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'■ \1\n', content, flags=re.MULTILINE)
        
        # 处理粗体和斜体
        content = re.sub(r'\*\*(.*?)\*\*', r'【\1】', content)
        content = re.sub(r'__(.*?)__', r'【\1】', content)
        content = re.sub(r'\*(.*?)\*', r'《\1》', content)
        content = re.sub(r'_(.*?)_', r'《\1》', content)
        
        # 处理行内代码
        content = re.sub(r'`(.*?)`', r'『\1』', content)
        
        # 处理链接
        content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', content)
        
        # 处理列表
        content = re.sub(r'^\s*[-*]\s+(.+)$', r'• \1', content, flags=re.MULTILINE)
        
        # 处理引用
        content = re.sub(r'^>\s+(.+)$', r'『引用』\1', content, flags=re.MULTILINE)
        
        return content
    
    def check_for_updates(self):
        """检查更新"""
        current_time = time.time()
        
        # 检查是否在3秒内再次点击
        if current_time - self.last_check_time < 3 and self.check_click_count >= 1:
            # 打开仓库页面
            webbrowser.open(self.repo_url)
            self.status_bar.config(text="正在打开项目仓库页面...")
            return
        
        # 更新点击计数和时间
        self.check_click_count += 1
        self.last_check_time = current_time
        
        self.status_bar.config(text="正在检查更新...")
        self.update_button.config(state=tk.DISABLED)  # 禁用按钮防止重复点击
        self.window.update_idletasks()
        
        # 如果有更新器，使用新方法检查更新
        if self.updater:
            self.updater.check_for_updates(self.update_check_callback)
        else:
            # 否则使用旧方法
            self._check_updates_old()
    
    def update_check_callback(self, update_info, error):
        """更新检查回调函数"""
        # 重新启用按钮
        self.update_button.config(state=tk.NORMAL)
        
        if error:
            self.hide_update_info()
            self.status_bar.config(text=f"检查更新失败: {error}")
        elif update_info:
            # 有新版本
            self.show_update_available(update_info["version"], update_info["assets"])
            self.status_bar.config(text=f"发现新版本: v{update_info['version']}")
        else:
            # 已是最新版本
            self.hide_update_info()
            self.status_bar.config(text="当前已是最新版本")
    
    def _check_updates_old(self):
        """旧的检查更新方法"""
        try:
            # GitHub Releases API URL
            url = "https://api.github.com/repos/lic06/Selfstudy_boards/releases/latest"
            
            # 创建请求对象
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # 创建SSL上下文
            context = ssl.create_default_context()
            
            # 发送请求，设置5秒超时
            response = urllib.request.urlopen(request, context=context, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            
            latest_version = data.get('tag_name', '').lstrip('v')  # 移除可能的'v'前缀
            release_url = data.get('html_url', '')
            
            if latest_version and self.is_newer_version(latest_version, self.current_version):
                # 有新版本
                self.show_update_available(latest_version, release_url)
                self.status_bar.config(text=f"发现新版本: v{latest_version}")
            else:
                # 已是最新版本
                self.hide_update_info()
                self.status_bar.config(text="当前已是最新版本")
                
        except Exception as e:
            self.hide_update_info()
            self.status_bar.config(text=f"检查更新失败，请再次点击跳转到仓库")
        finally:
            self.update_button.config(state=tk.NORMAL)  # 重新启用按钮
    
    def is_newer_version(self, latest_version: str, current_version: str) -> bool:
        """比较版本号，判断是否有新版本"""
        try:
            latest_parts = [int(x) for x in latest_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]
            
            for i in range(min(len(latest_parts), len(current_parts))):
                if latest_parts[i] > current_parts[i]:
                    return True
                elif latest_parts[i] < current_parts[i]:
                    return False
            
            # 如果前面的部分都相等，但latest版本号更长，则认为有新版本
            return len(latest_parts) > len(current_parts)
        except Exception:
            # 版本号格式异常时，进行简单字符串比较
            return latest_version > current_version
    
    def show_update_available(self, latest_version: str, assets):
        """显示更新信息"""
        self.latest_version_label.config(text=f"最新版本: v{latest_version}")
        self.update_frame.assets = assets  # 保存资产信息
        self.update_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 更新下载按钮功能
        self.download_button.config(text="自动更新", command=self.auto_update)
    
    def auto_update(self):
        """自动更新程序"""
        if not self.updater:
            messagebox.showerror("错误", "更新模块不可用")
            return
        
        if not hasattr(self.update_frame, 'assets'):
            messagebox.showerror("错误", "没有可用的更新文件")
            return
        
        # 确认更新
        if not messagebox.askyesno("确认更新", 
                                  f"确定要更新到版本 {self.update_frame.assets[0]['name']} 吗？\n\n"
                                  "更新过程中程序将被替换，完成后需要重启程序。"):
            return
        
        # 禁用更新按钮
        self.download_button.config(state=tk.DISABLED, text="正在更新...")
        self.status_bar.config(text="正在下载更新...")
        
        # 开始下载更新
        self.updater.download_latest_release(
            self.update_frame.assets, 
            self.download_progress_callback, 
            self.download_completion_callback
        )
    
    def download_progress_callback(self, percent, message):
        """下载进度回调"""
        self.status_bar.config(text=message)
        self.window.update_idletasks()
    
    def download_completion_callback(self, file_path, error):
        """下载完成回调"""
        if error:
            self.status_bar.config(text=f"下载失败: {error}")
            self.download_button.config(state=tk.NORMAL, text="自动更新")
            messagebox.showerror("更新失败", error)
        elif file_path:
            # 应用更新
            success, message = self.updater.apply_update(file_path)
            if success:
                self.status_bar.config(text=message)
                messagebox.showinfo("更新成功", message + "\n\n程序将退出，请手动重启。")
                self.root.quit()
            else:
                self.status_bar.config(text=message)
                self.download_button.config(state=tk.NORMAL, text="自动更新")
                messagebox.showerror("更新失败", message)
    
    def hide_update_info(self):
        """隐藏更新信息"""
        self.update_frame.pack_forget()
        # 恢复按钮文本和命令
        self.download_button.config(text="前往下载", command=self.open_release_page)
    
    def open_release_page(self):
        """打开发布页面"""
        if hasattr(self.update_frame, 'release_url'):
            webbrowser.open(self.update_frame.release_url)
