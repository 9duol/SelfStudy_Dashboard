import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import re
import urllib.request
import urllib.error
import ssl
from typing import Optional

# 尝试导入markdown库，如果没有安装则使用简单处理
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("提示：未安装markdown库，将使用简单格式处理。如需完整Markdown支持，请运行 'pip install markdown'")


class ReadmeViewer:
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title("README 查看器")
        self.window.geometry("800x600")
        
        # 设置窗口图标和属性
        self.window.minsize(600, 400)
        
        self.init_ui()
        self.load_readme()
    
    def init_ui(self):
        # 创建主框架
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题标签
        title_label = tk.Label(main_frame, text="README 文档", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=(0, 10))
        
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
                self.status_bar.config(text=f"已加载: {os.path.basename(readme_path)}")
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
                html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
                processed_content = self.process_html(html)
            except Exception as e:
                # 如果Markdown处理失败，回退到简单处理
                processed_content = self.process_markdown_simple(content)
        else:
            # 如果没有markdown库，使用简单处理
            processed_content = self.process_markdown_simple(content)
        
        self.text_area.insert(tk.END, processed_content)
        self.text_area.config(state=tk.DISABLED)
    
    def display_error(self, error_msg: str):
        """显示错误信息"""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, error_msg)
        self.text_area.config(state=tk.DISABLED)
    
    def process_html(self, html: str) -> str:
        """简化处理HTML标签"""
        # 处理标题
        html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'【\1】\n', html, flags=re.DOTALL)
        html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'● \1\n', html, flags=re.DOTALL)
        html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'■ \1\n', html, flags=re.DOTALL)
        html = re.sub(r'<h4[^>]*>(.*?)</h4>', r'◆ \1\n', html, flags=re.DOTALL)
        
        # 处理段落
        html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n', html, flags=re.DOTALL)
        
        # 处理粗体和斜体
        html = re.sub(r'<strong[^>]*>(.*?)</strong>', r'【\1】', html, flags=re.DOTALL)
        html = re.sub(r'<b[^>]*>(.*?)</b>', r'【\1】', html, flags=re.DOTALL)
        html = re.sub(r'<em[^>]*>(.*?)</em>', r'《\1》', html, flags=re.DOTALL)
        html = re.sub(r'<i[^>]*>(.*?)</i>', r'《\1》', html, flags=re.DOTALL)
        
        # 处理代码块
        html = re.sub(r'<code[^>]*>(.*?)</code>', r'『\1』', html, flags=re.DOTALL)
        html = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n代码块:\n\1\n', html, flags=re.DOTALL)
        
        # 处理列表
        html = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', html, flags=re.DOTALL)
        html = re.sub(r'<ul[^>]*>', r'', html)
        html = re.sub(r'</ul>', r'', html)
        html = re.sub(r'<ol[^>]*>', r'', html)
        html = re.sub(r'</ol>', r'', html)
        
        # 处理链接
        html = re.sub(r'<a href="(.*?)"[^>]*>(.*?)</a>', r'\2 (\1)', html)
        
        # 处理引用
        html = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'『引用』\1', html, flags=re.DOTALL)
        
        # 处理表格 (简化处理)
        html = re.sub(r'<table[^>]*>(.*?)</table>', r'表格:\1', html, flags=re.DOTALL)
        html = re.sub(r'<tr[^>]*>(.*?)</tr>', r'\1\n', html, flags=re.DOTALL)
        html = re.sub(r'<td[^>]*>(.*?)</td>', r'\1\t', html, flags=re.DOTALL)
        html = re.sub(r'<th[^>]*>(.*?)</th>', r'【\1】\t', html, flags=re.DOTALL)
        
        # 移除其他HTML标签
        html = re.sub(r'<[^>]+>', '', html)
        
        # 处理表情符号
        html = self.process_emojis(html)
        
        return html
    
    def process_markdown_simple(self, content: str) -> str:
        """简单处理Markdown格式和表情符号（备用方案）"""
        # 处理标题 (# H1, ## H2, ### H3等)
        content = re.sub(r'^# (.+)$', r'【\1】', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'● \1', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'■ \1', content, flags=re.MULTILINE)
        
        # 处理粗体 **text** 或 __text__
        content = re.sub(r'\*\*(.*?)\*\*', r'【\1】', content)
        content = re.sub(r'__(.*?)__', r'【\1】', content)
        
        # 处理斜体 *text* 或 _text_
        content = re.sub(r'\*(.*?)\*', r'《\1》', content)
        content = re.sub(r'_(.*?)_', r'《\1》', content)
        
        # 处理行内代码 `code`
        content = re.sub(r'`(.*?)`', r'『\1』', content)
        
        # 处理表情符号
        content = self.process_emojis(content)
        
        # 处理链接 [text](url)
        content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (\2)', content)
        
        # 处理无序列表项 (以-或*开头)
        content = re.sub(r'^\s*[-*]\s+(.+)$', r'• \1', content, flags=re.MULTILINE)
        
        # 处理引用块 (> text)
        content = re.sub(r'^>\s+(.+)$', r'『引用』\1', content, flags=re.MULTILINE)
        
        return content
    
    def process_emojis(self, content: str) -> str:
        """处理表情符号"""
        emoji_map = {
            ':)': '😊',
            ':(': '😞',
            ':D': '😄',
            ':P': '😛',
            ':O': '😲',
            '<3': '❤',
            '</3': '💔',
            ':thumbsup:': '👍',
            ':thumbsdown:': '👎',
            ':smile:': '😄',
            ':heart:': '❤',
            ':star:': '⭐',
            ':fire:': '🔥',
            ':warning:': '⚠',
            ':info:': 'ℹ',
            ':check:': '✅',
            ':x:': '❌',
            ':rocket:': '🚀',
            ':bulb:': '💡',
            ':cloud:': '☁',
            ':email:': '✉',
            ':phone:': '☎',
            ':house:': '🏠',
            ':book:': '📖',
            ':pencil:': '✏',
            ':paperclip:': '📎',
            ':scissors:': '✂',
            ':key:': '🔑',
            ':hammer:': '🔨',
            ':wrench:': '🔧',
            ':gear:': '⚙',
            ':calendar:': '📅',
            ':clock:': '⏰',
            ':hourglass:': '⏳',
            ':lock:': '🔒',
            ':unlock:': '🔓',
            ':bell:': '🔔',
            ':speech_balloon:': '💬',
            ':thought_balloon:': '💭'
        }
        
        for emoji_code, emoji_char in emoji_map.items():
            content = content.replace(emoji_code, emoji_char)
            
        return content